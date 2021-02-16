from scrapers.betfair import BetfairScraper
from scrapers.betflag import BetflagScraper
from dask.distributed import Client
from collections import defaultdict
from utility.bet_utility import BetInfo
from bet_container import BetContainer


def create_site_scraper(site_name, sport='calcio', bet_type='1x2'):
    classes = {'betfair': BetfairScraper,
               'betflag': BetflagScraper}

    if site_name not in classes:
        return None
    return classes[site_name](sport=sport, bet_type=bet_type)


def from_site_data_to_bet_info(data, site, sport):
    bets_info = []
    for match_tuple, match_bets in data.items():
        for bet_type, bet_price in match_bets.items():
            if match_tuple is not None and bet_price is not None:
                bets_info.append(BetInfo(*(*match_tuple, site, sport, bet_type, *bet_price)))
    return bets_info


class SingleBetTypeAnalyzer:
    def __init__(self, sport, bet_type, bet_container=BetContainer()):
        self.sites = ['betfair', 'betflag']
        self.sport = sport
        self.bet_type = bet_type
        self.bettors = dict(zip(self.sites,
                                [create_site_scraper(site, sport=sport, bet_type=bet_type) for site in self.sites]
                                )
                            )
        self.container = bet_container
        # Create a dask client
        self.client = Client(processes=False)

    def update_bets(self):
        # Get the data from the sites
        futures = [self.client.submit(bettor.get_data) for bettor in self.bettors.values()]
        sites_data = [f.result() for f in futures]
        bets_info = sum([from_site_data_to_bet_info(data, site, self.sport)
                         for site, data in zip(self.sites, sites_data)], [])
        # Find common bets between different sites

        # Filter the common bets
        for match, bets in match_bets:
            if len(bets) > 2:
                pass
        # Then return the results

    def analyze_bets(self, update=True):
        self.update_bets()
        pass

    def auto_bets(self):
        pass
