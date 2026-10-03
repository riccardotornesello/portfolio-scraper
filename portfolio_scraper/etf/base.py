from abc import ABC, abstractmethod
from typing import Literal, Dict

import pandas as pd

from .utils import rename_pandas_columns


LISTINGS_COLUMNS = Literal[
    "isin",
    "name",
    "internal_id",
    "ter",
]

HOLDINGS_COLUMNS = Literal[
    "ticker",
    "isin",
    "name",
    "weight",
    "sector",
    "type",
    "country",
    "currency",
    "rating",
]


class EtfBaseScraper(ABC):
    """
    Base class for all scrapers. Provides common methods and attributes.
    """

    ISSUER: str
    LISTINGS_COLUMN_NAMES: Dict[LISTINGS_COLUMNS, str]
    HOLDINGS_COLUMN_NAMES: Dict[HOLDINGS_COLUMNS, str]

    @abstractmethod
    def get_raw_listings(self) -> pd.DataFrame:
        """
        Fetch the raw listings data from the source. Must be implemented by subclasses.
        """
        pass

    @abstractmethod
    def get_raw_holdings(self, isin: str) -> pd.DataFrame:
        """
        Fetch the raw holdings data for a given ISIN from the source. Must be implemented by subclasses.
        """
        pass

    def get_issuer_listings(self) -> pd.DataFrame:
        """
        Fetch the listings and return a processed DataFrame with a format specific to the issuer.
        """
        return self.get_raw_listings()

    def get_issuer_holdings(self, isin: str) -> pd.DataFrame:
        """
        Fetch the holdings and return a processed DataFrame with a format specific to the issuer.
        """
        return self.get_raw_holdings(isin)

    def get_listings(self) -> pd.DataFrame:
        """
        Fetch the listings and return a standard DataFrame.
        """
        df = self.get_issuer_listings()
        df = rename_pandas_columns(df, self.LISTINGS_COLUMN_NAMES, reverse_mapping=True)
        return df

    def get_holdings(self, isin: str) -> pd.DataFrame:
        """
        Fetch the holdings and return a standard DataFrame.
        """
        df = self.get_issuer_holdings(isin)
        df = rename_pandas_columns(df, self.HOLDINGS_COLUMN_NAMES, reverse_mapping=True)
        return df
