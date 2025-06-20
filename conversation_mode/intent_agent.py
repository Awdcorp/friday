# conversation_mode/intent_agent.py

"""
Intent Agent – Classifies the user's utterance into high-level intent categories:
- Question (e.g. "What is the time?")
- Command (e.g. "Open Chrome")
- Follow-up (e.g. "Now summarize it")
- Casual/Noise (e.g. "Uhh", background sounds)

Uses GPT to determine the best-fit category.
"""

from ask_gpt import ask_gpt

# List of valid intent types we support
VALID_INTENTS = ["question", "command", "follow_up", "casual"]

def detect_intent(transcript: str) -> str:
    """
    Sends the transcript to GPT and asks it to classify the intent.
    Returns one of the supported intent categories.
    """

    print("📨 Detecting intent...")
    print(f"🗣️ Transcript: {transcript}")

    prompt = f"""
You are an AI intent classifier. Classify the following user input into one of these categories:
- question
- command
- follow_up
- casual

Return only the intent name in lowercase.
Input: "{transcript}"
Intent:
    """

    try:
        raw_output = ask_gpt(prompt)
        print(f"📤 GPT Raw Output: {raw_output}")

        intent = raw_output.strip().lower()

        if intent not in VALID_INTENTS:
            print(f"⚠️ Unrecognized intent from GPT: '{intent}' → defaulting to 'casual'")
            return "casual"

        print(f"🧠 Detected Intent: {intent}")
        return intent

    except Exception as e:
        print(f"❌ Error during intent detection: {e}")
        return "casual"
