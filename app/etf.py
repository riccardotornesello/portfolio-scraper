import streamlit as st
import pandas as pd
import plotly.express as px

from common import (
    FILTER_COLUMNS,
    SCRAPERS,
    add_display_columns,
    composition_charts,
    country_map,
    fetch_holdings,
    load_listings,
    sidebar_filters,
)


def concentration_stats(weights: pd.Series) -> dict:
    """Concentration statistics of the (positive) weights of the holdings."""
    weights = weights[weights > 0].sort_values(ascending=False)
    shares = weights / weights.sum()
    cumulative = shares.cumsum()

    def holdings_for(share: float) -> int:
        return int((cumulative < share).sum()) + 1

    return {
        "effective_holdings": 1 / (shares**2).sum(),
        "hhi": (shares**2).sum() * 10_000,
        "top": {n: weights.head(n).sum() for n in (1, 5, 10, 25, 50, 100)},
        "holdings_for": {s: holdings_for(s) for s in (0.5, 0.8, 0.9)},
    }


############################
# LAYOUT
############################
st.set_page_config(
    page_title="ETF analysis",
    page_icon="🔎",
    layout="wide",
)

############################
# ETF SELECTION
############################
st.sidebar.header("ETF")

# The selected ETF is kept in the URL, so the page can be shared and reloaded
scraper_names = list(SCRAPERS.keys())
query_scraper = st.query_params.get("scraper")
scraper_name = st.sidebar.selectbox(
    "Scraper",
    scraper_names,
    index=scraper_names.index(query_scraper) if query_scraper in scraper_names else 0,
)

try:
    with st.spinner(f"Fetching the {scraper_name} listings..."):
        listings = load_listings(scraper_name)
except Exception as e:
    st.error(f"Failed to fetch the {scraper_name} listings: {e}")
    st.stop()

listings = listings.sort_values("name")
isins = listings["isin"].tolist()
labels = dict(zip(listings["isin"], listings["name"] + " · " + listings["isin"]))
query_isin = st.query_params.get("isin")
isin = st.sidebar.selectbox(
    "Fund",
    isins,
    index=isins.index(query_isin) if query_isin in isins else None,
    format_func=lambda i: labels[i],
    placeholder="Search by name or ISIN",
)

st.query_params["scraper"] = scraper_name
if isin is None:
    st.query_params.pop("isin", None)
    st.title("🔎 ETF analysis")
    st.info("Select a fund in the sidebar to analyse its holdings.")
    st.stop()
st.query_params["isin"] = isin

listing = listings[listings["isin"] == isin].iloc[0]

############################
# DATA
############################
try:
    with st.spinner(f"Fetching the holdings of {listing['name']}..."):
        holdings_all = add_display_columns(fetch_holdings(scraper_name, isin))
except Exception as e:
    st.error(f"Failed to fetch the holdings of {isin}: {e}")
    st.stop()

if holdings_all.empty:
    st.warning("The provider returned no holdings for this fund.")
    st.stop()

############################
# APP
############################
st.title(f"🔎 {listing['name']}")
st.caption(f"{isin} · {scraper_name} · internal id {listing['internal_id']}")

stats = concentration_stats(holdings_all["weight"].dropna())
weights_sum = holdings_all["weight"].sum()

col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("TER", f"{listing['ter']:.2f} %" if pd.notna(listing["ter"]) else "n/a")
col2.metric("Holdings", len(holdings_all))
col3.metric("Top 10 weight", f"{stats['top'][10]:.1%}")
col4.metric(
    "Effective holdings",
    f"{stats['effective_holdings']:,.0f}",
    help="Number of equally-weighted holdings that would give the same "
    "concentration (1 / sum of the squared weights).",
)
col5.metric(
    "Weights sum",
    f"{weights_sum:.1%}",
    help="Sum of the weights of the holdings. "
    "Far from 100% means the data is incomplete.",
)
if abs(weights_sum - 1) > 0.02:
    st.warning(
        f"The holdings sum to {weights_sum:.1%}: the composition may be incomplete."
    )

holdings = sidebar_filters(holdings_all, FILTER_COLUMNS)
if len(holdings) != len(holdings_all):
    st.info(
        f"Filters active: {len(holdings)} holdings, "
        f"{holdings['weight'].sum():.1%} of the fund."
    )
if holdings.empty:
    st.warning("No holdings match the current filters.")
    st.stop()

tab_composition, tab_map, tab_concentration, tab_holdings = st.tabs(
    ["Composition", "Map", "Concentration", "Holdings"]
)

with tab_composition:
    composition_charts(holdings, "weight", "Weight")
    if "type" not in holdings_all.columns:
        st.caption(f"{scraper_name} does not provide the asset class of its holdings.")

with tab_map:
    country_map(holdings, "weight", "Weight")

with tab_concentration:
    top_n = st.slider("Holdings to show", 5, 100, 20, step=5)
    top = holdings.nlargest(top_n, "weight").iloc[::-1]
    fig_top = px.bar(
        top,
        x="weight",
        y="name",
        orientation="h",
        color="sector_name",
        hover_data={"country_name": True, "asset_class": True},
        labels={
            "weight": "Weight",
            "name": "",
            "sector_name": "Sector",
            "country_name": "Country",
            "asset_class": "Asset class",
        },
        title=f"Top {top_n} holdings",
    )
    fig_top.update_layout(
        xaxis_tickformat=".1%", height=max(400, 22 * len(top)), yaxis_type="category"
    )
    st.plotly_chart(fig_top, width="stretch")

    col_curve, col_stats = st.columns([2, 1])

    curve = (
        holdings_all[holdings_all["weight"] > 0]["weight"]
        .sort_values(ascending=False)
        .reset_index(drop=True)
    )
    curve = pd.DataFrame(
        {"holdings": range(1, len(curve) + 1), "cumulative": curve.cumsum()}
    )
    fig_curve = px.line(
        curve,
        x="holdings",
        y="cumulative",
        title="Cumulative weight",
        labels={"holdings": "Number of holdings", "cumulative": "Cumulative weight"},
    )
    fig_curve.update_layout(yaxis_tickformat=".0%")
    col_curve.plotly_chart(fig_curve, width="stretch")

    col_stats.subheader("Statistics")
    col_stats.caption("Computed on the whole fund, without filters.")
    col_stats.dataframe(
        pd.DataFrame(
            [
                *[
                    (f"Top {n} weight", f"{w:.1%}")
                    for n, w in stats["top"].items()
                    if n <= len(holdings_all)
                ],
                *[
                    (f"Holdings for {s:.0%} of the fund", f"{n:,}")
                    for s, n in stats["holdings_for"].items()
                ],
                ("Effective holdings", f"{stats['effective_holdings']:,.1f}"),
                ("HHI", f"{stats['hhi']:,.0f}"),
            ],
            columns=["Statistic", "Value"],
        ),
        hide_index=True,
        width="stretch",
    )

with tab_holdings:
    columns = [
        "name",
        "ticker",
        "isin",
        "weight",
        "asset_class",
        "sector_name",
        "country_name",
        "currency",
        "rating",
    ]
    columns = [c for c in columns if c in holdings.columns]
    st.dataframe(
        holdings[columns].sort_values("weight", ascending=False),
        hide_index=True,
        width="stretch",
        column_config={
            "name": st.column_config.TextColumn("Name", width="large"),
            "ticker": "Ticker",
            "isin": "ISIN",
            "weight": st.column_config.ProgressColumn(
                "Weight",
                format="percent",
                min_value=0,
                max_value=float(max(holdings["weight"].max(), 0.0001)),
            ),
            "asset_class": "Asset class",
            "sector_name": "Sector",
            "country_name": "Country",
            "currency": "Currency",
            "rating": "Rating",
        },
    )
    st.download_button(
        "Download holdings (CSV)",
        holdings.to_csv(index=False).encode("utf-8"),
        file_name=f"{isin}_holdings.csv",
        mime="text/csv",
    )
