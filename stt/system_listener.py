# stt/system_listener.py

"""
System audio capture with Google STT, restart logic, and Whisper fallback.
Improved version based on working design from voice_listener_system.py
"""

import os
from dotenv import load_dotenv
load_dotenv()  # Load from .env file at the beginning

import pyaudio
import threading
import queue
import time
from google.cloud import speech
from stt.google_backend import build_google_config, build_streaming_config
from stt.whisper_backend import whisper_transcribe_buffer

# === Check Google Credential Environment ===
if not os.getenv("GOOGLE_APPLICATION_CREDENTIALS"):
    print("⚠️ GOOGLE_APPLICATION_CREDENTIALS is not set — STT will fail unless cached credentials exist.")

# === Auto Device Detection ===
def find_device_by_name(keyword):
    p = pyaudio.PyAudio()
    for i in range(p.get_device_count()):
        info = p.get_device_info_by_index(i)
        name = info.get('name', '').lower()
        if keyword.lower() in name and info.get('maxInputChannels', 0) > 0:
            channels = int(info['maxInputChannels'])
            rate = int(info['defaultSampleRate'])
            print(f"✅ Found device: {name} | Index: {i} | Channels: {channels} | Rate: {rate}")
            p.terminate()
            return i, channels, rate
    p.terminate()
    return None, None, None

# === Try Voicemeeter first, then fallback ===
preferred_devices = [
    "Voicemeeter Out B2",
    "CABLE Output",
    "Stereo Mix",
    "Primary Sound Capture Driver"
]

DEVICE_INDEX = CHANNELS = RATE = None
for name in preferred_devices:
    DEVICE_INDEX, CHANNELS, RATE = find_device_by_name(name)
    if DEVICE_INDEX is not None:
        break

if DEVICE_INDEX is None:
    raise RuntimeError("❌ No valid system audio capture device found.")

# === Force correct mono config for Google STT ===
CHANNELS = 1
CHUNK = int(RATE / 10)
print(f"\n🎛 Using device #{DEVICE_INDEX} | Channels: {CHANNELS} | Sample rate: {RATE} Hz\n")

# After device detection
print(f"DEVICE_INDEX: {DEVICE_INDEX}, CHANNELS: {CHANNELS}, RATE: {RATE}")

# === Internal State ===
is_listening = False
stream_start_time = None
last_final_transcript_time = None
stream_thread = None

# === Constants ===
MAX_STREAM_DURATION = 300
SAFE_RESTART_CHECK = 180
SILENCE_THRESHOLD = 45

# === Audio Capture (for fallback) ===
def capture_system_audio(duration=5):
    print(f"🎧 Capturing {duration} sec system audio sample...")
    p = pyaudio.PyAudio()
    stream = p.open(
        format=pyaudio.paInt16,
        channels=CHANNELS,
        rate=RATE,
        input=True,
        input_device_index=DEVICE_INDEX,
        frames_per_buffer=CHUNK
    )
    frames = [stream.read(CHUNK) for _ in range(int(RATE / CHUNK * duration))]
    stream.stop_stream()
    stream.close()
    p.terminate()
    return b"".join(frames)

# === Main STT Worker Thread ===
def listen_loop(language, backend, punctuation, model, dispatch_callback, command_callback):
    global is_listening, stream_start_time, last_final_transcript_time
    print("🟢 system_listener.listen_loop() started")
    is_listening = True
    buffer = queue.Queue()

    try:
        client = speech.SpeechClient()
        config = build_google_config(language, punctuation, model)
        streaming_config = build_streaming_config(config)

        p = pyaudio.PyAudio()

        def audio_callback(in_data, frame_count, time_info, status):
            print(f"audio_callback called, got {len(in_data)} bytes")
            buffer.put(in_data)
            return (None, pyaudio.paContinue)

        stream = p.open(
            format=pyaudio.paInt16,
            channels=CHANNELS,
            rate=RATE,
            input=True,
            input_device_index=DEVICE_INDEX,
            stream_callback=audio_callback,
            frames_per_buffer=CHUNK
        )
        stream.start_stream()
        stream_start_time = time.time()
        last_final_transcript_time = time.time()
        print("🎧 Audio stream callback activated — buffer filling ✅")
        # After opening stream
        print(f"Stream opened: {stream.is_active()}")

        def monitor():
            global is_listening
            while is_listening:
                time.sleep(5)
                now = time.time()
                age = now - stream_start_time
                gap = now - last_final_transcript_time

                if age > SAFE_RESTART_CHECK:
                    if gap > SILENCE_THRESHOLD:
                        print("🔁 Restarting STT (silence detected)")
                        is_listening = False
                        return
                    elif age > (MAX_STREAM_DURATION - 10):
                        print("⚠️ Max stream limit near. Capturing buffer fallback")
                        audio_data = capture_system_audio(5)
                        whisper_result = whisper_transcribe_buffer(audio_data)
                        if whisper_result:
                            print(f"🧠 Whisper: {whisper_result}")
                            if dispatch_callback:
                                dispatch_callback(whisper_result, is_final=True)
                            if command_callback:
                                command_callback(whisper_result)
                        is_listening = False
                        return

        threading.Thread(target=monitor, daemon=True).start()

        print("🚀 Google STT stream started")
        requests = (
            speech.StreamingRecognizeRequest(audio_content=chunk)
            for chunk in iter(lambda: buffer.get(), None)
        )

        responses = client.streaming_recognize(streaming_config, requests)

        for response in responses:
            print("📨 Got STT response")
            if not is_listening:
                break
            if not response.results:
                continue
            result = response.results[0]
            if not result.alternatives:
                continue
            transcript = result.alternatives[0].transcript.strip()
            if result.is_final:
                last_final_transcript_time = time.time()
                print(f"🧠 Final: {transcript}")
                if dispatch_callback:
                    dispatch_callback(transcript, is_final=True)
                if command_callback:
                    command_callback(transcript)
            else:
                print(f"💬 Interim: {transcript}")
                if dispatch_callback:
                    dispatch_callback(transcript, is_final=False)

    except Exception as e:
        print(f"❌ Google STT Error: {e}")
        if dispatch_callback:
            dispatch_callback(f"[System STT Error: {e}]", is_final=True)

    finally:
        print("🔴 Ending stream and cleaning up")
        try:
            stream.stop_stream()
            stream.close()
            p.terminate()
        except:
            pass
        is_listening = False
        print("🔁 Restarting stream in background")
        threading.Thread(target=start, kwargs=dict(
            language=language,
            backend=backend,
            punctuation=punctuation,
            model=model,
            dispatch_callback=dispatch_callback,
            command_callback=command_callback
        ), daemon=True).start()

# === Public Start ===
def start(language="en-IN", backend="google", punctuation=True, model="default",
          dispatch_callback=None, command_callback=None):
    global stream_thread, is_listening
    if is_listening:
        print("⛔ System STT already running")
        return
    stream_thread = threading.Thread(target=listen_loop, args=(
        language, backend, punctuation, model, dispatch_callback, command_callback
    ))
    stream_thread.start()

# === Stop ===
def stop():
    global is_listening
    print("🛑 Stopping System STT")
    is_listening = False
