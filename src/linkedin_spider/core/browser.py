"""Browser management for LinkedIn Spider."""

import os
import random
import time
from pathlib import Path
from typing import Any, Optional

from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from linkedin_spider.utils import config, logger

# How long to wait for the feed after submitting the login form. A visible browser
# gets long enough for a person to finish 2FA or a checkpoint.
LOGIN_TIMEOUT_VISIBLE = 300
LOGIN_TIMEOUT_HEADLESS = 15


class BrowserManager:
    """Manages Selenium WebDriver instances and LinkedIn authentication."""

    def __init__(self):
        """Initialize browser manager."""
        # A Chrome driver and its WebDriverWait once start() has run, otherwise None
        self.driver: Any = None
        self.wait: Any = None

    def create_driver(self) -> webdriver.Chrome:
        """
        Create and configure Chrome WebDriver.

        Returns:
            Configured WebDriver instance
        """
        chrome_options = Options()

        # Headless mode
        if config.headless:
            chrome_options.add_argument("--headless=new")

        # Window size
        chrome_options.add_argument(
            f"--window-size={config.window_width},{config.window_height}"
        )

        # Anti-detection options
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option("useAutomationExtension", False)

        # Custom user agent
        if config.user_agent:
            chrome_options.add_argument(f"user-agent={config.user_agent}")
        else:
            # Use a realistic user agent
            user_agents = [
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            ]
            chrome_options.add_argument(f"user-agent={random.choice(user_agents)}")

        # Additional stability options
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")

        # The sandbox protects a logged-in browser from the pages it loads, so only
        # environments that can't run it (containers) should turn it off.
        if os.getenv("CHROME_NO_SANDBOX"):
            chrome_options.add_argument("--no-sandbox")

        # Selenium Manager finds or downloads a matching driver
        driver = webdriver.Chrome(options=chrome_options)

        # Set page load timeout
        driver.set_page_load_timeout(60)

        # Execute script to hide webdriver property
        driver.execute_script(
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
        )

        logger.info("Chrome WebDriver initialized")
        return driver

    def start(self) -> webdriver.Chrome:
        """
        Start browser session.

        Returns:
            WebDriver instance
        """
        if self.driver is None:
            self.driver = self.create_driver()
            self.wait = WebDriverWait(self.driver, 10)

        return self.driver

    def stop(self):
        """Stop browser session."""
        if self.driver:
            try:
                self.driver.quit()
                logger.info("Browser closed")
            except Exception as e:
                logger.error(f"Error closing browser: {e}")
            finally:
                self.driver = None
                self.wait = None

    def restart(self):
        """Restart browser session."""
        logger.info("Restarting browser...")
        self.stop()
        time.sleep(2)
        self.start()

    def login_linkedin(self, email: Optional[str] = None, password: Optional[str] = None) -> bool:
        """
        Log in to LinkedIn.

        Args:
            email: LinkedIn email. If None, uses config value.
            password: LinkedIn password. If None, uses config value.

        Returns:
            True if login successful, False otherwise
        """
        if self.driver is None:
            self.start()

        email = email or config.linkedin_email
        password = password or config.linkedin_password

        if not email or not password:
            logger.error("LinkedIn credentials not provided")
            return False

        try:
            logger.info("Logging in to LinkedIn...")
            self.driver.get("https://www.linkedin.com")
            time.sleep(2)

            # Find and fill email field
            try:
                email_field = self.wait.until(
                    EC.presence_of_element_located((By.ID, "session_key"))
                )
            except TimeoutException:
                # Try alternative selector
                email_field = self.driver.find_element(By.CLASS_NAME, "input__input")

            email_field.clear()
            email_field.send_keys(email)
            time.sleep(random.uniform(0.5, 1.5))

            # Find and fill password field
            password_field = self.driver.find_element(By.ID, "session_password")
            password_field.clear()
            password_field.send_keys(password)
            time.sleep(random.uniform(0.5, 1.5))

            # Click login button
            login_button = self.driver.find_element(
                By.CLASS_NAME, "sign-in-form__submit-button"
            )
            login_button.click()

            timeout = (
                LOGIN_TIMEOUT_HEADLESS if config.headless else LOGIN_TIMEOUT_VISIBLE
            )
            logger.info(
                f"Waiting up to {timeout}s for the feed. Complete any 2FA or "
                "verification in the browser window."
            )
            try:
                WebDriverWait(self.driver, timeout).until(
                    lambda driver: (
                        "feed" in driver.current_url
                        or "mynetwork" in driver.current_url
                    )
                )
            except TimeoutException:
                logger.warning(
                    "LinkedIn login failed - check for CAPTCHA or verification"
                )
                return False

            logger.info("✅ LinkedIn login successful")
            return True

        except Exception as e:
            logger.error(f"LinkedIn login failed: {e}")
            return False

    def scroll_page(self, duration: int = 15):
        """
        Scroll page to load dynamic content.

        Args:
            duration: How long to scroll (in seconds)
        """
        if self.driver is None:
            return

        start_time = time.time()
        scroll_y = 1000

        while time.time() - start_time < duration:
            try:
                self.driver.execute_script(f"window.scrollTo(0, {scroll_y})")
                scroll_y += 1000
                time.sleep(3)
            except Exception as e:
                logger.debug(f"Scroll error: {e}")
                break

    def random_delay(self, min_seconds: Optional[int] = None, max_seconds: Optional[int] = None):
        """
        Wait for a random amount of time.

        Args:
            min_seconds: Minimum delay. If None, uses config value.
            max_seconds: Maximum delay. If None, uses config value.
        """
        min_delay = config.min_delay if min_seconds is None else min_seconds
        max_delay = config.max_delay if max_seconds is None else max_seconds

        # A max below the min is a config mistake: honour the larger minimum
        delay = random.uniform(min_delay, max(min_delay, max_delay))
        logger.debug(f"Waiting {delay:.1f} seconds...")
        time.sleep(delay)

    def get(self, url: str):
        """
        Navigate to URL.

        Args:
            url: URL to navigate to
        """
        if self.driver is None:
            self.start()

        try:
            self.driver.get(url)
        except Exception as e:
            logger.error(f"Error navigating to {url}: {e}")
            raise

    @property
    def page_source(self) -> str:
        """Get current page source."""
        if self.driver is None:
            return ""
        return self.driver.page_source

    @property
    def current_url(self) -> str:
        """Get current URL."""
        if self.driver is None:
            return ""
        return self.driver.current_url


# Global browser manager instance
browser = BrowserManager()
