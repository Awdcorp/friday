
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
    entry = {
        "timestamp": datetime.now().isoformat(),
        "question": question,
        "answer": answer
    }

    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
        print(f"📝 Logged Q&A to {LOG_FILE}")
    except Exception as e:
        print(f"❌ Logging error: {e}")
