from typing import Dict


from ...utils.asset_class import AssetClass
from ...utils.sector import Sector
from .base import ISharesBaseScraper, ISHARES_HOLDINGS_COLUMNS


# TODO: use to test
HEADER = "Ticker dell'emittente,Nome,Settore,Asset Class,Valore di mercato,Ponderazione (%),Valore nozionale,Nominale,Prezzo,Area Geografica,Cambio,Valuta di mercato"


class ISharesItScraper(ISharesBaseScraper):
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

    COUNTRIES_LANGUAGE = "it"
    SECTORS_MAP: Dict[str, Sector | None] = {
        # Equity
        "COMUNICAZIONE": Sector.COMMUNICATION_SERVICES,
        "CONSUMI DISCREZIONALI": Sector.CONSUMER_DISCRETIONARY,
        "GENERI DI LARGO CONSUMO": Sector.CONSUMER_STAPLES,
        "ENERGIA": Sector.ENERGY,
        "FINANZIARI": Sector.FINANCIALS,
        "SALUTE": Sector.HEALTH_CARE,
        "INDUSTRIALI": Sector.INDUSTRIALS,
        "IT": Sector.INFORMATION_TECHNOLOGY,
        "MATERIALI": Sector.MATERIALS,
        "IMMOBILI": Sector.REAL_ESTATE,
        "IMPRESE DI SERVIZI DI PUBBLICA UTILITÀ": Sector.UTILITIES,
        # Corporate bonds
        "COMUNICAZIONI": Sector.COMMUNICATION_SERVICES,
        "BENI DI CONSUMO CICLICI": Sector.CONSUMER_DISCRETIONARY,
        "CONSUMER NON-CYCLICAL": Sector.CONSUMER_STAPLES,
        "SANITÀ": Sector.HEALTH_CARE,
        "ATTIVITÀ BANCARIE": Sector.FINANCIALS,
        "ASSICURAZIONI": Sector.FINANCIALS,
        "SOCIETÀ FINANZIARIE": Sector.FINANCIALS,
        "BROKERAGE/ASSET MANAGERS/EXCHANGES": Sector.FINANCIALS,
        "FINANCIAL OTHER": Sector.FINANCIALS,
        "BENI INDIRETTI": Sector.INDUSTRIALS,
        "TRASPORTO": Sector.INDUSTRIALS,
        "INDUSTRIAL OTHER": Sector.INDUSTRIALS,
        "BASIC INDUSTRY": Sector.MATERIALS,
        "CERTIFICATO IMMOBILIARE": Sector.REAL_ESTATE,
        "ELETTRICO": Sector.UTILITIES,
        "GAS NATURALE": Sector.UTILITIES,
        "UTILITY OTHER": Sector.UTILITIES,
        # Government bonds
        "TESORO": Sector.GOVERNMENT,
        "BUONI DEL TESORO": Sector.GOVERNMENT,
        "SOVRANI": Sector.GOVERNMENT,
        "SUPRANATIONAL": Sector.GOVERNMENT,
        "GOVERNMENT RELATED": Sector.GOVERNMENT,
        "GOVERNMENT GUARANTEED": Sector.GOVERNMENT,
        "GOVERNMENT SPONSORED": Sector.GOVERNMENT,
        "OWNED NO GUARANTEE": Sector.GOVERNMENT,
        "LOCAL GOVERNMENT": Sector.GOVERNMENT,
        "LOCAL GOVERNMENT GUARANTEE": Sector.GOVERNMENT,
        "LOCAL GOVERNMENT NO GUARANTEE": Sector.GOVERNMENT,
        # Securitized bonds
        "SECURITIZZATO": Sector.SECURITIZED,
        "COPERTO": Sector.SECURITIZED,
        "COVERED OTHER": Sector.SECURITIZED,
        "MORTGAGE COLLATERALIZED": Sector.SECURITIZED,
        "PUBLIC SECTOR COLLATERALIZED": Sector.SECURITIZED,
        "HYBRID COLLATERALIZED": Sector.SECURITIZED,
        "AGENCY FIXED RATE": Sector.SECURITIZED,
        "CMBS (TITOLO OBBLIGAZIONARIO PER IL QUALE LA GARANZIA DI PAGAMENTO È RAPPRESENTATA DA UN PORTAFOGLIO DI MUTUI)": Sector.SECURITIZED,
        "STRANDED COST UTILITY": Sector.SECURITIZED,
        "WHOLE BUSINESS": Sector.SECURITIZED,
        # Not a sector
        "AZIENDALI": None,
        "ALTRO": None,
        "ETFS": None,
        "LIQUIDITÀ E/O DERIVATI": None,
    }
    ASSET_CLASSES_MAP: Dict[str, AssetClass | None] = {
        "AZIONARIO": AssetClass.EQUITY,
        "OBBLIGAZIONARIO": AssetClass.FIXED_INCOME,
        "CONTANTI": AssetClass.CASH,
        "CASH COLLATERAL AND MARGINS": AssetClass.CASH,
        "MONEY MARKET": AssetClass.CASH,
        "FX": AssetClass.DERIVATIVES,
        "FORWARDS": AssetClass.DERIVATIVES,
        "FUTURES": AssetClass.DERIVATIVES,
        "SWAPS": AssetClass.DERIVATIVES,
        "OTHER DERIVATIVES": AssetClass.DERIVATIVES,
        "ALTERNATIVE": AssetClass.ALTERNATIVE,
    }
