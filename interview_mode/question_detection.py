from dotenv import load_dotenv
from openai import OpenAI
import os
import json

# Load API key from environment
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# === Internal state ===
input_chain = []
last_question = None
WORD_TRIGGER_THRESHOLD = 5  # Trigger classification when buffer has ≥ this many words

def classify_combined_input(combined_input, base_input=None, buffer_only=None):
    """
    Classifies the combined input using GPT with optional base context (previous question).
    Returns a JSON-compatible dictionary with classification + reference data.
    """
    try:
        system_prompt = (
            "You are a helpful assistant that classifies whether an input is:\n"
            "1. A new standalone question (different from the previous one)\n"
            "2. A follow-up or continuation to the previous question\n"
            "3. A rephrased or similar version of the previous question\n"
            "4. Irrelevant or incomplete\n\n"
            "Be liberal in identifying follow-ups when:\n"
            "- The base question is still in context\n"
            "- The fragment seems to elaborate or ask something related\n\n"
            "Return a JSON with only these keys:\n"
            "- intent: [new_question, follow_up, similar_to_previous, irrelevant_or_incomplete]\n"
            "- is_question\n"
            "- is_follow_up\n"
            "- is_similar"
        )

        user_prompt = f"""
Base Input (previous question): "{base_input or 'None'}"
Current Input (combined fragment): "{combined_input.strip()}"
""".strip()

        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            temperature=0,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
        )

        output = response.choices[0].message.content.strip()

        try:
            parsed = json.loads(output)

            # Add reference info for debugging/logging
            parsed["base_input"] = base_input or None
            parsed["current_input"] = combined_input.strip()
            parsed["buffer_only"] = buffer_only.strip() if buffer_only else None

            return parsed

        except Exception:
            return {
                "intent": "parse_error",
                "raw_output": output,
                "combined_input": combined_input,
                "base_input": base_input or None
            }

    except Exception as e:
        return {
            "intent": "error",
            "error": str(e),
            "combined_input": combined_input,
            "base_input": base_input or None
        }

def detect_question(input_text):
    """
    Buffers input fragments and sends combined inputs to GPT when confident.
    Updates last_question for new or follow-up cases.
    """
    global input_chain, last_question

    input_text = input_text.strip()
    word_count = len(input_text.split())

    # === Skip known filler fragments ===
    filler_phrases = {"hmm", "uh", "uhh", "uhhh", "let me think", "ah", "ahh"}
    if input_text.lower() in filler_phrases:
        return {
            "intent": "waiting_for_more_input",
            "note": "filler skipped",
            "fragments_collected": len(input_chain),
            "words_collected": sum(len(f.split()) for f in input_chain)
        }

    # === Early classify if clearly standalone question and no buffer
    if word_count >= 3 and not input_chain:
        if input_text.lower().startswith(("what is", "define", "explain", "how does", "can you", "when does", "why does")):
            input_chain.append(input_text)
            combined_input = input_text
            result = classify_combined_input(combined_input, last_question, buffer_only=input_text)

            if result.get("intent") == "new_question":
                last_question = combined_input.strip().rstrip("?") + "?"
                input_chain = []
            elif result.get("intent") == "follow_up":
                last_question = (last_question or "") + " " + combined_input
                last_question = last_question.strip().rstrip("?") + "?"
                input_chain = []

            return result

    # === Buffer the input
    input_chain.append(input_text)
    buffer_only = " ".join(input_chain)
    combined_input = buffer_only
    total_words = len(buffer_only.split())

    # === Trigger classification when buffer is long enough
    if total_words >= WORD_TRIGGER_THRESHOLD:
        result = classify_combined_input(combined_input, last_question, buffer_only=buffer_only)

        if result.get("intent") == "new_question":
            last_question = combined_input.strip().rstrip("?") + "?"
            input_chain = []
        elif result.get("intent") == "follow_up":
            last_question = (last_question or "") + " " + combined_input
            last_question = last_question.strip().rstrip("?") + "?"
            input_chain = []

        return result

    # === Still collecting fragments
    return {
        "intent": "waiting_for_more_input",
        "combined_input": buffer_only,
        "fragments_collected": len(input_chain),
        "words_collected": total_words
    }