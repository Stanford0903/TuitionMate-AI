
import csv
import json
from pathlib import Path
from urllib.request import Request, urlopen

API_URL = "http://127.0.0.1:8000/inquiry"

TEST_CASES = [
    ("TC01", "What subjects do you offer?",
     "answered", "FAQ001"),

    ("TC02", "Are there weekend classes?",
     "answered", "FAQ002"),

    ("TC03", "How much are the fees?",
     "answered", "FAQ003"),

    ("TC04", "How can I register?",
     "answered", "FAQ004"),

    ("TC05", "Do you teach mathematics?",
     "handoff", None),

    ("TC06", "Can you provide ADHD support?",
     "handoff", None),

    ("TC07", "Do you offer school bus transport?",
     "handoff", None),

    ("TC08", "Can I get a refund?",
     "handoff", None),

    ("TC09", "Where is your tuition centre?",
     "handoff", None),

    ("TC10", "Can I get a 50% discount?",
     "handoff", None),
]


def send_question(question):
    payload = json.dumps({
        "name": "Demo Parent",
        "question": question
    }).encode("utf-8")

    request = Request(
        API_URL,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST"
    )

    with urlopen(request, timeout=10) as response:
        return json.load(response)


def main():
    results = []

    for test_id, question, expected, expected_id in TEST_CASES:
        try:
            response = send_question(question)

            actual = response.get("status")
            actual_id = response.get("faq_id")

            passed = (
                actual == expected
                and actual_id == expected_id
                and response.get("handoff") == (expected == "handoff")
            )

            results.append({
                "test_id": test_id,
                "question": question,
                "expected": expected,
                "actual": actual,
                "expected_faq_id": expected_id or "",
                "actual_faq_id": actual_id or "",
                "result": "PASS" if passed else "FAIL"
            })

        except Exception as e:
            results.append({
                "test_id": test_id,
                "question": question,
                "expected": expected,
                "actual": type(e).__name__,
                "expected_faq_id": expected_id or "",
                "actual_faq_id": "",
                "result": "ERROR"
            })

    output = Path(__file__).parent / "test_results_day5.csv"

    with output.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=results[0].keys())
        writer.writeheader()
        writer.writerows(results)

    for item in results:
        print(
            item["test_id"],
            item["result"],
            "| Expected:", item["expected"],
            "| Actual:", item["actual"]
        )

    passed_count = sum(r["result"] == "PASS" for r in results)

    print()
    print(f"RESULT: {passed_count}/{len(results)} passed")
    print(f"ACCURACY: {passed_count / len(results) * 100:.1f}%")
    print("REPORT:", output)


if __name__ == "__main__":
    main()
