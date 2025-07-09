# web_action_router.py
# ------------------------
# Handles general web actions based on GPT-parsed instructions

import time
import webbrowser
import pyautogui
from .gui_mouse import click_text
from .screen_vision import locate_text_on_screen


def open_url(url: str):
    print(f"🌐 Opening {url} in browser...")
    webbrowser.open(url)
    time.sleep(6)


def search_on_site(query: str):
    print(f"🔍 Attempting to find a search bar and search for: {query}")
    # Try to find 'Search', 'Explore', 'Ask anything', etc.
    candidates = ["Search", "Explore", "Ask anything", "Type here"]
    for label in candidates:
        if click_text(label, debug=True):
            time.sleep(1)
            pyautogui.typewrite(query, interval=0.05)
            pyautogui.press('enter')
            print(f"✅ Search triggered for '{query}'")
            return True
    print("❌ Could not find a search box")
    return False


def click_on_label(label: str):
    print(f"🖱️ Attempting to click on '{label}' using OCR")
    return click_text(label, debug=True)


def type_text(text: str):
    print(f"⌨️ Typing: {text}")
    pyautogui.typewrite(text, interval=0.05)


def scroll_page(direction: str = "down"):
    print(f"🖱️ Scrolling {direction}")
    if direction == "down":
        pyautogui.scroll(-300)
    elif direction == "up":
        pyautogui.scroll(300)


def handle_web_action(parsed: dict):
    action = parsed.get("action")
    if action == "open_url":
        open_url(parsed.get("site"))
    elif action == "search_site":
        open_url(parsed.get("site"))
        search_on_site(parsed.get("query"))
    elif action == "click":
        click_on_label(parsed.get("text"))
    elif action == "type":
        type_text(parsed.get("text"))
    elif action == "scroll":
        scroll_page(parsed.get("direction", "down"))
    else:
        print(f"⚠️ Unsupported web action: {action}")
