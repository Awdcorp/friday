'''
unified_interview_gpt.py
-------------------------
Single GPT interface that performs both intent detection and answering.
Used only in Interview Mode (profile: software_engineer).
'''

import os
import json
import re
from datetime import datetime
from openai import OpenAI
from dotenv import load_dotenv
from .interview_prompt_profile import PROMPT_PROFILES
from .interview_context import get_interview_context_string, update_interview_context
from .interview_logger import log_qa

# === Load API Key ===
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

MODULE = "[unified_gpt]"

def log(msg):
    print(f"{MODULE} {msg}")

# === Config ===
MAX_FOLLOW_UPS = 3

# === Reference to state — set from outside
interview_state = {
    "mode": "IDLE",                       # Current mode: LISTENING, ANSWERING, etc.
    "last_question": None,               # Last asked question
    "last_answer": None,                 # Last given answer
    "last_time": 0,                      # Timestamp of last interaction
    "program_thread_active": False,      # Whether in the middle of a programming thread
    "program_topic": None,               # Active topic of the thread
    "followup_count": 0,                 # Number of follow-ups in current thread
    "program_anchor_question": None,     # Initial anchor question of the thread
    "program_anchor_answer": None,       # Anchor answer
    "listener_source": "system"          # mic or system audio
}

def detect_and_answer(transcript, profile="software_engineer"):
    """
    Unified GPT call to classify + answer.
    Returns: dict with all required metadata:
      { answer, corrected_text, intent, is_programming, is_follow_up, topic, popup_id, replace_popup }
    """
    global interview_state

    if profile != "software_engineer":
        log("🧾 Skipping intent logic for non-programming profile.")
        answer = _send_to_gpt(transcript, profile)
        return {
            "answer": answer,
            "corrected_text": transcript,
            "intent": "generic",
            "is_programming": False,
            "is_follow_up": False,
            "topic": None,
            "popup_id": 1,
            "replace_popup": True
        }

    base_question = interview_state.get("last_question")
    anchor_q = interview_state.get("program_anchor_question")
    anchor_a = interview_state.get("program_anchor_answer")
    context_str = get_interview_context_string()

    system_prompt = PROMPT_PROFILES.get(profile)
    user_prompt = f"""
You are an intelligent assistant that must first classify the input, then answer it.

Transcript: "{transcript}"
Base Question: "{base_question or 'None'}"
Anchor:
Q: {anchor_q or 'None'}
A: {anchor_a or 'None'}

Context:
{context_str}

Return JSON first, then answer below:
{{
  "intent": "program_start | program_follow_up | new_question | follow_up | similar_to_previous | irrelevant_or_incomplete",
  "is_programming": true/false,
  "is_follow_up": true/false,
  "topic": "<short topic>",
  "corrected_input": "<final form of question>"
}}

Then give the assistant answer.
"""

    try:
        log("🚀 Sending combined prompt to GPT...")
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            temperature=0.5,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt.strip()}
            ]
        )

        full_output = response.choices[0].message.content.strip()

        # === Safe JSON extraction ===
        json_match = re.search(r'\{[\s\S]*?\}', full_output)
        if not json_match:
            raise ValueError("No valid JSON found in GPT response.")

        json_part = json_match.group(0)
        answer_part = full_output[json_match.end():].strip()

        parsed = json.loads(json_part)
        intent = parsed.get("intent", "unknown")
        is_programming = parsed.get("is_programming", False)
        is_follow_up = parsed.get("is_follow_up", False)
        topic = parsed.get("topic")
        corrected_text = parsed.get("corrected_input", transcript)

        log(f"🔍 Intent: {intent} | Prog: {is_programming} | Follow: {is_follow_up} | Topic: {topic}")

        # === Popup logic ===
        replace_popup = True
        popup_id = 1

        if intent == "program_start":
            interview_state.update({
                "program_thread_active": True,
                "program_topic": topic,
                "followup_count": 0,
                "program_anchor_question": corrected_text,
                "program_anchor_answer": answer_part
            })
            popup_id = 1

        elif is_follow_up and interview_state.get("program_thread_active"):
            interview_state["followup_count"] += 1
            popup_id = 2

            if interview_state["followup_count"] > MAX_FOLLOW_UPS:
                interview_state.update({
                    "program_thread_active": False,
                    "program_topic": None,
                    "followup_count": 0,
                    "program_anchor_question": None,
                    "program_anchor_answer": None
                })

        # === Log and update context ===
        log_qa(corrected_text, answer_part)
        update_interview_context(corrected_text, answer_part)

        interview_state.update({
            "mode": "ANSWERING",
            "last_question": corrected_text,
            "last_answer": answer_part,
            "last_time": datetime.now().timestamp()
        })

        return {
            "answer": answer_part,
            "corrected_text": corrected_text,
            "intent": intent,
            "is_programming": is_programming,
            "is_follow_up": is_follow_up,
            "topic": topic,
            "popup_id": popup_id,
            "replace_popup": replace_popup
        }

    except Exception as e:
        log(f"❌ GPT Error: {e}")
        return {
            "answer": "⚠️ Error occurred while processing.",
            "corrected_text": transcript,
            "intent": "error",
            "is_programming": False,
            "is_follow_up": False,
            "topic": None,
            "popup_id": 1,
            "replace_popup": True
        }

def _send_to_gpt(transcript, profile):
    """Simple fallback for non-programming profiles"""
    context_str = get_interview_context_string()
    persona_prompt = PROMPT_PROFILES.get(profile)
    full_prompt = f"""{persona_prompt}

Context:
{context_str}

Question:
{transcript}

Answer as Friday.
"""
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": full_prompt}],
        temperature=0.7
    )
    return response.choices[0].message.content.strip()