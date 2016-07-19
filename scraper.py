#!/usr/bin/env python

from spacy.en import English
from selenium import webdriver
from pyvirtualdisplay import Display
from bs4 import BeautifulSoup
import requests
import re
import numpy as np

class Scraper:
    """
    Base class for scraping sites with Selenium and Beautiful Soup
    """
    def __init__(self, driver_path):
        self.display = Display(visible=0, size=(1920, 1080))
        self.display.start()
        # Firefox 47+ is incomparible with Selenium 2.53+; use Chrome
        self.driver = webdriver.Chrome(driver_path)
        self.nlp = English()

    def lemmatize(self, texts):
        """
        Lemmatizes each word, i.e. lower case and no inflection
        """
        lems = lambda x: [w.lemma_ for w in self.nlp(x) if not (w.is_stop or w.is_punct)]

        if type(texts) is str:
            text_lemmas = lems(text)

        elif type(texts) is list:
            text_lemmas = []
            for text in texts:
                if type(text) is str: 
                    text_lemmas.append(lems(text))

                elif type(text) is list:
                    text_item_lemmas = []
                    for text_item in text:
                        text_item_lemmas.extend(lems(text_item))
                    text_lemmas.append(text_item_lemmas)
 
                else:
                    print(type(text), text)
                    raise TypeError('Lemmatize list items are not strings or lists')
        else:
            print(type(texts), texts)
            raise TypeError('Lemmatize input is not a string or list')

        return text_lemmas

    def parse_url(self, url, tag, attrs=None, target=None, regex=None):
        """
        Retrieves a tag in a url's source, optionally extracting content
        """
        try:
            response = requests.get(url)
            soup = BeautifulSoup(response.content, 'lxml')
            parse = soup.find(tag, attrs)

            # Optionally extract a target attribute
            if target:
                parse = parse[target]

            # Optionally apply a regex
            if regex:
                parse = re.findall(regex, str(parse))

        except:
            parse = None

        return parse

    def write(self, write_items, write_files):
        """
        Writes a string to file or a list of strings separated by newlines
        """
        files = []
        for f in write_files:
            files.append(open(f, 'w'))

        for i,item in enumerate(write_items):
            if type(item) is str:
                files[i].write(item + '\n')
            elif type(item) is list:
                for row in item:
                    files[i].write(row + '\n')
            else:
                print(type(item), item)
                raise TypeError('Write input is not a string or list')

        for f in files:
            f.close()
