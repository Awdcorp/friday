"""
Interview Mode Handler (with Raw Transcript Audit + Audit Optimization)
---------------------------------------------------
Includes persistent raw buffer and GPT-based audit, now optimized to skip redundant audits when the transcript hasn't changed.
Also ensures audit recovery popups are non-redundant and self-replacing.
"""

import time
import threading
import json
import os
import hashlib
from datetime import datetime
from openai import OpenAI
from .ask_gpt_interview import ask_gpt_interview
from .interview_logger import log_qa
from .interview_context import update_interview_context
from .question_detection import detect_question
from voice_listener_system import start_system_listener, stop_system_listener
from voice_listener_google import start_mic_listener, stop_mic_listener

# === Internal state ===
interview_state = {
    "mode": "IDLE",
    "last_question": None,
    "last_answer": None,
    "last_time": 0,
    "program_thread_active": False,
    "program_topic": None,
    "followup_count": 0,
    "program_anchor_question": None,
    "program_anchor_answer": None,
    "listener_source": "system",
    "raw_transcript_full": [],
    "detected_questions_normal": [],
    "missed_question_checks_done": 0,
    "last_audit_hash": None
}

# === Start Interview Mode ===
def start_interview_mode(update_text_callback, response_callback, profile="software_engineer", source="system"):
    def on_transcript(transcript):
        print(f"\n[interview_handler] 🎵 Transcript Received: {transcript}")
        interview_state["raw_transcript_full"].append(transcript.strip())

        def run(transcript=transcript):
            print("\n[interview_handler] 🧠 Starting GPT processing thread...")

            if profile == "software_engineer":
                result = detect_question(transcript)
                if result.get("intent") in {"waiting_for_more_input", "irrelevant_or_incomplete"}:
                    print(f"[interview_handler] ⏳ Buffering... Intent: {result.get('intent')}")
                    return

                intent = result["intent"]
                is_programming = result.get("is_programming", False)
                topic = result.get("topic", "")
                corrected_text = result.get("current_input", transcript)
                is_follow_up = result.get("is_follow_up", False)

                print(f"[interview_handler] 🧠 Intent: {intent} | Programming: {is_programming} | Topic: {topic} | Follow-up: {is_follow_up}")

                replace_popup = True
                popup_id = 1

                if intent == "program_start":
                    interview_state.update({
                        "program_thread_active": True,
                        "program_topic": topic,
                        "followup_count": 0
                    })
                elif is_follow_up and interview_state["program_thread_active"]:
                    interview_state["followup_count"] += 1
                    popup_id = 2
                    if interview_state["followup_count"] > 3:
                        interview_state.update({
                            "program_thread_active": False,
                            "program_topic": None,
                            "followup_count": 0,
                            "program_anchor_question": None,
                            "program_anchor_answer": None
                        })

                interview_state["detected_questions_normal"].append(corrected_text)

            else:
                print("[interview_handler] 🗒️ Skipping intent logic for non-programming profile.")
                corrected_text = transcript
                popup_id = 1
                replace_popup = True

            print("[interview_handler] 🚀 Sending prompt to GPT...")
            answer = ask_gpt_interview(corrected_text, profile=profile)

            response_callback(f"🤖 {answer}", replace_popup=replace_popup, popup_id=popup_id)
            log_qa(corrected_text, answer)
            update_interview_context(corrected_text, answer)

            interview_state.update({
                "mode": "ANSWERING",
                "last_question": corrected_text,
                "last_answer": answer,
                "last_time": time.time()
            })

            if profile == "software_engineer" and intent == "program_start":
                interview_state["program_anchor_question"] = corrected_text
                interview_state["program_anchor_answer"] = answer

            print("[interview_handler] ✅ Interview Q&A complete.")

        threading.Thread(target=run).start()

    print(f"[interview_handler] 🚀 Interview Mode Activated | Source: {source}")
    interview_state["listener_source"] = source

    if source == "mic":
        start_mic_listener(update_text_callback, on_transcript)
    else:
        start_system_listener(update_text_callback, on_transcript)

    start_audit_checker(response_callback)

# === Stop Interview Mode ===
def stop_interview_mode():
    print("[interview_handler] 🚩 Interview Mode Deactivated")
    if interview_state.get("listener_source") == "mic":
        stop_mic_listener()
    else:
        stop_system_listener()

# === Audit Checker ===
def start_audit_checker(response_callback):
    def get_hash(text):
        return hashlib.md5(text.encode()).hexdigest()

    def monitor():
        while True:
            time.sleep(7)
            full_text = " ".join(interview_state["raw_transcript_full"]).strip()
            detected = interview_state["detected_questions_normal"]
            if not full_text or not detected:
                continue

            new_hash = get_hash(full_text)
            if new_hash == interview_state.get("last_audit_hash"):
                continue  # No change, skip audit

            interview_state["last_audit_hash"] = new_hash
            check_for_missed_questions(full_text, detected, response_callback)

    threading.Thread(target=monitor, daemon=True).start()

# === GPT Comparison Logic ===
def check_for_missed_questions(full_text, detected_questions, response_callback):
    print("[audit_checker] 🔍 Auditing transcript for missed questions...")
    prompt = f"""
You are an intelligent assistant reviewing a transcript from a technical interview.

Here is the full raw transcript of what the interviewer said:

<<<
{full_text}
>>>

The system has already detected and answered the following questions:

{json.dumps(detected_questions, indent=2)}

Your tasks:
1. Carefully review the raw transcript.
2. Identify any programming or technical questions that were missed, misclassified, or phrased too vaguely and therefore not detected earlier.
3. Focus on questions that are meaningful, relevant to technical interviews, or that request code, concepts, or clarifications.
4. Ignore filler phrases, greetings, or non-question statements.
5. you can also check if the raw transciption and overall detected questions are similar, if so, skip the audit.

Return a clean JSON list of only the missed or misinterpreted questions.
If none are missed, return an empty list: []
"""
    try:
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0
        )
        content = response.choices[0].message.content.strip()
        print("[audit_checker] 📊 GPT Response:", content)
        missed = json.loads(content)
        if not missed:
            response_callback("🕵️ Audit checked — no missed questions detected.", popup_id=3)
            interview_state["raw_transcript_full"].clear()  # ✅ Clear buffer after audit
            return

        for question in missed:
            if question not in interview_state["detected_questions_normal"]:
                print(f"[audit_checker] 🔹 Missed: {question}")
                answer = ask_gpt_interview(question)
                log_qa(question, answer)
                update_interview_context(question, answer)
                now = datetime.now().strftime("%H:%M:%S")
                response_callback(f"🤖 [Audit {now}]\n{answer}", popup_id=3)
                interview_state["raw_transcript_full"].clear()  # ✅ Clear buffer after audit recovery

    except Exception as e:
        print("[audit_checker] ❌ GPT Error:", e)