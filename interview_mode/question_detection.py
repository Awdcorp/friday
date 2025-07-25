import os
import json
from openai import OpenAI
from dotenv import load_dotenv

# === Module tag for logging ===
MODULE = "[detect]"

def log(msg):
    print(f"{MODULE} {msg}")

# === Load OpenAI API key ===
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# === Internal state ===
last_question = None  # Tracks the latest confirmed question
input_chain = []  # Stores buffered input fragments
WORD_TRIGGER_THRESHOLD = 2  # Minimum number of words to trigger classification


def classify_combined_input(combined_input, base_input=None, buffer_only=None):
    """
    Classifies the combined input using GPT with optional base context.
    Returns a dictionary with intent and related fields.
    """

    # === Few-shot examples to guide GPT ===
    examples = """
Examples:
Base: None
Current: What is a pointer in C?
→ intent: new_question

Base: What is a pointer?
Current: How does double pointer work?
→ intent: follow_up

Base: None
Current: Write a C++ program to reverse a string.
→ intent: program_start

Base: Write a program to reverse a string.
Current: Now do it using recursion.
→ intent: program_follow_up
"""

    # === Build the system prompt ===
    system_prompt = (
        "You are an intelligent intent classifier for a technical interview assistant.\n\n"
        "Your job is to detect whether the input is a new question, a follow-up, or a request to write or modify a program.\n\n"
        "Possible values for `intent`:\n"
        "- new_question: A standalone theory/conceptual question.\n"
        "- follow_up: A continuation or elaboration of the previous question.\n"
        "- program_start: A new request to write or implement a program (e.g., 'Write a C++ program to...').\n"
        "- program_follow_up: A modification, extension, or clarification of an already written program (e.g., 'What if input is null?', 'Can you do it in recursion?').\n"
        "- similar_to_previous: A rephrasing of the last question.\n"
        "- irrelevant_or_incomplete: Fragmented, unclear, or filler content.\n\n"
        "Be liberal in identifying programming-related follow-ups — vague phrases like 'optimize this', 'now do it in Java', 'what if it's empty' also count.\n\n"
        "Return a JSON object with:\n"
        "- intent\n"
        "- is_programming (if the question detected is saying to write a program, return True, else False)\n"
        "- topic (what is the topic focus of the question)\n"
        "- is_question\n"
        "- is_follow_up (this applies for both kind of intent follow_up and program_follow_up)\n"
        "- is_similar"
        + examples
    )

    user_prompt = f"""
Base Input (previous question): "{base_input or 'None'}"
Current Input (combined fragment): "{combined_input.strip()}"
""".strip()

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            timeout=10,
            temperature=0,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
        )

        output = response.choices[0].message.content.strip()

        try:
            parsed = json.loads(output)
            parsed.setdefault("is_programming", False)
            parsed.setdefault("topic", None)
            parsed["base_input"] = base_input or None
            parsed["current_input"] = combined_input.strip()
            parsed["buffer_only"] = buffer_only.strip() if buffer_only else None
            return parsed

        except Exception:
            log("❌ Failed to parse GPT response.")
            return {
                "intent": "parse_error",
                "raw_output": output,
                "combined_input": combined_input,
                "base_input": base_input or None
            }

    except Exception as e:
        log(f"❌ GPT API Error: {e}")
        return {
            "intent": "error",
            "error": str(e),
            "combined_input": combined_input,
            "base_input": base_input or None
        }


def detect_question(input_text):
    """
    Buffers input fragments and triggers classification when enough input is received.
    Uses the last detected question as base for follow-ups, but does NOT overwrite it with follow-ups.
    """
    global input_chain, last_question

    input_text = input_text.strip()
    word_count = len(input_text.split())

    log(f"🎙️ Fragment: \"{input_text}\"")

    # === Skip filler fragments ===
    filler_phrases = {"hmm", "uh", "uhh", "uhhh", "let me think", "ah", "ahh"}
    if input_text.lower() in filler_phrases:
        log("⏳ Filler skipped.")
        return {
            "intent": "waiting_for_more_input",
            "note": "filler skipped",
            "fragments_collected": len(input_chain),
            "words_collected": sum(len(f.split()) for f in input_chain)
        }

    # === Shortcut: single direct question ===
    if word_count >= 3 and not input_chain:
        if input_text.lower().startswith(("what is", "define", "explain", "how does", "can you", "when does", "why does")):
            input_chain.append(input_text)
            result = classify_combined_input(
                input_text,
                base_input=last_question,
                buffer_only=input_text
            )

            if result.get("intent") in {"new_question", "program_start", "follow_up", "program_follow_up"}:
                input_chain = []
                if result["intent"] in {"new_question", "program_start"}:
                    last_question = input_text.rstrip("?") + "?"

                log(f"✅ Intent: {result['intent']} | Prog: {result['is_programming']} | Follow: {result['is_follow_up']} | Topic: {result.get('topic', '')}")
                return result

            return result

    # === Buffered path ===
    input_chain.append(input_text)
    buffer_only = " ".join(input_chain)
    total_words = len(buffer_only.split())

    if total_words >= WORD_TRIGGER_THRESHOLD:
        result = classify_combined_input(
            buffer_only,
            base_input=last_question,
            buffer_only=buffer_only
        )

        if result.get("intent") in {"new_question", "program_start", "follow_up", "program_follow_up"}:
            input_chain = []
            if result["intent"] in {"new_question", "program_start"}:
                last_question = buffer_only.rstrip("?") + "?"

            log(f"✅ Intent: {result['intent']} | Prog: {result['is_programming']} | Follow: {result['is_follow_up']} | Topic: {result.get('topic', '')}")
            return result

        return result

    return {
        "intent": "waiting_for_more_input",
        "combined_input": buffer_only,
        "fragments_collected": len(input_chain),
        "words_collected": total_words
    }
