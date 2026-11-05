"""Profile parser for extracting LinkedIn profile data."""

import time
from typing import Optional
from urllib.parse import urlparse

from bs4 import BeautifulSoup

from linkedin_spider.core.browser import browser
from linkedin_spider.models import Profile, is_profile_url
from linkedin_spider.utils import config, logger

# Where LinkedIn sends you instead of a profile when it wants you to log in or
# prove something. Compared against the path, so /in/login-expert is unaffected.
BLOCKED_PATHS = ("/authwall", "/login", "/uas/login", "/checkpoint", "/signup")


class SessionBlocked(Exception):
    """LinkedIn showed a login wall or a challenge instead of the profile."""


class ProfileParser:
    """Parses LinkedIn profile pages to extract data."""

    def _raise_if_blocked(self):
        """Stop if the browser ended up on a login wall or challenge page."""
        path = urlparse(browser.current_url).path
        if path.startswith(BLOCKED_PATHS):
            raise SessionBlocked(f"LinkedIn redirected to {path}")

    def parse_profile(self, url: str) -> Optional[Profile]:
        """
        Parse a LinkedIn profile from URL.

        Args:
            url: LinkedIn profile URL

        Returns:
            Profile object if successful, None otherwise

        Raises:
            SessionBlocked: If LinkedIn showed a login wall or challenge
        """
        if not is_profile_url(url):
            logger.error(f"Not a LinkedIn profile URL, not opening it: {url}")
            return None

        try:
            logger.info(f"Parsing profile: {url}")

            # Navigate to profile
            browser.get(url)
            self._raise_if_blocked()

            # Random delay to mimic human behavior
            browser.random_delay()

            # Scroll to load all content
            browser.scroll_page(config.scroll_duration)
            self._raise_if_blocked()

            # Get page source and parse with BeautifulSoup
            html = browser.page_source
            soup = BeautifulSoup(html, "lxml")

            # Extract profile data
            profile_data = self._extract_profile_data(soup, url)

            if not profile_data["name"]:
                logger.warning(f"No profile data found on page: {url}")
                return None

            # Create Profile object
            profile = Profile(
                url=url,
                name=profile_data.get("name", ""),
                title=profile_data.get("title", ""),
                company=profile_data.get("company", ""),
                location=profile_data.get("location", ""),
                about=profile_data.get("about", ""),
                followers=profile_data.get("followers", 0),
            )

            logger.info(f"✅ Parsed: {profile.name}")
            return profile

        except SessionBlocked:
            raise
        except Exception as e:
            logger.error(f"Failed to parse {url}: {e}")
            return None

    def _extract_profile_data(self, soup: BeautifulSoup, url: str) -> dict:
        """
        Extract profile data from BeautifulSoup object.

        Args:
            soup: BeautifulSoup object of profile page
            url: Profile URL

        Returns:
            Dictionary with profile data
        """
        data = {
            "name": "",
            "title": "",
            "company": "",
            "location": "",
            "about": "",
            "followers": 0,
        }

        # Extract name
        try:
            name_elem = soup.find("h1")
            if name_elem:
                data["name"] = name_elem.get_text(strip=True)
        except Exception as e:
            logger.debug(f"Error extracting name: {e}")

        # Extract title
        try:
            title_elem = soup.find("div", class_="text-body-medium break-words")
            if title_elem:
                data["title"] = title_elem.get_text(strip=True)
        except Exception as e:
            logger.debug(f"Error extracting title: {e}")

        # Extract company
        try:
            company_elem = soup.find(
                "h2",
                class_="pv-text-details__right-panel-item-text hoverable-link-text break-words text-body-small inline",
            )

            if company_elem:
                data["company"] = company_elem.get_text(strip=True)
        except Exception as e:
            logger.debug(f"Error extracting company: {e}")

        # Extract location
        try:
            location_elem = soup.find(
                "span", class_="text-body-small inline t-black--light break-words"
            )
            if location_elem:
                data["location"] = location_elem.get_text(strip=True)
        except Exception as e:
            logger.debug(f"Error extracting location: {e}")

        # Extract about section
        try:
            about_elem = soup.find(
                "div",
                class_="pv-shared-text-with-see-more t-14 t-normal t-black display-flex align-items-center",
            )
            if about_elem:
                about_span = about_elem.find("span")
                if about_span:
                    data["about"] = about_span.get_text(strip=True)
        except Exception as e:
            logger.debug(f"Error extracting about: {e}")

        # Extract followers count
        try:
            followers_elem = soup.find("p", class_="pvs-header__subtitle text-body-small")
            if followers_elem:
                followers_span = followers_elem.find("span")
                if followers_span:
                    followers_text = followers_span.get_text(strip=True)
                    # Extract number from text like "1,234 followers"
                    followers_text = followers_text.replace(" followers", "").replace(",", "")
                    try:
                        data["followers"] = int(followers_text)
                    except ValueError:
                        pass
        except Exception as e:
            logger.debug(f"Error extracting followers: {e}")

        return data

    def connect_to_profile(self, url: str) -> bool:
        """
        Send connection request to a LinkedIn profile.

        Args:
            url: LinkedIn profile URL

        Returns:
            True if connection sent, False otherwise
        """
        try:
            logger.info(f"Connecting to profile: {url}")

            # Navigate to profile
            browser.get(url)
            time.sleep(3)

            # Try to find and click connect button
            try:
                # Look for "Connect" button
                from selenium.webdriver.common.by import By

                connect_button = browser.driver.find_element(
                    By.XPATH, "//button[contains(., 'Connect')]"
                )
                connect_button.click()
                time.sleep(2)

                # Click "Send" on the dialog
                send_button = browser.driver.find_element(
                    By.XPATH, "//button[@aria-label='Send now']"
                )
                send_button.click()

                logger.info(f"✅ Connection request sent to {url}")
                browser.random_delay()
                return True

            except Exception as e:
                logger.warning(f"Could not send connection request: {e}")
                return False

        except Exception as e:
            logger.error(f"Failed to connect to {url}: {e}")
            return False


# Global profile parser instance
profile_parser = ProfileParser()
