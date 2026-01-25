import click
import questionary
from rich.console import Console
from rich.table import Table

from gdrivectl.auth import authenticate, require_auth, logout as do_logout, get_credentials
from gdrivectl.config import get_owner_email
from gdrivectl.drive import (
    list_docs,
    get_permissions,
    grant_permissions,
    revoke_permissions,
    non_owner_permissions,
)
from gdrivectl.audit import export_permissions_csv, log_action

console = Console()


def _owner() -> str:
    """Get owner email from config, exit if not set."""
    email = get_owner_email()
    if not email:
        console.print("[red]Owner email not configured. Run:[/red] gdrivectl auth login")
        raise SystemExit(1)
    return email


@click.group()
def cli():
    """gdrivectl — Manage Google Docs permissions in bulk."""
    pass


@cli.group()
def auth():
    """Manage authentication (login/logout)."""
    pass


@auth.command()
def login():
    """Authenticate with Google (opens browser, one-time)."""
    authenticate()


@auth.command()
def logout():
    """Log out and remove stored credentials."""
    do_logout()


@auth.command()
def status():
    """Check current authentication status."""
    creds = get_credentials()
    if creds:
        owner = get_owner_email()
        console.print(f"[green]Logged in as {owner}[/green]" if owner else "[green]Logged in.[/green]")
    else:
        console.print("[yellow]Not logged in.[/yellow]")


@cli.command("list")
@click.option("--shared-only", is_flag=True, help="Show only docs shared with others")
def list_cmd(shared_only):
    """List all Google Docs you own."""
    creds = require_auth()
    owner = _owner()
    console.print("[dim]Fetching docs...[/dim]")
    docs = list_docs(creds, shared_only=shared_only)

    if not docs:
        console.print("[yellow]No docs found.[/yellow]")
        return

    table = Table(title=f"Google Docs ({len(docs)})")
    table.add_column("Name", style="cyan", max_width=50)
    table.add_column("Last Modified", style="green")
    table.add_column("Shared With", justify="right", style="magenta")
    table.add_column("Doc ID", style="dim", max_width=20)

    for doc in docs:
        perms = doc.get("permissions", [])
        share_count = len(non_owner_permissions(perms, owner))
        table.add_row(
            doc["name"],
            doc.get("modifiedTime", "")[:10],
            str(share_count),
            doc["id"][:20] + "...",
        )

    console.print(table)


@cli.command()
@click.option("--doc-id", default=None, help="Document ID to inspect")
@click.option("--doc-name", default=None, help="Document name to search for")
def inspect(doc_id, doc_name):
    """Inspect permissions on a specific doc."""
    creds = require_auth()
    owner = _owner()

    if not doc_id:
        docs = list_docs(creds)
        if not docs:
            console.print("[yellow]No docs found.[/yellow]")
            return

        choices = [
            questionary.Choice(title=d["name"], value=d["id"]) for d in docs
        ]

        if doc_name:
            choices = [c for c in choices if doc_name.lower() in c.title.lower()]
            if not choices:
                console.print(f"[red]No docs matching '{doc_name}'[/red]")
                return

        doc_id = questionary.select(
            "Select a document:",
            choices=choices,
        ).ask()

        if not doc_id:
            return

    perms = get_permissions(creds, doc_id)

    table = Table(title="Permissions")
    table.add_column("Email", style="cyan")
    table.add_column("Role", style="green")
    table.add_column("Type", style="yellow")
    table.add_column("Permission ID", style="dim")

    for p in perms:
        is_owner = p.get("emailAddress", "").lower() == owner.lower()
        style = "bold" if is_owner else ""
        table.add_row(
            p.get("emailAddress", p.get("type", "unknown")),
            p.get("role", ""),
            p.get("type", ""),
            p.get("id", ""),
            style=style,
        )

    console.print(table)


@cli.command()
@click.option("--execute", is_flag=True, help="Actually execute (default is dry-run)")
def grant(execute):
    """Grant access to Google Docs (interactive)."""
    creds = require_auth()
    docs = list_docs(creds)
    if not docs:
        console.print("[yellow]No docs found.[/yellow]")
        return

    # Pick docs
    choices = [
        questionary.Choice(title=d["name"], value=d["id"]) for d in docs
    ]
    selected_ids = questionary.checkbox(
        "Select docs to grant access on (space to select, enter to confirm):",
        choices=choices,
    ).ask()

    if not selected_ids:
        console.print("[yellow]No docs selected.[/yellow]")
        return

    # Enter emails
    emails_raw = questionary.text(
        "Enter email addresses (comma-separated):"
    ).ask()
    if not emails_raw:
        return
    emails = [e.strip() for e in emails_raw.split(",") if e.strip()]
    if not emails:
        console.print("[yellow]No emails provided.[/yellow]")
        return

    # Pick role
    role = questionary.select(
        "Select role:",
        choices=["reader", "writer", "commenter"],
    ).ask()
    if not role:
        return

    # Notification
    notify = questionary.confirm(
        "Send email notification to users?", default=False
    ).ask()

    # Build name map for display
    id_to_name = {d["id"]: d["name"] for d in docs}

    # Summary
    console.print()
    console.print("[bold]Summary:[/bold]")
    console.print(f"  Docs: {len(selected_ids)}")
    for fid in selected_ids:
        console.print(f"    - {id_to_name.get(fid, fid)}")
    console.print(f"  Emails: {', '.join(emails)}")
    console.print(f"  Role: {role}")
    console.print(f"  Notify: {'Yes' if notify else 'No'}")
    console.print()

    if not execute:
        console.print(
            "[yellow]DRY RUN — no changes made. "
            "Use --execute to apply.[/yellow]"
        )
        return

    if not questionary.confirm("Proceed?", default=False).ask():
        console.print("[dim]Cancelled.[/dim]")
        return

    console.print("[dim]Granting access...[/dim]")
    results = grant_permissions(creds, selected_ids, emails, role, notify)

    success = sum(1 for r in results if r["success"])
    failed = sum(1 for r in results if not r["success"])
    console.print(f"[green]Done: {success} granted[/green]", end="")
    if failed:
        console.print(f", [red]{failed} failed[/red]")
    else:
        console.print()

    # Log
    log_path = log_action("grant", results)
    console.print(f"[dim]Log saved: {log_path}[/dim]")

    # Show failures
    for r in results:
        if not r["success"]:
            console.print(
                f"  [red]FAILED[/red] {r['email']} on {r['file_id']}: {r['error']}"
            )


@cli.command()
@click.option("--execute", is_flag=True, help="Actually execute (default is dry-run)")
def revoke(execute):
    """Revoke access from Google Docs (interactive)."""
    creds = require_auth()
    owner = _owner()
    docs = list_docs(creds)
    if not docs:
        console.print("[yellow]No docs found.[/yellow]")
        return

    # Only show docs that have shared permissions
    shared_docs = [
        d for d in docs if non_owner_permissions(d.get("permissions", []), owner)
    ]
    if not shared_docs:
        console.print("[yellow]No docs with shared permissions found.[/yellow]")
        return

    # Pick docs
    choices = [
        questionary.Choice(
            title=f"{d['name']} ({len(non_owner_permissions(d.get('permissions', []), owner))} shared)",
            value=d["id"],
        )
        for d in shared_docs
    ]
    selected_ids = questionary.checkbox(
        "Select docs to revoke access from (space to select):",
        choices=choices,
    ).ask()

    if not selected_ids:
        console.print("[yellow]No docs selected.[/yellow]")
        return

    # Collect all non-owner permissions across selected docs
    selected_docs = [d for d in shared_docs if d["id"] in selected_ids]
    all_emails = set()
    for doc in selected_docs:
        for p in non_owner_permissions(doc.get("permissions", []), owner):
            email = p.get("emailAddress", "")
            if email:
                all_emails.add(email)

    if not all_emails:
        console.print("[yellow]No revocable permissions found.[/yellow]")
        return

    # Pick emails to revoke
    email_choices = [questionary.Choice(title=e, value=e) for e in sorted(all_emails)]
    email_choices.insert(
        0, questionary.Choice(title="[ALL except owner]", value="__ALL__")
    )
    selected_emails = questionary.checkbox(
        "Select emails to revoke (space to select):",
        choices=email_choices,
    ).ask()

    if not selected_emails:
        console.print("[yellow]No emails selected.[/yellow]")
        return

    revoke_all = "__ALL__" in selected_emails
    if revoke_all:
        target_emails = all_emails
    else:
        target_emails = set(selected_emails)

    # Build revocation list
    revocations = []

    for doc in selected_docs:
        for p in non_owner_permissions(doc.get("permissions", []), owner):
            email = p.get("emailAddress", "")
            if email in target_emails:
                revocations.append(
                    {
                        "file_id": doc["id"],
                        "permission_id": p["id"],
                        "email": email,
                        "doc_name": doc["name"],
                    }
                )

    # Summary
    console.print()
    console.print("[bold]Revocation Summary:[/bold]")
    console.print(f"  Total revocations: {len(revocations)}")
    for r in revocations:
        console.print(f"    - {r['email']} from {r['doc_name']}")
    console.print()

    if not execute:
        console.print(
            "[yellow]DRY RUN — no changes made. "
            "Use --execute to apply.[/yellow]"
        )
        return

    if not questionary.confirm(
        f"Revoke {len(revocations)} permissions?", default=False
    ).ask():
        console.print("[dim]Cancelled.[/dim]")
        return

    console.print("[dim]Revoking access...[/dim]")
    results = revoke_permissions(creds, revocations)

    success = sum(1 for r in results if r["success"])
    failed = sum(1 for r in results if not r["success"])
    console.print(f"[green]Done: {success} revoked[/green]", end="")
    if failed:
        console.print(f", [red]{failed} failed[/red]")
    else:
        console.print()

    # Log
    log_path = log_action("revoke", results)
    console.print(f"[dim]Log saved: {log_path}[/dim]")

    for r in results:
        if not r["success"]:
            console.print(
                f"  [red]FAILED[/red] {r['email']} on {r['file_id']}: {r['error']}"
            )


@cli.command()
def audit():
    """Export all docs + permissions to CSV."""
    creds = require_auth()
    console.print("[dim]Fetching all docs and permissions...[/dim]")
    docs = list_docs(creds)

    if not docs:
        console.print("[yellow]No docs found.[/yellow]")
        return

    filepath = export_permissions_csv(docs)
    total_perms = sum(len(d.get("permissions", [])) for d in docs)
    console.print(
        f"[green]Audit exported:[/green] {filepath}\n"
        f"  {len(docs)} docs, {total_perms} permissions"
    )


if __name__ == "__main__":
    cli()
