#!/usr/bin/env python3
import os
import threading
from flask import Flask, Response, request, jsonify, render_template_string
import cv2
import numpy as np

MOTOR_URL = os.environ.get("MOTOR_URL", "http://127.0.0.1:8088")
CAM_W = int(os.environ.get("CAM_W", "320"))
CAM_H = int(os.environ.get("CAM_H", "240"))
CAM_FPS = int(os.environ.get("CAM_FPS", "15"))

app = Flask(__name__)

cap_lock = threading.Lock()
cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, CAM_W)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CAM_H)
cap.set(cv2.CAP_PROP_FPS, CAM_FPS)

if not cap.isOpened():
    print("[ERR] Could not open camera /dev/video0")

HTML_PAGE = '''<!doctype html>
<html>
<head>
  <title>Robot Cam + Drive</title>
  <style>
    body { font-family: sans-serif; background:#111; color:#eee; text-align:center; }
    #video { border:2px solid #555; margin-top:10px; }
    button { margin:5px; padding:10px 15px; font-size:16px; }
  </style>
</head>
<body>
  <h1>Robot Camera + Drive</h1>
  <img id="video" src="/stream.mjpg" width="640" height="480" />
  <div>
    <button onclick="send('fwd')">FWD</button>
    <button onclick="send('back')">BACK</button>
    <button onclick="send('left')">LEFT</button>
    <button onclick="send('right')">RIGHT</button>
    <button onclick="send('stop')">STOP</button>
  </div>
  <div>
    Speed: <input type="range" min="0" max="100" value="50" id="speed" oninput="setSpeed(this.value)">
    <span id="sval">50</span>
  </div>
<script>
const motorUrl = "{{ motor_url }}";
function send(cmd) {
  fetch(motorUrl + "/cmd?c=" + cmd).catch(console.error);
}
function setSpeed(v) {
  document.getElementById("sval").innerText = v;
  fetch(motorUrl + "/cmd?c=speed&v=" + v).catch(console.error);
}
</script>
</body>
</html>
'''

@app.route("/")
def index():
    return render_template_string(HTML_PAGE, motor_url=MOTOR_URL)

def mjpeg_generator():
    global cap
    while True:
        with cap_lock:
            ret, frame = cap.read()
        if not ret:
            with cap_lock:
                cap.release()
                cap = cv2.VideoCapture(0)
                cap.set(cv2.CAP_PROP_FRAME_WIDTH, CAM_W)
                cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CAM_H)
                cap.set(cv2.CAP_PROP_FPS, CAM_FPS)
            continue

        ret, jpg = cv2.imencode(".jpg", frame)
        if not ret:
            continue
        data = jpg.tobytes()
        yield (b"--frame\r\n"
               b"Content-Type: image/jpeg\r\n\r\n" +
               data + b"\r\n")

@app.route("/stream.mjpg")
def stream():
    return Response(mjpeg_generator(),
                    mimetype="multipart/x-mixed-replace; boundary=frame")

@app.route("/status")
def status():
    return jsonify({"ok": True})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8090"))
    print(f"[INFO] Motor server: {MOTOR_URL}")
    print(f"[INFO] Camera: /dev/video0 at {CAM_W}x{CAM_H}@{CAM_FPS}")
    print(f"[INFO] Open your browser to: http://<Pi-IP>:{port}")
    app.run(host="0.0.0.0", port=port)
