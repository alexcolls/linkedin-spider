"""Main scraper orchestrator for LinkedIn Spider."""

from typing import Callable, Dict, List, Optional

from rich.console import Console
from rich.markup import escape
from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TaskProgressColumn,
    TextColumn,
)
from rich.table import Table

from linkedin_spider.core.browser import browser
from linkedin_spider.core.google_search import google_scraper
from linkedin_spider.core.profile_parser import SessionBlocked, profile_parser
from linkedin_spider.models import Profile, ProfileCollection, unique_profile_urls
from linkedin_spider.utils import config, logger, vpn_manager
from linkedin_spider.utils.progress import ProgressTracker

# Failing this many profiles in a row means something is wrong with the session or
# the browser, not with the profiles. Stop rather than burn through the whole list.
MAX_CONSECUTIVE_FAILURES = 5

# Connection requests are sent one at a time, with a person confirming each.
MAX_CONNECTS_PER_RUN = 10


class LinkedInScraper:
    """Main orchestrator for LinkedIn scraping operations."""

    def __init__(self):
        """Initialize LinkedIn scraper."""
        self.collection = ProfileCollection()
        self.profile_urls: List[str] = []
        self.tracker: Optional[ProgressTracker] = None

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

        # Remove duplicates
        self.profile_urls = unique_profile_urls([*self.profile_urls, *urls])

        logger.info(f"Total profile URLs collected: {len(self.profile_urls)}")
        return self.profile_urls

    def scrape_profiles(
        self,
        urls: Optional[List[str]] = None,
        login_first: bool = True,
        resume_session: Optional[str] = None,
        dry_run: bool = False,
        session_name: Optional[str] = None,
    ) -> List[Profile]:
        """
        Scrape profile data from LinkedIn URLs.

        Every scraped profile is saved to the session's progress file immediately.
        The run stops early if interrupted, if LinkedIn blocks the session, or after
        repeated failures, and returns what it has. Keep the progress file until the
        results are exported: call finish_session after exporting.

        Args:
            urls: List of profile URLs to scrape. If None, uses collected URLs.
            login_first: Whether to log in to LinkedIn first
            resume_session: Session name to resume from previous run
            dry_run: If True, only preview without scraping
            session_name: Custom session name for progress tracking

        Returns:
            All profiles scraped in this session, including earlier runs when resuming
        """
        console = Console()
        tracker: Optional[ProgressTracker] = None
        scraped_profiles: List[Profile] = []

        if resume_session:
            tracker = ProgressTracker.load_session(resume_session)
            if not tracker:
                logger.error(f"Session '{resume_session}' not found")
                return []
            logger.info(f"📂 Resuming session: {resume_session}")
            tracker.requeue_failed()
            urls_to_scrape = tracker.get_remaining()
            scraped_profiles = self._restore_profiles(tracker)

            # Show resume stats
            stats = tracker.get_stats()
            console.print("\n[cyan]Resuming from previous session:[/cyan]")
            console.print(
                f"  Already completed: {stats['completed']}/{stats['total_urls']}"
            )
            console.print(f"  Remaining: {stats['remaining']}")
            console.print(f"  Progress: {stats['progress_percent']:.1f}%\n")
        else:
            # Use provided URLs or collected URLs
            urls_to_scrape = unique_profile_urls(urls or self.profile_urls)

        # Dry run mode - just preview, writing nothing
        if dry_run:
            self._print_dry_run(console, urls_to_scrape)
            return []

        self.tracker = tracker

        if not urls_to_scrape:
            if not tracker:
                logger.error("No profile URLs to scrape")
            return scraped_profiles

        if tracker is None:
            tracker = ProgressTracker(session_name=session_name)
            tracker.initialize(urls_to_scrape)
            self.tracker = tracker

            # A reused session name brings its earlier results along
            urls_to_scrape = tracker.get_remaining()
            scraped_profiles = self._restore_profiles(tracker)

            if not urls_to_scrape:
                return scraped_profiles

        # Start browser
        browser.start()

        # Log in to LinkedIn
        if login_first and not browser.login_linkedin():
            if config.linkedin_email and config.linkedin_password:
                logger.error(
                    "LinkedIn login failed, so not scraping. "
                    f"Fix it and retry with: --resume {tracker.session_name}"
                )
                return scraped_profiles
            logger.warning(
                "No LinkedIn credentials set. Continuing logged out: "
                "scraping stops at the first login wall."
            )

        stop_reason = self._scrape_urls(
            urls_to_scrape, tracker, scraped_profiles, login_first
        )

        self._print_stats(console, tracker, stop_reason)

        logger.info(f"✅ {len(scraped_profiles)} profiles scraped in this session")
        return scraped_profiles

    def _restore_profiles(self, tracker: ProgressTracker) -> List[Profile]:
        """Bring back the profiles a session has already scraped."""
        profiles = tracker.get_profiles()
        for profile in profiles:
            self.collection.add(profile)
        return profiles

    def _scrape_urls(
        self,
        urls: List[str],
        tracker: ProgressTracker,
        scraped_profiles: List[Profile],
        login_first: bool,
    ) -> Optional[str]:
        """
        Scrape each URL, adding results to scraped_profiles as they arrive.

        Returns:
            Why the run stopped early, or None if it got through every URL
        """
        consecutive_failures = 0

        try:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TaskProgressColumn(),
            ) as progress:
                task = progress.add_task("Scraping profiles...", total=len(urls))

                for i, url in enumerate(urls, 1):
                    progress.update(
                        task, description=f"Scraping profile {i}/{len(urls)}"
                    )

                    try:
                        # Parse profile
                        profile = profile_parser.parse_profile(url)

                        if profile:
                            self.collection.add(profile)
                            scraped_profiles.append(profile)
                            tracker.mark_completed(url, profile)
                            consecutive_failures = 0
                        else:
                            tracker.mark_failed(url, "No data extracted")
                            consecutive_failures += 1

                    except SessionBlocked as e:
                        # This URL stays in remaining: the profile isn't at fault
                        return str(e)
                    except Exception as e:
                        logger.error(f"Failed to scrape {url}: {e}")
                        tracker.mark_failed(url, str(e))
                        consecutive_failures += 1

                    if consecutive_failures >= MAX_CONSECUTIVE_FAILURES:
                        return f"{MAX_CONSECUTIVE_FAILURES} profiles failed in a row"

                    # Check VPN switching
                    if vpn_manager.should_switch():
                        logger.info("Switching VPN connection...")
                        vpn_manager.switch()
                        browser.restart()
                        if login_first:
                            browser.login_linkedin()

                    progress.advance(task)

        except KeyboardInterrupt:
            return "Interrupted"

        return None

    @staticmethod
    def _print_dry_run(console: Console, urls: List[str]):
        """Show which URLs a run would scrape."""
        console.print("\n[yellow]🔍 DRY RUN MODE - Preview Only[/yellow]\n")

        table = Table(
            title="URLs to Scrape", show_header=True, header_style="bold cyan"
        )
        table.add_column("#", style="dim", width=6)
        table.add_column("URL", style="blue")

        for i, url in enumerate(urls[:20], 1):  # Show first 20
            table.add_row(str(i), escape(url))

        if len(urls) > 20:
            table.add_row("...", f"... and {len(urls) - 20} more")

        console.print(table)
        console.print(f"\n[green]Total URLs to scrape: {len(urls)}[/green]")
        console.print("[yellow]Run without --dry-run to start scraping[/yellow]\n")

    @staticmethod
    def _print_stats(
        console: Console, tracker: ProgressTracker, stop_reason: Optional[str]
    ):
        """Show how the run went and whether there is anything left to resume."""
        stats = tracker.get_stats()

        console.print("\n" + "=" * 60)
        console.print("[bold cyan]📊 Scraping Statistics[/bold cyan]")
        console.print("=" * 60)

        stats_table = Table(show_header=False, box=None)
        stats_table.add_column("Metric", style="cyan", width=25)
        stats_table.add_column("Value", style="green")

        stats_table.add_row("✅ Successfully scraped", str(stats["completed"]))
        stats_table.add_row("❌ Failed", str(stats["failed"]))
        stats_table.add_row("⏭️  Skipped", str(stats["skipped"]))
        stats_table.add_row("📊 Total", str(stats["total_urls"]))
        stats_table.add_row("📈 Success rate", f"{stats['progress_percent']:.1f}%")
        stats_table.add_row("📂 Session", stats["session_name"])

        console.print(stats_table)
        console.print("=" * 60 + "\n")

        if stop_reason:
            console.print(f"[bold red]🛑 Stopped: {escape(stop_reason)}[/bold red]")

        unfinished = stats["remaining"] + stats["failed"]
        if unfinished:
            console.print(
                f"[yellow]⚠️  {stats['remaining']} URLs remaining, {stats['failed']} failed.[/yellow]"
            )
            console.print(
                f"[yellow]Continue and retry failures with: --resume {stats['session_name']}[/yellow]\n"
            )

    def finish_session(self):
        """
        Delete the progress file once its results are safely exported. A session
        with anything failed or remaining keeps its file, so it can be resumed.
        """
        tracker = self.tracker
        if tracker and tracker.is_complete() and not tracker.get_stats()["failed"]:
            tracker.cleanup()
            self.tracker = None

    def connect_to_profiles(
        self,
        urls: List[str],
        confirm: Callable[[str, str], bool],
        login_first: bool = True,
    ) -> Dict[str, int]:
        """
        Offer to send connection requests, one person at a time.

        Stops after MAX_CONNECTS_PER_RUN requests have been sent. Declining someone
        doesn't count towards that.

        Args:
            urls: List of profile URLs to go through
            confirm: Called with (name, url) before each request. Required, so that
                a person decides every request.
            login_first: Whether to log in to LinkedIn first

        Returns:
            Number of requests "sent", "declined" and "skipped"
        """
        counts = {"sent": 0, "declined": 0, "skipped": 0}
        urls_to_connect = unique_profile_urls(urls)

        if not urls_to_connect:
            logger.error("No profile URLs to connect to")
            return counts

        # Start browser
        browser.start()

        # Log in to LinkedIn
        if login_first and not browser.login_linkedin():
            logger.error("LinkedIn login required for connections")
            return counts

        try:
            for url in urls_to_connect:
                if counts["sent"] >= MAX_CONNECTS_PER_RUN:
                    logger.warning(
                        f"Stopped at the limit of {MAX_CONNECTS_PER_RUN} requests per run"
                    )
                    break

                counts[profile_parser.connect_to_profile(url, confirm)] += 1

                # Check VPN switching
                if vpn_manager.should_switch():
                    logger.info("Switching VPN connection...")
                    vpn_manager.switch()
                    browser.restart()
                    browser.login_linkedin()

        except SessionBlocked as e:
            logger.error(f"Stopped: {e}")
        except KeyboardInterrupt:
            logger.warning("Interrupted")

        logger.info(
            f"✅ Connection requests: {counts['sent']} sent, "
            f"{counts['declined']} declined, {counts['skipped']} skipped"
        )
        return counts

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
