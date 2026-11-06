"""CLI commands for LinkedIn Spider."""

from pathlib import Path

from linkedin_spider.cli import display
from linkedin_spider.core import google_scraper, scraper
from linkedin_spider.core.scraper import MAX_CONNECTS_PER_RUN
from linkedin_spider.utils import config, exporter
from linkedin_spider.utils.export import load_urls, save_urls


def search_profiles_command():
    """Handle search & collect URLs command."""
    display.console.print("\n[bold cyan]🔍 Search & Collect Profile URLs[/bold cyan]\n")

    # Get keywords
    keywords = google_scraper.interactive_keywords()

    if not keywords:
        display.error("No keywords provided")
        return

    # Ask for max pages
    max_pages_str = display.prompt(
        "Maximum Google result pages to scrape",
        default=str(config.max_search_pages),
    )

    try:
        max_pages = int(max_pages_str)
    except ValueError:
        max_pages = config.max_search_pages

    # Perform search
    display.info(f"Searching with keywords: {', '.join(keywords)}")
    urls = scraper.search_profiles(keywords, max_pages)

    if urls:
        display.success(f"Found {len(urls)} profile URLs")

        # Show some URLs
        display.show_urls_list(urls, max_rows=10)

        # Ask to save
        if display.confirm("Save URLs to file?", default=True):
            filename = display.prompt(
                "Filename (without extension)", default="profile_urls"
            )
            filepath = config.data_dir / f"{filename}.txt"
            total = save_urls(filepath, urls)

            display.success(f"URLs saved to {filepath} ({total} total)")
    else:
        display.warning("No URLs found")

    display.prompt("\nPress Enter to continue")


def scrape_profiles_command():
    """Handle scrape profile data command."""
    display.console.print("\n[bold cyan]📊 Scrape Profile Data[/bold cyan]\n")

    # Check if we have URLs
    if not scraper.profile_urls:
        display.warning("No URLs collected yet")

        # Ask to load from file
        if display.confirm("Load URLs from file?", default=True):
            filename = display.prompt("Filename", default="profile_urls.txt")
            filepath = Path(filename)

            if not filepath.exists():
                filepath = config.data_dir / filename

            if filepath.exists():
                urls = load_urls(filepath)
                scraper.profile_urls = urls
                display.success(f"Loaded {len(urls)} URLs from {filepath}")
            else:
                display.error(f"File not found: {filepath}")
                display.prompt("\nPress Enter to continue")
                return
        else:
            display.prompt("\nPress Enter to continue")
            return

    # Confirm scraping
    display.info(f"Ready to scrape {len(scraper.profile_urls)} profiles")

    if not display.confirm("Start scraping?", default=True):
        return

    # Scrape profiles
    profiles = scraper.scrape_profiles(login_first=True)

    if profiles:
        display.success(f"Successfully scraped {len(profiles)} profiles")

        # Show profiles
        display.show_profiles_table(profiles, max_rows=10)

        # Ask to export
        if display.confirm("Export profiles now?", default=True):
            export_results_command()
    else:
        display.warning("No profiles scraped")

    display.prompt("\nPress Enter to continue")


def _confirm_connection(name: str, url: str) -> bool:
    """Ask whether to send a connection request to this person."""
    return display.confirm(f"Send request to {name} ({url})?", default=False)


def connect_to_profiles_command():
    """Handle auto-connect to profiles command."""
    display.console.print("\n[bold cyan]🤝 Auto-Connect to Profiles[/bold cyan]\n")

    display.warning(
        "⚠️  This sends real connection requests on LinkedIn.\n"
        f"   You'll confirm each person, up to {MAX_CONNECTS_PER_RUN} requests per run.\n"
        "   Use this feature responsibly and in accordance with LinkedIn's Terms of Service."
    )

    if not display.confirm("Do you understand and want to continue?", default=False):
        return

    # Check if we have URLs
    if not scraper.profile_urls:
        display.error("No profile URLs available. Search for profiles first.")
        display.prompt("\nPress Enter to continue")
        return

    # Confirm
    display.info(f"{len(scraper.profile_urls)} profiles to go through")

    if not display.confirm("Start?", default=False):
        return

    # Connect
    counts = scraper.connect_to_profiles(
        scraper.profile_urls, _confirm_connection, login_first=True
    )

    display.success(
        f"Sent {counts['sent']} connection requests "
        f"({counts['declined']} declined, {counts['skipped']} skipped)"
    )
    display.prompt("\nPress Enter to continue")


def view_export_results_command():
    """Handle view/export results command."""
    display.console.print("\n[bold cyan]📁 View/Export Results[/bold cyan]\n")

    profiles = scraper.get_profiles()

    if not profiles:
        display.warning("No profiles available. Scrape profiles first.")
        display.prompt("\nPress Enter to continue")
        return

    # Show profiles
    display.show_profiles_table(profiles, max_rows=20)

    # Ask to export
    if display.confirm("\nExport profiles?", default=True):
        export_results_command()

    display.prompt("\nPress Enter to continue")


def export_results_command():
    """Handle export logic."""
    profiles = scraper.get_profiles()

    if not profiles:
        display.warning("No profiles to export")
        return

    # Get export format
    display.console.print("\n[bold]Export Format:[/bold]")
    display.console.print("  1. CSV")
    display.console.print("  2. JSON")
    display.console.print("  3. Excel")

    format_choice = display.prompt("Choose format", default="1")

    format_map = {
        "1": "csv",
        "2": "json",
        "3": "excel",
        "csv": "csv",
        "json": "json",
        "excel": "excel",
        "xlsx": "excel",
    }

    export_format = format_map.get(format_choice.lower(), "csv")

    # Get filename
    filename = display.prompt("Filename (without extension)", default="profiles")

    # Export
    try:
        filepath = exporter.export(profiles, format=export_format, filename=filename)
        display.success(f"Exported {len(profiles)} profiles to {filepath}")
        scraper.finish_session()
    except ImportError as e:
        display.error(str(e))
    except Exception as e:
        display.error(f"Export failed: {e}")


def configure_settings_command():
    """Handle configure settings command."""
    display.console.print("\n[bold cyan]⚙️  Configure Settings[/bold cyan]\n")

    display.info("Current configuration:")
    display.console.print(f"  • Min Delay: {config.min_delay}s")
    display.console.print(f"  • Max Delay: {config.max_delay}s")
    display.console.print(f"  • Max Search Pages: {config.max_search_pages}")
    display.console.print(f"  • Headless: {config.headless}")
    display.console.print(f"  • VPN Enabled: {config.vpn_enabled}")
    display.console.print(f"  • Data Directory: {config.data_dir}")
    display.console.print(f"  • Export Format: {config.default_export_format}")

    display.console.print(
        "\n[dim]To change settings, edit config.yaml or .env file[/dim]"
    )
    display.prompt("\nPress Enter to continue")


def help_command():
    """Handle help command."""
    display.show_help()
    display.prompt("\nPress Enter to continue")
