# interview_intent.py

"""
Interview Intent Classifier
----------------------------
Uses GPT to classify a transcript as:
- question
- command
- follow_up
- casual
"""

import os
from openai import OpenAI

# Initialize GPT client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

VALID_INTENTS = ["question", "command", "follow_up", "casual"]

def detect_interview_intent(transcript):
    """
    Ask GPT to classify the type of input.
    Returns string like 'question', 'follow_up', etc.
    """
    print(f"\n[interview_intent] 🧠 Intent detection started...")
    print(f"[interview_intent] 🗣️ Input transcript: \"{transcript}\"")

    prompt = f"""
You are a strict intent classifier for a technical interview AI.
Classify the user input below into one of:
- question
- command
- follow_up
- casual

Only return one word. No explanations.

Input: "{transcript}"
Intent:
""".strip()

    print("[interview_intent] 📤 Sending intent classification prompt to GPT.")
    print("──────────────── Prompt Preview ────────────────")
    print(prompt)
    print("────────────────────────────────────────────────")

    try:
        # Direct GPT call (no persona or context)
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0
        )

        intent = response.choices[0].message.content.strip().lower()
        print(f"[interview_intent] 📩 Raw GPT response: \"{intent}\"")

        if intent not in VALID_INTENTS:
            print(f"[interview_intent] ⚠️ Unknown intent '{intent}' — defaulting to 'casual'")
            return "casual"

        print(f"[interview_intent] ✅ Detected Intent: {intent}")
        return intent

    except Exception as e:
        print(f"[interview_intent] ❌ GPT error during intent detection: {e}")
        return "casual"
