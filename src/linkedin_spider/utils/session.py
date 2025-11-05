"""Session and cookie management for distributed scraping."""

import base64
import json
import pickle
from pathlib import Path
from typing import Dict, List, Optional

from linkedin_spider.utils.logger import logger


class SessionManager:
    """Manages LinkedIn session cookies for distributed scraping."""

    def __init__(self, cookie_path: Optional[Path] = None):
        """
        Initialize session manager.

        Args:
            cookie_path: Path to store/load cookies. If None, uses default.
        """
        self.cookie_path = cookie_path or Path("/tmp/linkedin_cookies.pkl")

    def extract_cookies(self, driver) -> List[Dict]:
        """
        Extract cookies from active browser session.

        Args:
            driver: Selenium WebDriver instance with active LinkedIn session

        Returns:
            List of cookie dictionaries
        """
        try:
            cookies = driver.get_cookies()
            logger.info(f"✅ Extracted {len(cookies)} cookies from browser session")
            return cookies
        except Exception as e:
            logger.error(f"Failed to extract cookies: {e}")
            return []

    def save_cookies(self, cookies: List[Dict], path: Optional[Path] = None) -> bool:
        """
        Save cookies to file.

        Args:
            cookies: List of cookie dictionaries
            path: Optional custom path to save cookies

        Returns:
            True if successful, False otherwise
        """
        save_path = path or self.cookie_path
        save_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            with open(save_path, "wb") as f:
                pickle.dump(cookies, f)
            logger.info(f"✅ Saved cookies to {save_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to save cookies: {e}")
            return False

    def load_cookies(self, path: Optional[Path] = None) -> List[Dict]:
        """
        Load cookies from file.

        Args:
            path: Optional custom path to load cookies from

        Returns:
            List of cookie dictionaries
        """
        load_path = path or self.cookie_path

        if not load_path.exists():
            logger.warning(f"Cookie file not found: {load_path}")
            return []

        try:
            with open(load_path, "rb") as f:
                cookies = pickle.load(f)
            logger.info(f"✅ Loaded {len(cookies)} cookies from {load_path}")
            return cookies
        except Exception as e:
            logger.error(f"Failed to load cookies: {e}")
            return []

    def inject_cookies(self, driver, cookies: Optional[List[Dict]] = None) -> bool:
        """
        Inject cookies into browser session.

        Args:
            driver: Selenium WebDriver instance
            cookies: Optional list of cookies. If None, loads from default path.

        Returns:
            True if successful, False otherwise
        """
        if cookies is None:
            cookies = self.load_cookies()

        if not cookies:
            logger.error("No cookies to inject")
            return False

        try:
            # First navigate to LinkedIn domain to set cookies
            driver.get("https://www.linkedin.com")

            # Inject each cookie
            for cookie in cookies:
                try:
                    # Remove 'expiry' if present and problematic
                    if "expiry" in cookie:
                        # Selenium expects integer expiry
                        cookie["expiry"] = int(cookie["expiry"])

                    driver.add_cookie(cookie)
                except Exception as e:
                    logger.warning(f"Failed to add cookie {cookie.get('name', 'unknown')}: {e}")
                    continue

            logger.info(f"✅ Injected {len(cookies)} cookies into browser session")
            
            # Refresh page to apply cookies
            driver.refresh()
            return True

        except Exception as e:
            logger.error(f"Failed to inject cookies: {e}")
            return False

    def cookies_to_base64(self, cookies: List[Dict]) -> str:
        """
        Convert cookies to base64-encoded string for Kubernetes Secret.

        Args:
            cookies: List of cookie dictionaries

        Returns:
            Base64-encoded string
        """
        try:
            json_str = json.dumps(cookies)
            encoded = base64.b64encode(json_str.encode()).decode()
            logger.info("✅ Converted cookies to base64 for Kubernetes Secret")
            return encoded
        except Exception as e:
            logger.error(f"Failed to encode cookies: {e}")
            return ""

    def base64_to_cookies(self, encoded: str) -> List[Dict]:
        """
        Convert base64-encoded string back to cookies.

        Args:
            encoded: Base64-encoded cookie string

        Returns:
            List of cookie dictionaries
        """
        try:
            decoded = base64.b64decode(encoded.encode()).decode()
            cookies = json.loads(decoded)
            logger.info(f"✅ Decoded {len(cookies)} cookies from base64")
            return cookies
        except Exception as e:
            logger.error(f"Failed to decode cookies: {e}")
            return []

    def validate_session(self, driver) -> bool:
        """
        Validate that the current session is authenticated.

        Args:
            driver: Selenium WebDriver instance

        Returns:
            True if authenticated, False otherwise
        """
        try:
            current_url = driver.current_url
            
            # Check if on LinkedIn and not on login page
            if "linkedin.com" in current_url and "login" not in current_url:
                logger.info("✅ Session validated - user is authenticated")
                return True
            else:
                logger.warning("⚠️ Session validation failed - not authenticated")
                return False

        except Exception as e:
            logger.error(f"Failed to validate session: {e}")
            return False

    def create_k8s_secret_yaml(
        self, 
        cookies: List[Dict], 
        output_path: Path,
        secret_name: str = "linkedin-cookies"
    ) -> bool:
        """
        Create Kubernetes Secret YAML file for cookies.

        Args:
            cookies: List of cookie dictionaries
            output_path: Path to save the Secret YAML
            secret_name: Name for the Kubernetes Secret

        Returns:
            True if successful, False otherwise
        """
        try:
            encoded_cookies = self.cookies_to_base64(cookies)
            
            yaml_content = f"""apiVersion: v1
kind: Secret
metadata:
  name: {secret_name}
  namespace: linkedin-spider
type: Opaque
data:
  cookies: {encoded_cookies}
"""
            
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, "w") as f:
                f.write(yaml_content)
            
            logger.info(f"✅ Created Kubernetes Secret YAML at {output_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to create Kubernetes Secret YAML: {e}")
            return False


# Global session manager instance
session_manager = SessionManager()
