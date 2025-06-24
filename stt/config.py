# stt/config.py
"""
Shared config and state for STT module.
Tracks locks, active listeners, and default parameters.
"""

# === Global STT lock status (ensures exclusive access per mode)
stt_locks = {
    "mic": None,
    "system": None
}

# === Listener registries (multiple listeners can receive transcript)
listener_registry = {
    "mic": [],
    "system": []
}

# === Default STT behavior (can be overridden per-mode)
default_settings = {
    "language": "en-US",           # Global default language
    "backend": "google",           # 'google' or 'whisper'
    "punctuation": True,           # Automatic punctuation
    "model": "default"             # Google STT model to use
}
