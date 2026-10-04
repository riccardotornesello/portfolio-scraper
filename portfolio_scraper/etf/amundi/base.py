from typing import Dict

import requests
import pandas as pd

from ...utils.asset_class import AssetClass
from ...utils.sector import Sector
from ..base import HOLDINGS_COLUMNS, LISTINGS_COLUMNS, EtfBaseScraper


class AmundiScraper(EtfBaseScraper):
    """
    Scraper for Amundi ETFs.
    It fetches listings and holdings data from the Amundi API (JSON-based).

    NOTE: The Amundi API without filters returns products from all countries, so it is not required to use country-specific scrapers.
    """

    PRODUCTS_URL: str = "https://www.amundietf.it/mapi/ProductAPI/getProductsData"

    ISSUER: str = "Amundi"
    LISTINGS_COLUMN_NAMES: Dict[LISTINGS_COLUMNS, str] = {
        "isin": "characteristics.ISIN",
        "name": "characteristics.SHARE_MARKETING_NAME",
        "internal_id": "productId",
        "ter": "characteristics.TER",
    }
    HOLDINGS_COLUMN_NAMES: Dict[HOLDINGS_COLUMNS, str] = {
        "ticker": "bbg",  # Bloomberg ticker
        "isin": "isin",
        "name": "name",
        "weight": "weight",
        "sector": "sector",
        "type": "type",
        "country": "countryOfRisk",
        "currency": "currency",
    }

    SECTORS_MAP: Dict[str, Sector | None] = {
        "COMMUNICATIONS": Sector.COMMUNICATION_SERVICES,
        "GOVERNMENT": Sector.GOVERNMENT,
        "TECHNOLOGY": Sector.INFORMATION_TECHNOLOGY,
    }
    ASSET_CLASSES_MAP: Dict[str, AssetClass | None] = {
        "EQUITY_ORDINARY": AssetClass.EQUITY,
        "PREFERENCE_SHARES": AssetClass.EQUITY,
        "DEPOSITORY_RECEIPT": AssetClass.EQUITY,
        "RIGHT": AssetClass.EQUITY,
        "CORPORATE": AssetClass.FIXED_INCOME,
        "GOVERNMENT": AssetClass.FIXED_INCOME,
        "CASH": AssetClass.CASH,
        "FUTURE": AssetClass.DERIVATIVES,
        "FORWARD": AssetClass.DERIVATIVES,
        "ETF": AssetClass.FUND,
    }

    def get_raw_listings(self) -> pd.DataFrame:
        # TODO: add country availability

        response = requests.post(
            self.PRODUCTS_URL,
            timeout=self.REQUEST_TIMEOUT,
            json={
                "sortCriterias": [],
                "characteristics": [
                    "ISIN",
                    "TICKER",
                    "TER",
                    "IS_CLIMATE",
                    "SHARE_MARKETING_NAME",
                    "CURRENCY",
                    "FUND_AUM",
                    "WKN",
                    "MNEMO",
                    "INDEX_TICKER",
                    "EXCHANGE_PLACE",
                    "INCEPTION_DATE",
                    "AUM_IN_EURO",
                    "FUND_AUM_IN_EURO",
                    "NAV",
                    "NAV_DATE_DISPLAYED",
                    "FUND_TYPE",
                    "FUND_REPLICATION_METHODOLOGY",
                    "FUND_SFDR_CLASSIFICATION",
                    "FUND_ISR_LABEL",
                    "STRATEGY",
                    "SUBASSET_CLASS",
                    "ASSET_CLASS",
                    "ESG_SCOPE",
                    "ESG_SCOPES",
                    "INVESTMENT_ZONE",
                    "IMPACT",
                    "CATEGORY",
                    "DISTRIBUTION_POLICY",
                    "CURRENCY_HEDGE",
                    "FUND_PEA",
                    "MAIN_LISTING",
                    "CORE",
                    "IS_ESG",
                    "FUND_ISSUER",
                    "IS_THEMATIC",
                    "MAIN_LISTINGS",
                    "ETF_CLASSIFICATION2",
                    "IS_CORE",
                    "LEVERAGE",
                    "CURRENCY_HEDGE",
                    "OLD_ISINS",
                    "OLD_WKNS",
                    "OLD_SHARE_MARKETING_NAMES",
                    "INSURANCE_CONTRACTS_COUNT",
                    "INSURANCE_PAGE_URL",
                    "FUND_DOMICILIATION_COUNTRY",
                    "SRRI",
                    "LISTING_PLACES",
                    "DESCRIPTIF",
                    "IS_BEING_ABSORBED",
                    "IS_BEING_ABSORBED_BY",
                    "MARKET",
                    "SHARE_TYPE",
                    "IS_ACTIVELY_MANAGED",
                    "SHARE_CLASS_TYPE",
                ],
                "metrics": [
                    {"indicator": "shareCumulativePerformance", "period": "ONE_YEAR"},
                    {
                        "indicator": "shareCumulativePerformance",
                        "period": "THREE_YEARS",
                    },
                    {"indicator": "shareCumulativePerformance", "period": "FIVE_YEARS"},
                    {
                        "indicator": "shareCumulativePerformance",
                        "period": "YEAR_TO_DATE",
                    },
                    {"indicator": "shareCumulativePerformance", "period": "TEN_YEARS"},
                ],
                "productType": "ALL",
                "historics": [],
                "url": True,
                "filters": [],
            },
        )
        response.raise_for_status()

        df = pd.json_normalize(response.json()["products"])
        return df

    def get_raw_holdings(self, isin: str) -> pd.DataFrame:
        response = requests.post(
            self.PRODUCTS_URL,
            timeout=self.REQUEST_TIMEOUT,
            json={
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
            },
        )
        response.raise_for_status()

        data = response.json()["products"][0]["composition"]["compositionData"]
        data = [item["compositionCharacteristics"] for item in data]
        df = pd.DataFrame(data)
        return df
