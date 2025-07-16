# interview_context.py

"""
Interview Context Manager
--------------------------
Keeps a rolling memory of the last few interview Q&A pairs.
Used to feed context to GPT or analyze patterns.
"""

import time

# === Module tag for logging ===
MODULE = "[interview_ctx]"

def log(msg):
    print(f"{MODULE} {msg}")

# === Rolling memory store
INTERVIEW_HISTORY = []  # each item: {'time': ..., 'question': ..., 'answer': ...}
MAX_CONTEXT_ENTRIES = 6  # Adjustable rolling window


def update_interview_context(question, answer):
    """
    Adds a Q&A to rolling memory.
    """
    entry = {
        "time": time.time(),
        "question": question.strip(),
        "answer": answer.strip()
    }
    INTERVIEW_HISTORY.append(entry)

    if len(INTERVIEW_HISTORY) > MAX_CONTEXT_ENTRIES:
        removed = len(INTERVIEW_HISTORY) - MAX_CONTEXT_ENTRIES
        del INTERVIEW_HISTORY[:removed]
        log(f"🧹 Trimmed oldest {removed} entries from history.")

    log(f"🧠 Context updated | Q: \"{question.strip()[:50]}\" | A: \"{answer.strip()[:50]}\"")


def get_interview_context_string():
    """
    Builds a string representation of recent Q&A for GPT.
    """
    if not INTERVIEW_HISTORY:
        log("📭 No previous context available.")
        return "No previous interview history."

    formatted = [
        f"Interviewer: {item['question']}\nFriday: {item['answer']}"
        for item in INTERVIEW_HISTORY
    ]
    result = "\n\n".join(formatted)

    log(f"📚 Building context | Entries: {len(INTERVIEW_HISTORY)} | Words: {len(result.split())}")
    log("📝 Preview:\n" + result[:80] + ("... [truncated]" if len(result) > 80 else ""))

    return result


def get_last_interview_qa():
    """
    Returns the most recent question-answer pair, or None if empty.
    """
    return INTERVIEW_HISTORY[-1] if INTERVIEW_HISTORY else None
