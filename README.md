# gdrivectl

CLI tool to manage Google Docs permissions in bulk — grant, revoke, audit.

Interactive prompts, dry-run by default, owner protection built in.

## Install

### pipx (recommended)

```bash
pipx install git+https://github.com/TheDarkArtist/gdrivectl.git
```

### pip

```bash
git clone https://github.com/TheDarkArtist/gdrivectl.git
cd gdrivectl
python3 -m venv .venv
source .venv/bin/activate
pip install .
```

## Quick Start

```bash
# Authenticate (opens browser, one-time)
gdrivectl auth login

# List your Google Docs
gdrivectl list

# Revoke access
gdrivectl revoke              # dry-run
gdrivectl revoke --execute    # for real
```

That's it. OAuth credentials are bundled — no GCP setup needed.

## Commands

| Command | Description |
|---|---|
| `gdrivectl auth login` | Authenticate with Google (opens browser, one-time) |
| `gdrivectl auth logout` | Log out and remove stored credentials |
| `gdrivectl auth status` | Check current authentication status |
| `gdrivectl list` | List all your Google Docs |
| `gdrivectl list --shared-only` | Show only docs shared with others |
| `gdrivectl inspect` | Inspect permissions on a specific doc |
| `gdrivectl grant` | Grant access (dry-run) |
| `gdrivectl grant --execute` | Grant access (for real) |
| `gdrivectl revoke` | Revoke access (dry-run) |
| `gdrivectl revoke --execute` | Revoke access (for real) |
| `gdrivectl audit` | Export all permissions to CSV |

## Safety

- **Dry-run by default** — grant/revoke show what would happen without `--execute`
- **Owner protection** — your email (auto-detected) is never shown as revocable
- **Confirmation prompt** — always confirms before executing changes
- **Audit log** — every grant/revoke run logs results to `logs/`

## How It Works

OAuth client credentials are bundled with the package (this is standard practice
for desktop/CLI apps — the client ID identifies the app, not your data). When you
run `gdrivectl auth login`, it opens your browser for Google's consent screen where
you authorize the app. Your access token is stored locally at
`~/.config/gdrivectl/token.json` and never leaves your machine.

## License

MIT
