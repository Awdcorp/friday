import requests

OLLAMA_URL = "http://localhost:11434/api/generate"

def ask_local_llm(prompt, model="mistral"):
    """
    Send a prompt to the local LLM via Ollama and return the response text.
    """
    try:
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False  # We want the full reply, not streamed
        }

        response = requests.post(OLLAMA_URL, json=payload)
        response.raise_for_status()
        data = response.json()

        return data.get("response", "").strip()

    except Exception as e:
        return f"[Local LLM Error] {str(e)}"
