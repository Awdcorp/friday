from question_detection import detect_question
import json

# Sample test sequence
test_fragments = [
    "Can you explain the difference between call by value and call by reference in C?",
    "What is a pointer in C, and how is it used?",
    "Can you tell me",            
    "Write a program to find the factorial of a number.",
    "Can you optimize it using recursion?",
    "What if the number is zero?",
    "What if input is negative?",
    "What's the difference between stack and queue?",
    "What are the risks of using malloc without checking the return value?"
]

print("=== 🧠 Testing Enhanced Question Detection (No History Mode) ===\n")

for i, fragment in enumerate(test_fragments, 1):
    print(f"[Fragment {i}] \"{fragment}\" →")
    result = detect_question(fragment)

    # Print classification input
    if result.get("current_input") is not None:
        print("📤 Sent to GPT:")
        print(f"   ➤ Current Input : {result['current_input']}")
        print(f"   ➤ Base Input    : {result.get('base_input') or 'None'}")

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

    print("-" * 60)
