from question_detection_gemini import detect_question
import json

# === Test input: realistic C interview-style voice fragments ===
conversation_fragments = [
    "Can you explain",
    "the difference between",
    "call by value and call by reference",
    "in C?",
    "uhhh let me think",
    "hmm",
    "And how is this",
    "different when using",
    "pointers?",
    "What is a",
    "dangling pointer",
    "and how does it occur?",
    "Can you give",
    "an example?",
    "ahh",
    "i forgot",
    "How does malloc",
    "differ from calloc?"
]

# === Run detection and print only raw outputs ===
print("=== RAW OUTPUT from question_detection ===\n")

for i, fragment in enumerate(conversation_fragments, start=1):
    result = detect_question(fragment.strip())
    
    print(f"[Fragment {i}] \"{fragment.strip()}\" →")
    print(json.dumps(result, indent=2))
    print("-" * 60)
