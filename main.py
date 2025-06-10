# main.py

from overlay_ui import launch_overlay
from detect import detect_from_camera

if __name__ == "__main__":
    launch_overlay()  # 🧼 Start transparent overlay
    detect_from_camera()  # 🚀 Start camera + detection + GPT
