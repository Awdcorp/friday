import pyautogui
from .screen_vision import locate_text_on_screen, locate_text_on_screen_debug
import time

# === Move mouse to the position of text ===
def move_mouse_to_text(text_query: str, duration: float = 0.3, debug: bool = False) -> bool:
    """
    Moves the mouse to the location of the given text on screen.
    Returns True if successful, False if text not found.
    """
    if debug:
        result = locate_text_on_screen_debug(text_query)
        if result:
            x, y = result['position']
            print(f"🖱️ Moving to '{result['text']}' at ({x}, {y}) with confidence {result['confidence']:.2f}")
            pyautogui.moveTo(x, y, duration=duration)
            return True
        return False
    else:
        pos = locate_text_on_screen(text_query)
        if pos:
            pyautogui.moveTo(pos[0], pos[1], duration=duration)
            return True
        return False

# === Move and click on the text ===
def click_text(text_query: str, duration: float = 0.3, clicks: int = 1, interval: float = 0.1, debug: bool = False) -> bool:
    """
    Moves mouse to the text and clicks it.
    Returns True if clicked, False if not found.
    """
    if move_mouse_to_text(text_query, duration=duration, debug=debug):
        time.sleep(0.1)
        pyautogui.click(clicks=clicks, interval=interval)
        print(f"✅ Clicked on '{text_query}'")
        return True
    print(f"❌ Could not find '{text_query}' on screen")
    return False

# === Example test ===
if __name__ == '__main__':
    label = input("Enter button text to click: ")
    debug = input("Enable debug mode? (y/n): ").strip().lower() == 'y'
    click_text(label, debug=debug)
