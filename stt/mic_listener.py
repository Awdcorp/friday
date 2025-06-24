"""
Google STT mic input stream with interim/final callbacks.
Refactored from voice_listener_google.py
"""

import queue
import threading
import time
import re
import pyaudio
from google.cloud import speech
from stt.google_backend import build_google_config, build_streaming_config

# === Audio Params ===
RATE = 16000
CHUNK = int(RATE / 10)  # 100ms

# === Internal State ===
microphone_stream = None
stream_thread = None
is_listening = False
last_final_transcript = ""

# === Audio Stream Generator ===
class MicrophoneStream:
    def __init__(self, rate, chunk):
        self._rate = rate
        self._chunk = chunk
        self._buff = queue.Queue()
        self.closed = True

    def __enter__(self):
        self._audio_interface = pyaudio.PyAudio()
        self._audio_stream = self._audio_interface.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=self._rate,
            input=True,
            frames_per_buffer=self._chunk,
            stream_callback=self._fill_buffer
        )
        self.closed = False
        return self

    def __exit__(self, type, value, traceback):
        self._audio_stream.stop_stream()
        self._audio_stream.close()
        self.closed = True
        self._buff.put(None)
        self._audio_interface.terminate()

    def _fill_buffer(self, in_data, frame_count, time_info, status_flags):
        self._buff.put(in_data)
        return None, pyaudio.paContinue

    def generator(self):
        while not self.closed:
            chunk = self._buff.get()
            if chunk is None:
                return
            yield chunk

# === Helper: Clean Text ===
def clean_text(text):
    text = text.strip().lower()
    return re.sub(r"[^\w\s\.\!\?]", "", text)

# === Main Entry Point ===
def start(language="en-US", backend="google", punctuation=True, model="default",
          dispatch_callback=None, command_callback=None):
    global is_listening, last_final_transcript

    last_final_transcript = ""
    is_listening = True

    client = speech.SpeechClient()
    config = build_google_config(language, punctuation, model)
    streaming_config = build_streaming_config(config)

    def listen_loop():
        print("🎙️ [Google Mic] Starting mic stream...")

        with MicrophoneStream(RATE, CHUNK) as stream:
            audio_generator = stream.generator()
            requests = (speech.StreamingRecognizeRequest(audio_content=content)
                        for content in audio_generator)
            responses = client.streaming_recognize(streaming_config, requests)

            try:
                for response in responses:
                    if not is_listening:
                        break
                    if not response.results:
                        continue

                    result = response.results[0]
                    if not result.alternatives:
                        continue

                    transcript = result.alternatives[0].transcript
                    cleaned = clean_text(transcript)

                    if result.is_final:
                        if cleaned and cleaned != last_final_transcript and len(cleaned.split()) >= 2:
                            last_final_transcript = cleaned
                            print(f"🧠 Final: {cleaned}")
                            if command_callback:
                                command_callback(cleaned)
                        if dispatch_callback:
                            dispatch_callback(cleaned, is_final=True)
                    else:
                        print(f"💬 Interim: {cleaned}")
                        if dispatch_callback:
                            dispatch_callback(cleaned, is_final=False)

            except Exception as e:
                print("❌ Google Mic STT Error:", e)

    global stream_thread
    stream_thread = threading.Thread(target=listen_loop)
    stream_thread.daemon = True
    stream_thread.start()

# === Stop ===
def stop():
    global is_listening
    print("🛑 Stopping Google Mic STT")
    is_listening = False
