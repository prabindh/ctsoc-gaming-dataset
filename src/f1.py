import cv2
from deepface import DeepFace
from flask import Flask, request, jsonify
import threading
import time
import os
import numpy as np
import requests

if not os.path.exists('facial_captures'):
    os.makedirs('facial_captures')

app = Flask(__name__)
cap = cv2.VideoCapture(0) # Default webcam device index 0

capture_trigger     = threading.Event()
current_event_label = "MANUAL_TRIGGER"
current_sync_ts     = 0

EMOTION_STREAM_INTERVAL = 1.0
last_stream_time        = 0.0

font = cv2.FONT_HERSHEY_SIMPLEX

# --- GLOBALS FOR ASYNC AI THREAD ---
is_analyzing = False
face_detected = False
dominant = "NO_FACE"
stress_score = 0.0
region = None

def send_emotion_to_receiver(dom, stress):
    def _post():
        try:
            requests.post(
                "http://localhost:5000/log",
                json={"event": "FACIAL_DATA", "data": {"dominant": str(dom), "stress": float(stress), "timestamp_ms": int(time.time() * 1000)}},
                timeout=1.0
            )
        except Exception:
            pass
    threading.Thread(target=_post, daemon=True).start()

def send_capture_result(dom, stress, event_ts, image_file):
    def _post():
        try:
            requests.post(
                "http://localhost:5000/capture_result",
                json={"dominant": str(dom), "stress": float(stress), "timestamp_ms": int(event_ts), "image_file": str(image_file)},
                timeout=1.0
            )
        except Exception:
            pass
    threading.Thread(target=_post, daemon=True).start()

@app.route('/trigger_capture', methods=['POST'])
def trigger():
    global current_event_label, current_sync_ts
    data                = request.json
    current_event_label = data.get("event", "UNKNOWN")
    current_sync_ts     = data.get("timestamp", int(time.time() * 1000))
    capture_trigger.set()
    return jsonify({"status": "signal_received"}), 200

def run_deepface():
    global last_stream_time
    global is_analyzing, face_detected, dominant, stress_score, region
    
    print("Clinical AI Engine Started. Monitoring Circumplex Affect...")

    def analyze_frame_bg(frame_to_analyze):
        global is_analyzing, face_detected, dominant, stress_score, region
        try:
            results  = DeepFace.analyze(frame_to_analyze, actions=['emotion'], enforce_detection=True, detector_backend='ssd')
            
            if isinstance(results, list):
                results = results[0]
                
            temp_region = results['region']
            if temp_region['w'] == 0 or temp_region['h'] == 0:
                raise ValueError("DeepFace returned an empty face region.")
            
            emotions = results['emotion']
            temp_dominant = results['dominant_emotion']

            # Russell's Circumplex Model of Affect
            temp_arousal = (emotions['fear'] + emotions['angry'] + emotions['surprise']) - (emotions['sad'] + emotions['neutral'])
            temp_valence = (emotions['happy']) - (emotions['fear'] + emotions['angry'] + emotions['sad'] + emotions['disgust'])
            
            stress_x = max(0, -temp_valence) 
            stress_y = max(0, temp_arousal)
            
            stress_score = (stress_x + stress_y) / 2.0
            dominant = temp_dominant
            region = temp_region
            face_detected = True

            send_emotion_to_receiver(dominant, stress_score)

        except Exception:
            face_detected = False
            dominant = "NO_FACE"
            stress_score = 0.0
            region = None
        finally:
            is_analyzing = False

    while True:
        ret, frame = cap.read()
        if not ret:
            continue

        now = time.time()
        if not is_analyzing and (now - last_stream_time) >= EMOTION_STREAM_INTERVAL:
            last_stream_time = now
            is_analyzing = True
            threading.Thread(target=analyze_frame_bg, args=(frame.copy(),), daemon=True).start()

        if capture_trigger.is_set():
            capture_trigger.clear()
            img_name = f"facial_captures/event_{current_sync_ts}.jpg"
            cv2.imwrite(img_name, frame)
            send_capture_result(dominant, stress_score, current_sync_ts, img_name)

        time.sleep(0.03)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001)
