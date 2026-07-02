from portfolio_scraper.etf.xtrackers.base import XtrackersBaseEtfScraper
from portfolio_scraper.utils.sector import GICSector


class XtrackersItScraper(XtrackersBaseEtfScraper):
    COUNTRY_LANGUAGE = "it"

    HOLDINGS_URL_TEMPLATE = (
        "https://etf.dws.com/etfdata/export/ITA/ITA/csv/product/constituent/{isin}/"
    )
    HOLDINGS_COLUMNS_NAMES: dict[str, str] = {
        "name": "Constituent Name",
        "isin": "Constituent ISIN",
        "weight_in_etf": "Constituent Weighting",
        "gics_sector": "Constituent Industry Classification Name",
        "country_alpha2": "Constituent Country",
        "exchange": "Constituent Main Exchange Name",
        "currency": "Constituent Currency ISO Code",
        "rating": "Constituent Rating",
    }
    SECTORS_MAP: dict[str, GICSector] = {
        "AEROSPAZIO E DIFESA": GICSector.INDUSTRIALS,
        "APPARECCHIATURE E STRUMENTI ELETTRONICI ": GICSector.INFORMATION_TECHNOLOGY,
        "COMPONENTI E APPARECCHIATURE ELETTRICHE": GICSector.INDUSTRIALS,
        "MACCHINE PER L'EDILIZIA E AUTOCARRI PESANTI": GICSector.INDUSTRIALS,
        "TRASMISSIONI VIA CAVO E VIA SATELLITE": GICSector.COMMUNICATION_SERVICES,
        "SCONOSCIUTA": None,
        "SERVIZI DI CONSULENZA IT E ALTRI SERVIZI CORRELATI": GICSector.INFORMATION_TECHNOLOGY,
        "SERVIZI DI MANUTENZIONE E AMBIENTALI": GICSector.INDUSTRIALS,
        "SOFTWARE DI SISTEMA": GICSector.INFORMATION_TECHNOLOGY,
        "VETTORI ALTERNATIVI": GICSector.INDUSTRIALS,
        "BENI DI PRIMA NECESSITÀ": GICSector.CONSUMER_STAPLES,
        "BENI VOLUTTUARI": GICSector.CONSUMER_DISCRETIONARY,
        "ENERGIA": GICSector.ENERGY,
        "FINANZA": GICSector.FINANCIALS,
        "IMMOBILIARE": GICSector.REAL_ESTATE,
        "MATERIALI": GICSector.MATERIALS,
        "PRODOTTI INDUSTRIALI": GICSector.INDUSTRIALS,
        "SANITÀ": GICSector.HEALTH_CARE,
        "SERVIZI DI COMUNICAZIONE": GICSector.COMMUNICATION_SERVICES,
        "SERVIZI DI PUBBLICA UTILITÀ": GICSector.UTILITIES,
        "TECNOLOGIA DELL'INFORMAZIONE": GICSector.INFORMATION_TECHNOLOGY,
    }
