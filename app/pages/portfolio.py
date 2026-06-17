import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
import streamlit as st

from utils import SCRAPERS, ISO_TO_COUNTRY, fetch_holdings

# Stable initial data — never mutated, so data_editor key state stays valid
_INITIAL = pd.DataFrame({
    "isin": pd.array([""], dtype="string"),
    "weight": [100.0],
    "scraper": ["iShares (IT)"],
})

st.title("📋 Portfolio")
st.caption("Add your ETFs, set weights, then click **Analyze**.")

edited = st.data_editor(
    _INITIAL,
    column_config={
        "isin": st.column_config.TextColumn("ISIN", width="large"),
        "weight": st.column_config.NumberColumn(
            "Weight (%)",
            min_value=0.0,
            max_value=100.0,
            step=0.1,
            format="%.2f",
            width="small",
        ),
        "scraper": st.column_config.SelectboxColumn(
            "Scraper",
            options=list(SCRAPERS.keys()),
            width="medium",
        ),
    },
    num_rows="dynamic",
    use_container_width=True,
    key="portfolio_editor",
)

valid_rows = edited[edited["isin"].fillna("").str.strip() != ""]
total_weight = edited["weight"].fillna(0).sum()
weight_ok = abs(total_weight - 100) <= 0.5

col_status, col_clear = st.columns([3, 1])
with col_status:
    if weight_ok:
        st.success(f"Weights sum: **{total_weight:.1f}%** ✓")
    else:
        st.warning(f"Weights sum: **{total_weight:.1f}%** — expected 100%")
with col_clear:
    if st.button("Clear cache", use_container_width=True):
        fetch_holdings.clear()
        for k in ("holdings", "portfolio_meta", "portfolio_editor"):
            st.session_state.pop(k, None)
        st.rerun()

st.divider()

if st.button(
    "🔍 Analyze Portfolio",
    type="primary",
    use_container_width=True,
    disabled=len(valid_rows) == 0,
):
    entries = valid_rows.to_dict("records")
    progress = st.progress(0, "Fetching holdings…")
    frames, errors = [], []

    for i, entry in enumerate(entries):
        progress.progress((i + 1) / len(entries), f"Loading {entry['isin'].strip()}…")
        isin = entry["isin"].strip()
        weight_dec = entry["weight"] / 100.0
        scraper_name = entry["scraper"]
        try:
            holdings = fetch_holdings(isin, scraper_name).copy()
            holdings["etf_isin"] = isin
            holdings["etf_scraper"] = scraper_name
            holdings["portfolio_weight"] = holdings["weight_in_etf"] * weight_dec
            frames.append(holdings)
        except Exception as exc:
            errors.append(f"{isin}: {exc}")

    progress.empty()

    for e in errors:
        st.error(e)

    if frames:
        combined = pd.concat(frames, ignore_index=True)
        combined["country"] = combined["location"].map(
            lambda x: ISO_TO_COUNTRY.get(x, x) if pd.notna(x) else "Unknown"
        )
        combined["sector"] = combined["sector"].fillna("Unknown").astype(str)
        combined["asset_class"] = combined["asset_class"].fillna("Unknown").astype(str)
        st.session_state["holdings"] = combined
        st.session_state["portfolio_meta"] = entries
        st.switch_page("pages/analysis.py")
