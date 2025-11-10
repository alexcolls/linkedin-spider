"""Main scraper orchestrator for LinkedIn Spider."""

from typing import List, Optional

from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.table import Table
from rich.console import Console

from linkedin_spider.core.browser import browser
from linkedin_spider.core.google_search import google_scraper
from linkedin_spider.core.profile_parser import profile_parser
from linkedin_spider.models import Profile, ProfileCollection
from linkedin_spider.utils import config, logger, vpn_manager
from linkedin_spider.utils.progress import ProgressTracker


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
        resume_session: Optional[str] = None,
        dry_run: bool = False,
        session_name: Optional[str] = None,
    ) -> List[Profile]:
        """
        Scrape profile data from LinkedIn URLs.

        Args:
            urls: List of profile URLs to scrape. If None, uses collected URLs.
            login_first: Whether to log in to LinkedIn first
            resume_session: Session name to resume from previous run
            dry_run: If True, only preview without scraping
            session_name: Custom session name for progress tracking

        Returns:
            List of scraped profiles
        """
        # Initialize progress tracker
        if resume_session:
            tracker = ProgressTracker.load_session(resume_session)
            if not tracker:
                logger.error(f"Session '{resume_session}' not found")
                return []
            logger.info(f"📂 Resuming session: {resume_session}")
            urls_to_scrape = tracker.get_remaining()
            
            # Show resume stats
            stats = tracker.get_stats()
            console = Console()
            console.print(f"\n[cyan]Resuming from previous session:[/cyan]")
            console.print(f"  Already completed: {stats['completed']}/{stats['total_urls']}")
            console.print(f"  Remaining: {stats['remaining']}")
            console.print(f"  Progress: {stats['progress_percent']:.1f}%\n")
        else:
            # Use provided URLs or collected URLs
            urls_to_scrape = urls or self.profile_urls
            tracker = ProgressTracker(session_name=session_name)
            tracker.initialize(urls_to_scrape)

        if not urls_to_scrape:
            logger.error("No profile URLs to scrape")
            return []

        # Dry run mode - just preview
        if dry_run:
            console = Console()
            console.print("\n[yellow]🔍 DRY RUN MODE - Preview Only[/yellow]\n")
            
            table = Table(title="URLs to Scrape", show_header=True, header_style="bold cyan")
            table.add_column("#", style="dim", width=6)
            table.add_column("URL", style="blue")
            
            for i, url in enumerate(urls_to_scrape[:20], 1):  # Show first 20
                table.add_row(str(i), url)
            
            if len(urls_to_scrape) > 20:
                table.add_row("...", f"... and {len(urls_to_scrape) - 20} more")
            
            console.print(table)
            console.print(f"\n[green]Total URLs to scrape: {len(urls_to_scrape)}[/green]")
            console.print("[yellow]Run without --dry-run to start scraping[/yellow]\n")
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

                try:
                    # Parse profile
                    profile = profile_parser.parse_profile(url)

                    if profile:
                        self.collection.add(profile)
                        scraped_profiles.append(profile)
                        tracker.mark_completed(url)
                    else:
                        tracker.mark_failed(url, "No data extracted")

                except Exception as e:
                    logger.error(f"Failed to scrape {url}: {e}")
                    tracker.mark_failed(url, str(e))

                # Check VPN switching
                if vpn_manager.should_switch():
                    logger.info("Switching VPN connection...")
                    vpn_manager.switch()
                    browser.restart()
                    if login_first:
                        browser.login_linkedin()

                progress.advance(task)

        # Display final statistics
        console = Console()
        stats = tracker.get_stats()
        
        console.print("\n" + "="*60)
        console.print("[bold cyan]📊 Scraping Statistics[/bold cyan]")
        console.print("="*60)
        
        stats_table = Table(show_header=False, box=None)
        stats_table.add_column("Metric", style="cyan", width=25)
        stats_table.add_column("Value", style="green")
        
        stats_table.add_row("✅ Successfully scraped", str(stats['completed']))
        stats_table.add_row("❌ Failed", str(stats['failed']))
        stats_table.add_row("⏭️  Skipped", str(stats['skipped']))
        stats_table.add_row("📊 Total", str(stats['total_urls']))
        stats_table.add_row("📈 Success rate", f"{(stats['completed']/stats['total_urls']*100) if stats['total_urls'] > 0 else 0:.1f}%")
        stats_table.add_row("📂 Session", stats['session_name'])
        
        console.print(stats_table)
        console.print("=" *60 + "\n")
        
        # Cleanup progress file if complete
        if tracker.is_complete():
            tracker.cleanup()
            console.print("[green]✨ All URLs processed! Progress file cleaned up.[/green]\n")
        else:
            console.print(f"[yellow]⚠️  {stats['remaining']} URLs remaining.[/yellow]")
            console.print(f"[yellow]Resume with: --resume {stats['session_name']}[/yellow]\n")
        
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
