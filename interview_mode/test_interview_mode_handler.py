"""
Test Script for interview_mode_handler.py
Simulates transcript input and prints all outputs using dummy callbacks.
"""

import time
from .interview_mode_handler import start_interview_mode, stop_interview_mode

# === Dummy UI Callbacks ===

def update_text_callback(history, role, text):
    print(f"[UI UPDATE] {role.upper()}: {text}")

def response_callback(answer, replace_popup=True, popup_id=1):
    print(f"[UI RESPONSE] (popup {popup_id}) {'[Replace]' if replace_popup else '[Append]'} → {answer}")

# === Test Setup ===

def run_test(profile="software_engineer", source="system"):
    print("\n--- Running Interview Mode Test ---")

    # Start interview mode with dummy UI callbacks
    start_interview_mode(update_text_callback, response_callback, profile=profile, source=source)

    # Simulate some user inputs (transcripts)
    test_inputs = [
        "Can you explain the difference between call by value and call by reference in C?",
        "Write a C++ program to reverse a linked list.",
        "What if the input list is empty?",
        "Okay",
        "Now switch to Java and do the same",
        "Stop that, tell me what is a pointer again"
    ]

    for i, line in enumerate(test_inputs):
        print(f"\n[TEST INPUT {i+1}] ▶ {line}")
        # Simulate mic/system callback delay
        time.sleep(2)

        # Manually invoke the on_transcript logic (direct call)
        # In real use, this is triggered by the STT listener callback
        # You can call the internal `on_transcript()` if you expose it from the module
        from interview_mode_handler import interview_state  # get current listener source
        if interview_state["listener_source"] == "mic":
            from voice_listener_google import simulate_transcript
            simulate_transcript(line)
        else:
            from voice_listener_system import simulate_transcript
            simulate_transcript(line)

    # Allow final threads to complete
    time.sleep(5)
    stop_interview_mode()

    print("\n--- Test Complete ---")

# === Run if main ===
if __name__ == "__main__":
    run_test()
