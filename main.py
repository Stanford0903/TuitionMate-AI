import csv
from datetime import datetime, timezone
from threading import Lock
from typing import Literal
from fastapi import HTTPException

from test_ollama import ask_local_ai
from urllib.request import Request, urlopen
from fastapi import FastAPI
from pydantic import BaseModel, Field
from pathlib import Path
import json
from urllib.error import URLError, HTTPError
import os
import re

app = FastAPI(title="TuitionMate AI API")

FAQ_FILE = Path(__file__).parent / "data" / "faq.json"

# Only verified demo FAQs are allowed.
APPROVED_FAQ_IDS = {"FAQ001", "FAQ002", "FAQ003", "FAQ004"}

# Limit AI API calls during this development run.
MAX_AI_CALLS = 10
ai_calls = 0
ai_lock = Lock()

HANDOFF_MESSAGE = (
    "I cannot confirm that information. "
    "Please contact our staff for assistance."
)

# Safety: send these enquiries to human staff
# without calling the AI model.
SENSITIVE_WORDS = [
    "adhd", "autism", "diagnosis", "medical",
    "disability", "special needs", "refund",
    "complaint", "personal information",
    "ic number", "passport"
]


class Inquiry(BaseModel):
    name: str = Field(min_length=1)
    question: str = Field(min_length=1, max_length=500)


def normalize(text):
    return re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()


def load_faq():
    with FAQ_FILE.open("r", encoding="utf-8") as file:
        return json.load(file)


def approved_faqs():
    return [
        faq for faq in load_faq()
        if faq["id"] in APPROVED_FAQ_IDS
    ]


def exact_match(question, faqs):
    for faq in faqs:
        if normalize(question) == normalize(faq["question"]):
            return faq
    return None




def local_ai_match(question, faqs):
    try:
        # Reuse our previously successful Ollama function.
        selected_id = ask_local_ai(question).strip()

        print("LOCAL AI RAW RESULT:", repr(selected_id))

        # Only accept IDs from approved FAQ data.
        for faq in faqs:
            if selected_id == faq["id"]:
                return faq

        return None

    except Exception as e:
        print("LOCAL AI ERROR:", type(e).__name__)
        return None


@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "TuitionMate AI"
    }


@app.post("/inquiry")
def inquiry(data: Inquiry):
    question = data.question.strip()

    if not data.name.strip() or not question:
        return {
            "status": "invalid",
            "handoff": False,
            "reply": "Name and question cannot be blank."
        }

    faqs = approved_faqs()

    # Safety rules take priority over FAQ matching.
    normalized_question = normalize(question)

    if any(
        re.search(r"\b" + re.escape(word) + r"\b", normalized_question)
        for word in SENSITIVE_WORDS
    ):
        match = None

    else:
        match = exact_match(question, faqs)

        # Only use local AI if exact matching fails.
        if match is None:
            match = local_ai_match(question, faqs)

    if match:
        return {
            "status": "answered",
            "handoff": False,
            "customer": data.name,
            "faq_id": match["id"],
            "reply": match["answer"]
        }

    return {
        "status": "handoff",
        "handoff": True,
        "customer": data.name,
        "faq_id": None,
        "reply": HANDOFF_MESSAGE
    }


# =====================================
# Day 6 - Booking Request API
# =====================================

BOOKING_FILE = Path(__file__).parent / "data" / "leads_demo.csv"
booking_lock = Lock()

BOOKING_FIELDS = [
    "created_at",
    "parent_name",
    "contact_email",
    "subject",
    "preferred_day",
    "status"
]


class BookingRequest(BaseModel):
    parent_name: str = Field(min_length=1, max_length=80)

    contact_email: str = Field(
        min_length=5,
        max_length=120,
        pattern=r"^[^\s@]+@[^\s@]+\.[^\s@]+$"
    )

    subject: Literal["Maths", "Science", "English"]

    preferred_day: Literal[
        "Monday", "Tuesday", "Wednesday",
        "Thursday", "Friday", "Saturday", "Sunday"
    ]

    consent_to_contact: bool


def safe_csv_value(value):
    # Prevent spreadsheet formula execution.
    text = str(value).strip()
    if text.startswith(("=", "+", "-", "@")):
        return "'" + text
    return text


@app.post("/booking-request")
def create_booking_request(data: BookingRequest):

    name = data.parent_name.strip()
    email = data.contact_email.strip().lower()

    if not name or not data.consent_to_contact:
        raise HTTPException(
            status_code=422,
            detail="Valid name and consent are required."
        )

    with booking_lock:
        BOOKING_FILE.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        existing = []

        if BOOKING_FILE.exists():
            with BOOKING_FILE.open(
                "r", encoding="utf-8", newline=""
            ) as file:
                existing = list(csv.DictReader(file))

        # Check duplicate requests.
        for row in existing:
            if (
                row["contact_email"] == email
                and row["subject"] == data.subject
                and row["preferred_day"] == data.preferred_day
            ):
                return {
                    "status": "duplicate",
                    "message": "This demo request already exists."
                }

        record = {
            "created_at": datetime.now(
                timezone.utc
            ).isoformat(),
            "parent_name": safe_csv_value(name),
            "contact_email": email,
            "subject": data.subject,
            "preferred_day": data.preferred_day,
            "status": "pending_staff_review"
        }

        file_exists = BOOKING_FILE.exists()

        with BOOKING_FILE.open(
            "a", encoding="utf-8", newline=""
        ) as file:
            writer = csv.DictWriter(
                file, fieldnames=BOOKING_FIELDS
            )

            if not file_exists:
                writer.writeheader()

            writer.writerow(record)
    notification_sent = notify_n8n(record)

    return {
        "success": True,
        "status": "request_received",
        "notification_sent": notification_sent,
        "message": (
            "Your demo booking request has been recorded. "
            "The schedule is not confirmed."
        )
    }


# Day 7 - Local n8n webhook
N8N_WEBHOOK_URL = (
    "http://127.0.0.1:5678/webhook/tuitionmate-booking"
)


def notify_n8n(record):
    payload = json.dumps(record).encode("utf-8")

    request = Request(
        N8N_WEBHOOK_URL,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST"
    )

    try:
        with urlopen(request, timeout=3) as response:
            if not 200 <= response.status < 300:
                return False

        print("N8N WEBHOOK: SUCCESS")
        return True

    except (HTTPError, URLError, TimeoutError, OSError) as error:
        print("N8N WEBHOOK FAILED:", type(error).__name__)
        return False
