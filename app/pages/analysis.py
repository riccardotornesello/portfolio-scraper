import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
import plotly.express as px
import streamlit as st

from utils import PIE_COLORS, make_pie, hhi

# ── Guard ─────────────────────────────────────────────────────────────────────

if "holdings" not in st.session_state:
    st.warning("No portfolio data loaded.")
    if st.button("← Back to Portfolio"):
        st.switch_page("pages/portfolio.py")
    st.stop()

df: pd.DataFrame = st.session_state["holdings"]
portfolio_meta: list[dict] = st.session_state.get("portfolio_meta", [])
etf_isins = [e["isin"].strip() for e in portfolio_meta]

# ── Sidebar filters ───────────────────────────────────────────────────────────

with st.sidebar:
    st.header("Filters")

    sel_etfs = st.multiselect(
        "ETF",
        options=etf_isins,
        default=etf_isins,
    )

    all_countries = sorted(df["country"].dropna().unique().tolist())
    sel_countries = st.multiselect(
        "Country",
        options=all_countries,
        default=all_countries,
    )

    all_sectors = sorted(df["sector"].dropna().unique().tolist())
    sel_sectors = st.multiselect(
        "Sector",
        options=all_sectors,
        default=all_sectors,
    )

    all_ac = sorted(df["asset_class"].dropna().unique().tolist())
    sel_ac = st.multiselect(
        "Asset Class",
        options=all_ac,
        default=all_ac,
    )

    min_weight = st.slider(
        "Min portfolio weight (%)",
        min_value=0.0, max_value=1.0, value=0.0, step=0.001, format="%.3f",
    )

    st.divider()
    if st.button("← Portfolio", use_container_width=True):
        st.switch_page("pages/portfolio.py")

# ── Apply filters ─────────────────────────────────────────────────────────────

dff = df.copy()
if sel_etfs:
    dff = dff[dff["etf_isin"].isin(sel_etfs)]
if sel_countries:
    dff = dff[dff["country"].isin(sel_countries)]
if sel_sectors:
    dff = dff[dff["sector"].isin(sel_sectors)]
if sel_ac:
    dff = dff[dff["asset_class"].isin(sel_ac)]
dff = dff[dff["portfolio_weight"] * 100 >= min_weight]

# ── Header ────────────────────────────────────────────────────────────────────

st.title("📊 Analysis")
if len(dff) < len(df):
    st.caption(f"Showing {len(dff):,} of {len(df):,} holdings after filters")

# ── Tabs ──────────────────────────────────────────────────────────────────────

tab_overview, tab_charts, tab_table = st.tabs(["Overview", "Charts", "Holdings"])

# ── Overview ──────────────────────────────────────────────────────────────────

with tab_overview:
    total_pw = dff["portfolio_weight"].sum()
    unique_holdings = dff["name"].nunique() if "name" in dff.columns else len(dff)
    unique_countries = dff["location"].dropna().nunique()

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("ETFs", dff["etf_isin"].nunique())
    c2.metric("Holdings", len(dff))
    c3.metric("Unique Securities", unique_holdings)
    c4.metric("Countries", unique_countries)
    c5.metric("Total Weight", f"{total_pw * 100:.1f}%")

    st.divider()
    col_left, col_right = st.columns(2)

    with col_left:
        st.subheader("Top 15 Holdings")
        top_holdings = (
            dff.groupby("name")["portfolio_weight"]
            .sum()
            .sort_values(ascending=False)
            .head(15)
            .reset_index()
        )
        top_holdings["portfolio_weight"] = (top_holdings["portfolio_weight"] * 100).round(3)
        top_holdings.columns = ["Name", "Weight (%)"]
        st.dataframe(top_holdings, use_container_width=True, hide_index=True)

    with col_right:
        st.subheader("Concentration Metrics")
        pw = dff.groupby("name")["portfolio_weight"].sum()
        if not pw.empty:
            pw_sorted = pw.sort_values(ascending=False)
            top10_pct = pw_sorted.head(10).sum() * 100
            top20_pct = pw_sorted.head(20).sum() * 100
            hhi_norm = hhi(pw) * 10000

            mc1, mc2, mc3 = st.columns(3)
            mc1.metric("Top 10", f"{top10_pct:.1f}%")
            mc2.metric("Top 20", f"{top20_pct:.1f}%")
            mc3.metric("HHI", f"{hhi_norm:.0f}")
            with st.expander("What is HHI?"):
                st.write(
                    "**Herfindahl-Hirschman Index**: sum of squared weights × 10,000. "
                    "< 1,500 = diversified · 1,500–2,500 = moderate · > 2,500 = concentrated."
                )

        st.subheader("ETF Breakdown")
        etf_rows = []
        for entry in portfolio_meta:
            isin = entry["isin"].strip()
            subset = dff[dff["etf_isin"] == isin]
            if subset.empty:
                continue
            etf_rows.append({
                "ISIN": isin,
                "Scraper": entry["scraper"],
                "Weight (%)": entry["weight"],
                "Holdings": len(subset),
                "Coverage (%)": round(subset["weight_in_etf"].sum() * 100, 1),
            })
        if etf_rows:
            st.dataframe(pd.DataFrame(etf_rows), use_container_width=True, hide_index=True)

    st.divider()
    st.subheader("Asset Class Breakdown")
    ac_data = (
        dff.groupby("asset_class")["portfolio_weight"]
        .sum()
        .sort_values(ascending=False)
        .reset_index()
    )
    ac_data["portfolio_weight"] = (ac_data["portfolio_weight"] * 100).round(2)
    ac_data.columns = ["Asset Class", "Weight (%)"]
    fig_bar = px.bar(
        ac_data,
        x="Asset Class",
        y="Weight (%)",
        color="Asset Class",
        color_discrete_sequence=PIE_COLORS,
        text_auto=".2f",
    )
    fig_bar.update_layout(showlegend=False, margin=dict(t=20, b=0))
    st.plotly_chart(fig_bar, use_container_width=True)

# ── Charts ────────────────────────────────────────────────────────────────────

with tab_charts:
    col1, col2 = st.columns(2)
    with col1:
        st.plotly_chart(
            make_pie(dff.groupby("country")["portfolio_weight"].sum(), "By Country"),
            use_container_width=True,
        )
    with col2:
        st.plotly_chart(
            make_pie(dff.groupby("sector")["portfolio_weight"].sum(), "By Sector"),
            use_container_width=True,
        )

    col3, col4 = st.columns(2)
    with col3:
        st.plotly_chart(
            make_pie(dff.groupby("asset_class")["portfolio_weight"].sum(), "By Asset Class"),
            use_container_width=True,
        )
    with col4:
        if "currency" in dff.columns:
            st.plotly_chart(
                make_pie(
                    dff.groupby(dff["currency"].fillna("Unknown"))["portfolio_weight"].sum(),
                    "By Currency",
                ),
                use_container_width=True,
            )
        else:
            st.info("No currency data available.")

    st.subheader("Country × Sector Treemap")
    cs = (
        dff.groupby(["country", "sector"])["portfolio_weight"]
        .sum()
        .reset_index()
    )
    cs["portfolio_weight"] = (cs["portfolio_weight"] * 100).round(3)
    if not cs.empty:
        fig_tree = px.treemap(
            cs,
            path=["country", "sector"],
            values="portfolio_weight",
            color="country",
            color_discrete_sequence=PIE_COLORS,
        )
        fig_tree.update_layout(margin=dict(t=20, b=0))
        st.plotly_chart(fig_tree, use_container_width=True)

# ── Holdings Table ────────────────────────────────────────────────────────────

with tab_table:
    display_cols = [
        "name", "isin", "ticker", "asset_class", "sector", "country",
        "currency", "portfolio_weight", "weight_in_etf", "etf_isin",
    ]
    display_cols = [c for c in display_cols if c in dff.columns]
    dft_display = dff[display_cols].copy()
    dft_display["portfolio_weight"] = (dft_display["portfolio_weight"] * 100).round(4)
    dft_display["weight_in_etf"] = (dft_display["weight_in_etf"] * 100).round(4)
    dft_display = dft_display.sort_values("portfolio_weight", ascending=False)
    dft_display.columns = [
        c.replace("portfolio_weight", "Portfolio Weight (%)")
         .replace("weight_in_etf", "Weight in ETF (%)")
         .replace("etf_isin", "ETF ISIN")
         .replace("asset_class", "Asset Class")
        for c in dft_display.columns
    ]

    st.caption(f"{len(dft_display):,} holdings")
    st.dataframe(
        dft_display,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Portfolio Weight (%)": st.column_config.NumberColumn(format="%.4f"),
            "Weight in ETF (%)": st.column_config.NumberColumn(format="%.4f"),
        },
    )

    csv = dft_display.to_csv(index=False).encode("utf-8")
    st.download_button(
        "⬇️ Download CSV",
        data=csv,
        file_name="portfolio_holdings.csv",
        mime="text/csv",
    )
