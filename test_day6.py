
import csv
import json
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
from uuid import uuid4

API_URL = "http://127.0.0.1:8000/booking-request"
CSV_FILE = Path(__file__).parent / "data" / "leads_demo.csv"

# Unique, synthetic email for this test run.
email = f"day6-{uuid4().hex[:10]}@example.com"

base = {
    "parent_name": "Day 6 Demo",
    "contact_email": email,
    "subject": "Maths",
    "preferred_day": "Saturday",
    "consent_to_contact": True
}


def send(payload):
    request = Request(
        API_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST"
    )

    try:
        with urlopen(request, timeout=10) as response:
            return response.status, json.load(response)
    except HTTPError as error:
        return error.code, json.load(error)


def read_rows():
    if not CSV_FILE.exists():
        return []

    with CSV_FILE.open(
        "r", encoding="utf-8", newline=""
    ) as file:
        return list(csv.DictReader(file))


def check(label, condition):
    print(f"{'PASS' if condition else 'FAIL'} | {label}")
    return bool(condition)


def main():
    passed = 0
    total = 0

    def verify(label, condition):
        nonlocal passed, total
        total += 1
        passed += check(label, condition)

    before = len(read_rows())

    # 1. Valid request
    status, result = send(base)
    verify(
        "Valid booking request",
        status == 200
        and result.get("status") == "request_received"
    )

    # 2. Duplicate request
    status, result = send(base)
    verify(
        "Duplicate prevention",
        status == 200
        and result.get("status") == "duplicate"
    )

    # 3. Invalid email
    bad_email = {**base, "contact_email": "not-an-email"}
    status, _ = send(bad_email)
    verify("Invalid email rejected", status == 422)

    # 4. Missing preferred day
    missing_day = {**base}
    del missing_day["preferred_day"]
    status, _ = send(missing_day)
    verify("Missing field rejected", status == 422)

    # 5. No consent
    no_consent = {**base, "consent_to_contact": False}
    status, _ = send(no_consent)
    verify("No consent rejected", status == 422)

    # 6. CSV injection attempt
    malicious = {
        **base,
        "parent_name": "=1+1",
        "contact_email": f"safe-{uuid4().hex[:10]}@example.com"
    }
    status, result = send(malicious)
    rows = read_rows()

    matching = [
        row for row in rows
        if row["contact_email"] == malicious["contact_email"]
    ]

    verify(
        "Spreadsheet formula escaped",
        status == 200
        and result.get("status") == "request_received"
        and len(matching) == 1
        and matching[0]["parent_name"] == "'=1+1"
    )

    # 7. Only two valid records should have been added
    after = len(rows)
    verify(
        "CSV row count correct",
        after == before + 2
    )

    print("-" * 45)
    print(f"RESULT: {passed}/{total} PASS")


if __name__ == "__main__":
    try:
        main()
    except (URLError, TimeoutError) as error:
        print("API UNAVAILABLE OR TIMEOUT:", type(error).__name__)
        print("Make sure FastAPI is running on port 8000.")
