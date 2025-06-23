"""
interview_logger.py
--------------------
Handles logging of interview questions and answers to a local file.
"""

import json
from datetime import datetime

LOG_FILE = "interview_logs.jsonl"

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

        print("\n[interview_logger] 📝 Logged Q&A to:", LOG_FILE)
        print("──────────────── Q&A Log Preview ───────────────")
        print(f"[{timestamp}]")
        print(f"👤 Q: {question.strip()[:120]}")
        print(f"🤖 A: {answer.strip()[:120]}")
        print("────────────────────────────────────────────────")

    except Exception as e:
        print(f"[interview_logger] ❌ Logging error: {e}")
