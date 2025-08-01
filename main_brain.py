from memory_manager import load_memory
load_memory()

from overlay_ui import launch_overlay, update_overlay, on_listen_trigger, on_send_trigger, ask_with_model
import overlay_ui
import voice_listener_vad
from voice_listener_whisper import listen_once
from voice_listener_realtime import start_continuous_mode, stop_continuous_mode

# ✅ Register overlay update callback for legacy VAD
voice_listener_vad.update_overlay_callback = update_overlay

# ✅ Simplified command handler (GPT only)
def process_command(user_input):
    print(f"\n📤 Processing: {user_input}")
    reply = ask_with_model(user_input)
    return reply if reply.startswith("🤖") else f"🤖 {reply}"

# ✅ Register command handler with overlay
overlay_ui.process_command_callback = process_command

# 🔁 Trigger handlers for manual voice & text buttons
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