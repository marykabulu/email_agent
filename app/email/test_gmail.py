from typing import Any, cast

from gmail import get_gmail_service


service = cast(Any, get_gmail_service())

print("Successfully connected to Gmail!")

results = (
    service.users()
    .labels()
    .list(userId="me")
    .execute()
)

labels = results.get("labels", [])

print(f"Found {len(labels)} Gmail labels.")

for label in labels[:10]:
    print(label["name"])
