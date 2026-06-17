import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from portfolio_scraper import ISharesItScraper, VanguardItScraper, XtrackersItScraper

SCRAPERS = {
    "iShares (IT)": ISharesItScraper,
    "Vanguard (IT)": VanguardItScraper,
    "Xtrackers (IT)": XtrackersItScraper,
}

ISO_TO_COUNTRY: dict[str, str] = {
    "AD": "Andorra", "AE": "UAE", "AF": "Afghanistan", "AG": "Antigua",
    "AL": "Albania", "AM": "Armenia", "AO": "Angola", "AR": "Argentina",
    "AT": "Austria", "AU": "Australia", "AZ": "Azerbaijan", "BA": "Bosnia",
    "BB": "Barbados", "BD": "Bangladesh", "BE": "Belgium", "BF": "Burkina Faso",
    "BG": "Bulgaria", "BH": "Bahrain", "BJ": "Benin", "BM": "Bermuda",
    "BN": "Brunei", "BO": "Bolivia", "BR": "Brazil", "BS": "Bahamas",
    "BT": "Bhutan", "BW": "Botswana", "BY": "Belarus", "BZ": "Belize",
    "CA": "Canada", "CD": "DR Congo", "CF": "CAR", "CG": "Congo",
    "CH": "Switzerland", "CI": "Ivory Coast", "CL": "Chile", "CM": "Cameroon",
    "CN": "China", "CO": "Colombia", "CR": "Costa Rica", "CU": "Cuba",
    "CV": "Cape Verde", "CY": "Cyprus", "CZ": "Czech Republic",
    "DE": "Germany", "DJ": "Djibouti", "DK": "Denmark", "DO": "Dom. Rep.",
    "DZ": "Algeria", "EC": "Ecuador", "EE": "Estonia", "EG": "Egypt",
    "ER": "Eritrea", "ES": "Spain", "ET": "Ethiopia", "FI": "Finland",
    "FJ": "Fiji", "FM": "Micronesia", "FR": "France", "GA": "Gabon",
    "GB": "UK", "GE": "Georgia", "GH": "Ghana", "GM": "Gambia",
    "GN": "Guinea", "GQ": "Eq. Guinea", "GR": "Greece", "GT": "Guatemala",
    "GG": "Guernsey", "GW": "Guinea-Bissau", "GY": "Guyana", "HK": "Hong Kong",
    "HN": "Honduras", "HR": "Croatia", "HT": "Haiti", "HU": "Hungary",
    "ID": "Indonesia", "IE": "Ireland", "IL": "Israel", "IN": "India",
    "IQ": "Iraq", "IR": "Iran", "IS": "Iceland", "IT": "Italy",
    "JE": "Jersey", "JM": "Jamaica", "JO": "Jordan", "JP": "Japan",
    "KE": "Kenya", "KG": "Kyrgyzstan", "KH": "Cambodia", "KI": "Kiribati",
    "KM": "Comoros", "KN": "St Kitts", "KP": "North Korea", "KR": "South Korea",
    "KW": "Kuwait", "KY": "Cayman Islands", "KZ": "Kazakhstan",
    "LA": "Laos", "LB": "Lebanon", "LC": "St Lucia", "LI": "Liechtenstein",
    "LK": "Sri Lanka", "LR": "Liberia", "LS": "Lesotho", "LT": "Lithuania",
    "LU": "Luxembourg", "LV": "Latvia", "LY": "Libya",
    "MA": "Morocco", "MC": "Monaco", "MD": "Moldova", "ME": "Montenegro",
    "MG": "Madagascar", "MH": "Marshall Islands", "MK": "North Macedonia",
    "ML": "Mali", "MM": "Myanmar", "MN": "Mongolia", "MO": "Macau",
    "MR": "Mauritania", "MT": "Malta", "MU": "Mauritius", "MV": "Maldives",
    "MW": "Malawi", "MX": "Mexico", "MY": "Malaysia", "MZ": "Mozambique",
    "NA": "Namibia", "NE": "Niger", "NG": "Nigeria", "NI": "Nicaragua",
    "NL": "Netherlands", "NO": "Norway", "NP": "Nepal", "NR": "Nauru",
    "NZ": "New Zealand", "OM": "Oman", "PA": "Panama", "PE": "Peru",
    "PG": "Papua New Guinea", "PH": "Philippines", "PK": "Pakistan",
    "PL": "Poland", "PR": "Puerto Rico", "PT": "Portugal", "PW": "Palau",
    "PY": "Paraguay", "QA": "Qatar", "RO": "Romania", "RS": "Serbia",
    "RU": "Russia", "RW": "Rwanda", "SA": "Saudi Arabia", "SB": "Solomon Islands",
    "SC": "Seychelles", "SD": "Sudan", "SE": "Sweden", "SG": "Singapore",
    "SI": "Slovenia", "SL": "Sierra Leone", "SM": "San Marino", "SN": "Senegal",
    "SO": "Somalia", "SR": "Suriname", "SS": "South Sudan", "ST": "São Tomé",
    "SV": "El Salvador", "SY": "Syria", "SZ": "Eswatini",
    "TD": "Chad", "TG": "Togo", "TH": "Thailand", "TJ": "Tajikistan",
    "TL": "Timor-Leste", "TM": "Turkmenistan", "TN": "Tunisia", "TO": "Tonga",
    "TR": "Turkey", "TT": "Trinidad", "TV": "Tuvalu", "TW": "Taiwan",
    "TZ": "Tanzania", "UA": "Ukraine", "UG": "Uganda", "US": "USA",
    "UY": "Uruguay", "UZ": "Uzbekistan", "VC": "St Vincent", "VE": "Venezuela",
    "VN": "Vietnam", "VU": "Vanuatu", "WS": "Samoa", "YE": "Yemen",
    "ZA": "South Africa", "ZM": "Zambia", "ZW": "Zimbabwe",
}

PIE_COLORS = px.colors.qualitative.Set3 + px.colors.qualitative.Pastel


@st.cache_data(show_spinner=False)
def fetch_holdings(isin: str, scraper_name: str) -> pd.DataFrame:
    scraper_cls = SCRAPERS[scraper_name]
    return scraper_cls().get_holdings_by_isin(isin.strip())


def build_portfolio_df(portfolio: list[dict]) -> tuple[pd.DataFrame, list[str]]:
    frames, errors = [], []
    for entry in portfolio:
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

    if not frames:
        return pd.DataFrame(), errors

    combined = pd.concat(frames, ignore_index=True)
    combined["country"] = combined["location"].map(
        lambda x: ISO_TO_COUNTRY.get(x, x) if pd.notna(x) else "Unknown"
    )
    combined["sector"] = combined["sector"].fillna("Unknown").astype(str)
    combined["asset_class"] = combined["asset_class"].fillna("Unknown").astype(str)
    return combined, errors


def collapse_small(series: pd.Series, threshold: float = 0.01) -> pd.Series:
    total = series.sum()
    mask = series / total < threshold
    other = series[mask].sum()
    result = series[~mask].copy()
    if other > 0:
        result["Other"] = result.get("Other", 0) + other
    return result.sort_values(ascending=False)


def make_pie(series: pd.Series, title: str) -> go.Figure:
    series = collapse_small(series)
    fig = px.pie(
        values=series.values,
        names=series.index,
        title=title,
        color_discrete_sequence=PIE_COLORS,
        hole=0.35,
    )
    fig.update_traces(textposition="inside", textinfo="percent+label")
    fig.update_layout(
        showlegend=True,
        legend=dict(orientation="v", x=1.05, y=0.5),
        margin=dict(t=40, b=0, l=0, r=0),
    )
    return fig


def hhi(weights: pd.Series) -> float:
    w = weights / weights.sum()
    return float((w**2).sum())
