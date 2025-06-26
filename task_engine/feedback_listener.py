"""
🤔 Feedback Listener
------------------------
After task execution, asks the user if the result was correct.
Logs feedback into action log for evaluation.
"""

from .action_logger import log_action

def ask_for_feedback(task_summary, status):
    print("\n[feedback_listener] 🤔 Task complete:")
    print(f" - Summary: {task_summary}")
    print(f" - Status: {status}")

    feedback = input("\nDid it work as expected? (yes/no): ").strip().lower()

    log_action({
        "task_type": "code_patch",
        "file": task_summary.get("file"),
        "status": status,
        "user_feedback": feedback,
        "summary": task_summary.get("summary")
    })

    if feedback == "no":
        print("[feedback_listener] ⚠️ Noted. We can roll back or retry later.")
    else:
        print("[feedback_listener] ✅ Great. Feedback saved.")
