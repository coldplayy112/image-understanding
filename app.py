import os
import cv2
import numpy as np
import requests
import base64
from flask import Flask, request, jsonify, render_template

app = Flask(__name__)

# CONFIGURATION
# Using the provided key
OPENROUTER_API_KEY = "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"
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

def is_blurred(image_bytes, threshold=100):
    """Detects if an image is blurred using Laplacian variance."""
    try:
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if img is None:
            return None, "Corrupt or invalid image data"
        
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        score = cv2.Laplacian(gray, cv2.CV_64F).var()
        return score < threshold, score
    except Exception as e:
        return None, str(e)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/analyze', methods=['POST'])
def analyze():
    # 1. READ INPUT BYTES
    image_bytes = None
    
    if request.files.get('file'):
        image_bytes = request.files['file'].read()
    elif request.is_json:
        data = request.get_json(silent=True)
        if data and data.get('url'):
            try:
                # Explicitly unset proxies to prevent 404 interceptors
                resp = requests.get(data.get('url'), proxies={'http': None, 'https': None}, timeout=15)
                resp.raise_for_status()
                image_bytes = resp.content
            except Exception as e:
                return jsonify({"error": f"Failed to download image URL: {str(e)}"}), 400
    
    if not image_bytes:
        return jsonify({"error": "No image source found. Please upload a file or provide a URL."}), 400

    # 2. BLUR DETECTION
    blurred, score = is_blurred(image_bytes)
    if blurred is None:
        return jsonify({"error": f"Blur detection failed: {score}"}), 500
    
    if blurred:
        return jsonify({"result": "Blur"})

    # 3. AI DESCRIPTION (NOT BLURRED)
    try:
        # [V5] Aggressive resize to prevent payload/interceptor issues
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        max_dim = 640 # Even smaller for stability
        h, w = img.shape[:2]
        if max(h, w) > max_dim:
            scale = max_dim / max(h, w)
            img = cv2.resize(img, (int(w * scale), int(h * scale)))
            # Lower quality to keep payload tiny
            _, buffer = cv2.imencode('.jpg', img, [int(cv2.IMWRITE_JPEG_QUALITY), 70])
            image_bytes = buffer.tobytes()

        b64_img = base64.b64encode(image_bytes).decode('utf-8')
        
        # Using the absolute most stable free "router" ID
        model_id = "openrouter/free" 
        
        payload = {
            "model": model_id,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Describe this image concisely."},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64_img}"}}
                    ]
                }
            ]
        }

        # [V5] Use a fake referer to bypass potential localhost restrictions
        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://image-insight.local", 
            "X-Title": "ImageInsight"
        }
        
        print(f"DEBUG [V5]: Target: {OPENROUTER_URL} | Model: {model_id}", flush=True)
        
        response = requests.post(
            OPENROUTER_URL, 
            headers=headers, 
            json=payload, 
            proxies={'http': None, 'https': None}, 
            timeout=45
        )
        
        if not response.ok:
            print(f"DEBUG [V5]: Error {response.status_code}. Content: {response.text}", flush=True)
            return jsonify({"error": f"[V5] API Error {response.status_code}: {response.text}"}), response.status_code

        result = response.json()
        description = result['choices'][0]['message']['content'] if 'choices' in result else "No description available."
        
        return jsonify({"result": description})

    except Exception as e:
        print(f"DEBUG [V5]: Exception: {str(e)}", flush=True)
        return jsonify({"error": f"[V5] Analysis failed: {str(e)}"}), 500

if __name__ == '__main__':
    # Force no-debug for clean container logs
    app.run(host='0.0.0.0', port=5000, debug=False)
