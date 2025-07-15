"""
Interview Mode Handler
--------------------------
Controls Interview Mode: system or mic audio listening, question filtering,
GPT interaction, question detection, context tracking, and response logging.
"""

import time
import threading
from .ask_gpt_interview import ask_gpt_interview
from .interview_logger import log_qa
from .interview_context import update_interview_context
from .question_detection import detect_question  # ✅ New question detection module
from voice_listener_system import start_system_listener, stop_system_listener
from voice_listener_google import start_mic_listener, stop_mic_listener
from .raw_buffer_handler import start_raw_buffer_handler, add_fragment

# === Internal state to track session context
interview_state = {
    "mode": "IDLE",                       # Current mode: LISTENING, ANSWERING, etc.
    "last_question": None,               # Last asked question
    "last_answer": None,                 # Last given answer
    "last_time": 0,                      # Timestamp of last interaction
    "program_thread_active": False,      # Whether in the middle of a programming thread
    "program_topic": None,               # Active topic of the thread
    "followup_count": 0,                 # Number of follow-ups in current thread
    "program_anchor_question": None,     # Initial anchor question of the thread
    "program_anchor_answer": None,       # Anchor answer
    "listener_source": "system"          # mic or system audio
}

# === Start Interview Mode ===
def start_interview_mode(update_text_callback, response_callback, profile="software_engineer", source="system"):
    """
    Launches the Interview Mode and routes live transcription to GPT Q&A pipeline.
    """
    start_raw_buffer_handler(callback=response_callback)

    def on_transcript(transcript):
        print(f"\n[interview_handler] 🎧 Transcript Received: {transcript}")

        add_fragment(transcript)

        def run(transcript=transcript):
            print("\n[interview_handler] 🧠 Starting GPT processing thread...")

            # === Step 1: Detect Question Intent ===
            if profile == "software_engineer":
                result = detect_question(transcript)

                # Skip if more fragments are needed or input is irrelevant
                if result.get("intent") in {"waiting_for_more_input", "irrelevant_or_incomplete"}:
                    print(f"[interview_handler] ⏳ Buffering... Intent: {result.get('intent')}")
                    return

                # Extract useful info
                intent = result["intent"]
                is_programming = result.get("is_programming", False)
                topic = result.get("topic", "")
                corrected_text = result.get("current_input", transcript)
                is_follow_up = result.get("is_follow_up", False)

                print(f"[interview_handler] 🧠 Intent: {intent} | Programming: {is_programming} | Topic: {topic} | Follow-up: {is_follow_up}")

                # === Step 2: Determine Popup UI Behavior ===
                replace_popup = True
                popup_id = 1

                if intent == "program_start":
                    # New programming thread starts
                    interview_state.update({
                        "program_thread_active": True,
                        "program_topic": topic,
                        "followup_count": 0
                    })
                    popup_id = 1

                elif is_follow_up and interview_state["program_thread_active"]:
                    # Inside a programming thread: follow-up
                    interview_state["followup_count"] += 1
                    popup_id = 2  # Use follow-up popup

                    if interview_state["followup_count"] > 3:
                        # Auto-end thread after 3 follow-ups
                        interview_state.update({
                            "program_thread_active": False,
                            "program_topic": None,
                            "followup_count": 0,
                            "program_anchor_question": None,
                            "program_anchor_answer": None
                        })

            else:
                # For other profiles, skip intent logic
                print("[interview_handler] 🧾 Skipping intent logic for non-programming profile.")
                corrected_text = transcript
                popup_id = 1
                replace_popup = True

            # === Step 3: Send to GPT ===
            print("[interview_handler] 🚀 Sending prompt to GPT...")
            answer = ask_gpt_interview(corrected_text, profile=profile)

            # === Step 4: Update UI and Logs ===
            print("[interview_handler] 📤 Sending answer to UI and logger...")
            response_callback(f"🤖 {answer}", replace_popup=replace_popup, popup_id=popup_id)
            log_qa(corrected_text, answer)
            update_interview_context(corrected_text, answer)

            # === Step 5: Update Internal State ===
            interview_state.update({
                "mode": "ANSWERING",
                "last_question": corrected_text,
                "last_answer": answer,
                "last_time": time.time()
            })

            if profile == "software_engineer" and intent == "program_start":
                # Save anchor for this thread
                interview_state["program_anchor_question"] = corrected_text
                interview_state["program_anchor_answer"] = answer

            print("[interview_handler] ✅ Interview Q&A complete.")

        # Run processing in background thread
        threading.Thread(target=run).start()

    # === Start Audio Listener ===
    print(f"[interview_handler] 🚀 Interview Mode Activated | Source: {source}")
    interview_state["listener_source"] = source

    if source == "mic":
        start_mic_listener(update_text_callback, on_transcript)
    else:
        start_system_listener(update_text_callback, on_transcript)

# === Stop Interview Mode ===
def stop_interview_mode():
    print("[interview_handler] 🛑 Interview Mode Deactivated")
    if interview_state.get("listener_source") == "mic":
        stop_mic_listener()
    else:
        stop_system_listener()