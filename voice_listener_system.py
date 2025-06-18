import pyaudio
import threading
import queue
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
    language_code="en-US",
    enable_automatic_punctuation=True,
    model="default"
)
streaming_config = speech.StreamingRecognitionConfig(
    config=config,
    interim_results=True
)

# === Flags ===
is_listening = False
stream_thread = None

def audio_generator(buff):
    while is_listening:
        chunk = buff.get()
        if chunk is None:
            return
        yield speech.StreamingRecognizeRequest(audio_content=chunk)

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
        global is_listening
        is_listening = False

    stream_thread = threading.Thread(target=run)
    stream_thread.start()

def capture_system_audio(duration_seconds=5):
    """
    Captures system audio for a fixed duration and returns raw PCM bytes.
    Used by utterance_buffer.py for transcription fallback.
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
