# task_router.py
# ------------------
# Executes parsed commands using app launcher, navigation, and automation tools.
import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import time
import pyautogui
import webbrowser
from agents.app_launcher import open_app
from agents.gui_mouse import click_text


def execute_command(parsed):
    """
    Executes a parsed command dictionary.
    """
    if parsed['action'] == 'launch':
        print(f"🚀 Launching {parsed['target']}...")
        open_app(parsed['target'])
        time.sleep(3)

    elif parsed['action'] == 'navigate':
        if parsed['target'] == 'youtube':
            print("🌐 Navigating to YouTube...")
            webbrowser.open("https://www.youtube.com")
            time.sleep(6)  # Wait for full load

    elif parsed['action'] == 'search_youtube':
        print(f"🔎 Searching YouTube for: {parsed['target']}")
        # Move mouse to YouTube search bar (approx position)
        pyautogui.moveTo(600, 130, duration=0.3)
        pyautogui.click()
        time.sleep(1)

        # Type the search query
        pyautogui.typewrite(parsed['target'], interval=0.05)
        pyautogui.press('enter')
        time.sleep(6)  # Wait for search results

        # Move to first result (approx) and click
        pyautogui.moveTo(600, 300, duration=0.3)
        pyautogui.click()

    elif parsed["action"] == "ask_chatgpt":
        print("🌐 Opening ChatGPT...")
        webbrowser.open("https://chat.openai.com")
        time.sleep(7)  # Wait for site to load

        print("🖱️ Locating message input field...")
        if click_text("Ask anything", debug=True):  # Use OCR to find 'Message' input
            time.sleep(1)
            pyautogui.typewrite(parsed["text"], interval=0.04)
            pyautogui.press('enter')
            print("✅ Prompt submitted to ChatGPT.")
        else:
            print("❌ Could not find ChatGPT input box.")

    else:
        print("⚠️ Unknown action. Cannot execute.")


# Demo sequence processor
if __name__ == "__main__":
    import sys, os
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
    from task_engine.command_parser import parse_command

    input_text = "ask chatgpt generate Quantum computers"
    print("🧠 Parsing multi-step input...")
    steps = [s.strip() for s in input_text.split("and")]

    for step in steps:
        parsed = parse_command(step)
        if parsed:
            execute_command(parsed)
        else:
            print(f"❌ Could not understand: {step}")
