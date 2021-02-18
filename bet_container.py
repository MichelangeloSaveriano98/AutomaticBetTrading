from mysql import connector
from database.database_login import username, password, host
from utility.bet_utility import BetInfo, BetPrice
from utility.bet_utility import match_tuple_size as mts, bet_price_size as bps
from collections import defaultdict
import pandas as pd


# import numpy as np


def bet_tree():
    return defaultdict(bet_tree)


class BetContainer:
    def __init__(self):
        self.conn = connector.connect(host=host,
                                      user=username,
                                      password=password,
                                      database='bets')
        self.c = self.conn.cursor()
        self.data = bet_tree()  # data[MatchTuple][bet_type][site] = BetPrice
        self._df = pd.DataFrame(columns=BetInfo._fields)

    def find_match_id(self, match_tuple):
        sql = """select idmatch
        from `match`
        where club1=%s and
              club2=%s and
              date=%s and
              sport=%s
              """
        self.c.execute(sql, match_tuple)
        result = self.c.fetchone()
        if result:
            return result[0]
        return None

    def insert_match_into_database(self, match_tuple):
        sql = """INSERT INTO `bets`.`match` (`club1`, `club2`, `date`, `sport`) 
                     VALUES (%s, %s, %s, %s);"""
        self.c.execute(sql, match_tuple)
        self.conn.commit()

    def insert_bets_into_database(self, bet_info: BetInfo):
        sql = """INSERT INTO `bets`.`bet` 
            (`match_id`, `site`, `bet_type`, `back_price`, `back_size`, `lay_price`, `lay_size`) 
            VALUES (%s, %s, %s, %s, %s, %s, %s);"""
        match_id = self.find_match_id(bet_info[:mts])
        if match_id is None:
            self.insert_match_into_database(bet_info[:mts])
            match_id = self.find_match_id(bet_info[:mts])
        val = (match_id,) + bet_info[mts:]
        self.c.execute(sql, val)
        self.conn.commit()

    def update_bets(self, bets_list: list[BetInfo]):
        for bet_info in bets_list:
            # Insert bet into database
            self.insert_bets_into_database(bet_info)
            # self.data[bet_info[:mts]][bet_info.bet_type][bet_info.site] = BetPrice(*bet_info[-bps:])
            # Remove old bets from the dataframe
            self._df = self._df[~(self._df[list(BetInfo._fields[-bps:])] == bet_info[-bps:]).all(axis=1)]
            # Calculate the next bet index
            new_index = (self._df.index.max() + 1) if len(self._df) > 0 else 1
            self._df.loc[new_index] = bet_info

    def search_bets_by_bet_type(self, bet_type: str, return_only_multiple_bets=True):
        df = self._df[self._df.bet_type == bet_type]
        return {group_idx: group_df.drop(columns=list(BetInfo._fields[:mts]) + ['bet_type'])
                for group_idx, group_df in df.groupby(list(BetInfo._fields[:mts]))
                if (not return_only_multiple_bets) or len(group_df) > 1}

    @property
    def df(self):
        return self._df
