from typing import Literal, Dict

import pandas as pd
import requests
import numpy as np

from ..base import LISTINGS_COLUMNS, EtfBaseScraper, HOLDINGS_COLUMNS
from ..utils import (
    CsvSettings,
    rename_pandas_columns,
)


ISHARES_HOLDINGS_COLUMNS = Literal[
    "ticker",
    "name",
    "sector",
    "asset_class",
    "market_value",
    "weight",
    "book_value",
    "nominal",
    "price",
    "geographic_area",
    "exchange_rate",
    "market_currency",
]


class ISharesBaseScraper(EtfBaseScraper):
    ISSUER: str = "IShares"
    LISTINGS_COLUMN_NAMES: Dict[LISTINGS_COLUMNS, str] = {
        "isin": "isin",
        "name": "fundName",
        "internal_id": "portfolioId",
        "ter": "ter.r",
    }
    HOLDINGS_COLUMN_NAMES: Dict[HOLDINGS_COLUMNS, ISHARES_HOLDINGS_COLUMNS] = {
        "ticker": "ticker",
        "name": "name",
        "weight": "weight",
        "sector": "sector",
        "type": "asset_class",
        "country": "geographic_area",
        "currency": "market_currency",
    }

    WEIGHT_SCALE = 0.01  # Percentage

    LISTINGS_URL: str
    HOLDINGS_URL_TEMPLATE: str
    LOCALE_COLUMN_NAMES: Dict[str, ISHARES_HOLDINGS_COLUMNS]

    CSV_SETTINGS: CsvSettings = {
        "separator": ",",
        "thousands": ".",
        "decimal": ",",
    }

    def get_raw_listings(self) -> pd.DataFrame:
        response = requests.get(self.LISTINGS_URL)
        response.raise_for_status()
        df = pd.json_normalize(response.json().values())
        return df

    def get_raw_holdings(self, product_id: str) -> pd.DataFrame:
        # Download the CSV file from the URL and read it into a DataFrame
        url = self.HOLDINGS_URL_TEMPLATE.format(product_id=product_id)
        df = pd.read_csv(
            url,
            sep=self.CSV_SETTINGS["separator"],
            thousands=self.CSV_SETTINGS["thousands"],
            decimal=self.CSV_SETTINGS["decimal"],
            skiprows=2,
            header=0,
        )

        # Replace field that's entirely space (or empty) with NaN
        df = df.replace(r"^\s*$", np.nan, regex=True)

        # Drop rows where all values are NaN
        df = df.dropna(how="all")

        return df

    def get_issuer_holdings(self, product_id: str) -> pd.DataFrame:
        df = self.get_raw_holdings(product_id)
        df = rename_pandas_columns(df, self.LOCALE_COLUMN_NAMES)
        return df
