"""
Helpers shared by the Streamlit apps.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import pycountry

from portfolio_scraper.etf import (
    AmundiScraper,
    ISharesItScraper,
    XTrackersItScraper,
    VanguardItScraper,
)


# For each scraper, the listings column to pass to get_holdings()
SCRAPERS = {
    "Amundi": {"class": AmundiScraper, "holdings_id": "isin"},
    "iShares (IT)": {"class": ISharesItScraper, "holdings_id": "internal_id"},
    "Vanguard (IT)": {"class": VanguardItScraper, "holdings_id": "internal_id"},
    "Xtrackers (IT)": {"class": XTrackersItScraper, "holdings_id": "isin"},
}

UNKNOWN = "Unknown"

# Columns that can be used to filter the holdings, with their labels
FILTER_COLUMNS = {
    "asset_class": "Asset class",
    "sector_name": "Sector",
    "country_name": "Country",
    "currency": "Currency",
}

# Columns that can be used to group the holdings in the charts, with their titles
COMPOSITION_COLUMNS = {
    "country_name": "By country",
    "sector_name": "By sector",
    "asset_class": "By asset class",
    "currency": "By currency",
}


############################
# COUNTRIES
############################
def alpha2_to_alpha3(code: str) -> str | None:
    """Convert an ISO 3166-1 alpha-2 country code to alpha-3 for the map."""
    try:
        country = pycountry.countries.get(alpha_2=str(code).upper())
        return country.alpha_3 if country else None
    except (KeyError, AttributeError):
        return None


def alpha2_to_name(code: str) -> str:
    """Human-readable country name for an ISO 3166-1 alpha-2 code."""
    try:
        country = pycountry.countries.get(alpha_2=str(code).upper())
        return country.name if country else str(code)
    except (KeyError, AttributeError):
        return str(code)


############################
# DATA
############################
@st.cache_data(ttl="1d", show_spinner=False)
def load_listings(scraper_name: str) -> pd.DataFrame:
    df = SCRAPERS[scraper_name]["class"]().get_listings()
    df["internal_id"] = df["internal_id"].astype(str)
    return df.drop_duplicates(subset="isin")


def find_listing(scraper_name: str, isin: str) -> pd.Series | None:
    listings = load_listings(scraper_name)
    match = listings[listings["isin"] == isin]
    return match.iloc[0] if not match.empty else None


@st.cache_data(ttl="1h", show_spinner=False)
def fetch_holdings(scraper_name: str, isin: str) -> pd.DataFrame:
    """Fetch the holdings of an ETF in the standard format."""
    config = SCRAPERS[scraper_name]
    listing = find_listing(scraper_name, isin)
    if listing is None:
        raise ValueError(f"ISIN {isin} not found in the {scraper_name} listings")
    holdings_id = isin if config["holdings_id"] == "isin" else listing["internal_id"]
    return config["class"]().get_holdings(holdings_id)


def add_display_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Add the columns used in the charts, with "Unknown" for the missing values."""
    df = df.copy()
    df["country_name"] = df["country"].map(
        lambda c: alpha2_to_name(c) if isinstance(c, str) else UNKNOWN
    )
    df["sector_name"] = df["sector"].fillna(UNKNOWN)
    df["asset_class"] = df["type"].fillna(UNKNOWN) if "type" in df else UNKNOWN
    return df


############################
# UI
############################
def sidebar_filters(df: pd.DataFrame, columns: dict[str, str]) -> pd.DataFrame:
    """Show a multiselect in the sidebar for each column and return the filtered rows."""
    st.sidebar.header("Filters")
    filtered = df
    for column, label in columns.items():
        if column not in df.columns:
            continue
        options = sorted(df[column].dropna().astype(str).unique())
        if len(options) < 2:
            continue
        selected = st.sidebar.multiselect(label, options)
        if selected:
            filtered = filtered[filtered[column].isin(selected)]
    return filtered


def composition_pie(
    df: pd.DataFrame,
    column: str,
    value_column: str,
    title: str,
    max_slices: int,
    value_label: str,
):
    """Pie chart of value_column grouped by column, with the smallest slices in "Other"."""
    agg = (
        df.assign(**{column: df[column].fillna(UNKNOWN)})
        .groupby(column, as_index=False)[value_column]
        .sum()
        .sort_values(value_column, ascending=False)
    )
    if len(agg) > max_slices:
        other = agg.iloc[max_slices - 1 :][value_column].sum()
        agg = pd.concat(
            [
                agg.iloc[: max_slices - 1],
                pd.DataFrame({column: ["Other"], value_column: [other]}),
            ],
            ignore_index=True,
        )
    fig = px.pie(
        agg,
        names=column,
        values=value_column,
        title=title,
        hole=0.4,
        labels={value_column: value_label},
    )
    fig.update_traces(textposition="inside", textinfo="percent+label")
    fig.update_layout(showlegend=False)
    return fig


def composition_charts(
    df: pd.DataFrame, value_column: str, value_label: str, key: str = "slices"
):
    """Pie charts of the composition, two per row."""
    max_slices = st.slider("Max slices per chart", 3, 20, 10, key=key)
    pies = {c: t for c, t in COMPOSITION_COLUMNS.items() if c in df.columns}
    items = list(pies.items())
    for i in range(0, len(items), 2):
        for col, (column, title) in zip(st.columns(2), items[i : i + 2]):
            col.plotly_chart(
                composition_pie(
                    df, column, value_column, title, max_slices, value_label
                ),
                width="stretch",
            )


def country_map(df: pd.DataFrame, value_column: str, value_label: str):
    """Choropleth of value_column by country."""
    geo = (
        df.dropna(subset=["country"])
        .groupby("country", as_index=False)[value_column]
        .sum()
    )
    geo["iso_alpha3"] = geo["country"].map(alpha2_to_alpha3)
    geo["country_name"] = geo["country"].map(alpha2_to_name)
    geo["share"] = geo[value_column] / df[value_column].sum()
    geo = geo.dropna(subset=["iso_alpha3"])

    if geo.empty:
        st.info("No country data available for the current holdings.")
        return

    fig = px.choropleth(
        geo,
        locations="iso_alpha3",
        color=value_column,
        hover_name="country_name",
        hover_data={"iso_alpha3": False, "share": ":.2%"},
        color_continuous_scale="Blues",
        labels={value_column: value_label, "share": "Share"},
    )
    fig.update_layout(margin=dict(l=0, r=0, t=0, b=0), height=550)
    st.plotly_chart(fig, width="stretch")
