import pandas as pd
import streamlit as st
import plotly.express as px

from portfolio_scraper.etf.ishares import ISharesItScraper
from portfolio_scraper.etf.vanguard import VanguardItScraper
from portfolio_scraper.etf.xtrackers import XtrackersItScraper

SCRAPERS = {
    "iShares (Italy)": ISharesItScraper,
    "Vanguard (Italy)": VanguardItScraper,
    "Xtrackers (Italy)": XtrackersItScraper,
}

EXAMPLE_ISINS = {
    "iShares (Italy)": "IE00BG0J4C88",
    "Vanguard (Italy)": "IE00BK5BQT80",
    "Xtrackers (Italy)": "IE0006WW1TQ4",
}

st.set_page_config(page_title="Portfolio Explorer", page_icon="📊", layout="wide")
st.title("Portfolio Explorer")
st.caption("Add ETFs with their provider and allocation, then explore the combined portfolio statistics.")

# --- Session state init ---
if "etf_entries" not in st.session_state:
    st.session_state.etf_entries = [{"isin": "", "scraper": list(SCRAPERS.keys())[0], "allocation": 100.0}]

# --- Sidebar ---
with st.sidebar:
    st.header("ETF Portfolio")

    to_delete = None
    for i, entry in enumerate(st.session_state.etf_entries):
        st.markdown(f"**ETF {i + 1}**")
        col_del, _ = st.columns([1, 3])
        if col_del.button("✕", key=f"del_{i}", help="Remove this ETF") and len(st.session_state.etf_entries) > 1:
            to_delete = i

        scraper_name = st.selectbox(
            "Provider",
            list(SCRAPERS.keys()),
            index=list(SCRAPERS.keys()).index(entry["scraper"]),
            key=f"scraper_{i}",
        )
        isin = st.text_input(
            "ISIN",
            value=entry["isin"],
            placeholder=EXAMPLE_ISINS[scraper_name],
            key=f"isin_{i}",
        )
        allocation = st.number_input(
            "Allocation %",
            min_value=0.0,
            max_value=100.0,
            value=entry["allocation"],
            step=1.0,
            key=f"alloc_{i}",
        )
        st.session_state.etf_entries[i] = {"isin": isin, "scraper": scraper_name, "allocation": allocation}
        st.divider()

    if to_delete is not None:
        st.session_state.etf_entries.pop(to_delete)
        st.rerun()

    if st.button("+ Add ETF", use_container_width=True):
        st.session_state.etf_entries.append({"isin": "", "scraper": list(SCRAPERS.keys())[0], "allocation": 0.0})
        st.rerun()

    total_alloc = sum(e["allocation"] for e in st.session_state.etf_entries)
    if abs(total_alloc - 100.0) > 0.01:
        st.warning(f"Allocations sum to {total_alloc:.1f}% (expected 100%)")

    fetch = st.button("Fetch Holdings", type="primary", use_container_width=True)

# --- Validation ---
if not fetch:
    st.info("Configure your ETFs in the sidebar, then click **Fetch Holdings**.")
    st.stop()

entries = st.session_state.etf_entries
invalid = [i + 1 for i, e in enumerate(entries) if not e["isin"].strip()]
if invalid:
    st.error(f"Missing ISIN for ETF(s): {', '.join(map(str, invalid))}")
    st.stop()

# --- Fetch & merge ---
dfs = []
errors = []

for entry in entries:
    isin = entry["isin"].strip().upper()
    scraper_name = entry["scraper"]
    allocation = entry["allocation"] / 100.0

    with st.spinner(f"Fetching {isin} from {scraper_name}…"):
        try:
            scraper = SCRAPERS[scraper_name]()
            etf_df = scraper.get_holdings_by_isin(isin)
        except Exception as e:
            errors.append(f"{isin}: {e}")
            continue

    if etf_df is None or etf_df.empty:
        errors.append(f"{isin}: no data returned")
        continue

    etf_df = etf_df.copy()
    etf_df["source_etf"] = isin
    etf_df["etf_allocation"] = entry["allocation"]

    if "weight_in_etf" in etf_df.columns:
        etf_df["portfolio_weight"] = etf_df["weight_in_etf"] * allocation

    dfs.append(etf_df)

for err in errors:
    st.error(f"Failed to fetch {err}")

if not dfs:
    st.stop()

df = pd.concat(dfs, ignore_index=True)

weight_col = "portfolio_weight"
has_weight = weight_col in df.columns and df[weight_col].notna().any()

# --- Summary ---
total_holdings = len(df)
unique_holdings = df["name"].nunique() if "name" in df.columns else total_holdings

st.subheader("Portfolio Summary")
col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("Total Rows", total_holdings)
col2.metric("Unique Holdings", unique_holdings)
col2.caption("by name")

if has_weight:
    weights = df[weight_col].dropna()
    top_weight = weights.nlargest(1).iloc[0]
    top10_weight = weights.nlargest(10).sum()
    hhi = (weights ** 2).sum()
    col3.metric("Top Holding Weight", f"{top_weight:.2%}")
    col4.metric("Top 10 Concentration", f"{top10_weight:.2%}")
    col5.metric("HHI", f"{hhi:.4f}", help="Herfindahl–Hirschman Index. Higher = more concentrated.")

st.divider()

# --- Tabs ---
tab_holdings, tab_sector, tab_geo, tab_asset, tab_currency, tab_raw = st.tabs(
    ["Top Holdings", "Sectors", "Geography", "Asset Classes", "Currencies", "Raw Data"]
)

# ── Top Holdings ──────────────────────────────────────────────────────────────
with tab_holdings:
    if has_weight:
        if "name" in df.columns:
            agg_df = (
                df.dropna(subset=[weight_col])
                .groupby("name", as_index=False)
                .agg(
                    portfolio_weight=(weight_col, "sum"),
                    ticker=("ticker", "first") if "ticker" in df.columns else (weight_col, "count"),
                    sector=("sector", "first") if "sector" in df.columns else (weight_col, "count"),
                    location=("location", "first") if "location" in df.columns else (weight_col, "count"),
                    source_etfs=("source_etf", lambda x: ", ".join(sorted(x.unique()))),
                )
                .sort_values("portfolio_weight", ascending=False)
                .reset_index(drop=True)
            )
        else:
            agg_df = df

        top_n = st.slider("Number of top holdings to display", 5, min(50, len(agg_df)), min(10, len(agg_df)))
        top_df = agg_df.head(top_n).copy()
        top_df.index = range(1, len(top_df) + 1)

        fig = px.bar(
            top_df,
            x="portfolio_weight",
            y="name",
            orientation="h",
            labels={"portfolio_weight": "Portfolio Weight", "name": "Holding"},
            title=f"Top {top_n} Holdings by Combined Portfolio Weight",
            color="portfolio_weight",
            color_continuous_scale="Blues",
        )
        fig.update_layout(yaxis={"autorange": "reversed"}, coloraxis_showscale=False)
        st.plotly_chart(fig, use_container_width=True)

        display_df = top_df.copy()
        display_df["portfolio_weight"] = display_df["portfolio_weight"].map("{:.2%}".format)
        st.dataframe(display_df, use_container_width=True)
    else:
        st.info("Weight data not available.")

# ── Sectors ───────────────────────────────────────────────────────────────────
with tab_sector:
    if "sector" in df.columns:
        sector_data = df.dropna(subset=["sector"])
        if sector_data.empty:
            st.info("No sector data available.")
        else:
            if has_weight:
                sector_agg = (
                    sector_data.groupby("sector")[weight_col]
                    .sum()
                    .sort_values(ascending=False)
                    .reset_index()
                )
                sector_agg.columns = ["Sector", "Weight"]
                fig = px.pie(sector_agg, names="Sector", values="Weight", title="Sector Allocation (by portfolio weight)", hole=0.35)
            else:
                sector_agg = sector_data["sector"].value_counts().reset_index()
                sector_agg.columns = ["Sector", "Count"]
                fig = px.pie(sector_agg, names="Sector", values="Count", title="Sector Distribution (by count)", hole=0.35)
            fig.update_traces(textposition="inside", textinfo="percent+label")
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Sector data not available.")

# ── Geography ─────────────────────────────────────────────────────────────────
with tab_geo:
    if "location" in df.columns:
        geo_data = df.dropna(subset=["location"])
        if geo_data.empty:
            st.info("No geographic data available.")
        else:
            if has_weight:
                geo_agg = (
                    geo_data.groupby("location")[weight_col]
                    .sum()
                    .sort_values(ascending=False)
                    .reset_index()
                )
                geo_agg.columns = ["Country", "Weight"]
                label_col, title, y_label = "Weight", "Geographic Allocation (by portfolio weight)", "Weight"
            else:
                geo_agg = geo_data["location"].value_counts().reset_index()
                geo_agg.columns = ["Country", "Count"]
                label_col, title, y_label = "Count", "Geographic Distribution (by count)", "Count"

            fig = px.bar(
                geo_agg.head(20),
                x="Country",
                y=label_col,
                title=title,
                labels={"Country": "Country", label_col: y_label},
                color=label_col,
                color_continuous_scale="Teal",
            )
            fig.update_layout(coloraxis_showscale=False)
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Geographic data not available.")

# ── Asset Classes ──────────────────────────────────────────────────────────────
with tab_asset:
    if "asset_class" in df.columns:
        ac_data = df.dropna(subset=["asset_class"])
        if ac_data.empty:
            st.info("No asset class data available.")
        else:
            if has_weight:
                ac_agg = (
                    ac_data.groupby("asset_class")[weight_col]
                    .sum()
                    .sort_values(ascending=False)
                    .reset_index()
                )
                ac_agg.columns = ["Asset Class", "Weight"]
                fig = px.bar(ac_agg, x="Asset Class", y="Weight", title="Asset Class Allocation (by portfolio weight)", color="Weight", color_continuous_scale="Purples")
            else:
                ac_agg = ac_data["asset_class"].value_counts().reset_index()
                ac_agg.columns = ["Asset Class", "Count"]
                fig = px.bar(ac_agg, x="Asset Class", y="Count", title="Asset Class Distribution (by count)", color="Count", color_continuous_scale="Purples")
            fig.update_layout(coloraxis_showscale=False)
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Asset class data not available.")

# ── Currencies ─────────────────────────────────────────────────────────────────
with tab_currency:
    if "currency" in df.columns:
        cur_data = df.dropna(subset=["currency"])
        if cur_data.empty:
            st.info("No currency data available.")
        else:
            if has_weight:
                cur_agg = (
                    cur_data.groupby("currency")[weight_col]
                    .sum()
                    .sort_values(ascending=False)
                    .reset_index()
                )
                cur_agg.columns = ["Currency", "Weight"]
                fig = px.pie(cur_agg, names="Currency", values="Weight", title="Currency Exposure (by portfolio weight)", hole=0.35)
            else:
                cur_agg = cur_data["currency"].value_counts().reset_index()
                cur_agg.columns = ["Currency", "Count"]
                fig = px.pie(cur_agg, names="Currency", values="Count", title="Currency Distribution (by count)", hole=0.35)
            fig.update_traces(textposition="inside", textinfo="percent+label")
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Currency data not available.")

# ── Raw Data ───────────────────────────────────────────────────────────────────
with tab_raw:
    etf_labels = ", ".join(e["isin"].strip().upper() for e in entries)
    st.caption(f"{total_holdings} rows · ETFs: {etf_labels}")
    st.dataframe(df, use_container_width=True)
    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button("Download CSV", csv, file_name="portfolio_holdings.csv", mime="text/csv")
