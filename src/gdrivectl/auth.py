from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from rich.console import Console

from gdrivectl.config import (
    CREDENTIALS_FILE, TOKEN_FILE, CONFIG_FILE, SCOPES, CONFIG_DIR, save_config,
)

console = Console()


def get_credentials() -> Credentials:
    """Load existing credentials or return None."""
    if TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)
        if creds and creds.valid:
            return creds
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
            _save_token(creds)
            return creds
    return None


def authenticate() -> Credentials:
    """Run full OAuth2 flow. Auto-detects and saves owner email."""
    if not CREDENTIALS_FILE.exists():
        console.print(
            f"[red]credentials.json not found at {CREDENTIALS_FILE}[/red]\n"
            "This is a packaging error — the file should be bundled with the app."
        )
        raise SystemExit(1)

    creds = get_credentials()
    if creds:
        console.print("[green]Already authenticated (token valid).[/green]")
        return creds

    flow = InstalledAppFlow.from_client_secrets_file(str(CREDENTIALS_FILE), SCOPES)
    creds = flow.run_local_server(port=0)
    _save_token(creds)

    # Auto-detect and save owner email
    email = _detect_email(creds)
    if email:
        save_config({"owner_email": email})
        console.print(f"[green]Authenticated as {email}. Token saved.[/green]")
    else:
        console.print("[green]Authentication successful. Token saved.[/green]")

    return creds


def require_auth() -> Credentials:
    """Get credentials, failing if not authenticated."""
    creds = get_credentials()
    if not creds:
        console.print("[red]Not authenticated. Run:[/red] gdrivectl auth login")
        raise SystemExit(1)
    return creds


def logout():
    """Remove stored token and config, logging the user out."""
    removed = False
    if TOKEN_FILE.exists():
        TOKEN_FILE.unlink()
        removed = True
    if CONFIG_FILE.exists():
        CONFIG_FILE.unlink()
        removed = True
    if removed:
        console.print("[green]Logged out. Token and config removed.[/green]")
    else:
        console.print("[yellow]Not logged in — nothing to remove.[/yellow]")


def _save_token(creds: Credentials):
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    TOKEN_FILE.write_text(creds.to_json())


def _detect_email(creds: Credentials) -> str | None:
    """Get authenticated user's email from Drive API."""
    try:
        service = build("drive", "v3", credentials=creds)
        about = service.about().get(fields="user(emailAddress)").execute()
        return about["user"]["emailAddress"]
    except Exception:
        return None
