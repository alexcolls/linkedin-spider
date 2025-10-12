"""Export utilities for LinkedIn Spider."""

import json
from datetime import datetime
from pathlib import Path
from typing import List, Optional

import pandas as pd

from linkedin_spider.models import Profile
from linkedin_spider.utils.config import config
from linkedin_spider.utils.logger import logger


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

    def to_csv(
        self, profiles: List[Profile], filename: str = "profiles"
    ) -> Path:
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
        format: str = None,
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
        if format is None:
            format = config.default_export_format

        format = format.lower()

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
