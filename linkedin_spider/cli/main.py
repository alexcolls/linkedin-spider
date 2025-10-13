"""Main CLI application for LinkedIn Spider."""

import sys

import typer

from linkedin_spider.cli import commands, display
from linkedin_spider.core import scraper
from linkedin_spider.utils import logger


app = typer.Typer(
    name="linkedin-spider",
    help="A professional CLI tool for scraping LinkedIn profiles via Google Search",
    add_completion=False,
    no_args_is_help=False,  # Don't show help when no args provided
)


def interactive_menu():
    """Run the interactive menu."""
    while True:
        choice = display.interactive_menu_select()

        if choice == "1":
            commands.search_profiles_command()
        elif choice == "2":
            commands.scrape_profiles_command()
        elif choice == "3":
            commands.connect_to_profiles_command()
        elif choice == "4":
            commands.view_export_results_command()
        elif choice == "5":
            commands.configure_settings_command()
        elif choice == "6":
            commands.help_command()
        elif choice == "0":
            display.console.print("\n[cyan]👋 Goodbye![/cyan]\n")
            break
        else:
            display.warning(f"Invalid option: {choice}")
            display.prompt("\nPress Enter to continue")


@app.callback(invoke_without_command=True)
def callback(
    ctx: typer.Context,
):
    """
    LinkedIn Spider - Professional profile scraping tool.

    By default, runs in interactive mode with a menu.
    Use subcommands for specific operations.
    """
    # If a subcommand is provided, don't run the interactive menu
    if ctx.invoked_subcommand is not None:
        return

    # No subcommand provided - run interactive menu
    try:
        # Run interactive menu (it will show welcome screen)
        interactive_menu()

    except KeyboardInterrupt:
        display.console.print("\n\n[yellow]⚠️  Interrupted by user[/yellow]")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        display.error(f"An error occurred: {e}")
        sys.exit(1)
    finally:
        # Cleanup
        try:
            scraper.close_browser()
        except:
            pass


@app.command()
def search(
    keywords: list[str] = typer.Argument(..., help="Keywords to search for"),
    max_pages: int = typer.Option(10, "--max-pages", "-n", help="Maximum pages to scrape"),
    save: bool = typer.Option(True, "--save/--no-save", help="Save URLs to file"),
):
    """Search for LinkedIn profiles using keywords."""
    try:
        display.info(f"Searching for profiles with keywords: {', '.join(keywords)}")
        urls = scraper.search_profiles(keywords, max_pages)

        display.success(f"Found {len(urls)} profile URLs")

        if save and urls:
            from linkedin_spider.utils import config
            filepath = config.data_dir / "profile_urls.txt"
            filepath.parent.mkdir(parents=True, exist_ok=True)

            with open(filepath, "w") as f:
                f.write("\n".join(urls))

            display.success(f"URLs saved to {filepath}")

    except KeyboardInterrupt:
        display.warning("Interrupted by user")
    except Exception as e:
        logger.error(f"Search failed: {e}", exc_info=True)
        display.error(f"Search failed: {e}")
        sys.exit(1)
    finally:
        scraper.close_browser()


@app.command()
def scrape(
    url_file: str = typer.Option(
        "spider_output/profile_urls.txt",
        "--urls",
        "-u",
        help="File containing profile URLs (one per line)",
    ),
    output: str = typer.Option(
        "profiles",
        "--output",
        "-o",
        help="Output filename (without extension)",
    ),
    format: str = typer.Option(
        "csv",
        "--format",
        "-f",
        help="Export format (csv, json, excel)",
    ),
):
    """Scrape profile data from URLs."""
    try:
        from pathlib import Path

        # Load URLs
        url_path = Path(url_file)
        if not url_path.exists():
            display.error(f"URL file not found: {url_file}")
            sys.exit(1)

        with open(url_path, "r") as f:
            urls = [line.strip() for line in f if line.strip()]

        display.info(f"Loaded {len(urls)} URLs from {url_file}")

        # Scrape
        profiles = scraper.scrape_profiles(urls, login_first=True)

        if profiles:
            display.success(f"Scraped {len(profiles)} profiles")

            # Export
            from linkedin_spider.utils import exporter
            filepath = exporter.export(profiles, format=format, filename=output)
            display.success(f"Exported to {filepath}")
        else:
            display.warning("No profiles scraped")

    except KeyboardInterrupt:
        display.warning("Interrupted by user")
    except Exception as e:
        logger.error(f"Scraping failed: {e}", exc_info=True)
        display.error(f"Scraping failed: {e}")
        sys.exit(1)
    finally:
        scraper.close_browser()


@app.command()
def version():
    """Show version information."""
    display.console.print("[bold cyan]LinkedIn Spider v0.1.0[/bold cyan]")
    display.console.print("[dim]A professional CLI tool for scraping LinkedIn profiles[/dim]")


if __name__ == "__main__":
    app()
