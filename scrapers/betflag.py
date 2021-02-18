from selenium import webdriver
from webdriver_manager.firefox import GeckoDriverManager
from bs4 import BeautifulSoup
import selenium
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.common.by import By
import datetime
import time
import pandas as pd
from scrapers.site_scraper import SiteScraper
from collections import defaultdict
from utility.bet_utility import BetPrice


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
    return {'1': BetPrice(odds[0].text,
                               liquidity[1].text[:-1],
                          odds[3].text,
                               liquidity[5].text[:-1]),
            'x': BetPrice(odds[1].text,
                               liquidity[2].text[:-1],
                          odds[4].text,
                               liquidity[6].text[:-1]),
            '2': BetPrice(odds[2].text,
                               liquidity[3].text[:-1],
                          odds[5].text,
                               liquidity[7].text[:-1])}

def parse_12_button(row):
    # Find odds
    odds_div = row.find('div', class_='odds')
    if not odds_div:
        return {'u': None, 'o': None}
    odds = odds_div.find_all('label')
    # Find liquidity
    liquidity = row.find('div', class_='odds').find_all('span')
    if not (odds and len(odds) == 4 and liquidity and len(liquidity) == 6):
        return {'u': None, 'o': None}
    return {'u': BetPrice(odds[0].text,
                               liquidity[1].text[:-1],
                          odds[2].text,
                               liquidity[4].text[:-1]),
            'o': BetPrice(odds[1].text,
                               liquidity[2].text[:-1],
                          odds[3].text,
                               liquidity[5].text[:-1])}

def parse_uo_button(row):
    # Find odds
    odds_div = row.find('div', class_='odds')
    if not odds_div:
        return {'u': None, 'o': None}
    odds = odds_div.find_all('label')
    # Find liquidity
    liquidity = row.find('div', class_='odds').find_all('span')
    if not (odds and len(odds) == 4 and liquidity and len(liquidity) == 6):
        return {'u': None, 'o': None}
    return {'u': BetPrice(odds[0].text,
                               liquidity[1].text[:-1],
                          odds[2].text,
                               liquidity[4].text[:-1]),
            'o': BetPrice(odds[1].text,
                               liquidity[2].text[:-1],
                          odds[3].text,
                               liquidity[5].text[:-1])}

def parse_uo1_button(row):
    bets = parse_uo_button(row)
    return {'u1.5': bets['u'], 'o1.5': bets['o']}

def parse_uo2_button(row):
    bets = parse_uo_button(row)
    return {'u2.5': bets['u'], 'o2.5': bets['o']}

def parse_uo3_button(row):
    bets = parse_uo_button(row)
    return {'u3.5': bets['u'], 'o3.5': bets['o']}

def parse_uo4_button(row):
    bets = parse_uo_button(row)
    return {'u4.5': bets['u'], 'o4.5': bets['o']}

def parse_row(row, bet_type='1x2'):
    bet_type_bets_parsers = {'1x2': parse_1x2_button,
                            '12': parse_12_button,
                            'uo1.5': parse_uo1_button,
                            'uo2.5': parse_uo2_button,
                            'uo3.5': parse_uo3_button,
                            'uo4.5': parse_uo4_button}
    if bet_type not in bet_type_bets_parsers:
        raise Exception(f"bet_type {bet_type} is not allowed!")
    # campionato = row_div.find('div', class_='details').text

    # Find match date
    # matchDate = str(pd.to_datetime(row_div.find('div', class_='date')['dt']).date())
    matchDate = row.find('div', class_='date')['dt'][:10]

    # Find clubs
    clubs = row.find('a', class_='da').find_all('b')
    if len(clubs) != 2:
        return (None, None)
    club1_tag, club2_tag = clubs
    сlub1 = club1_tag.text.lower().replace(' / ', '/').replace(' ,', '-')
    сlub2 = club2_tag.text.lower().replace(' / ', '/').replace(' ,', '-')

    # Return the bet tuple
    return (сlub1, сlub2, matchDate), bet_type_bets_parsers[bet_type](row)


class BetflagScraper(SiteScraper):
    def __init__(self, sport='calcio', bet_type='1x2', n_additional_data_loaded=4):
        self.n_additional_data_loaded = n_additional_data_loaded
        self.sport = sport
        self.bet_type = bet_type
        self.url = 'https://www.betflag.it/exchange'

        self.driver = webdriver.Chrome()
        self.driver.get(self.url)
        # Setup the driver
        self.setup_driver()
        # Login
        time.sleep(1)
        # self.driver.find_element_by_xpath('//*[@id="btnLoginModal"]').click()
        # time.sleep(0.75)
        # self.driver.find_element_by_xpath('//*[@id="LoginUsername"]').send_keys('username')
        # self.driver.find_element_by_xpath('//*[@id="LoginPassword"]').send_keys('password')
        # self.driver.find_element_by_xpath('//*[@id="BtnLoginNew2"]').click()

        # Load data
        self.load_additional_data()

    def setup_driver(self):
        # Close +18 warning
        WebDriverWait(self.driver, timeout=15).until(
            expected_conditions.element_to_be_clickable(
                (By.XPATH, '//*[@id="Button1"]')))
        time.sleep(1)
        self.driver.find_element_by_xpath('//*[@id="Button1"]').click()
        # Close login
        WebDriverWait(self.driver, timeout=15).until(
            expected_conditions.element_to_be_clickable((By.XPATH, '//*[@id="PromoPopup"]/div[2]/div[2]')))
        time.sleep(1)
        self.driver.find_element_by_xpath('//*[@id="PromoPopup"]/div[2]/div[2]').click()
        # Click on last minute
        time.sleep(1)
        WebDriverWait(self.driver, timeout=15).until(
            expected_conditions.element_to_be_clickable(
                (By.XPATH, '/html/body/form/section/div[9]/div[3]/nav/div[2]/ul/li[1]/button'))).click()
        self.set_sport()

    def set_sport(self):
        if self.sport == 'tennis':
            self.driver.find_element_by_xpath('//*[@id="MenuScroller"]/ul/li[2]').click()
        elif self.sport == 'basket':
            self.driver.find_element_by_xpath('//*[@id="MenuScroller"]/ul/li[3]').click()
        elif self.sport == 'volley':
            self.driver.find_element_by_xpath('//*[@id="MenuScroller"]/ul/li[4]').click()

    def set_bet_type(self):
        time.sleep(1)
        if self.bet_type != '1x2':
            is_uo = self.bet_type[:2] == 'uo'
            if is_uo:
                n_goal = self.bet_type[-3:]
                self.driver.find_element_by_xpath(f"//a[contains(text(), 'Under And Over {n_goal}')]"
                                                  ).find_element_by_xpath('..').click()

    def load_additional_data(self):
        # Add data
        time.sleep(2.5)
        for i in range(self.n_additional_data_loaded):
            try:
                self.driver.find_element_by_class_name('addEvents').click()
                time.sleep(0.25)
            except selenium.common.exceptions.NoSuchElementException:
                break
        # Set the bet_type
        self.driver.execute_script(f"window.scrollTo(0,0)")
        self.set_bet_type()
        # Wait until they are loaded
        self.scroll_page()

    def scroll_page(self, wait_period=0.75):
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
            key, value = parse_row(div, bet_type=self.bet_type)
            if value:
                data[key] = value

        return data

    def bet(self):
        pass

    def close(self):
        self.driver.close()

