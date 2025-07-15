import os
import json
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def detect_interview_intent(transcript, anchor_question=None, anchor_answer=None):
    print(f"\n[interview_intent] 🧠 Enhanced Intent detection started...")
    #print(f"[interview_intent] 🗣️ Input transcript: \"{transcript}\"")

    # Optional anchor context
    anchor_info = ""
    if anchor_question and anchor_answer:
        anchor_info = f"""
Here is the original program-related question and answer for reference:

Q: "{anchor_question}"
A: "{anchor_answer}"

Use this to help determine if the current message is a follow-up.
"""

    # === GPT Prompt ===
    prompt = f"""
You are an intelligent intent classifier for a technical interview assistant.

{anchor_info}

Classify the intent of the user's message into one of the following:
- program_start: A request to write a program (e.g. "Write a program to...", "Implement...")
- program_follow_up: A follow-up related to a previously written program (e.g. "Can you optimize it?", "What if input is null?")
- question: A general technical question (e.g. "What is malloc used for?", "What is a pointer?")
- clarify: A vague or unclear message (e.g. "Can you explain?", "What about that?")
- thread_end: A command or signal to switch context (e.g. "Let's move on", "Next question")
- casual: Greetings, confirmations, or irrelevant phrases (e.g. "Okay", "Alright")

Also return:
- A corrected version of the message (fix typos or transcription issues)
- Whether it is related to programming (true/false)
- The main topic (e.g. "linked list", "factorial", "malloc")
- Whether it is a follow-up to the program anchor above (true/false)

Respond in this JSON format:
{{
  "intent": "...",
  "corrected_text": "...",
  "is_programming": true/false,
  "topic": "...",
  "follow_up": true/false
}}

Current message: "{transcript}"
""".strip()

    print("[interview_intent] 📤 Sending enhanced prompt to GPT...")

    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3
        )

        content = response.choices[0].message.content.strip()
        #print("[interview_intent] 📩 Raw response:", content)

        result = json.loads(content)
        return result

    except Exception as e:
        #print(f"[interview_intent] ❌ Error: {e}")
        return {
            "intent": "question",
            "corrected_text": transcript,
            "is_programming": False,
            "topic": "",
            "follow_up": False
        }
