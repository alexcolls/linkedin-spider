"""Tests for Profile data models."""

import pytest
from datetime import datetime

from linkedin_spider.models import Profile, ProfileCollection


class TestProfile:
    """Test Profile dataclass."""

    def test_profile_creation(self):
        """Test creating a basic profile."""
        profile = Profile(
            url="https://linkedin.com/in/johndoe",
            name="John Doe",
            title="Software Engineer",
            company="Tech Corp",
            location="San Francisco, CA",
        )

        assert profile.name == "John Doe"
        assert profile.title == "Software Engineer"
        assert profile.company == "Tech Corp"
        assert profile.location == "San Francisco, CA"
        assert profile.followers == 0

    def test_profile_url_normalization(self):
        """Test URL normalization."""
        profile = Profile(
            url="https://linkedin.com/in/johndoe/?param=value"
        )

        assert profile.url == "https://linkedin.com/in/johndoe"

    def test_profile_text_cleaning(self):
        """Test text field cleaning."""
        profile = Profile(
            url="https://linkedin.com/in/johndoe",
            name="  John   Doe  ",
            title="Software\\nEngineer",
        )

        assert profile.name == "John Doe"
        assert profile.title == "Software Engineer"

    def test_profile_to_dict(self):
        """Test profile serialization."""
        profile = Profile(
            url="https://linkedin.com/in/johndoe",
            name="John Doe",
        )

        data = profile.to_dict()

        assert isinstance(data, dict)
        assert data["name"] == "John Doe"
        assert data["url"] == "https://linkedin.com/in/johndoe"
        assert isinstance(data["scraped_at"], str)

    def test_profile_from_dict(self):
        """Test profile deserialization."""
        data = {
            "url": "https://linkedin.com/in/johndoe",
            "name": "John Doe",
            "title": "Software Engineer",
            "company": "Tech Corp",
            "location": "San Francisco",
            "about": "Experienced developer",
            "followers": 500,
            "scraped_at": "2025-01-12T10:00:00",
        }

        profile = Profile.from_dict(data)

        assert profile.name == "John Doe"
        assert profile.followers == 500
        assert isinstance(profile.scraped_at, datetime)


class TestProfileCollection:
    """Test ProfileCollection."""

    def test_collection_add(self):
        """Test adding profiles to collection."""
        collection = ProfileCollection()

        profile1 = Profile(url="https://linkedin.com/in/johndoe", name="John Doe")
        profile2 = Profile(url="https://linkedin.com/in/janedoe", name="Jane Doe")

        assert collection.add(profile1) is True
        assert collection.add(profile2) is True
        assert len(collection) == 2

    def test_collection_deduplication(self):
        """Test profile deduplication."""
        collection = ProfileCollection()

        profile1 = Profile(url="https://linkedin.com/in/johndoe", name="John Doe")
        profile2 = Profile(url="https://linkedin.com/in/johndoe", name="John Doe Updated")

        assert collection.add(profile1) is True
        assert collection.add(profile2) is False  # Duplicate URL
        assert len(collection) == 1

    def test_collection_get(self):
        """Test getting profile by URL."""
        collection = ProfileCollection()

        profile = Profile(url="https://linkedin.com/in/johndoe", name="John Doe")
        collection.add(profile)

        retrieved = collection.get("https://linkedin.com/in/johndoe")

        assert retrieved is not None
        assert retrieved.name == "John Doe"

    def test_collection_remove(self):
        """Test removing profile."""
        collection = ProfileCollection()

        profile = Profile(url="https://linkedin.com/in/johndoe", name="John Doe")
        collection.add(profile)

        assert collection.remove("https://linkedin.com/in/johndoe") is True
        assert len(collection) == 0
        assert collection.remove("https://linkedin.com/in/johndoe") is False

    def test_collection_iteration(self):
        """Test iterating over profiles."""
        collection = ProfileCollection()

        profile1 = Profile(url="https://linkedin.com/in/johndoe", name="John Doe")
        profile2 = Profile(url="https://linkedin.com/in/janedoe", name="Jane Doe")

        collection.add(profile1)
        collection.add(profile2)

        profiles = list(collection)

        assert len(profiles) == 2
        assert any(p.name == "John Doe" for p in profiles)
        assert any(p.name == "Jane Doe" for p in profiles)
