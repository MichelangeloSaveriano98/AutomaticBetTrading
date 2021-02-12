from abc import ABC


class SiteBettor(ABC):
    def get_data(self):
        pass

    def bet(self):
        pass

    def close(self):
        pass
