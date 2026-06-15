import pandas as pd

from scrapers.base import BaseScraper


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
        df = pd.read_csv(url, sep=self.HOLDINGS_CSV_SEPARATOR, encoding="latin-1")
        df = df.rename(columns={v: k for k, v in self.HOLDINGS_COLUMN_NAMES.items()})
        return df

    def _get_holdings_by_ticker(self, ticker: str) -> pd.DataFrame:
        raise NotImplementedError
