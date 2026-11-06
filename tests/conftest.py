"""Pytest configuration and fixtures."""

import importlib
import logging

import pytest

from linkedin_spider.models import Profile
from linkedin_spider.utils.logger import logger

# core/__init__.py and utils/__init__.py replace these submodule names with instances
config_module = importlib.import_module("linkedin_spider.utils.config")

CONFIG_ENV_VARS = [
    "LINKEDIN_EMAIL",
    "LINKEDIN_PASSWORD",
    "DATA_DIR",
    "DEFAULT_EXPORT_FORMAT",
    "LOG_LEVEL",
    "LOG_FILE",
    "HEADLESS",
    "MIN_DELAY",
    "MAX_DELAY",
    "SCROLL_DURATION",
    "CHROME_NO_SANDBOX",
    "ENABLE_VPN",
    "VPN_COMMAND",
    "LINKEDIN_SPIDER_CWD",
]


@pytest.fixture(autouse=True)
def isolated_environment(tmp_path, monkeypatch):
    """Run every test in an empty directory, unaffected by the developer's setup."""
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(config_module, "load_dotenv", lambda: None)
    for name in CONFIG_ENV_VARS:
        monkeypatch.delenv(name, raising=False)

    yield

    for handler in [h for h in logger.handlers if isinstance(h, logging.FileHandler)]:
        logger.removeHandler(handler)
        handler.close()


@pytest.fixture
def sample_profiles():
    """Create multiple sample profiles for testing."""
    return [
        Profile(
            url="https://www.linkedin.com/in/johndoe",
            name="John Doe",
            title="Software Engineer",
        ),
        Profile(
            url="https://www.linkedin.com/in/janedoe",
            name="Jane Doe",
            title="Data Scientist",
        ),
    ]
