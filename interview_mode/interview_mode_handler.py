"""
Interview Mode Handler
--------------------------
Controls Interview Mode: system audio listening, question filtering,
GPT interaction, intent detection, context tracking, and response logging.
"""

import time
import threading
from .ask_gpt_interview import ask_gpt_interview
from .interview_logger import log_qa
from .interview_prompt_profile import engineer_prompt
from .interview_context import update_interview_context
from .interview_intent import detect_interview_intent
from voice_listener_system import start_system_listener, stop_system_listener

# === Internal state to track session context
interview_state = {
    "mode": "IDLE",
    "last_question": None,
    "last_answer": None,
    "last_time": 0,
    "program_thread_active": False,
    "program_topic": None,
    "followup_count": 0,
    "program_anchor_question": None,
    "program_anchor_answer": None
}

# === Skip filters for empty/filler inputs
def should_skip(transcript):
    if not transcript:
        return True
    if len(transcript.strip().split()) < 3:
        return True
    fillers = ["hmm", "okay", "ok", "alright", "yes", "no", "fine", "sure"]
    if any(f in transcript.lower() for f in fillers):
        return True
    return False

# === Core Listener Setup ===
def start_interview_mode(update_text_callback, response_callback):
    def on_transcript(transcript):
        print(f"\n[interview_handler] 🎧 Transcript Received: {transcript}")

        if should_skip(transcript):
            print("[interview_handler] ⚠️ Skipped filler or short input.")
            return

        update_text_callback([], "", f"🧠 Final: {transcript}")

        def run(transcript=transcript):
            print("\n[interview_handler] 🧠 Starting GPT processing thread...")

            # === Step 1: Detect Enhanced Intent using program anchor
            anchor_q = interview_state.get("program_anchor_question")
            anchor_a = interview_state.get("program_anchor_answer")

            intent_result = detect_interview_intent(transcript, anchor_q, anchor_a)
            intent = intent_result["intent"]
            corrected_text = intent_result.get("corrected_text", transcript)
            is_programming = intent_result.get("is_programming", False)
            topic = intent_result.get("topic", "")
            follow_up = intent_result.get("follow_up", False)

            print(f"[interview_handler] 🧠 Intent: {intent} | Topic: {topic} | Programming: {is_programming} | Follow-up: {follow_up}")

            # === Step 2: Determine popup and thread context
            replace_popup = True
            popup_id = 1  # default

            if intent == "program_start":
                interview_state.update({
                    "program_thread_active": True,
                    "program_topic": topic,
                    "followup_count": 0
                })
                popup_id = 1  # new program question will always start in popup 1

            elif follow_up and interview_state["program_thread_active"]:
                interview_state["followup_count"] += 1
                popup_id = 2
                replace_popup = True

                # Auto-end thread after too many followups
                if interview_state["followup_count"] > 3:
                    interview_state.update({
                        "program_thread_active": False,
                        "program_topic": None,
                        "followup_count": 0,
                        "program_anchor_question": None,
                        "program_anchor_answer": None
                    })

            elif intent == "thread_end":
                interview_state.update({
                    "program_thread_active": False,
                    "program_topic": None,
                    "followup_count": 0,
                    "program_anchor_question": None,
                    "program_anchor_answer": None
                })

            # === Step 3: Vague Clarification
            if intent == "clarify":
                corrected_text += " Please clarify what you mean in the context of programming."

            # === Step 4: GPT Query
            print("[interview_handler] 🚀 Sending prompt to GPT...")
            answer = ask_gpt_interview(corrected_text)

            # === Step 5: Update UI + Log
            print("[interview_handler] 📤 Sending answer to UI and logger...")
            response_callback(f"🤖 {answer}", replace_popup=replace_popup, popup_id=popup_id)
            log_qa(corrected_text, answer)
            update_interview_context(corrected_text, answer)

            # === Step 6: Update state
            interview_state.update({
                "mode": "ANSWERING",
                "last_question": corrected_text,
                "last_answer": answer,
                "last_time": time.time()
            })

            # If new program, save as anchor
            if intent == "program_start":
                interview_state["program_anchor_question"] = corrected_text
                interview_state["program_anchor_answer"] = answer

            print("[interview_handler] ✅ Interview Q&A complete.")

        threading.Thread(target=run).start()

    print("[interview_handler] 🚀 Interview Mode Activated")
    start_system_listener(update_text_callback, on_transcript)

def stop_interview_mode():
    print("[interview_handler] 🛑 Interview Mode Deactivated")
    stop_system_listener()
