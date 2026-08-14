from typing import Dict


from .base import ISharesScraper, ISHARES_HOLDINGS_COLUMNS


# TODO: use to test
HEADER = "Ticker dell'emittente,Nome,Settore,Asset Class,Valore di mercato,Ponderazione (%),Valore nozionale,Nominale,Prezzo,Area Geografica,Cambio,Valuta di mercato"


class ISharesItScraper(ISharesScraper):
    """
    Scraper for iShares ETFs in Italy.
    It fetches listings and holdings data from the iShares API (CSV-based).
    """

    LISTINGS_URL = "https://www.ishares.com/it/investitore-privato/it/product-screener/product-screener-v3.1.jsn?dcrPath=/templatedata/config/product-screener-v3/data/it/it/product-screener/ishares-product-screener-backend-config&siteEntryPassthrough=true"
    HOLDINGS_URL_TEMPLATE = "https://www.ishares.com/it/investitore-privato/it/prodotti/{product_id}/fund/1506575546154.ajax?fileType=csv"

    LOCALE_COLUMN_NAMES: Dict[str, ISHARES_HOLDINGS_COLUMNS] = {
        "Ticker dell'emittente": "ticker",
        "Nome": "name",
        "Settore": "sector",
        "Asset Class": "asset_class",
        "Valore di mercato": "market_value",
        "Ponderazione (%)": "weight",
        "Valore nozionale": "book_value",
        "Nominale": "nominal",
        "Prezzo": "price",
        "Area Geografica": "geographic_area",
        "Cambio": "exchange_rate",
        "Valuta di mercato": "market_currency",
    }
