# conversation_mode/utterance_buffer.py

"""
Utterance Streamer – Continuous system audio streaming with Google STT.
Sends final + interim results via callback functions.
"""

import queue
import threading
import pyaudio
from google.cloud import speech
from voice_listener_whisper import transcribe_whisper

# === Audio Device Setup ===
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
    raise RuntimeError("❌ No valid system audio capture device found.")

CHUNK = int(RATE / 10)

# === Google STT Client ===
client = speech.SpeechClient()
recognition_config = speech.RecognitionConfig(
    encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
    sample_rate_hertz=RATE,
    language_code="en-US",
    enable_automatic_punctuation=True
)
streaming_config = speech.StreamingRecognitionConfig(
    config=recognition_config,
    interim_results=True
)

# === Global Control ===
_stream_running = False
_audio_thread = None
_listener_thread = None

def start_streaming_listener(on_final_callback, on_interim_callback=None):
    """
    Starts continuous streaming from system audio.
    Calls `on_final_callback(transcript)` for final text.
    Calls `on_interim_callback(text)` (optional) for live updates.
    """

    global _stream_running, _audio_thread, _listener_thread

    if _stream_running:
        print("⚠️ Stream already running.")
        return

    print("🎧 Starting continuous system STT stream...")
    _stream_running = True
    audio_queue = queue.Queue()

    # Audio callback
    def callback(in_data, frame_count, time_info, status):
        if _stream_running:
            audio_queue.put(in_data)
        return (None, pyaudio.paContinue)

    # Open audio stream
    stream = P.open(
        format=pyaudio.paInt16,
        channels=CHANNELS,
        rate=RATE,
        input=True,
        input_device_index=DEVICE_INDEX,
        frames_per_buffer=CHUNK,
        stream_callback=callback
    )
    stream.start_stream()

    # Audio generator
    def generator():
        while _stream_running:
            data = audio_queue.get()
            if data is None:
                break
            yield speech.StreamingRecognizeRequest(audio_content=data)

    # Listener thread
    def listen():
        global _stream_running
        try:
            responses = client.streaming_recognize(streaming_config, generator())
            for response in responses:
                if not _stream_running:
                    break
                if not response.results:
                    continue

                result = response.results[0]
                transcript = result.alternatives[0].transcript.strip()

                if result.is_final:
                    print(f"👂 Final: {transcript}")
                    if on_final_callback:
                        threading.Thread(target=on_final_callback, args=(transcript,)).start()
                else:
                    print(f"💬 Interim: {transcript}")
                    if on_interim_callback:
                        on_interim_callback(transcript)

        except Exception as e:
            print(f"❌ STT error: {e}")
            print("🔁 Falling back to Whisper...")
            fallback_transcript = fallback_to_whisper()
            if fallback_transcript and on_final_callback:
                on_final_callback(fallback_transcript)

        finally:
            print("🔁 Stopping system STT...")
            try:
                stream.stop_stream()
                stream.close()
            except:
                pass
            _stream_running = False

    _listener_thread = threading.Thread(target=listen, daemon=True)
    _listener_thread.start()

def stop_streaming_listener():
    """
    Gracefully stops the continuous audio stream.
    """
    global _stream_running
    _stream_running = False
    print("🛑 Requested to stop streaming STT.")

def fallback_to_whisper(duration_seconds=6):
    """
    Captures a short fixed system sample and passes to Whisper for transcription.
    """
    print(f"🔁 Whisper fallback for {duration_seconds}s...")

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
