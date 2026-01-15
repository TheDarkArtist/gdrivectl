import time
from typing import Optional

from googleapiclient.discovery import build
from googleapiclient.http import BatchHttpRequest
from google.oauth2.credentials import Credentials
from rich.console import Console

from tda_gdrivectl.config import (
    DOCS_QUERY,
    DRIVE_FIELDS,
    BATCH_SIZE,
    OWNER_EMAIL,
)

console = Console()


def get_service(creds: Credentials):
    return build("drive", "v3", credentials=creds)


def list_docs(
    creds: Credentials, shared_only: bool = False
) -> list[dict]:
    """Fetch all Google Docs owned by user. Handles pagination."""
    service = get_service(creds)
    docs = []
    page_token = None

    while True:
        resp = (
            service.files()
            .list(
                q=DOCS_QUERY,
                fields=f"nextPageToken,{DRIVE_FIELDS}",
                pageSize=1000,
                pageToken=page_token,
            )
            .execute()
        )
        docs.extend(resp.get("files", []))
        page_token = resp.get("nextPageToken")
        if not page_token:
            break

    if shared_only:
        docs = [
            d
            for d in docs
            if len(d.get("permissions", [])) > 1
            or any(
                p.get("type") == "anyone" for p in d.get("permissions", [])
            )
        ]

    return docs


def get_permissions(creds: Credentials, file_id: str) -> list[dict]:
    """Get all permissions for a specific file."""
    service = get_service(creds)
    resp = (
        service.files()
        .get(
            fileId=file_id,
            fields="permissions(id,type,role,emailAddress)",
        )
        .execute()
    )
    return resp.get("permissions", [])


def grant_permissions(
    creds: Credentials,
    file_ids: list[str],
    emails: list[str],
    role: str,
    send_notification: bool = False,
) -> list[dict]:
    """Grant permissions on files. Returns list of results."""
    service = get_service(creds)
    results = []

    for i in range(0, len(file_ids), BATCH_SIZE):
        batch = service.new_batch_http_request()
        batch_file_ids = file_ids[i : i + BATCH_SIZE]

        for file_id in batch_file_ids:
            for email in emails:
                body = {"type": "user", "role": role, "emailAddress": email}

                def _callback(request_id, response, exception, fid=file_id, em=email):
                    results.append(
                        {
                            "file_id": fid,
                            "email": em,
                            "role": role,
                            "action": "grant",
                            "success": exception is None,
                            "error": str(exception) if exception else None,
                        }
                    )

                batch.add(
                    service.permissions().create(
                        fileId=file_id,
                        body=body,
                        sendNotificationEmail=send_notification,
                        fields="id,emailAddress,role",
                    ),
                    callback=_callback,
                )

        batch.execute()
        if i + BATCH_SIZE < len(file_ids):
            time.sleep(1)  # Rate limit courtesy

    return results


def revoke_permissions(
    creds: Credentials,
    revocations: list[dict],  # [{"file_id": ..., "permission_id": ..., "email": ...}]
) -> list[dict]:
    """Revoke permissions. Returns list of results."""
    service = get_service(creds)
    results = []

    for i in range(0, len(revocations), BATCH_SIZE):
        batch = service.new_batch_http_request()
        batch_items = revocations[i : i + BATCH_SIZE]

        for item in batch_items:

            def _callback(
                request_id,
                response,
                exception,
                fid=item["file_id"],
                em=item["email"],
            ):
                results.append(
                    {
                        "file_id": fid,
                        "email": em,
                        "action": "revoke",
                        "success": exception is None,
                        "error": str(exception) if exception else None,
                    }
                )

            batch.add(
                service.permissions().delete(
                    fileId=item["file_id"],
                    permissionId=item["permission_id"],
                ),
                callback=_callback,
            )

        batch.execute()
        if i + BATCH_SIZE < len(revocations):
            time.sleep(1)

    return results


def non_owner_permissions(permissions: list[dict]) -> list[dict]:
    """Filter out owner permissions."""
    return [
        p
        for p in permissions
        if p.get("emailAddress", "").lower() != OWNER_EMAIL.lower()
        and p.get("role") != "owner"
    ]
