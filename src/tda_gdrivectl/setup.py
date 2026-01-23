import glob
import json
import shutil
import webbrowser
from pathlib import Path

import questionary
from rich.console import Console
from rich.panel import Panel

from tda_gdrivectl.config import CONFIG_DIR, CREDENTIALS_FILE, save_config

console = Console()

CONSOLE_URL = "https://console.cloud.google.com"


def _open_browser(url):
    """Open URL in browser, handle failures gracefully."""
    try:
        webbrowser.open(url)
        return True
    except Exception:
        console.print(f"[dim]Could not open browser. Go to:[/dim]\n{url}")
        return False


def _step_owner_email():
    """Ask for the owner's Google email."""
    console.print(Panel(
        "Which Google account owns the docs you want to manage?\n"
        "This email will be [bold]protected from accidental revocation[/bold].",
        title="Step 1: Owner Email",
        style="blue",
    ))
    email = questionary.text("Your Google email:").ask()
    if not email or "@" not in email:
        console.print("[red]Invalid email.[/red]")
        return None
    save_config({"owner_email": email})
    console.print(f"[green]\u2713[/green] Owner: [cyan]{email}[/cyan]")
    return email


def _step_create_project():
    """Guide user to create a GCP project in the browser."""
    console.print(Panel(
        "1. Click [bold]Create Project[/bold] (or select an existing one)\n"
        "2. Project name: anything you want (e.g. [bold]gdrivectl[/bold])\n"
        "3. Click [bold]Create[/bold]\n"
        "4. Wait for the notification that the project is ready",
        title="Step 2: Create Google Cloud Project",
        style="blue",
    ))
    _open_browser(f"{CONSOLE_URL}/projectcreate")
    questionary.confirm("Project created?", default=True).ask()
    project_id = questionary.text(
        "Enter your project ID (shown under the project name in the console):"
    ).ask()
    if not project_id:
        return None
    project_id = project_id.strip()
    console.print(f"[green]\u2713[/green] Project: [cyan]{project_id}[/cyan]")
    save_config({"gcp_project_id": project_id})
    return project_id


def _step_enable_api(project_id):
    """Guide user to enable Google Drive API."""
    console.print(Panel(
        "1. Make sure your project is selected in the top bar\n"
        "2. Click [bold]Enable[/bold]",
        title="Step 3: Enable Google Drive API",
        style="blue",
    ))
    _open_browser(
        f"{CONSOLE_URL}/apis/library/drive.googleapis.com?project={project_id}"
    )
    questionary.confirm("Drive API enabled?", default=True).ask()
    console.print("[green]\u2713[/green] Drive API enabled")


def _step_consent_screen(project_id):
    """Guide user through OAuth consent screen setup."""
    console.print(Panel(
        "1. Select [bold]External[/bold] user type, click Create\n"
        "2. App name: [bold]tda-gdrivectl[/bold]\n"
        "3. User support email: [bold]your email[/bold]\n"
        "4. Developer contact email: [bold]your email[/bold]\n"
        "5. Click [bold]Save and Continue[/bold] through all remaining steps\n"
        "6. On the Summary page, click [bold]Back to Dashboard[/bold]\n"
        "7. Click [bold]Publish App[/bold] (or add your email under Test Users)",
        title="Step 4: OAuth Consent Screen",
        style="blue",
    ))
    _open_browser(
        f"{CONSOLE_URL}/apis/credentials/consent?project={project_id}"
    )
    questionary.confirm("Consent screen configured?", default=True).ask()
    console.print("[green]\u2713[/green] Consent screen configured")


def _step_create_credentials(project_id):
    """Guide user to create OAuth client credentials and place them."""
    if CREDENTIALS_FILE.exists():
        if not questionary.confirm(
            f"credentials.json already exists at {CREDENTIALS_FILE}. Replace?",
            default=False,
        ).ask():
            console.print("[green]\u2713[/green] Using existing credentials")
            return True

    console.print(Panel(
        "1. Click [bold]+ Create Credentials[/bold] at the top\n"
        "2. Select [bold]OAuth client ID[/bold]\n"
        "3. Application type: [bold]Desktop app[/bold]\n"
        "4. Name: [bold]tda-gdrivectl[/bold]\n"
        "5. Click [bold]Create[/bold]\n"
        "6. Click [bold]Download JSON[/bold] on the popup",
        title="Step 5: Create OAuth Credentials",
        style="blue",
    ))
    _open_browser(
        f"{CONSOLE_URL}/apis/credentials?project={project_id}"
    )

    console.print("\n[dim]After downloading, press Enter to auto-detect "
                   "or paste the file path.[/dim]")
    downloads = Path.home() / "Downloads"

    creds_input = questionary.text(
        "Path to downloaded JSON (or press Enter to scan Downloads):",
        default=str(downloads),
    ).ask()
    if not creds_input:
        return False

    creds_path = Path(creds_input).expanduser()

    # If directory, find most recent client_secret file
    if creds_path.is_dir():
        matches = sorted(
            glob.glob(str(creds_path / "client_secret*.json")),
            key=lambda f: Path(f).stat().st_mtime,
            reverse=True,
        )
        if not matches:
            console.print(f"[red]No client_secret*.json found in {creds_path}[/red]")
            return False
        creds_path = Path(matches[0])
        console.print(f"[dim]Found: {creds_path.name}[/dim]")

    if not creds_path.exists():
        console.print(f"[red]File not found: {creds_path}[/red]")
        return False

    # Validate JSON structure
    try:
        data = json.loads(creds_path.read_text())
        if "installed" not in data and "web" not in data:
            console.print("[red]Invalid credentials file (no 'installed' or 'web' key).[/red]")
            return False
    except (json.JSONDecodeError, OSError):
        console.print("[red]Cannot read file as JSON.[/red]")
        return False

    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    shutil.copy2(str(creds_path), str(CREDENTIALS_FILE))
    console.print(f"[green]\u2713[/green] Credentials saved to {CREDENTIALS_FILE}")
    return True


def _step_authenticate():
    """Run the OAuth flow."""
    if not CREDENTIALS_FILE.exists():
        console.print(f"[red]credentials.json not found at {CREDENTIALS_FILE}[/red]")
        return False
    console.print("\n[dim]Opening browser for Google authorization...[/dim]")
    from tda_gdrivectl.auth import authenticate
    authenticate()
    return True


def run_setup():
    """Main setup flow — called by the CLI `setup` command."""
    console.print(Panel(
        "[bold]tda-gdrivectl Setup[/bold]\n"
        "5 steps, all in your browser. No extra tools needed.",
        style="blue",
    ))

    # 1. Owner email
    owner = _step_owner_email()
    if not owner:
        raise SystemExit(1)

    # 2. GCP project
    project_id = _step_create_project()
    if not project_id:
        raise SystemExit(1)

    # 3. Enable Drive API
    _step_enable_api(project_id)

    # 4. Consent screen
    _step_consent_screen(project_id)

    # 5. OAuth credentials
    creds_ok = _step_create_credentials(project_id)

    # 6. Authenticate
    if creds_ok and _step_authenticate():
        console.print(Panel(
            "[bold green]Setup complete![/bold green]\n"
            "Run [bold]tda-gdrivectl list[/bold] to see your docs.",
            style="green",
        ))
    else:
        console.print(
            f"\n[yellow]Place credentials.json at {CREDENTIALS_FILE}[/yellow]\n"
            "Then run: [bold]tda-gdrivectl auth[/bold]"
        )
