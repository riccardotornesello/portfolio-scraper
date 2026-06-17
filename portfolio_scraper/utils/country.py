import json
import logging

_log = logging.getLogger(__name__)


COUNTRIES_JSON_PATH = "portfolio_scraper/assets/countries.json"

COUNTRIES = None
LANGUAGE_MAPS: dict[str, dict[str, str]] = {}

FIXES = {
    "ita": {
        "UNIONE EUROPEA": None,
        "COREA": "KR",
        "PAESI BASSI (OLANDA)": "NL",
        "STATI UNITI": "US",
    }
}


def get_language_map(language: str) -> dict[str, str]:
    global COUNTRIES, LANGUAGE_MAPS

    if not COUNTRIES:
        with open(COUNTRIES_JSON_PATH, "r") as f:
            COUNTRIES = json.load(f)

    if language in LANGUAGE_MAPS:
        return LANGUAGE_MAPS[language]

    translations = {}

    for row in COUNTRIES:
        country_code = row["cca2"]

        if language == "eng":
            translation_data = row["name"]
        else:
            translation_data = row["translations"].get(language, {})

        common_name = translation_data.get("common")
        if common_name:
            translations[common_name.upper()] = country_code

        official_name = translation_data.get("official")
        if official_name:
            translations[official_name.upper()] = country_code

    LANGUAGE_MAPS[language] = translations
    return translations


def country_to_iso(name: str, language: str = "eng") -> str | None:
    if not name or name == "-":
        return None

    translations = get_language_map(language)
    country = name.upper()

    if country not in translations and country not in FIXES.get(language, {}):
        _log.warning(
            "Unknown country name (not mapped to ISO): %r (%s)",
            country,
            language,
        )
        return f"__{country}__"

    return translations.get(country) or FIXES.get(language, {}).get(country)
