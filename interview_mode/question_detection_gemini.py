# question_detection_gemini.py

import os
import json
import google.generativeai as genai
from dotenv import load_dotenv

# Load API key
load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# === State ===
input_chain = []
last_question = None
MAX_FRAGMENTS = 3

def classify_combined_input(combined_input, base_input=None):
    """
    Uses Gemini to classify whether the combined input is a new question, follow-up, or irrelevant.
    Returns a dict with intent, new_question_text, is_question, is_follow_up.
    """
    prompt = f"""
You are a helpful AI that classifies user input during an interview or conversation.

Based on the user's speech, decide whether the current input is:
1. A completely new question
2. A follow-up to the last question
3. Irrelevant or incomplete (e.g., filler words, noises, hesitation, partial thoughts)

Return only valid JSON with the following fields:
- "intent": one of ["new_question", "follow_up", "irrelevant_or_incomplete"]
- "new_question_text": full question if applicable (string, empty or null otherwise)
- "is_question": true or false
- "is_follow_up": true or false

Examples:
- If user says "Can you explain polymorphism?" → intent: new_question
- If user says "And what if it's private?" after a question → intent: follow_up
- If user says "Hmm okay maybe..." → intent: irrelevant_or_incomplete

Base Input (last question): "{base_input or 'None'}"
Current Input (combined fragment): "{combined_input.strip()}"

IMPORTANT:
- Use the full context to decide.
- If you think it's a valid question, make sure it ends with "?" in "new_question_text".
- Respond ONLY with the JSON object. No extra explanation or markdown.
"""

    try:
        model = genai.GenerativeModel("models/gemini-1.5-pro")
        response = model.generate_content(prompt)
        output = response.text.strip()

        # Clean markdown wrapping
        if output.startswith("```"):
            output = output.strip("`").strip()
            if output.startswith("json"):
                output = output[4:].strip()

        parsed = json.loads(output)

        # Normalize: add ? if needed
        if parsed.get("intent") == "new_question":
            q = parsed.get("new_question_text", "")
            if q and not q.endswith("?"):
                parsed["new_question_text"] = q.strip() + "?"

        return parsed

    except Exception as e:
        return {
            "intent": "error",
            "error": str(e),
            "raw_output": output if 'output' in locals() else None
        }

def detect_question(input_text):
    """
    Main function to accumulate input fragments and decide classification using Gemini.
    """
    global input_chain, last_question

    input_text = input_text.strip()
    input_chain.append(input_text)
    combined_input = " ".join(input_chain)

    ai_result = classify_combined_input(combined_input, last_question)

    if ai_result.get("intent") in ("new_question", "follow_up"):
        input_chain = []
        if ai_result["intent"] == "new_question":
            last_question = ai_result["new_question_text"]
        return ai_result

    if len(input_chain) >= MAX_FRAGMENTS:
        input_chain = []
        return ai_result

    return {
        "intent": "waiting_for_more_input",
        "combined_input": combined_input,
        "fragments_collected": len(input_chain)
    }
