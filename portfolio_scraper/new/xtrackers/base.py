from typing import Dict

import pandas as pd
import requests

from portfolio_scraper.new.utils import CsvSettings
from portfolio_scraper.new.base import LISTINGS_COLUMNS, HOLDINGS_COLUMNS, Scraper


# TODO: use to test
HEADER = "ShareClass ISIN;Constituent ISIN;Constituent Name;Constituent Country;Constituent Currency ISO Code;Constituent Weighting;Constituent Rating;Constituent Main Exchange Name;Constituent Industry Classification Name"


class XTrackersScraper(Scraper):
    ISSUER: str = "XTrackers"
    LISTINGS_COLUMN_NAMES: Dict[LISTINGS_COLUMNS, str] = {
        "isin": "ISIN",
        "name": "Name",
        "internal_id": "ID",
        "ter": "TotalExpenseRatio",
    }
    HOLDINGS_COLUMN_NAMES: Dict[HOLDINGS_COLUMNS, str] = {
        "isin": "Constituent ISIN",
        "name": "Constituent Name",
        "weight": "Constituent Weighting",
        "sector": "Constituent Industry Classification Name",
        "country": "Constituent Country",
        "currency": "Constituent Currency ISO Code",
        "rating": "Constituent Rating",
    }

    LISTINGS_URL: str
    HOLDINGS_URL_TEMPLATE: str
    COOKIE: str

    CSV_SETTINGS: CsvSettings = {
        "separator": ";",
        "thousands": ",",
        "decimal": ".",
    }

    def get_raw_listings(self) -> pd.DataFrame:
        response = requests.post(
            self.LISTINGS_URL,
            json={
                "selectedTabIndex": 0,
                "totalReturnType": 0,
                "searchTerm": "",
                "filters": [],
            },
            headers={
                "cookie": self.COOKIE,
            },
        )
        response.raise_for_status()

        data = response.json()["values"]
        df = pd.DataFrame(data)
        return df

    def get_raw_holdings(self, isin: str) -> pd.DataFrame:
        url = self.HOLDINGS_URL_TEMPLATE.format(isin=isin)
        df = pd.read_csv(
            url,
            sep=self.CSV_SETTINGS["separator"],
            thousands=self.CSV_SETTINGS["thousands"],
            decimal=self.CSV_SETTINGS["decimal"],
        )
        return df

    def get_issuer_listings(self) -> pd.DataFrame:
        df = self.get_raw_listings()

        # Extract the name from the nested "ProductNameIsin" structure
        df["Name"] = df["ProductNameIsin"].apply(
            lambda x: x["ProductNameIsin_0"]["sortValue"]
        )

        # For each column, if the column is an object with a "sortValue" or "value" key, replace the column with the value of that key
        for column in df.columns:
            if df[column].dtype == "object":
                if (
                    df[column]
                    .apply(
                        lambda x: (
                            isinstance(x, dict) and ("sortValue" in x or "value" in x)
                        )
                    )
                    .any()
                ):
                    df[column] = df[column].apply(
                        lambda x: (
                            x["sortValue"]
                            if isinstance(x, dict)
                            and "sortValue" in x
                            and x["sortValue"] is not None
                            else x["value"]
                            if isinstance(x, dict)
                            and "value" in x
                            and x["value"] is not None
                            else x
                        )
                    )

        # Duplicate the "ID" column to "isin" for consistency with other scrapers
        df["ISIN"] = df["ID"]

        return df
