# tda-gdrivectl

CLI tool to manage Google Docs permissions in bulk — grant, revoke, audit.

Interactive prompts, dry-run by default, owner protection built in.

## Prerequisites

- Python 3.10+
- [gcloud CLI](https://cloud.google.com/sdk/docs/install) (for automated setup)

## Install

### Option 1: pipx (recommended for CLI tools)

```bash
pipx install git+https://github.com/TheDarkArtist/tda-gdrivectl.git
```

This installs `tda-gdrivectl` in an isolated environment and makes it available globally.

### Option 2: pip + venv

```bash
git clone https://github.com/TheDarkArtist/tda-gdrivectl.git
cd tda-gdrivectl
python3 -m venv .venv
source .venv/bin/activate    # Linux/macOS
# .venv\Scripts\activate     # Windows
pip install .
```

### Option 3: pip (dev mode)

```bash
git clone https://github.com/TheDarkArtist/tda-gdrivectl.git
cd tda-gdrivectl
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

> **Note:** If you installed via Option 2 or 3, make sure the venv is activated before running commands, or use the full path `.venv/bin/tda-gdrivectl`.

## Quick Start

```bash
# 1. Run guided setup (creates GCP project, configures OAuth — all interactive)
tda-gdrivectl setup

# 2. List your Google Docs
tda-gdrivectl list

# 3. Revoke access (dry-run first, then --execute)
tda-gdrivectl revoke
tda-gdrivectl revoke --execute
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

## Commands

| Command | Description |
|---|---|
| `tda-gdrivectl setup` | One-time GCP project + OAuth setup (interactive) |
| `tda-gdrivectl auth` | Re-authenticate if token expires |
| `tda-gdrivectl list` | List all your Google Docs |
| `tda-gdrivectl list --shared-only` | Show only docs shared with others |
| `tda-gdrivectl inspect` | Inspect permissions on a specific doc |
| `tda-gdrivectl grant` | Grant access (dry-run) |
| `tda-gdrivectl grant --execute` | Grant access (for real) |
| `tda-gdrivectl revoke` | Revoke access (dry-run) |
| `tda-gdrivectl revoke --execute` | Revoke access (for real) |
| `tda-gdrivectl audit` | Export all permissions to CSV |

## Safety

- **Dry-run by default** — grant/revoke show what would happen without `--execute`
- **Owner protection** — your email is never shown as revocable, configured during setup
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
