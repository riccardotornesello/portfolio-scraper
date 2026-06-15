from scrapers.vanguard.base import VanguardGraphQLScraper


class VanguardItScraper(VanguardGraphQLScraper):
    GRAPHQL_URL = "https://www.it.vanguard/gpx/graphql"
    LISTINGS_PAGE = "https://www.it.vanguard/investitori-privati/prodotti"
