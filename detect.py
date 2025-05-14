from ultralytics import YOLO
import cv2
import time
import threading
import logging
import datetime
from ai_chat import get_ai_response
from ocr import extract_text_from_frame

# Reduce YOLO logs
logging.getLogger("ultralytics").setLevel(logging.WARNING)

# Load YOLOv8 model
model = YOLO("yolov8s.pt")  # More accurate than yolov8n

# Globals
last_detected_objects = set()
last_detected_text = ""
last_asked_time = 0
cooldown = 30               # Minimum seconds between GPT calls
wait_if_no_change = 120     # Max wait if nothing changes
gpt_thread = None
gpt_lock = threading.Lock()

# 🔍 Log helper function
def log(msg, level="INFO", emoji="ℹ️"):
    now = datetime.datetime.now().strftime("%H:%M:%S")
    print(f"[{now}] {emoji} [{level}] {msg}")

def ask_gpt_async(objects, screen_text):
    global last_detected_objects, last_detected_text, last_asked_time
    with gpt_lock:
        log(f"Detected objects: {objects}", "YOLO", "🔍")
        if screen_text:
            log(f"Detected screen text: {screen_text}", "OCR", "📄")

        # Compose GPT prompt
        prompt = (
            f"The camera sees the following objects: {', '.join(objects)}.\n"
            f"The visible text on screen is: \"{screen_text}\".\n"
            "What is the user likely doing, and what suggestions can you give?"
        )

        # Send to GPT
        log("Sending prompt to GPT...", "GPT", "🤖")
        try:
            response = get_ai_response([prompt])
            log("GPT response received:", "GPT", "✅")
            print("\n" + "=" * 50)
            print(response)
            print("=" * 50 + "\n")
        except Exception as e:
            response = f"GPT Error: {e}"
            log(str(e), "GPT ERROR", "❌")

        # Update state
        last_detected_objects = set(objects)
        last_detected_text = screen_text
        last_asked_time = time.time()

def detect_from_camera():
    global gpt_thread, last_detected_objects, last_detected_text, last_asked_time

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        log("Could not open webcam", "ERROR", "❌")
        return

    log("Friday AI - YOLO + OCR + GPT Mode ON. Press 'q' to quit.", "START", "🧠")

    while True:
        ret, frame = cap.read()
        if not ret:
            log("Failed to read frame from webcam", "ERROR", "❌")
            break

        log("Frame captured", "FRAME", "📥")

        try:
            results = model(frame, stream=True)
            for r in results:
                annotated_frame = r.plot()
                labels = [model.names[int(cls)] for cls in r.boxes.cls]
        except Exception as e:
            log(f"YOLO detection error: {e}", "YOLO", "❌")
            labels = []
            continue

        try:
            screen_text = extract_text_from_frame(frame)
        except Exception as e:
            log(f"OCR error: {e}", "OCR", "❌")
            screen_text = ""

        # Show annotated frame
        cv2.imshow("Friday - Vision Mode", annotated_frame)

        current_labels = set(labels)
        current_time = time.time()

        scene_changed = (
            current_labels != last_detected_objects or
            screen_text != last_detected_text
        )

        time_expired = current_time - last_asked_time > wait_if_no_change

        if (scene_changed and current_labels) or time_expired:
            if gpt_thread is None or not gpt_thread.is_alive():
                gpt_thread = threading.Thread(
                    target=ask_gpt_async,
                    args=(list(current_labels), screen_text)
                )
                gpt_thread.start()

        if cv2.waitKey(1) & 0xFF == ord("q"):
            log("Quitting...", "EXIT", "👋")
            break

    cap.release()
    cv2.destroyAllWindows()
