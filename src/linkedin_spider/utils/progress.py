"""Progress persistence for resume functionality."""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from linkedin_spider.utils import config, logger


class ProgressTracker:
    """Track and persist scraping progress for resume functionality."""

    def __init__(self, session_name: Optional[str] = None):
        """
        Initialize progress tracker.

        Args:
            session_name: Optional session name. If None, generates timestamp-based name.
        """
        self.session_name = session_name or f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.progress_file = config.data_dir / f".progress_{self.session_name}.json"
        self.progress_data: Dict = self._load_progress()

    def _load_progress(self) -> Dict:
        """Load progress from file if exists."""
        if self.progress_file.exists():
            try:
                with open(self.progress_file, "r") as f:
                    data = json.load(f)
                    logger.info(f"📂 Loaded progress from {self.progress_file}")
                    return data
            except Exception as e:
                logger.warning(f"Failed to load progress file: {e}")
                return self._create_new_progress()
        return self._create_new_progress()

    def _create_new_progress(self) -> Dict:
        """Create new progress data structure."""
        return {
            "session_name": self.session_name,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "total_urls": 0,
            "completed_urls": [],
            "failed_urls": [],
            "skipped_urls": [],
            "remaining_urls": [],
            "stats": {
                "total_scraped": 0,
                "total_failed": 0,
                "total_skipped": 0,
            },
        }

    def save(self):
        """Save progress to file."""
        try:
            self.progress_data["updated_at"] = datetime.now().isoformat()
            self.progress_file.parent.mkdir(parents=True, exist_ok=True)

            with open(self.progress_file, "w") as f:
                json.dump(self.progress_data, f, indent=2)

            logger.debug(f"💾 Progress saved to {self.progress_file}")
        except Exception as e:
            logger.error(f"Failed to save progress: {e}")

    def initialize(self, urls: List[str]):
        """
        Initialize progress with list of URLs to scrape.

        Args:
            urls: List of URLs to track
        """
        self.progress_data["total_urls"] = len(urls)
        self.progress_data["remaining_urls"] = urls.copy()
        self.save()

    def mark_completed(self, url: str):
        """
        Mark a URL as completed.

        Args:
            url: URL that was successfully scraped
        """
        if url in self.progress_data["remaining_urls"]:
            self.progress_data["remaining_urls"].remove(url)

        if url not in self.progress_data["completed_urls"]:
            self.progress_data["completed_urls"].append(url)
            self.progress_data["stats"]["total_scraped"] += 1

        self.save()

    def mark_failed(self, url: str, reason: Optional[str] = None):
        """
        Mark a URL as failed.

        Args:
            url: URL that failed to scrape
            reason: Optional reason for failure
        """
        if url in self.progress_data["remaining_urls"]:
            self.progress_data["remaining_urls"].remove(url)

        failure_entry = {"url": url, "reason": reason, "timestamp": datetime.now().isoformat()}

        if url not in [f["url"] for f in self.progress_data["failed_urls"]]:
            self.progress_data["failed_urls"].append(failure_entry)
            self.progress_data["stats"]["total_failed"] += 1

        self.save()

    def mark_skipped(self, url: str, reason: Optional[str] = None):
        """
        Mark a URL as skipped.

        Args:
            url: URL that was skipped
            reason: Optional reason for skipping
        """
        if url in self.progress_data["remaining_urls"]:
            self.progress_data["remaining_urls"].remove(url)

        skip_entry = {"url": url, "reason": reason}

        if url not in [s["url"] for s in self.progress_data["skipped_urls"]]:
            self.progress_data["skipped_urls"].append(skip_entry)
            self.progress_data["stats"]["total_skipped"] += 1

        self.save()

    def get_remaining(self) -> List[str]:
        """
        Get list of remaining URLs to scrape.

        Returns:
            List of URLs not yet completed
        """
        return self.progress_data["remaining_urls"].copy()

    def get_progress_percent(self) -> float:
        """
        Get progress percentage.

        Returns:
            Progress as percentage (0-100)
        """
        total = self.progress_data["total_urls"]
        if total == 0:
            return 0.0

        completed = len(self.progress_data["completed_urls"])
        return (completed / total) * 100

    def get_stats(self) -> Dict:
        """
        Get progress statistics.

        Returns:
            Dictionary with progress stats
        """
        return {
            "session_name": self.session_name,
            "total_urls": self.progress_data["total_urls"],
            "completed": len(self.progress_data["completed_urls"]),
            "failed": len(self.progress_data["failed_urls"]),
            "skipped": len(self.progress_data["skipped_urls"]),
            "remaining": len(self.progress_data["remaining_urls"]),
            "progress_percent": self.get_progress_percent(),
            "created_at": self.progress_data["created_at"],
            "updated_at": self.progress_data["updated_at"],
        }

    def is_complete(self) -> bool:
        """
        Check if all URLs have been processed.

        Returns:
            True if no remaining URLs
        """
        return len(self.progress_data["remaining_urls"]) == 0

    def cleanup(self):
        """Delete progress file."""
        try:
            if self.progress_file.exists():
                self.progress_file.unlink()
                logger.info(f"🗑️  Cleaned up progress file: {self.progress_file}")
        except Exception as e:
            logger.error(f"Failed to cleanup progress file: {e}")

    @staticmethod
    def list_sessions() -> List[str]:
        """
        List all available progress sessions.

        Returns:
            List of session names
        """
        try:
            progress_files = list(config.data_dir.glob(".progress_*.json"))
            sessions = []

            for file in progress_files:
                # Extract session name from filename
                session_name = file.stem.replace(".progress_", "")
                sessions.append(session_name)

            return sorted(sessions, reverse=True)  # Most recent first
        except Exception as e:
            logger.error(f"Failed to list sessions: {e}")
            return []

    @staticmethod
    def load_session(session_name: str) -> Optional["ProgressTracker"]:
        """
        Load an existing progress session.

        Args:
            session_name: Name of session to load

        Returns:
            ProgressTracker instance or None if not found
        """
        tracker = ProgressTracker(session_name=session_name)
        if tracker.progress_file.exists():
            return tracker
        return None
