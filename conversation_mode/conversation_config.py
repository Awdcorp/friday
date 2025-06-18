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
