import time
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
import web_config as cfg


class Device:

    def __init__(self):

        options = Options()
        options.set_preference('profile', cfg.profile_path)
        options.headless = False
        self.browser = webdriver.Firefox(options=options)

    def check_exists_by_xpath(self, xpath):
        try:
            element = self.browser.find_element(By.XPATH, xpath)
            return element
        except NoSuchElementException:
            return None
        return element

    def click_xpath(self, xpath):
        element = self.check_exists_by_xpath(xpath)
        if element is not None:
            element.click()
            return True
        return False

    def find_element_by_xpath(self, xpath):
        try:
            element = self.browser.find_element(By.XPATH, xpath)
            return element
        except NoSuchElementException:
            return None

    def find_elements_by_id(self, element_id):
        try:
            element = self.browser.find_elements(By.ID, element_id)
            return element
        except NoSuchElementException:
            return None

    def go_back(self):
        self.browser.back()
        time.sleep(0.5)

    def load_page(self, url):
        self.browser.get(url)
        time.sleep(0.5)

    def scroll_to_bottom(self):
        scroll_pause_time = 2.5
        last_height = self.browser.execute_script("return document.body.scrollHeight")
        i = 2
        while i > 0:
            # Scroll down to bottom
            self.browser.execute_script("window.scrollTo(0, document.body.scrollHeight);")

            # Wait to load page
            time.sleep(scroll_pause_time)

            # Calculate new scroll height and compare with last scroll height
            new_height = self.browser.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height
            i -= 1
