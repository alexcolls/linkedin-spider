"""Data models for LinkedIn Spider."""

from linkedin_spider.models.profile import (
    Profile,
    ProfileCollection,
    is_profile_url,
    normalize_profile_url,
    unique_profile_urls,
)

__all__ = [
    "Profile",
    "ProfileCollection",
    "is_profile_url",
    "normalize_profile_url",
    "unique_profile_urls",
]
