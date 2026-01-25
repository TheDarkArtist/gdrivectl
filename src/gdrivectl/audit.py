import csv
import json
from datetime import datetime
from pathlib import Path

from rich.console import Console

from gdrivectl.config import LOGS_DIR

console = Console()


def export_permissions_csv(docs: list[dict]) -> Path:
    """Export all docs + permissions to a CSV file."""
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filepath = LOGS_DIR / f"audit_{timestamp}.csv"

    with open(filepath, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(
            ["doc_name", "doc_id", "email", "role", "type", "timestamp"]
        )

        for doc in docs:
            for perm in doc.get("permissions", []):
                writer.writerow(
                    [
                        doc["name"],
                        doc["id"],
                        perm.get("emailAddress", ""),
                        perm.get("role", ""),
                        perm.get("type", ""),
                        timestamp,
                    ]
                )

    return filepath


def log_action(action: str, results: list[dict]) -> Path:
    """Log grant/revoke results to a JSON file."""
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filepath = LOGS_DIR / f"{action}_{timestamp}.json"

    log_data = {
        "action": action,
        "timestamp": datetime.now().isoformat(),
        "total": len(results),
        "success": sum(1 for r in results if r["success"]),
        "failed": sum(1 for r in results if not r["success"]),
        "details": results,
    }

    filepath.write_text(json.dumps(log_data, indent=2))
    return filepath
