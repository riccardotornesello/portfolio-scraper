from abc import ABC, abstractmethod
from typing import Literal, Dict

import pandas as pd

from ..utils.asset_class import AssetClass
from ..utils.country import gen_country_to_alpha_2_map
from ..utils.sector import SECTORS_MAP, Sector
from .utils import map_values, rename_pandas_columns


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

    # Normalisation of the holdings values to the standard format
    WEIGHT_SCALE: float = 1
    """Factor to convert the issuer's weight to a fraction (0.05 = 5%)."""
    COUNTRIES_LANGUAGE: str | None = "en"
    """Language of the issuer's country names, None if they are ISO alpha-2 codes."""
    COUNTRIES_MAP: Dict[str, str | None] = {}
    """Issuer-specific uppercase country names to ISO alpha-2 codes, on top of the standard ones."""
    SECTORS_MAP: Dict[str, Sector | None] = {}
    """Issuer's uppercase sector names to standard sectors, on top of the English names."""
    ASSET_CLASSES_MAP: Dict[str, AssetClass | None] = {}
    """Issuer's uppercase holding types to standard asset classes."""

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
        df = self.normalise_holdings(df)
        return df

    def normalise_holdings(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Convert the values of the standard holdings columns to the standard format:
        - weight: fraction (0.05 = 5%)
        - country: ISO 3166-1 alpha-2 code
        - sector: Sector value
        - type: AssetClass value
        Values that can't be mapped become None, and are logged as warnings.
        """
        df = df.copy()

        if "weight" in df.columns:
            df["weight"] = (
                pd.to_numeric(df["weight"], errors="coerce") * self.WEIGHT_SCALE
            )

        if "country" in df.columns:
            countries_map = {
                **gen_country_to_alpha_2_map(self.COUNTRIES_LANGUAGE),
                **self.COUNTRIES_MAP,
            }
            df["country"] = map_values(
                df["country"], countries_map, f"{self.ISSUER} countries"
            )

        if "sector" in df.columns:
            sectors_map = {**SECTORS_MAP, **self.SECTORS_MAP}
            df["sector"] = map_values(
                df["sector"], sectors_map, f"{self.ISSUER} sectors"
            )

        if "type" in df.columns:
            df["type"] = map_values(
                df["type"], self.ASSET_CLASSES_MAP, f"{self.ISSUER} asset classes"
            )

        return df
