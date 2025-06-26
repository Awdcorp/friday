"""
🔍 Context Tracker
------------------------
Tracks last copied code or working project context for use in task routing.
"""

# Simple in-memory store for now
context = {
    "last_clipboard": None
}

def update_last_clipboard(text):
    context["last_clipboard"] = text
    print("[context_tracker] 🔍 Clipboard context updated.")

def get_last_clipboard():
    return context["last_clipboard"]
