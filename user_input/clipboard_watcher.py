"""
📋 Clipboard Watcher
---------------------
Continuously monitors clipboard content.
On meaningful copy (code, instruction, etc.), passes to intent_classifier.
"""

import pyperclip
import time
import threading
from .intent_classifier import classify_clipboard_content
from .context_tracker import update_last_clipboard
import logging

# === Config ===
CHECK_INTERVAL = 1.0  # seconds between clipboard checks
MIN_LENGTH = 5        # ignore very short copies

# === Internal State ===
last_clip = ""

# === Callback Dispatcher (replace with router later) ===
def on_clipboard_update(text):
    print(f"[clipboard_watcher] 📋 New clipboard detected:\n{text[:100]}...")
    update_last_clipboard(text)
    classify_clipboard_content(text)  # Step 2 will define this

# === Threaded Watcher ===
def clipboard_watch_loop():
    global last_clip
    while True:
        try:
            current = pyperclip.paste()
            if current != last_clip and len(current.strip()) > MIN_LENGTH:
                last_clip = current
                on_clipboard_update(current)
        except Exception as e:
            logging.warning(f"[clipboard_watcher] Error reading clipboard: {e}")
        time.sleep(CHECK_INTERVAL)

# === Public Starter ===
def start_clipboard_watcher():
    print("[clipboard_watcher] 🟢 Clipboard monitor started...")
    thread = threading.Thread(target=clipboard_watch_loop, daemon=True)
    thread.start()
