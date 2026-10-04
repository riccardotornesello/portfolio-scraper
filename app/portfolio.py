import re
import threading
from concurrent.futures import ThreadPoolExecutor

import streamlit as st
import pandas as pd
from streamlit.runtime.scriptrunner import add_script_run_ctx, get_script_run_ctx

from common import (
    FILTER_COLUMNS,
    SCRAPERS,
    add_display_columns,
    composition_charts,
    country_map,
    fetch_holdings,
    find_listing,
    sidebar_filters,
)


# Scraper names used by older versions of the app, for CSV imports
LEGACY_SCRAPER_NAMES = {"Amundi (IT)": "Amundi"}

ISIN_REGEX = re.compile(r"^[A-Z]{2}[A-Z0-9]{9}[0-9]$")

# Suffixes removed from holding names to match the same company across ETFs
NAME_SUFFIXES_REGEX = re.compile(
    r"(\s+(INC|CORP|CORPORATION|CO|COMPANY|LTD|LIMITED|PLC|SA|SE|AG|NV|AB|ASA|"
    r"SPA|HOLDINGS?|GROUP|REIT|ADR|REG|CLASS [A-Z]|CL [A-Z]|[A-Z]))+$"
)


def holding_key(name: str) -> str:
    """Approximate key to match the same holding across ETFs of different providers."""
    key = re.sub(r"[^A-Z0-9 ]", " ", str(name).upper())
    key = re.sub(r"\s+", " ", key).strip()
    return NAME_SUFFIXES_REGEX.sub("", key) or key


############################
# DATA
############################
def scrape_portfolio(etfs: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    """
    Scrape all the ETFs of the portfolio in parallel.
    Returns the holdings, a summary of each ETF and the errors by ISIN.
    """
    ctx = get_script_run_ctx()

    def scrape(row) -> pd.DataFrame:
        df = fetch_holdings(row["Scraper"], row["ISIN"])
        return add_display_columns(df)

    rows = [row for _, row in etfs.iterrows()]
    with ThreadPoolExecutor(
        max_workers=4,
        initializer=lambda: add_script_run_ctx(threading.current_thread(), ctx),
    ) as executor:
        futures = [executor.submit(scrape, row) for row in rows]

    holdings, summary, errors = [], [], {}
    for row, future in zip(rows, futures):
        try:
            etf_holdings = future.result()
        except Exception as e:
            errors[row["ISIN"]] = f"{row['Scraper']}: {e}"
            continue

        listing = find_listing(row["Scraper"], row["ISIN"])
        etf_holdings["etf_isin"] = row["ISIN"]
        etf_holdings["etf_name"] = listing["name"]
        etf_holdings["etf_scraper"] = row["Scraper"]
        etf_holdings["etf_value"] = row["Value"]
        etf_holdings["value_in_portfolio"] = (
            etf_holdings["weight"].fillna(0) * row["Value"]
        )
        holdings.append(etf_holdings)

        summary.append(
            {
                "ISIN": row["ISIN"],
                "Name": listing["name"],
                "Scraper": row["Scraper"],
                "Value": row["Value"],
                "TER": listing["ter"],
                "Holdings": len(etf_holdings),
                "Weights sum": etf_holdings["weight"].sum(),
            }
        )

    holdings_df = pd.concat(holdings, ignore_index=True) if holdings else None
    summary_df = pd.DataFrame(summary)
    if not summary_df.empty:
        summary_df["Portfolio weight"] = summary_df["Value"] / summary_df["Value"].sum()
    return holdings_df, summary_df, errors


def reset_results():
    st.session_state.holdings = None
    st.session_state.summary = None
    st.session_state.errors = {}


############################
# LAYOUT
############################
st.set_page_config(
    page_title="Portfolio scraper",
    page_icon="💵",
    layout="wide",
)

############################
# SESSION STATE
############################
if "etfs" not in st.session_state:
    st.session_state.etfs = pd.DataFrame(
        {
            "ISIN": pd.Series(dtype="str"),
            "Scraper": pd.Series(dtype="str"),
            "Value": pd.Series(dtype="float"),
        }
    )
if "holdings" not in st.session_state:
    reset_results()
if "imported_file_id" not in st.session_state:
    st.session_state.imported_file_id = None


############################
# APP
############################
st.title("💵 Portfolio scraper")
st.caption("Scrape the portfolio of ETFs and analyze its composition.")

st.header("Portfolio")

with st.form("form_add_etf", clear_on_submit=True):
    col1, col2, col3 = st.columns(3)
    isin = col1.text_input("ISIN", placeholder="IE00B4L5Y983")
    scraper = col2.selectbox("Scraper", list(SCRAPERS.keys()))
    value = col3.number_input("Value (EUR)", min_value=0.0, step=100.0)

    add = st.form_submit_button("Add", width="stretch")

if add:
    isin = isin.strip().upper()
    already_added = (
        (st.session_state.etfs["ISIN"] == isin)
        & (st.session_state.etfs["Scraper"] == scraper)
    ).any()

    if not ISIN_REGEX.match(isin):
        st.error(f"'{isin}' is not a valid ISIN.")
    elif value <= 0:
        st.error("The value must be greater than 0.")
    elif already_added:
        st.error(f"{isin} is already in the portfolio: edit its value in the table.")
    else:
        with st.spinner(f"Looking for {isin} in the {scraper} listings..."):
            try:
                listing = find_listing(scraper, isin)
            except Exception as e:
                listing = None
                st.error(f"Failed to fetch the {scraper} listings: {e}")
        if listing is not None:
            st.session_state.etfs = pd.concat(
                [
                    st.session_state.etfs,
                    pd.DataFrame(
                        {"ISIN": [isin], "Scraper": [scraper], "Value": [value]}
                    ),
                ],
                ignore_index=True,
            )
            reset_results()
            st.success(f"Added {listing['name']} ({isin}), {value:,.2f} EUR.")
        else:
            st.error(
                f"{isin} not found in the {scraper} listings. "
                "Check the ISIN or try another scraper."
            )

# Import / export
col_imp, col_exp = st.columns(2)

uploaded = col_imp.file_uploader("Import ETFs (CSV)", type="csv")
# The uploader keeps the file across reruns: import it only once
if uploaded is not None and uploaded.file_id != st.session_state.imported_file_id:
    st.session_state.imported_file_id = uploaded.file_id
    imported = pd.read_csv(uploaded)
    missing = {"ISIN", "Scraper", "Value"} - set(imported.columns)
    if missing:
        col_imp.error(f"Missing columns in CSV: {', '.join(sorted(missing))}.")
    else:
        imported = imported[["ISIN", "Scraper", "Value"]].copy()
        imported["ISIN"] = imported["ISIN"].astype(str).str.strip().str.upper()
        imported["Scraper"] = imported["Scraper"].replace(LEGACY_SCRAPER_NAMES)
        unknown = set(imported["Scraper"]) - set(SCRAPERS)
        if unknown:
            col_imp.error(f"Unknown scrapers in CSV: {', '.join(sorted(unknown))}.")
        else:
            st.session_state.etfs = imported
            reset_results()
            col_imp.success(f"Imported {len(imported)} ETFs.")

col_exp.download_button(
    "Export ETFs (CSV)",
    data=st.session_state.etfs.to_csv(index=False).encode("utf-8"),
    file_name="etfs.csv",
    mime="text/csv",
    width="stretch",
    disabled=st.session_state.etfs.empty,
)

# Editable table with row deletion
edited = st.data_editor(
    st.session_state.etfs,
    hide_index=True,
    num_rows="dynamic",
    width="stretch",
    column_config={
        "ISIN": st.column_config.TextColumn(required=True),
        "Scraper": st.column_config.SelectboxColumn(
            options=list(SCRAPERS.keys()), required=True
        ),
        "Value": st.column_config.NumberColumn(
            "Value (EUR)", min_value=0, step=0.01, format="%.2f", required=True
        ),
    },
    key="etf_editor",
)
if not edited.equals(st.session_state.etfs):
    st.session_state.etfs = edited.reset_index(drop=True)
    reset_results()
    st.rerun()


etfs = st.session_state.etfs.dropna()
if not etfs.empty:
    st.divider()
    st.header("Scraping")

    if st.button(f"Scrape {len(etfs)} ETFs", width="stretch", type="primary"):
        with st.spinner("Scraping the holdings..."):
            holdings, summary, errors = scrape_portfolio(etfs)
        st.session_state.holdings = holdings
        st.session_state.summary = summary
        st.session_state.errors = errors

    for isin, error in st.session_state.errors.items():
        st.error(f"Failed to scrape {isin} with {error}")

if st.session_state.holdings is not None:
    holdings_all = st.session_state.holdings
    summary = st.session_state.summary
    total_value = summary["Value"].sum()

    st.divider()
    st.header("Analysis")

    # Sidebar filters
    holdings = sidebar_filters(holdings_all, {"etf_name": "ETF", **FILTER_COLUMNS})

    filtered_value = holdings["value_in_portfolio"].sum()
    is_filtered = len(holdings) != len(holdings_all)

    # Key figures
    weighted_ter = (summary["TER"] * summary["Portfolio weight"]).sum(min_count=1)
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Portfolio value", f"{total_value:,.2f} €")
    col2.metric("ETFs", len(summary))
    col3.metric(
        "Weighted TER",
        f"{weighted_ter:.3f} %" if pd.notna(weighted_ter) else "n/a",
        help="Average TER weighted by the value of each ETF. "
        "ETFs without a TER are counted as 0.",
    )
    col4.metric(
        "Annual cost",
        f"{total_value * weighted_ter / 100:,.2f} €"
        if pd.notna(weighted_ter)
        else "n/a",
    )
    if is_filtered:
        st.info(
            f"Filters active: {len(holdings)} holdings, "
            f"{filtered_value:,.2f} € ({filtered_value / total_value:.1%} of the portfolio)."
        )

    if holdings.empty:
        st.warning("No holdings match the current filters.")
        st.stop()

    (
        tab_etfs,
        tab_composition,
        tab_map,
        tab_top,
        tab_holdings,
    ) = st.tabs(["ETFs", "Composition", "Map", "Top holdings", "Holdings"])

    with tab_etfs:
        st.dataframe(
            summary,
            hide_index=True,
            width="stretch",
            column_order=[
                "Name",
                "ISIN",
                "Scraper",
                "Value",
                "Portfolio weight",
                "TER",
                "Holdings",
                "Weights sum",
            ],
            column_config={
                "Name": st.column_config.TextColumn(width="large"),
                "Value": st.column_config.NumberColumn("Value (EUR)", format="%.2f"),
                "Portfolio weight": st.column_config.ProgressColumn(
                    format="percent", min_value=0, max_value=1
                ),
                "TER": st.column_config.NumberColumn("TER (%)", format="%.2f"),
                "Weights sum": st.column_config.NumberColumn(
                    format="percent",
                    help="Sum of the weights of the holdings. "
                    "Far from 100% means the data is incomplete.",
                ),
            },
        )
        incomplete = summary[(summary["Weights sum"] - 1).abs() > 0.02]
        for _, row in incomplete.iterrows():
            st.warning(
                f"The holdings of {row['Name']} sum to {row['Weights sum']:.1%}: "
                "its composition may be incomplete."
            )

    with tab_composition:
        composition_charts(holdings, "value_in_portfolio", "Value (EUR)")
        if (holdings["etf_scraper"] == "Xtrackers (IT)").any():
            st.caption("Xtrackers does not provide the asset class of its holdings.")

    with tab_map:
        country_map(holdings, "value_in_portfolio", "Invested (EUR)")

    with tab_top:
        st.caption(
            "The same holding in different ETFs is matched by name, "
            "so the aggregation is approximate."
        )
        top_n = st.slider("Holdings to show", 10, 200, 25, step=5)

        top = (
            holdings.assign(key=holdings["name"].map(holding_key))
            .groupby("key")
            .agg(
                name=("name", lambda s: s.mode().iloc[0] if not s.mode().empty else ""),
                sector_name=("sector_name", "first"),
                country_name=("country_name", "first"),
                value=("value_in_portfolio", "sum"),
                etfs=("etf_name", lambda s: ", ".join(sorted(s.unique()))),
                etf_count=("etf_isin", "nunique"),
            )
            .sort_values("value", ascending=False)
            .head(top_n)
            .reset_index(drop=True)
        )
        top["share"] = top["value"] / filtered_value

        st.dataframe(
            top,
            hide_index=True,
            width="stretch",
            column_order=[
                "name",
                "share",
                "value",
                "sector_name",
                "country_name",
                "etf_count",
                "etfs",
            ],
            column_config={
                "name": st.column_config.TextColumn("Name", width="medium"),
                "share": st.column_config.ProgressColumn(
                    "Share",
                    format="percent",
                    min_value=0,
                    max_value=float(top["share"].max()),
                ),
                "value": st.column_config.NumberColumn("Value (EUR)", format="%.2f"),
                "sector_name": "Sector",
                "country_name": "Country",
                "etf_count": st.column_config.NumberColumn("ETFs"),
                "etfs": st.column_config.TextColumn("In ETFs", width="large"),
            },
        )

    with tab_holdings:
        columns = [
            "etf_name",
            "name",
            "ticker",
            "isin",
            "weight",
            "value_in_portfolio",
            "asset_class",
            "sector_name",
            "country_name",
            "currency",
            "rating",
            "etf_isin",
            "etf_scraper",
        ]
        columns = [c for c in columns if c in holdings.columns]
        table = holdings[columns].sort_values("value_in_portfolio", ascending=False)

        st.dataframe(
            table,
            hide_index=True,
            width="stretch",
            column_config={
                "etf_name": "ETF",
                "name": st.column_config.TextColumn("Name", width="medium"),
                "ticker": "Ticker",
                "isin": "ISIN",
                "weight": st.column_config.NumberColumn(
                    "Weight in ETF", format="percent"
                ),
                "value_in_portfolio": st.column_config.NumberColumn(
                    "Value (EUR)", format="%.2f"
                ),
                "asset_class": "Asset class",
                "sector_name": "Sector",
                "country_name": "Country",
                "currency": "Currency",
                "rating": "Rating",
                "etf_isin": "ETF ISIN",
                "etf_scraper": "Scraper",
            },
        )
        st.download_button(
            "Download holdings (CSV)",
            holdings.to_csv(index=False).encode("utf-8"),
            file_name="holdings.csv",
            mime="text/csv",
        )
