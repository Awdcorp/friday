import whisper
import webrtcvad
import numpy as np
import sounddevice as sd
import queue
import re
import time
from ask_gpt import ask_gpt
from overlay_ui import update_overlay

# Load Whisper model
model = whisper.load_model("small")
vad = webrtcvad.Vad(2)

FORMAT = 'int16'
CHANNELS = 1
RATE = 16000
FRAME_DURATION = 30  # ms
FRAME_SIZE = int(RATE * FRAME_DURATION / 1000)

last_transcript = ""
MAX_RECORD_TIME = 5  # seconds

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

def frame_generator(stream_queue, timeout=MAX_RECORD_TIME):
    start = time.time()
    while time.time() - start < timeout:
        try:
            frame = stream_queue.get(timeout=1)
            yield frame
        except queue.Empty:
            break

def is_speech(frame_bytes):
    return vad.is_speech(frame_bytes, RATE)

def clean_text(text):
    text = text.strip().lower()
    return re.sub(r'[^\w\s]', '', text)

def transcribe_audio(frames):
    audio_bytes = b"".join(frames)
    audio_np = np.frombuffer(audio_bytes, dtype=np.int16).astype(np.float32) / 32768.0
    result = model.transcribe(audio_np, language='en', temperature=0.0)
    return clean_text(result['text'])

def listen_once(timeout=MAX_RECORD_TIME):
    stream, stream_queue = get_audio_stream()
    stream.start()

    voiced_frames = []
    triggered = False
    silence_counter = 0
    max_silence = int(1.2 * 1000 / FRAME_DURATION)

    for frame in frame_generator(stream_queue, timeout):
        if is_speech(frame):
            if not triggered:
                print("🎤 Listening...")
                triggered = True
            voiced_frames.append(frame)
            silence_counter = 0
        else:
            if triggered:
                silence_counter += 1
                if silence_counter > max_silence:
                    print("🛑 End of speech")
                    break

    stream.stop()
    stream.close()

    if not voiced_frames:
        return ""

    return transcribe_audio(voiced_frames)

def listen_loop():
    global last_transcript
    print("🕓 Waiting for 'friday listen'...")

    while True:
        text = listen_once()
        if not text:
            continue
        print(f"🧠 You said: {text}")

        if "friday listen" in text:
            update_overlay([], "", "🎤 Speak your command...")
            spoken_text = listen_once(timeout=MAX_RECORD_TIME)
            if spoken_text:
                print(f"🧠 Heard: {spoken_text}")
                last_transcript = spoken_text
                update_overlay([], "", f"🧠 You said: {spoken_text}\nSay 'confirm' to process.")
            else:
                print("⚠️ No command captured.")
                update_overlay([], "", "⚠️ No speech detected.")
        elif text in ["confirm", "haan", "yes", "okay", "kar do", "theek hai"]:
            if last_transcript:
                update_overlay([], "", f"🔁 Confirmed: {last_transcript}\n🤖 Thinking...")
                reply = ask_gpt(last_transcript)
                print(f"🤖 GPT: {reply}")
                update_overlay([], "", f"You: {last_transcript}\n\nFriday: {reply}")
                last_transcript = ""
            else:
                update_overlay([], "", "⚠️ Nothing to confirm.")
