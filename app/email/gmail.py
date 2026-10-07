import os
import base64
from typing import Any, cast

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build


# Only allow the application to read emails for now.
SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]


def get_gmail_service() -> Any:
    """Authenticate with Gmail and return a Gmail API service."""

    credentials = None

    # Check if we already have a saved Gmail login.
    if os.path.exists("token.json"):
        credentials = Credentials.from_authorized_user_file(
            "token.json",
            SCOPES
        )

    # If we don't have valid credentials, authenticate.
    if not credentials or not credentials.valid:

        # Refresh the token if it has expired.
        if credentials and credentials.expired and credentials.refresh_token:
            credentials.refresh(Request())

        # Otherwise, start the Google login process.
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                "credentials.json",
                SCOPES
            )

            credentials = flow.run_local_server(port=0)

        # Save the credentials for future runs.
        with open("token.json", "w", encoding="utf-8") as token:
            token.write(credentials.to_json())

    # Create the Gmail API service.
    service: Any = build(
        "gmail",
        "v1",
        credentials=credentials
    )

    return service


def get_emails(max_results: int = 10) -> list[dict[str, str]]:
    """Get unread emails from the Gmail inbox."""

    # Connect to Gmail.
    service = cast(Any, get_gmail_service())

    # Ask Gmail for message IDs.
    results = (
        service.users()
        .messages()
        .list(
            userId="me",
            labelIds=["INBOX"],
            q="is:unread",
            maxResults=max_results
        )
        .execute()
    )

    # Get the messages from Google's response.
    messages = results.get("messages", [])

    emails = []

    # Retrieve the full details of each message.
    for message in messages:

        email = (
            service.users()
            .messages()
            .get(
                userId="me",
                id=message["id"],
                format="full"
            )
            .execute()
        )

        emails.append(parse_email(email))

    return emails


def parse_email(message: dict[str, Any]) -> dict[str, str | None]:
    """Convert a Gmail API message into a simple dictionary."""

    payload = message.get("payload", {})

    headers = payload.get("headers", [])

    sender = ""
    subject = ""
    date = ""

    # Look through the email headers.
    for header in headers:

        name = header.get("name", "")
        value = header.get("value", "")

        if name.lower() == "from":
            sender = value

        elif name.lower() == "subject":
            subject = value

        elif name.lower() == "date":
            date = value

    # Get the email body.
    body = extract_body(payload)

    return {
        "id": message.get("id"),
        "thread_id": message.get("threadId"),
        "sender": sender,
        "subject": subject,
        "date": date,
        "body": body
    }


def extract_body(payload: dict[str, Any]) -> str:
    """Extract the readable text from a Gmail message."""

    body = payload.get("body", {})

    data = body.get("data")

    # Simple email with the body directly available.
    if data:
        return base64.urlsafe_b64decode(data).decode(
            "utf-8",
            errors="ignore"
        )

    # Multipart email.
    parts = payload.get("parts", [])

    for part in parts:

        if part.get("mimeType") == "text/plain":

            part_body = part.get("body", {})
            data = part_body.get("data")

            if data:
                return base64.urlsafe_b64decode(data).decode(
                    "utf-8",
                    errors="ignore"
                )

    return ""
