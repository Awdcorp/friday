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
SILENCE_TIMEOUT = 8  # seconds of no input to trigger GPT
DEBUG = True         # toggle debug logging
MAX_HISTORY = 10     # Number of past GPT responses to keep in popup
MAX_CONTEXT_TURNS = 3  # Number of exchanges (user + assistant) to keep as GPT context
ACTIVE_PROFILE = "software_engineer"

# === Internal state ===
buffer_fragments = []           # List of incoming speech chunks
last_input_time = None          # Timestamp of last input
is_processing = False           # Avoid overlap in GPT responses
active = False                  # Global run flag
buffer_lock = threading.Lock()  # Thread safety for shared buffer
silence_thread = None           # Watcher thread
response_callback = None        # Function to show result in UI
on_done_callback = None         # Optional: hook after GPT response

# === New: Popup and GPT memory
raw_response_history = []       # Scrollable history for popup 3
conversation_history = []       # GPT context memory (last 3 user + assistant turns)


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
    global last_input_time, is_processing

    while active:
        time.sleep(1)

        with buffer_lock:
            if not buffer_fragments or last_input_time is None:
                continue

            elapsed = time.time() - last_input_time
            if elapsed < SILENCE_TIMEOUT:
                continue

            if is_processing:
                debug("[silence_watcher] ⏳ Waiting: GPT already processing...")
                continue

            # Enough silence, prepare to process
            combined = " ".join(buffer_fragments).strip()
            buffer_fragments.clear()
            debug(f"[silence_watcher] ⏱️ No input for {SILENCE_TIMEOUT}s. Triggering GPT...")
        
        # Process in a new thread to avoid blocking loop
        threading.Thread(target=_process_buffer, args=(combined,), daemon=True).start()


def _process_buffer(text):
    """
    Sends the buffer to GPT and handles the result.
    Includes last 3-turn conversation memory and scrollable popup history.
    """
    global is_processing, conversation_history, raw_response_history

    is_processing = True

    debug("[raw_buffer_handler] 🧠 Processing buffer...")
    debug("👉 " + text)

    try:
        # === Build GPT prompt with explicit history ===
        messages = [{"role": "system", "content": PROMPT_PROFILES[ACTIVE_PROFILE].strip()}]

        # Add last 3 user+assistant exchanges with explicit context wording
        for i in range(0, len(conversation_history[-6:]), 2):
            prev_user = conversation_history[-6:][i]["content"]
            prev_gpt = conversation_history[-6:][i+1]["content"]
            messages.append({"role": "user", "content": f"Previously, the user asked: {prev_user}"})
            messages.append({"role": "assistant", "content": f"The assistant answered: {prev_gpt}"})

        # Add current user message
        messages.append({"role": "user", "content": text})


        # === Call GPT ===
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages,
            temperature=0.5
        )
        answer = response.choices[0].message.content.strip()

        # === Update GPT conversation memory ===
        conversation_history.append({"role": "user", "content": text})
        conversation_history.append({"role": "assistant", "content": answer})
        if len(conversation_history) > 6:
            conversation_history = conversation_history[-6:]

        # === Update scrollable history for popup ===
        raw_response_history.append(f"🧠 {answer}")
        if len(raw_response_history) > MAX_HISTORY:
            raw_response_history.pop(0)

        # Combine history into scrollable popup text
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
