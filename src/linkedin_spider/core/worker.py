"""Distributed worker for LinkedIn profile scraping."""

import os
import signal
import sys
import time
from pathlib import Path
from typing import Optional

from linkedin_spider.core.browser import browser
from linkedin_spider.core.profile_parser import profile_parser
from linkedin_spider.db import get_db_client
from linkedin_spider.queue import get_consumer
from linkedin_spider.utils.logger import logger
from linkedin_spider.utils.session import session_manager


class DistributedWorker:
    """Worker node for distributed LinkedIn scraping."""

    def __init__(self):
        """Initialize distributed worker."""
        self.worker_id = os.getenv("HOSTNAME", "local-worker")
        self.running = False
        self.processed_count = 0
        self.failed_count = 0
        
        # Components
        self.db_client = None
        self.consumer = None
        
        # Session cookies path (from env or K8s secret mount)
        self.cookie_path = os.getenv("SESSION_COOKIE_PATH", "/tmp/linkedin_cookies.pkl")
        
        # Graceful shutdown handling
        signal.signal(signal.SIGTERM, self._handle_shutdown)
        signal.signal(signal.SIGINT, self._handle_shutdown)

    def _handle_shutdown(self, signum, frame):
        """Handle graceful shutdown signals."""
        logger.info(f"Received shutdown signal ({signum}). Gracefully shutting down...")
        self.running = False

    def initialize(self) -> bool:
        """
        Initialize worker components.

        Returns:
            True if successful, False otherwise
        """
        try:
            logger.info(f"🚀 Initializing worker: {self.worker_id}")
            
            # Initialize database client
            logger.info("Connecting to database...")
            self.db_client = get_db_client()
            
            # Initialize queue consumer
            logger.info("Connecting to message queue...")
            self.consumer = get_consumer()
            
            # Initialize browser
            logger.info("Starting browser...")
            browser.start()
            
            # Load and inject session cookies
            if Path(self.cookie_path).exists():
                logger.info(f"Loading session cookies from {self.cookie_path}...")
                
                # Load cookies from env variable (base64) or file
                cookies_env = os.getenv("LINKEDIN_COOKIES_B64")
                if cookies_env:
                    # Decode from Kubernetes Secret
                    cookies = session_manager.base64_to_cookies(cookies_env)
                    if session_manager.inject_cookies(browser.driver, cookies):
                        logger.info("✅ Session cookies injected from K8s Secret")
                    else:
                        logger.warning("Failed to inject cookies from Secret")
                else:
                    # Load from file
                    cookies = session_manager.load_cookies(Path(self.cookie_path))
                    if cookies and session_manager.inject_cookies(browser.driver, cookies):
                        logger.info("✅ Session cookies injected from file")
                    else:
                        logger.warning("Failed to inject cookies from file")
            else:
                logger.warning(f"No cookie file found at {self.cookie_path}")
                logger.warning("Worker will attempt to scrape without authentication")
            
            logger.info(f"✅ Worker {self.worker_id} initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize worker: {e}", exc_info=True)
            return False

    def process_url(self, url: str) -> bool:
        """
        Process a single profile URL.

        Args:
            url: LinkedIn profile URL to scrape

        Returns:
            True if successful, False otherwise
        """
        start_time = time.time()
        
        try:
            logger.info(f"Processing: {url}")
            
            # Check if already exists in database (deduplication)
            if self.db_client.profile_exists(url):
                logger.info(f"⏭️  Profile already exists in database: {url}")
                self.db_client.log_scrape_attempt(url, "skipped", "Already exists")
                return True  # Consider this a success
            
            # Scrape the profile
            profile = profile_parser.parse_profile(url)
            
            if profile:
                # Save to database
                if self.db_client.save_profile(profile):
                    duration = int(time.time() - start_time)
                    self.db_client.log_scrape_attempt(url, "success", duration_seconds=duration)
                    self.processed_count += 1
                    logger.info(f"✅ Successfully scraped and saved: {url}")
                    return True
                else:
                    self.failed_count += 1
                    self.db_client.log_scrape_attempt(url, "failed", "Database save failed")
                    logger.error(f"❌ Failed to save profile: {url}")
                    return False
            else:
                self.failed_count += 1
                self.db_client.log_scrape_attempt(url, "failed", "Profile parsing failed")
                logger.error(f"❌ Failed to scrape profile: {url}")
                return False
                
        except Exception as e:
            self.failed_count += 1
            error_msg = f"{type(e).__name__}: {str(e)}"
            self.db_client.log_scrape_attempt(url, "failed", error_msg)
            logger.error(f"❌ Error processing {url}: {error_msg}")
            return False

    def run(self):
        """
        Main worker loop.

        Continuously pulls URLs from queue and processes them.
        """
        if not self.initialize():
            logger.error("Worker initialization failed. Exiting.")
            sys.exit(1)
        
        self.running = True
        
        logger.info("="*60)
        logger.info(f"🕷️  WORKER {self.worker_id} STARTED")
        logger.info(f"Queue: {self.consumer.queue_name}")
        logger.info(f"Database: Connected")
        logger.info(f"Browser: Ready")
        logger.info("="*60)
        
        try:
            # Start consuming loop
            self.consumer.consume_loop(
                process_func=self.process_url,
                poll_interval=5
            )
            
        except KeyboardInterrupt:
            logger.info("Worker interrupted by user")
        except Exception as e:
            logger.error(f"Worker crashed: {e}", exc_info=True)
        finally:
            self.shutdown()

    def shutdown(self):
        """Clean shutdown of worker components."""
        logger.info("="*60)
        logger.info(f"🛑 WORKER {self.worker_id} SHUTTING DOWN")
        logger.info(f"Processed: {self.processed_count} profiles")
        logger.info(f"Failed: {self.failed_count} profiles")
        logger.info("="*60)
        
        # Get and log final stats
        if self.db_client:
            try:
                stats = self.db_client.get_worker_stats()
                logger.info(f"Final stats: {stats}")
            except:
                pass
        
        # Close connections
        try:
            if browser.driver:
                browser.stop()
        except:
            pass
        
        try:
            if self.consumer:
                self.consumer.close()
        except:
            pass
        
        try:
            if self.db_client:
                self.db_client.close()
        except:
            pass
        
        logger.info("✅ Worker shutdown complete")


def start_worker():
    """
    Entry point for worker mode.

    Can be called from CLI or directly.
    """
    worker = DistributedWorker()
    worker.run()


if __name__ == "__main__":
    start_worker()
