
import json
import os
from urllib.request import Request, urlopen
from urllib.error import HTTPError

BASE_URL = "http://127.0.0.1:8000"

BOOKING_ID = "BK-FC4278EAC5BC"
API_KEY = os.getenv("TUITIONMATE_STAFF_API_KEY")


def patch_status(booking_id, status, key=None):
    headers = {"Content-Type": "application/json"}

    if key is not None:
        headers["x-staff-api-key"] = key

    request = Request(
        f"{BASE_URL}/bookings/{booking_id}/status",
        data=json.dumps({"status": status}).encode(),
        headers=headers,
        method="PATCH"
    )

    try:
        with urlopen(request, timeout=5) as response:
            return response.status, json.load(response)
    except HTTPError as error:
        return error.code, json.load(error)


def check(name, actual, expected):
    passed = actual == expected
    print(
        f"{'PASS' if passed else 'FAIL'} | "
        f"{name}: HTTP {actual}, expected {expected}"
    )
    return passed


def main():
    if not API_KEY:
        print("ERROR: TUITIONMATE_STAFF_API_KEY not set.")
        return

    results = []

    status, _ = patch_status(BOOKING_ID, "completed")
    results.append(check("Missing API key", status, 401))

    status, _ = patch_status(
        BOOKING_ID, "completed", "invalid-demo-key"
    )
    results.append(check("Wrong API key", status, 401))

    status, _ = patch_status(
        "BK-NOTFOUND123", "completed", API_KEY
    )
    results.append(check("Unknown booking", status, 404))

    status, _ = patch_status(
        BOOKING_ID, "pending_staff_review", API_KEY
    )
    results.append(check("Invalid status value", status, 422))

    # Booking is already in "contacted" state.
    status, result = patch_status(
        BOOKING_ID, "contacted", API_KEY
    )
    results.append(
        check("Repeated update", status, 200)
        and result.get("changed") is False
    )

    # Test invalid status transition:
# contacted -> completed is allowed,
# but completed -> contacted is not.

    status, result = patch_status(
        BOOKING_ID, "completed", API_KEY
    )
    results.append(
        check("Complete follow-up", status, 200)
        and result.get("changed") is True
    )

    status, _ = patch_status(
        BOOKING_ID, "contacted", API_KEY
    )
    results.append(
        check("Invalid status transition", status, 409)
    )

    print("-" * 45)
    print(f"RESULT: {sum(results)}/{len(results)} PASS")


if __name__ == "__main__":
    main()
