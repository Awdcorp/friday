from overlay_ui import launch_overlay, update_overlay, on_listen_trigger, on_send_trigger
from ask_gpt import ask_gpt
from voice_listener_whisper import listen_once
from task_router import route_command  # ✅ Added

import threading

def handle_listen_click():
    print("🔘 Listen button clicked")
    result = listen_once()
    print(f"🧠 Transcribed: {result}")
    update_overlay([], "", result or "⚠️ No speech detected")

def handle_send_click(transcript):
    print(f"📤 Sending to GPT or routing: {transcript}")
    update_overlay([], "", f"🔄 Checking command: {transcript}")

    # ✅ Attempt to route system command first
    routed = route_command(transcript)
    if routed:
        update_overlay([], "", f"✅ Actioned: {transcript}")
    else:
        update_overlay([], "", f"🤖 Thinking about: {transcript}")
        reply = ask_gpt(transcript)
        print(f"🤖 GPT: {reply}")
        update_overlay([], "", f"You: {transcript}\n\nFriday: {reply}")

def run_overlay_mode():
    print("🎙️ Running in BUTTON MODE (overlay-based)")
    on_listen_trigger.append(handle_listen_click)
    on_send_trigger.append(handle_send_click)
    launch_overlay()

if __name__ == "__main__":
    run_overlay_mode()
