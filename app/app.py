import streamlit as st

st.set_page_config(
    page_title="ETF Portfolio Analyzer",
    page_icon="📊",
    layout="wide",
)

portfolio_page = st.Page("pages/portfolio.py", title="Portfolio", icon="📋", default=True)
analysis_page = st.Page("pages/analysis.py", title="Analysis", icon="📊")

pg = st.navigation([portfolio_page, analysis_page], position="hidden")
pg.run()
