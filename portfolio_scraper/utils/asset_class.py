import logging
from enum import Enum

_log = logging.getLogger(__name__)


class AssetClass(str, Enum):
    EQUITY = "Equity"
    FIXED_INCOME = "Fixed Income"
    REAL_ESTATE = "Real Estate"
    CASH = "Cash"
    DERIVATIVES = "Derivatives"
    ALTERNATIVE = "Alternative"


_ISHARES_TO_ASSET_CLASS: dict[str, AssetClass] = {
    "Azionario": AssetClass.EQUITY,
    "Obbligazionario": AssetClass.FIXED_INCOME,
    "Contanti": AssetClass.CASH,
    "Cash Collateral and Margins": AssetClass.CASH,
    "Money Market": AssetClass.CASH,
    "FX": AssetClass.DERIVATIVES,
    "Forwards": AssetClass.DERIVATIVES,
    "Futures": AssetClass.DERIVATIVES,
    "Swaps": AssetClass.DERIVATIVES,
    "Alternative": AssetClass.ALTERNATIVE,
}

_VANGUARD_TO_ASSET_CLASS: dict[str, AssetClass] = {
    "EQ.STOCK": AssetClass.EQUITY,
    "EQ.PREF": AssetClass.EQUITY,
    "EQ.DRCPT": AssetClass.EQUITY,
    "EQ.RIGHT": AssetClass.EQUITY,
    "EQ.WRT": AssetClass.EQUITY,
    "EQ.REIT": AssetClass.REAL_ESTATE,
    "FI.CORP": AssetClass.FIXED_INCOME,
    "FI.US_GOV": AssetClass.FIXED_INCOME,
    "FI.NONUS_GOV": AssetClass.FIXED_INCOME,
    "FI.ABS": AssetClass.FIXED_INCOME,
    "FI.MBS": AssetClass.FIXED_INCOME,
    "FI.MUNI": AssetClass.FIXED_INCOME,
    "FI.IP": AssetClass.FIXED_INCOME,
    "CRNY": AssetClass.CASH,
    "CT.SPOT": AssetClass.CASH,
    "CT.FOREX": AssetClass.DERIVATIVES,
    "CT.PORTSWAP": AssetClass.DERIVATIVES,
    "DE.COMM": AssetClass.DERIVATIVES,
    "DE.IND": AssetClass.DERIVATIVES,
}

_ISHARES_NO_CLASS = {"Other"}
_VANGUARD_NO_CLASS: set[str] = set()


def ishares_to_asset_class(name: str) -> AssetClass | None:
    if name in _ISHARES_NO_CLASS:
        return None
    if name not in _ISHARES_TO_ASSET_CLASS:
        _log.warning("iShares: unknown asset class %r", name)
    return _ISHARES_TO_ASSET_CLASS.get(name)


def vanguard_to_asset_class(name: str) -> AssetClass | None:
    if name in _VANGUARD_NO_CLASS:
        return None
    if name not in _VANGUARD_TO_ASSET_CLASS:
        _log.warning("Vanguard: unknown asset class %r", name)
    return _VANGUARD_TO_ASSET_CLASS.get(name)


def find_unmapped_ishares(names: list[str]) -> list[str]:
    return sorted({n for n in names if n not in _ISHARES_TO_ASSET_CLASS and n not in _ISHARES_NO_CLASS})


def find_unmapped_vanguard(names: list[str]) -> list[str]:
    return sorted({n for n in names if n not in _VANGUARD_TO_ASSET_CLASS and n not in _VANGUARD_NO_CLASS})
