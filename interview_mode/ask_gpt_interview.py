# ask_gpt_interview.py
"""
ask_gpt_interview.py
---------------------
Dedicated GPT interface for Interview Mode.
Uses context + custom persona.
"""

from openai import OpenAI
import os
from .interview_prompt_profile import engineer_prompt
from .interview_context import get_interview_context_string

# Load API key from env
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def ask_gpt_interview(question):
    """
    Sends the interview question + recent context to GPT.
    Returns GPT's answer.
    """
    print(f"\n[ask_gpt_interview] 📥 Received question: \"{question}\"")

    # Step 1: Get prior Q&A context
    context_str = get_interview_context_string()
    print("[ask_gpt_interview] 📚 Context length:", len(context_str.split()), "words")

    # Step 2: Build the full prompt
    full_prompt = f"""{engineer_prompt}

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
        # Step 3: Call OpenAI API
        print("[ask_gpt_interview] 🚀 Sending to GPT (model: gpt-3.5-turbo)...")
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",  # Change to gpt-4 if needed
            messages=[{"role": "user", "content": full_prompt}],
            temperature=0.7
        )

        # Step 4: Extract response
        reply = response.choices[0].message.content.strip()
        print("[ask_gpt_interview] ✅ GPT responded successfully.")
        print("──────────────── GPT Output Preview ─────────────")
        print(reply[:500] + ("\n... [truncated]" if len(reply) > 500 else ""))
        print("─────────────────────────────────────────────────")
        return reply

    except Exception as e:
        print(f"[ask_gpt_interview] ❌ GPT Error: {e}")
        return "⚠️ Unable to process the question right now."
