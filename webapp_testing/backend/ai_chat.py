import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def get_ai_response(messages):
    if isinstance(messages, str):
        messages = [{"role": "user", "content": messages}]
    else:
        messages = [{"role": "system", "content": "You are a helpful AI assistant."}] + [
            {"role": "user", "content": m} for m in messages
        ]

    try:
        res = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages,
            max_tokens=150
        )
        return res.choices[0].message.content
    except Exception as e:
        return f"GPT error: {e}"
