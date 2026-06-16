from abc import ABC, abstractmethod

import pandas as pd

from portfolio_scraper.utils.dataframe import prepare_dataframe, Column, ColumnType


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
        return prepare_dataframe(
            self._fetch_listings(),
            LISTINGS_COLUMNS,
            index_col="isin",
        )

    def get_holdings_by_id(self, internal_id: str) -> pd.DataFrame:
        """
        Get the holdings of an ETF by its internal ID.
        """
        return prepare_dataframe(
            self._get_holdings_by_id(internal_id),
            HOLDINGS_COLUMNS,
        )

    def get_holdings_by_isin(self, isin: str) -> pd.DataFrame:
        """
        Get the holdings of an ETF by its ISIN.
        """
        return prepare_dataframe(
            self._get_holdings_by_isin(isin),
            HOLDINGS_COLUMNS,
        )

    def get_holdings_by_ticker(self, ticker: str) -> pd.DataFrame:
        """
        Get the holdings of an ETF by its ticker.
        """
        return prepare_dataframe(
            self._get_holdings_by_ticker(ticker),
            HOLDINGS_COLUMNS,
        )

    @abstractmethod
    def _fetch_listings(self) -> pd.DataFrame:
        raise NotImplementedError

    @abstractmethod
    def _get_holdings_by_id(self, product_id: str) -> pd.DataFrame:
        raise NotImplementedError

    @abstractmethod
    def _get_holdings_by_isin(self, isin: str) -> pd.DataFrame:
        raise NotImplementedError

    @abstractmethod
    def _get_holdings_by_ticker(self, ticker: str) -> pd.DataFrame:
        raise NotImplementedError
