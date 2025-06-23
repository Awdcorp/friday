import threading
from interview_mode.interview_intent import detect_interview_intent
from interview_mode.ask_gpt_interview import ask_gpt_interview
from interview_mode.interview_logger import log_qa
from interview_mode.interview_context import update_interview_context
from overlay_ui import handle_interview_response, update_text_box_only

def simulate_input(text):
    print(f"\n🟡 [SIM INPUT]: {text}")
    update_text_box_only([], "", f"🧠 Final: {text}")

    def run():
        result = detect_interview_intent(text)
        intent = result['intent']
        corrected_text = result.get("corrected_text", text)
        is_programming = result.get("is_programming", False)

        print(f"[INTENT] → {intent} | Programming: {is_programming}")

        replace = not (intent == "program_follow_up" and is_programming)

        reply = ask_gpt_interview(corrected_text)
        handle_interview_response(f"🤖 {reply}", replace_popup=replace)

        log_qa(corrected_text, reply)
        update_interview_context(corrected_text, reply)

    threading.Thread(target=run).start()

# === Call test inputs here ===
simulate_input("Write a program to reverse a linked list.")
simulate_input("Can you optimize it?")
simulate_input("Any edge cases?")
simulate_input("What are other methods?")
simulate_input("Let's move on")
