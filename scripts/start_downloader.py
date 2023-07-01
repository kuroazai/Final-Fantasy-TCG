import time
import urllib.request
import os
from databases import database
from browser.web_engine import Device
from bs4 import BeautifulSoup


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

    values = (name, text, group, element, cost, serial,
              job, power, catagory, boxset, code, card_img)
    database.DB.append_table(values)

    return EG.driver.page_source


def download_cards():
    EG.browser.get('https://fftcg.square-enix-games.com/na/card-browser')
    sch_btn = '/html/body/section/section/div/div[2]/div/div[1]/div[3]/button'
    EG.driver.find_element_by_xpath(sch_btn).click()

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


if __name__ == '__main__':

    EG = Device()
    source = download_cards()
