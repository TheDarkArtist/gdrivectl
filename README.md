# tda-gdrivectl

CLI tool to manage Google Docs permissions in bulk — grant, revoke, audit.

## Google Cloud Setup (one-time)

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project (or use existing)
3. Enable **Google Drive API** (APIs & Services → Library)
4. Create **OAuth 2.0 credentials** (APIs & Services → Credentials → Create → OAuth client ID → Desktop app)
5. Download the JSON file
6. Save it to `~/.config/tda-gdrivectl/credentials.json`

## Install

```bash
cd ~/Workspace/Projects/tda-gdrivectl
pip install -e .
```

## Usage

```bash
# Authenticate (opens browser for OAuth)
tda-gdrivectl auth

# List all your Google Docs
tda-gdrivectl list
tda-gdrivectl list --shared-only

# Inspect permissions on a specific doc
tda-gdrivectl inspect
tda-gdrivectl inspect --doc-id <id>

# Grant access (interactive)
tda-gdrivectl grant              # dry-run (default)
tda-gdrivectl grant --execute    # actually grant

# Revoke access (interactive)
tda-gdrivectl revoke             # dry-run (default)
tda-gdrivectl revoke --execute   # actually revoke

# Export all permissions to CSV
tda-gdrivectl audit
```

## Safety

- **Dry-run by default** — grant/revoke print what would happen without `--execute`
- **Owner protection** — your email is never shown as revocable
- **Confirmation prompt** — always confirms before executing
- **Audit log** — every run logs to `logs/`
