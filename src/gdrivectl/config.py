import json
from pathlib import Path

# Bundled with the package — public OAuth client ID (safe to ship)
CREDENTIALS_FILE = Path(__file__).parent / "credentials.json"

# Per-user config + tokens
CONFIG_DIR = Path.home() / ".config" / "gdrivectl"
CONFIG_FILE = CONFIG_DIR / "config.json"
TOKEN_FILE = CONFIG_DIR / "token.json"

PROJECT_DIR = Path(__file__).resolve().parent.parent.parent
LOGS_DIR = PROJECT_DIR / "logs"

SCOPES = ["https://www.googleapis.com/auth/drive"]

DRIVE_FIELDS = "files(id,name,modifiedTime,permissions(id,type,role,emailAddress))"
DOCS_MIME_TYPE = "application/vnd.google-apps.document"
DOCS_QUERY = f"mimeType='{DOCS_MIME_TYPE}' and 'me' in owners"

BATCH_SIZE = 100


def load_config() -> dict:
    """Load config from disk. Returns empty dict if missing."""
    if CONFIG_FILE.exists():
        return json.loads(CONFIG_FILE.read_text())
    return {}


def save_config(data: dict):
    """Save config to disk (merges with existing)."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    existing = load_config()
    existing.update(data)
    CONFIG_FILE.write_text(json.dumps(existing, indent=2))


def get_owner_email() -> str | None:
    """Get owner email from config."""
    return load_config().get("owner_email")
