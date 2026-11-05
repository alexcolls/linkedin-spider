"""Tests for reading profile pages and Google results, using fixture HTML."""

import importlib
from unittest.mock import MagicMock

import pytest
from bs4 import BeautifulSoup

from linkedin_spider.utils.logger import logger

# core/__init__.py replaces this submodule name with an instance
parser_module = importlib.import_module("linkedin_spider.core.profile_parser")
search_module = importlib.import_module("linkedin_spider.core.google_search")

SessionBlocked = parser_module.SessionBlocked
find_connect_button = parser_module.find_connect_button
parser = parser_module.profile_parser
search = search_module.google_scraper

URL = "https://www.linkedin.com/in/ana"

PROFILE_HTML = """
<main>
  <h1>Ana García</h1>
  <div class="text-body-medium break-words">Staff Engineer</div>
  <h2 class="pv-text-details__right-panel-item-text hoverable-link-text break-words text-body-small inline">Acme</h2>
  <span class="text-body-small inline t-black--light break-words">Madrid, Spain</span>
  <div class="pv-shared-text-with-see-more t-14 t-normal t-black display-flex align-items-center"><span>Builds things.</span></div>
  <p class="pvs-header__subtitle text-body-small"><span>1,234 followers</span></p>
</main>
"""


def fake_browser(page_source=PROFILE_HTML, current_url=URL):
    return MagicMock(page_source=page_source, current_url=current_url)


class TestExtractProfileData:
    def test_reads_every_field(self):
        data = parser._extract_profile_data(BeautifulSoup(PROFILE_HTML, "lxml"), URL)

        assert data == {
            "name": "Ana García",
            "title": "Staff Engineer",
            "company": "Acme",
            "location": "Madrid, Spain",
            "about": "Builds things.",
            "followers": 1234,
        }

    def test_location_is_not_mistaken_for_company(self):
        html = '<span class="text-body-small inline t-black--light break-words">Madrid</span>'

        data = parser._extract_profile_data(BeautifulSoup(html, "lxml"), URL)

        assert data["company"] == ""
        assert data["location"] == "Madrid"


class TestParseProfile:
    def test_returns_profile(self, monkeypatch):
        monkeypatch.setattr(parser_module, "browser", fake_browser())

        profile = parser.parse_profile(URL)

        assert profile.name == "Ana García"
        assert profile.url == URL

    @pytest.mark.parametrize(
        "blocked_url",
        [
            "https://www.linkedin.com/authwall?trk=x",
            "https://www.linkedin.com/login",
            "https://www.linkedin.com/uas/login",
            "https://www.linkedin.com/checkpoint/challenge/abc",
            "https://www.linkedin.com/signup/cold-join",
        ],
    )
    def test_login_wall_raises_instead_of_saving_a_profile(
        self, monkeypatch, blocked_url
    ):
        html = "<h1>Join LinkedIn</h1>"
        monkeypatch.setattr(parser_module, "browser", fake_browser(html, blocked_url))

        with pytest.raises(SessionBlocked):
            parser.parse_profile(URL)

    def test_profile_whose_slug_looks_blocked_is_fine(self, monkeypatch):
        url = "https://www.linkedin.com/in/login"
        monkeypatch.setattr(parser_module, "browser", fake_browser(current_url=url))

        assert parser.parse_profile(url).name == "Ana García"

    def test_page_without_a_name_is_a_failure(self, monkeypatch):
        monkeypatch.setattr(parser_module, "browser", fake_browser("<html></html>"))

        assert parser.parse_profile(URL) is None

    def test_browser_errors_are_a_failure(self, monkeypatch):
        browser = fake_browser()
        browser.get.side_effect = RuntimeError("chrome crashed [/x]")
        monkeypatch.setattr(parser_module, "browser", browser)

        assert parser.parse_profile(URL) is None

    def test_non_profile_url_is_never_opened(self, monkeypatch):
        browser = fake_browser()
        monkeypatch.setattr(parser_module, "browser", browser)

        assert parser.parse_profile("https://evil.example/in/x") is None
        browser.get.assert_not_called()


def button(label):
    element = MagicMock()
    element.get_attribute.return_value = label
    return element


class TestFindConnectButton:
    def test_picks_the_button_naming_this_person(self):
        other = button("Invite Bob Smith to connect")
        hers = button("Invite Ana García to connect")

        assert find_connect_button([other, hers], "Ana García") is hers

    @pytest.mark.parametrize(
        "labels",
        [
            [],
            ["Invite Bob Smith to connect"],
            ["Connections", "Message Ana García"],
            ["Invite Ana García to connect", "Invite Ana García to connect"],
        ],
    )
    def test_no_clear_match_means_no_button(self, labels):
        assert find_connect_button([button(x) for x in labels], "Ana García") is None

    def test_empty_name_matches_nothing(self):
        assert find_connect_button([button("Invite  to connect")], "") is None


class TestConnectToProfile:
    @pytest.fixture
    def page(self, monkeypatch):
        """A profile page with an invite button and a send button."""
        browser = fake_browser()
        driver = browser.driver
        driver.find_element.return_value.text = "Ana García"

        self.invite = button("Invite Ana García to connect")
        self.send = button("Send now")
        driver.find_elements.side_effect = lambda by, selector: (
            [self.send] if "dialog" in selector else [self.invite]
        )

        monkeypatch.setattr(parser_module, "browser", browser)
        monkeypatch.setattr(parser_module.time, "sleep", lambda _: None)
        return browser

    def test_sends_after_confirmation(self, page):
        confirm = MagicMock(return_value=True)

        assert parser.connect_to_profile(URL, confirm) == "sent"

        confirm.assert_called_once_with("Ana García", URL)
        self.invite.click.assert_called_once()
        self.send.click.assert_called_once()

    def test_declining_clicks_nothing(self, page):
        assert parser.connect_to_profile(URL, lambda *_: False) == "declined"

        self.invite.click.assert_not_called()
        self.send.click.assert_not_called()

    def test_someone_elses_button_is_never_clicked(self, page):
        confirm = MagicMock(return_value=True)
        page.driver.find_element.return_value.text = "Bob Smith"

        assert parser.connect_to_profile(URL, confirm) == "skipped"

        confirm.assert_not_called()
        self.invite.click.assert_not_called()

    def test_ambiguous_send_button_is_not_clicked(self, page):
        page.driver.find_elements.side_effect = lambda by, selector: (
            [self.send, self.send] if "dialog" in selector else [self.invite]
        )

        assert parser.connect_to_profile(URL, lambda *_: True) == "skipped"

        self.send.click.assert_not_called()

    def test_login_wall_raises(self, page):
        page.current_url = "https://www.linkedin.com/authwall"

        with pytest.raises(SessionBlocked):
            parser.connect_to_profile(URL, lambda *_: True)

    def test_non_profile_url_is_never_opened(self, page):
        assert (
            parser.connect_to_profile("https://evil.example/", lambda *_: True)
            == "skipped"
        )

        page.get.assert_not_called()


class TestGoogleSearch:
    def test_word_captcha_in_results_is_not_a_captcha(self, monkeypatch):
        browser = MagicMock()
        browser.driver.current_url = "https://www.google.com/search?q=captcha+engineer"
        browser.driver.page_source = "<html>CAPTCHA engineer, unusual traffic</html>"
        browser.driver.find_elements.return_value = []
        monkeypatch.setattr(search_module, "browser", browser)

        assert search._detect_captcha() is False

    def test_block_page_is_a_captcha(self, monkeypatch):
        browser = MagicMock()
        browser.driver.current_url = "https://www.google.com/sorry/index?continue=x"
        monkeypatch.setattr(search_module, "browser", browser)

        assert search._detect_captcha() is True

    def test_recaptcha_iframe_is_a_captcha(self, monkeypatch):
        browser = MagicMock()
        browser.driver.current_url = "https://www.google.com/search?q=x"
        browser.driver.find_elements.return_value = [MagicMock()]
        monkeypatch.setattr(search_module, "browser", browser)

        assert search._detect_captcha() is True

    def test_headless_doesnt_wait_for_a_captcha(self, monkeypatch):
        monkeypatch.setenv("HEADLESS", "true")
        sleep = MagicMock()
        monkeypatch.setattr(search_module.time, "sleep", sleep)

        search._wait_for_captcha_resolution()

        sleep.assert_not_called()

    def test_results_keep_only_linkedin_profiles(self, monkeypatch):
        def link(href):
            element = MagicMock()
            element.get_attribute.return_value = href
            return element

        browser = MagicMock()
        browser.driver.current_url = "https://www.google.com/search?q=x"
        browser.driver.find_elements.side_effect = lambda by, selector: (
            []
            if "recaptcha" in selector
            else [
                link("https://es.linkedin.com/in/ana"),
                link("https://evil.example/?u=linkedin.com/in/x"),
                link("https://www.google.com/search?q=site:linkedin.com/in/"),
            ]
        )
        monkeypatch.setattr(search_module, "browser", browser)

        assert search._scrape_current_page() == ["https://es.linkedin.com/in/ana"]


def test_logging_bracket_text_doesnt_raise():
    logger.error("Failed: selenium said [/div] boom")
