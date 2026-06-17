import logging

from portfolio_scraper import ISharesItScraper, VanguardItScraper, XtrackersItScraper


logging.basicConfig()
logging.getLogger().setLevel(logging.DEBUG)
_log = logging.getLogger(__name__)


if __name__ == "__main__":
    ishares_scraper = ISharesItScraper()
    vanguard_scraper = VanguardItScraper()
    xtrackers_scraper = XtrackersItScraper()

    _log.info("Testing ISharesItScraper")
    ishares_scraper.get_holdings_by_isin("IE00B6R52143")

    _log.info("Testing VanguardItScraper")
    vanguard_scraper.get_holdings_by_isin("IE00B3XXRP09")

    _log.info("Testing XtrackersItScraper")
    xtrackers_scraper.get_holdings_by_isin("LU3061478973")
