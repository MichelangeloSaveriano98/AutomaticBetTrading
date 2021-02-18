from selenium import webdriver
from bs4 import BeautifulSoup
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.common.by import By
import datetime
import pandas as pd
import time
from collections import defaultdict
from utility.date_utility import next_date_given_dayofweek
from scrapers.site_scraper import SiteScraper
from utility.bet_utility import BetPrice
from math import ceil
from dask.distributed import Client
from selenium.common.exceptions import NoSuchElementException

def parse_1x2_button(row):
    # Find bet price and size
    bet_buttons = row.find('td', class_='coupon-runners').find_all('span')
    bets = [button.text if button.text[0] != '€' else button.text[1:] for button in bet_buttons]
    return {'1': BetPrice(*map(float, bets[:4])),
            'x': BetPrice(*map(float, bets[4:8])),
            '2': BetPrice(*map(float, bets[8:12]))}


def parse_12_button(row):
    # Find bet price and size
    bet_buttons = row.find('td', class_='coupon-runners').find_all('span')
    bets = [button.text if button.text[0] != '€' else button.text[1:] for button in bet_buttons]
    return {'1': BetPrice(*map(float, bets[:4])),
            '2': BetPrice(*map(float, bets[4:8]))}


def parse_uo_button(row):
    # Find bet price and size
    bet_buttons = row.find('td', class_='coupon-runners').find_all('span')
    bets = [button.text if button.text[0] != '€' else button.text[1:] for button in bet_buttons]
    return {'u': BetPrice(*map(float, bets[:4])),
            'o': BetPrice(*map(float, bets[4:8]))}


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


def parse_row(row, bet_type):
    bet_type_bets_parsers = {'1x2': parse_1x2_button,
                             '12': parse_12_button,
                             'uo1.5': parse_uo1_button,
                             'uo2.5': parse_uo2_button,
                             'uo3.5': parse_uo3_button,
                             'uo4.5': parse_uo4_button}
    if bet_type not in bet_type_bets_parsers:
        raise Exception(f"bet_type {bet_type} is not allowed!")

    # Check if it is live
    start_date_wrapper = row.find('div', class_='start-date-wrapper')
    if start_date_wrapper is None or start_date_wrapper.text.lower() == 'live':
        # ...
        matchDate = str(datetime.datetime.today().date())
    else:
        # Find the date
        date_string = row.find('div', class_='start-date-wrapper').text.lower().split()
        if date_string[0] == 'inizia':
            matchDate = str(datetime.date.today())
        else:
            _hour, _min = map(int, date_string[-1].split(':'))
            if len(date_string) == 2:
                if date_string[0] == 'oggi':
                    date = datetime.date.today()
                else:
                    date = next_date_given_dayofweek(date_string[0])
            else:
                date = pd.to_datetime(' '.join(date_string[:-1]) + ' ' + str(datetime.date.today().year)).date()

            matchDate = str(date)

    # Find the clubs
    clubs = row.find('ul', class_='runners').find_all('li')
    if clubs:
        club1 = clubs[0].text.lower()
        club2 = clubs[1].text.lower()

        # Find bets price and size
        return (club1, club2, matchDate), bet_type_bets_parsers[bet_type](row)

def parse_content(content_html, bet_type):
    soup = BeautifulSoup(content_html, 'html.parser')
    # Parse the content
    rows = soup.find_all('tr', attrs={"ng-repeat-start": "(marketId, event) in vm.tableData.events"})
    data = {}
    for row in rows:
        key, value = parse_row(row, bet_type=bet_type)
        data[key] = value

    return data

def sport_url(sport):
    sports_path = {'calcio': 'calcio-scommesse-1/',
                   'tennis': 'tennis-scommesse-2/',
                   'basket': 'basket-scommesse-7522/'}
    return 'https://www.betfair.it/exchange/plus/it/' + sports_path[sport]


class BetfairScraper(SiteScraper):
    def __init__(self, sport='calcio', bet_type='1x2', max_pages=10, cluster=None):
        self.sport = sport
        self.bet_type = bet_type
        self.max_pages = max_pages
        self.url = sport_url(self.sport)
        self.refresh_period = 600 # seconds
        # Create a dask client
        if cluster is not None:
            self.client = Client(cluster)
        else:
            self.client = Client(processes=False)
        self.drivers = []
        # Calculate the number of pages
        self.reset_drivers(1)
        self.n_pages = self.number_of_pages()
        # Create the drivers
        self.reset_drivers(min(self.max_pages, self.n_pages))

    def reset_drivers(self, n_drivers=-1):
        self.close(close_client=False)
        if n_drivers == -1:
            n_drivers = len(self.drivers)
        self.drivers = [webdriver.Chrome() for i in range(n_drivers)]
        self.setup_drivers()

    def setup_drivers(self):
        # Get the pages
        i=1
        for driver in self.drivers:
            driver.get(self.url + str(i))
            i += 1
        self.last_refresh = datetime.datetime.now()
        # Accept the cookies
        for driver in self.drivers:
            WebDriverWait(driver, timeout=15).until(
                expected_conditions.element_to_be_clickable(
                    (By.XPATH, '//*[@id="onetrust-accept-btn-handler"]'))).click()  # Cookies
        self.set_bet_type()

    def set_bet_type(self):
        # If bet type is under/over
        if self.bet_type[:2] == 'uo':
            n_goal = self.bet_type[-3:]
            for driver in self.drivers:
                driver.find_elements_by_class_name('selected-option')[-1].click()
                time.sleep(0.1)
                driver.find_element_by_xpath(f"//span[contains(text(), 'Under/Over {n_goal} Goal')]").click()

    def number_of_pages(self):
        self.drivers[0].get(self.url)
        time.sleep(1)
        try:
            return len(self.drivers[0].find_element_by_class_name("coupon-page-navigation__bullets"
                                                                  ).find_elements_by_tag_name('li'))
        except NoSuchElementException:
            # Number of pages not found
            return 1

    def close(self, close_client=True):
        for driver in self.drivers:
            driver.close()
        if close_client:
            self.client.close()

    def refresh_pages(self, loading_period=2):
        n_pages = self.number_of_pages()
        if self.n_pages == n_pages:
            for driver in self.drivers:
                driver.refresh()
            time.sleep(loading_period)
        else:
            self.n_pages = n_pages
            self.reset_drivers(min(self.max_pages, self.n_pages))

    def get_data(self):
        data = {}
        if self.last_refresh + datetime.timedelta(seconds=self.refresh_period) > datetime.datetime.now():
            self.refresh_pages()
            self.last_refresh = datetime.datetime.now()
        # Parse the content using dask futures
        futures = [self.client.submit(parse_content,  # function
                                      driver.find_element_by_tag_name('bf-super-coupon').get_attribute('innerHTML'), # content_html
                                      self.bet_type,  # bet_type
                                      ) for driver in self.drivers]
        for f in futures:
            data.update(f.result())
        return data