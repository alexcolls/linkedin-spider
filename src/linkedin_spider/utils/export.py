"""Export utilities for LinkedIn Spider."""

import json
from datetime import datetime
from pathlib import Path
from typing import Iterable, List, Optional

import pandas as pd

from linkedin_spider.models import Profile, unique_profile_urls
from linkedin_spider.utils.config import config
from linkedin_spider.utils.logger import logger


def create_private_file(path: Path) -> Path:
    """Create a file only the owner can read: these files hold personal data."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.touch(mode=0o600)
    path.chmod(0o600)
    return path


def load_urls(path: Path) -> List[str]:
    """
    Read profile URLs from a file with one URL per line.

    Args:
        path: File to read

    Returns:
        Canonical URLs without duplicates. Lines that aren't LinkedIn profile
        URLs are dropped, so a bad file can't send the logged-in browser elsewhere.
    """
    lines = [line.strip() for line in path.read_text(encoding="utf-8").splitlines()]
    urls = unique_profile_urls(line for line in lines if line)

    ignored = sum(1 for line in lines if line) - len(urls)
    if ignored:
        logger.warning(f"Ignored {ignored} duplicate or non-profile lines in {path}")

    return urls


def save_urls(path: Path, urls: Iterable[str]) -> int:
    """
    Add profile URLs to a file, keeping the ones already there.

    Args:
        path: File to write
        urls: URLs to add

    Returns:
        Number of URLs now in the file
    """
    existing = load_urls(path) if path.exists() else []
    merged = unique_profile_urls([*existing, *urls])

    create_private_file(path).write_text("\n".join(merged) + "\n", encoding="utf-8")
    return len(merged)


class Exporter:
    """Handles exporting profiles to various formats."""

    def __init__(self, data_dir: Optional[Path] = None):
        """
        Initialize exporter.

        Args:
            data_dir: Directory to save exports. If None, uses config value.
        """
        self.data_dir = data_dir or config.data_dir
        self.data_dir.mkdir(parents=True, exist_ok=True)

    def _generate_filename(self, base_name: str, extension: str) -> Path:
        """
        Generate filename with optional timestamp.

        Args:
            base_name: Base filename
            extension: File extension (without dot)

        Returns:
            Full path to file
        """
        if config.timestamp_filenames:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{base_name}_{timestamp}.{extension}"
        else:
            filename = f"{base_name}.{extension}"

        return self.data_dir / filename

    def check_format(self, format: Optional[str] = None) -> str:
        """
        Confirm an export format can be written, before any scraping starts.

        Args:
            format: Export format (csv, json, excel). If None, uses config default.

        Returns:
            The resolved format

        Raises:
            ValueError: If the format is unknown
            ImportError: If Excel export is requested without openpyxl installed
        """
        format = str(format or config.default_export_format).lower()

        if format not in ("csv", "json", "excel", "xlsx"):
            raise ValueError(
                f"Unknown export format: {format}. Use csv, json, or excel."
            )

        if format in ("excel", "xlsx"):
            try:
                import openpyxl  # noqa: F401
            except ImportError as e:
                raise ImportError(
                    "Excel export requires openpyxl. "
                    "Install with: pip install linkedin-tarantula[excel]"
                ) from e

        return format

    def to_csv(self, profiles: List[Profile], filename: str = "profiles") -> Path:
        """
        Export profiles to CSV.

        Args:
            profiles: List of profiles to export
            filename: Base filename (without extension)

        Returns:
            Path to exported file
        """
        if not profiles:
            logger.warning("No profiles to export")
            return None

        # Convert to DataFrame
        data = [profile.to_dict() for profile in profiles]
        df = pd.DataFrame(data)

        # Generate filename
        filepath = self._generate_filename(filename, "csv")

        # Export
        df.to_csv(filepath, index=False, encoding="utf-8")
        logger.info(f"Exported {len(profiles)} profiles to {filepath}")

        return filepath

    def to_json(
        self, profiles: List[Profile], filename: str = "profiles"
    ) -> Path:
        """
        Export profiles to JSON.

        Args:
            profiles: List of profiles to export
            filename: Base filename (without extension)

        Returns:
            Path to exported file
        """
        if not profiles:
            logger.warning("No profiles to export")
            return None

        # Convert to dict
        data = [profile.to_dict() for profile in profiles]

        # Generate filename
        filepath = self._generate_filename(filename, "json")

        # Export
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        logger.info(f"Exported {len(profiles)} profiles to {filepath}")

        return filepath

    def to_excel(
        self, profiles: List[Profile], filename: str = "profiles"
    ) -> Path:
        """
        Export profiles to Excel.

        Args:
            profiles: List of profiles to export
            filename: Base filename (without extension)

        Returns:
            Path to exported file

        Raises:
            ImportError: If openpyxl is not installed
        """
        try:
            import openpyxl
        except ImportError:
            logger.error(
                "openpyxl not installed. Install with: poetry install -E excel"
            )
            raise

        if not profiles:
            logger.warning("No profiles to export")
            return None

        # Convert to DataFrame
        data = [profile.to_dict() for profile in profiles]
        df = pd.DataFrame(data)

        # Generate filename
        filepath = self._generate_filename(filename, "xlsx")

        # Export
        df.to_excel(filepath, index=False, engine="openpyxl")
        logger.info(f"Exported {len(profiles)} profiles to {filepath}")

        return filepath

    def export(
        self,
        profiles: List[Profile],
        format: Optional[str] = None,
        filename: str = "profiles",
    ) -> Path:
        """
        Export profiles to specified format.

        Args:
            profiles: List of profiles to export
            format: Export format (csv, json, excel). If None, uses config default.
            filename: Base filename (without extension)

        Returns:
            Path to exported file
        """
        format = self.check_format(format)

        if format == "csv":
            return self.to_csv(profiles, filename)
        elif format == "json":
            return self.to_json(profiles, filename)
        elif format in ("excel", "xlsx"):
            return self.to_excel(profiles, filename)
        else:
            raise ValueError(
                f"Unknown export format: {format}. Use csv, json, or excel."
            )


# Global exporter instance
exporter = Exporter()
