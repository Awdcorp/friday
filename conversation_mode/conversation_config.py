# conversation_mode/conversation_config.py

"""
Global configuration for Friday's conversation mode.
Allows switching audio input strategy.
"""

# Available options:
# "mic"     → Mic only
# "system"  → System audio only (e.g., Voicemeeter)
# "both"    → Capture mic and system audio together
AUDIO_INPUT_MODE = "both"

def set_audio_input_mode(mode):
    """
    Update AUDIO_INPUT_MODE in memory and persist if needed.
    """
    global AUDIO_INPUT_MODE
    if mode in ("mic", "system", "both"):
        AUDIO_INPUT_MODE = mode
        print(f"🔧 Audio Input Mode set to: {mode}")
    else:
        print(f"⚠️ Invalid audio input mode: {mode}")

