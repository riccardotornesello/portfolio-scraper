import csv
import logging

_log = logging.getLogger(__name__)


EXCHANGES_CSV_PATH = "assets/ISO10383_MIC.csv"

EXCHANGE_TO_MIC = None

FIXES = {
    "NEW YORK STOCK EXCHANGE INC.": "XNYS",
    "XBSP": "BNTW",
    "QATAR EXCHANGE": "DSMD",
    "EURONEXT AMSTERDAM": "XAMS",
    "ISTANBUL STOCK EXCHANGE": "XIST",
}


def exchange_to_mic(name: str) -> str | None:
    global EXCHANGE_TO_MIC

    if not name or name == "-":
        return None

    if EXCHANGE_TO_MIC is None:
        exchanges_map = {}
        with open(EXCHANGES_CSV_PATH, "r") as f:
            reader = csv.DictReader(f)
            for row in reader:
                exchanges_map[
                    row["MARKET NAME-INSTITUTION DESCRIPTION"].strip().upper()
                ] = row["MIC"].strip().upper()
        EXCHANGE_TO_MIC = exchanges_map

    exchange_name = name.strip().upper()

    if exchange_name not in EXCHANGE_TO_MIC and exchange_name not in FIXES:
        _log.warning("Unknown exchange name (not mapped to MIC): %r", exchange_name)
        return f"__{name}__"

    return EXCHANGE_TO_MIC.get(exchange_name) or FIXES.get(exchange_name)
