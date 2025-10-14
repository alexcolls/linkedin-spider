"""Main scraper orchestrator for LinkedIn Spider."""

from typing import List, Optional

from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn

from linkedin_spider.core.browser import browser
from linkedin_spider.core.google_search import google_scraper
from linkedin_spider.core.profile_parser import profile_parser
from linkedin_spider.models import Profile, ProfileCollection
from linkedin_spider.utils import config, logger, vpn_manager


class LinkedInScraper:
    """Main orchestrator for LinkedIn scraping operations."""

    def __init__(self):
        """Initialize LinkedIn scraper."""
        self.collection = ProfileCollection()
        self.profile_urls: List[str] = []

    def search_profiles(
        self, keywords: List[str], max_pages: Optional[int] = None
    ) -> List[str]:
        """
        Search for LinkedIn profiles using Google Search.

        Args:
            keywords: List of keywords to search for
            max_pages: Maximum number of Google result pages to scrape

        Returns:
            List of profile URLs found
        """
        # Ensure browser is started
        browser.start()

        # Perform Google search
        urls = google_scraper.search(keywords, max_pages)
        self.profile_urls.extend(urls)

        # Remove duplicates
        self.profile_urls = list(set(self.profile_urls))

        logger.info(f"Total profile URLs collected: {len(self.profile_urls)}")
        return self.profile_urls

    def scrape_profiles(
        self,
        urls: Optional[List[str]] = None,
        login_first: bool = True,
    ) -> List[Profile]:
        """
        Scrape profile data from LinkedIn URLs.

        Args:
            urls: List of profile URLs to scrape. If None, uses collected URLs.
            login_first: Whether to log in to LinkedIn first

        Returns:
            List of scraped profiles
        """
        # Use provided URLs or collected URLs
        urls_to_scrape = urls or self.profile_urls

        if not urls_to_scrape:
            logger.error("No profile URLs to scrape")
            return []

        # Start browser
        browser.start()

        # Log in to LinkedIn
        if login_first:
            if not browser.login_linkedin():
                logger.error("LinkedIn login failed. Continuing without login...")

        # Scrape profiles with progress bar
        scraped_profiles = []

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
        ) as progress:
            task = progress.add_task("Scraping profiles...", total=len(urls_to_scrape))

            for i, url in enumerate(urls_to_scrape, 1):
                progress.update(task, description=f"Scraping profile {i}/{len(urls_to_scrape)}")

                # Parse profile
                profile = profile_parser.parse_profile(url)

                if profile:
                    self.collection.add(profile)
                    scraped_profiles.append(profile)

                # Check VPN switching
                if vpn_manager.should_switch():
                    logger.info("Switching VPN connection...")
                    vpn_manager.switch()
                    browser.restart()
                    if login_first:
                        browser.login_linkedin()

                progress.advance(task)

        logger.info(f"✅ Successfully scraped {len(scraped_profiles)} profiles")
        return scraped_profiles

    def connect_to_profiles(
        self,
        urls: Optional[List[str]] = None,
        login_first: bool = True,
    ) -> int:
        """
        Send connection requests to LinkedIn profiles.

        Args:
            urls: List of profile URLs to connect to. If None, uses collected URLs.
            login_first: Whether to log in to LinkedIn first

        Returns:
            Number of successful connection requests
        """
        # Use provided URLs or collected URLs
        urls_to_connect = urls or self.profile_urls

        if not urls_to_connect:
            logger.error("No profile URLs to connect to")
            return 0

        # Start browser
        browser.start()

        # Log in to LinkedIn
        if login_first:
            if not browser.login_linkedin():
                logger.error("LinkedIn login required for connections")
                return 0

        # Send connection requests with progress bar
        successful_connections = 0

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
        ) as progress:
            task = progress.add_task("Sending connection requests...", total=len(urls_to_connect))

            for i, url in enumerate(urls_to_connect, 1):
                progress.update(task, description=f"Connecting {i}/{len(urls_to_connect)}")

                # Send connection request
                if profile_parser.connect_to_profile(url):
                    successful_connections += 1

                # Check VPN switching
                if vpn_manager.should_switch():
                    logger.info("Switching VPN connection...")
                    vpn_manager.switch()
                    browser.restart()
                    browser.login_linkedin()

                progress.advance(task)

        logger.info(f"✅ Successfully sent {successful_connections} connection requests")
        return successful_connections

    def get_profiles(self) -> List[Profile]:
        """
        Get all scraped profiles.

        Returns:
            List of profiles
        """
        return self.collection.get_all()

    def clear_profiles(self):
        """Clear all collected profiles."""
        self.collection.clear()
        logger.info("Cleared all profiles")

    def clear_urls(self):
        """Clear all collected URLs."""
        self.profile_urls.clear()
        logger.info("Cleared all URLs")

    def close_browser(self):
        """Close the browser."""
        browser.stop()


# Global scraper instance
scraper = LinkedInScraper()
