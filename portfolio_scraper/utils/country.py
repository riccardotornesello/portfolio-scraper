import functools
import gettext

import pycountry


# Names that are not a country (e.g. supranational issuers)
WITHOUT_CODE = {
    "en": {"SUPRANATIONAL", "SUPRANATIONALS", "EUROPEAN UNION"},
    "it": {"UNIONE EUROPEA", "SOVRANAZIONALE"},
}
FIXES = {
    "en": {
        "CAYMAN ISLAND": "KY",
        "CZECH REPUBLIC": "CZ",
        "RUSSIA": "RU",
        "SOUTH KOREA": "KR",
        "TAIWAN": "TW",
        "TURKEY": "TR",
        "UAE": "AE",
        "VIETNAM": "VN",
    },
    "it": {
        "COREA": "KR",
        "COSTARICA": "CR",
        "DEMOCRATIC REP OF CONGO": "CD",
        "DOMINICANA (REP.)": "DO",
        "ISOLE FAROE": "FO",
        "ISOLE VERGINE BRITANNICHE": "VG",
        "MACEDONIA": "MK",
        "MALESIA": "MY",
        "PAESI BASSI (OLANDA)": "NL",
        "REPUBBLICA CECA": "CZ",
        "REPUBBLICA DI COREA (COREA DEL SUD)": "KR",
        "SLOVACCHIA (REPUBBLICA SLOVACCA)": "SK",
        "STATI UNITI D'AMERICA": "US",
        "SUD AFRICA": "ZA",
        "TAILANDIA": "TH",
        "TAIWAN": "TW",
    },
}


def gen_countries_translation_map(language: str) -> dict[str, str]:
    translation = gettext.translation(
        "iso3166-1",
        pycountry.LOCALES_DIR,
        languages=[language],
    )

    translation_map = {
        v.upper().strip(): k.upper().strip()
        for k, v in translation._catalog.items()
        if k and v
    }
    return translation_map


@functools.cache
def gen_country_to_alpha_2_map(language: str | None) -> dict[str, str | None]:
    """
    Generate a map from the uppercase country names in the given language to
    the ISO 3166-1 alpha-2 codes. With language None, the map validates alpha-2 codes.
    """
    if language is None:
        return {country.alpha_2: country.alpha_2 for country in pycountry.countries}

    # English names: the names in other languages fall back to them,
    # as providers sometimes leave some countries in English
    country_to_alpha_2 = {}
    for country in pycountry.countries:
        for attribute in ("name", "common_name", "official_name"):
            name = getattr(country, attribute, None)
            if name:
                country_to_alpha_2[name.upper()] = country.alpha_2

    if language != "en":
        translation_map = gen_countries_translation_map(language)
        for name, english_name in translation_map.items():
            country = pycountry.countries.get(name=english_name)
            if country:
                country_to_alpha_2[name] = country.alpha_2

    country_to_alpha_2.update(
        {name: None for name in WITHOUT_CODE.get(language, set())}
    )
    country_to_alpha_2["-"] = None  # Handle dash case
    country_to_alpha_2.update(FIXES.get(language, {}))  # Apply fixes
    return country_to_alpha_2


@functools.cache
def gen_alpha_3_to_alpha_2_map() -> dict[str, str]:
    return {country.alpha_3: country.alpha_2 for country in pycountry.countries}
