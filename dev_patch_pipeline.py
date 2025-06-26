"""
🚀 Dev Patch Pipeline (Test Entry)
--------------------------------------
Simulates end-to-end flow for: patch -> run -> confirm -> log
"""

from agent_core.intent_classifier import classify_clipboard_content
from agent_core.context_tracker import update_last_clipboard
from agent_core.terminal_executor import run_project
from agent_core.output_analyzer import analyze_output
from agent_core.feedback_listener import ask_for_feedback

# === Test Input ===
clipboard_text = """
def toggle_followup_mode():
    print("[interview_handler] \u2705 Follow-up Mode logic triggered.")
    # TODO: implement conditions for thread termination
"""

# Simulate known file context (e.g., auto-filled by ChatGPT response)
task_context = {
    "task_type": "code_patch",
    "raw_text": clipboard_text,
    "file_guess": "interview_mode_handler.py",
    "function_guess": "toggle_followup_mode"
}

if __name__ == "__main__":
    print("\n[dev_patch_pipeline] 🚀 Starting test pipeline...")
    update_last_clipboard(clipboard_text)
    classify_clipboard_content(clipboard_text)

    print("\n[dev_patch_pipeline] 🔋 Running Friday...")
    run_project()

    print("\n[dev_patch_pipeline] 🔜 Analyzing output...")
    result = analyze_output()

    print("\n[dev_patch_pipeline] 🤔 Getting feedback...")
    ask_for_feedback(task_summary={
        "file": task_context["file_guess"],
        "summary": "Patch toggle_followup_mode()"
    }, status=result)

    print("\n[dev_patch_pipeline] 🚀 Test pipeline complete.")
