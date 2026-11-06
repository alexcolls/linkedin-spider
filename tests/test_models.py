"""Tests for Profile data models."""

from datetime import datetime

import pytest

from linkedin_spider.models import (
    Profile,
    ProfileCollection,
    is_profile_url,
    unique_profile_urls,
)


class TestProfileUrls:
    """Test profile URL validation and canonicalization."""

    @pytest.mark.parametrize(
        "url",
        [
            "https://www.linkedin.com/in/foo",
            "https://linkedin.com/in/foo/",
            "http://es.linkedin.com/in/foo?trk=x",
            "https://www.linkedin.com/in/foo/en",
        ],
    )
    def test_accepts_profile_urls(self, url):
        assert is_profile_url(url)

    @pytest.mark.parametrize(
        "url",
        [
            "",
            "foo",
            "https://evil.example/?u=linkedin.com/in/x",
            "https://linkedin.com.evil.example/in/x",
            "https://notlinkedin.com/in/x",
            "https://www.linkedin.com/company/acme",
            "https://www.linkedin.com/in/",
            "javascript:alert(1)//linkedin.com/in/x",
            "http://[bad",
        ],
    )
    def test_rejects_everything_else(self, url):
        assert not is_profile_url(url)

    def test_same_person_gets_one_url(self):
        urls = [
            "https://es.linkedin.com/in/foo/",
            "https://www.linkedin.com/in/foo?trk=x",
            "http://linkedin.com/in/foo/en",
        ]
        assert unique_profile_urls(urls) == ["https://www.linkedin.com/in/foo"]

    def test_keeps_order_and_drops_invalid(self):
        urls = [
            "https://www.linkedin.com/in/b",
            "https://evil.example/in/x",
            "https://www.linkedin.com/in/a",
        ]
        assert unique_profile_urls(urls) == [
            "https://www.linkedin.com/in/b",
            "https://www.linkedin.com/in/a",
        ]

    def test_profile_rejects_invalid_url(self):
        with pytest.raises(ValueError):
            Profile(url="foo")


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
        profile = Profile(url="https://linkedin.com/in/johndoe/?param=value")

        assert profile.url == "https://www.linkedin.com/in/johndoe"

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
        assert data["url"] == "https://www.linkedin.com/in/johndoe"
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

    def test_profile_from_dict_leaves_input_alone(self):
        """Test that deserializing doesn't change the caller's data."""
        data = {
            "url": "https://linkedin.com/in/johndoe",
            "scraped_at": "2025-01-12T10:00:00",
        }

        Profile.from_dict(data)

        assert data["scraped_at"] == "2025-01-12T10:00:00"


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
        profile2 = Profile(
            url="https://linkedin.com/in/johndoe", name="John Doe Updated"
        )

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

    def test_collection_lookup_normalizes(self):
        """Test that any form of a profile's URL finds it."""
        collection = ProfileCollection()
        collection.add(Profile(url="https://www.linkedin.com/in/johndoe", name="John"))

        assert "https://es.linkedin.com/in/johndoe/" in collection
        assert collection.get("https://es.linkedin.com/in/johndoe/").name == "John"
        assert collection.get("not a url") is None
        assert collection.remove("https://es.linkedin.com/in/johndoe/") is True
        assert len(collection) == 0

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
