from gtts import gTTS
from pydub import AudioSegment
import os

# 1. List each prompt on its own line:
questions = [
    "Can you explain the difference between call by value and call by reference in C?",
    "What is a pointer in C, and how is it used?",
    "Can you tell me",            
    "Write a program to find the factorial of a number.",
    "Can you optimize it using recursion?",
    "What if the number is zero?",
    "What if input is negative?",
    "What's the difference between stack and queue?",
    "What are the risks of using malloc without checking the return value?",
]

# 2. Where to put temp files
os.makedirs("temp_tts", exist_ok=True)

segments = []
# 1s of silence between lines
pause = AudioSegment.silent(duration=5000)

for idx, line in enumerate(questions):
    tts = gTTS(text=line, lang='en', slow=False)
    tmp = f"temp_tts/part_{idx}.mp3"
    tts.save(tmp)
    clip = AudioSegment.from_file(tmp, format="mp3")
    segments.append(clip)
    segments.append(pause)

# 3. Concatenate everything
final = sum(segments)

# 4. Export
out = "c_interview_questions_with_pauses.mp3"
final.export(out, format="mp3")
print(f"✅ Saved: {out}")
