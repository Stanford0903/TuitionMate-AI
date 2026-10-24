
from fastapi import FastAPI
from pydantic import BaseModel, Field

app = FastAPI(title="AI Automation Business API")


# Data structure for a customer inquiry
class Inquiry(BaseModel):
    name: str = Field(min_length=1)
    question: str = Field(min_length=1)


# Check if our API is running
@app.get("/health")
def health():
    return {
        "status": "ok",
        "message": "FastAPI is running!"
    }


# Receive a customer inquiry
@app.post("/inquiry")
def inquiry(data: Inquiry):

    question = data.question.lower().strip()

    if "open" in question or "hour" in question:
        answer = "We are open from 9 AM to 6 PM."

    elif "price" in question:
        answer = "Please contact our team for pricing."

    else:
        answer = "Our team will assist you shortly."

    return {
        "success": True,
        "customer": data.name,
        "reply": answer
    }

