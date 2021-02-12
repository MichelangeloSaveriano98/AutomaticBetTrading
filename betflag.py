from selenium import webdriver
from webdriver_manager.firefox import GeckoDriverManager
from bs4 import BeautifulSoup
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.common.by import By
import datetime
import time
import pandas as pd
from site_bettor import SiteBettor
from collections import defaultdict
from utility.bet_utility import SingleBetInfo



def parse_1x2_button(row):
    # Find odds
    odds_div = row.find('div', class_='odds')
    if not odds_div:
        return {}
    odds = odds_div.find_all('label')
    # Find liquidity
    liquidity = row.find('div', class_='odds').find_all('span')
    if not (odds and len(odds) == 6 and liquidity and len(liquidity) == 8):
        return None
    return {'1': SingleBetInfo(odds[0].text,
                               liquidity[1].text,
                               odds[3].text,
                               liquidity[5].text),
            'x': SingleBetInfo(odds[1].text,
                               liquidity[2].text,
                               odds[4].text,
                               liquidity[6].text),
            '2': SingleBetInfo(odds[2].text,
                               liquidity[3].text,
                               odds[5].text,
                               liquidity[7].text)}

def parse_row(row, feature='1x2'):
    feature_bets_parsers = {'1x2': parse_1x2_button}
    if feature not in feature_bets_parsers:
        raise Exception(f"Feature {feature} is not allowed!")
    # campionato = row_div.find('div', class_='details').text

    # Find match date
    # matchDate = str(pd.to_datetime(row_div.find('div', class_='date')['dt']).date())
    matchDate = row.find('div', class_='date')['dt'][:10]

    # Find clubs
    clubs = row.find('a', class_='da').find_all('b')
    if len(clubs) != 2:
        return (None, None)
    club1_tag, club2_tag = clubs
    сlub1 = club1_tag.text
    сlub2 = club2_tag.text

    # Return the bet tuple
    return (сlub1, сlub2, matchDate), feature_bets_parsers[feature](row)


class BetflagBettor(SiteBettor):
    def __init__(self, n_additional_data_loaded=10, sport='calcio', feature='1x2'):
        self.n_additional_data_loaded = n_additional_data_loaded
        self.sport = sport
        self.feature = feature
        self.url = 'https://www.betflag.it/exchange'

        # self.driver = webdriver.Firefox(executable_path=GeckoDriverManager().install())
        self.driver = webdriver.Chrome(executable_path='./chromeDriver/chromedriver.exe')
        self.driver.get(self.url)
        self.setup_driver()

        # Load data
        self.load_additional_data()

    def setup_driver(self):
        # Close login
        WebDriverWait(self.driver, timeout=15).until(
            expected_conditions.element_to_be_clickable(
                (By.XPATH, '/html/body/form/section/div[5]/div[2]/div[2]'))).click()
        # Close +18 warning
        WebDriverWait(self.driver, timeout=15).until(
            expected_conditions.element_to_be_clickable((By.XPATH, '//*[@id="Button1"]'))).click()
        # Click on last minute
        time.sleep(1)
        WebDriverWait(self.driver, timeout=15).until(
            expected_conditions.element_to_be_clickable(
                (By.XPATH, '/html/body/form/section/div[9]/div[3]/nav/div[2]/ul/li[1]/button'))).click()

    def load_additional_data(self):
        # Add data
        for i in range(self.n_additional_data_loaded):
            self.driver.find_element_by_class_name('addEvents').click()
            time.sleep(0.25)
        # Wait until they are loaded
        self.scroll_page()

    def scroll_page(self, wait_period=0.5):
        time.sleep(1)
        for i in range(self.n_additional_data_loaded * 4):
            self.driver.execute_script(f"window.scrollTo(0,{int(500 * i)})")
            time.sleep(wait_period)

    def get_data(self):
        data = {}
        # Scroll the page in order to be sure that all the bets are loaded
        self.scroll_page(0.1)
        # Extract HTML code
        content_html = self.driver.find_element_by_class_name('containerEvents').get_attribute('innerHTML')
        soup = BeautifulSoup(content_html, 'html.parser')
        # Scrape the data
        divs = soup.find_all('div', 'row-e')
        for div in divs:
            key, value = parse_row(div)
            if value:
                data[key] = value

        return data

    def bet(self):
        pass

    def close(self):
        self.driver.close()

