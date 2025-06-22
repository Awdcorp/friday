
"""
ask_gpt_interview.py
---------------------
Dedicated GPT interface for Interview Mode in Friday Assistant.
Sends questions to GPT-4 with a hardcoded senior software engineer profile.
"""

from openai import OpenAI
import os
from .interview_prompt_profile import engineer_prompt

# Load API key from environment
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def ask_gpt_interview(question):
    """
    Sends the transcribed interview question to GPT with a hardcoded profile.

    Args:
        question (str): The interview question to answer.

    Returns:
        str: The assistant's response.
    """
    messages = [
        {"role": "system", "content": engineer_prompt},
        {"role": "user", "content": question}
    ]

    try:
        print(f"📤 Sending to GPT-4: {question}")
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages,
            temperature=0.7
        )
        reply = response.choices[0].message.content.strip()
        print(f"✅ GPT Response: {reply}")
        return reply

    except Exception as e:
        print(f"❌ GPT Error: {e}")
        return "⚠️ Unable to process the question right now."
