import pyaudio
import threading
import queue
import time
from google.cloud import speech

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
    raise RuntimeError("❌ No valid system audio capture device found. Please check Voicemeeter or VB Cable.")

# === Force correct channel config ===
CHANNELS = 1  # ✅ Always use mono for Google STT

CHUNK = int(RATE / 10)
print(f"\n🎛 Using device #{DEVICE_INDEX} | Channels: {CHANNELS} | Sample rate: {RATE} Hz\n")

# === Google STT Setup ===
client = speech.SpeechClient()
config = speech.RecognitionConfig(
    encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
    sample_rate_hertz=RATE,
    language_code="en-IN",  # use 'en-IN' for Hinglish support
    enable_automatic_punctuation=True,
    model="default"
)
streaming_config = speech.StreamingRecognitionConfig(
    config=config,
    interim_results=True
)

# === Session Management Constants ===
MAX_STREAM_DURATION = 300      # 5 min
SAFE_RESTART_CHECK = 180       # check at 3 min
SILENCE_THRESHOLD = 45         # require 45s of silence

# === Flags and State
is_listening = False
stream_thread = None
stream_start_time = None
last_final_transcript_time = None


def audio_generator(buff):
    while is_listening:
        chunk = buff.get()
        if chunk is None:
            return
        yield speech.StreamingRecognizeRequest(audio_content=chunk)


def whisper_transcribe_buffer(audio_bytes):
    """
    Replace this with actual Whisper transcription logic.
    This placeholder just returns a dummy string.
    """
    return "[Whisper transcription placeholder]"


def stream_monitor(update_callback, command_callback):
    """
    Background thread to monitor stream age and decide safe restart.
    """
    global stream_start_time, last_final_transcript_time, is_listening

    while is_listening:
        time.sleep(5)
        now = time.time()
        stream_age = now - stream_start_time
        silence_gap = now - last_final_transcript_time

        if stream_age > SAFE_RESTART_CHECK:
            if silence_gap > SILENCE_THRESHOLD:
                print("🔁 Restarting STT stream (safe silence detected)")
                is_listening = False  # This triggers restart
                break
            elif stream_age > (MAX_STREAM_DURATION - 10):
                print("⚠️ No silence, capturing buffer before forced STT restart...")
                audio_data = capture_system_audio(5)
                whisper_text = whisper_transcribe_buffer(audio_data)
                if whisper_text:
                    print(f"🧠 (Whisper Fallback): {whisper_text}")
                    update_callback([], "", f"🧠 Whisper: {whisper_text}")
                    command_callback(whisper_text)
                is_listening = False
                break


def listen_loop(update_callback, command_callback):
    global is_listening, stream_start_time, last_final_transcript_time

    print("🎧 Starting system audio stream...")
    p = pyaudio.PyAudio()
    buffer = queue.Queue()

    def callback(in_data, frame_count, time_info, status):
        buffer.put(in_data)
        return (None, pyaudio.paContinue)

    try:
        stream = p.open(
            format=pyaudio.paInt16,
            channels=CHANNELS,
            rate=RATE,
            input=True,
            input_device_index=DEVICE_INDEX,
            stream_callback=callback,
            frames_per_buffer=CHUNK
        )
    except Exception as e:
        print(f"❌ Failed to open audio stream: {e}")
        update_callback([], "", f"❌ Audio error: {e}")
        return

    stream.start_stream()

    # Start session timestamp tracking
    stream_start_time = time.time()
    last_final_transcript_time = time.time()

    # Start monitor in parallel
    monitor_thread = threading.Thread(target=stream_monitor, args=(update_callback, command_callback))
    monitor_thread.start()

    responses = client.streaming_recognize(streaming_config, audio_generator(buffer))

    try:
        for response in responses:
            if not is_listening:
                break
            if not response.results:
                continue

            result = response.results[0]
            transcript = result.alternatives[0].transcript.strip()

            if result.is_final:
                last_final_transcript_time = time.time()
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


def start_system_listener(update_callback, command_callback):
    global is_listening, stream_thread

    if is_listening:
        print("⛔ System STT already running")
        return

    is_listening = True

    def run():
        listen_loop(update_callback, command_callback)
        print("♻️ STT stream exited — restarting new session if needed...")
        start_system_listener(update_callback, command_callback)  # ✅ Always restart

    stream_thread = threading.Thread(target=run)
    stream_thread.start()

def capture_system_audio(duration_seconds=5):
    """
    Captures system audio for a fixed duration and returns raw PCM bytes.
    Used by whisper fallback before forced STT restarts.
    """
    print(f"🎧 Capturing {duration_seconds} sec system audio sample...")

    p = pyaudio.PyAudio()
    stream = p.open(
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
    p.terminate()

    return b"".join(frames)


def stop_system_listener():
    global is_listening
    print("🔁 Stopping system STT...")
    is_listening = False
