from .base import VanguardScraper


class VanguardItScraper(VanguardScraper):
    """
    Scraper for Vanguard ETFs in Italy.
    It fetches listings and holdings data from the Vanguard API (GraphQL-based).
    """

    GRAPHQL_URL = "https://www.it.vanguard/gpx/graphql"
    LISTINGS_PAGE = "https://www.it.vanguard/investitori-privati/prodotti"
