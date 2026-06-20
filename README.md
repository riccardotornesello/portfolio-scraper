# portfolio-scraper

`portfolio-scraper` is a Python library that scrapes **ETF holdings** from the
official iShares, Vanguard, and Xtrackers websites and returns them as clean,
standardised pandas DataFrames.

Each provider publishes holdings in a different format; this library normalises
them into a common schema so holdings from different ETFs can be merged and
analysed together.

It also ships an optional **Gradio app** to build an ETF portfolio and explore
its combined holdings interactively.

## Installation

```bash
pip install portfolio-scraper
```

To install the Gradio app dependencies too:

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

## Scrapers

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

All scrapers expose the same interface:

- `get_holdings_by_isin(isin)`
- `get_holdings_by_ticker(ticker)`
- `get_holdings_by_id(internal_id)`
- `get_listings()`

## Holdings schema

`get_holdings_*` returns a DataFrame with standardised columns including:

- `name`, `isin`, `ticker`
- `weight_in_etf`
- `sector`, `asset_class`, `rating`
- `location`, `exchange`, `currency`
- value/quantity columns where available

Missing values are returned as `NaN`.

## Gradio app

The app is in `app/app.py` and supports:

- editable portfolio table (`isin`, `scraper`, `investment_eur`) with row add/remove;
- CSV import/export for portfolio rows;
- validation (empty ISIN, invalid scraper, non-numeric/negative investment);
- holdings scraping per ETF and weighted portfolio merge;
- filterable holdings table;
- pie charts (geography, sector, asset type) bound to active filters;
- global choropleth map by country exposure;
- KPIs + extra charts (top holdings bar, sunburst hierarchy, ETF exposure bar).

### Run the Gradio app

```bash
pip install "portfolio-scraper[app]"
python app/app.py
```

Then open the local URL printed in the terminal (usually `http://127.0.0.1:7860`).

### Expected CSV format

Required columns:

- `isin`
- `scraper` (valid values: `iShares (IT)`, `Vanguard (IT)`, `Xtrackers (IT)`)
- `investment_eur`

Example:

```csv
isin,scraper,investment_eur
IE00B6R52143,iShares (IT),6000
LU3061478973,Xtrackers (IT),4000
```

## Development

```bash
pip install -e ".[app]"
python -m unittest tests/test_portfolio_analysis.py
```

## Disclaimer

This is an **unofficial** project. It is not affiliated with, endorsed by, or
supported by BlackRock/iShares, Vanguard, DWS/Xtrackers, or any other fund
provider. All trademarks belong to their respective owners.

Data is scraped from public websites whose structure may change or become
unavailable. No guarantee is given about accuracy, completeness, timeliness, or
availability. Use at your own risk.

## Credits

Thanks to https://github.com/mledoze/countries for the countries database.
