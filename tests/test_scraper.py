"""Tests for the scraping run: keeping data, stopping and resuming."""

import importlib
import json
import stat
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from linkedin_spider.models import Profile

# core/__init__.py replaces these submodule names with instances
scraper_module = importlib.import_module("linkedin_spider.core.scraper")
parser_module = importlib.import_module("linkedin_spider.core.profile_parser")
progress_module = importlib.import_module("linkedin_spider.utils.progress")

LinkedInScraper = scraper_module.LinkedInScraper
ProgressTracker = progress_module.ProgressTracker
SessionBlocked = parser_module.SessionBlocked


def urls(count):
    return [f"https://www.linkedin.com/in/u{i}" for i in range(count)]


def ok(url):
    return Profile(url=url, name=url.rsplit("/", 1)[-1])


def progress_file(session):
    return Path("data") / f".progress_{session}.json"


@pytest.fixture
def browser(monkeypatch):
    fake = MagicMock()
    fake.login_linkedin.return_value = True
    monkeypatch.setattr(scraper_module, "browser", fake)
    return fake


@pytest.fixture
def parse(monkeypatch, browser):
    """Replace parse_profile. Tests set .side_effect to script each URL's outcome."""
    fake = MagicMock(side_effect=ok)
    monkeypatch.setattr(scraper_module.profile_parser, "parse_profile", fake)
    return fake


class TestKeepingData:
    def test_interrupt_returns_what_was_scraped(self, parse):
        all_urls = urls(4)
        parse.side_effect = [ok(all_urls[0]), ok(all_urls[1]), KeyboardInterrupt]

        profiles = LinkedInScraper().scrape_profiles(all_urls, session_name="s")

        assert [p.url for p in profiles] == all_urls[:2]

    def test_scraped_profiles_are_saved_as_they_arrive(self, parse):
        all_urls = urls(3)
        parse.side_effect = [ok(all_urls[0]), KeyboardInterrupt]

        LinkedInScraper().scrape_profiles(all_urls, session_name="s")

        saved = json.loads(progress_file("s").read_text())
        assert [p["url"] for p in saved["profiles"]] == all_urls[:1]
        assert saved["remaining_urls"] == all_urls[1:]

    def test_resume_returns_earlier_profiles_too(self, parse):
        all_urls = urls(3)
        parse.side_effect = [ok(all_urls[0]), KeyboardInterrupt]
        LinkedInScraper().scrape_profiles(all_urls, session_name="s")

        parse.side_effect = ok
        scraper = LinkedInScraper()
        profiles = scraper.scrape_profiles(resume_session="s")

        assert [p.url for p in profiles] == all_urls
        assert len(scraper.get_profiles()) == 3

    def test_resume_with_nothing_left_still_returns_profiles(self, parse, browser):
        all_urls = urls(2)
        LinkedInScraper().scrape_profiles(all_urls, session_name="s")
        browser.reset_mock()
        parse.reset_mock()

        profiles = LinkedInScraper().scrape_profiles(resume_session="s")

        assert [p.url for p in profiles] == all_urls
        parse.assert_not_called()
        browser.start.assert_not_called()

    def test_progress_file_survives_until_results_are_exported(self, parse):
        scraper = LinkedInScraper()
        scraper.scrape_profiles(urls(1), session_name="s")

        assert progress_file("s").exists()

        scraper.finish_session()

        assert not progress_file("s").exists()

    def test_failures_keep_the_progress_file(self, parse):
        parse.side_effect = None
        parse.return_value = None
        scraper = LinkedInScraper()
        scraper.scrape_profiles(urls(1), session_name="s")

        scraper.finish_session()

        assert progress_file("s").exists()

    def test_unfinished_session_keeps_the_progress_file(self, parse):
        parse.side_effect = KeyboardInterrupt
        scraper = LinkedInScraper()
        scraper.scrape_profiles(urls(2), session_name="s")

        scraper.finish_session()

        assert progress_file("s").exists()

    def test_progress_file_is_owner_only(self, parse):
        LinkedInScraper().scrape_profiles(urls(1), session_name="s")

        assert stat.S_IMODE(progress_file("s").stat().st_mode) == 0o600

    def test_save_leaves_no_temp_files(self, parse):
        LinkedInScraper().scrape_profiles(urls(2), session_name="s")

        assert [p.name for p in Path("data").iterdir()] == [".progress_s.json"]

    def test_corrupt_progress_file_is_not_silently_replaced(self, parse):
        file = progress_file("s")
        file.parent.mkdir()
        file.write_text('{"completed_urls": ["half a fi')

        with pytest.raises(ValueError, match="Can't read progress file"):
            LinkedInScraper().scrape_profiles(urls(1), session_name="s")

        assert file.read_text() == '{"completed_urls": ["half a fi'

    def test_progress_files_from_older_versions_load(self):
        file = progress_file("old")
        file.parent.mkdir()
        file.write_text(
            json.dumps(
                {
                    "session_name": "old",
                    "created_at": "2025-01-01T00:00:00",
                    "updated_at": "2025-01-01T00:00:00",
                    "total_urls": 1,
                    "completed_urls": [],
                    "failed_urls": [],
                    "skipped_urls": [],
                    "remaining_urls": urls(1),
                    "stats": {"total_scraped": 0},
                }
            )
        )

        assert ProgressTracker.load_session("old").get_profiles() == []


class TestStopping:
    def test_login_wall_stops_the_run(self, parse):
        all_urls = urls(5)
        parse.side_effect = [ok(all_urls[0]), SessionBlocked("authwall")]

        profiles = LinkedInScraper().scrape_profiles(all_urls, session_name="s")

        assert parse.call_count == 2
        assert [p.url for p in profiles] == all_urls[:1]

        # The blocked URL isn't the profile's fault, so it stays in the queue
        tracker = ProgressTracker.load_session("s")
        assert tracker.get_remaining() == all_urls[1:]
        assert tracker.get_stats()["failed"] == 0

    def test_repeated_failures_stop_the_run(self, parse):
        parse.side_effect = None
        parse.return_value = None

        LinkedInScraper().scrape_profiles(urls(20), session_name="s")

        assert parse.call_count == scraper_module.MAX_CONSECUTIVE_FAILURES
        assert len(ProgressTracker.load_session("s").get_remaining()) == 15

    def test_scattered_failures_dont_stop_the_run(self, parse):
        limit = scraper_module.MAX_CONSECUTIVE_FAILURES
        all_urls = urls(2 * limit)
        outcomes = (
            [None] * (limit - 1) + [ok(all_urls[limit - 1])] + [None] * (limit - 1)
        )
        outcomes.append(ok(all_urls[-1]))
        parse.side_effect = outcomes

        LinkedInScraper().scrape_profiles(all_urls, session_name="s")

        assert parse.call_count == len(all_urls)

    def test_failed_login_doesnt_scrape_logged_out(self, parse, browser, monkeypatch):
        monkeypatch.setenv("LINKEDIN_EMAIL", "a@example.com")
        monkeypatch.setenv("LINKEDIN_PASSWORD", "pw")
        browser.login_linkedin.return_value = False

        assert LinkedInScraper().scrape_profiles(urls(2), session_name="s") == []

        parse.assert_not_called()
        assert len(ProgressTracker.load_session("s").get_remaining()) == 2

    def test_no_credentials_continues_logged_out(self, parse, browser):
        browser.login_linkedin.return_value = False

        assert len(LinkedInScraper().scrape_profiles(urls(2), session_name="s")) == 2


class TestSessions:
    def test_resume_retries_failed_urls(self, parse):
        all_urls = urls(2)
        parse.side_effect = [None, ok(all_urls[1])]
        LinkedInScraper().scrape_profiles(all_urls, session_name="s")

        parse.side_effect = ok
        profiles = LinkedInScraper().scrape_profiles(resume_session="s")

        assert {p.url for p in profiles} == set(all_urls)
        assert ProgressTracker.load_session("s").get_stats()["failed"] == 0

    def test_reusing_a_session_skips_completed_urls(self, parse):
        all_urls = urls(3)
        LinkedInScraper().scrape_profiles(all_urls[:2], session_name="s")
        parse.reset_mock()

        LinkedInScraper().scrape_profiles(all_urls, session_name="s")

        assert [c.args[0] for c in parse.call_args_list] == all_urls[2:]
        assert ProgressTracker.load_session("s").get_stats()["total_urls"] == 3

    def test_reusing_a_session_returns_its_earlier_profiles(self, parse):
        all_urls = urls(2)
        LinkedInScraper().scrape_profiles(all_urls[:1], session_name="s")

        profiles = LinkedInScraper().scrape_profiles(all_urls, session_name="s")

        assert [p.url for p in profiles] == all_urls

    def test_reusing_a_finished_session_opens_no_browser(self, parse, browser):
        all_urls = urls(1)
        LinkedInScraper().scrape_profiles(all_urls, session_name="s")
        browser.reset_mock()

        profiles = LinkedInScraper().scrape_profiles(all_urls, session_name="s")

        assert [p.url for p in profiles] == all_urls
        browser.start.assert_not_called()

    def test_dry_run_writes_nothing_and_opens_no_browser(self, parse, browser):
        result = LinkedInScraper().scrape_profiles(
            urls(2), dry_run=True, session_name="s"
        )

        assert result == []
        assert not Path("data").exists()
        browser.start.assert_not_called()
        parse.assert_not_called()

    def test_dry_run_resume_changes_nothing(self, parse):
        all_urls = urls(2)
        parse.side_effect = [None, KeyboardInterrupt]
        LinkedInScraper().scrape_profiles(all_urls, session_name="s")
        before = progress_file("s").read_text()

        LinkedInScraper().scrape_profiles(resume_session="s", dry_run=True)

        assert progress_file("s").read_text() == before

    def test_urls_are_cleaned_before_scraping(self, parse):
        LinkedInScraper().scrape_profiles(
            [
                "https://es.linkedin.com/in/a/",
                "https://www.linkedin.com/in/a",
                "https://evil.example/in/b",
            ],
            session_name="s",
        )

        assert [c.args[0] for c in parse.call_args_list] == [
            "https://www.linkedin.com/in/a"
        ]

    def test_search_results_stay_in_order_without_duplicates(
        self, browser, monkeypatch
    ):
        search = MagicMock(
            return_value=[
                "https://www.linkedin.com/in/b",
                "https://es.linkedin.com/in/b",
                "https://www.linkedin.com/in/a",
            ]
        )
        monkeypatch.setattr(scraper_module.google_scraper, "search", search)

        assert LinkedInScraper().search_profiles(["x"]) == [
            "https://www.linkedin.com/in/b",
            "https://www.linkedin.com/in/a",
        ]


class TestConnecting:
    @pytest.fixture
    def connect(self, monkeypatch, browser):
        fake = MagicMock(return_value="sent")
        monkeypatch.setattr(scraper_module.profile_parser, "connect_to_profile", fake)
        return fake

    def test_confirm_is_required(self, connect):
        with pytest.raises(TypeError):
            LinkedInScraper().connect_to_profiles(urls(1))

    def test_stops_at_the_limit(self, connect):
        limit = scraper_module.MAX_CONNECTS_PER_RUN

        counts = LinkedInScraper().connect_to_profiles(urls(limit + 5), lambda *_: True)

        assert connect.call_count == limit
        assert counts["sent"] == limit

    def test_declining_doesnt_use_up_the_limit(self, connect):
        limit = scraper_module.MAX_CONNECTS_PER_RUN
        connect.side_effect = ["declined", "skipped"] + ["sent"] * limit

        counts = LinkedInScraper().connect_to_profiles(urls(limit + 5), lambda *_: True)

        assert counts == {"sent": limit, "declined": 1, "skipped": 1}

    def test_passes_confirm_through(self, connect):
        confirm = MagicMock()

        LinkedInScraper().connect_to_profiles(urls(1), confirm)

        connect.assert_called_once_with(urls(1)[0], confirm)

    def test_login_wall_stops_the_run(self, connect):
        connect.side_effect = ["sent", SessionBlocked("authwall")]

        counts = LinkedInScraper().connect_to_profiles(urls(5), lambda *_: True)

        assert connect.call_count == 2
        assert counts["sent"] == 1

    def test_interrupt_keeps_the_counts(self, connect):
        connect.side_effect = ["sent", KeyboardInterrupt]

        counts = LinkedInScraper().connect_to_profiles(urls(5), lambda *_: True)

        assert counts["sent"] == 1

    def test_failed_login_sends_nothing(self, connect, browser):
        browser.login_linkedin.return_value = False

        counts = LinkedInScraper().connect_to_profiles(urls(2), lambda *_: True)

        connect.assert_not_called()
        assert counts["sent"] == 0
