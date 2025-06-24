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
stream_start_time = None
last_final_transcript_time = None

# === Session Management Constants ===
MAX_STREAM_DURATION = 300
SAFE_RESTART_CHECK = 180
SILENCE_THRESHOLD = 45

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

# === Optional Whisper Fallback (stub)
def whisper_transcribe_buffer(audio_bytes):
    return "[Whisper fallback transcript placeholder]"

# === Mic Audio Capture for Whisper
def capture_mic_audio(duration_seconds=5):
    print(f"🎧 Capturing {duration_seconds} sec mic audio sample...")
    p = pyaudio.PyAudio()
    stream = p.open(
        format=pyaudio.paInt16,
        channels=1,
        rate=RATE,
        input=True,
        frames_per_buffer=CHUNK
    )
    frames = []
    for _ in range(0, int(RATE / CHUNK * duration_seconds)):
        data = stream.read(CHUNK)
        frames.append(data)
    stream.stop_stream()
    stream.close()
    p.terminate()
    return b"".join(frames)

# === Monitor Thread for Restart

def stream_monitor(update_callback, command_callback):
    global stream_start_time, last_final_transcript_time, is_listening

    while is_listening:
        time.sleep(5)
        now = time.time()
        stream_age = now - stream_start_time
        silence_gap = now - last_final_transcript_time

        if stream_age > SAFE_RESTART_CHECK:
            if silence_gap > SILENCE_THRESHOLD:
                print("🔁 Restarting Mic STT stream (safe silence detected)")
                is_listening = False
                break
            elif stream_age > (MAX_STREAM_DURATION - 10):
                print("⚠️ No silence, capturing buffer before forced mic STT restart...")
                audio_data = capture_mic_audio(5)
                whisper_text = whisper_transcribe_buffer(audio_data)
                if whisper_text:
                    print(f"🧠 (Whisper Fallback): {whisper_text}")
                    update_callback([], "", f"🧠 Whisper: {whisper_text}")
                    command_callback(whisper_text)
                is_listening = False
                break

# === Main Live Stream Logic
def listen_loop(update_callback, command_callback):
    global is_listening, last_final_transcript, stream_start_time, last_final_transcript_time

    print("🎙️ [Google] Starting mic stream...")
    update_callback([], "", "🎙️ Google STT: Listening...")

    with MicrophoneStream(RATE, CHUNK) as stream:
        audio_generator = stream.generator()
        requests = (speech.StreamingRecognizeRequest(audio_content=content)
                    for content in audio_generator)

        stream_start_time = time.time()
        last_final_transcript_time = time.time()

        monitor_thread = threading.Thread(target=stream_monitor, args=(update_callback, command_callback))
        monitor_thread.start()

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
                    last_final_transcript_time = time.time()
                    print(f"✅ Final: {cleaned}")
                    update_callback([], "", f"🧠 Final: {cleaned}")
                    if cleaned and cleaned != last_final_transcript and len(cleaned.split()) >= 2:
                        last_final_transcript = cleaned
                        response = command_callback(cleaned)
                        if isinstance(response, str) and response.strip():
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
        print("⛔ Already listening (Google STT)")
        return

    is_listening = True

    def wrapped_loop():
        listen_loop(update_callback, command_callback)
        global is_listening
        is_listening = False
        print("♻️ Mic STT stream exited — restarting new session...")
        start_google_listening(update_callback, command_callback)

    stream_thread = threading.Thread(target=wrapped_loop)
    stream_thread.start()

def stop_google_listening():
    global is_listening
    print("🔁 Requesting Google STT stop...")
    is_listening = False

# === Wrappers for Interview Mode Integration ===
def start_mic_listener(ui_callback, command_callback):
    print("[mic_listener] 🎙️ Starting mic input for Interview Mode...")
    start_google_listening(ui_callback, command_callback)

def stop_mic_listener():
    print("[mic_listener] 🛑 Stopping mic input for Interview Mode...")
    stop_google_listening()
