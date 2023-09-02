import os
import time
import urllib.request
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import pandas as pd
import pytesseract
from PIL import Image, ImageOps
import cv2
import logging

class WebScraper:

    def __init__(self):
        self.start_time = time.time()
        self.path = self.create_directories()
        self.url = 'https://etenders.gov.in/eprocure/app'
        self.file_name = self.generate_file_name(self.url)
        self.log_file_path = self.log_file_dir()


        logging.basicConfig(
            filename=self.log_file_path + self.file_name + ".log",
            filemode='a',
            level=logging.INFO,
            format='%(asctime)s %(message)s'
        )
        logging.info('Started Web Scraping')
        logging.info('Program Start')

        self.chrome_options = Options()
        self.chrome_options.add_argument('--ignore-ssl-errors=yes')
        self.chrome_options.add_argument('--ignore-certificate-errors')
        self.driver = webdriver.Chrome(executable_path='chromedriver.exe', options=self.chrome_options)
        self.driver.maximize_window()

    def create_directories(self):
        cappath = os.path.dirname(os.path.abspath(__file__)) + "\\Images"
        if not os.path.exists(cappath):
            os.makedirs(cappath)
        return cappath

    def log_file_dir(self):
        log_file_path = os.path.expanduser('~') + "\\Documents\\" + "PythonLog\\"
        if not os.path.exists(log_file_path):
            os.makedirs(log_file_path)
        return log_file_path

    def generate_file_name(self, url):
        file_name = url.split('://')[1].split("/")[0].replace(".", "_")
        return file_name

    def solve_captcha(self):
        # path = r'C:\Users\dhruvin.kalathiya\Downloads'
        # self.cappath
        while True:
            capImg1 = self.driver.find_element(By.XPATH, '//*[@id="captchaImage"]').get_attribute("src")
            urllib.request.urlretrieve(capImg1, self.path + '\\captcha.png')

            img = Image.open(self.path + '\\captcha.png')
            img_with_border = ImageOps.expand(img, border=50, fill='white')
            path1 = self.path + '\\10.png'
            img_with_border.save(path1)

            img = cv2.imread(path1, 10)
            img = cv2.medianBlur(img, 5)

            x = pytesseract.image_to_string(img)

            os.remove(self.path + '\\captcha.png')
            doccaptchaText = self.driver.find_element(By.ID, 'captchaText')
            doccaptchaText.send_keys(x)

            try:
                self.driver.find_element(By.XPATH, "//*[text()='Invalid Captcha! Please Enter Correct Captcha.']")
            except:
                break

    def scrape_active_tenders(self):
        try:
            self.driver.get(self.url)
            wait = WebDriverWait(self.driver, 10)
            active_tender = wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="Menu"]/tbody/tr/td/span//a[text() = "Active Tenders"]')))
            self.driver.execute_script("arguments[0].click();", active_tender)
            n_page = 0
            page = True
            while page:
                self.solve_captcha()
                wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="table"]')))
                html = self.driver.find_element(By.XPATH, '//*[@id="table"]').get_attribute("outerHTML")
                soup = BeautifulSoup(html, 'html.parser')
                rows = soup.find('table', {'id': 'table'}).find_all('tr')
            
                info = []
                n_page += 1

                for row in rows[1:11]:
                    data = dict()
                    columns = row.find_all('td')
                    data["id"] = columns[4].find_all(text=True, recursive=False)[-1].strip()
                    # data["id"] = columns[4].get_text(strip=True).replace('\n', '').replace('\t', '')
                    data["pub_date"] = columns[1].get_text()
                    data["close_date"] = columns[2].get_text()
                    data["open_date"] = columns[3].get_text()
                    data["title"] = columns[4].find('a').text.replace('[', '').replace(']', '')
                    data["org"] = columns[5].get_text().replace('\n', '').replace('\t', '')
                    data["tender_value"] = columns[6].get_text()
                    data["doc"] = urljoin(self.url, columns[4].find('a').get("href"))
                    info.append(data)

                try:
                    new_df = pd.DataFrame(info)
                    new_df.to_csv('collected_tenders.csv', mode='a', header=False, index=False)
                except:
                    df = pd.DataFrame(info)
                    print(df.head())
                    df.to_csv('collected_tenders.csv', index=False)

                try:
                    next = self.driver.find_element(By.XPATH, '//*[@id="table"]/tbody/tr/td[@class = "list_footer"]//a[@id = "linkFwd"]')
                    self.driver.execute_script("arguments[0].click();", next)
                except:
                    page = False

        except Exception as e:
            print(e)
            logging.error(e)

    def run(self):
        try:
            self.scrape_active_tenders()
        except Exception as e:
            print(e)
            logging.error(e)

        time.sleep(5)
        print("Completed")
        self.driver.close()
        self.driver.quit()
        end_time = time.time()
        execution_time = end_time - self.start_time
        print(f"Execution time: {execution_time} seconds")

if __name__ == "__main__":
    scraper = WebScraper()
    scraper.run()


