from collections import namedtuple

BetPrice = namedtuple('BetPrice', ['back_price', 'back_size', 'lay_price', 'lay_size'])
BetInfo = namedtuple('BetInfo', ['club1', 'club2', 'date',
                                 'site', 'sport', 'bet_type',
                                 'back_price', 'back_size', 'lay_price', 'lay_size'])
