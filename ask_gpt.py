# ask_gpt.py
from openai import OpenAI
from dotenv import load_dotenv
import os
from memory_manager import get_recent_context, save_message

# Load API key
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key)

def ask_gpt(prompt):
    try:
        # ⬅️ Get recent context from memory
        messages = get_recent_context()
        messages.append({"role": "user", "content": prompt})

        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages,
            temperature=0.7
        )
        reply = response.choices[0].message.content.strip()

        # 💾 Save conversation turn
        save_message("user", prompt)
        save_message("assistant", reply)

        return reply

    except Exception as e:
        print(f"❌ GPT Error:\n\n{e}")
        return "Sorry, I couldn't get a response from GPT."
