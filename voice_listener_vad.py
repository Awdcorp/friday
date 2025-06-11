import whisper
import webrtcvad
import numpy as np
import sounddevice as sd
import queue
import re
import time
from ask_gpt import ask_gpt

# ✅ Callback to update overlay (set by main_brain)
update_overlay_callback = None

# Load Whisper model
model = whisper.load_model("base")
vad = webrtcvad.Vad(2)

FORMAT = 'int16'
CHANNELS = 1
RATE = 16000
FRAME_DURATION = 30
FRAME_SIZE = int(RATE * FRAME_DURATION / 1000)
MAX_RECORD_TIME = 5
last_transcript = ""

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

def transcribe_audio(frames):
    audio_bytes = b"".join(frames)
    audio_np = np.frombuffer(audio_bytes, dtype=np.int16).astype(np.float32) / 32768.0
    result = model.transcribe(audio_np, language='en')
    return result['text'].strip().lower()

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
            if update_overlay_callback:
                update_overlay_callback([], "", "🎤 Speak your command...")
            spoken_text = listen_once()
            if spoken_text:
                print(f"🧠 Heard: {spoken_text}")
                last_transcript = spoken_text
                if update_overlay_callback:
                    update_overlay_callback([], "", f"🧠 You said: {spoken_text}\nSay 'confirm' to process.")
            else:
                print("⚠️ No speech detected.")
                if update_overlay_callback:
                    update_overlay_callback([], "", "⚠️ No speech detected.")
        elif text in ["confirm", "yes", "okay", "haan", "kar do", "go ahead"]:
            if last_transcript:
                if update_overlay_callback:
                    update_overlay_callback([], "", f"🔁 Confirmed: {last_transcript}\n🤖 Thinking...")
                reply = ask_gpt(last_transcript)
                print(f"🤖 GPT: {reply}")
                if update_overlay_callback:
                    update_overlay_callback([], "", f"You: {last_transcript}\n\nFriday: {reply}")
                last_transcript = ""
            else:
                if update_overlay_callback:
                    update_overlay_callback([], "", "⚠️ Nothing to confirm.")
