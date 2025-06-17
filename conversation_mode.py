# friday/conversation_mode.py

import os
from dotenv import load_dotenv
load_dotenv()  # ✅ Load .env for GOOGLE_APPLICATION_CREDENTIALS if not already loaded

import threading
import queue
import time
import sounddevice as sd
from google.cloud import speech

# === Audio Configuration ===
RATE = 16000
CHUNK = int(RATE / 10)

# === Google STT Client ===
client = speech.SpeechClient()
config = speech.RecognitionConfig(
    encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
    sample_rate_hertz=RATE,
    language_code="en-US",
    enable_automatic_punctuation=True
)
streaming_config = speech.StreamingRecognitionConfig(
    config=config,
    interim_results=False
)

# === Shared Conversation Buffer ===
conversation_buffer = []

def add_to_buffer(text, speaker):
    print(f"👤 {speaker}: {text}")  # Live preview in console
    conversation_buffer.append({
        "text": text,
        "speaker": speaker,
        "timestamp": time.time()
    })

def get_recent_transcript():
    return sorted(conversation_buffer, key=lambda x: x["timestamp"])[-20:]

# === STT Streaming Logic ===
def start_google_transcription(device_index, speaker_label):
    audio_queue = queue.Queue()

    def callback(indata, frames, time_info, status):
        audio_queue.put(indata.copy())

    with sd.InputStream(samplerate=RATE, blocksize=CHUNK, device=device_index, channels=1, dtype='int16', callback=callback):
        while True:
            audio_stream = (speech.StreamingRecognizeRequest(audio_content=audio_queue.get().tobytes()) for _ in range(30))

            try:
                responses = client.streaming_recognize(streaming_config, audio_stream)
                for response in responses:
                    for result in response.results:
                        if result.is_final:
                            text = result.alternatives[0].transcript.strip()
                            add_to_buffer(text, speaker_label)
            except Exception as e:
                print(f"[{speaker_label} Stream Error]:", e)
                time.sleep(1)  # Wait briefly before restarting loop

# === Conversation Mode Starter ===
def start_conversation_mode(mic_index=9, system_index=21):
    print("🎙️ Starting Conversation Mode...")
    threading.Thread(target=start_google_transcription, args=(mic_index, "You"), daemon=True).start()
    threading.Thread(target=start_google_transcription, args=(system_index, "Other"), daemon=True).start()
