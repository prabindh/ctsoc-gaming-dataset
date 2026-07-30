import csv
import time
import json
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS

app  = Flask(__name__)
CORS(app)

# Configuration placeholders (Replace with specific session details)
CSV_FILE = "subject_session.csv"
MY_ID    = "PLAYER_ID"

WRITE_BIOMETRIC_UPDATES = False

# Latest biometric snapshot
latest_bio = {
    "bpm"    : 0,
    "rr_ms"  : 0,
    "status" : "CALIBRATING"
}

# Latest continuous emotion
latest_emotion = {
    "dominant"     : "",
    "stress_score" : 0.0
}

# Triggered emotion
triggered_emotion = {
    "dominant"     : "",
    "stress_score" : 0.0,
    "timestamp_ms" : 0
}

# Anti-spam trackers
last_logged_event = ""
last_logged_time = 0

# CSV Initialization
with open(CSV_FILE, 'w', newline='') as f:
    csv.writer(f).writerow([
        "timestamp_ms",
        "event",
        "player_name",
        "victim",
        "weapon",
        "bpm",
        "rr_ms",
        "bio_status",
        "dominant_emotion",
        "stress_score",
        "composite_stress",
        "image_file"
    ])


def compute_composite_stress(bpm_status, stress_score, event):
    score = 0.0
    hr_map = {
        "INTENSE_SPIKE" : 40, "ELEVATED" : 25, "NORMAL" : 10, "RECOVERY" : 5, "CALIBRATING" : 0
    }
    score += hr_map.get(bpm_status, 0)
    score += min(stress_score * 0.4, 40)

    event_map = {
        "DEATH" : 20, "SPIKE_PLANTED" : 15, "SPIKE_DEFUSED" : 15, "KILL" : 10, "ROUND_START" : 5, "COMBAT_EVENT" : 8
    }
    score += event_map.get(event, 0)
    return round(min(score, 100), 2)


def trigger_face_capture(event_type, master_ts):
    try:
        requests.post(
            "http://localhost:5001/trigger_capture",
            json={"event": event_type, "timestamp": master_ts},
            timeout=0.05
        )
    except Exception:
        pass


def get_best_emotion(event_ts):
    if (triggered_emotion["timestamp_ms"] > 0 and
            abs(triggered_emotion["timestamp_ms"] - event_ts) < 2000):
        return triggered_emotion["dominant"], triggered_emotion["stress_score"]
    return latest_emotion["dominant"], latest_emotion["stress_score"]


def write_row(ts, event, player="", victim="", weapon="", image_file=""):
    dominant, stress = get_best_emotion(ts)
    composite = compute_composite_stress(latest_bio["status"], stress, event)

    with open(CSV_FILE, 'a', newline='') as f:
        csv.writer(f).writerow([
            ts, event, player, victim, weapon,
            latest_bio["bpm"],
            latest_bio["rr_ms"],
            latest_bio["status"],
            dominant,
            stress,
            composite,
            image_file
        ])

@app.route('/log', methods=['POST'])
def log_event():
    global latest_bio, latest_emotion, triggered_emotion, last_logged_event, last_logged_time
    data = request.json
    event_type = data.get("event")
    event_data = data.get("data", {})

    if event_type == "BIOMETRIC_DATA":
        latest_bio["bpm"] = event_data.get("bpm", 0)
        latest_bio["rr_ms"] = event_data.get("rr_ms", 0)
        latest_bio["status"] = event_data.get("status", "CALIBRATING")
        return jsonify({"status": "biometrics_updated"}), 200

    elif event_type == "FACIAL_DATA":
        latest_emotion["dominant"] = event_data.get("dominant", "NO_FACE")
        latest_emotion["stress_score"] = event_data.get("stress", 0.0)
        return jsonify({"status": "facial_updated"}), 200

    elif event_type == "GAME_EVENT":
        ts = event_data.get("timestamp_ms", int(time.time() * 1000))
        evt = event_data.get("event_name", "GAME_EVENT")
        player = event_data.get("player", MY_ID)
        victim = event_data.get("victim", "")
        weapon = event_data.get("weapon", "")

        now = time.time()
        if evt == last_logged_event and (now - last_logged_time) < 1.0:
            return jsonify({"status": "duplicate_skipped"}), 200

        last_logged_event = evt
        last_logged_time = now

        trigger_face_capture(evt, ts)
        write_row(ts, evt, player, victim, weapon)
        return jsonify({"status": "game_event_logged"}), 200

    return jsonify({"status": "ignored"}), 400

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
