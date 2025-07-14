from question_detection import detect_question, question_history
import json

# Sample test sequence
test_fragments = [
    # Simple standalone question
    "what is a pointer",

    # Filler - should be skipped or buffered
    "uh",

    # Follow-up fragments, to be combined
    "how does it work",
    "in memory",

    # New programming question
    "write a C++ program",
    "to reverse a linked list",

    # Follow-up to program
    "what if the input is empty",

    # Unrelated or ambiguous fragment
    "okay fine",

    # Shift back to new concept
    "explain memory leak",

    # Another program
    "implement binary search in Java",

    # Follow-up again
    "now do it for a sorted array of strings",

    # End thread
    "thanks, let's move on",

    # New standalone
    "what is virtual function"
]

print("=== 🧠 Testing Enhanced Question Detection ===\n")

for i, fragment in enumerate(test_fragments, 1):
    print(f"[Fragment {i}] \"{fragment}\" →")
    result = detect_question(fragment)

    # Print classification input
    if result.get("current_input") is not None:
        print("📤 Sent to GPT:")
        print(f"   ➤ Current Input : {result['current_input']}")
        print(f"   ➤ Base Question : {result['base_input'] or 'None'}")

    # Print classification result
    if result["intent"] == "waiting_for_more_input":
        print("⏳ Waiting for more fragments...")
        print(json.dumps(result, indent=2))
        if result.get("note"):
            print(f"🟡 Note: {result['note']}")
    elif result["intent"] == "parse_error":
        print("❌ Parse Error from GPT:")
        print(result["raw_output"])
    elif result["intent"] == "error":
        print("🚨 Error:")
        print(result["error"])
    else:
        print("✅ Classified:")
        print(json.dumps(result, indent=2))

    # Show latest root question for clarity
    if question_history:
        last = question_history[-1]
        print(f"🧠 Latest Question Stored: {last['question']}")
        if last.get("is_follow_up"):
            print(f"   ↪ Follow-up to: {last.get('link_to', '[Unknown]')}")

    print("-" * 60)
