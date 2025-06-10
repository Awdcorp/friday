# task_router.py
from windows_agent import open_app, type_text, press_key, move_mouse, click
import re

def route_command(gpt_response):
    response = gpt_response.lower().strip()
    print(f"🧠 Routing command: {response}")

    # OPEN APP
    if "open" in response or "launch" in response:
        apps = ["notepad", "chrome", "calculator", "cmd", "explorer"]
        for app in apps:
            if app in response:
                open_app(app)
                return

    # TYPE SOMETHING
    if "type" in response or "write" in response:
        match = re.search(r'(type|write)\s+(.*)', response)
        if match:
            text = match.group(2).strip(' "\'')
            type_text(text)
            return

    # PRESS KEY
    if "press enter" in response:
        press_key("enter")
        return
    if "press tab" in response:
        press_key("tab")
        return

    # CLICK
    if "click" in response:
        match = re.search(r'click\s+(\d{2,4})\s+(\d{2,4})', response)
        if match:
            x, y = int(match.group(1)), int(match.group(2))
            click(x, y)
        else:
            click()
        return

    # MOVE MOUSE
    if "move mouse" in response or "move cursor" in response:
        match = re.search(r'(\d{2,4})\s+(\d{2,4})', response)
        if match:
            x, y = int(match.group(1)), int(match.group(2))
            move_mouse(x, y)
            return

    # FALLBACK
    print("❓ No actionable command found.")
