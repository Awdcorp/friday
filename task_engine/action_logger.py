"""
📝 Action Logger
------------------------
Logs patch attempts, actions, and final result into a structured JSONL file.
"""

import json
import time
import os

LOG_FILE = "logs/self_build_log.jsonl"

# === Utility ===
def current_time():
    return time.strftime("%Y-%m-%d %H:%M:%S")

# === Append Action to Log ===
def log_action(entry):
    entry["timestamp"] = current_time()

    try:
        os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
        print(f"[action_logger] 📃 Logged action at {entry['timestamp']}")
    except Exception as e:
        print(f"[action_logger] ❌ Failed to log: {e}")

# === Example Usage ===
if __name__ == "__main__":
    log_action({
        "task_type": "code_patch",
        "file": "example.py",
        "status": "success",
        "summary": "Replaced toggle_mode() function"
    })
