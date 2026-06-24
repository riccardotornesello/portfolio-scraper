from .base import BaseEtfScraper
from .amundi import AmundiItScraper
from .ishares import ISharesItScraper
from .vanguard import VanguardItScraper
from .xtrackers import XtrackersItScraper

__all__ = [
    "BaseEtfScraper",
    "AmundiItScraper",
    "ISharesItScraper",
    "VanguardItScraper",
    "XtrackersItScraper",
]
