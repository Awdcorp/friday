# conversation_mode/utterance_buffer.py

"""
Utterance Buffer – Captures spoken input from selected audio source:
- Mic
- System audio
- Both combined

Transcribes using Google STT, with Whisper fallback.
"""

import time
import threading
import io
import pyaudio
import wave

import speech_recognition as sr
from voice_listener_whisper import transcribe_whisper
from conversation_mode.conversation_config import AUDIO_INPUT_MODE
from voice_listener_system import capture_system_audio  # ⬅️ You already have this
# We'll implement mic + merging below

# === Common Settings ===
SAMPLE_RATE = 16000
CHUNK = 1024
RECORD_SECONDS = 5  # For simplicity (can be pause-based later)

recognizer = sr.Recognizer()


def capture_mic_audio():
    """Capture raw audio from the mic."""
    print("🎤 Capturing mic audio...")
    p = pyaudio.PyAudio()
    stream = p.open(format=pyaudio.paInt16,
                    channels=1,
                    rate=SAMPLE_RATE,
                    input=True,
                    frames_per_buffer=CHUNK)

    frames = []
    for _ in range(0, int(SAMPLE_RATE / CHUNK * RECORD_SECONDS)):
        data = stream.read(CHUNK)
        frames.append(data)

    stream.stop_stream()
    stream.close()
    p.terminate()

    return b"".join(frames)


def merge_audio_bytes(bytes1, bytes2):
    """
    Merge two raw PCM audio byte streams.
    Assumes same format/sample rate/channels.
    Simply averages samples from both sources.
    """
    import numpy as np

    # Convert to numpy int16 arrays
    a1 = np.frombuffer(bytes1, dtype=np.int16)
    a2 = np.frombuffer(bytes2, dtype=np.int16)

    # Pad shorter one
    min_len = min(len(a1), len(a2))
    a1 = a1[:min_len]
    a2 = a2[:min_len]

    merged = ((a1.astype(int) + a2.astype(int)) // 2).astype(np.int16)
    return merged.tobytes()


def get_next_utterance():
    """
    Main entry. Captures audio from configured source(s),
    transcribes, and returns the transcript string.
    """

    audio_data = None

    if AUDIO_INPUT_MODE == "mic":
        mic_audio = capture_mic_audio()
        audio_data = mic_audio

    elif AUDIO_INPUT_MODE == "system":
        system_audio = capture_system_audio(RECORD_SECONDS)  # Must return raw PCM bytes
        audio_data = system_audio

    elif AUDIO_INPUT_MODE == "both":
        print("🎧 Capturing mic + system audio together...")
        mic_audio = capture_mic_audio()
        system_audio = capture_system_audio(RECORD_SECONDS)
        audio_data = merge_audio_bytes(mic_audio, system_audio)

    else:
        print(f"❌ Unknown AUDIO_INPUT_MODE: {AUDIO_INPUT_MODE}")
        return None

    # Transcribe with Google first
    print("🧠 Transcribing via Google STT...")
    try:
        audio = sr.AudioData(audio_data, SAMPLE_RATE, 2)
        transcript = recognizer.recognize_google(audio)
        print(f"📄 Google Transcript: {transcript}")
        return transcript

    except sr.UnknownValueError:
        print("⚠️ Google couldn't understand. Trying Whisper...")
        return transcribe_whisper(audio_data)

    except sr.RequestError:
        print("⚠️ Google STT failed (API error). Trying Whisper...")
        return transcribe_whisper(audio_data)
