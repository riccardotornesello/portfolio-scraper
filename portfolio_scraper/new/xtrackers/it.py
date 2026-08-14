from .base import XTrackersScraper


class XTrackersItScraper(XTrackersScraper):
    """
    Scraper for XTrackers ETFs in Italy.
    It fetches listings and holdings data from the XTrackers API (CSV-based).
    """

    LISTINGS_URL = "https://etf.dws.com/api/fundfinder/it-it/datatable"
    HOLDINGS_URL_TEMPLATE = (
        "https://etf.dws.com/etfdata/export/ITA/ITA/csv/product/constituent/{isin}/"
    )
    # TODO: check for sensitive data
    COOKIE = "audiences_it-it=%7B%22a%22%3A%5B%227864d84e-9892-4df4-9d1b-0109d415b8ae%22%5D%2C%22i%22%3Afalse%2C%22e%22%3A%2218%2F09%2F2027%2017%3A30%22%7D"
