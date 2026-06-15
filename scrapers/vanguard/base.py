import pandas as pd
import requests

from scrapers.base import BaseScraper


class VanguardGraphQLScraper(BaseScraper):
    GRAPHQL_URL: str
    LISTINGS_PAGE: str

    LISTINGS_COLUMN_NAMES: dict[str, str] = {
        "internal_id": "portId",
        "name": "fundFullName",
        "isin": "isin",
    }

    HOLDINGS_COLUMN_NAMES: dict[str, str] = {
        "ticker": "ticker",
        "name": "issuerName",
        "sector": "gicsSectorDescription",
        "asset_class": "securityType",
        "market_value": "marketValueBaseCurrency",  # TODO: check
        "weight": "marketValuePercentage",
        "notional_value": None,  # TODO: maybe marketValueBaseCurrency / quantity?
        "amount": "quantity",  # TODO: check
        "price": None,  # TODO: maybe marketValueBaseCurrency / quantity?
        "location": "bloombergIsoCountry",
    }

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

    def _fetch_listings(self) -> pd.DataFrame:
        # TODO: extract TER from feesAndExpenses
        # TODO: extract ticker from listings

        # Extract portIds from listings page HTML
        listings_page_req = requests.get(self.LISTINGS_PAGE)
        listings_page_html = listings_page_req.text

        port_ids_start_string = '"portIds":"'
        port_ids_start = listings_page_html.find(port_ids_start_string) + len(
            port_ids_start_string
        )
        port_ids_end = listings_page_html.find('"', port_ids_start)
        port_ids = listings_page_html[port_ids_start:port_ids_end].split(",")

        # Make GraphQL request to get listings data
        resp = requests.post(
            self.GRAPHQL_URL,
            headers={"x-consumer-id": "it0"},
            json={
                "operationName": "FundsQuery",
                "variables": {"portIds": port_ids},
                "query": self.LISTINGS_QUERY,
            },
        )

        data = resp.json()
        data = data["data"]["funds"]
        data = [fund["profile"] for fund in data]

        for fund in data:
            identifiers = fund.pop("identifiers")
            for identifier in identifiers:
                if identifier["altId"] == "ISIN":
                    fund["isin"] = identifier["altIdValue"]
                    break

        df = pd.DataFrame(data)
        df = df.rename(columns={v: k for k, v in self.LISTINGS_COLUMN_NAMES.items()})
        return df

    def _get_holdings_by_id(self, id: str) -> pd.DataFrame:
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
            data = resp.json()
            holdings = data["data"]["borHoldings"][0]["holdings"]["items"]
            last_item_key = data["data"]["borHoldings"][0]["holdings"]["lastItemKey"]
            df = pd.concat([df, pd.DataFrame(holdings)], ignore_index=True)

        df = df.rename(columns={v: k for k, v in self.HOLDINGS_COLUMN_NAMES.items()})
        df["weight"] = df["weight"] / 100  # Convert percentage to decimal
        return df

    def _get_holdings_by_isin(self, isin: str) -> pd.DataFrame:
        listings = self.get_listings()
        product_id = listings.loc[isin, "portId"]
        return self._get_holdings_by_id(product_id)

    def _get_holdings_by_ticker(self, ticker: str) -> pd.DataFrame:
        raise NotImplementedError
