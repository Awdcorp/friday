import os
from openai import OpenAI
from dotenv import load_dotenv

# Load API key
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def get_ai_response(detected_objects):
    object_list = ", ".join(detected_objects)
    prompt = (
        f"The following objects are visible through the user's camera: {object_list}. "
        "What do you think the user is doing, and what helpful suggestions can you give?"
    )

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a smart AI assistant observing the user's surroundings."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=150,
            temperature=0.7
        )
        return response.choices[0].message.content

    except Exception as e:
        return f"Error from GPT: {e}"
