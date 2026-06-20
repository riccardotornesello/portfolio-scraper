from __future__ import annotations

import tempfile
import unittest

import pandas as pd

from portfolio_scraper.portfolio_analysis import (
    apply_holdings_filters,
    build_combined_holdings,
    compute_kpis,
    parse_portfolio_csv,
    validate_portfolio,
)


class FakeScraper:
    def __init__(self):
        pass

    def get_holdings_by_isin(self, isin: str) -> pd.DataFrame:
        if isin == "FAIL":
            raise RuntimeError("scrape failed")

        return pd.DataFrame(
            {
                "name": ["AAA Corp", "BBB Inc"],
                "isin": ["HOLD1", "HOLD2"],
                "weight_in_etf": [0.6, 0.4],
                "location": ["US", "IT"],
                "sector": ["Technology", "Financials"],
                "asset_class": ["Equity", "Equity"],
            }
        )


class PortfolioAnalysisTests(unittest.TestCase):
    def test_validate_portfolio_reports_invalid_rows(self):
        portfolio = pd.DataFrame(
            {
                "isin": ["IE00AAA", "", "IE00CCC"],
                "scraper": ["iShares (IT)", "invalid", "Vanguard (IT)"],
                "investment_eur": [1000, "abc", -10],
            }
        )

        valid, errors = validate_portfolio(portfolio)

        self.assertEqual(len(valid), 1)
        self.assertEqual(valid.iloc[0]["isin"], "IE00AAA")
        self.assertEqual(len(errors), 2)

    def test_parse_portfolio_csv_requires_columns(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as tmp:
            tmp.write("isin,scraper\nIE00AAA,iShares (IT)\n")
            path = tmp.name

        with self.assertRaises(ValueError):
            parse_portfolio_csv(path)

    def test_build_combined_holdings_and_filters(self):
        portfolio = pd.DataFrame(
            {
                "isin": ["ETF1", "ETF2"],
                "scraper": ["iShares (IT)", "Vanguard (IT)"],
                "investment_eur": [600, 400],
            }
        )

        combined, errors, valid = build_combined_holdings(
            portfolio,
            scraper_map={
                "iShares (IT)": FakeScraper,
                "Vanguard (IT)": FakeScraper,
            },
        )

        self.assertTrue(combined.shape[0] > 0)
        self.assertEqual(errors, [])
        self.assertEqual(valid["investment_eur"].sum(), 1000)

        filtered = apply_holdings_filters(
            combined,
            search_text="AAA",
            etf_isins=[],
            countries=["US"],
            sectors=["Technology"],
            asset_types=["Equity"],
        )

        self.assertEqual(len(filtered), 2)
        self.assertTrue((filtered["holding_name"] == "AAA Corp").all())

        kpis = compute_kpis(filtered, valid)
        self.assertEqual(kpis["etf_count"], 2)
        self.assertEqual(kpis["unique_holdings"], 1)


if __name__ == "__main__":
    unittest.main()
