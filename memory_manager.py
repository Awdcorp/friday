# memory_manager.py
import json
import os
from datetime import datetime

MEMORY_FILE = "chat_memory.jsonl"
MAX_CONTEXT_MESSAGES = 10

chat_history = []

def load_memory():
    global chat_history
    if os.path.exists(MEMORY_FILE):
        with open(MEMORY_FILE, "r", encoding="utf-8") as f:
            chat_history = [json.loads(line.strip()) for line in f if line.strip()]
        print(f"📜 Loaded {len(chat_history)} messages from memory")
    else:
        print("📂 No memory file found, starting fresh")

def save_message(role, content):
    entry = {
        "timestamp": datetime.now().isoformat(),
        "role": role,
        "content": content
    }
    chat_history.append(entry)
    with open(MEMORY_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")

def get_recent_context():
    return [
        {"role": msg["role"], "content": msg["content"]}
        for msg in chat_history[-MAX_CONTEXT_MESSAGES:]
    ]

# ✅ Use function instead of variable import
def get_full_memory_log():
    return chat_history.copy()
