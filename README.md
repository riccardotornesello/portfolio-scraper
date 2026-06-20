# portfolio-scraper

`portfolio-scraper` is a Python library that scrapes **ETF holdings** from the
official iShares, Vanguard, and Xtrackers websites and returns them as clean,
standardised pandas DataFrames.

Each provider publishes its holdings in a different format, with different column
names, languages, sector taxonomies, country names and exchange labels. This
library normalises all of that into a single common schema, so holdings from
different ETFs can be compared, merged and analysed together.

It also ships an optional **Streamlit app** to build a portfolio of ETFs and
explore the combined holdings interactively.

## Installation

```bash
pip install portfolio-scraper
```

To also install the Streamlit app dependencies (Streamlit + Plotly):

```bash
pip install "portfolio-scraper[app]"
```

## Quick start

```python
from portfolio_scraper import ISharesItScraper

scraper = ISharesItScraper()
df = scraper.get_holdings_by_isin("IE00B6R52143")

print(df[["name", "weight_in_etf", "sector", "location"]].head())
```

## Usage

### Scrapers

```python
from portfolio_scraper import (
    ISharesItScraper,
    VanguardItScraper,
    XtrackersItScraper,
)
```

| Scraper   | Class                | Provider          | Region |
| --------- | -------------------- | ----------------- | ------ |
| iShares   | `ISharesItScraper`   | BlackRock iShares | Italy  |
| Vanguard  | `VanguardItScraper`  | Vanguard          | Italy  |
| Xtrackers | `XtrackersItScraper` | DWS Xtrackers     | Italy  |

Every scraper exposes the same interface:

| Method                            | Description                                  |
| --------------------------------- | -------------------------------------------- |
| `get_holdings_by_isin(isin)`      | Fetch holdings for a given ISIN              |
| `get_holdings_by_ticker(ticker)`  | Fetch holdings for a given ticker            |
| `get_holdings_by_id(internal_id)` | Fetch holdings by the provider's internal id |
| `get_listings()`                  | List all available funds for the provider    |

### Holdings schema

`get_holdings_*` methods return a DataFrame with these standardised columns:

| Column                                                                       | Description                                       |
| ---------------------------------------------------------------------------- | ------------------------------------------------- |
| `name`                                                                       | Holding name                                      |
| `isin`                                                                       | Holding ISIN                                      |
| `ticker`                                                                     | Holding ticker                                    |
| `weight_in_etf`                                                              | Weight inside the ETF, as a decimal (`0.05` = 5%) |
| `sector`                                                                     | GICS sector name                                  |
| `asset_class`                                                                | Asset class (Equity, Bond, Cash, …)               |
| `rating`                                                                     | Credit rating, when available                     |
| `location`                                                                   | ISO 3166-1 alpha-2 country code                   |
| `exchange`                                                                   | MIC code (ISO 10383), when listed                 |
| `currency`                                                                   | Currency code                                     |
| `total_market_value`, `total_notional_value`, `shares_amount`, `share_price` | Position figures, when available                  |

Not every provider fills every column; missing values are `NaN`.

### Example: combine several ETFs into one portfolio

Weight each ETF's holdings by its share of the total portfolio value, then merge:

```python
import pandas as pd
from portfolio_scraper import ISharesItScraper, XtrackersItScraper

# (scraper, isin, value in euro)
portfolio = [
    (ISharesItScraper(), "IE00B6R52143", 6000),
    (XtrackersItScraper(), "LU3061478973", 4000),
]
total = sum(value for _, _, value in portfolio)

frames = []
for scraper, isin, value in portfolio:
    holdings = scraper.get_holdings_by_isin(isin).copy()
    holdings["etf_isin"] = isin
    holdings["portfolio_weight"] = holdings["weight_in_etf"] * (value / total)
    frames.append(holdings)

combined = pd.concat(frames, ignore_index=True)

# Allocation by sector across the whole portfolio
by_sector = combined.groupby("sector")["portfolio_weight"].sum().sort_values(ascending=False)
print(by_sector)
```

### Example: list available funds

```python
from portfolio_scraper import ISharesItScraper

listings = ISharesItScraper().get_listings()
print(listings[["name", "ticker", "ter"]].head())
```

## Streamlit app

The app (in `app/app.py`) lets you:

- build a portfolio of ETFs (ISIN, scraper, value in euro);
- import/export the portfolio list as CSV;
- scrape and merge all holdings into a single weighted DataFrame;
- browse the holdings in a filterable table;
- view pie charts of the allocation by sector, asset class and country (filterable).

Run it:

```bash
pip install "portfolio-scraper[app]"
streamlit run app/app.py
```

Then open the URL printed in the terminal (default http://localhost:8501).

## Development

```bash
uv sync --all-extras
```

Run the app from the cloned repo:

```bash
uv run streamlit run app/app.py
```

## Disclaimer

This is an **unofficial** project. It is not affiliated with, endorsed by, or
supported by BlackRock/iShares, Vanguard, DWS/Xtrackers, or any other fund
provider. All trademarks belong to their respective owners.

The data is scraped from public websites whose structure and content may change
or become unavailable at any time. **No guarantee** is given about the accuracy,
completeness, timeliness or availability of the data. It is provided "as is",
without warranty of any kind. Do not rely on it for investment decisions — always
verify against the providers' official sources. Use at your own risk, and make
sure your usage complies with each provider's terms of service.

## Credits

Thanks to https://github.com/mledoze/countries for the countries database.
