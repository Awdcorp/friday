"""
ask_gpt_interview.py
---------------------
Dedicated GPT interface for Interview Mode with multiple profiles.
"""

from openai import OpenAI
import os
from .interview_prompt_profile import PROMPT_PROFILES
from .interview_context import get_interview_context_string

# === Module tag for logging ===
MODULE = "[ask_gpt]"

def log(msg):
    print(f"{MODULE} {msg}")

# === Load API key ===
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def ask_gpt_interview(question, profile="software_engineer"):
    """
    Sends the interview question + recent context to GPT.
    Returns GPT's answer.
    """
    log(f"📥 Received question: \"{question}\"")

    # Step 1: Retrieve recent Q&A context
    context_str = get_interview_context_string()

    # Step 2: Load persona prompt
    persona_prompt = PROMPT_PROFILES.get(profile)
    if not persona_prompt:
        log(f"⚠️ Unknown profile '{profile}', using fallback profile.")
        persona_prompt = PROMPT_PROFILES["software_engineer"]

    # Step 3: Add anchor Q&A if in programming thread
    from .interview_mode_handler import interview_state  # Lazy import to avoid circular dependency

    anchor_context = ""
    if (
        profile == "software_engineer"
        and interview_state.get("program_thread_active")
        and interview_state.get("followup_count", 0) > 0
    ):
        anchor_q = interview_state.get("program_anchor_question")
        anchor_a = interview_state.get("program_anchor_answer")
        if anchor_q and anchor_a:
            anchor_context = f"""
This is a follow-up to the previous programming question:
Q: {anchor_q}
A: {anchor_a}
"""
            log("📎 Including anchor Q&A in prompt.")

    # Step 4: Build full prompt
    full_prompt = f"""{persona_prompt}

{anchor_context.strip()}

Prior Q&A context:
{context_str}

Now the interviewer asks:
"{question}"

Answer as Friday.
"""

    try:
        log("🚀 Sending prompt to GPT...")
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": full_prompt}],
            temperature=0.7
        )

        reply = response.choices[0].message.content.strip()
        log("✅ GPT responded successfully.")
        return reply

    except Exception as e:
        log(f"❌ GPT Error: {e}")
        return "⚠️ Unable to process the question right now."
