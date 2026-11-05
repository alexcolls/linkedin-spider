"""LinkedIn Spider - A professional CLI tool for scraping LinkedIn profiles."""

from importlib.metadata import PackageNotFoundError, version

from linkedin_spider.models import Profile, ProfileCollection

try:
    __version__ = version("linkedin-tarantula")
except PackageNotFoundError:
    __version__ = "0.0.0+unknown"

__author__ = "quantium"
__description__ = (
    "A professional CLI tool for scraping LinkedIn profiles via Google Search"
)

__all__ = ["Profile", "ProfileCollection", "__version__"]
