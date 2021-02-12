from betfair import BetfairBettor
from betflag import BetflagBettor


def create_bettor(site_name, sport='calcio', feature='1x2'):
    classes = {'betfair': BetfairBettor,
               'betflag': BetflagBettor}

    if site_name not in classes:
        return None
    return classes[site_name](sport=sport, feature=feature)
