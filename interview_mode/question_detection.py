import os
import json
from openai import OpenAI
from dotenv import load_dotenv

# === Load OpenAI API key ===
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# === Internal state ===
last_question = None  # Tracks the latest confirmed question
last_root_question = None  # ✅ Tracks the stable root for base_input
input_chain = []  # Stores buffered input fragments
question_history = []  # Stores rolling Q&A memory with follow-up tracking
WORD_TRIGGER_THRESHOLD = 2  # Minimum number of words to trigger classification
MAX_HISTORY = 3  # Max questions to include in context for GPT


def classify_combined_input(combined_input, base_input=None, buffer_only=None, recent_history=None):
    """
    Classifies the combined input using GPT with optional base and rolling history.
    Returns a JSON-compatible dictionary with intent, flags, and debug fields.
    """

    # === Few-shot examples to guide GPT more reliably ===
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

    # === Format recent history for GPT (show follow-up links) ===
    history_str = ""
    if recent_history:
        context_lines = []
        for i, q in enumerate(recent_history):
            q_num = f"Q{i+1}"
            if q.get("is_follow_up"):
                q_line = f"{q_num} (follow-up to previous): {q['question']}"
            else:
                q_line = f"{q_num}: {q['question']}"
            a_line = f"A{i+1}: {q.get('answer', '[not answered]')}"
            context_lines.extend([q_line, a_line])
        history_str = "\nRecent Context:\n" + "\n".join(context_lines)

    # === Build the final system prompt ===
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
        "- topic (if relevant)\n"
        "- is_question\n"
        "- is_follow_up\n"
        "- is_similar"
        + examples + history_str
    )

    user_prompt = f"""
Base Input (previous question): "{base_input or 'None'}"
Current Input (combined fragment): "{combined_input.strip()}"
""".strip()

    try:
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
            parsed.setdefault("is_programming", False)
            parsed.setdefault("topic", None)
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
    Buffers input fragments and triggers classification when enough input is received.
    Tracks rolling history of past Q&A to aid in intent detection.
    """
    global input_chain, question_history, last_question, last_root_question

    input_text = input_text.strip()
    word_count = len(input_text.split())

    # === Skip filler fragments ===
    filler_phrases = {"hmm", "uh", "uhh", "uhhh", "let me think", "ah", "ahh"}
    if input_text.lower() in filler_phrases:
        return {
            "intent": "waiting_for_more_input",
            "note": "filler skipped",
            "fragments_collected": len(input_chain),
            "words_collected": sum(len(f.split()) for f in input_chain)
        }

    # === Heuristic shortcut: detect likely questions immediately if alone ===
    if word_count >= 3 and not input_chain:
        if input_text.lower().startswith(("what is", "define", "explain", "how does", "can you", "when does", "why does")):
            input_chain.append(input_text)
            combined_input = input_text
            result = classify_combined_input(
                combined_input,
                base_input=last_root_question,
                buffer_only=input_text,
                recent_history=question_history[-MAX_HISTORY:]
            )

            if result.get("intent") in {"new_question", "program_start", "follow_up", "program_follow_up"}:
                input_chain = []
                entry = {
                    "question": combined_input.strip().rstrip("?") + "?",
                    "answer": None,
                    "topic": result.get("topic", None),
                    "is_follow_up": result["intent"] in {"follow_up", "program_follow_up"},
                    "link_to": question_history[-1]["question"] if result["intent"] in {"follow_up", "program_follow_up"} and question_history else None
                }
                question_history.append(entry)
                last_question = entry["question"]
                if result["intent"] in {"new_question", "program_start"}:
                    last_root_question = entry["question"]  # ✅ Reset thread root
                return result

            return result

    # === Buffer the current fragment ===
    input_chain.append(input_text)
    buffer_only = " ".join(input_chain)
    combined_input = buffer_only
    total_words = len(buffer_only.split())

    # === Trigger GPT classification if buffer is long enough ===
    if total_words >= WORD_TRIGGER_THRESHOLD:
        result = classify_combined_input(
            combined_input,
            base_input=last_root_question,
            buffer_only=buffer_only,
            recent_history=question_history[-MAX_HISTORY:]
        )

        if result.get("intent") in {"new_question", "program_start", "follow_up", "program_follow_up"}:
            input_chain = []
            entry = {
                "question": combined_input.strip().rstrip("?") + "?",
                "answer": None,
                "topic": result.get("topic", None),
                "is_follow_up": result["intent"] in {"follow_up", "program_follow_up"},
                "link_to": question_history[-1]["question"] if result["intent"] in {"follow_up", "program_follow_up"} and question_history else None
            }
            question_history.append(entry)
            last_question = entry["question"]
            if result["intent"] in {"new_question", "program_start"}:
                last_root_question = entry["question"]  # ✅ Reset anchor
            return result

        return result

    # === Still waiting for more fragments ===
    return {
        "intent": "waiting_for_more_input",
        "combined_input": buffer_only,
        "fragments_collected": len(input_chain),
        "words_collected": total_words
    }
