#!/usr/bin/env python

from mtp import MTPScraper
import json

# Instantiate scraper class
chrome_path = '/home/gshine/Documents/Utilities/chromedriver'
mtp = MTPScraper(chrome_path)

# Get urls by crawling user IDs
user_IDs = list(range(1,35870))
# Output file name
users_file_name = 'MTP.txt'

place_IDs = mtp.crawl(user_IDs)
mtp.format_store(user_IDs, place_IDs, file_name)

place_names = mtp.get_names()
names_file_name = 'Name_Mapping.json'
with open(names_file_name, 'w') as f:
    json.dump(place_names, f)

place_coords = mtp.get_coords(place_names)
coords_file_name = 'Coord_Mapping.json'
with open(coords_file_name, 'w') as f:
    json.dump(place_coords, f)
