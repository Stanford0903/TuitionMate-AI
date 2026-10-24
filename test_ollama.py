
import json
from urllib.request import Request, urlopen

OLLAMA_URL = "http://127.0.0.1:11434/api/generate"

FAQ_CONTEXT = """
Approved FAQs:

FAQ001
Question: What subjects do you offer?
Answer: We offer Maths, Science and English.

FAQ002
Question: Are there weekend classes?
Answer: Weekend classes are available.

FAQ003
Question: How much are the fees?
Answer: Staff will confirm the latest fees.

FAQ004
Question: How can I register?
Answer: Contact our registration team.
"""

def ask_local_ai(question):
    prompt = f"""
You are an FAQ intent classifier.

Choose the FAQ whose approved ANSWER directly
answers the customer's question.

Maths means mathematics.

{FAQ_CONTEXT}

Rules:
- Return only FAQ001, FAQ002, FAQ003, FAQ004 or NONE.
- Never choose an unrelated FAQ.
- If no approved answer supports the question,
  return NONE.
- Do not invent information.

Customer question: {question}

FAQ ID:
"""

    payload = {
        "model": "qwen2.5:3b",
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0
        }
    }

    request = Request(
        OLLAMA_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST"
    )

    with urlopen(request, timeout=120) as response:
        data = json.load(response)

    return data["response"].strip()



if __name__ == "__main__":
    tests = [
        ("Do you teach mathematics?", "FAQ001"),
        ("Do you provide school bus transportation?", "NONE")
    ]

    for question, expected in tests:
        actual = ask_local_ai(question)
        result = "PASS" if actual == expected else "FAIL"

        print("Question:", question)
        print("Expected:", expected)
        print("Actual:", actual)
        print("Result:", result)
        print("-" * 40)


