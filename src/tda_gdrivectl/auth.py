from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from rich.console import Console

from tda_gdrivectl.config import CREDENTIALS_FILE, TOKEN_FILE, SCOPES, CONFIG_DIR

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
    """Run full OAuth2 flow."""
    if not CREDENTIALS_FILE.exists():
        console.print(
            f"[red]credentials.json not found at {CREDENTIALS_FILE}[/red]\n"
            "Download it from Google Cloud Console and place it there."
        )
        raise SystemExit(1)

    creds = get_credentials()
    if creds:
        console.print("[green]Already authenticated (token valid).[/green]")
        return creds

    flow = InstalledAppFlow.from_client_secrets_file(str(CREDENTIALS_FILE), SCOPES)
    creds = flow.run_local_server(port=0)
    _save_token(creds)
    console.print("[green]Authentication successful. Token saved.[/green]")
    return creds


def require_auth() -> Credentials:
    """Get credentials, failing if not authenticated."""
    creds = get_credentials()
    if not creds:
        console.print("[red]Not authenticated. Run:[/red] tda-gdrivectl auth")
        raise SystemExit(1)
    return creds


def _save_token(creds: Credentials):
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    TOKEN_FILE.write_text(creds.to_json())
