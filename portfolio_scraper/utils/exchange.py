# TODO: create a generic structure to map country names to ISO codes


import logging


_log = logging.getLogger(__name__)


EXCHANGE_TO_MIC: dict[str, str] = {
    # iShares
    "Asx - All Markets": "XASX",
    "Asx - Trade24": "XASX",
    "Bolsa De Madrid": "XMAD",
    "Borsa Italiana": "XMIL",
    "Cboe BZX": "BATS",
    "Chicago Mercantile Exchange": "XCME",
    "Deutsche Boerse Xetra": "XETR",
    "Eurex Deutschland": "XEUR",
    "Euronext Amsterdam": "XAMS",
    "Hong Kong Exchanges And Clearing Ltd": "XHKG",
    "IFLL": "IFLL",
    "Irish Stock Exchange - All Market": "XDUB",
    "London Stock Exchange": "XLON",
    "NASDAQ": "XNAS",
    "Nasdaq Omx Helsinki Ltd.": "XHEL",
    "Nasdaq Omx Nordic": "XSTO",
    "New York Stock Exchange Inc.": "XNYS",
    "New Zealand Exchange Ltd": "XNZE",
    "Nyse Euronext - Euronext Brussels": "XBRU",
    "Nyse Euronext - Euronext Lisbon": "XLIS",
    "Nyse Euronext - Euronext Paris": "XPAR",
    "Omx Nordic Exchange Copenhagen A/S": "XCSE",
    "Osaka Securities Exchange": "XOSE",
    "Oslo Bors Asa": "XOSL",
    "SIX Swiss Exchange": "XSWX",
    "Singapore Exchange": "XSES",
    "Singapore Exchange Derivatives Clearing Limited": "XSIM",
    "Standard-Classica-Forts": "MISX",
    "Tel Aviv Stock Exchange": "XTAE",
    "Tokyo Stock Exchange": "XTKS",
    "Toronto Stock Exchange": "XTSE",
    "Wiener Boerse Ag": "XWBO",
    "Xetra": "XETR",
    # Xtrackers
    "Australian Stock Exchange": "XASX",
    "Copenhagen Stock Exchange": "XCSE",
    "Euronext Brussels": "XBRU",
    "Euronext Lisbon": "XLIS",
    "Euronext Paris": "XPAR",
    "Helsinki Stock Exchange": "XHEL",
    "Irish Stock Exchange": "XDUB",
    "Mercado Continuo Espana": "XMAD",
    "Milan Stock Exchange": "XMIL",
    "NASDAQ National Market System": "XNAS",
    "New York Stock Exchange": "XNYS",
    "New Zealand Exchange": "XNZE",
    "Oslo Stock Exchange": "XOSL",
    "Scoach Switzerland": "XSWX",
    "Stockholm Stock Exchange": "XSTO",
    "Vienna Stock Exchange": "XWBO",
    "XETRA": "XETR",
    # Xtrackers / other
    "Ice Futures U.S.": "IFUS",
    "Bursa Malaysia": "XKLS",
    "Gretai Securities Market": "ROTC",
    "Indonesia Stock Exchange": "XIDX",
    "Istanbul Stock Exchange": "XIST",
    "Johannesburg Stock Exchange": "XJSE",
    "Korea Exchange (Kosdaq)": "XKOS",
    "Korea Exchange (Stock Market)": "XKRX",
    "National Stock Exchange Of India": "XNSE",
    "Nyse Mkt Llc": "XASE",
    "Santiago Stock Exchange": "XSGO",
    "Saudi Stock Exchange": "XSAU",
    "Shanghai Stock Exchange": "XSHG",
    "Shenzhen Stock Exchange": "XSHE",
    "Stock Exchange Of Thailand": "XBKK",
    "Taiwan Stock Exchange": "XTAI",
    "The Montreal Exchange / Bourse De Montreal": "XMOD",
    "Warsaw Stock Exchange/Equities/Main Market": "XWAR",
    "XBSP": "BVMF",
}


_NO_MARKET = {"-", "NO MARKET (E.G. UNLISTED)", "Index And Options Market"}


def exchange_to_mic(name: str) -> str | None:
    if name in _NO_MARKET:
        return None
    if name not in EXCHANGE_TO_MIC:
        _log.warning("Unknown exchange name (not mapped to MIC): %r", name)
    return EXCHANGE_TO_MIC.get(name, name)


def find_unmapped(names: list[str]) -> list[str]:
    """Return unique names not present in EXCHANGE_TO_MIC and not in _NO_MARKET."""
    return sorted(
        {n for n in names if n not in EXCHANGE_TO_MIC and n not in _NO_MARKET}
    )
