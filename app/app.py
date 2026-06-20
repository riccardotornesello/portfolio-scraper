import sys
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

# Allow running via `streamlit run app/app.py` from the repo root.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from portfolio_scraper.etf import (  # noqa: E402
    ISharesItScraper,
    VanguardItScraper,
    XtrackersItScraper,
)

SCRAPERS: dict[str, type] = {
    "iShares (IT)": ISharesItScraper,
    "Vanguard (IT)": VanguardItScraper,
    "Xtrackers (IT)": XtrackersItScraper,
}

PORTFOLIO_COLUMNS = ["isin", "scraper", "value"]


st.set_page_config(page_title="ETF Portfolio Analyzer", page_icon="📊", layout="wide")


def empty_portfolio() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "isin": pd.Series(dtype="str"),
            "scraper": pd.Series(dtype="str"),
            "value": pd.Series(dtype="float"),
        }
    )


if "portfolio" not in st.session_state:
    st.session_state.portfolio = empty_portfolio()


@st.cache_data(show_spinner=False)
def scrape_holdings(scraper_name: str, isin: str) -> pd.DataFrame:
    """Fetch a single ETF holdings dataframe. Cached per (scraper, isin)."""
    scraper = SCRAPERS[scraper_name]()
    return scraper.get_holdings_by_isin(isin.strip().upper())


def build_combined(portfolio: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    """
    Scrape every ETF, weight its holdings by the ETF portfolio fraction and
    concatenate into one dataframe. Returns (combined_df, errors).
    """
    rows = portfolio.dropna(subset=["isin", "scraper", "value"])
    rows = rows[rows["isin"].str.strip() != ""]
    if rows.empty:
        return pd.DataFrame(), []

    total_value = rows["value"].astype(float).sum()
    if total_value <= 0:
        return pd.DataFrame(), ["Total value must be greater than zero."]

    frames: list[pd.DataFrame] = []
    errors: list[str] = []
    for _, row in rows.iterrows():
        isin = str(row["isin"]).strip().upper()
        scraper_name = row["scraper"]
        if scraper_name not in SCRAPERS:
            errors.append(f"{isin}: invalid scraper '{scraper_name}'.")
            continue
        etf_fraction = float(row["value"]) / total_value
        try:
            holdings = scrape_holdings(scraper_name, isin).copy()
        except Exception as exc:  # noqa: BLE001 - surface any scrape failure to the UI
            errors.append(f"{isin} ({scraper_name}): {exc}")
            continue

        holdings["etf_isin"] = isin
        holdings["etf_scraper"] = scraper_name
        holdings["etf_value"] = float(row["value"])
        holdings["etf_fraction"] = etf_fraction
        holdings["portfolio_weight"] = (
            pd.to_numeric(holdings["weight_in_etf"], errors="coerce") * etf_fraction
        )
        frames.append(holdings)

    if not frames:
        return pd.DataFrame(), errors

    combined = pd.concat(frames, ignore_index=True)
    return combined, errors


def portfolio_tab() -> None:
    st.subheader("Portfolio composition")
    st.caption(
        "Add the ETFs with ISIN, scraper and value in euro. Each ETF weight in "
        "the portfolio is its value divided by the total value."
    )

    edited = st.data_editor(
        st.session_state.portfolio,
        num_rows="dynamic",
        use_container_width=True,
        hide_index=True,
        column_config={
            "isin": st.column_config.TextColumn("ISIN", required=True),
            "scraper": st.column_config.SelectboxColumn(
                "Scraper", options=list(SCRAPERS.keys()), required=True
            ),
            "value": st.column_config.NumberColumn(
                "Value (€)", min_value=0.0, step=100.0, required=True
            ),
        },
    )
    st.session_state.portfolio = edited.reset_index(drop=True)

    total = edited["value"].dropna().sum()
    if total > 0:
        st.metric("Total value", f"€ {total:,.2f}")

    st.divider()
    col_imp, col_exp = st.columns(2)

    with col_exp:
        st.markdown("**Export**")
        csv = edited.to_csv(index=False).encode("utf-8")
        st.download_button(
            "Download CSV",
            data=csv,
            file_name="portfolio.csv",
            mime="text/csv",
            use_container_width=True,
        )

    with col_imp:
        st.markdown("**Import**")
        uploaded = st.file_uploader(
            "Upload CSV", type="csv", label_visibility="collapsed"
        )
        if uploaded is not None:
            try:
                df = pd.read_csv(uploaded)
                missing = [c for c in PORTFOLIO_COLUMNS if c not in df.columns]
                if missing:
                    st.error(f"Missing columns in CSV: {', '.join(missing)}")
                else:
                    st.session_state.portfolio = df[PORTFOLIO_COLUMNS].reset_index(
                        drop=True
                    )
                    st.success("Portfolio imported.")
                    st.rerun()
            except Exception as exc:  # noqa: BLE001
                st.error(f"Error reading CSV: {exc}")


def filter_holdings(df: pd.DataFrame) -> pd.DataFrame:
    st.markdown("**Filters**")
    c1, c2, c3, c4 = st.columns(4)

    def multiselect_for(col: str, label: str, container) -> list:
        if col not in df.columns:
            return []
        options = sorted(df[col].dropna().unique().tolist())
        return container.multiselect(label, options, key=f"filter_{col}")

    sectors = multiselect_for("sector", "Sector", c1)
    assets = multiselect_for("asset_class", "Asset class", c2)
    locations = multiselect_for("location", "Country", c3)
    etfs = multiselect_for("etf_isin", "ETF", c4)
    name_query = st.text_input("Search by name", key="filter_name")

    out = df
    if sectors:
        out = out[out["sector"].isin(sectors)]
    if assets:
        out = out[out["asset_class"].isin(assets)]
    if locations:
        out = out[out["location"].isin(locations)]
    if etfs:
        out = out[out["etf_isin"].isin(etfs)]
    if name_query:
        out = out[out["name"].str.contains(name_query, case=False, na=False)]
    return out


def pie_chart(df: pd.DataFrame, group_col: str, title: str) -> None:
    if group_col not in df.columns or df.empty:
        st.info(f"No data for {title.lower()}.")
        return
    agg = (
        df.groupby(group_col, dropna=True)["portfolio_weight"]
        .sum()
        .reset_index()
        .sort_values("portfolio_weight", ascending=False)
    )
    agg = agg[agg["portfolio_weight"] > 0]
    if agg.empty:
        st.info(f"No data for {title.lower()}.")
        return
    fig = px.pie(agg, names=group_col, values="portfolio_weight", title=title, hole=0.3)
    fig.update_traces(textposition="inside", textinfo="percent+label")
    st.plotly_chart(fig, use_container_width=True)


def analysis_tab() -> None:
    st.subheader("Holdings analysis")

    if st.button("🔍 Analyze portfolio", type="primary"):
        with st.spinner("Scraping ETFs..."):
            combined, errors = build_combined(st.session_state.portfolio)
        st.session_state.combined = combined
        st.session_state.errors = errors

    if "combined" not in st.session_state:
        st.info("Fill in the portfolio and press *Analyze portfolio*.")
        return

    for err in st.session_state.get("errors", []):
        st.error(err)

    combined = st.session_state.combined
    if combined.empty:
        st.warning("No holdings available.")
        return

    filtered = filter_holdings(combined)

    total_weight = filtered["portfolio_weight"].sum()
    m1, m2, m3 = st.columns(3)
    m1.metric("Holdings", f"{len(filtered):,}")
    m2.metric("ETFs", filtered["etf_isin"].nunique())
    m3.metric("Covered weight", f"{total_weight:.2%}")

    st.divider()
    st.markdown("**Composition**")
    g1, g2, g3 = st.columns(3)
    with g1:
        pie_chart(filtered, "sector", "By sector")
    with g2:
        pie_chart(filtered, "asset_class", "By asset class")
    with g3:
        pie_chart(filtered, "location", "By country")

    st.divider()
    st.markdown("**Holdings table**")
    display = filtered.sort_values("portfolio_weight", ascending=False)
    st.dataframe(
        display,
        use_container_width=True,
        hide_index=True,
        column_config={
            "weight_in_etf": st.column_config.NumberColumn(
                "Weight in ETF", format="percent"
            ),
            "portfolio_weight": st.column_config.NumberColumn(
                "Portfolio weight", format="percent"
            ),
            "etf_fraction": st.column_config.NumberColumn(
                "ETF fraction", format="percent"
            ),
            "etf_value": st.column_config.NumberColumn("ETF value (€)", format="%.2f"),
        },
    )
    st.download_button(
        "Download holdings (CSV)",
        data=display.to_csv(index=False).encode("utf-8"),
        file_name="holdings.csv",
        mime="text/csv",
    )


st.title("📊 ETF Portfolio Analyzer")
tab_portfolio, tab_analysis = st.tabs(["Portfolio", "Analysis"])
with tab_portfolio:
    portfolio_tab()
with tab_analysis:
    analysis_tab()
