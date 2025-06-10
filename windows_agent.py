# windows_agent.py
import pyautogui
import subprocess
import keyboard
import time
import os
import sys

# 📂 1. Open an app by known name
def open_app(app_name):
    known_apps = {
        "notepad": "notepad",
        "chrome": "chrome",
        "calculator": "calc",
        "cmd": "cmd",
        "explorer": "explorer",
    }

    command = known_apps.get(app_name.lower())
    if command:
        try:
            subprocess.Popen(command)
            print(f"✅ Opened: {app_name}")
        except Exception as e:
            print(f"❌ Failed to open {app_name}: {e}")
    else:
        print(f"❓ App '{app_name}' not recognized.")

# ⌨️ 2. Type a string into current window
def type_text(text, delay=0.05):
    try:
        pyautogui.write(text, interval=delay)
        print(f"✅ Typed: {text}")
    except Exception as e:
        print(f"❌ Typing failed: {e}")

# ⌨️ 3. Press a specific key (e.g., enter, tab)
def press_key(key):
    try:
        keyboard.press_and_release(key)
        print(f"✅ Pressed key: {key}")
    except Exception as e:
        print(f"❌ Failed to press key '{key}': {e}")

# 🖱️ 4. Move mouse to (x, y)
def move_mouse(x, y):
    try:
        pyautogui.moveTo(x, y)
        print(f"🖱️ Moved mouse to ({x}, {y})")
    except Exception as e:
        print(f"❌ Mouse move failed: {e}")

# 🖱️ 5. Click at current position or (x, y)
def click(x=None, y=None):
    try:
        if x is not None and y is not None:
            pyautogui.click(x, y)
            print(f"✅ Clicked at ({x}, {y})")
        else:
            pyautogui.click()
            print("✅ Clicked at current mouse position")
    except Exception as e:
        print(f"❌ Click failed: {e}")
