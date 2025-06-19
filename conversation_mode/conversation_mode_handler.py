"""
Main Loop – Friday's Conversation Mode Brain

This file ties together:
- Audio capture (utterance_buffer)
- Intent detection
- GPT/local reasoning
- Context tracking
- Cooldown & dedup logic
- UI response
- Conversation logging

Runs in a continuous loop to simulate a real intelligent assistant.
"""

from conversation_mode.utterance_buffer import get_next_utterance
from conversation_mode.intent_agent import detect_intent
from conversation_mode.reasoning_core import get_response
from conversation_mode.context_manager import update_context
from conversation_mode.action_selector import should_respond
from conversation_mode.conversation_logger import log_conversation

import threading

# === Runtime Toggle Support ===
_conversation_mode_running = False
_stop_event = threading.Event()

def run_conversation_loop(update_overlay, handle_transcript):
    """
    Main blocking loop to run Friday's smart voice mode.
    """
    global _conversation_mode_running
    print("🎤 Friday Conversation Mode Active...")
    _stop_event.clear()

    while not _stop_event.is_set():
        try:
            # 1. Listen and get transcript (blocking)
            transcript = get_next_utterance()
            if not transcript:
                continue

            print(f"👂 Heard: {transcript}")

            # 2. Show raw input (before classification) on UI
            handle_transcript(transcript)

            # 3. Cooldown & duplication check
            if not should_respond(transcript):
                continue

            # 4. Classify the intent
            intent = detect_intent(transcript)

            # 5. Get smart response from reasoning core
            response = get_response(transcript, intent)

            # 6. Update short-term memory/context
            update_context(transcript, intent, response)

            # 7. Show reply in UI
            update_overlay([transcript, response], "Conversation", f"🤖 {response}")

            # 8. Save log
            log_conversation(transcript, intent, response)

        except Exception as e:
            print(f"❌ Loop Error: {e}")
            continue

def start_conversation_mode(update_overlay_func, handle_transcript_func):
    """
    Starts the conversation loop in a background thread.
    Called when user enables 🎙️ Passive Mode.
    """
    global _conversation_mode_running

    if _conversation_mode_running:
        print("⚠️ Conversation mode already running.")
        return

    def _loop():
        global _conversation_mode_running
        _conversation_mode_running = True
        try:
            run_conversation_loop(update_overlay_func, handle_transcript_func)
        finally:
            _conversation_mode_running = False

    thread = threading.Thread(target=_loop, daemon=True)
    thread.start()
    print("🟢 Conversation Mode Started in background.")

def run_single_utterance(transcript: str) -> str:
    """
    Allows manual routing of a transcript (e.g., from UI text/voice input).
    Includes all memory, intent, and logging logic.
    """
    try:
        if not should_respond(transcript):
            return ""

        intent = detect_intent(transcript)
        response = get_response(transcript, intent)
        update_context(transcript, intent, response)
        log_conversation(transcript, intent, response)
        return response

    except Exception as e:
        print(f"❌ Error in run_single_utterance: {e}")
        return "⚠️ Failed to process input."

def stop_conversation_mode():
    """
    Stops the conversation loop – soft stop.
    """
    global _conversation_mode_running

    if _conversation_mode_running:
        print("🟡 Conversation Mode Stop requested.")
        _stop_event.set()
    else:
        print("⚠️ Conversation Mode is not running.")
