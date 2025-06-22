"""
interview_mode_handler.py
--------------------------
Controls Interview Mode: system audio listening, question filtering,
GPT interaction, and response logging.
"""

import time
import threading
from .ask_gpt_interview import ask_gpt_interview
from .interview_logger import log_qa
from .interview_prompt_profile import engineer_prompt
from voice_listener_system import start_system_listener, stop_system_listener

# Internal state to track session context
interview_state = {
    "mode": "IDLE",          # "IDLE" or "ANSWERING"
    "last_question": None,
    "last_answer": None,
    "last_time": 0
}

def should_skip(transcript):
    """
    Determines whether to ignore the transcript (filler/noise).
    """
    if not transcript:
        return True
    if len(transcript.split()) < 3:
        return True
    fillers = ["hmm", "okay", "ok", "alright", "yes", "no", "fine", "sure"]
    if any(f in transcript.lower() for f in fillers):
        return True
    return False

def start_interview_mode(update_text_callback, response_callback):
    """
    Starts Interview Mode with system audio listener.
    Shows STT transcriptions in output_text, GPT responses in popup.
    """

    def on_transcript(transcript):
        print(f"🎧 Transcript Received: {transcript}")

        # Skip irrelevant or short inputs
        if should_skip(transcript):
            print("⚠️ Skipped filler or non-question input.")
            return

        global interview_state

        # Append to previous question if it's a follow-up
        if interview_state["mode"] == "ANSWERING":
            print("🔁 Treating as follow-up...")
            transcript = f"{interview_state['last_question']} Follow-up: {transcript}"

        def run():
            print("⏳ Interview GPT thread started...")
            # Query GPT with the question
            answer = ask_gpt_interview(transcript)

            # Respond via UI callback
            response_callback(f"🤖 {answer}")

            # Log Q&A
            log_qa(transcript, answer)

            # Update internal state
            interview_state.update({
                "mode": "ANSWERING",
                "last_question": transcript,
                "last_answer": answer,
                "last_time": time.time()
            })

        threading.Thread(target=run).start()

    print("🚀 Interview Mode Activated")
    start_system_listener(update_text_callback, on_transcript)

def stop_interview_mode():
    """
    Manually stops Interview Mode and its system listener.
    """
    print("🛑 Interview Mode Deactivated")
    stop_system_listener()
