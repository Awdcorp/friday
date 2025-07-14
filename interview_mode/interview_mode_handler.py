"""
Interview Mode Handler
--------------------------
Controls Interview Mode: system or mic audio listening, question filtering,
GPT interaction, intent detection, context tracking, and response logging.
"""

import time
import threading
from .ask_gpt_interview import ask_gpt_interview
from .interview_logger import log_qa
from .interview_context import update_interview_context
from .interview_intent import detect_interview_intent
from voice_listener_system import start_system_listener, stop_system_listener
from voice_listener_google import start_mic_listener, stop_mic_listener

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
    "program_anchor_answer": None,
    "listener_source": "system"  # Track active listener type
}

# === Core Listener Setup ===
def start_interview_mode(update_text_callback, response_callback, profile="software_engineer", source="system"):
    def on_transcript(transcript):
        print(f"\n[interview_handler] 🎧 Transcript Received: {transcript}")

        def run(transcript=transcript):
            print("\n[interview_handler] 🧠 Starting GPT processing thread...")

            # === For software engineer profile, run intent detection logic
            if profile == "software_engineer":
                anchor_q = interview_state.get("program_anchor_question")
                anchor_a = interview_state.get("program_anchor_answer")

                # Step 1: Intent Detection
                intent_result = detect_interview_intent(transcript, anchor_q, anchor_a)
                intent = intent_result["intent"]
                corrected_text = intent_result.get("corrected_text", transcript)
                is_programming = intent_result.get("is_programming", False)
                topic = intent_result.get("topic", "")
                follow_up = intent_result.get("follow_up", False)

                print(f"[interview_handler] 🧠 Intent: {intent} | Topic: {topic} | Programming: {is_programming} | Follow-up: {follow_up}")

                # Step 2: Determine popup and thread context
                replace_popup = True
                popup_id = 1

                if intent == "program_start":
                    interview_state.update({
                        "program_thread_active": True,
                        "program_topic": topic,
                        "followup_count": 0
                    })
                    popup_id = 1

                elif intent == "program_follow_up" and interview_state["program_thread_active"]:
                    interview_state["followup_count"] += 1
                    popup_id = 2

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

            else:
                print("[interview_handler] 🧾 Skipping intent logic for non-programming profile.")
                corrected_text = transcript
                popup_id = 1
                replace_popup = True

            # Step 3: Ask GPT
            print("[interview_handler] 🚀 Sending prompt to GPT...")
            answer = ask_gpt_interview(corrected_text, profile=profile)

            # Step 4: Update UI + Log
            print("[interview_handler] 📤 Sending answer to UI and logger...")
            response_callback(f"🤖 {answer}", replace_popup=replace_popup, popup_id=popup_id)
            log_qa(corrected_text, answer)
            update_interview_context(corrected_text, answer)

            # Step 5: Final state update
            interview_state.update({
                "mode": "ANSWERING",
                "last_question": corrected_text,
                "last_answer": answer,
                "last_time": time.time()
            })

            if profile == "software_engineer" and intent == "program_start":
                interview_state["program_anchor_question"] = corrected_text
                interview_state["program_anchor_answer"] = answer

            print("[interview_handler] ✅ Interview Q&A complete.")

        threading.Thread(target=run).start()

    # === Listener Routing ===
    print(f"[interview_handler] 🚀 Interview Mode Activated | Source: {source}")
    interview_state["listener_source"] = source

    if source == "mic":
        start_mic_listener(update_text_callback, on_transcript)
    else:
        start_system_listener(update_text_callback, on_transcript)

def stop_interview_mode():
    print("[interview_handler] 🛑 Interview Mode Deactivated")
    if interview_state.get("listener_source") == "mic":
        stop_mic_listener()
    else:
        stop_system_listener()
