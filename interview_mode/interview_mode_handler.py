# interview_mode_handler.py

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
    "mode": "IDLE",          # "IDLE" or "ANSWERING"
    "last_question": None,
    "last_answer": None,
    "last_time": 0
}

# === Skip filters for empty/filler inputs
def should_skip(transcript):
    """
    Determines whether to ignore the transcript (filler/noise).
    """
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
    """
    Starts Interview Mode with system audio listener.
    Shows STT transcriptions in output_text, GPT responses in popup.
    """

    def on_transcript(transcript):
        print(f"\n[interview_handler] 🎧 Transcript Received: {transcript}")

        if should_skip(transcript):
            print("[interview_handler] ⚠️ Skipped filler or short input.")
            return

        global interview_state

        update_text_callback([], "", f"🧠 Final: {transcript}")

        def run(transcript=transcript):
            print("\n[interview_handler] 🧠 Starting GPT processing thread...")

            # === Step 1: Detect Intent
            print("[interview_handler] 🧩 Detecting intent...")
            intent = detect_interview_intent(transcript)
            print(f"[interview_handler] 🧠 Intent Detected: {intent}")

            # === Step 2: Reframe follow-up questions if needed
            if intent == "follow_up":
                print("[interview_handler] 🔁 Handling follow-up intent...")
                prev_q = interview_state.get("last_question") or ""
                prev_a = interview_state.get("last_answer") or ""
                if prev_q and prev_a:
                    print("[interview_handler] 🔗 Attaching previous Q&A context.")
                    transcript = f"""Earlier, the interviewer asked:
"{prev_q}"
And you answered:
"{prev_a}"

Now the follow-up is:
"{transcript}"
"""
                else:
                    print("[interview_handler] ⚠️ No prior context to attach. Proceeding normally.")

            # === Step 3: Sanitize vague questions
            if intent == "question" and len(transcript.strip().split()) <= 4:
                print("[interview_handler] ⚠️ Vague question detected. Auto-clarifying prompt.")
                transcript += " Please explain what you would like to know more about, preferably in the context of programming."

            # === Step 4: GPT Query
            print("[interview_handler] 🚀 Sending prompt to GPT...")
            answer = ask_gpt_interview(transcript)

            # === Step 5: Update UI + Log
            print("[interview_handler] 📤 Sending answer to UI and logger...")
            response_callback(f"🤖 {answer}")
            log_qa(transcript, answer)
            update_interview_context(transcript, answer)

            # === Step 6: Update state
            interview_state.update({
                "mode": "ANSWERING",
                "last_question": transcript,
                "last_answer": answer,
                "last_time": time.time()
            })

            print("[interview_handler] ✅ Interview Q&A complete.")

        threading.Thread(target=run).start()

    print("[interview_handler] 🚀 Interview Mode Activated")
    start_system_listener(update_text_callback, on_transcript)

# === Stop Function ===
def stop_interview_mode():
    """
    Manually stops Interview Mode and its system listener.
    """
    print("[interview_handler] 🛑 Interview Mode Deactivated")
    stop_system_listener()
