import logging
from enum import Enum

_log = logging.getLogger(__name__)


class GICSector(str, Enum):
    ENERGY = "Energy"
    MATERIALS = "Materials"
    INDUSTRIALS = "Industrials"
    CONSUMER_DISCRETIONARY = "Consumer Discretionary"
    CONSUMER_STAPLES = "Consumer Staples"
    HEALTH_CARE = "Health Care"
    FINANCIALS = "Financials"
    INFORMATION_TECHNOLOGY = "Information Technology"
    COMMUNICATION_SERVICES = "Communication Services"
    UTILITIES = "Utilities"
    REAL_ESTATE = "Real Estate"


# Maps Italian sector names (iShares IT + Xtrackers IT) to GICSector.
# Vanguard already returns standard GICS English names, no mapping needed.
ITALIAN_TO_GICS: dict[str, GICSector] = {
    # iShares IT
    "Comunicazione": GICSector.COMMUNICATION_SERVICES,
    "Consumi Discrezionali": GICSector.CONSUMER_DISCRETIONARY,
    "Energia": GICSector.ENERGY,
    "Finanziari": GICSector.FINANCIALS,
    "Generi di largo consumo": GICSector.CONSUMER_STAPLES,
    "IT": GICSector.INFORMATION_TECHNOLOGY,
    "Immobili": GICSector.REAL_ESTATE,
    "Imprese di servizi di pubblica utilità": GICSector.UTILITIES,
    "Industriali": GICSector.INDUSTRIALS,
    "Materiali": GICSector.MATERIALS,
    "Salute": GICSector.HEALTH_CARE,
    # Xtrackers IT
    "Assistenza sanitaria": GICSector.HEALTH_CARE,
    "Beni di prima necessità": GICSector.CONSUMER_STAPLES,
    "Beni voluttuari": GICSector.CONSUMER_DISCRETIONARY,
    "Finanza": GICSector.FINANCIALS,
    "Immobiliare": GICSector.REAL_ESTATE,
    "Industria": GICSector.INDUSTRIALS,
    "Materie prime": GICSector.MATERIALS,
    "Prodotti industriali": GICSector.INDUSTRIALS,
    "Sanità": GICSector.HEALTH_CARE,
    "Servizi di comunicazione": GICSector.COMMUNICATION_SERVICES,
    "Servizi di pubblica utilità": GICSector.UTILITIES,
    "Tecnologia": GICSector.INFORMATION_TECHNOLOGY,
    "Tecnologia dell'informazione": GICSector.INFORMATION_TECHNOLOGY,
    "Telecomunicazioni": GICSector.COMMUNICATION_SERVICES,
    "Utenze": GICSector.UTILITIES,
}

_NO_SECTOR = {"Liquidità e/o derivati", "Tesoro", "sconosciuta"}


def italian_to_gics(name: str) -> GICSector | None:
    if name in _NO_SECTOR:
        return None
    if name not in ITALIAN_TO_GICS:
        _log.warning("Unknown sector name (not mapped to GICS): %r", name)
    return ITALIAN_TO_GICS.get(name)


def find_unmapped(names: list[str]) -> list[str]:
    """Return unique names not present in ITALIAN_TO_GICS and not in _NO_SECTOR."""
    return sorted({n for n in names if n not in ITALIAN_TO_GICS and n not in _NO_SECTOR})
