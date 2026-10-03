import logging
from typing import get_args

import pandas as pd
import pytest

from portfolio_scraper.etf.base import LISTINGS_COLUMNS, HOLDINGS_COLUMNS


logging.basicConfig()
logging.getLogger().setLevel(logging.DEBUG)


# The full set of standardized column names a scraper is allowed to produce.
ALLOWED_LISTINGS_COLUMNS = set(get_args(LISTINGS_COLUMNS))
ALLOWED_HOLDINGS_COLUMNS = set(get_args(HOLDINGS_COLUMNS))


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

    @classmethod
    @pytest.fixture(scope="class")
    def scraper(cls, request):
        return request.getfixturevalue(cls.scraper_fixture)

    @classmethod
    @pytest.fixture(scope="class")
    def listings(cls, scraper):
        return scraper.get_listings()

    @classmethod
    @pytest.fixture(scope="class")
    def all_holdings(cls, scraper):
        return [scraper.get_holdings(holdings_id) for holdings_id in cls.HOLDINGS_IDS]

    @classmethod
    @pytest.fixture(scope="class", params=range(3))
    def holdings(cls, all_holdings, request):
        return all_holdings[request.param]

    @classmethod
    @pytest.fixture(scope="class")
    def holdings_union(cls, all_holdings):
        return pd.concat(all_holdings, ignore_index=True)

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
