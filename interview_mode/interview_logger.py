"""
interview_logger.py
--------------------
Handles logging of interview questions and answers to a local file.
"""

import json
from datetime import datetime

LOG_FILE = "interview_logs.jsonl"
MODULE = "[interview_logger]"
SHOW_PREVIEW = False  # Toggle to show Q&A preview in console


def log(msg):
    print(f"{MODULE} {msg}")


def log_qa(question, answer):
    """
    Logs a Q&A pair with timestamp to a JSON lines file.

    Args:
        question (str): The question received.
        answer (str): The GPT-generated answer.
    """
    timestamp = datetime.now().isoformat()

    entry = {
        "timestamp": timestamp,
        "question": question.strip(),
        "answer": answer.strip()
    }

    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

        log(f"✅ Logged Q&A | Time: {timestamp}")

        if SHOW_PREVIEW:
            log("📝 Preview:")
            log(f"👤 Q: {question.strip()[:80]}")
            log(f"🤖 A: {answer.strip()[:80]}")

    except Exception as e:
        log(f"❌ Logging error: {e}")
