"""
Conversation Mode Handler – Continuous mode brain for Friday

Implements:
- System audio streaming via utterance_buffer
- Callback-based processing of final/interim transcripts
- Intent detection, GPT response, logging
"""

from conversation_mode.utterance_buffer import (
    start_streaming_listener,
    stop_streaming_listener
)
from conversation_mode.intent_agent import detect_intent
from conversation_mode.reasoning_core import get_response
from conversation_mode.context_manager import update_context
from conversation_mode.action_selector import should_respond
from conversation_mode.conversation_logger import log_conversation

import threading

# === Runtime Toggle Support ===
_conversation_mode_running = False

# These will be set by overlay UI on init
_overlay_ui_callback = None
_transcript_ui_callback = None

def start_conversation_mode(update_overlay_func, handle_transcript_func):
    """
    Starts continuous conversation mode.
    Registers callbacks for final + interim STT results.
    """
    global _conversation_mode_running, _overlay_ui_callback, _transcript_ui_callback

    if _conversation_mode_running:
        print("⚠️ Conversation mode already running.")
        return

    _overlay_ui_callback = update_overlay_func
    _transcript_ui_callback = handle_transcript_func
    _conversation_mode_running = True

    print("🎤 Friday Conversation Mode Active (stream-based)...")

    # Start STT stream
    start_streaming_listener(
        on_final_callback=on_final_transcript,
        on_interim_callback=on_interim_update
    )

def stop_conversation_mode():
    """
    Stops the continuous streaming STT listener.
    """
    global _conversation_mode_running

    if _conversation_mode_running:
        print("🟡 Conversation Mode Stop requested.")
        stop_streaming_listener()
        _conversation_mode_running = False
        print("🛑 Streaming STT stopped.")
    else:
        print("⚠️ Conversation Mode is not running.")

def on_interim_update(text: str):
    """
    Optional UI update for interim STT results.
    """
    print(f"💬 Interim: {text}")
    if _transcript_ui_callback:
        _transcript_ui_callback(f"[Interim] {text}")

def on_final_transcript(transcript: str):
    """
    Called by utterance_buffer when a full sentence is finalized.
    Runs full reasoning + UI update in a background thread.
    """
    transcript = transcript.strip()
    if not transcript:
        print("⚠️ Empty final transcript received. Skipping.")
        return

    print(f"👂 Final transcript: {transcript}")

    # Show transcript in UI
    if _transcript_ui_callback:
        _transcript_ui_callback(transcript)

    def process():
        try:
            if not should_respond(transcript):
                print("⏩ Skipping further processing due to cooldown or duplicate.")
                return

            print(f"📥 Processing: {transcript}")
            intent = detect_intent(transcript)
            print(f"🧠 Intent: {intent}")

            response = get_response(transcript, intent)
            print(f"📤 GPT Response: {response}")

            update_context(transcript, intent, response)
            print("🗃️ Context updated.")

            log_conversation(transcript, intent, response)
            print("📝 Logged conversation to file.")

            if _overlay_ui_callback:
                _overlay_ui_callback([transcript, response], "Conversation", f"🤖 {response}")

        except Exception as e:
            print(f"❌ Error in process(): {e}")

    threading.Thread(target=process).start()

def run_single_utterance(transcript: str) -> str:
    """
    Manual call for single transcript (e.g. typed or recorded).
    """
    transcript = transcript.strip()
    print(f"📥 Manual Transcript: {transcript}")
    try:
        if not should_respond(transcript):
            print("⏩ Skipping (manual): Cooldown or duplicate.")
            return ""

        intent = detect_intent(transcript)
        print(f"🧠 Intent (manual): {intent}")

        response = get_response(transcript, intent)
        print(f"📤 GPT Response (manual): {response}")

        update_context(transcript, intent, response)
        log_conversation(transcript, intent, response)
        return response

    except Exception as e:
        print(f"❌ Error in run_single_utterance: {e}")
        return "⚠️ Failed to process input."
