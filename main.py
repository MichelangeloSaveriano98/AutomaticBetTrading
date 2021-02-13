from betfair import BetfairBettor
from betflag import BetflagBettor
from bettors import create_bettor
# drivers.switch_to.window(drivers.window_handles[1])


def print_data(_d):
    print(f'{len(_d)} match')
    for x in _d:
        print(x)
        for y in _d[x]:
            print(y, ':', _d[x][y])


if __name__ == '__main__':
    # bettor = create_bettor('betfair')
    # bettor = BetfairBettor(n_drivers=1, max_pages=10, feature='12', sport='tennis')
    bettor = BetflagBettor(feature='12', sport='tennis')
    data = bettor.get_data()
    print_data(data)
    # df.to_csv('./data/betfair.csv')
    bettor.close()

