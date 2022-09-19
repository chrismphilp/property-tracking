import time
import urllib.parse
import logging
import requests
import math
import re

import pandas as pd

from lxml import html
from parse import Parser
from fake_useragent import UserAgent

ua = UserAgent()


class ZooplaPropertiesForSale:
    headers = {'User-Agent': ua.random, 'Accept-Language': 'en-gb', 'Referer': 'https://www.google.com/'}

    def __init__(self, location_identifier: str,
                 min_price: int = 375_000,
                 max_price: int = 650_000,
                 page_size: int = 25,
                 radius_from_location: int = 0,
                 property_type: [str] = 'houses',
                 include_sstc: bool = False, ):
        self.parser = Parser()
        self.base_url = 'https://www.zoopla.co.uk/for-sale'
        self.location_identifier = location_identifier
        self.min_price = min_price
        self.max_price = max_price
        self.page_size = page_size
        self.radius_from_location = radius_from_location
        self.property_type = property_type
        self.include_sstc = include_sstc

        self.current_page = self._request(1)

    def parse_site(self):
        return self.process_results()

    def create_url(self, index: int = 2):
        url_vars = {
            "include_sold": str(self.include_sstc).lower(),
            "is_auction": "false",
            "is_shared_ownership": "false",
            "view_type": "list",
            "page_size": self.page_size,
            "price_max": self.max_price,
            "price_min": self.min_price,
            "radius": self.radius_from_location,
            "pn": index,
        }
        return "{}/{}/{}/?{}".format(self.base_url, self.property_type, self.location_identifier,
                                     urllib.parse.urlencode(url_vars))

    def _request(self, index):
        self.url = self.create_url(index)

        logging.info(f"Making request to {self.url}")

        r = requests.get(self.url, headers=self.headers)
        if r.status_code != 200:
            raise ValueError(f"Cannot make request to zoopla.co.uk. Returned status: {r.status_code} with error: {r.headers, r.content}")
        return r.content

    def process_results(self):
        no_of_pages = self.number_of_pages
        logging.info(f"Processing {no_of_pages} pages on {self.base_url} for {self.location_identifier}")

        results = self.process_page()

        for p in range(1, self.number_of_pages, 1):
            self.current_page = self._request(p + 1)
            results = pd.concat([results, self.process_page()])

        results["price"].replace(regex=True, inplace=True, to_replace=r"\D", value=r"")
        results["price"] = pd.to_numeric(results["price"])

        # Extract postcodes to a separate column:
        postcode_regex = r"\b([A-Za-z][A-Za-z]?[0-9][0-9]?[A-Za-z]?)\b"
        results["address"] = results["address"].astype(str)
        results["postcode"] = results["address"].str.extract(postcode_regex, expand=True)

        # Extract number of bedrooms from `type` to a separate column:
        no_of_bedroom_regex = r"\b([\d][\d]?)\b"
        no_of_bedrooms = results["type"].astype(str).str.extract(no_of_bedroom_regex, expand=True)
        if no_of_bedrooms is None:
            no_of_bedrooms = 1.0
        results["number_bedrooms"] = no_of_bedrooms
        results.loc[results["type"].astype(str).str.contains("studio", case=False), "number_bedrooms"] = 0
        results["number_bedrooms"] = pd.to_numeric(results["number_bedrooms"])

        # Extract the date the property was added on to rightmove
        ord_day_pattern = re.compile(r"(?<=\d)(st|nd|rd|th)")
        results["added_on"] = results["added_on"].astype(str).str.replace(ord_day_pattern, '')
        results["added_on"] = pd.to_datetime(results["added_on"], format="%d %b %Y")

        # Clean up annoying white spaces and newlines in `type` column:
        results["type"] = results["type"].astype(str).str.strip("\n").astype(str).str.strip()

        results["search_datetime"] = results["search_datetime"].astype('str')
        results["added_on"] = results["added_on"].astype('str')

        results.sort_values("added_on", ascending=False, inplace=True)

        time.sleep(1)

        return results

    def process_page(self):
        tree = html.fromstring(self.current_page)

        base = "https://www.zoopla.co.uk"
        xp_titles = """//div[@data-testid="search-result"]
        //h2[@data-testid="listing-title"]/text()"""
        xp_prices = """//div[@data-testid="search-result"]
        //div[@data-testid="listing-price"]
        //p[contains(text(), '£')]/text()"""
        xp_addresses = """//div[@data-testid="search-result"]
        //p[@data-testid="listing-description"]/text()"""
        xp_weblinks = """//div[@data-testid="search-result"]
        //a[@data-testid="listing-details-link"]/@href"""
        xp_added_on = """//div[@data-testid="search-result"]
        //span[@data-testid="date-published"]/text()[last()]"""

        # Create data lists from xpaths:
        price = tree.xpath(xp_prices)
        if price is None:
            price = '0'
        titles = tree.xpath(xp_titles)
        addresses = tree.xpath(xp_addresses)
        weblinks = [f"{base}{tree.xpath(xp_weblinks)[w]}" for w in range(len(tree.xpath(xp_weblinks)))]
        added_on = tree.xpath(xp_added_on)

        data = [price, titles, addresses, weblinks, added_on]
        return self.parser.create_data_frame(data)

    @property
    def number_of_pages(self):
        tree = html.fromstring(self.current_page)
        xpath = """//main[@data-testid="search-content"]
        //p[@data-testid="total-results"]/text()"""
        pattern = re.compile(r"""[0-9]+""", re.VERBOSE)
        pages = pattern.findall(str(tree.xpath(xpath)))
        no_of_pages = (pages or [0])[0]
        return math.ceil(int(no_of_pages) / self.page_size)
