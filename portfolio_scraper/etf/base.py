from abc import ABC, abstractmethod

import pandas as pd

from portfolio_scraper.utils.dataframe import (
    prepare_dataframe,
    Column,
    ColumnType,
    rename_dataframe_columns,
)


LISTINGS_COLUMNS: dict[str, Column] = {
    "internal_id": Column(),  # Unique identifier for the ETF in the scraper's database
    "name": Column(),
    "isin": Column(),
    "ticker": Column(),
    "ter": Column(col_type=ColumnType.NUMERIC),  # Total Expense Ratio as a decimal
    "profit_distribution_strategy": Column(),  # TODO: enum
}

HOLDINGS_COLUMNS: dict[str, Column] = {
    # Basic information
    "name": Column(),
    "isin": Column(),
    "ticker": Column(),
    # ETF-specific information
    "weight_in_etf": Column(col_type=ColumnType.NUMERIC),  # Decimal between 0 and 1
    # Generic holding information
    "sector": Column(),  # GICS sector name, None if not applicable (cash, derivatives)
    "rating": Column(),
    "asset_class": Column(),  # TODO: create an asset class enum
    "total_market_value": Column(col_type=ColumnType.NUMERIC),
    "total_notional_value": Column(col_type=ColumnType.NUMERIC),
    "shares_amount": Column(col_type=ColumnType.NUMERIC),
    "share_price": Column(col_type=ColumnType.NUMERIC),
    "location": Column(),  # ISO 3166-1 alpha-2 country code
    "exchange": Column(),  # MIC code (ISO 10383), None if unlisted
    "currency": Column(),
}


class BaseEtfScraper(ABC):
    """
    Base class for ETF scrapers. Provides methods to fetch listings and holdings data.
    """

    LISTINGS_COLUMN_NAMES: dict[str, str] = {}
    HOLDINGS_COLUMN_NAMES: dict[str, str] = {}

    listings_cache: pd.DataFrame | None = None

    def get_listings(self, refresh: bool = False) -> pd.DataFrame:
        """
        Get the ETF listings. Caches the result to avoid redundant fetching.
        """
        if self.listings_cache is None or refresh:
            self.listings_cache = self.fetch_listings()
        return self.listings_cache

    def fetch_listings(self) -> pd.DataFrame:
        """
        Fetch the ETF listings from the source. Must be implemented by subclasses.
        """
        df = self._fetch_raw_listings()
        df = self._prepare_listings(df)
        df = prepare_dataframe(df, LISTINGS_COLUMNS, index_col="isin")
        return df

    def get_holdings_by_id(self, internal_id: str) -> pd.DataFrame:
        """
        Get the holdings of an ETF by its internal ID.
        """
        df = self._fetch_raw_holdings_by_id(internal_id)
        df = self._prepare_holdings(df)
        df = prepare_dataframe(df, HOLDINGS_COLUMNS)
        return df

    def get_holdings_by_isin(self, isin: str) -> pd.DataFrame:
        """
        Get the holdings of an ETF by its ISIN.
        """
        df = self._fetch_raw_holdings_by_isin(isin)
        df = self._prepare_holdings(df)
        df = prepare_dataframe(df, HOLDINGS_COLUMNS)
        return df

    def get_holdings_by_ticker(self, ticker: str) -> pd.DataFrame:
        """
        Get the holdings of an ETF by its ticker.
        """
        df = self._fetch_raw_holdings_by_ticker(ticker)
        df = self._prepare_holdings(df)
        df = prepare_dataframe(df, HOLDINGS_COLUMNS)
        return df

    @abstractmethod
    def _fetch_raw_listings(self) -> pd.DataFrame:
        """
        Fetch the raw ETF listings from the source. Must be implemented by subclasses.
        It returns a DataFrame with the raw data, without mapping and with more columns than the final output.
        """
        raise NotImplementedError

    def _prepare_listings(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Rename the columns and update the output.
        Can be overridden by subclasses for custom processing.
        """
        df = rename_dataframe_columns(df, self.LISTINGS_COLUMN_NAMES)
        df = df.dropna(how="all")
        return df

    @abstractmethod
    def _fetch_raw_holdings_by_id(self, product_id: str) -> pd.DataFrame:
        raise NotImplementedError

    @abstractmethod
    def _fetch_raw_holdings_by_isin(self, isin: str) -> pd.DataFrame:
        raise NotImplementedError

    @abstractmethod
    def _fetch_raw_holdings_by_ticker(self, ticker: str) -> pd.DataFrame:
        raise NotImplementedError

    def _prepare_holdings(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Rename the columns and update the output.
        Can be overridden by subclasses for custom processing.
        """
        df = rename_dataframe_columns(df, self.HOLDINGS_COLUMN_NAMES)
        df = df.dropna(how="all")
        return df
