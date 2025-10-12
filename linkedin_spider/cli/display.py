"""Display utilities for CLI interface."""

from pathlib import Path
from typing import List, Optional

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from linkedin_spider.models import Profile


console = Console()


def load_ascii_art(filename: str) -> str:
    """
    Load ASCII art from file.

    Args:
        filename: Name of ASCII art file

    Returns:
        ASCII art content
    """
    try:
        assets_dir = Path(__file__).parent.parent / "assets"
        filepath = assets_dir / filename

        with open(filepath, "r") as f:
            return f.read()
    except Exception:
        return ""


def show_welcome():
    """Display welcome screen with ASCII art."""
    spider_art = load_ascii_art("spider.txt")
    linkedin_art = load_ascii_art("linkedin.txt")

    console.clear()
    console.print()

    # Spider and LinkedIn logos side by side
    if spider_art:
        console.print(spider_art, style="bold cyan", justify="center")

    console.print()

    if linkedin_art:
        console.print(linkedin_art, style="bold blue", justify="center")

    console.print()
    console.print(
        Panel(
            "[bold white]A professional CLI tool for scraping LinkedIn profiles via Google Search[/bold white]\n"
            "[dim]Made with ❤️  for data professionals[/dim]",
            title="[bold green]LinkedIn Spider[/bold green]",
            border_style="green",
        )
    )
    console.print()


def show_menu():
    """Display interactive menu options."""
    menu_table = Table(show_header=False, box=None, padding=(0, 2))
    menu_table.add_column("Option", style="bold cyan", width=4)
    menu_table.add_column("Description", style="white")

    menu_table.add_row("1", "🔍  Search & Collect Profile URLs")
    menu_table.add_row("2", "📊  Scrape Profile Data")
    menu_table.add_row("3", "🤝  Auto-Connect to Profiles")
    menu_table.add_row("4", "📁  View/Export Results")
    menu_table.add_row("5", "⚙️   Configure Settings")
    menu_table.add_row("6", "❓  Help")
    menu_table.add_row("0", "🚪  Exit")

    console.print(
        Panel(
            menu_table,
            title="[bold yellow]Main Menu[/bold yellow]",
            border_style="yellow",
        )
    )


def show_profiles_table(profiles: List[Profile], max_rows: Optional[int] = 20):
    """
    Display profiles in a formatted table.

    Args:
        profiles: List of profiles to display
        max_rows: Maximum number of rows to display
    """
    if not profiles:
        console.print("[yellow]No profiles to display[/yellow]")
        return

    table = Table(title=f"LinkedIn Profiles ({len(profiles)} total)")

    table.add_column("#", style="dim", width=4)
    table.add_column("Name", style="cyan", no_wrap=False)
    table.add_column("Title", style="green", no_wrap=False)
    table.add_column("Company", style="blue", no_wrap=False)
    table.add_column("Location", style="magenta", no_wrap=False)
    table.add_column("Followers", justify="right", style="yellow")

    # Show limited rows
    display_profiles = profiles[:max_rows] if max_rows else profiles

    for i, profile in enumerate(display_profiles, 1):
        table.add_row(
            str(i),
            profile.name or "[dim]Unknown[/dim]",
            profile.title[:50] + "..." if len(profile.title) > 50 else profile.title or "[dim]-[/dim]",
            profile.company[:30] + "..." if len(profile.company) > 30 else profile.company or "[dim]-[/dim]",
            profile.location or "[dim]-[/dim]",
            str(profile.followers) if profile.followers > 0 else "[dim]-[/dim]",
        )

    console.print(table)

    if max_rows and len(profiles) > max_rows:
        console.print(
            f"\n[dim]Showing {max_rows} of {len(profiles)} profiles. "
            f"Export to see all.[/dim]"
        )


def show_urls_list(urls: List[str], max_rows: Optional[int] = 20):
    """
    Display URLs in a formatted list.

    Args:
        urls: List of URLs to display
        max_rows: Maximum number of URLs to display
    """
    if not urls:
        console.print("[yellow]No URLs to display[/yellow]")
        return

    table = Table(title=f"Profile URLs ({len(urls)} total)")
    table.add_column("#", style="dim", width=4)
    table.add_column("URL", style="cyan")

    display_urls = urls[:max_rows] if max_rows else urls

    for i, url in enumerate(display_urls, 1):
        table.add_row(str(i), url)

    console.print(table)

    if max_rows and len(urls) > max_rows:
        console.print(
            f"\n[dim]Showing {max_rows} of {len(urls)} URLs. "
            f"Use scrape command to process all.[/dim]"
        )


def show_help():
    """Display help information."""
    console.print()
    console.print(
        Panel(
            """[bold]LinkedIn Spider Help[/bold]

[cyan]1. Search & Collect Profile URLs[/cyan]
   Use Google Search to find LinkedIn profiles matching your keywords.
   Example: Enter keywords like "Python Developer", "San Francisco"

[cyan]2. Scrape Profile Data[/cyan]
   Extract detailed information from collected profile URLs.
   Requires LinkedIn login credentials in .env file.

[cyan]3. Auto-Connect to Profiles[/cyan]
   Automatically send connection requests to profiles.
   Requires LinkedIn login. Use responsibly!

[cyan]4. View/Export Results[/cyan]
   View scraped profiles or export them to CSV, JSON, or Excel.

[cyan]5. Configure Settings[/cyan]
   Adjust delays, VPN settings, export formats, etc.
   Edit config.yaml or .env file directly.

[yellow]⚠️  Important Notes:[/yellow]
• Respect LinkedIn's Terms of Service
• Use delays to avoid detection
• Consider using VPN for IP rotation
• Keep your credentials secure

[blue]For more info, visit the documentation[/blue]
""",
            title="[bold green]Help[/bold green]",
            border_style="green",
        )
    )


def prompt(message: str, default: Optional[str] = None) -> str:
    """
    Prompt user for input.

    Args:
        message: Prompt message
        default: Default value

    Returns:
        User input
    """
    if default:
        message = f"{message} [{default}]"

    return console.input(f"[bold cyan]➤[/bold cyan] {message}: ").strip() or default or ""


def confirm(message: str, default: bool = False) -> bool:
    """
    Prompt user for yes/no confirmation.

    Args:
        message: Confirmation message
        default: Default value

    Returns:
        True if confirmed, False otherwise
    """
    suffix = " [Y/n]" if default else " [y/N]"
    response = prompt(message + suffix).lower()

    if not response:
        return default

    return response in ("y", "yes")


def success(message: str):
    """Display success message."""
    console.print(f"[green]✓[/green] {message}")


def error(message: str):
    """Display error message."""
    console.print(f"[red]✗[/red] {message}")


def warning(message: str):
    """Display warning message."""
    console.print(f"[yellow]⚠[/yellow] {message}")


def info(message: str):
    """Display info message."""
    console.print(f"[blue]ℹ[/blue] {message}")
