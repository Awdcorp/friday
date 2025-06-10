# main_brain.py

from task_router import route_command
from overlay_ui import launch_overlay, update_overlay
from voice_listener_whisper import listen_loop
import time

# 🧠 Test mode commands (simulated GPT output)
test_commands = [
    "Open notepad",
    "Type Hello, this is Friday",
    "Press enter",
    "Click 500 300",
    "Move mouse to 100 200"
]

def run_test_mode():
    print("🔧 Running in TEST MODE (simulated commands)")
    launch_overlay()
    time.sleep(1)  # Give time for overlay to appear

    for command in test_commands:
        print(f"\n🧠 Test command: {command}")
        update_overlay([], "", command)
        route_command(command)
        time.sleep(2)

def run_voice_mode():
    print("🎙️ Running in VOICE MODE (speak your commands naturally)")
    launch_overlay()
    time.sleep(1)  # Let overlay settle
    listen_loop()  # This blocks and continuously listens

if __name__ == "__main__":
    MODE = "voice"  # Change to "test" or "voice"

    if MODE == "test":
        run_test_mode()
    elif MODE == "voice":
        run_voice_mode()
    else:
        print("❌ Invalid MODE. Use 'test' or 'voice'.")
