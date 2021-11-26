import datetime as dt
import urllib.parse
import logging
import requests
import math
from lxml import html
import pandas as pd

from parse import Parser


class RightmovePropertiesForSale:

    def __init__(self, location_identifier: str,
                 min_price: int = 250_000,
                 max_price: int = 475_000,
                 radius_from_location: float = 0,
                 property_type: [str] = 'houses',
                 include_sstc: bool = True):
        self.parser = Parser()
        self.base_url = 'https://www.rightmove.co.uk/property-for-sale/find.html'
        self.location_identifier = location_identifier
        self.min_price = min_price
        self.max_price = max_price
        self.radius_from_location = radius_from_location
        self.property_type = property_type
        self.include_sstc = include_sstc

        self.current_page = self._request(0)

    def parse_site(self):
        return self.process_results()

    def create_url(self, index: int = 0):
        url_vars = {
            "index": index,
            "locationIdentifier": self.location_identifier,
            "minPrice": self.min_price,
            "maxPrice": self.max_price,
            "radius": self.radius_from_location,
            "primaryDisplayPropertyType": self.property_type,
            "includeSSTC": self.include_sstc,
        }
        return "{}?{}".format(self.base_url, urllib.parse.urlencode(url_vars))

    def _request(self, index):
        self.url = self.create_url(index)
        r = requests.get(self.url)
        if r.status_code != 200:
            raise ValueError('Cannot make request to rightmove.co.uk')
        return r.content

    def process_results(self):
        no_of_pages = self.number_of_pages
        logging.info(f"Processing {no_of_pages} pages on {self.base_url} for {self.location_identifier}")

        results = self.process_page()

        for p in range(1, no_of_pages, 1):
            current_index = p * 24

            self.current_page = self._request(current_index)
            results = pd.concat([results, self.process_page()])

        results["price"].replace(regex=True, inplace=True, to_replace=r"\D", value=r"")
        results["price"] = pd.to_numeric(results["price"])

        # Extract postcodes to a separate column:
        postcode_regex = r"\b([A-Za-z][A-Za-z]?[0-9][0-9]?[A-Za-z]?)\b"
        results["address"] = results["address"].astype(str)
        results["postcode"] = results["address"].astype(str).str.extract(postcode_regex, expand=True)

        # Extract number of bedrooms from `type` to a separate column:
        no_of_bedroom_regex = r"\b([\d][\d]?)\b"
        results["number_bedrooms"] = results["type"].astype(str).str.extract(no_of_bedroom_regex, expand=True)
        results.loc[results["type"].str.contains("studio", case=False), "number_bedrooms"] = 0
        results["number_bedrooms"] = pd.to_numeric(results["number_bedrooms"])

        # Extract the date the property was added on to rightmove
        date_added_regex = r"\b([0-9]{1,2}\/[0-9]{1,2}\/[0-9]{1,4})\b"
        today = dt.datetime.now().strftime("%d/%m/%Y")
        yesterday = (dt.datetime.today() - dt.timedelta(days=1)).strftime("%d/%m/%Y")
        results["added_on"] = results["added_on"].str.replace('today', today)
        results["added_on"] = results["added_on"].str.replace('yesterday', yesterday)
        results["added_on"] = results["added_on"].astype(str).str.extract(date_added_regex, expand=True)

        # Clean up annoying white spaces and newlines in `type` column:
        results["type"] = results["type"].str.strip("\n").str.strip()

        results["search_datetime"] = results["search_datetime"].astype('str')

        results["added_on"] = results["added_on"].astype('str')

        results.sort_values("added_on", ascending=False, inplace=True)

        return results

    def process_page(self):
        tree = html.fromstring(self.current_page)

        base = "https://www.rightmove.co.uk"
        xp_titles = """//div[@class="propertyCard-details"]\
                //a[@class="propertyCard-link"]\
                //h2[@class="propertyCard-title"]/text()"""
        xp_prices = """//div[@class="propertyCard-priceValue"]/text()"""
        xp_addresses = """//address[@class="propertyCard-address"]//span/text()"""
        xp_weblinks = """//div[@class="propertyCard-details"]//a[@class="propertyCard-link"]/@href"""
        xp_added_on = """//div[@class="propertyCard-detailsFooter"]//span[@class="propertyCard-branchSummary-addedOrReduced"]/text()"""

        # Create data lists from xpaths:
        price = tree.xpath(xp_prices)
        titles = tree.xpath(xp_titles)
        addresses = tree.xpath(xp_addresses)
        weblinks = [f"{base}{tree.xpath(xp_weblinks)[w]}" for w in range(len(tree.xpath(xp_weblinks)))]
        added_on = tree.xpath(xp_added_on)

        data = [price, titles, addresses, weblinks, added_on]
        return self.parser.create_data_frame(data)

    @property
    def number_of_pages(self):
        tree = html.fromstring(self.current_page)
        xpath = """//span[@class="searchHeader-resultCount"]/text()"""
        return math.ceil(int(tree.xpath(xpath)[0].replace(",", "")) / 24)
