#!/usr/bin/env python3
import os
import time
import base64
import requests
import cv2
import numpy as np
from flask import Flask, Response

from openai import OpenAI
import httpx

client = OpenAI(http_client=httpx.Client(timeout=30.0))

MOTOR_URL = os.environ.get("MOTOR_URL", "http://127.0.0.1:8088")
STREAM_URL = os.environ.get("STREAM_URL", "http://127.0.0.1:8090/stream.mjpg")
MODEL = os.environ.get("AI_MODEL", "gpt-4o-mini")
PERIOD = float(os.environ.get("AI_PERIOD", "2.0"))

app = Flask(__name__)
latest_overlay = None

def get_frame_from_stream():
    """Grab one frame from MJPEG stream."""
    resp = requests.get(STREAM_URL, stream=True, timeout=5)
    bytes_buff = b""
    try:
        for chunk in resp.iter_content(chunk_size=1024):
            bytes_buff += chunk
            a = bytes_buff.find(b'\xff\xd8')
            b = bytes_buff.find(b'\xff\xd9')
            if a != -1 and b != -1:
                jpg = bytes_buff[a:b+2]
                bytes_buff = bytes_buff[b+2:]
                img = cv2.imdecode(np.frombuffer(jpg, dtype=np.uint8), cv2.IMREAD_COLOR)
                return img
    finally:
        resp.close()
    return None

def call_openai_on_frame(frame_bgr):
    _, jpg = cv2.imencode(".jpg", frame_bgr)
    b64 = base64.b64encode(jpg.tobytes()).decode("ascii")

    prompt = (
        "You are onboard a small robot. Look at this image.\n"
        "Return a short JSON describing whether you see:\n"
        "- a person directly ahead, and roughly how far (near / mid / far)\n"
        "- a red stop sign\n\n"
        "Example:\n"
        "{\"person\": {\"present\": true, \"distance\": \"near\"}, \"stop_sign\": {\"present\": false}}"
    )

    resp = client.chat.completions.create(
        model=MODEL,
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{b64}"
                        },
                    },
                ],
            }
        ],
        temperature=0.2,
    )
    text = resp.choices[0].message.content
    return text

def parse_policy(text):
    text_low = text.lower()
    policy = {"action": "none"}
    if "stop sign" in text_low or "stop_sign" in text_low:
        policy["action"] = "stop"
    elif "person" in text_low:
        if "near" in text_low:
            policy["action"] = "slow"
        elif "mid" in text_low:
            policy["action"] = "slow"
        else:
            policy["action"] = "go"
    return policy

def apply_policy(policy):
    try:
        if policy["action"] == "stop":
            requests.get(f"{MOTOR_URL}/cmd", params={"c": "stop"}, timeout=2)
        elif policy["action"] == "slow":
            requests.get(f"{MOTOR_URL}/cmd", params={"c": "speed", "v": 30}, timeout=2)
            requests.get(f"{MOTOR_URL}/cmd", params={"c": "fwd"}, timeout=2)
        elif policy["action"] == "go":
            requests.get(f"{MOTOR_URL}/cmd", params={"c": "speed", "v": 70}, timeout=2)
            requests.get(f"{MOTOR_URL}/cmd", params={"c": "fwd"}, timeout=2)
    except Exception as e:
        print("[WARN] motor apply error:", e)

def policy_loop():
    global latest_overlay
    print("[INFO] Policy loop started.")
    while True:
        try:
            frame = get_frame_from_stream()
            if frame is None:
                time.sleep(PERIOD)
                continue

            latest_overlay = frame.copy()

            text = call_openai_on_frame(frame)
            print("[AI RAW]", text)
            policy = parse_policy(text)
            print("[POLICY]", policy)
            apply_policy(policy)

            cv2.putText(
                latest_overlay,
                f"action: {policy['action']}",
                (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (0, 255, 0),
                2,
            )
        except Exception as e:
            print("[WARN] policy error:", e)
        time.sleep(PERIOD)

@app.route("/overlay.mjpg")
def overlay_stream():
    def gen():
        global latest_overlay
        while True:
            if latest_overlay is None:
                time.sleep(0.1)
                continue
            _, jpg = cv2.imencode(".jpg", latest_overlay)
            data = jpg.tobytes()
            yield (b"--frame\r\n"
                   b"Content-Type: image/jpeg\r\n\r\n" + data + b"\r\n")
    return Response(gen(), mimetype="multipart/x-mixed-replace; boundary=frame")

if __name__ == "__main__":
    import threading
    t = threading.Thread(target=policy_loop, daemon=True)
    t.start()

    port = int(os.environ.get("POLICY_PORT", "8091"))
    print(f"[INFO] Motor={MOTOR_URL}  Vision={STREAM_URL}  Overlay=http://<Pi-IP>:{port}/overlay.mjpg")
    app.run(host="0.0.0.0", port=port)
