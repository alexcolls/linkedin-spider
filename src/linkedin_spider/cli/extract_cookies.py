"""Interactive script to extract LinkedIn cookies after manual login."""

import sys
import time
from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel

from linkedin_spider.core.browser import browser
from linkedin_spider.utils.session import session_manager
from linkedin_spider.utils.logger import logger

console = Console()
app = typer.Typer()


@app.command()
def extract(
    output: str = typer.Option(
        "data/linkedin_cookies.pkl",
        "--output",
        "-o",
        help="Path to save cookies"
    ),
    k8s_secret: bool = typer.Option(
        False,
        "--k8s-secret",
        "-k",
        help="Also generate Kubernetes Secret YAML"
    ),
    secret_path: str = typer.Option(
        "k8s/linkedin-cookies-secret.yaml",
        "--secret-path",
        "-s",
        help="Path to save Kubernetes Secret YAML"
    ),
):
    """
    Extract LinkedIn cookies after manual login.
    
    This script opens a browser where you can manually log in to LinkedIn,
    solve any CAPTCHA, and handle 2FA. Once authenticated, cookies are extracted.
    """
    console.print(Panel.fit(
        "[bold cyan]LinkedIn Cookie Extraction Wizard[/bold cyan]\n\n"
        "This tool will:\n"
        "1. Open a Chrome browser\n"
        "2. Navigate to LinkedIn\n"
        "3. Wait for you to manually log in\n"
        "4. Extract and save your session cookies\n"
        "5. Optionally create a Kubernetes Secret\n\n"
        "[yellow]⚠️  Keep your cookies secure - they provide full account access![/yellow]",
        title="🔐 Cookie Extractor",
        border_style="cyan"
    ))
    
    try:
        # Start browser
        console.print("\n[cyan]Starting browser...[/cyan]")
        browser.start()
        
        # Navigate to LinkedIn
        console.print("[cyan]Navigating to LinkedIn...[/cyan]")
        browser.driver.get("https://www.linkedin.com/login")
        
        # Wait for user to log in
        console.print("\n" + "="*60)
        console.print("[bold yellow]MANUAL ACTION REQUIRED[/bold yellow]")
        console.print("="*60)
        console.print(
            "\n📋 [bold]Please complete the following steps:[/bold]\n\n"
            "   1. Log in to your LinkedIn account in the browser\n"
            "   2. Complete any CAPTCHA challenges\n"
            "   3. Complete 2FA if prompted\n"
            "   4. Wait until you see your LinkedIn feed\n"
            "   5. Return here and press Enter\n"
        )
        
        input("Press Enter when you are logged in and on the LinkedIn feed...")
        
        # Validate session
        console.print("\n[cyan]Validating session...[/cyan]")
        if not session_manager.validate_session(browser.driver):
            console.print("[bold red]❌ Session validation failed![/bold red]")
            console.print("[yellow]Make sure you're logged in and on the LinkedIn feed.[/yellow]")
            sys.exit(1)
        
        # Extract cookies
        console.print("[cyan]Extracting cookies...[/cyan]")
        cookies = session_manager.extract_cookies(browser.driver)
        
        if not cookies:
            console.print("[bold red]❌ Failed to extract cookies![/bold red]")
            sys.exit(1)
        
        # Save cookies
        output_path = Path(output)
        console.print(f"[cyan]Saving cookies to {output_path}...[/cyan]")
        
        if session_manager.save_cookies(cookies, output_path):
            console.print(f"[bold green]✅ Cookies saved successfully to {output_path}[/bold green]")
            console.print(f"[dim]Total cookies: {len(cookies)}[/dim]")
        else:
            console.print("[bold red]❌ Failed to save cookies![/bold red]")
            sys.exit(1)
        
        # Optionally create Kubernetes Secret
        if k8s_secret:
            console.print(f"\n[cyan]Creating Kubernetes Secret YAML...[/cyan]")
            k8s_path = Path(secret_path)
            
            if session_manager.create_k8s_secret_yaml(cookies, k8s_path):
                console.print(f"[bold green]✅ Kubernetes Secret created at {k8s_path}[/bold green]")
                console.print(
                    f"\n[yellow]To apply the secret:[/yellow]\n"
                    f"  kubectl apply -f {k8s_path}"
                )
            else:
                console.print("[bold red]❌ Failed to create Kubernetes Secret![/bold red]")
        
        # Final instructions
        console.print("\n" + "="*60)
        console.print("[bold green]✨ Cookie Extraction Complete![/bold green]")
        console.print("="*60)
        console.print(
            f"\n[bold]Next steps:[/bold]\n\n"
            f"   For Docker:\n"
            f"   • Copy {output_path} to your worker containers\n"
            f"   • Set SESSION_COOKIE_PATH environment variable\n\n"
            f"   For Kubernetes:\n"
            f"   • Apply the secret: kubectl apply -f {secret_path}\n"
            f"   • Workers will automatically use the cookies\n\n"
            f"[yellow]⚠️  Security reminder:[/yellow]\n"
            f"   • Keep cookie files secure (add to .gitignore)\n"
            f"   • Rotate cookies periodically\n"
            f"   • Never commit cookies to version control\n"
        )
        
    except KeyboardInterrupt:
        console.print("\n[yellow]⚠️  Interrupted by user[/yellow]")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Cookie extraction failed: {e}", exc_info=True)
        console.print(f"[bold red]❌ Error: {e}[/bold red]")
        sys.exit(1)
    finally:
        # Close browser
        console.print("\n[cyan]Closing browser...[/cyan]")
        browser.stop()
        console.print("[green]Done![/green]\n")


if __name__ == "__main__":
    app()
