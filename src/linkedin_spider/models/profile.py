"""Data models for LinkedIn profiles."""

from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Dict, List, Optional
from urllib.parse import urlparse


@dataclass
class Profile:
    """Represents a LinkedIn profile."""

    url: str
    name: str = ""
    title: str = ""
    company: str = ""
    location: str = ""
    about: str = ""
    followers: int = 0
    scraped_at: datetime = field(default_factory=datetime.now)

    def __post_init__(self):
        """Validate and normalize data after initialization."""
        # Validate URL
        if not self.url:
            raise ValueError("Profile URL cannot be empty")

        # Normalize URL
        self.url = self._normalize_url(self.url)

        # Clean text fields
        self.name = self._clean_text(self.name)
        self.title = self._clean_text(self.title)
        self.company = self._clean_text(self.company)
        self.location = self._clean_text(self.location)
        self.about = self._clean_text(self.about)

        # Ensure followers is non-negative
        if self.followers < 0:
            self.followers = 0

    @staticmethod
    def _normalize_url(url: str) -> str:
        """
        Normalize LinkedIn profile URL.

        Args:
            url: Raw URL

        Returns:
            Normalized URL
        """
        # Remove query parameters and fragments
        parsed = urlparse(url)
        clean_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"

        # Remove trailing slash
        clean_url = clean_url.rstrip("/")

        return clean_url

    @staticmethod
    def _clean_text(text: str) -> str:
        """
        Clean and normalize text.

        Args:
            text: Raw text

        Returns:
            Cleaned text
        """
        if not text:
            return ""

        # Remove excess whitespace
        cleaned = " ".join(text.split())

        # Remove common artifacts
        cleaned = cleaned.replace("\\n", " ")
        cleaned = cleaned.replace("\\t", " ")

        return cleaned.strip()

    def to_dict(self) -> Dict:
        """
        Convert profile to dictionary.

        Returns:
            Dictionary representation
        """
        data = asdict(self)
        # Convert datetime to ISO format string
        data["scraped_at"] = self.scraped_at.isoformat()
        return data

    @classmethod
    def from_dict(cls, data: Dict) -> "Profile":
        """
        Create profile from dictionary.

        Args:
            data: Dictionary with profile data

        Returns:
            Profile instance
        """
        # Parse datetime if it's a string
        if isinstance(data.get("scraped_at"), str):
            data["scraped_at"] = datetime.fromisoformat(data["scraped_at"])

        return cls(**data)

    def __hash__(self) -> int:
        """Hash profile by URL for deduplication."""
        return hash(self.url)

    def __eq__(self, other) -> bool:
        """Compare profiles by URL."""
        if not isinstance(other, Profile):
            return False
        return self.url == other.url


class ProfileCollection:
    """Manages a collection of profiles with deduplication."""

    def __init__(self):
        """Initialize empty profile collection."""
        self._profiles: Dict[str, Profile] = {}

    def add(self, profile: Profile) -> bool:
        """
        Add profile to collection.

        Args:
            profile: Profile to add

        Returns:
            True if profile was added, False if it already existed
        """
        if profile.url in self._profiles:
            return False

        self._profiles[profile.url] = profile
        return True

    def add_many(self, profiles: List[Profile]) -> int:
        """
        Add multiple profiles to collection.

        Args:
            profiles: List of profiles to add

        Returns:
            Number of profiles added (excluding duplicates)
        """
        added = 0
        for profile in profiles:
            if self.add(profile):
                added += 1
        return added

    def get(self, url: str) -> Optional[Profile]:
        """
        Get profile by URL.

        Args:
            url: Profile URL

        Returns:
            Profile if found, None otherwise
        """
        return self._profiles.get(url)

    def remove(self, url: str) -> bool:
        """
        Remove profile by URL.

        Args:
            url: Profile URL

        Returns:
            True if profile was removed, False if not found
        """
        if url in self._profiles:
            del self._profiles[url]
            return True
        return False

    def get_all(self) -> List[Profile]:
        """
        Get all profiles.

        Returns:
            List of all profiles
        """
        return list(self._profiles.values())

    def clear(self):
        """Clear all profiles."""
        self._profiles.clear()

    def __len__(self) -> int:
        """Get number of profiles."""
        return len(self._profiles)

    def __iter__(self):
        """Iterate over profiles."""
        return iter(self._profiles.values())

    def __contains__(self, url: str) -> bool:
        """Check if URL exists in collection."""
        return url in self._profiles
