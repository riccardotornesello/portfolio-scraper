import logging
from typing import get_args

import pandas as pd
import pycountry
import pytest

from portfolio_scraper.etf.base import LISTINGS_COLUMNS, HOLDINGS_COLUMNS
from portfolio_scraper.utils.asset_class import AssetClass
from portfolio_scraper.utils.sector import Sector


logging.basicConfig()
logging.getLogger().setLevel(logging.DEBUG)


# The full set of standardized column names a scraper is allowed to produce.
ALLOWED_LISTINGS_COLUMNS = set(get_args(LISTINGS_COLUMNS))
ALLOWED_HOLDINGS_COLUMNS = set(get_args(HOLDINGS_COLUMNS))

# The standard values of the normalised holdings columns.
ALLOWED_SECTORS = {sector.value for sector in Sector}
ALLOWED_ASSET_CLASSES = {asset_class.value for asset_class in AssetClass}
ALLOWED_COUNTRIES = {country.alpha_2 for country in pycountry.countries}


class RecordingHandler(logging.Handler):
    """
    Logging handler that keeps the messages of the warnings.
    """

    def __init__(self):
        super().__init__(level=logging.WARNING)
        self.messages = []

    def emit(self, record):
        self.messages.append(record.getMessage())


def empty_columns(df: pd.DataFrame) -> set[str]:
    """
    Return the columns of df that are entirely NaN, empty strings, or whitespace-only.
    """
    result = set()
    for col in df.columns:
        stripped = df[col].astype(str).str.strip()
        if (df[col].isna() | (stripped == "")).all():
            result.add(col)
    return result


@pytest.fixture(scope="module")
def ishares_scraper():
    from portfolio_scraper.etf.ishares.it import ISharesItScraper

    return ISharesItScraper()


@pytest.fixture(scope="module")
def vanguard_scraper():
    from portfolio_scraper.etf.vanguard.it import VanguardItScraper

    return VanguardItScraper()


@pytest.fixture(scope="module")
def xtrackers_scraper():
    from portfolio_scraper.etf.xtrackers.it import XTrackersItScraper

    return XTrackersItScraper()


@pytest.fixture(scope="module")
def amundi_scraper():
    from portfolio_scraper.etf.amundi.base import AmundiScraper

    return AmundiScraper()


@pytest.fixture(scope="class")
def scraper(request):
    return request.getfixturevalue(request.cls.scraper_fixture)


@pytest.fixture(scope="class")
def listings(scraper):
    return scraper.get_listings()


@pytest.fixture(scope="class")
def holdings_and_warnings(request, scraper):
    handler = RecordingHandler()
    logger = logging.getLogger("portfolio_scraper")
    logger.addHandler(handler)
    try:
        holdings = [
            scraper.get_holdings(holdings_id)
            for holdings_id in request.cls.HOLDINGS_IDS
        ]
    finally:
        logger.removeHandler(handler)
    return holdings, handler.messages


@pytest.fixture(scope="class")
def all_holdings(holdings_and_warnings):
    return holdings_and_warnings[0]


@pytest.fixture(scope="class", params=range(3))
def holdings(all_holdings, request):
    return all_holdings[request.param]


@pytest.fixture(scope="class")
def holdings_union(all_holdings):
    return pd.concat(all_holdings, ignore_index=True)


class ScraperTestBase:
    """
    Shared, parametrized tests for the standardized get_listings/get_holdings API
    exposed by portfolio_scraper.etf.base.Scraper subclasses.
    """

    scraper_fixture: str

    # Identifiers passed to get_holdings() for 3 known, non-empty ETFs.
    # NOTE: what these identifiers represent (ISIN vs. the issuer's internal_id)
    # depends on how each scraper implements get_raw_holdings.
    HOLDINGS_IDS: tuple[str, str, str]

    def test_get_listings_is_nonempty(self, listings):
        assert listings is not None
        assert len(listings) > 0

    def test_listings_columns_are_known(self, listings):
        unknown_columns = set(listings.columns) - ALLOWED_LISTINGS_COLUMNS
        assert not unknown_columns, f"Unknown listings columns: {unknown_columns}"

    def test_listings_contains_all_mapped_columns(self, scraper, listings):
        expected_columns = set(scraper.LISTINGS_COLUMN_NAMES.keys())
        missing_columns = expected_columns - set(listings.columns)
        assert not missing_columns, f"Missing listings columns: {missing_columns}"

    def test_listings_has_no_empty_columns(self, listings):
        bad_columns = empty_columns(listings)
        assert not bad_columns, f"Columns entirely empty/NaN: {bad_columns}"

    def test_get_holdings_is_nonempty(self, holdings):
        assert holdings is not None
        assert len(holdings) > 0

    def test_holdings_columns_are_known(self, holdings):
        unknown_columns = set(holdings.columns) - ALLOWED_HOLDINGS_COLUMNS
        assert not unknown_columns, f"Unknown holdings columns: {unknown_columns}"

    def test_holdings_contains_all_mapped_columns(self, scraper, holdings):
        expected_columns = set(scraper.HOLDINGS_COLUMN_NAMES.keys())
        missing_columns = expected_columns - set(holdings.columns)
        assert not missing_columns, f"Missing holdings columns: {missing_columns}"

    def test_holdings_union_has_no_empty_columns(self, holdings_union):
        bad_columns = empty_columns(holdings_union)
        assert not bad_columns, f"Columns entirely empty/NaN: {bad_columns}"

    def test_holdings_weights_sum_to_one(self, holdings):
        total = holdings["weight"].sum()
        assert 0.9 < total < 1.1, f"Weights sum to {total}, expected about 1"

    def test_holdings_sectors_are_standard(self, holdings_union):
        if "sector" not in holdings_union.columns:
            pytest.skip("No sector column")
        unknown = set(holdings_union["sector"].dropna()) - ALLOWED_SECTORS
        assert not unknown, f"Non-standard sectors: {unknown}"

    def test_holdings_asset_classes_are_standard(self, holdings_union):
        if "type" not in holdings_union.columns:
            pytest.skip("No type column")
        unknown = set(holdings_union["type"].dropna()) - ALLOWED_ASSET_CLASSES
        assert not unknown, f"Non-standard asset classes: {unknown}"

    def test_holdings_countries_are_standard(self, holdings_union):
        if "country" not in holdings_union.columns:
            pytest.skip("No country column")
        unknown = set(holdings_union["country"].dropna()) - ALLOWED_COUNTRIES
        assert not unknown, f"Non-standard countries: {unknown}"

    def test_holdings_have_no_unmapped_values(self, holdings_and_warnings):
        _, warnings = holdings_and_warnings
        unmapped = [message for message in warnings if message.startswith("Unmapped")]
        assert not unmapped, "\n".join(unmapped)


class TestISharesItScraper(ScraperTestBase):
    scraper_fixture = "ishares_scraper"
    # portfolioIds of 3 iShares UCITS ETFs.
    # get_raw_holdings needs iShares' internal portfolioId, not the ISIN.
    HOLDINGS_IDS = ("296967", "251911", "251909")


class TestVanguardItScraper(ScraperTestBase):
    scraper_fixture = "vanguard_scraper"
    # portIds of 3 Vanguard funds.
    HOLDINGS_IDS = ("9104", "9110", "9117")


class TestXTrackersItScraper(ScraperTestBase):
    scraper_fixture = "xtrackers_scraper"
    HOLDINGS_IDS = ("IE00BK1PV551", "LU0490618542", "IE00BJ0KDQ92")


class TestAmundiScraper(ScraperTestBase):
    scraper_fixture = "amundi_scraper"
    HOLDINGS_IDS = ("LU1681048804", "LU1681041460", "LU1681039134")
