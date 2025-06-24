# stt/whisper_backend.py
"""
Provides Whisper-based transcription fallback for STT system mode.
Can use local or remote inference depending on integration.
"""

def whisper_transcribe_buffer(audio_bytes):
    """
    Transcribes raw PCM audio using Whisper backend.
    You can plug in:
    - local faster-whisper
    - OpenAI Whisper API
    - whisper-jax, etc.
    
    Args:
        audio_bytes (bytes): PCM audio bytes from system stream

    Returns:
        str: transcribed text (or "" if failed)
    """
    # TODO: Replace this with actual Whisper integration
    print("🔄 Whisper fallback transcription (placeholder)")
    return "[Whisper transcription placeholder]"
