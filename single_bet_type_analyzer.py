from scrapers.betfair import BetfairScraper
from scrapers.betflag import BetflagScraper
from dask.distributed import Client
from collections import defaultdict
from utility.bet_utility import BetInfo, BetComparison
from bet_container import BetContainer
import pandas as pd

def print_data(_d):
    print(f'{len(_d)} match')
    for x in _d:
        print(x)
        for y in _d[x]:
            print(y, ':', _d[x][y])

def create_site_scraper(site_name, sport='calcio', bet_type='1x2', cluster=None):
    classes = {'betfair': BetfairScraper,
               'betflag': BetflagScraper}

    if site_name not in classes:
        return None
    return classes[site_name](sport=sport, bet_type=bet_type, cluster=cluster)


def from_site_data_to_bet_info(data, site, sport):
    bets_info = []
    for match_tuple_without_sport, match_bets in data.items():
        for bet_type, bet_price in match_bets.items():
            if match_tuple_without_sport is not None and bet_price is not None:
                bets_info.append(BetInfo(*(*match_tuple_without_sport, sport, site, bet_type, *bet_price)))
    return bets_info


class SingleBetTypeAnalyzer:
    def __init__(self, sport, bet_type, cluster=None, bet_container=None):
        self.sites = ['betfair', 'betflag']
        self.sport = sport
        self.bet_type = bet_type
        self.bettors = dict(zip(self.sites,
                                [create_site_scraper(site, sport=sport,
                                                     bet_type=bet_type, cluster=cluster) for site in self.sites]
                                )
                            )
        self.container = BetContainer(cluster=cluster)
        # Create a dask client
        if cluster is not None:
            self.client = Client(cluster)
        else:
            self.client = Client(processes=False)

    def update_bets(self):
        # Get the data from the sites
        # futures = [self.client.submit(bettor.get_data) for bettor in self.bettors.values()]
        # sites_data = [f.result() for f in futures]
        print('\tGet data')
        sites_data = [bettor.get_data() for bettor in self.bettors.values()]
        print('\tCreate bets list')
        bets_list = sum([from_site_data_to_bet_info(data, site, self.sport)
                         for site, data in zip(self.sites, sites_data)], [])
        # Update the bets in the bets container
        print('\tUpdate bets in container')
        self.container.update_bets(bets_list)

    def analyze_bets(self, update=True):
        if update:
            print('Inizio update bet')
            self.update_bets()
        df = pd.DataFrame(columns=BetComparison._fields)
        print('Ciclo su ', self.container.df.bet_type.unique())
        for bet_type in self.container.df.bet_type.unique():
            print('\tInizio search_bets_by_bet_type', bet_type)
            bets_dict = self.container.search_bets_by_bet_type(bet_type,
                                                               return_only_multiple_bets=True)
            print('\tInizio ciclo for su bets_dict')
            for match, bets in bets_dict.items():
                t = match + (bet_type,)
                t += tuple(bets.iloc[bets.back_price.argmax()][['site', 'back_price', 'back_size']])
                t += tuple(bets.iloc[bets.lay_price.argmin()][['site', 'lay_price', 'lay_size']])
                new_index = len(df)  # (df.index.max() + 1) if len(df) > 0 else 1
                df.loc[new_index] = t
        return df

    def auto_bets(self):
        pass

    def close(self):
        for bettor in self.bettors.values():
            bettor.close()
