# from scrapers.betflag import BetflagScraper
from single_bet_type_analyzer import SingleBetTypeAnalyzer
from dask.distributed import LocalCluster


def print_data(_d):
    print(f'{len(_d)} match')
    for x in _d:
        print(x)
        for y in _d[x]:
            print(y, ':', _d[x][y])


if __name__ == '__main__':
    cluster = LocalCluster(processes=False)
    # cluster = None
    analyzer = SingleBetTypeAnalyzer('calcio', '1x2', cluster=cluster)
    try:
        df = analyzer.analyze_bets()
    finally:
        analyzer.close()
    print(df)
