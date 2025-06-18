# conversation_mode/reasoning_core.py

"""
Reasoning Core – This is Friday’s main brain.
It receives the transcript and the detected intent,
then produces a meaningful response using GPT (or local model).

Responsibility:
- Handle logic differently based on intent
- Generate responses for questions, commands, follow-ups
- Skip or fallback for casual/noise
"""

from ask_gpt import ask_gpt
from local_llm_interface import ask_local_llm  # optional fallback
from conversation_mode.prompt_builder import build_prompt  # To implement soon

USE_GPT = True  # Can toggle for offline use in future


def get_response(transcript: str, intent: str) -> str:
    """
    Main function that returns a smart response to the user's utterance.
    Uses prompt builder + GPT reasoning based on intent.
    """
    if intent == "casual":
        return "🙂 Got it. Let me know if you need anything."

    try:
        # Step 1: Format structured prompt
        prompt = build_prompt(transcript, intent)

        # Step 2: Choose model (GPT or local)
        if USE_GPT:
            print("🧠 Using GPT for reasoning...")
            reply = ask_gpt(prompt)
        else:
            print("🧠 Using Local LLM for reasoning...")
            reply = ask_local_llm(prompt)

        return reply.strip()

    except Exception as e:
        print(f"❌ Error in reasoning core: {e}")
        return "⚠️ Something went wrong while thinking..."
