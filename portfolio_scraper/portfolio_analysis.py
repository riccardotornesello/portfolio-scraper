from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from portfolio_scraper.etf import ISharesItScraper, VanguardItScraper, XtrackersItScraper

SCRAPERS: dict[str, type] = {
    "iShares (IT)": ISharesItScraper,
    "Vanguard (IT)": VanguardItScraper,
    "Xtrackers (IT)": XtrackersItScraper,
}

PORTFOLIO_COLUMNS = ["isin", "scraper", "investment_eur"]
UNKNOWN_VALUE = "Unknown"


def empty_portfolio() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "isin": pd.Series(dtype="str"),
            "scraper": pd.Series(dtype="str"),
            "investment_eur": pd.Series(dtype="float"),
        }
    )


def _normalize_string(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, float) and pd.isna(value):
        return ""
    return str(value).strip()


def _normalize_unknown(value: Any) -> str:
    cleaned = _normalize_string(value)
    if not cleaned or cleaned == "-":
        return UNKNOWN_VALUE
    return cleaned


def validate_portfolio(portfolio: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    missing = [column for column in PORTFOLIO_COLUMNS if column not in portfolio.columns]
    if missing:
        return empty_portfolio(), [
            f"Missing required columns: {', '.join(missing)}"
        ]

    selected = portfolio[PORTFOLIO_COLUMNS].copy()
    selected["isin"] = selected["isin"].apply(_normalize_string).str.upper()
    selected["scraper"] = selected["scraper"].apply(_normalize_string)

    investment_errors = (
        pd.to_numeric(selected["investment_eur"], errors="coerce").isna()
        & selected["investment_eur"].apply(_normalize_string).ne("")
    )
    selected["investment_eur"] = pd.to_numeric(selected["investment_eur"], errors="coerce")

    fully_empty = (
        selected["isin"].eq("")
        & selected["scraper"].eq("")
        & selected["investment_eur"].isna()
    )
    selected = selected.loc[~fully_empty].reset_index(drop=True)
    investment_errors = investment_errors.loc[~fully_empty].reset_index(drop=True)

    errors: list[str] = []
    valid_rows: list[dict[str, Any]] = []

    for idx, row in selected.iterrows():
        row_num = idx + 1
        row_errors: list[str] = []

        isin = row["isin"]
        scraper_name = row["scraper"]
        investment = row["investment_eur"]

        if not isin:
            row_errors.append("ISIN cannot be empty")

        if scraper_name not in SCRAPERS:
            row_errors.append(f"Invalid scraper '{scraper_name}'")

        if investment_errors.iloc[idx]:
            row_errors.append("Investment must be numeric")
        elif pd.isna(investment):
            row_errors.append("Investment is required")
        elif float(investment) < 0:
            row_errors.append("Investment must be >= 0")

        if row_errors:
            errors.append(f"Row {row_num}: {'; '.join(row_errors)}")
            continue

        valid_rows.append(
            {
                "isin": isin,
                "scraper": scraper_name,
                "investment_eur": float(investment),
            }
        )

    valid_df = pd.DataFrame(valid_rows, columns=PORTFOLIO_COLUMNS)
    return valid_df, errors


def parse_portfolio_csv(path: str) -> pd.DataFrame:
    try:
        frame = pd.read_csv(path)
    except pd.errors.EmptyDataError as exc:
        raise ValueError("CSV is empty") from exc
    except pd.errors.ParserError as exc:
        raise ValueError(f"CSV parsing error: {exc}") from exc
    except UnicodeDecodeError as exc:
        raise ValueError("CSV encoding is not valid UTF-8") from exc
    except Exception as exc:  # noqa: BLE001
        raise ValueError(f"Unable to read CSV: {exc}") from exc

    missing = [column for column in PORTFOLIO_COLUMNS if column not in frame.columns]
    if missing:
        raise ValueError(
            "Missing required CSV columns: " + ", ".join(missing)
        )

    return frame[PORTFOLIO_COLUMNS].copy()


def portfolio_to_csv(portfolio: pd.DataFrame) -> bytes:
    frame = portfolio.copy()
    for column in PORTFOLIO_COLUMNS:
        if column not in frame.columns:
            frame[column] = ""
    return frame[PORTFOLIO_COLUMNS].to_csv(index=False).encode("utf-8")


def build_combined_holdings(
    portfolio: pd.DataFrame,
    scraper_map: dict[str, type] | None = None,
) -> tuple[pd.DataFrame, list[str], pd.DataFrame]:
    valid_portfolio, validation_errors = validate_portfolio(portfolio)
    if valid_portfolio.empty:
        return pd.DataFrame(), validation_errors, valid_portfolio

    total_invested = float(valid_portfolio["investment_eur"].sum())
    if total_invested <= 0:
        return (
            pd.DataFrame(),
            validation_errors + ["Total investment must be greater than zero"],
            valid_portfolio,
        )

    active_scrapers = scraper_map or SCRAPERS
    frames: list[pd.DataFrame] = []
    scraping_errors: list[str] = []

    for _, row in valid_portfolio.iterrows():
        isin = row["isin"]
        scraper_name = row["scraper"]
        investment_eur = float(row["investment_eur"])
        etf_fraction = investment_eur / total_invested

        try:
            scraper = active_scrapers[scraper_name]()
            holdings = scraper.get_holdings_by_isin(isin).copy()
        except Exception as exc:  # noqa: BLE001
            scraping_errors.append(f"{isin} ({scraper_name}): {exc}")
            continue

        holdings["weight_in_etf"] = pd.to_numeric(
            holdings.get("weight_in_etf"), errors="coerce"
        )

        holdings["etf_isin"] = isin
        holdings["etf_origin"] = scraper_name
        holdings["etf_investment_eur"] = investment_eur
        holdings["etf_fraction"] = etf_fraction
        holdings["weighted_portfolio_weight"] = holdings["weight_in_etf"] * etf_fraction
        holdings["estimated_value_eur"] = holdings["weighted_portfolio_weight"] * total_invested
        holdings["holding_name"] = holdings.get("name", pd.Series(dtype="str")).apply(
            _normalize_unknown
        )
        holdings["holding_isin"] = holdings.get("isin", pd.Series(dtype="str")).apply(
            _normalize_string
        )
        holdings["country"] = holdings.get("location", pd.Series(dtype="str")).apply(
            _normalize_unknown
        )
        holdings["sector_group"] = holdings.get("sector", pd.Series(dtype="str")).apply(
            _normalize_unknown
        )
        holdings["asset_type"] = holdings.get("asset_class", pd.Series(dtype="str")).apply(
            _normalize_unknown
        )

        frames.append(holdings)

    if not frames:
        return pd.DataFrame(), validation_errors + scraping_errors, valid_portfolio

    combined = pd.concat(frames, ignore_index=True)
    combined["weighted_portfolio_weight"] = pd.to_numeric(
        combined["weighted_portfolio_weight"], errors="coerce"
    ).fillna(0.0)
    combined["estimated_value_eur"] = pd.to_numeric(
        combined["estimated_value_eur"], errors="coerce"
    ).fillna(0.0)

    display_columns = [
        "etf_origin",
        "etf_isin",
        "holding_name",
        "holding_isin",
        "country",
        "sector_group",
        "asset_type",
        "weight_in_etf",
        "weighted_portfolio_weight",
        "estimated_value_eur",
        "ticker",
        "currency",
        "exchange",
    ]
    for column in display_columns:
        if column not in combined.columns:
            combined[column] = pd.NA
    combined = combined[display_columns].sort_values(
        "weighted_portfolio_weight", ascending=False
    )

    return combined.reset_index(drop=True), validation_errors + scraping_errors, valid_portfolio


def apply_holdings_filters(
    holdings: pd.DataFrame,
    search_text: str,
    etf_isins: list[str],
    countries: list[str],
    sectors: list[str],
    asset_types: list[str],
) -> pd.DataFrame:
    if holdings.empty:
        return holdings

    filtered = holdings.copy()
    if etf_isins:
        filtered = filtered[filtered["etf_isin"].isin(etf_isins)]
    if countries:
        filtered = filtered[filtered["country"].isin(countries)]
    if sectors:
        filtered = filtered[filtered["sector_group"].isin(sectors)]
    if asset_types:
        filtered = filtered[filtered["asset_type"].isin(asset_types)]

    query = _normalize_string(search_text)
    if query:
        mask = (
            filtered["holding_name"].str.contains(query, case=False, na=False)
            | filtered["holding_isin"].str.contains(query, case=False, na=False)
            | filtered["etf_isin"].str.contains(query, case=False, na=False)
        )
        filtered = filtered[mask]

    return filtered.reset_index(drop=True)


def allocation_table(holdings: pd.DataFrame, group_col: str) -> pd.DataFrame:
    if holdings.empty or group_col not in holdings.columns:
        return pd.DataFrame(columns=[group_col, "weighted_portfolio_weight", "estimated_value_eur"])

    aggregated = (
        holdings.groupby(group_col, dropna=False)[
            ["weighted_portfolio_weight", "estimated_value_eur"]
        ]
        .sum()
        .reset_index()
        .sort_values("weighted_portfolio_weight", ascending=False)
    )
    aggregated[group_col] = aggregated[group_col].apply(_normalize_unknown)
    return aggregated


def compute_kpis(filtered_holdings: pd.DataFrame, portfolio: pd.DataFrame, top_n: int = 10) -> dict[str, float | int]:
    total_invested = float(pd.to_numeric(portfolio.get("investment_eur", 0), errors="coerce").fillna(0).sum())
    top_sum = (
        filtered_holdings.nlargest(top_n, "weighted_portfolio_weight")["weighted_portfolio_weight"].sum()
        if not filtered_holdings.empty
        else 0.0
    )
    return {
        "total_invested": total_invested,
        "etf_count": int(portfolio["isin"].nunique()) if "isin" in portfolio.columns else 0,
        "unique_holdings": int(filtered_holdings["holding_isin"].replace("", pd.NA).dropna().nunique())
        if "holding_isin" in filtered_holdings.columns
        else 0,
        "rows_after_filters": int(len(filtered_holdings)),
        "top_n_concentration": float(top_sum),
    }


def _empty_figure(title: str) -> go.Figure:
    fig = go.Figure()
    fig.update_layout(title=title)
    return fig


def pie_figure(holdings: pd.DataFrame, column: str, title: str) -> go.Figure:
    aggregated = allocation_table(holdings, column)
    aggregated = aggregated[aggregated["weighted_portfolio_weight"] > 0]
    if aggregated.empty:
        return _empty_figure(title)

    fig = px.pie(
        aggregated,
        names=column,
        values="weighted_portfolio_weight",
        title=title,
        hole=0.35,
    )
    fig.update_traces(textposition="inside", textinfo="percent+label")
    return fig


def top_holdings_bar_figure(holdings: pd.DataFrame, top_n: int = 15) -> go.Figure:
    if holdings.empty:
        return _empty_figure("Top holdings by estimated value")

    top = holdings.nlargest(top_n, "estimated_value_eur")
    fig = px.bar(
        top,
        x="estimated_value_eur",
        y="holding_name",
        color="sector_group",
        orientation="h",
        title=f"Top {top_n} holdings by estimated value (€)",
    )
    fig.update_layout(yaxis={"categoryorder": "total ascending"})
    return fig


def sunburst_figure(holdings: pd.DataFrame) -> go.Figure:
    if holdings.empty:
        return _empty_figure("Portfolio hierarchy")

    fig = px.sunburst(
        holdings,
        path=["asset_type", "sector_group", "country", "holding_name"],
        values="estimated_value_eur",
        title="Portfolio hierarchy (asset type → sector → country → holding)",
    )
    return fig


def etf_exposure_figure(holdings: pd.DataFrame) -> go.Figure:
    aggregated = allocation_table(holdings, "etf_isin")
    if aggregated.empty:
        return _empty_figure("Exposure by ETF")

    fig = px.bar(
        aggregated,
        x="etf_isin",
        y="estimated_value_eur",
        color="etf_isin",
        title="Estimated exposure by ETF (€)",
    )
    fig.update_layout(showlegend=False)
    return fig


def _iso_to_name_map() -> dict[str, str]:
    countries_path = Path(__file__).resolve().parent / "assets" / "countries.json"
    with countries_path.open("r", encoding="utf-8") as file:
        countries = json.load(file)

    mapping: dict[str, str] = {}
    for country in countries:
        iso = country.get("cca2")
        name = country.get("name", {}).get("common")
        if iso and name:
            mapping[iso] = name
    return mapping


def world_map_figure(holdings: pd.DataFrame) -> go.Figure:
    aggregated = allocation_table(holdings, "country")
    if aggregated.empty:
        return _empty_figure("Global exposure map")

    iso_map = _iso_to_name_map()
    aggregated = aggregated[aggregated["country"].isin(iso_map)]
    if aggregated.empty:
        return _empty_figure("Global exposure map")

    aggregated["country_name"] = aggregated["country"].map(iso_map)

    fig = px.choropleth(
        aggregated,
        locations="country_name",
        locationmode="country names",
        color="estimated_value_eur",
        hover_name="country_name",
        color_continuous_scale="Blues",
        title="Global exposure map by country (€)",
    )
    return fig
