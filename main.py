from selenium import webdriver
from webdriver_manager.firefox import GeckoDriverManager
from bs4 import BeautifulSoup
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.common.by import By
import datetime
import time
import pandas as pd
from collections import defaultdict

# driver.switch_to.window(driver.window_handles[1])

if __name__ == '__main__':
    betfair_url = 'https://www.betfair.it/exchange/plus/it/calcio-scommesse-1/'

    driver = webdriver.Firefox(executable_path=GeckoDriverManager().install())
    driver.get(betfair_url)
    # Accept cookies
    WebDriverWait(driver, timeout=10).until(
        expected_conditions.element_to_be_clickable((By.XPATH, '//*[@id="onetrust-accept-btn-handler"]'))).click()
    n_pages = number_of_pages(driver)
    print(f'N pages: {n_pages}')
    df = pd.DataFrame.from_dict(parse_content(driver))
    for i in range(2, n_pages+1):
        driver.get(betfair_url + str(i))
        time.sleep(5)
        df = df.append(pd.DataFrame.from_dict(parse_content(driver)), ignore_index=True)
    print(df)
    df.to_csv('./data/betfair.csv')


