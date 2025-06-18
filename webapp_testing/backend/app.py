from flask import Flask, request, jsonify
from detect import detect_objects_from_image
from ocr import extract_text_from_image
from ai_chat import get_ai_response

app = Flask(__name__)

@app.route("/api/friday", methods=["POST"])
def analyze_frame():
    if 'image' not in request.files:
        return jsonify({"error": "Image is required"}), 400

    image_file = request.files['image']
    image_bytes = image_file.read()

    # Run detection
    objects = detect_objects_from_image(image_bytes)
    text = extract_text_from_image(image_bytes)

    # Build prompt
    prompt = (
        f"The image contains objects: {', '.join(objects)}.\n"
        f"The visible text says: \"{text}\".\n"
        "What is the user likely doing and how can I help?"
    )

    # Get GPT response
    response = get_ai_response([prompt])

    return jsonify({
        "objects": objects,
        "text": text,
        "response": response
    })

if __name__ == "__main__":
    app.run(debug=True)
