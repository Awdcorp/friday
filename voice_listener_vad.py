import whisper
import webrtcvad
import collections
import numpy as np
import sounddevice as sd
import queue
from ask_gpt import ask_gpt
from overlay_ui import update_overlay

# Load Whisper model
model = whisper.load_model("base")
vad = webrtcvad.Vad(2)  # Aggressiveness level (0–3)

FORMAT = 'int16'
CHANNELS = 1
RATE = 16000
FRAME_DURATION = 30  # ms
FRAME_SIZE = int(RATE * FRAME_DURATION / 1000)
MAX_BUFFER_DURATION = 10  # seconds

last_transcript = ""  # Stores last command until confirmed

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

def frame_generator(stream_queue):
    while True:
        frame = stream_queue.get()
        if len(frame) == 0:
            break
        yield frame

def is_speech(frame_bytes):
    return vad.is_speech(frame_bytes, RATE)

def listen_loop():
    global last_transcript
    print("🎙️ VAD-based Whisper listener started. Speak naturally...")

    while True:
        stream, stream_queue = get_audio_stream()
        stream.start()

        triggered = False
        voiced_frames = []
        silence_counter = 0
        max_silence = int(1.2 * 1000 / FRAME_DURATION)  # ~1.2 seconds of silence

        for frame in frame_generator(stream_queue):
            if is_speech(frame):
                if not triggered:
                    triggered = True
                    print("🎤 Listening...")
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
            continue  # No speech detected, restart

        # Convert audio to float32 for Whisper
        audio_bytes = b"".join(voiced_frames)
        audio_np = np.frombuffer(audio_bytes, dtype=np.int16).astype(np.float32) / 32768.0

        result = model.transcribe(audio_np, language='en')
        text = result['text'].strip().lower()

        if not text:
            continue

        print(f"🧠 You said: {text}")

        # Handle confirmation
        if text in ["yes", "confirm", "go ahead", "okay", "do it"]:
            if last_transcript:
                update_overlay([], "", f"🔁 Confirmed: {last_transcript}\n🤖 Thinking...")
                reply = ask_gpt(last_transcript)
                print(f"🤖 GPT: {reply}")
                update_overlay([], "", f"You: {last_transcript}\n\nFriday: {reply}")
                last_transcript = ""  # Clear after use
            else:
                update_overlay([], "", "⚠️ Nothing to confirm.")
        else:
            last_transcript = text
            update_overlay([], "", f"🧠 You said: {text}\nSay 'confirm' to ask Friday.")
