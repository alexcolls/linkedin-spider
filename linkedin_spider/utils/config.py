"""Configuration management for LinkedIn Spider."""

import os
from pathlib import Path
from typing import Any, Dict, Optional

import yaml
from dotenv import load_dotenv


class Config:
    """Manages configuration from environment variables and YAML files."""

    def __init__(self, config_path: Optional[Path] = None):
        """
        Initialize configuration.

        Args:
            config_path: Path to config.yaml file. If None, uses default location.
        """
        # Load environment variables
        load_dotenv()

        # Set default config path
        if config_path is None:
            config_path = Path.cwd() / "config.yaml"

        self.config_path = config_path
        self._config_data: Dict[str, Any] = {}

        # Load YAML config if exists
        if self.config_path.exists():
            with open(self.config_path, "r") as f:
                self._config_data = yaml.safe_load(f) or {}

    def get(self, key: str, default: Any = None, section: Optional[str] = None) -> Any:
        """
        Get configuration value.

        Args:
            key: Configuration key
            default: Default value if key not found
            section: YAML section to look in

        Returns:
            Configuration value
        """
        # Try environment variable first (uppercase)
        env_key = key.upper()
        env_value = os.getenv(env_key)
        if env_value is not None:
            # Convert string booleans
            if env_value.lower() in ("true", "false"):
                return env_value.lower() == "true"
            # Try to convert to int
            try:
                return int(env_value)
            except ValueError:
                return env_value

        # Try YAML config
        if section and section in self._config_data:
            return self._config_data[section].get(key, default)

        return default

    @property
    def linkedin_email(self) -> str:
        """Get LinkedIn email from environment."""
        return self.get("linkedin_email", "")

    @property
    def linkedin_password(self) -> str:
        """Get LinkedIn password from environment."""
        return self.get("linkedin_password", "")

    @property
    def min_delay(self) -> int:
        """Get minimum delay between actions."""
        return self.get("min_delay", 10, "scraper")

    @property
    def max_delay(self) -> int:
        """Get maximum delay between actions."""
        return self.get("max_delay", 25, "scraper")

    @property
    def max_search_pages(self) -> int:
        """Get maximum number of search pages to scrape."""
        return self.get("max_search_pages", 100, "scraper")

    @property
    def scroll_duration(self) -> int:
        """Get scroll duration for profile pages."""
        return self.get("scroll_duration", 15, "scraper")

    @property
    def headless(self) -> bool:
        """Check if browser should run in headless mode."""
        return self.get("headless", False, "browser")

    @property
    def window_width(self) -> int:
        """Get browser window width."""
        return self.get("window_width", 1920, "browser")

    @property
    def window_height(self) -> int:
        """Get browser window height."""
        return self.get("window_height", 1080, "browser")

    @property
    def user_agent(self) -> str:
        """Get custom user agent."""
        return self.get("user_agent", "", "browser")

    @property
    def vpn_enabled(self) -> bool:
        """Check if VPN switching is enabled."""
        return self.get("enable_vpn", False) or self.get("enabled", False, "vpn")

    @property
    def vpn_command(self) -> str:
        """Get VPN command."""
        return self.get("vpn_command", "") or self.get("command", "protonvpn-cli c -r", "vpn")

    @property
    def vpn_switch_frequency(self) -> int:
        """Get VPN switch frequency."""
        return self.get("switch_frequency", 50, "vpn")

    @property
    def data_dir(self) -> Path:
        """Get data directory path (relative to current working directory)."""
        dir_str = self.get("data_dir", "data") or self.get("data_dir", "data", "export")
        # Use current working directory, not package installation directory
        return Path.cwd() / dir_str

    @property
    def default_export_format(self) -> str:
        """Get default export format."""
        return self.get("default_export_format", "csv") or self.get("default_format", "csv", "export")

    @property
    def timestamp_filenames(self) -> bool:
        """Check if filenames should include timestamps."""
        return self.get("timestamp_filenames", True, "export")

    @property
    def log_level(self) -> str:
        """Get log level."""
        return self.get("log_level", "INFO") or self.get("level", "INFO", "logging")

    @property
    def log_file(self) -> str:
        """Get log file path."""
        return self.get("log_file", "logs/linkedin-spider.log") or self.get("file", "logs/linkedin-spider.log", "logging")

    @property
    def console_logging(self) -> bool:
        """Check if console logging is enabled."""
        return self.get("console", True, "logging")


# Global config instance
config = Config()
