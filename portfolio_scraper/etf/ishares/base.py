import pandas as pd

from portfolio_scraper.etf.base import BaseEtfScraper
from portfolio_scraper.utils.asset_class import ishares_to_asset_class
from portfolio_scraper.utils.country import country_name_to_alpha_2
from portfolio_scraper.utils.dataframe import Column, rename_dataframe_columns
from portfolio_scraper.utils.exchange import exchange_to_mic
from portfolio_scraper.utils.sector import italian_to_gics


class ISharesBaseEtfScraper(BaseEtfScraper):
    LISTINGS_URL: str
    LISTINGS_COLUMN_NAMES: dict[str, Column]
    HOLDINGS_URL_TEMPLATE: str
    HOLDINGS_COLUMN_NAMES: dict[str, str]
    HOLDINGS_CSV_SEPARATOR: str
    HOLDINGS_CSV_THOUSANDS: str
    HOLDINGS_CSV_DECIMAL: str
    COUNTRY_LANGUAGE: str

    def _fetch_raw_listings(self) -> pd.DataFrame:
        return pd.read_json(self.LISTINGS_URL).T

    def _fetch_raw_holdings_by_id(self, product_id: str) -> pd.DataFrame:
        url = self.HOLDINGS_URL_TEMPLATE.format(product_id=product_id)
        df = pd.read_csv(
            url,
            sep=self.HOLDINGS_CSV_SEPARATOR,
            thousands=self.HOLDINGS_CSV_THOUSANDS,
            decimal=self.HOLDINGS_CSV_DECIMAL,
            skiprows=2,
            header=0,
        )
        return df

    def _fetch_raw_holdings_by_isin(self, isin: str) -> pd.DataFrame:
        listings = self.get_listings()
        product_id = listings.loc[isin, "internal_id"]
        return self._fetch_raw_holdings_by_id(product_id)

    def _fetch_raw_holdings_by_ticker(self, ticker: str) -> pd.DataFrame:
        listings = self.get_listings()
        product_id = listings[listings["ticker"] == ticker].iloc[0]["internal_id"]
        return self._fetch_raw_holdings_by_id(product_id)

    def _prepare_holdings(self, df: pd.DataFrame) -> pd.DataFrame:
        df = rename_dataframe_columns(df, self.HOLDINGS_COLUMN_NAMES)
        df = df.dropna(how="all")
        weights = (
            df["weight_in_etf"]
            .astype(str)
            .str.replace("%", "", regex=False)
            .str.replace(".", "", regex=False)
            .str.replace(",", ".", regex=False)
            .str.strip()
        )
        df["weight_in_etf"] = pd.to_numeric(weights, errors="coerce") / 100
        df["location"] = df["location"].map(
            country_name_to_alpha_2,
            na_action="ignore",
            language=self.COUNTRY_LANGUAGE,
        )
        df["exchange"] = df["exchange"].map(exchange_to_mic, na_action="ignore")
        df["sector"] = df["sector"].map(italian_to_gics, na_action="ignore")
        df["asset_class"] = df["asset_class"].map(
            ishares_to_asset_class,
            na_action="ignore",
        )
        return df
