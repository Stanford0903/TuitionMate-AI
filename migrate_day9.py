
import csv
import os
import tempfile
from pathlib import Path
from uuid import uuid4

BOOKING_FILE = Path(__file__).parent / "data" / "leads_demo.csv"

OLD_FIELDS = [
    "created_at",
    "parent_name",
    "contact_email",
    "subject",
    "preferred_day",
    "status",
]

NEW_FIELDS = ["booking_id"] + OLD_FIELDS


def migrate():
    if not BOOKING_FILE.exists():
        print("ERROR: Booking CSV not found.")
        return

    with BOOKING_FILE.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        fields = reader.fieldnames
        rows = list(reader)

    if fields == NEW_FIELDS:
        print("Already migrated. No changes needed.")
        return

    if fields != OLD_FIELDS:
        print("ERROR: Unexpected CSV columns. No changes made.")
        print("Columns:", fields)
        return

    for row in rows:
        row["booking_id"] = "BK-" + uuid4().hex[:12].upper()

    temp_path = None

    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            newline="",
            dir=BOOKING_FILE.parent,
            suffix=".tmp",
            delete=False,
        ) as file:
            temp_path = Path(file.name)
            writer = csv.DictWriter(file, fieldnames=NEW_FIELDS)
            writer.writeheader()
            writer.writerows(rows)

        os.replace(temp_path, BOOKING_FILE)

    finally:
        if temp_path is not None and temp_path.exists():
            temp_path.unlink()

    print(f"SUCCESS: Migrated {len(rows)} booking records.")
    print("Added column: booking_id")


if __name__ == "__main__":
    migrate()
