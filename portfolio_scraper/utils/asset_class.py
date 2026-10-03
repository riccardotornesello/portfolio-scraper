from enum import Enum


class AssetClass(str, Enum):
    """
    Standard asset classes of the holdings.
    """

    EQUITY = "Equity"
    FIXED_INCOME = "Fixed Income"
    CASH = "Cash"
    DERIVATIVES = "Derivatives"
    FUND = "Fund"
    ALTERNATIVE = "Alternative"
