import logging
import pytest

import pandas as pd

from portfolio_scraper.utils.country import gen_country_to_alpha_2_map
from portfolio_scraper.utils.dataframe import ColumnType
from portfolio_scraper.utils.sector import GICSector


logging.basicConfig()
logging.getLogger().setLevel(logging.DEBUG)


HOLDINGS_COLUMNS: dict[str, ColumnType] = {
    # Basic information
    "name": ColumnType.STRING,
    "isin": ColumnType.STRING,
    "ticker": ColumnType.STRING,
    # ETF-specific information
    "weight_in_etf": ColumnType.NUMERIC,  # Decimal between 0 and 1
    # Generic holding information
    "gics_sector": ColumnType.STRING,
    "rating": ColumnType.STRING,
    "asset_class": ColumnType.STRING,
    "total_market_value": ColumnType.NUMERIC,
    "total_notional_value": ColumnType.NUMERIC,
    "shares_amount": ColumnType.NUMERIC,
    "share_price": ColumnType.NUMERIC,
    "country_alpha2": ColumnType.STRING,  # ISO 3166-1 alpha-2 country code
    "exchange": ColumnType.STRING,  # MIC code (ISO 10383), None if unlisted
    "currency": ColumnType.STRING,
}


@pytest.fixture(scope="module")
def amundi_scraper():
    from portfolio_scraper.etf.amundi.it import AmundiItScraper

    return AmundiItScraper()


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
    from portfolio_scraper.etf.xtrackers.it import XtrackersItScraper

    return XtrackersItScraper()


class ScraperTestBase:
    ISIN: str
    scraper_fixture: str

    @pytest.fixture(autouse=True)
    def setup(self, request):
        self.scraper = request.getfixturevalue(self.scraper_fixture)
        self.result = self.scraper.get_holdings_by_isin(self.ISIN)
        self.raw_result = self.scraper._fetch_raw_holdings_by_isin(self.ISIN)

    def test_get_holdings_does_not_raise(self):
        pass

    def test_get_holdings_is_nonempty(self):
        assert self.result is not None
        assert len(self.result) > 0

    def test_holdings_columns_format(self):
        # Check that the columns in the result DataFrame match the expected columns and types
        for col in self.result.columns:
            assert col in HOLDINGS_COLUMNS
            assert (
                pd.api.types.is_numeric_dtype(self.result[col])
                or pd.isnull(self.result[col]).all()
                if HOLDINGS_COLUMNS[col] == ColumnType.NUMERIC
                else True
            )

        # weight_in_etf should sum to 1.0 (or very close to it, allowing for rounding errors)
        assert self.result["weight_in_etf"].sum() == pytest.approx(1.0, rel=1e-2)

        # country_alpha2 should be a valid ISO 3166-1 alpha-2 country code (2-letter string)
        assert (
            self.result["country_alpha2"]
            .dropna()
            .apply(lambda x: isinstance(x, str) and len(x) == 2)
            .all()
        )

        # gics_sector should be one of the GICSector enum values
        assert (
            self.result["gics_sector"]
            .dropna()
            .apply(lambda x: x in GICSector._value2member_map_)
            .all()
        )

    def test_holdings_countries(self):
        """
        Test country_alpha2 mapping
        """

        if hasattr(self.scraper, "COUNTRY_LANGUAGE"):
            column_name = self.scraper.HOLDINGS_COLUMNS["country_alpha2"].source
            mapper = gen_country_to_alpha_2_map(self.scraper.COUNTRY_LANGUAGE)

            countries = set(self.raw_result[column_name].dropna().str.upper().unique())
            available_countries = mapper.keys()
            unmapped_countries = sorted(countries - available_countries)

            assert len(unmapped_countries) == 0, (
                f"Unmapped countries: {unmapped_countries}"
            )

    def test_gics_sector_mapping(self):
        """
        Test that all gics_sector values in the raw result are either mapped to a GICSector
        or are None (for unmapped sectors).
        """
        column = self.scraper.HOLDINGS_COLUMNS["gics_sector"]
        source = column.source
        mapper = column.mapper

        sectors = set(self.raw_result[source].dropna().str.upper().unique())
        unmapped_sectors = sorted(sector for sector in sectors if sector not in mapper)

        assert len(unmapped_sectors) == 0, f"Unmapped GICSectors: {unmapped_sectors}"


class TestAmundiItScraper(ScraperTestBase):
    ISIN = "LU1681048804"
    scraper_fixture = "amundi_scraper"


class TestISharesItScraper(ScraperTestBase):
    ISIN = "IE00B6R52143"
    scraper_fixture = "ishares_scraper"


class TestVanguardItScraper(ScraperTestBase):
    ISIN = "IE00B3XXRP09"
    scraper_fixture = "vanguard_scraper"


class TestXtrackersItScraper(ScraperTestBase):
    ISIN = "LU0490618542"
    scraper_fixture = "xtrackers_scraper"
