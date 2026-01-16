# tda-gdrivectl

CLI tool to manage Google Docs permissions in bulk — grant, revoke, audit.

## Prerequisites

- Python 3.10+
- [gcloud CLI](https://cloud.google.com/sdk/docs/install) (for automated setup)

## Install

```bash
cd ~/Workspace/Projects/tda-gdrivectl
pip install -e .
```

## First-time Setup

```bash
tda-gdrivectl setup
```

This interactively walks you through:
1. gcloud login
2. GCP project creation (or selection)
3. Enabling Drive API
4. OAuth consent screen configuration (opens browser)
5. OAuth client credential creation (opens browser)
6. Auto-detects downloaded `credentials.json` from `~/Downloads`
7. Runs the OAuth auth flow

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

- **Dry-run by default** — grant/revoke print what would happen without `--execute`
- **Owner protection** — your email is never shown as revocable
- **Confirmation prompt** — always confirms before executing
- **Audit log** — every run logs to `logs/`
