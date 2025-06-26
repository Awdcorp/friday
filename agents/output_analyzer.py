"""
🔜 Output Analyzer
------------------------
Parses terminal output from logs to confirm success, failure, or warning.
"""

import os
import time

LOG_FILE = "logs/terminal_output.log"
KEYWORDS = ["Error", "Exception", "Traceback", "successfully", "started"]

# === Analyze Terminal Output ===
def analyze_output():
    print("[output_analyzer] 🔜 Checking logs for result...")

    if not os.path.exists(LOG_FILE):
        print("[output_analyzer] ❌ Log file not found.")
        return "log_missing"

    with open(LOG_FILE, 'r', encoding='utf-8') as f:
        content = f.read()

    for keyword in KEYWORDS:
        if keyword.lower() in content.lower():
            print(f"[output_analyzer] ✅ Found keyword: '{keyword}'")
            if "error" in keyword.lower() or "exception" in keyword.lower():
                return "error"
            return "success"

    print("[output_analyzer] ❓ No clear success or error found.")
    return "unknown"

# === For Testing Only ===
if __name__ == "__main__":
    result = analyze_output()
    print(f"[output_analyzer] Final Result: {result}")
