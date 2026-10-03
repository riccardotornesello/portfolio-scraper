from enum import Enum


class Sector(str, Enum):
    """
    Standard sectors of the holdings: the 11 GICS sectors, plus the
    categories used for bonds whose issuer is not a company.
    """

    # GICS sectors
    COMMUNICATION_SERVICES = "Communication Services"
    CONSUMER_DISCRETIONARY = "Consumer Discretionary"
    CONSUMER_STAPLES = "Consumer Staples"
    ENERGY = "Energy"
    FINANCIALS = "Financials"
    HEALTH_CARE = "Health Care"
    INDUSTRIALS = "Industrials"
    INFORMATION_TECHNOLOGY = "Information Technology"
    MATERIALS = "Materials"
    REAL_ESTATE = "Real Estate"
    UTILITIES = "Utilities"

    # Bonds
    GOVERNMENT = "Government"  # Treasuries, sovereigns, agencies, supranationals
    SECURITIZED = "Securitized"  # Covered bonds, MBS, ABS


# English names (uppercase) shared by all the scrapers
SECTORS_MAP: dict[str, Sector | None] = {
    **{sector.value.upper(): sector for sector in Sector},
}
