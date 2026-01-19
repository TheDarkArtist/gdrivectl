# Contributing

## Setup

```bash
git clone https://github.com/TheDarkArtist/tda-gdrivectl.git
cd tda-gdrivectl
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

## Project Structure

```
src/tda_gdrivectl/
├── __init__.py
├── __main__.py    # python -m tda_gdrivectl
├── cli.py         # Click commands + interactive prompts
├── auth.py        # OAuth2 flow, token storage/refresh
├── drive.py       # Google Drive API wrapper
├── audit.py       # CSV export + action logging
├── config.py      # Paths, constants, config load/save
└── setup.py       # Guided GCP project + OAuth setup
```

## Adding a Command

1. Add your function to `cli.py` with the `@cli.command()` decorator
2. Use `require_auth()` to get credentials
3. Use `_owner()` to get the protected owner email
4. Use `questionary` for interactive prompts, `rich` for output

## Code Style

- No frameworks beyond what's in `pyproject.toml`
- Keep it simple — this is a CLI tool, not a library
- Interactive prompts via `questionary`, tables via `rich`
- All destructive operations must be dry-run by default (`--execute` to apply)

## Submitting Changes

1. Fork the repo
2. Create a branch (`git checkout -b feature/my-thing`)
3. Make your changes
4. Test manually against your own Google Drive
5. Open a PR
