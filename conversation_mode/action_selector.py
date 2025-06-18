# conversation_mode/action_selector.py

"""
Action Selector – Decides whether to respond or skip a given transcript.
Handles:
- Cooldown between responses
- Duplicate utterance prevention
- Basic noise/empty input filtering
"""

import time

# === Settings ===
COOLDOWN_SECONDS = 3  # Minimum time gap between replies
DUPLICATE_THRESHOLD = 0.9  # Similarity score (if 90% same, skip)

# Internal state
_last_response_time = 0
_last_transcript = ""


def should_respond(transcript: str) -> bool:
    """
    Returns True if Friday should respond to the given transcript,
    otherwise False (e.g., recent duplicate or cooldown active).
    """

    global _last_response_time, _last_transcript

    now = time.time()

    # 1. Skip if empty
    if not transcript.strip():
        print("⚠️ Skipping: Empty input")
        return False

    # 2. Skip if too soon (cooldown)
    if now - _last_response_time < COOLDOWN_SECONDS:
        print("⏳ Skipping: Cooldown not finished")
        return False

    # 3. Skip if same/similar to last message
    if is_duplicate(transcript, _last_transcript):
        print("🔁 Skipping: Duplicate input")
        return False

    # 4. If passed all checks, update state
    _last_response_time = now
    _last_transcript = transcript
    return True


def is_duplicate(current: str, previous: str) -> bool:
    """
    Simple fuzzy match: compare how similar two strings are.
    Can be replaced with difflib, Jaccard, etc. later.
    """
    if not previous:
        return False

    # Token-level match ratio
    cur_words = set(current.lower().split())
    prev_words = set(previous.lower().split())

    if not cur_words or not prev_words:
        return False

    overlap = len(cur_words & prev_words) / len(cur_words | prev_words)
    return overlap >= DUPLICATE_THRESHOLD
