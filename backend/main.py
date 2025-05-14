from fastapi import FastAPI, WebSocket, WebSocketDisconnect
import base64
import cv2
import numpy as np
from detect import detect_objects_from_frame
from ocr import extract_text_from_frame
from ai_chat import get_ai_response

app = FastAPI()

@app.websocket("/ws/friday")
async def friday_socket(websocket: WebSocket):
    await websocket.accept()
    print("✅ WebSocket connected")

    try:
        while True:
            data = await websocket.receive_text()
            print("📥 Frame received from client")

            if "," not in data:
                print("⚠️ Invalid image format received")
                await websocket.send_json({"error": "Invalid image data"})
                continue

            try:
                # Decode base64 image
                img_bytes = base64.b64decode(data.split(",")[1])
                np_arr = np.frombuffer(img_bytes, np.uint8)
                frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
                
                if frame is None:
                    print("❌ Failed to decode image")
                    await websocket.send_json({"error": "Failed to decode image"})
                    continue
            except Exception as e:
                print(f"❌ Exception during decoding image: {e}")
                await websocket.send_json({"error": f"Image decode error: {str(e)}"})
                continue

            print("🔍 Running object detection and OCR...")

            try:
                objects = detect_objects_from_frame(frame)
                print(f"🟩 Objects detected: {objects}")
            except Exception as e:
                print(f"❌ Error during YOLO detection: {e}")
                objects = []

            try:
                text = extract_text_from_frame(frame)
                print(f"📄 OCR result: {text}")
            except Exception as e:
                print(f"❌ Error during OCR: {e}")
                text = ""

            # Compose prompt for GPT
            prompt = (
                f"The camera sees the following objects: {', '.join(objects)}.\n"
                f"The visible text on screen is: \"{text}\".\n"
                "What is the user likely doing, and what suggestions can you give?"
            )

            print("🤖 Sending prompt to GPT...")
            try:
                response = get_ai_response([prompt])
                print(f"✅ GPT Response: {response}")
            except Exception as e:
                print(f"❌ GPT error: {e}")
                response = f"GPT Error: {str(e)}"

            # Send back response
            await websocket.send_json({
                "objects": objects,
                "text": text,
                "response": response
            })

    except WebSocketDisconnect:
        print("❌ Client disconnected")
