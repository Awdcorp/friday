import whisper
import webrtcvad
import numpy as np
import sounddevice as sd
import threading
import queue
import time
import re

# === Config ===
model = whisper.load_model("small")
vad = webrtcvad.Vad(2)

FORMAT = 'int16'
CHANNELS = 1
RATE = 16000
FRAME_DURATION = 30  # ms
FRAME_SIZE = int(RATE * FRAME_DURATION / 1000)

MAX_PHRASE_GAP = 1.0  # seconds
MIN_WORDS = 3

# === Runtime state ===
listener_thread = None
listening = False
last_transcript = ""
stream = None

# === Helper: Start mic stream
def get_audio_stream():
    q = queue.Queue()

    def callback(indata, frames, time_info, status):
        q.put(bytes(indata))

    stream = sd.RawInputStream(
        samplerate=RATE,
        blocksize=FRAME_SIZE,
        dtype=FORMAT,
        channels=CHANNELS,
        callback=callback
    )
    return stream, q

# === Helper: Frame generator
def frame_generator(stream_queue):
    while listening:
        try:
            frame = stream_queue.get(timeout=1)
            yield frame
        except queue.Empty:
            continue

# === Helper: Check speech
def is_speech(frame_bytes):
    return vad.is_speech(frame_bytes, RATE)

# === Helper: Clean and normalize
def clean_text(text):
    text = text.strip().lower()
    return re.sub(r"[^\w\s\.\?\!]", "", text)

# === Core Loop ===
def listen_loop(update_callback, command_callback):
    global listening, last_transcript, stream

    print("🎙️ [Realtime] Starting mic stream...")
    stream, q = get_audio_stream()
    stream.start()
    update_callback([], "", "🎙️ Continuous mode: Listening...")

    phrase_frames = []
    last_voice_time = time.time()

    while listening:
        for frame in frame_generator(q):
            if not listening:
                break

            if is_speech(frame):
                phrase_frames.append(frame)
                last_voice_time = time.time()
                print("🟢 [Realtime] Detected speech frame")
            else:
                time_since_last = time.time() - last_voice_time
                if phrase_frames and time_since_last > MAX_PHRASE_GAP:
                    print("🟡 [Realtime] Speech pause detected, transcribing...")

                    audio_bytes = b"".join(phrase_frames)
                    audio_np = np.frombuffer(audio_bytes, dtype=np.int16).astype(np.float32) / 32768.0
                    try:
                        result = model.transcribe(audio_np, language='en', temperature=0.0)
                        phrase = clean_text(result['text'])
                    except Exception as e:
                        print(f"❌ [Realtime] Whisper error: {e}")
                        phrase = ""

                    print(f"📝 [Realtime] Transcript: '{phrase}'")
                    update_callback([], "", f"🎧 Heard: {phrase}")

                    if phrase and phrase != last_transcript and len(phrase.split()) >= MIN_WORDS:
                        print("📤 [Realtime] Sending to GPT:", phrase)
                        last_transcript = phrase
                        response = command_callback(phrase)
                        update_callback([], "", response)
                    else:
                        print("⚠️ [Realtime] Ignored (empty/duplicate/too short)")

                    phrase_frames = []

    print("🛑 [Realtime] Stopping mic stream")
    stream.stop()
    stream.close()
    update_callback([], "", "🛑 Continuous mode: Stopped.")

# === Public API ===

def start_continuous_mode(update_callback, command_callback):
    global listener_thread, listening
    if listening:
        return
    listening = True
    listener_thread = threading.Thread(target=listen_loop, args=(update_callback, command_callback))
    listener_thread.start()

def stop_continuous_mode():
    global listening, listener_thread
    listening = False
    if listener_thread:
        listener_thread.join()
        listener_thread = None

# === Utility: transcribe raw audio bytes using Whisper model ===

def transcribe_whisper(audio_bytes: bytes) -> str:
    """
    Accepts raw PCM 16-bit audio bytes.
    Returns transcribed text using Whisper.
    """
    try:
        # Convert to float32 numpy array
        audio_np = np.frombuffer(audio_bytes, dtype=np.int16).astype(np.float32) / 32768.0
        result = model.transcribe(audio_np, language='en', temperature=0.0)
        return result['text'].strip()
    except Exception as e:
        print(f"❌ Whisper transcription failed: {e}")
        return ""
    
# === Optional: One-time Whisper Listener for Manual Mode ===
def listen_once():
    import sounddevice as sd
    import numpy as np

    duration = 5  # seconds
    print("🎙️ Listening (once)...")
    audio_np = sd.rec(int(RATE * duration), samplerate=RATE, channels=CHANNELS, dtype='int16')
    sd.wait()

    audio_float = audio_np.astype(np.float32).flatten() / 32768.0
    try:
        result = model.transcribe(audio_float, language='en', temperature=0.0)
        text = clean_text(result['text'])
        print(f"📝 Transcribed: {text}")
        return text
    except Exception as e:
        print(f"❌ Whisper Error: {e}")
        return ""
