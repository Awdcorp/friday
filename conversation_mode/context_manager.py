# conversation_mode/context_manager.py

"""
Context Manager – Maintains short-term memory for Friday's brain.

Responsibilities:
- Store last few user + AI exchanges
- Track active task/topic
- Provide context string for prompt building
- Allow updates when new message comes in
"""

import time

# In-memory rolling store (can be replaced with persistent memory later)
CONTEXT_HISTORY = []  # each item: {'timestamp': ..., 'role': 'user'|'assistant', 'text': ...}

# Max messages to retain in short-term memory
MAX_HISTORY = 6


def update_context(transcript: str, intent: str, response: str):
    """
    Adds the latest interaction to memory history.
    Stores both user input and assistant reply.
    Logs what was added.
    """
    now = time.time()

    CONTEXT_HISTORY.append({'timestamp': now, 'role': 'user', 'text': transcript})
    CONTEXT_HISTORY.append({'timestamp': now, 'role': 'assistant', 'text': response})

    # Trim memory if too long
    if len(CONTEXT_HISTORY) > MAX_HISTORY:
        print(f"🧹 Trimming context history: {len(CONTEXT_HISTORY)} → {MAX_HISTORY}")
        del CONTEXT_HISTORY[:len(CONTEXT_HISTORY) - MAX_HISTORY]

    print(f"🧠 Context Updated – Intent: {intent}")
    print(f"👤 User: {transcript}")
    print(f"🤖 Friday: {response}")


def get_recent_context() -> str:
    """
    Returns a formatted context string of recent conversation history
    for prompt_builder to include in GPT queries.
    Logs the full output string returned.
    """
    if not CONTEXT_HISTORY:
        print("📭 No prior context to include.")
        return "No prior context."

    parts = []
    for item in CONTEXT_HISTORY:
        who = "You" if item['role'] == 'user' else "Friday"
        parts.append(f"{who}: {item['text']}")

    full_context = "\n".join(parts)
    print("📚 Providing recent context to prompt builder:\n" + full_context)
    return full_context
