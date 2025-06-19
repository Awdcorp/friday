# conversation_mode/utterance_buffer.py

"""
Utterance Buffer – Captures spoken input from system audio using real-time Google STT.
Fallback to Whisper if needed.

✅ Current Mode: SYSTEM AUDIO ONLY
"""

import time
import threading
import queue
import pyaudio
import numpy as np
import speech_recognition as sr
from google.cloud import speech
from voice_listener_whisper import transcribe_whisper

# === Default System Audio Input Settings ===
DEVICE_INDEX = CHANNELS = RATE = None
P = pyaudio.PyAudio()

preferred_devices = [
    "Voicemeeter Out B2",
    "CABLE Output",
    "Stereo Mix",
    "Primary Sound Capture Driver"
]

for name in preferred_devices:
    for i in range(P.get_device_count()):
        info = P.get_device_info_by_index(i)
        if name.lower() in info.get('name', '').lower() and info.get('maxInputChannels', 0) > 0:
            DEVICE_INDEX = i
            CHANNELS = 1
            RATE = int(info['defaultSampleRate'])
            print(f"✅ Found system device: {info['name']} | Index: {DEVICE_INDEX} | Rate: {RATE}")
            break
    if DEVICE_INDEX is not None:
        break

if DEVICE_INDEX is None:
    raise RuntimeError("❌ No valid system audio capture device found. Please check Voicemeeter or Cable Output.")

CHUNK = int(RATE / 10)

# === Google STT Setup ===
client = speech.SpeechClient()
recognition_config = speech.RecognitionConfig(
    encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
    sample_rate_hertz=RATE,
    language_code="en-US",
    enable_automatic_punctuation=True
)
streaming_config = speech.StreamingRecognitionConfig(
    config=recognition_config,
    interim_results=False  # We only want final result here
)

# === Realtime Audio Generator ===
def audio_generator(q):
    while True:
        data = q.get()
        if data is None:
            break
        yield speech.StreamingRecognizeRequest(audio_content=data)

# === Main Entry ===
def get_next_utterance():
    """
    Captures live system audio and returns transcribed text.
    Falls back to Whisper if Google STT fails.
    """
    print("🎧 Starting system audio stream...")

    audio_queue = queue.Queue()

    def callback(in_data, frame_count, time_info, status):
        audio_queue.put(in_data)
        return (None, pyaudio.paContinue)

    try:
        stream = P.open(
            format=pyaudio.paInt16,
            channels=CHANNELS,
            rate=RATE,
            input=True,
            input_device_index=DEVICE_INDEX,
            frames_per_buffer=CHUNK,
            stream_callback=callback
        )
    except Exception as e:
        print("❌ Failed to open system stream:", e)
        return None

    stream.start_stream()
    responses = client.streaming_recognize(streaming_config, audio_generator(audio_queue))

    try:
        for response in responses:
            if not response.results:
                continue
            result = response.results[0]
            if result.is_final:
                transcript = result.alternatives[0].transcript.strip()
                print(f"👂 Heard (Google): {transcript}")
                stream.stop_stream()
                stream.close()
                return transcript
    except Exception as e:
        print(f"⚠️ Google STT error: {e}")
        # fallback to Whisper using last few seconds
        stream.stop_stream()
        stream.close()
        return fallback_to_whisper()

    return None

def fallback_to_whisper(duration_seconds=6):
    """
    Captures a short fixed system sample and passes to Whisper for transcription.
    """
    print(f"🔁 Falling back to Whisper for {duration_seconds}s audio...")

    stream = P.open(
        format=pyaudio.paInt16,
        channels=CHANNELS,
        rate=RATE,
        input=True,
        input_device_index=DEVICE_INDEX,
        frames_per_buffer=CHUNK
    )

    frames = []
    for _ in range(0, int(RATE / CHUNK * duration_seconds)):
        data = stream.read(CHUNK)
        frames.append(data)

    stream.stop_stream()
    stream.close()
    raw_audio = b''.join(frames)

    return transcribe_whisper(raw_audio)
