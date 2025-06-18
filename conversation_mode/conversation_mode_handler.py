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

# === Runtime Toggle Support ===
_conversation_mode_running = False

def run_conversation_loop(update_overlay):
    """
    Main blocking loop to run Friday's smart voice mode.
    """
    print("🎤 Friday Conversation Mode Active...")

    while True:
        try:
            # 1. Listen and get transcript (blocking)
            transcript = get_next_utterance()
            if not transcript:
                continue  # skip empty

            print(f"👂 Heard: {transcript}")

            # 2. Cooldown & duplication check
            if not should_respond(transcript):
                continue

            # 3. Classify the intent
            intent = detect_intent(transcript)

            # 4. Get smart response from reasoning core
            response = get_response(transcript, intent)

            # 5. Update short-term memory/context
            update_context(transcript, intent, response)

            # 6. Show reply in UI – ✅ FIXED ARGUMENTS
            update_overlay([transcript, response], "Conversation", f"🤖 {response}")

            # 7. Save log
            log_conversation(transcript, intent, response)

        except KeyboardInterrupt:
            print("🛑 Exiting conversation mode...")
            break

        except Exception as e:
            print(f"❌ Loop Error: {e}")

def start_conversation_mode(update_overlay_func):
    """
    Starts the conversation loop in a background thread.
    Called when user enables 🎙️ Passive Mode.
    """
    import threading

    global _conversation_mode_running
    if _conversation_mode_running:
        print("⚠️ Conversation mode already running.")
        return

    def _loop():
        global _conversation_mode_running
        _conversation_mode_running = True
        try:
            run_conversation_loop(update_overlay_func)
        finally:
            _conversation_mode_running = False

    thread = threading.Thread(target=_loop, daemon=True)
    thread.start()
    print("🟢 Conversation Mode Started in background.")

def stop_conversation_mode():
    """
    Stops the conversation loop – soft stop (requires you to interrupt).
    You can extend this with an event/flag to break the loop.
    """
    global _conversation_mode_running
    if _conversation_mode_running:
        print("🟡 Conversation Mode Stop requested. Use Ctrl+C to exit loop.")
        # You may set a flag here for a graceful exit.
    else:
        print("⚠️ Conversation Mode is not running.")
