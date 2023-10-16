
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

class LinkExtractor:
    BASE_URL = "https://www.ultimate-guitar.com/explore?&type[]=Chords"

    def __init__(self):
        self.driver = self.initiate_chrome_driver()
        self.first_time = True
    
    def initiate_chrome_driver(self):
        driver = webdriver.Chrome()
        return driver
    
    def execute_CTA_accept_cookies(self):
        try:
            CTA_button = self.driver.find_element(By.XPATH, '//button[contains(text(), "thanks")]')
            CTA_button.click()
        except:
            print('cookies banner not found in site')
    
    def link_to_song_dict(self,link, genre, decade):
        return {
            "name": link.contents[0],
            "url": link['href'],
            "genre": genre["name"],
            "decade": decade["name"]
        }
    
    def get_links_single_page(self,genreFilter,decadeFilter, pageFilter):
        self.driver.get(f'{self.BASE_URL}{genreFilter}{decadeFilter}{pageFilter}')
        
        if self.driver.page_source == '<html><head></head><body></body></html>':
            raise Exception('Denegation error')

        if self.first_time:
            self.click_on_accept_cookies()
            self.first_time = False

        soup = BeautifulSoup(self.driver.page_source, 'lxml')

        return soup.findAll('a', {"class":"_2KJtL _1mes3 kWOod"})
    
    def get_all_filter_song_links(self,genreFilter,decadeFilter, first_page, last_page):
        list_of_list = [self.get_links_single_page(genreFilter, decadeFilter, f'&page={page}')
                  for page in range(first_page,last_page + 1)]
        
        return reduce(lambda list1, list2: [*list1, *list2], list_of_list)
    
    def get_all_songs(self, genre, decade, starting_page, ending_page):
        links = self.get_all_filter_song_links(genre['pattern'],decade['pattern'], starting_page, ending_page)
        result = [ self.link_to_song_dict(link,genre,decade) for link in links]
        
        return result


class ChordScraper:
    def __init__(self, linkExtractor, chordExtractor, genres, decades, song_data):
        self.linkExtractor = linkExtractor
        self.chordExtractor = chordExtractor
        self.genres = genres
        self.decades = decades
        self.song_data = song_data
        
        self.combinations = []

        for decade in self.decades:
            for genre in self.genres:
                    self.combinations.append( {"decade": decade, "genre": genre})
        
    def extract(self, first_page, last_page):      
        startIndex = 1
        
        return self.extract_from(startIndex, first_page, last_page)
    
    def extract_from(self, startIndexBase1,first_page, last_page):    
        for index, combination in enumerate(self.combinations[startIndexBase1 - 1:]):
            new_extracted_songs = []
            genre = combination["genre"]
            decade = combination["decade"]
            
            if self.song_data.has_genre_and_decade(genre["name"], decade["name"]):
                print(f'{genre["name"]},{decade["name"]} already extracted')
                continue
            
            song_basic_data_array = []          
            try:
                song_basic_data_array = self.linkExtractor.get_all_songs(genre,decade, first_page, last_page)
                      
                for basic_data in song_basic_data_array:
                    self.song_data.add_basic_data(basic_data)
                      
                new_extracted_songs = [self.extract_song_data(index,song) for index,song in enumerate(new_extracted_songs)]
            except Exception as e: 
                print(f'Error in ({genre["name"]},{decade["name"]})')
                raise e
            
            for index,song in enumerate(song_basic_data_array):
                try:
                    self.extract_song_data(index,song)
                except Exception as e: 
                    print(f'Error in "{song["name"]}"')
                    raise e
            
            number_of_songs = len(self.song_data.df)
            print(f'Extracted {index+startIndexBase1} of {len(self.combinations)} ({genre["name"]},{decade["name"]}). {number_of_songs} in total')  
        
    def extract_song_data(self,index,song): 
        if self.song_data.has_chords(song["url"]):
            print(f'Song {index}. "{song["name"]}" already extracted')  
            return
      
        song_details = self.chordExtractor.extract_song_data(song["url"])           
        self.song_data.add_details(song_details)
        print(f'Extracted data from song {index}. "{song["name"]}"')