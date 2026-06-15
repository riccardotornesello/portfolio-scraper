import pandas as pd

from scrapers.base import BaseScraper
from utils.dataframe import Column


class ISharesBaseScraper(BaseScraper):
    LISTINGS_URL: str
    LISTINGS_COLUMN_NAMES: dict[str, Column]
    HOLDINGS_URL_TEMPLATE: str
    HOLDINGS_COLUMN_NAMES: dict[str, str]
    HOLDINGS_CSV_SEPARATOR: str
    HOLDINGS_CSV_THOUSANDS: str
    HOLDINGS_CSV_DECIMAL: str

    def _fetch_listings(self) -> pd.DataFrame:
        df = pd.read_json(self.LISTINGS_URL).T
        df = df.rename(columns={v: k for k, v in self.LISTINGS_COLUMN_NAMES.items()})
        return df

    def _get_holdings_by_id(self, product_id: str) -> pd.DataFrame:
        url = self.HOLDINGS_URL_TEMPLATE.format(product_id=product_id)
        df = pd.read_csv(
            url,
            sep=self.HOLDINGS_CSV_SEPARATOR,
            thousands=self.HOLDINGS_CSV_THOUSANDS,
            decimal=self.HOLDINGS_CSV_DECIMAL,
            skiprows=2,
            header=0,
        )
        df = df.rename(columns={v: k for k, v in self.HOLDINGS_COLUMN_NAMES.items()})
        df["weight_in_etf"] = df["weight_in_etf"] / 100
        return df

    def _get_holdings_by_isin(self, isin: str) -> pd.DataFrame:
        listings = self.get_listings()
        product_id = listings.loc[isin, "product_id"]
        return self._get_holdings_by_id(product_id)

    def _get_holdings_by_ticker(self, ticker: str) -> pd.DataFrame:
        listings = self.get_listings()
        product_id = listings[listings["ticker"] == ticker].iloc[0]["product_id"]
        return self._get_holdings_by_id(product_id)
