# tda-gdrivectl

CLI tool to manage Google Docs permissions in bulk — grant, revoke, audit.

Interactive prompts, dry-run by default, owner protection built in.

## Prerequisites

- Python 3.10+
- [gcloud CLI](https://cloud.google.com/sdk/docs/install) (for automated setup)

## Install

```bash
git clone https://github.com/TheDarkArtist/tda-gdrivectl.git
cd tda-gdrivectl
pip install -e .
```

Or install directly:
```bash
pip install git+https://github.com/TheDarkArtist/tda-gdrivectl.git
```

## First-time Setup

```bash
tda-gdrivectl setup
```

This interactively walks you through:
1. gcloud login
2. Owner email configuration (protected from accidental revocation)
3. GCP project creation (or selection)
4. Enabling Google Drive API
5. OAuth consent screen configuration (opens browser)
6. OAuth client credential creation (opens browser, auto-detects download)
7. OAuth authentication flow

All config is stored in `~/.config/tda-gdrivectl/`.

## Usage

```bash
# Re-authenticate if token expires
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

- **Dry-run by default** — grant/revoke show what would happen without `--execute`
- **Owner protection** — your email is never shown as revocable, hardcoded during setup
- **Confirmation prompt** — always confirms before executing changes
- **Audit log** — every grant/revoke run logs results to `logs/`

## Config Location

```
~/.config/tda-gdrivectl/
├── config.json        # owner email, settings
├── credentials.json   # OAuth client credentials (from GCP)
└── token.json         # OAuth token (auto-generated)
```

## License

MIT
