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
MAX_FRAGMENTS = 3

def classify_combined_input(combined_input, base_input=None):
    """
    Classifies the combined input using GPT with optional base context (previous question).
    Returns a JSON-compatible dictionary.
    """
    try:
        # More intelligent system prompt
        system_prompt = (
            "You are a helpful assistant that classifies whether an input is:\n"
            "1. A new standalone question (and different from the previous question)\n"
            "2. A follow-up to the previous question\n"
            "3. A new question but similar or rephrased version of the previous one\n"
            "4. Irrelevant or incomplete\n\n"
            "Return a JSON with the following keys:\n"
            "- intent: one of [new_question, follow_up, similar_to_previous, irrelevant_or_incomplete]\n"
            "- new_question_text: cleaned and complete question text if any\n"
            "- is_question: true or false\n"
            "- is_follow_up: true if it's a follow-up to last question\n"
            "- is_similar: true if it is a new question but similar to last one"
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

        # Try parsing the JSON response
        try:
            parsed = json.loads(output)

            # Normalize question mark if intent is new_question
            if parsed.get("intent") == "new_question":
                q = parsed.get("new_question_text", "")
                if q and not q.endswith("?"):
                    parsed["new_question_text"] = q.strip() + "?"

            return parsed

        except Exception:
            return {
                "intent": "parse_error",
                "raw_output": output,
                "combined_input": combined_input
            }

    except Exception as e:
        return {
            "intent": "error",
            "error": str(e),
            "combined_input": combined_input
        }

def detect_question(input_text):
    """
    Main handler: buffers fragments, decides when to classify, and updates state.
    Returns classification dict or 'waiting' status.
    """
    global input_chain, last_question

    input_text = input_text.strip()
    input_chain.append(input_text)

    combined_input = " ".join(input_chain)
    ready = len(input_chain) >= MAX_FRAGMENTS

    if ready:
        result = classify_combined_input(combined_input, last_question)

        # === Update behavior based on classification ===
        if result.get("intent") == "new_question":
            last_question = result.get("new_question_text")
            input_chain = []

        elif result.get("intent") == "similar_to_previous":
            # Do not update last_question, just clear buffer
            input_chain = []

        elif result.get("intent") in ("follow_up", "irrelevant_or_incomplete"):
            input_chain = []

        return result

    # Wait for more input
    return {
        "intent": "waiting_for_more_input",
        "combined_input": combined_input,
        "fragments_collected": len(input_chain)
    }
