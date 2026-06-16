from portfolio_scraper.etf.ishares.base import ISharesBaseEtfScraper


class ISharesItScraper(ISharesBaseEtfScraper):
    LISTINGS_URL = "https://www.ishares.com/it/investitore-privato/it/product-screener/product-screener-v3.1.jsn?dcrPath=/templatedata/config/product-screener-v3/data/it/it/product-screener/ishares-product-screener-backend-config&siteEntryPassthrough=true"
    LISTINGS_COLUMN_NAMES: dict[str, str] = {
        "internal_id": "portfolioId",
        "name": "fundName",
        "isin": "isin",
        "ticker": "localExchangeTicker",
        "ter": "ter_r",
    }

    HOLDINGS_URL_TEMPLATE = "https://www.ishares.com/it/investitore-privato/it/prodotti/{product_id}/fund/1506575546154.ajax?fileType=csv"
    HOLDINGS_COLUMN_NAMES: dict[str, str] = {
        "name": "Nome",
        "ticker": "Ticker dell'emittente",
        "weight_in_etf": "Ponderazione (%)",
        "sector": "Settore",
        "asset_class": "Asset Class",
        "total_market_value": "Valore di mercato",
        "total_notional_value": "Valore nozionale",
        "shares_amount": "Nominale",
        "share_price": "Prezzo",
        "location": "Area Geografica",
        "exchange": "Cambio",
        "currency": "Valuta di mercato",
    }
    HOLDINGS_CSV_SEPARATOR = ","
    HOLDINGS_CSV_THOUSANDS = "."
    HOLDINGS_CSV_DECIMAL = ","
