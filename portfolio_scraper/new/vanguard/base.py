from typing import Dict

import pandas as pd
import requests

from portfolio_scraper.new.base import LISTINGS_COLUMNS, HOLDINGS_COLUMNS, Scraper


class VanguardScraper(Scraper):
    ISSUER: str = "Vanguard"
    LISTINGS_COLUMN_NAMES: Dict[LISTINGS_COLUMNS, str] = {
        "isin": "isin",
        "name": "fundFullName",
        "internal_id": "portId",
        "ter": "ter",
    }
    HOLDINGS_COLUMN_NAMES: Dict[HOLDINGS_COLUMNS, str] = {
        "ticker": "ticker",
        "name": "issuerName",
        "weight": "marketValuePercentage",
        "sector": "gicsSectorDescription",  # TODO: or icbSectorDescription
        "type": "securityType",
        "country": "bloombergIsoCountry",
    }

    GRAPHQL_URL: str
    LISTINGS_PAGE: str

    LISTINGS_QUERY = """
        query FundsQuery($portIds: [String!]!) {
            funds(portIds: $portIds) {
                profile {
                    portId
                    polarisPdtTypeIndicator
                    fundIndicator
                    assetClassificationLevel1
                    productTypeLevel1
                    marketOfDomicile
                    consarApproved
                    fundGroupHedgedFunds
                    fundFullName
                    prospectusShareClassName
                    fundInceptionDate
                    currencyHedgingStrategy
                    closedToAllPurchases
                    distributionStrategy
                    fundCurrency
                    investmentStrategy
                    shareClassName
                    managementStrategy
                    marketRegionFocus
                    countryMarketedForSale
                    investmentStrategy
                    feesAndExpenses {
                        feesAndExpensesType {
                            expenseType {
                                code
                                value
                                startDate
                            }
                        }
                    }
                    identifiers(
                        altIds: ["ISIN", "CITI Code", "CUSIP", "MexId", "Bloomberg", "SEDOL", "WKN Code", "VALOREN - Swiss Security Number", "Ticker", "Bolsa Ticker", "Ticker - Canada", "FundServ Code"]
                    ) {
                        altId
                        altIdCode
                        altIdValue
                        __typename
                    }
                    __typename
                }
                __typename
            }
        }
    """

    HOLDINGS_QUERY = """
        query FundsHoldingsQuery($portIds: [String!], $lastItemKey: String) {
            borHoldings(portIds: $portIds) {
                holdings(limit: 1500, lastItemKey: $lastItemKey) {
                items {
                    issuerName
                    securityLongDescription
                    gicsSectorDescription
                    icbSectorDescription
                    icbIndustryDescription
                    marketValuePercentage
                    sedol1
                    quantity
                    ticker
                    securityType
                    finalMaturity
                    effectiveDate
                    marketValueBaseCurrency
                    bloombergIsoCountry
                    couponRate
                    __typename
                }
                totalHoldings
                lastItemKey
                __typename
                }
                __typename
            }
        }
    """

    def get_raw_listings(self) -> pd.DataFrame:
        # Extract portIds from listings page HTML
        listings_page_req = requests.get(self.LISTINGS_PAGE)
        listings_page_req.raise_for_status()
        listings_page_html = listings_page_req.text

        port_ids_start_string = '"portIds":"'
        port_ids_start = listings_page_html.find(port_ids_start_string) + len(
            port_ids_start_string
        )
        port_ids_end = listings_page_html.find('"', port_ids_start)
        port_ids = listings_page_html[port_ids_start:port_ids_end].split(",")

        # Make GraphQL request to get listings data
        response = requests.post(
            self.GRAPHQL_URL,
            headers={"x-consumer-id": "it0"},
            json={
                "operationName": "FundsQuery",
                "variables": {"portIds": port_ids},
                "query": self.LISTINGS_QUERY,
            },
        )
        response.raise_for_status()

        funds = [fund["profile"] for fund in response.json()["data"]["funds"]]

        df = pd.json_normalize(funds)
        return df

    def get_raw_holdings(self, id: str) -> pd.DataFrame:
        df = pd.DataFrame()

        first_request = True
        last_item_key = None
        while first_request or last_item_key is not None:
            first_request = False
            resp = requests.post(
                self.GRAPHQL_URL,
                headers={"x-consumer-id": "it0"},
                json={
                    "operationName": "FundsHoldingsQuery",
                    "variables": {
                        "portIds": [id],
                        "lastItemKey": last_item_key,
                    },
                    "query": self.HOLDINGS_QUERY,
                },
            )
            resp.raise_for_status()

            data = resp.json()
            holdings = data["data"]["borHoldings"][0]["holdings"]["items"]
            last_item_key = data["data"]["borHoldings"][0]["holdings"]["lastItemKey"]
            df = pd.concat([df, pd.DataFrame(holdings)], ignore_index=True)

        return df

    def get_issuer_listings(self) -> pd.DataFrame:
        df = self.get_raw_listings()

        # Extract the ISIN from the list of identifiers
        df["isin"] = df["identifiers"].apply(
            lambda ids: next(
                (i["altIdValue"] for i in ids or [] if i["altIdCode"] == "ISIN"),
                None,
            )
        )

        # The TER is the most recent "total expense ratio" entry
        def extract_ter(expense_types):
            if not isinstance(expense_types, list):
                return None
            expenses = [
                e
                for t in expense_types
                for e in t["expenseType"] or []
                if e["code"] == "TOTEXPRTPC"
            ]
            if not expenses:
                return None
            return max(expenses, key=lambda e: e["startDate"] or "")["value"]

        df["ter"] = df["feesAndExpenses.feesAndExpensesType"].apply(extract_ter)

        return df
