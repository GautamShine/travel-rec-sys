#!/usr/bin/env python

from bs4 import BeautifulSoup
from scraper import Scraper
from selenium.webdriver.common.keys import Keys
import requests
import re
from geopy.geocoders import Nominatim

class MTPScraper(Scraper):
    """
    Derived class for scraping MostTraveledPeople visit lists
    """
    def __init__(self, chrome_path):
        super(MTPScraper, self).__init__(chrome_path)

    def crawl(self, user_IDs):
        """
        Returns a list of list of place IDs for each user ID
        """
        # MTP profiles
        place_IDs = []
        base_url = 'http://mosttraveledpeople.com/My-World-Text.php?id='

        for user_ID in user_IDs:
            try:
                resp = requests.get(base_url + str(user_ID))
                soup = BeautifulSoup(resp.content, 'lxml')

                # Gets all fields with checked boxes
                parse = soup.find_all(checked=True)

                # Extracts place ID and converts them to ints
                place_IDs.append([int(x['name'][1:]) for x in parse])

            except:
                # Add falsy value to maintain index correspondence
                place_IDs.append(None)
                print('Failed on user ID: ' + str(user_ID))

        return place_IDs

    def get_names(self):
        """
        Returns the mapping from place IDs to names
        """
        base_url = 'http://mosttraveledpeople.com/My-World-Text.php?id=1'
        resp = requests.get(base_url)
        soup = BeautifulSoup(resp.content, 'lxml')
        parse = soup.find_all('a')[51:]

        names = {}
        for link in parse:
            parts = re.split('=|&|\"', str(link))
            names[parts[3]] = parts[5]

        return names

    def get_coords(self, place_names):
        """
        Returns the mapping from place IDs/names to coords
        """
        geolocator = Nominatim()
        coords = {}
        for ID in place_names:
            name = place_names[ID]
            try:
                coord = geolocator.geocode(place_names[ID])[-1]
            except:
                print(name)
                coord = None
            coords[ID] = coord
            coords[name] = coord

        return coords

    def format_store(self, user_IDs, place_IDs, file_name):
        """
        Write to file with each row containing one user ID (first item)
        and the list place IDs for that user, all comma separated
        """
        assert len(user_IDs) == len(place_IDs)

        # Rows to be written into output
        write_rows = []
        for i, user in enumerate(user_IDs):
            # Only include users with at least one visit
            if place_IDs[i]:
                write_rows.append(str(user) + ', ' + str(place_IDs[i])[1:-1])

        # Convert to lists because base class writes in batches
        self.write([write_rows], [file_name])
