# tda-gdrivectl

CLI tool to manage Google Docs permissions in bulk — grant, revoke, audit.

Interactive prompts, dry-run by default, owner protection built in.

## Install

### pipx (recommended)

```bash
pipx install git+https://github.com/TheDarkArtist/tda-gdrivectl.git
```

### pip

```bash
git clone https://github.com/TheDarkArtist/tda-gdrivectl.git
cd tda-gdrivectl
python3 -m venv .venv
source .venv/bin/activate
pip install .
```

## Quick Start

```bash
# Authenticate (opens browser, one-time)
tda-gdrivectl auth

# List your Google Docs
tda-gdrivectl list

# Revoke access
tda-gdrivectl revoke              # dry-run
tda-gdrivectl revoke --execute    # for real
```

That's it. OAuth credentials are bundled — no GCP setup needed.

## Commands

| Command | Description |
|---|---|
| `tda-gdrivectl auth` | Authenticate with Google (opens browser, one-time) |
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
- **Owner protection** — your email (auto-detected) is never shown as revocable
- **Confirmation prompt** — always confirms before executing changes
- **Audit log** — every grant/revoke run logs results to `logs/`

## How It Works

OAuth client credentials are bundled with the package (this is standard practice
for desktop/CLI apps — the client ID identifies the app, not your data). When you
run `tda-gdrivectl auth`, it opens your browser for Google's consent screen where
you authorize the app. Your access token is stored locally at
`~/.config/tda-gdrivectl/token.json` and never leaves your machine.

## License

MIT
