import easyocr
import cv2

# Load OCR reader once
reader = easyocr.Reader(['en'], gpu=False)

def extract_text_from_frame(frame):
    """
    Extracts visible text from a frame using EasyOCR.
    Returns the text as a single string.
    """
    # Convert to grayscale
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # Detect text
    results = reader.readtext(gray)

    # Join all detected text into one string
    text_lines = [text for (_, text, _) in results]
    return " ".join(text_lines)
