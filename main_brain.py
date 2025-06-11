from overlay_ui import launch_overlay, update_overlay, on_listen_trigger, on_send_trigger
import overlay_ui
import voice_listener_vad
from task_router import route_command
from ask_gpt import ask_gpt
from voice_listener_whisper import listen_once

# ✅ Register callback for overlay update
voice_listener_vad.update_overlay_callback = update_overlay

# ✅ Main shared command handler
def process_command(user_input):
    print(f"📤 Processing: {user_input}")
    routed = route_command(user_input)
    if routed:
        return f"✅ Actioned: {user_input}"
    else:
        reply = ask_gpt(user_input)
        return f"🤖 {reply}"

# ✅ Register command handler with overlay
overlay_ui.process_command_callback = process_command

# 🔁 Trigger handlers
def handle_listen_click():
    print("🎤 Listening...")
    transcript = listen_once()
    print("🧠 Transcript:", transcript)
    update_overlay([], "", f"You: {transcript}")
    result = process_command(transcript)
    update_overlay([], "", result)

def handle_send_click(transcript):
    print("⌨️ Text:", transcript)
    update_overlay([], "", f"🔄 Checking: {transcript}")
    result = process_command(transcript)
    update_overlay([], "", result)

# 🚀 Launch UI
def run_overlay_mode():
    print("🔁 Starting Overlay UI")
    on_listen_trigger.append(handle_listen_click)
    on_send_trigger.append(handle_send_click)
    launch_overlay()

if __name__ == "__main__":
    run_overlay_mode()
