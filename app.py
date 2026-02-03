import os
import cv2
import numpy as np
import requests
from flask import Flask, request, jsonify, render_template

app = Flask(__name__)

OPENROUTER_API_KEY = "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"
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

def is_blurred(image_bytes, threshold=100):
    """
    Detects if an image is blurred using the variance of the Laplacian.
    """
    try:
        # Convert bytes to numpy array
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if img is None:
            return None, "Invalid image"

        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        score = cv2.Laplacian(gray, cv2.CV_64F).var()
        
        return score < threshold, score
    except Exception as e:
        print(f"Error in blur detection: {e}")
        return None, str(e)

def get_image_description(image_url=None):
    """
    Uses OpenRouter (Gemini 2.0 Flash) to describe the image.
    Note: OpenRouter's Gemini 2.0 implementation typically requires a URL.
    Uploading raw bytes to OpenRouter usually involves a separate upload step or base64 encoding 
    depending on the specific provider support, but for 'google/gemini-2.0-flash-exp:free',
    providing a public URL is the most reliable method if we don't have a storage backend.
    
    However, the user request implies we might upload a file. 
    If the user uploads a file, we can't send a local path to OpenRouter.
    We would need to base64 encode it.
    """
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }

    content = []
    
    # If we had a real hosting, we'd use the URL. 
    # For local file uploads, we'll try base64 (if supported by the specific model route)
    # or just assume the simplified flow for now where we might rely on text description if passed URL.
    # But wait, the requirement says "accept an image URL as input" initially.
    # The UI requirement says "upload image feature". 
    # To support upload + OpenRouter without S3, we send Base64.
    
    # Correction: The prompt specifically said "The endpoint must accept an image URL as input."
    # AND "for the ui... it will have like a upload image feature".
    # So we need to support both or handle the upload by serving it temporarily?
    # Sending Base64 is the standard way for multimodal LLMs.
    
    pass # Implementation moved to the route for context handling

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/analyze', methods=['POST'])
def analyze():
    data = request.json
    image_url = None
    image_bytes = None

    # Handle Input
    if request.files.get('file'):
        file = request.files['file']
        image_bytes = file.read()
    elif data and data.get('url'):
        image_url = data.get('url')
        try:
            resp = requests.get(image_url)
            resp.raise_for_status()
            image_bytes = resp.content
        except Exception as e:
            return jsonify({"error": f"Failed to fetch URL: {str(e)}"}), 400
    else:
        return jsonify({"error": "No image provided. Send 'url' or 'file'."}), 400

    # 1. Blur Detection
    blurred, score = is_blurred(image_bytes)
    if blurred is None:
        return jsonify({"error": "Failed to process image for blur detection"}), 500
    
    if blurred:
        return jsonify({
            "result": "Blur",
            "details": f"Image is blurred (Score: {score:.2f})"
        })

    # 2. Image Description (Not Blurred)
    # Prepare payload for OpenRouter
    
    # For file uploads, we need to base64 encode
    import base64
    base64_image = base64.b64encode(image_bytes).decode('utf-8')
    
    payload = {
        "model": "google/gemini-2.0-flash-exp:free",
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "Describe this image in detail."
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_image}"
                        }
                    }
                ]
            }
        ]
    }

    try:
        response = requests.post(OPENROUTER_URL, headers={
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
            "HTTP-Referer": "http://localhost:5000", # Required by OpenRouter
            "X-Title": "ImageBlurApp" # Required by OpenRouter
        }, json=payload)
        
        response.raise_for_status()
        result_json = response.json()
        
        description = "No description generated."
        if 'choices' in result_json and len(result_json['choices']) > 0:
            description = result_json['choices'][0]['message']['content']
        
        return jsonify({
            "result": description
        })
        
    except Exception as e:
        print(f"OpenRouter Error: {e}")
        # Fallback details if API fails
        try:
            err_msg = response.json()
            print(f"API Response: {err_msg}")
        except:
            pass
        return jsonify({"error": f"Failed to generate description: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
