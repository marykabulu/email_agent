import sys

from gmail import get_emails


sys.stdout.reconfigure(encoding="utf-8")

emails = get_emails(5)

print(f"\nFound {len(emails)} emails.\n")


for email in emails:

    print("=" * 60)

    print(f"From: {email['sender']}")
    print(f"Subject: {email['subject']}")
    print(f"Date: {email['date']}")

    print("\nBody:")
    print(email["body"])

    print("=" * 60)
