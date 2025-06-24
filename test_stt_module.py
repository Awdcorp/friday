# test_stt_module.py
import time
from stt.stt_controller import start_stt, stop_stt

# === Callback to receive transcript
def handle_text_output(text, is_final):
    prefix = "🧠 Final" if is_final else "💬 Interim"
    print(f"{prefix}: {text}")

# === Callback to simulate mode-specific logic
def handle_command_logic(transcript):
    print(f"[Command] Received: {transcript}")
    if "stop listening" in transcript.lower():
        print("🛑 Stop command detected — stopping STT.")
        stop_stt(mode, caller="test")

# === Configuration
mode = "system"   # Change to "mic" to test mic input instead
caller = "test"

print(f"🎙️ Starting STT test in '{mode}' mode...")
start_stt(
    mode=mode,
    caller=caller,
    language="en-IN",
    dispatch_callback=handle_text_output,
    command_callback=handle_command_logic
)

# === Let it run
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("\n🛑 Keyboard interrupt — stopping manually.")
    stop_stt(mode, caller)
