import glob
import json
import shutil
import subprocess
import webbrowser
from pathlib import Path

import questionary
from rich.console import Console
from rich.panel import Panel

from tda_gdrivectl.config import CONFIG_DIR, CREDENTIALS_FILE, save_config

console = Console()


def _run(cmd, capture=True):
    """Run a shell command. Returns stdout on success, None on failure."""
    try:
        r = subprocess.run(cmd, capture_output=capture, text=True, check=True)
        return r.stdout.strip() if capture else ""
    except (FileNotFoundError, subprocess.CalledProcessError):
        return None


def _check_gcloud():
    if shutil.which("gcloud"):
        console.print("[green]\u2713[/green] gcloud CLI found")
        return True
    console.print("[red]gcloud CLI not installed.[/red]")
    console.print("Install: https://cloud.google.com/sdk/docs/install")
    if questionary.confirm("Open install page?", default=True).ask():
        webbrowser.open("https://cloud.google.com/sdk/docs/install")
    console.print("After installing, run [bold]tda-gdrivectl setup[/bold] again.")
    return False


def _gcloud_login():
    """Ensure gcloud is logged in. Returns account email or None."""
    account = _run(["gcloud", "config", "get-value", "account"])
    if account and "@" in account:
        console.print(f"[green]\u2713[/green] Logged in as [cyan]{account}[/cyan]")
        if questionary.confirm(f"Continue as {account}?", default=True).ask():
            return account

    console.print("[dim]Opening browser for Google login...[/dim]")
    _run(["gcloud", "auth", "login"], capture=False)
    account = _run(["gcloud", "config", "get-value", "account"])
    if account and "@" in account:
        console.print(f"[green]\u2713[/green] Logged in as [cyan]{account}[/cyan]")
        return account
    return None


def _create_or_select_project():
    """Create a new GCP project or select existing one. Returns project ID."""
    action = questionary.select(
        "GCP project:",
        choices=[
            questionary.Choice("Create new project", "new"),
            questionary.Choice("Use existing project", "existing"),
        ],
    ).ask()

    if action == "new":
        pid = questionary.text("Project ID (lowercase, hyphens ok):", default="tda-gdrivectl").ask()
        if not pid:
            return None
        console.print(f"[dim]Creating project '{pid}'...[/dim]")
        result = _run(["gcloud", "projects", "create", pid])
        if result is None:
            console.print("[yellow]Creation failed — project may already exist.[/yellow]")
            if not questionary.confirm(f"Try using '{pid}' anyway?", default=True).ask():
                return None
        else:
            console.print(f"[green]\u2713[/green] Project created: {pid}")
        _run(["gcloud", "config", "set", "project", pid])
        return pid

    # List existing projects
    out = _run(["gcloud", "projects", "list", "--format=value(projectId)"])
    if not out:
        console.print("[red]No projects found.[/red]")
        return None
    projects = [p.strip() for p in out.splitlines() if p.strip()]
    pid = questionary.select("Select project:", choices=projects).ask()
    if pid:
        _run(["gcloud", "config", "set", "project", pid])
        console.print(f"[green]\u2713[/green] Project: {pid}")
    return pid


def _enable_drive_api(project_id):
    """Enable Google Drive API on the project."""
    console.print("[dim]Enabling Drive API...[/dim]")
    if _run(["gcloud", "services", "enable", "drive.googleapis.com", f"--project={project_id}"]) is not None:
        console.print("[green]\u2713[/green] Drive API enabled")
        return
    console.print("[yellow]Auto-enable failed. Opening browser...[/yellow]")
    url = f"https://console.cloud.google.com/apis/library/drive.googleapis.com?project={project_id}"
    webbrowser.open(url)
    questionary.confirm("Done enabling Drive API?", default=True).ask()


def _setup_consent_screen(project_id):
    """Guide user through OAuth consent screen setup."""
    console.print(Panel(
        "[bold]OAuth Consent Screen[/bold]\n\n"
        "1. User type: [bold]External[/bold]\n"
        "2. App name: [bold]tda-gdrivectl[/bold]\n"
        "3. Support email + developer email: [bold]your email[/bold]\n"
        "4. Scopes: skip (no scopes needed here)\n"
        "5. Test users: [bold]add your Google email[/bold]\n"
        "6. Save through all steps",
        title="Configure in browser",
        style="blue",
    ))
    url = f"https://console.cloud.google.com/apis/credentials/consent?project={project_id}"
    webbrowser.open(url)
    questionary.confirm("Consent screen configured?", default=True).ask()
    console.print("[green]\u2713[/green] Consent screen done")


def _setup_credentials(project_id):
    """Guide user through OAuth client creation and place credentials.json."""
    if CREDENTIALS_FILE.exists():
        if not questionary.confirm(
            f"credentials.json already exists at {CREDENTIALS_FILE}. Replace?",
            default=False,
        ).ask():
            console.print("[green]\u2713[/green] Using existing credentials")
            return True

    console.print(Panel(
        "[bold]Create OAuth Client[/bold]\n\n"
        "1. Application type: [bold]Desktop app[/bold]\n"
        "2. Name: [bold]tda-gdrivectl[/bold]\n"
        "3. Click [bold]Create[/bold]\n"
        "4. Click [bold]Download JSON[/bold] on the popup",
        title="Configure in browser",
        style="blue",
    ))
    url = f"https://console.cloud.google.com/apis/credentials/oauthclient?project={project_id}"
    webbrowser.open(url)

    console.print("\n[dim]After downloading the JSON, provide its location below.[/dim]")
    downloads = Path.home() / "Downloads"

    creds_input = questionary.text(
        "Path to downloaded JSON (or directory to auto-detect):",
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


def run_setup():
    """Main setup flow — called by the CLI `setup` command."""
    console.print(Panel(
        "[bold]tda-gdrivectl Setup[/bold]\n"
        "Creates GCP project, enables Drive API, configures OAuth.",
        style="blue",
    ))

    # 1. gcloud CLI
    if not _check_gcloud():
        raise SystemExit(1)

    # 2. Login
    account = _gcloud_login()
    if not account:
        console.print("[red]Login failed.[/red]")
        raise SystemExit(1)

    # 3. Owner email (used for safety — never revoke your own access)
    owner_email = questionary.text(
        "Your Google email (owner — will be protected from revocation):",
        default=account,
    ).ask()
    if not owner_email:
        raise SystemExit(1)
    save_config({"owner_email": owner_email})
    console.print(f"[green]\u2713[/green] Owner email saved: [cyan]{owner_email}[/cyan]")

    # 4. Project
    project_id = _create_or_select_project()
    if not project_id:
        console.print("[red]No project selected.[/red]")
        raise SystemExit(1)

    # 5. Enable API
    _enable_drive_api(project_id)

    # 6. Consent screen
    _setup_consent_screen(project_id)

    # 7. Credentials
    creds_ok = _setup_credentials(project_id)

    # 8. Auth flow
    if creds_ok and CREDENTIALS_FILE.exists():
        console.print("\n[dim]Running OAuth flow...[/dim]")
        from tda_gdrivectl.auth import authenticate
        authenticate()
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
