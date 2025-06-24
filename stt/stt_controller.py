# stt/stt_controller.py
"""
Unified STT controller to manage mic/system/hybrid audio input.
Handles listener registration, thread management, and lock-based access control.
"""

import threading
from stt import mic_listener, system_listener
from stt.config import stt_locks, listener_registry, default_settings

# === Thread handles ===
mic_thread = None
system_thread = None

# === Control: Start STT ===
def start_stt(
    mode="system",
    caller="unknown",
    dispatch_callback=None,
    command_callback=None,
    language=None,
    backend=None,
    punctuation=None,
    model=None,
    force=False
):
    global mic_thread, system_thread

    # Load global defaults if not provided
    language = language or default_settings["language"]
    backend = backend or default_settings["backend"]
    punctuation = punctuation if punctuation is not None else default_settings["punctuation"]
    model = model or default_settings["model"]

    lock = stt_locks.get(mode)
    if lock is not None and lock != caller:
        if not force:
            print(f"⛔ STT '{mode}' is locked by '{lock}'. Use force=True to override.")
            return
        print(f"⚠️ Forcing STT override: {lock} → {caller}")

    # Lock this mode
    stt_locks[mode] = caller
    listener_registry[mode].append(dispatch_callback)

    # === Start corresponding thread ===
    def wrapped():
        if mode == "mic":
            mic_listener.start(
                language=language,
                backend=backend,
                punctuation=punctuation,
                model=model,
                dispatch_callback=dispatch_to_listeners(mode),
                command_callback=command_callback
            )
        elif mode == "system":
            system_listener.start(
                language=language,
                backend=backend,
                punctuation=punctuation,
                model=model,
                dispatch_callback=dispatch_to_listeners(mode),
                command_callback=command_callback
            )

    thread = threading.Thread(target=wrapped)
    thread.start()

    if mode == "mic":
        mic_thread = thread
    elif mode == "system":
        system_thread = thread

# === Dispatch helper ===
def dispatch_to_listeners(mode):
    def dispatch(text, is_final=True):
        for callback in listener_registry[mode]:
            callback(text, is_final)
    return dispatch

# === Stop STT ===
def stop_stt(mode, caller="unknown"):
    if stt_locks.get(mode) != caller:
        print(f"🔒 Cannot stop STT '{mode}' — lock owned by {stt_locks.get(mode)}")
        return

    print(f"🛑 Stopping STT '{mode}' for caller '{caller}'")
    stt_locks[mode] = None
    listener_registry[mode] = []

    if mode == "mic":
        mic_listener.stop()
    elif mode == "system":
        system_listener.stop()

# === Register additional listeners ===
def register_listener(mode, callback):
    listener_registry[mode].append(callback)

# === Reset all STT ===
def reset_all():
    print("🔁 Resetting all STT states")
    stop_stt("mic", stt_locks.get("mic"))
    stop_stt("system", stt_locks.get("system"))
