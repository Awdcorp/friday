# ask_gpt.py
from openai import OpenAI
from dotenv import load_dotenv
import os
from memory_manager import get_recent_context, save_message

# Load API key
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key)

# 👨‍💻 Define the assistant's role as a senior C/C++ engineer
PROFILE_MESSAGE = {
    "role": "system",
    "content": (
        "You are a senior software engineer with over 10 years of experience in C and C++. "
        "You are currently participating in a technical interview. "
        "Answer all questions as if you are explaining them to an interviewer. "
        "Be precise, use technical language, and justify your answers with examples or code when relevant. "
        "Stay professional and confident in tone. "
        "Avoid overly verbose explanations unless clarification is asked."
    )
}

def ask_gpt(prompt):
    try:
        # ⬅️ Get recent context from memory
        messages = [PROFILE_MESSAGE] + get_recent_context()
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
