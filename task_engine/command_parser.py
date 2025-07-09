# command_parser.py
# ------------------
# Simple rule-based command parser for demo purposes.

def parse_command(text):
    """
    Parses a voice or text instruction into an action dict.
    """
    text = text.lower()

    if "open chrome" in text:
        return {"action": "launch", "target": "chrome"}

    elif "open notepad" in text:
        return {"action": "launch", "target": "notepad"}

    elif "youtube" in text:
        return {"action": "navigate", "target": "youtube"}

    elif "play" in text:
        search_term = text.split("play")[-1].strip()
        return {"action": "search_youtube", "target": search_term}

    elif "ask chatgpt" in text:
        query = text.split("ask chatgpt", 1)[-1].strip()
        return {"action": "ask_chatgpt", "text": query}

    return None

# Test example
if __name__ == "__main__":
    cmd = "play tarak mehta episode 541"
    print(parse_command(cmd))
