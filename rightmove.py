import datetime as dt
import urllib.parse
import requests
import math
from lxml import html
import pandas as pd


class RightmovePropertiesForSale:

    def __init__(self, location_identifier: str,
                 min_price: int = 250_000,
                 max_price: int = 10_000_000,
                 radius_from_location: int = 0,
                 property_type: [str] = 'houses',
                 include_sstc: bool = False):
        self.base_url = 'https://www.rightmove.co.uk/property-for-sale/find.html'
        self.location_identifier = location_identifier
        self.min_price = min_price
        self.max_price = max_price
        self.radius_from_location = radius_from_location
        self.property_type = property_type
        self.include_sstc = include_sstc

        self.current_page = self._request(0)

        try:
            current_csv = pd.read_csv('rightmove-houses.csv')
        except:
            current_csv = None

        self.process_results(current_csv).to_csv('rightmove-houses.csv', index=False)

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

    @property
    def number_of_pages(self):
        tree = html.fromstring(self.current_page)
        xpath = """//span[@class="searchHeader-resultCount"]/text()"""
        return math.ceil(int(tree.xpath(xpath)[0].replace(",", "")) / 24)

    def process_results(self, current_csv):
        results = self.process_page()

        for p in range(1, self.number_of_pages, 1):
            current_index = p * 24

            self.current_page = self._request(current_index)
            results = pd.concat([results, self.process_page()])

        results["price"].replace(regex=True, inplace=True, to_replace=r"\D", value=r"")
        results["price"] = pd.to_numeric(results["price"])

        # Extract postcodes to a separate column:
        postcode_regex = r"\b([A-Za-z][A-Za-z]?[0-9][0-9]?[A-Za-z]?)\b"
        results["address"] = results["address"].astype(str) + "±"
        results["postcode"] = results["address"].astype(str).str.extract(postcode_regex, expand=True)

        # Extract number of bedrooms from `type` to a separate column:
        no_of_bedroom_regex = r"\b([\d][\d]?)\b"
        results["number_bedrooms"] = results["type"].astype(str).str.extract(no_of_bedroom_regex, expand=True)
        results.loc[results["type"].str.contains("studio", case=False), "number_bedrooms"] = 0
        results["number_bedrooms"] = pd.to_numeric(results["number_bedrooms"])

        # Clean up annoying white spaces and newlines in `type` column:
        results["type"] = results["type"].str.strip("\n").str.strip()

        if current_csv is None:
            return results
        else:
            current_csv = pd.concat([current_csv, results])
            current_csv.drop_duplicates(subset=current_csv.columns.difference(['search_datetime']), keep="first", inplace=True)

        return current_csv

    def process_page(self):
        tree = html.fromstring(self.current_page)

        base = "https://www.rightmove.co.uk"
        xp_titles = """//div[@class="propertyCard-details"]\
                //a[@class="propertyCard-link"]\
                //h2[@class="propertyCard-title"]/text()"""
        xp_prices = """//div[@class="propertyCard-priceValue"]/text()"""
        xp_addresses = """//address[@class="propertyCard-address"]//span/text()"""
        xp_weblinks = """//div[@class="propertyCard-details"]//a[@class="propertyCard-link"]/@href"""

        # Create data lists from xpaths:
        price_pcm = tree.xpath(xp_prices)
        titles = tree.xpath(xp_titles)
        addresses = tree.xpath(xp_addresses)
        weblinks = [f"{base}{tree.xpath(xp_weblinks)[w]}" for w in range(len(tree.xpath(xp_weblinks)))]

        data = [price_pcm, titles, addresses, weblinks]
        return self.create_data_frame(data)

    @staticmethod
    def create_data_frame(data: [str]):
        columns = ["price", "type", "address", "url"]

        temp_df = pd.DataFrame(data)
        temp_df = temp_df.transpose()

        temp_df.columns = columns
        temp_df = temp_df[temp_df["address"].notnull()]

        temp_df["search_datetime"] = dt.datetime.now().strftime("%I:%M%p on %B %d, %Y")

        return temp_df
