import streamlit as st
import pandas as pd

from portfolio_scraper.etf import (
    AmundiScraper,
    ISharesItScraper,
    XTrackersItScraper,
    VanguardItScraper,
)


SCRAPERS = {
    "Amundi": AmundiScraper,
    "iShares (IT)": ISharesItScraper,
    "Vanguard (IT)": VanguardItScraper,
    "Xtrackers (IT)": XTrackersItScraper,
}


@st.cache_data(ttl="1d", show_spinner=False)
def load_listings(scraper_name: str) -> pd.DataFrame:
    df = SCRAPERS[scraper_name]().get_listings()
    df.insert(0, "scraper", scraper_name)
    # internal_id types differ between scrapers (int for iShares, str for the others)
    df["internal_id"] = df["internal_id"].astype(str)
    return df


############################
# LAYOUT
############################
st.set_page_config(
    page_title="ETF listings",
    page_icon="📋",
    layout="wide",
)

############################
# APP
############################
st.title("📋 ETF listings")
st.caption("All the funds available across every scraper, in a single table.")

frames = []
errors = {}
with st.spinner("Fetching listings..."):
    for scraper_name in SCRAPERS:
        try:
            frames.append(load_listings(scraper_name))
        except Exception as e:
            errors[scraper_name] = e

for scraper_name, error in errors.items():
    st.error(f"Failed to fetch listings for {scraper_name}: {error}")

if not frames:
    st.stop()

listings = pd.concat(frames, ignore_index=True)

# Sidebar filters
st.sidebar.header("Filters")

if st.sidebar.button("Refresh data", width="stretch"):
    load_listings.clear()
    st.rerun()

selected_scrapers = st.sidebar.multiselect(
    "Scraper", sorted(listings["scraper"].unique())
)
if selected_scrapers:
    listings = listings[listings["scraper"].isin(selected_scrapers)]

search = st.sidebar.text_input("Search name / ISIN / internal id")
if search:
    mask = (
        listings["name"].str.contains(search, case=False, na=False, regex=False)
        | listings["isin"].str.contains(search, case=False, na=False, regex=False)
        | listings["internal_id"].str.contains(
            search, case=False, na=False, regex=False
        )
    )
    listings = listings[mask]

ter_values = listings["ter"].dropna()
if not ter_values.empty and ter_values.min() < ter_values.max():
    ter_min, ter_max = st.sidebar.slider(
        "TER (%)",
        min_value=float(ter_values.min()),
        max_value=float(ter_values.max()),
        value=(float(ter_values.min()), float(ter_values.max())),
        step=0.01,
    )
    include_missing_ter = st.sidebar.checkbox("Include funds without TER", value=True)
    ter_mask = listings["ter"].between(ter_min, ter_max)
    if include_missing_ter:
        ter_mask |= listings["ter"].isna()
    listings = listings[ter_mask]

# Results
col1, col2 = st.columns(2)
col1.metric("Funds", len(listings))
col2.metric("Scrapers", listings["scraper"].nunique())

st.dataframe(
    listings,
    width="stretch",
    hide_index=True,
    column_config={
        "scraper": st.column_config.TextColumn("Scraper"),
        "isin": st.column_config.TextColumn("ISIN"),
        "name": st.column_config.TextColumn("Name", width="large"),
        "internal_id": st.column_config.TextColumn("Internal id"),
        "ter": st.column_config.NumberColumn("TER (%)", format="%.2f"),
    },
)

st.download_button(
    "Download CSV",
    listings.to_csv(index=False),
    file_name="etf_listings.csv",
    mime="text/csv",
)
