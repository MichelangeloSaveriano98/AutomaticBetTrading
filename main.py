from scrapers.betflag import BetflagScraper
from single_bet_type_analyzer import SingleBetTypeAnalyzer
from dask.distributed import LocalCluster
from ensemble_bet_analyzer import EnsembleBetAnalyzer


def print_data(_d):
    print(f'{len(_d)} match')
    for x in _d:
        print(x)
        for y in _d[x]:
            print(y, ':', _d[x][y])


if __name__ == '__main__':
    # cluster = None
    cluster = LocalCluster(processes=False)
    # analyzer = EnsembleBetAnalyzer()
    analyzer = SingleBetTypeAnalyzer('tennis', '12', cluster=cluster)
    # scraper = BetflagScraper('tennis', '12')
    try:
        df = analyzer.analyze_bets()
        # df = scraper.get_data()
    finally:
        analyzer.close()
        # scraper.close()
    print(df)
