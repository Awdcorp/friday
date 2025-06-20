# conversation_mode/conversation_logger.py

"""
Conversation Logger – Saves every interaction to a persistent log file.

Includes:
- Timestamp
- Transcript (user input)
- Intent detected
- Final response
- Optional tags (task ID, model used, etc.)

Format: One JSON entry per line (JSONL)
"""

import json
import os
import time

# Where logs will be saved
LOG_FILE_PATH = "conversation_logs.jsonl"  # Flat file, one JSON object per line


def log_conversation(transcript: str, intent: str, response: str, extra: dict = None):
    """
    Appends a structured entry to the conversation log.
    Logs the full entry content.
    """
    entry = {
        "timestamp": time.time(),
        "transcript": transcript,
        "intent": intent,
        "response": response,
    }

    if extra:
        entry.update(extra)
        print(f"📝 Extra log fields: {extra}")

    try:
        with open(LOG_FILE_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

        print(f"🗃️ Logged to file: {LOG_FILE_PATH}")
        print(f"📄 Entry:\n{json.dumps(entry, indent=2)}")

    except Exception as e:
        print(f"❌ Failed to write conversation log: {e}")
