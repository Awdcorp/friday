import easyocr
import cv2

reader = easyocr.Reader(['en'], gpu=False)

def extract_text_from_frame(frame):
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    results = reader.readtext(gray)
    return " ".join([text for (_, text, _) in results])
