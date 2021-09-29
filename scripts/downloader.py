# -*- coding: utf-8 -*-
"""
Created on Thu Sep 16 17:22:40 2021

@author: Odin
"""

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from dataclasses import dataclass, field
import time
import re
import database
import urllib.request
import os

class device(object):

    def __init__(self):
        options = Options()
        options.headless = False
        self.browser = webdriver.Firefox(options=options)
        self.driver = self.browser

class CardManager:

    def __init__(self):
        self.cards = []

    def add_card(self, card):
        self.cards.append(card)
        pass

    def remove_card(self, card):
        pass

    def return_catagory(self,):
        pass

    def return_all_catagory(self):
        pass


@dataclass(order=True, frozen=True)
class Card:
    sort_index: str = field(init=False, repr=False)
    name: str
    text: str
    group: str
    element: str
    cost: int
    serial: str
    job : str
    power: int
    catagory: str
    boxset: str
    code: str
    card_img: str

    def _post_init__(self):
        object.__setattr__(self, 'sort_index', self.name)

    def generate_feat(self):
        feat = {'geometry': {'Type': 'Point',
                             'coordiantes': [self.lat, self.long]},

                'properties': {'name': self.name,
                               'station_id': self.station_id,
                               'value': self.value,
                               'units': self.units
                               }
                }
        return feat

    def __str__(self):
        return f'Name: {self.name} \nType: {self.group} \nCost:{self.cost}  Element:{self.element} \nEffect:{self.text}'


def get_details():
    # soup method
    soup = BeautifulSoup(EG.driver.page_source, "html.parser")
    details = soup.find_all('div', class_='col details')
    # print(len(details))
    name = '/html/body/section/section/div/div[2]/div/div[4]/div[1]/span[4]'
    name = EG.driver.find_element_by_xpath(name).text
    element = '/html/body/section/section/div/div[2]/div/div[4]/div[3]/span[4]/span[2]'
    element = EG.driver.find_element_by_xpath(element).get_attribute('class')
    element = element.replace('icon', '').strip()
    card_img = '/html/body/section/section/div/div[2]/div/div[4]/div[2]/img'
    card_img = EG.driver.find_element_by_xpath(card_img).get_attribute('src')
    # obj_name = {}
    # obj_name[name] = Card()

    items = [x for x in details[0]]
    text = items[1].text.replace('  ', ' ')
    text = ' '.join(text.split())
    group = items[3].text.split(':')[1].strip()
    job = items[4].text.split(':')[1].strip()
    cost = items[6].text.split(':')[1].strip()
    serial = items[7].text.split(':')[1].strip()
    catagory = items[9].text.split(':')[1].strip()
    boxset = items[10].text.split(':')[1].strip()
    code = items[11].text.split(':')[1].strip()
    power = items[8].text.split(':')[1].strip()
    mydir = os.getcwd()

    urllib.request.urlretrieve(card_img, mydir + "/images/{}-{}.jpg".format(name,
                                                                            code))

    obj_name = {}
    obj_name[name] = Card(name,
                          text,
                          group,
                          element,
                          cost,
                          serial,
                          job,
                          power,
                          catagory,
                          boxset,
                          code,
                          card_img
                          )
    # print(obj_name[name].__str__())
    CM.add_card(obj_name[name])
    values = (name, text, group, element, cost, serial,
              job, power, catagory, boxset, code, card_img)
    database.DB.append_table(values)

    return EG.driver.page_source


def download_cards():
    EG.browser.get('https://fftcg.square-enix-games.com/na/card-browser')
    # search all cards
    sch_btn = '/html/body/section/section/div/div[2]/div/div[1]/div[3]/button'
    EG.driver.find_element_by_xpath(sch_btn).click()
    # first item
    time.sleep(4)
    pic1 = '/html/body/section/section/div/div[2]/div/div[3]/div[2]/img'
    EG.driver.find_element_by_xpath(pic1).click()
    total = '/html/body/section/section/div/div[2]/div/div[4]/div[1]/span[2]'
    total = EG.driver.find_element_by_xpath(total).text
    total = total.split('/')[1]
    nxt_btn = '/html/body/section/section/div/div[2]/div/div[4]/div[1]/span[3]'
    for i in range(1, int(total)):
        source = get_details()
        EG.driver.find_element_by_xpath(nxt_btn).click()
        time.sleep(1)
    EG.browser.close()
    database.DB.cursor.close()

    return source


EG = device()
CM = CardManager()
source = download_cards()
