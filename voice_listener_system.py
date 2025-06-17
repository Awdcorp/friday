# voice_listener_system.py

import pyaudio
import threading
import queue
from google.cloud import speech

# === Device Selection ===
DEVICE_INDEX = 65  # You can change this based on your system

# === Auto-detect sample rate ===
def get_sample_rate(device_index):
    p = pyaudio.PyAudio()
    try:
        info = p.get_device_info_by_index(device_index)
        return int(info['defaultSampleRate'])
    except Exception as e:
        print(f"❌ Failed to get sample rate for device {device_index}:", e)
        return 16000  # fallback
    finally:
        p.terminate()

RATE = get_sample_rate(DEVICE_INDEX)
CHUNK = int(RATE / 10)
print(f"🎛 Using sample rate {RATE} Hz for device {DEVICE_INDEX}")

# === Google STT Config ===
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

# === Internal flags ===
is_listening = False
stream_thread = None

# === Audio Streaming Generator ===
def audio_generator(buff):
    while is_listening:
        chunk = buff.get()
        if chunk is None:
            return
        yield speech.StreamingRecognizeRequest(audio_content=chunk)

# === Main Listening Loop ===
def listen_loop(update_callback, command_callback):
    global is_listening
    print("🎧 Starting system audio stream...")

    p = pyaudio.PyAudio()
    buffer = queue.Queue()

    def callback(in_data, frame_count, time_info, status):
        buffer.put(in_data)
        return (None, pyaudio.paContinue)

    try:
        stream = p.open(
            format=pyaudio.paInt16,
            channels=2,
            rate=RATE,
            input=True,
            frames_per_buffer=CHUNK,
            input_device_index=DEVICE_INDEX,
            stream_callback=callback
        )
    except Exception as e:
        print(f"❌ Failed to open audio stream: {e}")
        update_callback([], "", f"❌ Audio error: {e}")
        return

    stream.start_stream()

    requests = audio_generator(buffer)
    responses = client.streaming_recognize(streaming_config, requests)

    try:
        for response in responses:
            if not is_listening:
                break
            if not response.results:
                continue

            result = response.results[0]
            transcript = result.alternatives[0].transcript.strip()

            if result.is_final:
                print(f"🧠 Final: {transcript}")
                update_callback([], "", f"🧠 Final: {transcript}")
                if transcript:
                    command_callback(transcript)
            else:
                print(f"💬 Interim: {transcript}")
                update_callback([], "", f"💬 {transcript}")

    except Exception as e:
        print("❌ System STT Error:", e)
        update_callback([], "", f"❌ STT Error: {e}")
    finally:
        stream.stop_stream()
        stream.close()
        p.terminate()
        update_callback([], "", "🛑 System STT stopped")

# === Public API ===
def start_system_listener(update_callback, command_callback):
    global is_listening, stream_thread

    if is_listening:
        print("⛔ System STT already running")
        return

    is_listening = True

    def run():
        listen_loop(update_callback, command_callback)
        global is_listening
        is_listening = False

    stream_thread = threading.Thread(target=run)
    stream_thread.start()

def stop_system_listener():
    global is_listening
    print("🔁 Stopping system STT...")
    is_listening = False
