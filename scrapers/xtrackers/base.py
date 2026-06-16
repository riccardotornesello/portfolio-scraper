import pandas as pd

from scrapers.base import BaseScraper
from utils.country import italian_to_iso
from utils.dataframe import rename_dataframe_columns
from utils.exchange import exchange_to_mic
from utils.sector import italian_to_gics


class XtrackersScraper(BaseScraper):
    HOLDINGS_URL_TEMPLATE: str
    HOLDINGS_COLUMN_NAMES: dict[str, str]
    HOLDINGS_CSV_SEPARATOR: str

    def _fetch_listings(self) -> pd.DataFrame:
        raise NotImplementedError

    def _get_holdings_by_id(self, isin: str) -> pd.DataFrame:
        return self._get_holdings_by_isin(isin)

    def _get_holdings_by_isin(self, isin: str) -> pd.DataFrame:
        url = self.HOLDINGS_URL_TEMPLATE.format(isin=isin)
        df = pd.read_csv(url, sep=self.HOLDINGS_CSV_SEPARATOR, encoding="utf-8")
        df = rename_dataframe_columns(df, self.HOLDINGS_COLUMN_NAMES)
        df["location"] = df["location"].map(italian_to_iso, na_action="ignore")
        df["exchange"] = df["exchange"].map(exchange_to_mic, na_action="ignore")
        df["sector"] = df["sector"].map(italian_to_gics, na_action="ignore")
        df = df.dropna(how='all')
        return df

    def _get_holdings_by_ticker(self, ticker: str) -> pd.DataFrame:
        raise NotImplementedError
