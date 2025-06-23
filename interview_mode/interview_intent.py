import os
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def detect_interview_intent(transcript):
    print(f"\n[interview_intent] 🧠 Enhanced Intent detection started...")
    print(f"[interview_intent] 🗣️ Input transcript: \"{transcript}\"")

    prompt = f"""
You are an intelligent intent classifier for a technical interview assistant.

Classify the intent of the user's message into one of the following:
- program_start: A request to write a program (e.g. "Write a program to...", "Implement...")
- program_follow_up: A follow-up related to a previously written program (e.g. "Can you optimize it?", "What if input is null?")
- question: A general technical question (e.g. "What is malloc used for?", "What is a pointer?")
- clarify: A vague or unclear message (e.g. "Can you explain?", "What about that?")
- thread_end: A command or signal to switch context (e.g. "Let's move on", "Next question")
- casual: Greetings, confirmations, or irrelevant phrases (e.g. "Okay", "Alright")

Also answer these:
- Is the message related to programming? (true/false)
- Provide a corrected version if transcription is unclear (e.g., fix "linked test" to "linked list")
- If known, extract a topic (e.g. "linked list", "malloc")

Respond in JSON:
{{
  "intent": "...",
  "corrected_text": "...",
  "is_programming": true/false,
  "topic": "..."
}}

Input: "{transcript}"
""".strip()

    print("[interview_intent] 📤 Sending enhanced prompt to GPT...")

    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3
        )

        content = response.choices[0].message.content.strip()
        print("[interview_intent] 📩 Raw response:", content)

        import json
        result = json.loads(content)

        return result

    except Exception as e:
        print(f"[interview_intent] ❌ Error: {e}")
        return {
            "intent": "question",
            "corrected_text": transcript,
            "is_programming": False,
            "topic": ""
        }
