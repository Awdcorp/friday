# app_launcher.py
# ------------------
# Handles launching desktop applications like Chrome, Notepad, etc.

import subprocess
import os

def open_app(app_name):
    """
    Launches an application by name.
    Currently supports hardcoded paths for known apps.
    """
    app_name = app_name.lower()

    if app_name == "chrome":
        path = "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe"
        if os.path.exists(path):
            subprocess.Popen([path])
        else:
            print("❌ Chrome path not found.")

    elif app_name == "notepad":
        subprocess.Popen(["notepad.exe"])

    elif app_name == "vscode":
        subprocess.Popen(["code"])  # Assumes VSCode is in PATH

    else:
        print(f"❌ App '{app_name}' not recognized or not supported.")

# Test run
if __name__ == "__main__":
    open_app("chrome")
