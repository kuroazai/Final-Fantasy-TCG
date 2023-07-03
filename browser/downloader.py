import os
import time
from browser.web_engine import Device
from bs4 import BeautifulSoup
from tqdm import tqdm



class DLEngine:

    def __init__(self, redis_conn):
        self.redis_conn = redis_conn
        self.device = Device()

    def get_details(self):

        soup = BeautifulSoup(self.device.browser.page_source, "html.parser")
        details = soup.find_all('div', class_='col details')
        data = self.process_details(details)
        name = '/html/body/section/section/div/div[2]/div/div[4]/div[1]/span[4]'
        name = '/html/body/section/section/div/div[2]/div/div[4]/div[3]/table/tbody/tr[3]/td[2]/span'
        data['name'] = self.device.find_element_by_xpath(name).text

        # element = '/html/body/section/section/div/div[2]/div/div[4]/div[3]/span[4]/span[2]'
        # element = self.device.find_element_by_xpath(element).get_attribute('class')
        # data['element'] = element.replace('icon', '').strip()

        card_img = '/html/body/section/section/div/div[2]/div/div[4]/div[2]/img'
        card_img_2 ='/html/body/section/section/div/div[2]/div/div[4]/div[2]/div/div[2]/div/div/div/img'
        kda = self.device.find_element_by_xpath(card_img_2)
        data['card_img'] = kda.get_attribute('src')
        # data['card_img'] = self.device.find_element_by_xpath(card_img).get_attribute('src')

        return data

    def process_details(self, details: list) -> dict:

        data = {}
        items = details[0].find_all("td")

        data['text'] = ' '.join(details[0].find("p",
                                                class_="text").text.split())
        data['group'] = items[1].text.strip()
        data['job'] = items[3].text.strip()
        data['element'] = self.get_element(items[5])
        data['cost'] = items[7].text.strip()
        data['serial'] = items[9].text.strip()
        data['category'] = items[13].text.strip()
        data['box_set'] = items[15].text.strip()
        data['code'] = items[17].text.strip()
        data['power'] = items[11].text.strip()

        return data

    def get_element(self, td_element):
        # Create a BeautifulSoup object
        soup = BeautifulSoup(str(td_element), 'html.parser')
        # Access the <td> element
        td_element = soup.find('td')
        # Access the <span> element
        span_element = td_element.find('span')
        # Get the value of the "class" attribute
        class_value = span_element.get('class')
        return class_value[1]

    def download_cards(self):
        self.device.browser.get('https://fftcg.square-enix-games.com/na/card-browser')
        sch_btn = '/html/body/section/section/div/div[2]/div/div[1]/div[3]/button'
        self.device.find_element_by_xpath(sch_btn).click()

        time.sleep(4)

        element_id = "onetrust-accept-btn-handler"
        self.device.find_elements_by_id(element_id)[0].click()
        time.sleep(1)
        pic1 = '/html/body/section/section/div/div[2]/div/div[3]/div[2]/img'
        self.device.find_element_by_xpath(pic1).click()

        total = '/html/body/section/section/div/div[2]/div/div[4]/div[1]/span[2]'
        total = self.device.find_element_by_xpath(total).text
        total = total.split('/')[1]
        nxt_btn = '/html/body/section/section/div/div[2]/div/div[4]/div[1]/span[3]'

        data = []
        for i in tqdm(range(1, int(total))):
            try:
                data.append(self.get_details())
                self.device.find_element_by_xpath(nxt_btn).click()
                time.sleep(0.5)
            except Exception as e:
                self.device.find_element_by_xpath(nxt_btn).click()
                time.sleep(1)
            if i % 50 == 0:
                self.redis_conn.set('ff-tcg-cards', data)

        return data

