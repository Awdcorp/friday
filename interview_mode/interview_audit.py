import os
import json
import hashlib
import re
from openai import OpenAI
from datetime import datetime
from .ask_gpt_interview import ask_gpt_interview
from .interview_logger import log_qa
from .interview_context import update_interview_context

# === GPT Comparison Logic ===
def check_for_missed_questions(full_text, detected_questions, response_callback):
    print("[interview_audit] 🔍 Auditing transcript for missed questions...")
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
5. you can also check if the raw transcription and overall detected questions are similar, if so, skip the audit.

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
        print("[interview_audit] 📩 GPT Raw Output (preview):", content[:200])

        json_block = re.search(r'\[.*\]', content, re.DOTALL)
        if not json_block:
            print("[interview_audit] ❌ Audit GPT returned no valid JSON list.")
            return

        try:
            missed = json.loads(json_block.group(0))
        except json.JSONDecodeError as e:
            print("[interview_audit] ❌ Failed to parse JSON list from GPT output:", e)
            return

        if not missed:
            response_callback("🕵️ Audit checked — no missed questions detected.", popup_id=3)
            return

        for question in missed:
            if question not in detected_questions:
                print(f"[interview_audit] 🔹 Missed: {question}")
                answer = ask_gpt_interview(question)
                log_qa(question, answer)
                update_interview_context(question, answer)
                now = datetime.now().strftime("%H:%M:%S")
                response_callback(f"🤖 [Audit {now}]\n{answer}", popup_id=3)

    except Exception as e:
        print("[interview_audit] ❌ Audit GPT Error:", e)
