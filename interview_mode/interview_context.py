# interview_context.py

"""
Interview Context Manager
--------------------------
Keeps a rolling memory of the last few interview Q&A pairs.
Used to feed context to GPT or analyze patterns.
"""

import time

# Rolling memory store (in RAM)
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

    # Trim memory if needed
    if len(INTERVIEW_HISTORY) > MAX_CONTEXT_ENTRIES:
        removed = len(INTERVIEW_HISTORY) - MAX_CONTEXT_ENTRIES
        print(f"[interview_context] 🧹 Trimming oldest {removed} entries...")
        del INTERVIEW_HISTORY[:removed]

    print("[interview_context] 🧠 Context Updated:")
    print(" ├─ 👤 Question:", question.strip()[:100])
    print(" └─ 🤖 Answer  :", answer.strip()[:100])


def get_interview_context_string():
    """
    Builds a string representation of recent Q&A for GPT.
    """
    if not INTERVIEW_HISTORY:
        print("[interview_context] 📭 No previous context available.")
        return "No previous interview history."

    formatted = []
    for item in INTERVIEW_HISTORY:
        formatted.append(f"Interviewer: {item['question']}\nFriday: {item['answer']}")

    result = "\n\n".join(formatted)

    print("[interview_context] 📚 Building context for GPT...")
    print(f"[interview_context] 🧾 Entries: {len(INTERVIEW_HISTORY)}")
    print(f"[interview_context] 📝 Word count: {len(result.split())}")
    print("──────────────── Context Preview ───────────────")
    print(result[:500] + ("\n... [truncated]" if len(result) > 500 else ""))
    print("────────────────────────────────────────────────")

    return result

def get_last_interview_qa():
    """
    Returns the most recent question-answer pair, or None if empty.
    """
    if not INTERVIEW_HISTORY:
        return None
    return INTERVIEW_HISTORY[-1]
