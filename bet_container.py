from mysql import connector
from database.database_login import username, password, host
from utility.bet_utility import BetInfo, BetPrice
from utility.bet_utility import match_tuple_size as mts, bet_price_size as bps
from collections import defaultdict
import pandas as pd
from utility.bet_utility import is_equal_match
from utility.string_utility import simpler_club_name
from dask.distributed import Client


def find_match_index(matches_df, match):
    for i in matches_df.index[::-1]:
        if is_equal_match(match, tuple(matches_df.loc[i])):
            # Return index
            return i
    return None


class BetContainer:
    def __init__(self, cluster=None):
        self.conn = connector.connect(host=host,
                                      user=username,
                                      password=password,
                                      database='bets')
        # Create a dask client
        if cluster is not None:
            self.client = Client(cluster)
        else:
            self.client = Client(processes=False)
        self.c = self.conn.cursor()
        self._df = pd.DataFrame(columns=['match_id'] + list(BetInfo._fields[mts:]))
        self.matches = pd.DataFrame(columns=BetInfo._fields[:mts])

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

    # def update_matches(self, new_match):
    #     idx = find_match_index(
    #                       self.matches[(self.matches.date == new_match[2]) & (self.matches.sport == new_match[3])],
    #                            new_match)
    #     if idx is not None:
    #         self.matches.loc[idx, ['club1', 'club2']] = [
    #             simpler_club_name(new_match[0], self.matches.loc[idx, 'club1']),
    #             simpler_club_name(new_match[1], self.matches.loc[idx, 'club2'])
    #         ]
    #     # If it's not present in matches insert the new match
    #     new_index = len(self.matches.index)
    #     self.matches.loc[new_index] = new_match
    #     # Then return its index
    #     return new_index

    def update_matches(self, matches):
        # Remove duplicates from matches
        matches = list(dict.fromkeys(matches))
        # Find the matches index
        futures = [self.client.submit(find_match_index,
                                      self.matches[(self.matches.date == match[2]) & (self.matches.sport == match[3])],
                                      match) for match in matches]
        ids = [future.result() for future in futures]

        # Update the matches dataframe
        for i in range(len(matches)):
            idx, match = ids[i], matches[i]
            if idx is not None:
                self.matches.loc[idx, ['club1', 'club2']] = [
                    simpler_club_name(match[0], self.matches.loc[idx, 'club1']),
                    simpler_club_name(match[1], self.matches.loc[idx, 'club2'])
                ]
            else:
                idx = find_match_index(self.matches[(self.matches.date == match[2]) & (self.matches.sport == match[3])],
                                       match)
                if idx is not None:
                    self.matches.loc[idx, ['club1', 'club2']] = [
                        simpler_club_name(match[0], self.matches.loc[idx, 'club1']),
                        simpler_club_name(match[1], self.matches.loc[idx, 'club2'])
                    ]
                else:
                    # If it's not present in matches insert the new match
                    new_index = len(self.matches.index)
                    self.matches.loc[new_index] = match
                    idx = new_index
                ids[i] = idx
        # Then return the ids
        return dict(zip(matches, ids))

    def update_bets(self, bets_list: list[BetInfo]):
        # Remove empty bets
        bets_list = list(filter(lambda bet: bet.back_price != 0 and bet.lay_price != 0 and bet.club1 and bet.club2 and bet.date == '2021-03-07',
                                bets_list))
        matches_id = self.update_matches([bet[:mts] for bet in bets_list])
        # Transform bets list
        for bet_info in bets_list:
            match_id = matches_id[bet_info[:mts]]
            # Insert bet into database
            # self.insert_bets_into_database(bet_info)
            # self.data[bet_info[:mts]][bet_info.bet_type][bet_info.site] = BetPrice(*bet_info[-bps:])

            # Remove old bets from the dataframe
            # self._df = self._df[~(
            #         (self._df.match_id == match_id) &
            #         (self._df.site == bet_info.site) &
            #         (self._df.bet_type == bet_info.bet_type)
            # )]

            # Calculate the next bet index
            new_index = len(self._df)  # (self._df.index.max() + 1) if len(self._df) > 0 else 1
            self._df.loc[new_index] = (match_id,) + bet_info[mts:]

    def search_bets_by_bet_type(self, bet_type: str, return_only_multiple_bets=True):
        df = self._df[self._df.bet_type == bet_type]
        return {tuple(self.matches.loc[group_idx]): group_df.drop(columns=['match_id', 'bet_type'])
                for group_idx, group_df in df.groupby('match_id')
                if (not return_only_multiple_bets) or len(group_df) > 1}

    @property
    def df(self):
        return self._df
