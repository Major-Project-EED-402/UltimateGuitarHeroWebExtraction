
import jl_io as io
from selenium import webdriver
from bs4 import BeautifulSoup
from functools import reduce
import time, os, random, uuid, pandas as pd

from jl_song_data import SongData

class ChordExtractor:

    def __init__(self, raw_html_output_directory):
        self.raw_html_output_directory = raw_html_output_directory
        self.driver = self.create_chrome_driver()
        self.first_time = True

        if not os.path.isdir(self.raw_html_output_directory):
            os.mkdir(self.raw_html_output_directory)