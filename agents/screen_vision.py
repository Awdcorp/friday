import pytesseract
from PIL import ImageGrab, Image
import cv2
import numpy as np
import difflib

# === Capture full screen ===
def capture_screen(region=None) -> Image:
    """
    Capture a screenshot of the full screen or a specific region.
    region: (left, top, right, bottom) if only a portion is needed.
    """
    screenshot = ImageGrab.grab(bbox=region)
    return screenshot

# === Run OCR to extract text regions ===
def extract_text_regions(image: Image):
    """
    Run OCR and return list of text regions with positions and confidence.
    Each item: {text, bbox: (x, y, w, h), confidence}
    """
    image_cv = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
    data = pytesseract.image_to_data(image_cv, output_type=pytesseract.Output.DICT)

    results = []
    for i in range(len(data['text'])):
        try:
            conf = float(data['conf'][i])
            if conf > 60.0 and data['text'][i].strip() != '':
                x, y, w, h = data['left'][i], data['top'][i], data['width'][i], data['height'][i]
                results.append({
                    'text': data['text'][i],
                    'bbox': (x, y, w, h),
                    'confidence': conf
                })
        except ValueError:
            continue
    return results

# === Find best matching text and return its position ===
def find_text_position(text_query: str, regions):
    """
    Fuzzy match the target text with OCR results.
    Return center (x, y) coordinates of the matched region.
    """
    best_match = None
    best_score = 0

    for region in regions:
        score = difflib.SequenceMatcher(None, text_query.lower(), region['text'].lower()).ratio()
        if score > best_score:
            best_score = score
            best_match = region

    if best_match and best_score > 0.6:
        x, y, w, h = best_match['bbox']
        return (x + w // 2, y + h // 2)
    return None

# === High-level function ===
def locate_text_on_screen(text_query: str):
    """
    Capture screen, extract text, and return position of text_query.
    """
    image = capture_screen()
    regions = extract_text_regions(image)
    return find_text_position(text_query, regions)

# === Debug version: draw box and return full info ===
def locate_text_on_screen_debug(text_query: str):
    """
    Same as locate_text_on_screen but draws box and returns match info.
    """
    image = capture_screen()
    regions = extract_text_regions(image)

    best_match = None
    best_score = 0
    for region in regions:
        score = difflib.SequenceMatcher(None, text_query.lower(), region['text'].lower()).ratio()
        if score > best_score:
            best_score = score
            best_match = region

    if best_match and best_score > 0.6:
        x, y, w, h = best_match['bbox']
        cv2_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
        cv2.rectangle(cv2_image, (x, y), (x + w, y + h), (0, 255, 0), 2)
        cv2.putText(cv2_image, best_match['text'], (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
        cv2.imshow("Matched Region", cv2_image)
        cv2.waitKey(1000)
        cv2.destroyAllWindows()
        return {
            'text': best_match['text'],
            'confidence': best_match['confidence'],
            'position': (x + w // 2, y + h // 2)
        }
    return None

# Example debug test
if __name__ == '__main__':
    query = input("Enter text to locate: ")
    result = locate_text_on_screen_debug(query)
    if result:
        print(f"✅ Found '{result['text']}' at {result['position']} (conf: {result['confidence']:.2f})")
    else:
        print("❌ No good match found")
