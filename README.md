# portfolio-scraper

Python library to scrape ETF holdings from iShares, Vanguard, and Xtrackers.

## Installation

```bash
pip install portfolio-scraper
```

To also install the Streamlit app dependencies:

```bash
pip install "portfolio-scraper[app]"
```

## Usage

```python
from portfolio_scraper import ISharesItScraper, VanguardItScraper, XtrackersItScraper

scraper = ISharesItScraper()
df = scraper.get_holdings_by_isin("IE00BG0J4C88")
print(df.head())
```

Each scraper exposes:

| Method | Description |
|--------|-------------|
| `get_holdings_by_isin(isin)` | Fetch holdings for a given ISIN |
| `get_holdings_by_ticker(ticker)` | Fetch holdings for a given ticker |
| `get_listings()` | List all available funds |

Holdings DataFrames have standardised columns: `name`, `isin`, `ticker`, `weight_in_etf`, `sector`, `asset_class`, `location`, `currency`, `exchange`, and more.

## Streamlit app

```bash
pip install "portfolio-scraper[app]"
streamlit run app/app.py
```

## Supported scrapers

| Scraper | Class | Region |
|---------|-------|--------|
| iShares | `ISharesItScraper` | Italy |
| Vanguard | `VanguardItScraper` | Italy |
| Xtrackers | `XtrackersItScraper` | Italy |

## Development

```bash
uv sync --all-extras
```
