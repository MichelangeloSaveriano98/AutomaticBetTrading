from mysql import connector
from database.database_login import username, password, host
from utility.bet_utility import BetInfo


class BetContainer:
    def __init__(self):
        self.conn = connector.connect(host=host,
                                      user=username,
                                      password=password,
                                      database='bets')
        self.c = self.conn.cursor()
        self.data = {}

    def find_match_id(self, match_tuple):
        sql = """select idmatch
        from `match`
        where club1=%s and
              club2=%s and
              date=%s
              """
        return self.c.execute(sql, match_tuple)

    def insert_match_into_database(self, match_tuple):
        sql = """INSERT INTO `bets`.`match` (`club1`, `club2`, `date`) 
                     VALUES (%s, %s, %s);"""
        self.c.execute(sql, match_tuple)
        self.conn.commit()

    def insert_bets_into_database(self, bet_info):
        sql = """INSERT INTO `bets`.`bet` 
            (`match_id`, `site`, `sport`, `bet_type`, `back_price`, `back_size`, `lay_price`, `lay_size`) 
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s);"""

    def update_bets(self, bets_list: list[BetInfo]):
        for bet_info in bets_list:
            match_id = self.find_match_id(bet_info[:3])
            if match_id is None:
                self.insert_match_into_database(bet_info[:3])
                match_id = self.find_match_id(bet_info[:3])


        pass
