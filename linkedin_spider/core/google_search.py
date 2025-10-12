"""Google Search scraper for finding LinkedIn profiles."""

import time
from typing import List

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

from linkedin_spider.core.browser import browser
from linkedin_spider.utils import config, logger


class GoogleSearchScraper:
    """Scrapes Google Search to find LinkedIn profile URLs."""

    def __init__(self):
        """Initialize Google Search scraper."""
        self.urls: List[str] = []

    def build_search_query(self, keywords: List[str]) -> str:
        """
        Build Google Search query for LinkedIn profiles.

        Args:
            keywords: List of keywords to search for

        Returns:
            Formatted search query
        """
        # Start with site constraint
        query = "site:linkedin.com/in/"

        # Add keywords with AND operator
        for keyword in keywords:
            query += f' AND "{keyword}"'

        return query

    def search(self, keywords: List[str], max_pages: int = None) -> List[str]:
        """
        Search Google for LinkedIn profiles matching keywords.

        Args:
            keywords: List of keywords to search for
            max_pages: Maximum number of Google result pages to scrape.
                      If None, uses config value.

        Returns:
            List of LinkedIn profile URLs
        """
        if not keywords:
            logger.error("No keywords provided for search")
            return []

        max_pages = max_pages or config.max_search_pages
        self.urls = []

        # Build search query
        search_query = self.build_search_query(keywords)
        logger.info(f"Searching Google: {search_query}")

        try:
            # Navigate to Google
            browser.get("https://www.google.com")
            time.sleep(2)

            # Accept cookies if prompted
            try:
                cookies_button = browser.driver.find_element(By.ID, "L2AGLb")
                cookies_button.click()
                time.sleep(1)
            except:
                pass  # No cookies prompt

            # Find search input
            search_input = browser.driver.find_element(By.NAME, "q")
            search_input.send_keys(search_query)
            search_input.send_keys(Keys.RETURN)
            time.sleep(3)

            # Scrape result pages
            pages_scraped = 0
            while pages_scraped < max_pages:
                page_urls = self._scrape_current_page()
                self.urls.extend(page_urls)

                logger.info(f"Page {pages_scraped + 1}: Found {len(page_urls)} URLs (Total: {len(self.urls)})")

                pages_scraped += 1

                # Try to go to next page
                if not self._go_to_next_page():
                    logger.info("No more result pages available")
                    break

                time.sleep(2)

            # Remove duplicates
            self.urls = list(set(self.urls))
            logger.info(f"✅ Total unique LinkedIn URLs found: {len(self.urls)}")

            return self.urls

        except Exception as e:
            logger.error(f"Google search failed: {e}")
            return self.urls

    def _scrape_current_page(self) -> List[str]:
        """
        Scrape LinkedIn URLs from current Google results page.

        Returns:
            List of URLs found on current page
        """
        page_urls = []

        try:
            # Find all result divs
            result_divs = browser.driver.find_elements(By.CLASS_NAME, "yuRUbf")

            for result_div in result_divs:
                try:
                    # Get the link element
                    link_element = result_div.find_element(By.CSS_SELECTOR, "a")
                    url = link_element.get_attribute("href")

                    # Check if it's a LinkedIn profile URL
                    if url and "linkedin.com/in/" in url:
                        page_urls.append(url)

                except Exception as e:
                    logger.debug(f"Error extracting URL from result: {e}")
                    continue

        except Exception as e:
            logger.error(f"Error scraping current page: {e}")

        return page_urls

    def _go_to_next_page(self) -> bool:
        """
        Navigate to next Google results page.

        Returns:
            True if successful, False otherwise
        """
        try:
            next_button = browser.driver.find_element(By.ID, "pnnext")
            next_button.click()
            return True
        except:
            return False

    def interactive_keywords(self) -> List[str]:
        """
        Interactively collect keywords from user.

        Returns:
            List of keywords
        """
        keywords = []

        print("\n🔍 Enter search keywords (press Enter with empty input to finish):")

        while True:
            keyword = input("  Keyword: ").strip()

            if not keyword:
                if len(keywords) == 0:
                    print("  ⚠️  You must enter at least one keyword")
                    continue
                else:
                    break

            keywords.append(keyword)
            print(f"  ✓ Added: {keyword}")

        print(f"\n📋 Your keywords: {', '.join(keywords)}")
        return keywords


# Global Google Search scraper instance
google_scraper = GoogleSearchScraper()
