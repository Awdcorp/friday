# ask_gpt_interview.py
"""
ask_gpt_interview.py
---------------------
Dedicated GPT interface for Interview Mode with multiple profiles.
"""

from openai import OpenAI
import os
from .interview_prompt_profile import PROMPT_PROFILES
from .interview_context import get_interview_context_string

# Load API key from env
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def ask_gpt_interview(question, profile="software_engineer"):
    """
    Sends the interview question + recent context to GPT.
    Returns GPT's answer.
    """
    print(f"\n[ask_gpt_interview] 📥 Received question: \"{question}\"")
    #print(f"[ask_gpt_interview] 🧑‍💻 Using profile: {profile}")

    # Step 1: Get prior Q&A context
    context_str = get_interview_context_string()
    #print("[ask_gpt_interview] 📚 Context length:", len(context_str.split()), "words")

    # Step 2: Load persona prompt
    persona_prompt = PROMPT_PROFILES.get(profile)
    if not persona_prompt:
        #print(f"[ask_gpt_interview] ⚠️ Unknown profile: {profile}. Falling back to 'software_engineer'.")
        persona_prompt = PROMPT_PROFILES["software_engineer"]

    # Step 3: Add follow-up context if in programming thread
    from .interview_mode_handler import interview_state  # ✅ Lazy import to avoid circular import

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

    # Step 4: Build the full prompt
    full_prompt = f"""{persona_prompt}

{anchor_context.strip()}

Prior Q&A context:
{context_str}

Now the interviewer asks:
"{question}"

Answer as Friday.
"""

    #print("[ask_gpt_interview] 🧾 Final prompt built.")
    #print("──────────────── Prompt Preview ────────────────")
    #print(full_prompt[:120] + ("\n... [truncated]" if len(full_prompt) > 120 else ""))
    #print("────────────────────────────────────────────────")

    try:
        #print("[ask_gpt_interview] 🚀 Sending to GPT (model: gpt-3.5-turbo)...")
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": full_prompt}],
            temperature=0.7
        )

        reply = response.choices[0].message.content.strip()
        #print("[ask_gpt_interview] ✅ GPT responded successfully.")
        #print("──────────────── GPT Output Preview ─────────────")
        #print(reply[:120] + ("\n... [truncated]" if len(reply) > 120 else ""))
        #print("─────────────────────────────────────────────────")
        return reply

    except Exception as e:
        #print(f"[ask_gpt_interview] ❌ GPT Error: {e}")
        return "⚠️ Unable to process the question right now."
