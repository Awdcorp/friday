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
from .question_detection import detect_question
from voice_listener_system import start_system_listener, stop_system_listener
from voice_listener_google import start_mic_listener, stop_mic_listener
from .raw_buffer_handler import start_raw_buffer_handler, add_fragment

# === Module tag for logging
MODULE = "[interview]"

def log(msg):
    print(f"{MODULE} {msg}")

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

# === Rolling response memory (used to build scrollable popup text)
raw_response_history = []
MAX_HISTORY = 10

# === Start Interview Mode ===
def start_interview_mode(update_text_callback, response_callback, profile="software_engineer", source="system"):
    """
    Launches the Interview Mode and routes live transcription to GPT Q&A pipeline.
    """
    start_raw_buffer_handler(callback=response_callback)

    def on_transcript(transcript):
        log(f"🎧 Transcript Received: {transcript}")

        add_fragment(transcript)

        def run(transcript=transcript):
            try:
                log("🧠 Processing...")

                # === Step 1: Detect Question Intent ===
                if profile == "software_engineer":
                    result = detect_question(transcript)

                    # Skip if more fragments are needed or input is irrelevant
                    if result.get("intent") in {"waiting_for_more_input", "irrelevant_or_incomplete"}:
                        log(f"⏳ Buffering... Intent: {result.get('intent')}")
                        return

                    # Extract detected info
                    intent = result["intent"]
                    is_programming = result.get("is_programming", False)
                    topic = result.get("topic", "")
                    corrected_text = result.get("current_input", transcript)
                    is_follow_up = result.get("is_follow_up", False)

                    #log(f"🔍 Intent: {intent} | Prog: {is_programming} | Follow: {is_follow_up} | Topic: {topic}")

                    replace_popup = True
                    popup_id = 1

                    if intent == "program_start":
                        interview_state.update({
                            "program_thread_active": True,
                            "program_topic": topic,
                            "followup_count": 0
                        })
                        popup_id = 1

                    elif is_follow_up and interview_state["program_thread_active"]:
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
                    log("🧾 Skipping intent logic for non-programming profile.")
                    corrected_text = transcript
                    popup_id = 1
                    replace_popup = True

                log("🚀 Sending to GPT...")
                answer = ask_gpt_interview(corrected_text, profile=profile)

                # === Build cumulative response text if replacing
                if replace_popup:
                    raw_response_history.append(f"🤖 {answer}")
                    if len(raw_response_history) > MAX_HISTORY:
                        raw_response_history.pop(0)
                    response_text = "\n\n".join(raw_response_history)
                else:
                    response_text = f"🤖 {answer}"

                log(f"📤 Response ready → popup {popup_id}")
                response_callback(response_text, replace_popup=replace_popup, popup_id=popup_id)

                log_qa(corrected_text, answer)
                update_interview_context(corrected_text, answer)

                interview_state.update({
                    "mode": "ANSWERING",
                    "last_question": corrected_text,
                    "last_answer": answer,
                    "last_time": time.time()
                })

                if profile == "software_engineer" and intent == "program_start":
                    interview_state["program_anchor_question"] = corrected_text
                    interview_state["program_anchor_answer"] = answer

                log("✅ Interview Q&A complete.")

            except Exception as e:
                log(f"❌ Error during processing: {e}")

        threading.Thread(target=run).start()

    log(f"🚀 Interview Mode Activated | Source: {source}")
    interview_state["listener_source"] = source

    if source == "mic":
        start_mic_listener(update_text_callback, on_transcript)
    else:
        start_system_listener(update_text_callback, on_transcript)

def stop_interview_mode():
    log("🛑 Interview Mode Deactivated")
    if interview_state.get("listener_source") == "mic":
        stop_mic_listener()
    else:
        stop_system_listener()
