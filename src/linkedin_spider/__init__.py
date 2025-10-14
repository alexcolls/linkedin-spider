"""LinkedIn Spider - A professional CLI tool for scraping LinkedIn profiles."""

__version__ = "0.1.0"
__author__ = "quantium"
__description__ = "A professional CLI tool for scraping LinkedIn profiles via Google Search"

from linkedin_spider.core import scraper
from linkedin_spider.models import Profile, ProfileCollection

__all__ = ["scraper", "Profile", "ProfileCollection", "__version__"]
