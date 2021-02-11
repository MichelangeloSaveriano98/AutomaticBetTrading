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


def parse_1x2_button(row):
    # Find odds
    odds_div = row_div.find('div', class_='odds')
    if not odds_div:
        return {}
    odds = odds_div.find_all('label')
    # Find liquidity
    liquidity = row_div.find('div', class_='odds').find_all('span')

    if odds and len(odds) == 6 and liquidity and len(liquidity) == 8:
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

def parse_row(row_div, feature='1x2'):
    feature_bets_parsers = {'1x2': parse_1x2_button}
    if feature not in feature_bets_parsers:
        raise Exception(f"Feature {feature} is not allowed!")
    # campionato = row_div.find('div', class_='details').text

    # Find match date
    # Modificare match date affinché contenga solo la data e non contenga informazioni riguardo l'orario
    # matchDate = str(pd.to_datetime(row_div.find('div', class_='date')['dt']).date())
    matchDate = row_div.find('div', class_='date')['dt'][:10]

    # Find clubs
    club1_tag, club2_tag = row_div.find('a', class_='da').find_all('b')
    сlub1 = club1_tag.text
    сlub2 = club2_tag.text

    # Return the bet tuple
    return (tuple(сlub1, сlub2, matchDate), feature_bets_parsers[feature](row))


class BetflagBettor(SiteBettor):
    def __init__(self, n_additional_data_loaded=10, sport='calcio'):
        self.n_additional_data_loaded = n_additional_data_loaded
        self.sport = sport
        self.url = 'https://www.betflag.it/exchange'

        self.driver = webdriver.Firefox(executable_path=GeckoDriverManager().install())
        self.driver.get(betflag_url)
        self.setup_driver()

        # Load data
        self.load_more_data(n_additional_data_loaded)

    def setup_driver(self):
        # Close login
        WebDriverWait(self.driver, timeout=10).until(
            expected_conditions.element_to_be_clickable(
                (By.XPATH, '/html/body/form/section/div[5]/div[2]/div[2]'))).click()
        # Close +18 warning
        WebDriverWait(self.driver, timeout=10).until(
            expected_conditions.element_to_be_clickable((By.XPATH, '//*[@id="Button1"]'))).click()
        # Click on last minute
        time.sleep(1)
        WebDriverWait(self.driver, timeout=10).until(
            expected_conditions.element_to_be_clickable(
                (By.XPATH, '/html/body/form/section/div[9]/div[3]/nav/div[2]/ul/li[1]/button'))).click()

    def load_more_data(self, n_times=1):
        # Add data
        for i in range(n_times):
            self.driver.execute_script("addEventsLast(30, '1')")
            time.sleep(0.1)

        # Wait until they are loaded
        for i in range((n_times + 2) * 2):
            self.driver.execute_script(f"window.scrollTo(0,{int(500 * i)})")
            time.sleep(0.5)

    def get_data(self):
        content_html = self.driver.find_element_by_class_name('containerEvents').get_attribute('innerHTML')
        soup = BeautifulSoup(content_html, 'html.parser')
        divs = soup.find_all('div', 'row-e')
        data = {'Timestamp': [], 'MatchDate': [],
                'Campionato': [], 'Club1': [], 'Club2': [],
                'Punta1Quota': [], 'Punta1Liqui': [],
                'PuntaXQuota': [], 'PuntaXLiqui': [],
                'Punta2Quota': [], 'Punta2Liqui': [],
                'Banca1Quota': [], 'Banca1Liqui': [],
                'BancaXQuota': [], 'BancaXLiqui': [],
                'Banca2Quota': [], 'Banca2Liqui': []
                }
        for div in divs:
            for key, value in parse_row(div).items():
                data[key].append(value)

        return data


