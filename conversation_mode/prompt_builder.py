# conversation_mode/prompt_builder.py

"""
Prompt Builder – Dynamically generates GPT prompt
based on user input, intent, and current context.

This allows Friday to provide better answers by including:
- Prior memory
- Detected task intent
- Clear instruction formatting
"""

from conversation_mode.context_manager import get_recent_context

def build_prompt(transcript: str, intent: str) -> str:
    """
    Constructs a structured prompt string for GPT
    based on intent and previous context.
    Logs key details for traceability.
    """
    print("🧱 Building Prompt")
    print(f"🔍 Intent: {intent}")
    print(f"💬 User Transcript: {transcript}")

    # 1. Fetch recent memory (e.g., last task, topic, user flow)
    context = get_recent_context()
    print("🧠 Recent Context Fetched:", repr(context[:200]) + ("..." if len(context) > 200 else ""))

    # 2. Format prompt differently based on intent
    if intent == "question":
        prompt = f"""
You are Friday, a helpful AI assistant. Here is the current context:

{context}

Now the user asked a question:
"{transcript}"

Answer clearly and concisely.
"""
    elif intent == "command":
        prompt = f"""
You are Friday, a smart assistant that executes system-level or workflow tasks.

Context:
{context}

The user gave this instruction:
"{transcript}"

Summarize the task or give a confirmation message.
If it's code or an action, give clean output or description.
"""
    elif intent == "follow_up":
        prompt = f"""
You are continuing an earlier task. Previous context:

{context}

User follow-up:
"{transcript}"

Respond appropriately — continue, modify, or clarify.
"""
    else:  # fallback
        prompt = f"You received: \"{transcript}\". Try to be helpful."

    print("🧾 Final Prompt:\n" + prompt.strip())
    return prompt.strip()
