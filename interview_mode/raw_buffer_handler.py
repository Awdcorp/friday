"""
raw_buffer_handler.py
---------------------
Handles raw speech fragments and sends to GPT after 8 seconds of silence.
Runs independently of Interview Mode. Shows results in popup_id=3.
"""

import threading
import time
import os
from openai import OpenAI
from dotenv import load_dotenv
from .interview_prompt_profile import PROMPT_PROFILES

# === Load API key ===
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# === Configuration ===
SILENCE_TIMEOUT = 8
DEBUG = True
MAX_HISTORY = 10
MAX_CONTEXT_TURNS = 3
ACTIVE_PROFILE = "software_engineer"

# === Internal state ===
buffer_fragments = []
last_input_time = None
is_processing = False
active = False
buffer_lock = threading.Lock()
silence_thread = None
response_callback = None
on_done_callback = None

# === New: Popup and GPT memory
raw_response_history = []
conversation_history = []


def debug(msg):
    if DEBUG:
        print(msg)


def start_raw_buffer_handler(callback=None, on_done=None):
    """
    Start the raw buffer silence handler.
    - callback: function(text, popup_id=3) to show result in UI
    - on_done: optional hook after GPT response
    """
    global active, silence_thread, response_callback, on_done_callback

    response_callback = callback
    on_done_callback = on_done
    active = True
    silence_thread = threading.Thread(target=_silence_watcher, daemon=True)
    silence_thread.start()

    debug("[raw_buffer_handler] ✅ Handler started")


def stop_raw_buffer_handler():
    """
    Stop the buffer silence watcher.
    """
    global active
    active = False
    debug("[raw_buffer_handler] 🛑 Handler stopped")


def add_fragment(fragment):
    """
    Add a new transcript chunk to the buffer.
    Resets the silence timer.
    """
    global last_input_time
    with buffer_lock:
        buffer_fragments.append(fragment.strip())
        last_input_time = time.time()

    debug(f"[raw_buffer_handler] ➕ Fragment received: \"{fragment.strip()}\"")


def _silence_watcher():
    """
    Monitors silence by checking time since last fragment.
    If timeout occurs, triggers GPT processing.
    """
    global last_input_time, is_processing, conversation_history, raw_response_history

    while active:
        time.sleep(1)

        with buffer_lock:
            if not buffer_fragments or last_input_time is None:
                continue

            elapsed = time.time() - last_input_time

            # Auto-clear old history after 60s of no input
            if elapsed > 60:
                conversation_history.clear()
                raw_response_history.clear()
                debug("[raw_buffer_handler] ⏳ Long silence: clearing history")

            if elapsed < SILENCE_TIMEOUT or is_processing:
                continue

            combined = " ".join(buffer_fragments).strip()
            buffer_fragments.clear()
            is_processing = True  # ✅ Move up to avoid race
            debug(f"[silence_watcher] ⏱️ No input for {SILENCE_TIMEOUT}s. Triggering GPT...")

        threading.Thread(target=_process_buffer, args=(combined,), daemon=True).start()


def _process_buffer(text):
    """
    Sends the buffer to GPT and handles the result.
    Includes last 3-turn conversation memory and scrollable popup history.
    """
    global is_processing, conversation_history, raw_response_history

    debug("[raw_buffer_handler] 🧠 Processing buffer...")
    debug("👉 " + text)

    try:
        system_prompt = PROMPT_PROFILES.get(ACTIVE_PROFILE, PROMPT_PROFILES["software_engineer"]).strip()
        messages = [{"role": "system", "content": system_prompt}]

        # Add last 3 user+assistant exchanges with improved wording
        for i in range(0, len(conversation_history[-6:]), 2):
            prev_user = conversation_history[-6:][i]["content"]
            prev_gpt = conversation_history[-6:][i+1]["content"]
            messages.append({"role": "user", "content": f"Earlier, the user asked: {prev_user}"})
            messages.append({"role": "assistant", "content": f"The assistant replied: {prev_gpt}"})

        # Add current user message
        messages.append({"role": "user", "content": text})

        # === Call GPT with timeout ===
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages,
            temperature=0.5,
            timeout=15  # ✅ timeout added
        )
        answer = response.choices[0].message.content.strip()

        # Update memory
        conversation_history.append({"role": "user", "content": text})
        conversation_history.append({"role": "assistant", "content": answer})
        if len(conversation_history) > 6:
            conversation_history = conversation_history[-6:]

        raw_response_history.append(f"🧠 {answer}")
        if len(raw_response_history) > MAX_HISTORY:
            raw_response_history.pop(0)

        popup_text = "\n\n".join(raw_response_history)

        if response_callback:
            response_callback(popup_text, popup_id=3)
        else:
            print("[raw_buffer_handler] 🤖 GPT Answer:\n", answer)

    except Exception as e:
        print("[raw_buffer_handler] ❌ GPT Error:", e)

    finally:
        is_processing = False
        if on_done_callback:
            on_done_callback()
