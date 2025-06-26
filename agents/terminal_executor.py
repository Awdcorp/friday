"""
🔋 Terminal Executor
------------------------
Runs or restarts scripts like 'main_brain.py' to test changes.
Captures terminal output for later inspection.
"""

import subprocess
import threading
import logging

# === Config ===
COMMAND = ["python", "main_brain.py"]
OUTPUT_LOG = "logs/terminal_output.log"

# === Run Project ===
def run_project():
    print("[terminal_executor] 🔋 Running: main_brain.py")

    try:
        with open(OUTPUT_LOG, 'w', encoding='utf-8') as log_file:
            process = subprocess.Popen(COMMAND, stdout=log_file, stderr=log_file)
            print(f"[terminal_executor] ✅ Process started (PID: {process.pid})")

            # Optional: Run in background and return immediately
            threading.Thread(target=process.wait, daemon=True).start()

    except Exception as e:
        logging.error(f"[terminal_executor] ❌ Failed to start script: {e}")
