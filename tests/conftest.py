"""Pytest configuration and fixtures."""

import pytest
from pathlib import Path

from linkedin_spider.models import Profile


@pytest.fixture
def sample_profile():
    """Create a sample profile for testing."""
    return Profile(
        url="https://linkedin.com/in/johndoe",
        name="John Doe",
        title="Software Engineer",
        company="Tech Corp",
        location="San Francisco, CA",
        about="Experienced software engineer",
        followers=500,
    )


@pytest.fixture
def sample_profiles():
    """Create multiple sample profiles for testing."""
    return [
        Profile(
            url="https://linkedin.com/in/johndoe",
            name="John Doe",
            title="Software Engineer",
        ),
        Profile(
            url="https://linkedin.com/in/janedoe",
            name="Jane Doe",
            title="Data Scientist",
        ),
        Profile(
            url="https://linkedin.com/in/bobsmith",
            name="Bob Smith",
            title="Product Manager",
        ),
    ]


@pytest.fixture
def temp_data_dir(tmp_path):
    """Create a temporary data directory."""
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    return data_dir
