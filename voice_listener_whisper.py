# voice_listener_whisper.py
import whisper
import sounddevice as sd
import numpy as np
import queue
import threading
from task_router import route_command

model = whisper.load_model("base")  # or "small", "medium", "large"
q = queue.Queue()

def callback(indata, frames, time, status):
    q.put(indata.copy())

def listen_loop(duration=3, samplerate=16000):
    print("🎙️ Whisper listener started. Speak naturally...")
    with sd.InputStream(samplerate=samplerate, channels=1, callback=callback):
        while True:
            audio_data = []
            for _ in range(int(duration * samplerate / 1024)):
                audio_data.append(q.get())
            audio_np = np.concatenate(audio_data, axis=0).flatten()

            # Convert to float32 and send to Whisper
            audio_float32 = audio_np.astype(np.float32)
            result = model.transcribe(audio_float32, language="en")  # use language='hi' or 'en' as needed
            text = result["text"].strip()

            if text:
                print(f"🧠 You said: {text}")
                route_command(text)  # Route to action engine
