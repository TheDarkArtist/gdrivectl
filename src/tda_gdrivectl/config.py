from pathlib import Path

CONFIG_DIR = Path.home() / ".config" / "tda-gdrivectl"
CREDENTIALS_FILE = CONFIG_DIR / "credentials.json"
TOKEN_FILE = CONFIG_DIR / "token.json"
PROJECT_DIR = Path(__file__).resolve().parent.parent.parent
LOGS_DIR = PROJECT_DIR / "logs"

OWNER_EMAIL = "kushagrasharma.dev@gmail.com"

SCOPES = ["https://www.googleapis.com/auth/drive"]

DRIVE_FIELDS = "files(id,name,modifiedTime,permissions(id,type,role,emailAddress))"
DOCS_MIME_TYPE = "application/vnd.google-apps.document"
DOCS_QUERY = f"mimeType='{DOCS_MIME_TYPE}' and 'me' in owners"

BATCH_SIZE = 100
