from question_detection import detect_question
import json

# Sample test sequence
test_fragments = [
    "what is pointer",
    "hmm",
    "and how it",
    "will be used",
    "uh",
    "define memory leak",
    "can you explain",
    "malloc",
    "and how it works"
]

print("=== Testing Enhanced Question Detection ===\n")

for i, fragment in enumerate(test_fragments, 1):
    print(f"[Fragment {i}] \"{fragment}\" →")
    result = detect_question(fragment)

    # Show what was sent to GPT for classification
    if result.get("current_input"):
        print("📤 Input sent to GPT:")
        print(f"   Current Input : {result['current_input']}")
        print(f"   Base Question : {result['base_input'] or 'None'}")

    if result["intent"] == "waiting_for_more_input":
        note = result.get("note", "")
        print(json.dumps(result, indent=2))
        if note:
            print(f"🟡 Skipped or buffered due to: {note}")
        else:
            print(f"🟡 Waiting: {result['fragments_collected']} fragments, {result['words_collected']} words")
    else:
        print("✅ Classified:")
        print(json.dumps(result, indent=2))
        if result.get("intent") == "new_question":
            print(f"🧠 Updated last_question: {result.get('new_question_text')}")
    print("------------------------------------------------------------")