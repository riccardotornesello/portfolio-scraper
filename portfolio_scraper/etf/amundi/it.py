import pandas as pd
import requests

from portfolio_scraper.etf.base import BaseEtfScraper


class AmundiItScraper(BaseEtfScraper):
    HOLDINGS_COLUMN_NAMES = {
        "name": "name",
        "isin": "isin",
        "weight_in_etf": "weight",
        "sector": "sector",
        "asset_class": "type",
        "shares_amount": "quantity",
        "location": "countryOfRisk",  # TODO: map
        "currency": "currency",
    }

    def _fetch_raw_listings(self) -> pd.DataFrame:
        raise NotImplementedError

    def _fetch_raw_holdings_by_id(self, isin: str) -> pd.DataFrame:
        return self._fetch_raw_holdings_by_isin(isin)

    def _fetch_raw_holdings_by_isin(self, isin: str) -> pd.DataFrame:
        url = "https://www.amundietf.it/mapi/ProductAPI/getProductsData"
        payload = {
            "composition": {
                "compositionFields": [
                    "date",
                    "type",
                    "bbg",
                    "isin",
                    "name",
                    "weight",
                    "quantity",
                    "currency",
                    "sector",
                    "country",
                    "countryOfRisk",
                ]
            },
            "productIds": [isin],
        }
        response = requests.post(url, json=payload)
        response.raise_for_status()
        data = [
            element["compositionCharacteristics"]
            for element in response.json()["products"][0]["composition"][
                "compositionData"
            ]
        ]
        df = pd.DataFrame(data)
        return df

    def _fetch_raw_holdings_by_ticker(self, ticker: str) -> pd.DataFrame:
        raise NotImplementedError(
            "Amundi Italy ETF holdings by ticker is not implemented yet."
        )
