# portfolio-scraper

`portfolio-scraper` is a Python library that scrapes **ETF listings and holdings** from the official Amundi, iShares, Vanguard, and Xtrackers websites and returns them as pandas DataFrames with standardised column names.

Each provider publishes its data in a different format (JSON, CSV, GraphQL), with different column names. Every scraper maps the provider's columns onto a common set of names, so listings and holdings from different providers can be put side by side.

It also ships some **Streamlit apps** to explore the data interactively.

This project stems from my personal desire to understand the actual composition of my portfolio, and I work on it in my spare time, though very slowly. Contributions are welcome to add more scrapers or improve how it works!

Disclaimer: some fields may change in the future, and some mappings are not 100% correct.

## Installation

```bash
pip install portfolio-scraper
```

## Quick start

```python
from portfolio_scraper.etf import ISharesItScraper

scraper = ISharesItScraper()

# All the funds available on the provider's website
listings = scraper.get_listings()
print(listings.head())

# Holdings of a fund (iShares wants its internal id, see below)
holdings = scraper.get_holdings("251911")
print(holdings[["name", "weight", "sector", "country"]].head())
```

## Scrapers

```python
from portfolio_scraper.etf import (
    AmundiScraper,
    ISharesItScraper,
    VanguardItScraper,
    XTrackersItScraper,
)
```

| Class                | Provider          | Region         | Source format | `get_holdings()` identifier |
| -------------------- | ----------------- | -------------- | ------------- | --------------------------- |
| `AmundiScraper`      | Amundi            | All countries¹ | JSON API      | ISIN                        |
| `ISharesItScraper`   | BlackRock iShares | Italy          | JSON + CSV    | `internal_id`               |
| `VanguardItScraper`  | Vanguard          | Italy          | GraphQL       | `internal_id`               |
| `XTrackersItScraper` | DWS Xtrackers     | Italy          | JSON + CSV    | ISIN (= `internal_id`)      |

¹ The Amundi API returns the products of every country, so a single scraper is enough.

The identifier for `get_holdings()` can always be found in the output of `get_listings()`.

### How a scraper works

Every scraper extends `EtfBaseScraper` (`portfolio_scraper/etf/base.py`) and exposes three levels of data, for both listings and holdings:

| Listings                | Holdings                  | Output                                                                                      |
| ----------------------- | ------------------------- | ------------------------------------------------------------------------------------------- |
| `get_raw_listings()`    | `get_raw_holdings(id)`    | The data exactly as returned by the provider                                                |
| `get_issuer_listings()` | `get_issuer_holdings(id)` | The provider's data, cleaned up (flattened fields, readable column names), all columns kept |
| `get_listings()`        | `get_holdings(id)`        | **Standard format**: only the columns below, with the standard names and values             |

Use `get_listings()` / `get_holdings()` to combine data across providers. Use the issuer methods when you need a column that exists for one provider only.

In the standard format the holdings **values are normalised** too: weights, countries, sectors and asset classes use the same scale and the same names for every provider, so holdings from different providers can be summed.

## Standard format

### Listings

Returned by `get_listings()`. All scrapers provide all the columns.

| Column        | Description                                      | Amundi | iShares | Vanguard | Xtrackers |
| ------------- | ------------------------------------------------ | :----: | :-----: | :------: | :-------: |
| `isin`        | ISIN of the fund                                 |   ✅   |   ✅    |    ✅    |    ✅     |
| `name`        | Name of the fund                                 |   ✅   |   ✅    |    ✅    |    ✅     |
| `internal_id` | Provider's internal id of the fund               |   ✅   |   ✅    |    ✅    |    ✅     |
| `ter`         | Total expense ratio, in percent (`0.20` = 0.20%) |   ✅   |   ✅    |    ✅    |    ✅     |

Notes:

- `internal_id` is an integer for iShares and a string for the others. For Amundi it looks like `dl_<ISIN>`, for Xtrackers it is the ISIN itself.
- The Vanguard listings include mutual funds as well as ETFs.
- `ter` can be missing for some funds.

### Holdings

Returned by `get_holdings(id)`. Columns not provided by a scraper are absent from its DataFrame.

| Column     | Description                  | Values                                         | Amundi | iShares | Vanguard | Xtrackers |
| ---------- | ---------------------------- | ---------------------------------------------- | :----: | :-----: | :------: | :-------: |
| `ticker`   | Ticker of the holding        | Provider's ticker¹                             |   ✅   |   ✅    |    ✅    |    ❌     |
| `isin`     | ISIN of the holding          | ISIN                                           |   ✅   |   ❌    |    ❌    |    ✅     |
| `name`     | Name of the holding          | Provider's name                                |   ✅   |   ✅    |    ✅    |    ✅     |
| `weight`   | Weight in the fund           | Fraction (`0.05` = 5%)                         |   ✅   |   ✅    |    ✅    |    ✅     |
| `sector`   | Sector of the holding        | [`Sector`](#sectors)                           |   ✅   |   ✅    |   ✅²    |    ✅     |
| `type`     | Asset class of the holding   | [`AssetClass`](#asset-classes)                 |   ✅   |   ✅    |    ✅    |    ❌     |
| `country`  | Country of the holding       | ISO 3166-1 alpha-2 code (e.g. `US`)            |  ✅³   |   ✅    |    ✅    |    ✅     |
| `currency` | Currency of the holding      | ISO 4217 code (e.g. `USD`)                     |   ✅   |   ✅    |    ❌    |    ✅     |
| `rating`   | Credit rating of the holding | Provider's rating                              |   ❌   |   ❌    |    ❌    |    ✅     |

Values that have no standard equivalent (e.g. the sector of cash, or a supranational issuer as country) are `None`. Values that are not in the scraper's maps yet are `None` too, and are logged as warnings (`Unmapped ...`): please open an issue or a PR to add them.

Notes:

1. Amundi returns the Bloomberg ticker (e.g. `NVDA UW`).
2. Vanguard doesn't provide the sector of bonds: it is derived from the security type for government and securitized bonds, while corporate bonds have no sector.
3. Amundi returns the country of risk.

#### Sectors

`portfolio_scraper.utils.sector.Sector`: the 11 GICS sectors, plus two categories for bonds whose issuer is not a company.

| Value                                                                                                                                                                                       | Description                                    |
| ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------- |
| `Communication Services`, `Consumer Discretionary`, `Consumer Staples`, `Energy`, `Financials`, `Health Care`, `Industrials`, `Information Technology`, `Materials`, `Real Estate`, `Utilities` | GICS sectors                                   |
| `Government`                                                                                                                                                                                | Treasuries, sovereigns, agencies, supranationals |
| `Securitized`                                                                                                                                                                               | Covered bonds, MBS, ABS                        |

Sub-industries and bond sectors used by some providers (e.g. `Tabacco`, `Attività bancarie`) are mapped to their GICS sector.

#### Asset classes

`portfolio_scraper.utils.asset_class.AssetClass`:

| Value          | Description                                               |
| -------------- | --------------------------------------------------------- |
| `Equity`       | Stocks, preferred shares, depositary receipts, REITs, rights |
| `Fixed Income` | Bonds                                                     |
| `Cash`         | Cash, money market, collateral                            |
| `Derivatives`  | Futures, forwards, FX, swaps                              |
| `Fund`         | Other funds and ETFs                                      |
| `Alternative`  | Alternative investments                                   |

### Example: list every fund from every provider

```python
import pandas as pd
from portfolio_scraper.etf import (
    AmundiScraper,
    ISharesItScraper,
    VanguardItScraper,
    XTrackersItScraper,
)

frames = []
for scraper in [AmundiScraper(), ISharesItScraper(), VanguardItScraper(), XTrackersItScraper()]:
    df = scraper.get_listings()
    df["issuer"] = scraper.ISSUER
    frames.append(df)

listings = pd.concat(frames, ignore_index=True)
print(listings[listings["name"].str.contains("MSCI World")].sort_values("ter"))
```

## Streamlit apps

The apps live in the `app/` folder (with the helpers they share in `app/common.py`) and are meant to be run from the cloned repository with [uv](https://docs.astral.sh/uv/).

1. Install uv, if you don't have it yet:

   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

2. Clone the repository and install the dependencies. Streamlit and Plotly are part of the `dev` dependency group, which `uv sync` installs by default:

   ```bash
   git clone https://github.com/riccardotornesello/etf-scraping.git
   cd etf-scraping
   uv sync
   ```

3. Launch an app with `uv run`, which runs the command inside the project's virtual environment (no need to activate it):

   ```bash
   uv run streamlit run app/listings.py
   ```

Then open the URL printed in the terminal (default http://localhost:8501). To use a different port, add `--server.port 8502`.

### Listings (`app/listings.py`)

Shows the listings of **all the scrapers in a single table**, with:

- a filter by scraper;
- a text search on name, ISIN and internal id;
- a TER range filter;
- the export of the filtered table as CSV.

Listings are cached for one day; use the _Refresh data_ button in the sidebar to fetch them again.

### ETF analysis (`app/etf.py`)

Analyses a single fund: pick the scraper and search the fund by name or ISIN in the sidebar.

- **Key figures**: TER, number of holdings, weight of the top 10 holdings, effective number of holdings and sum of the weights.
- **Composition**: pie charts by country, sector, asset class and currency.
- **Map**: geographic distribution of the weights.
- **Concentration**: the largest holdings, the cumulative weight curve and statistics like the weight of the top N holdings, the holdings needed to reach 50/80/90% of the fund and the HHI.
- **Holdings**: all the holdings in a table, downloadable as CSV.

The sidebar filters (asset class, sector, country, currency) apply to all the tabs. The selected fund is kept in the URL (`?scraper=...&isin=...`), so the page can be bookmarked or shared.

```bash
uv run streamlit run app/etf.py
```

### Portfolio (`app/app.py`)

![Dashboard](docs/dashboard.png "Dashboard")

Lets you build a portfolio of ETFs and analyse what's inside it:

- **Portfolio**: add ETFs by ISIN, scraper and value in euro (the ISIN is checked against the scraper's listings), edit them in a table, import/export the list as CSV.
- **ETFs**: summary of each ETF with name, TER, number of holdings and portfolio weight; total value, weighted TER and annual cost of the portfolio.
- **Composition**: pie charts by country, sector, asset class and currency.
- **Map**: geographic distribution of the invested value.
- **Top holdings**: the largest holdings of the whole portfolio, with the same company summed across ETFs (matched by name, so it is approximate).
- **Holdings**: all the holdings in a table, downloadable as CSV.

The sidebar filters (ETF, asset class, sector, country, currency) apply to all the analysis tabs.

Holdings are cached for one hour and listings for one day.

```bash
uv run streamlit run app/app.py
```

## Development

```bash
uv sync
```

Run the tests (they hit the providers' websites, so they need an internet connection):

```bash
uv run pytest
```

Lint and format:

```bash
uv run ruff check
uv run ruff format
```

### Adding a scraper

1. Create a class that extends `EtfBaseScraper` (or the provider's base class, to add a new country).
2. Implement `get_raw_listings()` and `get_raw_holdings(id)`.
3. Optionally override `get_issuer_listings()` / `get_issuer_holdings(id)` to clean up the raw data.
4. Set `LISTINGS_COLUMN_NAMES` and `HOLDINGS_COLUMN_NAMES`, mapping each standard column to the provider's column in the issuer DataFrame.
5. Set the attributes that normalise the holdings values (keys are uppercase):
   - `WEIGHT_SCALE`: factor to convert the weight to a fraction (`0.01` if the provider uses percentages);
   - `COUNTRIES_LANGUAGE`: language of the country names (`"en"`, `"it"`, …), or `None` if they are alpha-2 codes; `COUNTRIES_MAP` for the names that the standard maps don't know;
   - `SECTORS_MAP`: provider's sectors to `Sector` (the English GICS names are already mapped);
   - `ASSET_CLASSES_MAP`: provider's holding types to `AssetClass`.
6. Export it from `portfolio_scraper/etf/__init__.py` and add a test class in `tests/test_etf.py`. The tests check that all the values are mapped.

## Disclaimer

This is an **unofficial** project. It is not affiliated with, endorsed by, or supported by Amundi, BlackRock/iShares, Vanguard, DWS/Xtrackers, or any other fund provider. All trademarks belong to their respective owners.

The data is scraped from public websites whose structure and content may change or become unavailable at any time. **No guarantee** is given about the accuracy, completeness, timeliness or availability of the data. It is provided "as is", without warranty of any kind. Do not rely on it for investment decisions - always verify against the providers' official sources. Use at your own risk, and make sure your usage complies with each provider's terms of service.

## Credits

Thanks to https://github.com/mledoze/countries for the countries database.
