from portfolio_scraper.etf.xtrackers.base import XtrackersScraper


class XtrackersItScraper(XtrackersScraper):
    HOLDINGS_URL_TEMPLATE = (
        "https://etf.dws.com/etfdata/export/ITA/ITA/csv/product/constituent/{isin}/"
    )
    HOLDINGS_COLUMN_NAMES: dict[str, str] = {
        "name": "Constituent Name",
        "isin": "Constituent ISIN",
        "sector": "Constituent Industry Classification Name",
        "weight_in_etf": "Constituent Weighting",
        "location": "Constituent Country",
        "exchange": "Constituent Main Exchange Name",
        "currency": "Constituent Currency ISO Code",
        "rating": "Constituent Rating",
    }
    HOLDINGS_CSV_SEPARATOR = ";"

    COUNTRY_LANGUAGE = "ita"
