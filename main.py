from test_ollama import ask_local_ai
from urllib.request import Request, urlopen
from fastapi import FastAPI
from pydantic import BaseModel, Field
from pathlib import Path
from openai import OpenAI
from threading import Lock
import json
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
