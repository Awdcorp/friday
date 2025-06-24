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
    
    Args:
        question (str): The interview question.
        profile (str): The GPT role profile key (e.g., 'software_engineer').
    """
    print(f"\n[ask_gpt_interview] 📥 Received question: \"{question}\"")
    print(f"[ask_gpt_interview] 🧑‍💻 Using profile: {profile}")

    # Step 1: Get prior Q&A context
    context_str = get_interview_context_string()
    print("[ask_gpt_interview] 📚 Context length:", len(context_str.split()), "words")

    # Step 2: Load prompt for selected profile
    persona_prompt = PROMPT_PROFILES.get(profile)
    if not persona_prompt:
        print(f"[ask_gpt_interview] ⚠️ Unknown profile: {profile}. Falling back to 'software_engineer'.")
        persona_prompt = PROMPT_PROFILES["software_engineer"]

    # Step 3: Build the full prompt
    full_prompt = f"""{persona_prompt}

Prior Q&A context:
{context_str}

Now the interviewer asks:
"{question}"

Answer as Friday.
"""

    print("[ask_gpt_interview] 🧾 Final prompt built.")
    print("──────────────── Prompt Preview ────────────────")
    print(full_prompt[:800] + ("\n... [truncated]" if len(full_prompt) > 800 else ""))
    print("────────────────────────────────────────────────")

    try:
        # Step 4: Call OpenAI API
        print("[ask_gpt_interview] 🚀 Sending to GPT (model: gpt-3.5-turbo)...")
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": full_prompt}],
            temperature=0.7
        )

        # Step 5: Extract response
        reply = response.choices[0].message.content.strip()
        print("[ask_gpt_interview] ✅ GPT responded successfully.")
        print("──────────────── GPT Output Preview ─────────────")
        print(reply[:500] + ("\n... [truncated]" if len(reply) > 500 else ""))
        print("─────────────────────────────────────────────────")
        return reply

    except Exception as e:
        print(f"[ask_gpt_interview] ❌ GPT Error: {e}")
        return "⚠️ Unable to process the question right now."
