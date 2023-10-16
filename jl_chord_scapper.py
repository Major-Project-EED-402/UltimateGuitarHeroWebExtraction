
import jl_io as io
from bs4 import BeautifulSoup
from functools import reduce
import time, os, random, uuid, pandas as pd

from selenium import webdriver
from selenium.webdriver.common.by import By

from jl_song_data import SongData

class ChordExtractor:

    def __init__(self, raw_html_output_directory):
        self.raw_html_output_directory = raw_html_output_directory
        self.driver = self.instantiate_chrome_driver()
        self.first_time = True

        if not os.path.isdir(self.raw_html_output_directory):
            os.mkdir(self.raw_html_output_directory)
    
    def instantiate_chrome_driver(self):
        driver = webdriver.Chrome()
        return driver
    
    def execute_CTA_accept_cookies(self):
        try:
            CTA_button = self.driver.find_element(By.XPATH, '//button[contains(text(), "thanks")]')
            CTA_button.click()
        except:
            print('cookies banner not found in site')

    def get_chord_span_element(self,url):
        self.driver.get(url)
        
        if self.driver.page_source == '<html><head></head><body></body></html>':
            raise Exception('Denegation error')

        if self.first_time:
            self.click_on_accept_cookies()
            self.first_time = False

        soup = BeautifulSoup(self.driver.page_source, 'lxml')

        article = soup.findAll('article')[3]
        
        return article.findAll('span', {"style":"color: rgb(0, 0, 0);"})
        
    def extract_song_data(self, url):
        chords_span_elements = self.get_chord_span_element(url)

        chords = [span.decode_contents() for span in chords_span_elements]
        song_uuid = str(uuid.uuid4())

        with open(f"{self.raw_html_output_directory}/{song_uuid}.html", "w") as file: # URL pattern needed to extract paginated data
            file.write(self.driver.page_source )
            
        info = {
            "url":url,
            "chords":chords,
            "uuid":song_uuid
        }
        
        return info