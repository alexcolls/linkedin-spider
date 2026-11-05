"""Display utilities for CLI interface."""

import sys
from pathlib import Path
from typing import List, Optional

from rich.console import Console
from rich.markup import escape
from rich.panel import Panel
from rich.table import Table

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
    banner = load_ascii_art("banner.txt")

    console.clear()
    console.print()

    # Display spider art first
    if spider_art:
        console.print(spider_art, style="bold red")

    # Display banner
    if banner:
        console.print(banner, style="bold blue", justify="center")
    else:
        # Fallback if banner file not found
        console.print(
            Panel(
                "[bold white]LinkedIn Spider[/bold white]\n"
                "[dim]A professional CLI tool for scraping LinkedIn profiles via Google Search[/dim]",
                border_style="green",
            )
        )


def get_key():
    """Get a single keypress from the user."""
    # Unix only. On other platforms this raises, and the menu falls back to typed input.
    import termios
    import tty

    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(sys.stdin.fileno())
        ch = sys.stdin.read(1)
        # Handle arrow keys (ESC sequences)
        if ch == "\x1b":
            ch = sys.stdin.read(2)
        return ch
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)


def show_menu(selected_index: int = 0):
    """Display interactive menu options with selection highlight.

    Args:
        selected_index: Currently selected menu item index
    """
    menu_items = [
        ("1", "🔍  Search & Collect Profile URLs"),
        ("2", "📊  Scrape Profile Data"),
        ("3", "🤝  Auto-Connect to Profiles"),
        ("4", "📁  View/Export Results"),
        ("5", "⚙️   Configure Settings"),
        ("6", "❓  Help"),
        ("0", "🚪  Exit"),
    ]

    menu_table = Table(show_header=False, box=None, padding=(0, 2))
    menu_table.add_column("Selector", style="dim", width=2)
    menu_table.add_column("Option", style="bold cyan", width=4)
    menu_table.add_column("Description", style="white")

    for i, (option, description) in enumerate(menu_items):
        if i == selected_index:
            # Highlight selected item
            menu_table.add_row(
                "▶",
                f"[bold yellow]{option}[/bold yellow]",
                f"[bold yellow]{description}[/bold yellow]",
            )
        else:
            menu_table.add_row(" ", option, description)

    console.print(
        Panel(
            menu_table,
            title="[bold yellow]Main Menu[/bold yellow] [dim](Use ↑↓ arrows and Enter, or type number)[/dim]",
            border_style="yellow",
        )
    )


def _cell(text: str, limit: Optional[int] = None) -> str:
    """Format scraped text for a table: it's untrusted, so it can't carry markup."""
    if not text:
        return "[dim]-[/dim]"
    if limit and len(text) > limit:
        text = text[:limit] + "..."
    return escape(text)


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
            _cell(profile.name),
            _cell(profile.title, limit=50),
            _cell(profile.company, limit=30),
            _cell(profile.location),
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
        table.add_row(str(i), escape(url))

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
   Go through collected profiles and send connection requests.
   You confirm each person, and each run has a limit.
   Requires LinkedIn login. Use responsibly!

[cyan]4. View/Export Results[/cyan]
   View scraped profiles or export them to CSV, JSON, or Excel.

[cyan]5. Configure Settings[/cyan]
   Adjust delays, export formats, etc.
   Edit config.yaml or .env file directly.

[yellow]⚠️  Important Notes:[/yellow]
• LinkedIn's terms prohibit automated access, and it can restrict your account
• Scraped profiles are personal data: GDPR and CCPA may apply
• Keep the delays: they limit the load you put on the site
• Keep your credentials secure

[blue]For more info, visit the documentation[/blue]
""",
            title="[bold green]Help[/bold green]",
            border_style="green",
        )
    )


def interactive_menu_select() -> str:
    """Interactive menu selection with arrow keys.

    Returns:
        Selected option as string ("1", "2", etc.)
    """
    menu_items = ["1", "2", "3", "4", "5", "6", "0"]
    selected_index = 0

    try:
        while True:
            # Clear and redraw menu
            console.clear()
            show_welcome()
            show_menu(selected_index)

            # Get user input
            console.print("\n[dim]Select option: [/dim]", end="")
            key = get_key()

            # Handle arrow keys
            if key == "[A":  # Up arrow
                selected_index = (selected_index - 1) % len(menu_items)
            elif key == "[B":  # Down arrow
                selected_index = (selected_index + 1) % len(menu_items)
            elif key == "\r" or key == "\n":  # Enter
                return menu_items[selected_index]
            elif key in menu_items:  # Direct number input
                return key
            elif key == "\x03":  # Ctrl+C
                raise KeyboardInterrupt
    except Exception:
        # Fallback to text input if arrow keys don't work
        return prompt("Select an option")


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

    return (
        console.input(f"[bold cyan]➤[/bold cyan] {escape(message)}: ").strip()
        or default
        or ""
    )


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
    console.print(f"[green]✓[/green] {escape(message)}")


def error(message: str):
    """Display error message."""
    console.print(f"[red]✗[/red] {escape(message)}")


def warning(message: str):
    """Display warning message."""
    console.print(f"[yellow]⚠[/yellow] {escape(message)}")


def info(message: str):
    """Display info message."""
    console.print(f"[blue]ℹ[/blue] {escape(message)}")
