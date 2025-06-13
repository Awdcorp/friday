# voice_listener_google.py

import queue
import re
import threading
import time

import pyaudio
from google.cloud import speech

# === Google Speech Config ===
RATE = 16000
CHUNK = int(RATE / 10)  # 100ms

client = speech.SpeechClient()
config = speech.RecognitionConfig(
    encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
    sample_rate_hertz=RATE,
    language_code="en-US",
    enable_automatic_punctuation=True,
    model="default"
)
streaming_config = speech.StreamingRecognitionConfig(
    config=config,
    interim_results=True
)

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

# === Helper: Clean Text
def clean_text(text):
    text = text.strip().lower()
    return re.sub(r"[^\w\s\.\!\?]", "", text)

# === Main Live Stream Logic
def listen_loop(update_callback, command_callback):
    global is_listening, last_final_transcript

    print("🎙️ [Google] Starting mic stream...")
    update_callback([], "", "🎙️ Google STT: Listening...")

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
                transcript = result.alternatives[0].transcript
                cleaned = clean_text(transcript)

                if result.is_final:
                    print(f"✅ Final: {cleaned}")
                    update_callback([], "", f"🧠 Final: {cleaned}")
                    if cleaned and cleaned != last_final_transcript and len(cleaned.split()) >= 2:
                        last_final_transcript = cleaned
                        response = command_callback(cleaned)
                        update_callback([], "", response)
                else:
                    print(f"✏️ Interim: {cleaned}")
                    update_callback([], "", f"💬 {cleaned}")

        except Exception as e:
            print("❌ Google STT Error:", e)
        finally:
            update_callback([], "", "🛑 Google STT: Stopped.")

# === Public API
def start_google_listening(update_callback, command_callback):
    global is_listening, stream_thread
    if is_listening:
        return
    is_listening = True
    stream_thread = threading.Thread(target=listen_loop, args=(update_callback, command_callback))
    stream_thread.start()

def stop_google_listening():
    global is_listening
    print("🔁 Requesting Google STT stop...")
    is_listening = False  # Do not join here; let the thread exit naturally