from selenium import webdriver
from webdriver_manager.firefox import GeckoDriverManager
from bs4 import BeautifulSoup
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.common.by import By
import datetime
import pandas as pd
from collections import defaultdict
from utility.date_utility import next_date_given_dayofweek
from site_bettor import SiteBettor
from utility.bet_utility import SingleBetInfo


def parse_1x2_button(row):
    # Find bet price and size
    bet_buttons = row.find('td', class_='coupon-runners').find_all('span')
    bets = [button.text if button.text[0] != '€' else button.text[1:] for button in bet_buttons]
    return {'1': SingleBetInfo(*bets[:4]),
            'x': SingleBetInfo(*bets[4:8]),
            '2': SingleBetInfo(*bets[8:])}

# def parse_row(row, feature='1x2'):
#     feature_bets_parsers = {'1x2': parse_1x2_button}
#     if feature not in feature_bets_parsers:
#         raise Exception(f"Feature {feature} is not allowed!")
#
#     data = {'Timestamp': str(datetime.datetime.now())}
#
#     # Check if it is live
#     start_date_wrapper = row.find('div', class_='start-date-wrapper')
#     if start_date_wrapper is None or start_date_wrapper.text.lower() == 'live':
#         # ...
#         data['MatchDate'] = str(datetime.datetime.today())
#     else:
#         # Find the date
#         date_string = row.find('div', class_='start-date-wrapper').text.lower().split()
#         if date_string[0] == 'inizia':
#             data['MatchDate'] = str(datetime.datetime.today())
#             # if date_string[-1] == 'poco':
#             #     data['MatchDate'] = str(datetime.datetime.now())
#             # else:
#             #     date = datetime.date.today()
#             #     data['MatchDate'] = str(pd.to_datetime(date) + datetime.timedelta(minutes=int(date_string[-1][:-1])))
#         else:
#             _hour, _min = map(int, date_string[-1].split(':'))
#             if len(date_string) == 2:
#                 if date_string[0] == 'oggi':
#                     date = datetime.date.today()
#                 else:
#                     date = next_date_given_dayofweek(date_string[0])
#             else:
#                 date = pd.to_datetime(' '.join(date_string[:-1]) + ' ' + str(datetime.date.today().year))
#
#             data['MatchDate'] = str(date)
#             # data['MatchDate'] = str(pd.to_datetime(date) + datetime.timedelta(minutes=_min,
#             #                                                                   hours=_hour))
#
#     # Find the competition
#     competition_string = row.find('a', class_='mod-link')['data-competition-or-venue-name'].lower().split('-')
#     data['Stato'] = competition_string[0]
#     data['Campionato'] = ' '.join(competition_string[1:])
#
#     # Find the clubs
#     clubs = row.find('ul', class_='runners').find_all('li')
#     if clubs:
#         data['Club1'] = clubs[0].text.lower()
#         data['Club2'] = clubs[1].text.lower()
#
#     # Find bets price and size
#     data.update(feature_bets_parsers[feature](row))
#
#     return data


def parse_row(row, feature='1x2'):
    feature_bets_parsers = {'1x2': parse_1x2_button}
    if feature not in feature_bets_parsers:
        raise Exception(f"Feature {feature} is not allowed!")

    # Check if it is live
    start_date_wrapper = row.find('div', class_='start-date-wrapper')
    if start_date_wrapper is None or start_date_wrapper.text.lower() == 'live':
        # ...
        matchDate = str(datetime.datetime.today())
    else:
        # Find the date
        date_string = row.find('div', class_='start-date-wrapper').text.lower().split()
        if date_string[0] == 'inizia':
            matchDate = str(datetime.datetime.today())
            # if date_string[-1] == 'poco':
            #     data['MatchDate'] = str(datetime.datetime.now())
            # else:
            #     date = datetime.date.today()
            #     data['MatchDate'] = str(pd.to_datetime(date) + datetime.timedelta(minutes=int(date_string[-1][:-1])))
        else:
            _hour, _min = map(int, date_string[-1].split(':'))
            if len(date_string) == 2:
                if date_string[0] == 'oggi':
                    date = datetime.date.today()
                else:
                    date = next_date_given_dayofweek(date_string[0])
            else:
                date = pd.to_datetime(' '.join(date_string[:-1]) + ' ' + str(datetime.date.today().year))

            matchDate = str(date)
            # data['MatchDate'] = str(pd.to_datetime(date) + datetime.timedelta(minutes=_min,
            #                                                                   hours=_hour))

    # Find the clubs
    clubs = row.find('ul', class_='runners').find_all('li')
    if clubs:
        club1 = clubs[0].text.lower()
        club2 = clubs[1].text.lower()

    # Find bets price and size
    return (tuple(club1, club2, matchDate), feature_bets_parsers[feature](row))


def sport_url(sport):
    sports_path = {'calcio': 'calcio-scommesse-1/'}
    return 'https://www.betfair.it/exchange/plus/it/' + sports_path[sport]


class BetfairBettor(SiteBettor):
    def __init__(self, max_pages=10, sport='calcio'):
        self.sport = sport
        self.max_pages = max_pages
        self.url = sport_url(self.sport)
        self.driver = webdriver.Firefox(executable_path=GeckoDriverManager().install())
        self.driver.get(self.url)

        # Accept cookies
        WebDriverWait(self.driver, timeout=10).until(
            expected_conditions.element_to_be_clickable((By.XPATH, '//*[@id="onetrust-accept-btn-handler"]'))).click()
        self.n_pages = self.number_of_pages()

    def number_of_pages(self):
        return len(self.driver.find_element_by_class_name(
            "coupon-page-navigation__bullets").find_elements_by_tag_name('li'))

    def get_data(self):
        content_html = self.driver.find_element_by_tag_name('bf-super-coupon').get_attribute('innerHTML')
        soup = BeautifulSoup(content_html, 'html.parser')
        rows = soup.find_all('tr', attrs={"ng-repeat-start":
                                          "(marketId, event) in vm.tableData.events"})
        data = {}
        for row in rows:
            key, value = parse_row(row)
            data[key] = value

        return data

    def bet(self):
        pass
