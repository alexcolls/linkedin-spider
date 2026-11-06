"""Tests for the command line and its output of untrusted text."""

import importlib
import json
import os
import subprocess
import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from typer.testing import CliRunner

from linkedin_spider import __version__
from linkedin_spider.cli import commands, display
from linkedin_spider.cli.main import app
from linkedin_spider.models import Profile
from linkedin_spider.utils.export import load_urls

# core/__init__.py and cli/__init__.py replace these submodule names with instances
scraper_module = importlib.import_module("linkedin_spider.core.scraper")
main_module = importlib.import_module("linkedin_spider.cli.main")

runner = CliRunner()
URL = "https://www.linkedin.com/in/ana"


def write_urls(path="urls.txt"):
    Path(path).write_text(URL + "\n")
    return path


@pytest.fixture
def scrape_profiles(monkeypatch):
    fake = MagicMock(return_value=[Profile(url=URL, name="Ana")])
    monkeypatch.setattr(main_module.scraper, "scrape_profiles", fake)
    return fake


class TestVersion:
    def test_prints_the_package_version(self):
        result = runner.invoke(app, ["version"])

        assert result.exit_code == 0
        assert __version__ in result.output

    def test_creates_nothing(self):
        runner.invoke(app, ["version"])

        assert list(Path(".").iterdir()) == []


def test_importing_models_needs_no_browser_and_creates_nothing(tmp_path):
    src = str(Path(__file__).parent.parent / "src")
    code = "import sys, linkedin_spider.models; assert 'selenium' not in sys.modules"

    subprocess.run(
        [sys.executable, "-c", code],
        check=True,
        cwd=tmp_path,
        env={**os.environ, "PYTHONPATH": src, "PYTHONDONTWRITEBYTECODE": "1"},
    )

    assert list(tmp_path.iterdir()) == []


class TestScrape:
    def test_bad_format_fails_before_scraping(self, scrape_profiles):
        result = runner.invoke(
            app, ["scrape", "--urls", write_urls(), "--format", "pdf"]
        )

        assert result.exit_code == 2
        scrape_profiles.assert_not_called()

    def test_missing_openpyxl_fails_before_scraping(self, scrape_profiles, monkeypatch):
        monkeypatch.setitem(sys.modules, "openpyxl", None)

        result = runner.invoke(
            app, ["scrape", "--urls", write_urls(), "--format", "excel"]
        )

        assert result.exit_code == 1
        scrape_profiles.assert_not_called()

    def test_exports_then_finishes_the_session(self, scrape_profiles, monkeypatch):
        finish = MagicMock()
        monkeypatch.setattr(main_module.scraper, "finish_session", finish)

        result = runner.invoke(
            app, ["scrape", "--urls", write_urls(), "--format", "json"]
        )

        assert result.exit_code == 0
        assert len(list(Path("data").glob("profiles_*.json"))) == 1
        finish.assert_called_once()

    def test_failed_export_keeps_the_session(self, scrape_profiles, monkeypatch):
        finish = MagicMock()
        monkeypatch.setattr(main_module.scraper, "finish_session", finish)
        monkeypatch.setattr(
            main_module.exporter, "export", MagicMock(side_effect=OSError("disk full"))
        )

        result = runner.invoke(
            app, ["scrape", "--urls", write_urls(), "--format", "csv"]
        )

        assert result.exit_code == 1
        finish.assert_not_called()

    def test_format_defaults_to_config(self, scrape_profiles, monkeypatch):
        monkeypatch.setenv("DEFAULT_EXPORT_FORMAT", "json")

        result = runner.invoke(app, ["scrape", "--urls", write_urls()])

        assert result.exit_code == 0
        assert len(list(Path("data").glob("profiles_*.json"))) == 1

    def test_default_url_file_is_in_the_data_dir(self, scrape_profiles, monkeypatch):
        monkeypatch.setenv("DATA_DIR", "custom")
        Path("custom").mkdir()
        write_urls("custom/profile_urls.txt")

        result = runner.invoke(app, ["scrape", "--dry-run"])

        assert result.exit_code == 0
        assert scrape_profiles.call_args.args[0] == [URL]

    def test_missing_url_file_fails(self, scrape_profiles):
        result = runner.invoke(app, ["scrape", "--urls", "nope.txt"])

        assert result.exit_code == 1
        scrape_profiles.assert_not_called()

    def test_error_text_with_brackets_is_reported(self, scrape_profiles):
        scrape_profiles.side_effect = RuntimeError("selenium said [/div]")

        result = runner.invoke(app, ["scrape", "--urls", write_urls()])

        assert result.exit_code == 1
        assert "[/div]" in result.output

    def test_debug_reaches_the_console(self, scrape_profiles):
        logger = main_module.logger
        level_before = logger.level
        handlers_before = [(h, h.level) for h in logger.handlers]
        try:
            runner.invoke(
                app, ["scrape", "--urls", write_urls(), "--debug", "--dry-run"]
            )

            assert logger.level == 10
            assert all(h.level == 10 for h in logger.handlers)
        finally:
            logger.setLevel(level_before)
            for handler, level in handlers_before:
                handler.setLevel(level)


class TestInterruptAndResume:
    """The whole journey through the real CLI, with only the browser replaced."""

    @pytest.fixture
    def parse(self, monkeypatch):
        browser = MagicMock()
        browser.login_linkedin.return_value = True
        monkeypatch.setattr(scraper_module, "browser", browser)
        monkeypatch.setattr(main_module, "scraper", scraper_module.LinkedInScraper())

        fake = MagicMock()
        monkeypatch.setattr(scraper_module.profile_parser, "parse_profile", fake)
        return fake

    @staticmethod
    def exported_names():
        newest = max(
            Path("data").glob("profiles_*.json"), key=lambda p: p.stat().st_mtime_ns
        )
        return [row["name"] for row in json.loads(newest.read_text("utf-8"))]

    def test_ctrl_c_exports_then_resume_exports_everything(self, parse, monkeypatch):
        urls = [f"https://www.linkedin.com/in/u{i}" for i in range(3)]
        Path("urls.txt").write_text("\n".join(urls))
        progress = Path("data/.progress_job.json")
        args = ["--format", "json", "--session", "job", "--output", "first"]

        # First run: one profile scraped, then Ctrl+C
        parse.side_effect = [Profile(url=urls[0], name="First"), KeyboardInterrupt]
        result = runner.invoke(app, ["scrape", "--urls", "urls.txt", *args])

        assert result.exit_code == 0
        assert [
            row["name"]
            for row in json.loads(next(Path("data").glob("first_*.json")).read_text())
        ] == ["First"]
        assert progress.exists()

        # Resume: fresh process state, the rest get scraped, the export has everyone
        monkeypatch.setattr(main_module, "scraper", scraper_module.LinkedInScraper())
        parse.side_effect = [
            Profile(url=urls[1], name="Second"),
            Profile(url=urls[2], name="Third"),
        ]
        result = runner.invoke(app, ["scrape", "--resume", "job", "--format", "json"])

        assert result.exit_code == 0
        assert self.exported_names() == ["First", "Second", "Third"]
        assert not progress.exists()


class TestSearch:
    def test_second_search_adds_to_the_url_file(self, monkeypatch):
        fake = MagicMock(return_value=["https://www.linkedin.com/in/one"])
        monkeypatch.setattr(main_module.scraper, "search_profiles", fake)

        runner.invoke(app, ["search", "x"])
        fake.return_value = ["https://www.linkedin.com/in/two"]
        result = runner.invoke(app, ["search", "y"])

        assert result.exit_code == 0
        assert load_urls(Path("data/profile_urls.txt")) == [
            "https://www.linkedin.com/in/one",
            "https://www.linkedin.com/in/two",
        ]


class TestSessionsCommand:
    def test_corrupt_session_is_reported_and_others_still_listed(self):
        data = Path("data")
        data.mkdir()
        (data / ".progress_bad.json").write_text("{not json")
        (data / ".progress_good.json").write_text(
            '{"session_name": "good", "created_at": "2025-01-01T00:00:00",'
            ' "updated_at": "2025-01-01T00:00:00", "total_urls": 0,'
            ' "completed_urls": [], "failed_urls": [], "skipped_urls": [],'
            ' "remaining_urls": []}'
        )

        result = runner.invoke(app, ["sessions"])

        assert result.exit_code == 0
        assert "good" in result.output
        assert "Can't read progress file" in result.output


class TestUntrustedText:
    NAME = "Bob [/x] [red]Smith"

    def test_profiles_table_shows_brackets_literally(self):
        with display.console.capture() as captured:
            display.show_profiles_table([Profile(url=URL, name=self.NAME)])

        assert self.NAME in captured.get()

    def test_url_list_shows_brackets_literally(self):
        with display.console.capture() as captured:
            display.show_urls_list(["https://www.linkedin.com/in/[/x]"])

        assert "[/x]" in captured.get().replace("\n", "")

    @pytest.mark.parametrize(
        "show", [display.success, display.error, display.warning, display.info]
    )
    def test_messages_show_brackets_literally(self, show):
        with display.console.capture() as captured:
            show(self.NAME)

        assert self.NAME in captured.get()

    def test_prompts_show_brackets_literally(self, monkeypatch):
        monkeypatch.setattr("builtins.input", lambda *_: "")

        with display.console.capture() as captured:
            assert display.confirm(self.NAME) is False

        output = captured.get()
        assert self.NAME in output
        assert "[y/N]" in output


class TestConnectCommand:
    def test_each_person_is_asked_and_the_default_is_no(self, monkeypatch):
        answers = []
        monkeypatch.setattr(
            commands.display,
            "confirm",
            lambda message, default=False: answers.append((message, default)) or False,
        )

        assert commands._confirm_connection("Ana", URL) is False
        assert answers == [(f"Send request to Ana ({URL})?", False)]
