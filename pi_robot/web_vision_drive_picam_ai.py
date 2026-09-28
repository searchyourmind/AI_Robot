#!/usr/bin/env python3
"""Camera display, provenance-bearing snapshots, and manual same-origin controls."""
import json
import os
import threading
import time
import uuid

import requests
from flask import Flask, Response, jsonify, render_template_string, request

try:
    from .vision_safety import Observation, VisionError, local_boot_id, require_fresh
except ImportError:
    from vision_safety import Observation, VisionError, local_boot_id, require_fresh

MOTOR_URL = os.environ.get('MOTOR_URL', 'http://127.0.0.1:8088')
CAM_W = int(os.environ.get('CAM_W', '320'))
CAM_H = int(os.environ.get('CAM_H', '240'))
CAM_FPS = int(os.environ.get('CAM_FPS', '15'))


class CameraSource:
    """One capture worker publishes only its latest image; HTTP never blocks on read.

    Timestamp precedes the capture API call, so blocked capture/encoding consumes
    the age budget. Sensor/driver buffering still needs physical characterization.
    """
    def __init__(self, cv=None, clock=time.monotonic, boot_id=None):
        self.cv = cv
        self.clock = clock
        self.boot_id = local_boot_id() if boot_id is None else boot_id
        self.session = str(uuid.uuid4())
        self.lock = threading.Lock()
        self.latest = None
        self.cap = None
        self.sequence = 0
        self.stop_event = threading.Event()
        self.worker = None

    def start(self):
        if self.worker is not None:
            return
        if self.cv is None:
            import cv2
            self.cv = cv2
        self.worker = threading.Thread(target=self._run, daemon=True)
        self.worker.start()

    def _open(self):
        self.cap = self.cv.VideoCapture(0)
        self.cap.set(self.cv.CAP_PROP_FRAME_WIDTH, CAM_W)
        self.cap.set(self.cv.CAP_PROP_FRAME_HEIGHT, CAM_H)
        self.cap.set(self.cv.CAP_PROP_FPS, CAM_FPS)
        # This request is best-effort; it does not establish sensor capture age.
        self.cap.set(self.cv.CAP_PROP_BUFFERSIZE, 1)
        if not self.cap.isOpened():
            raise VisionError('camera did not open')

    def capture_once(self):
        if self.cap is None:
            self._open()
        captured_at = self.clock()  # Must precede the potentially blocking read.
        success, frame = self.cap.read()
        if not success:
            raise VisionError('camera read failed')
        success, encoded = self.cv.imencode('.jpg', frame)
        if not success:
            raise VisionError('camera JPEG encoding failed')
        self.sequence += 1
        item = Observation(encoded.tobytes(), captured_at, self.boot_id,
                           self.session, self.sequence)
        with self.lock:
            self.latest = item
        return item

    def _run(self):
        while not self.stop_event.is_set():
            try:
                self.capture_once()
            except Exception as exc:
                with self.lock:
                    self.latest = None
                if self.cap is not None:
                    self.cap.release()
                    self.cap = None
                self.session = str(uuid.uuid4())
                self.sequence = 0
                print('[WARN] camera unavailable:', exc, flush=True)
                self.stop_event.wait(0.2)

    def snapshot(self):
        with self.lock:
            return self.latest

    def close(self):
        self.stop_event.set()
        if self.worker is not None:
            self.worker.join(timeout=0.5)
        # Do not release a capture concurrently with a blocked native read.
        if self.cap is not None and (self.worker is None or not self.worker.is_alive()):
            self.cap.release()
            self.cap = None


HTML_PAGE = '''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><title>Robot Cam + Drive</title>
<style>body{font-family:sans-serif;background:#111;color:#eee;text-align:center}img{max-width:95%;border:2px solid #555}button{margin:5px;padding:10px 15px;font-size:16px}#status{white-space:pre-wrap}</style>
</head><body><h1>Robot Camera + Drive</h1>
<img src="/stream.mjpg" width="640" height="480" alt="Live camera">
<p>Manual commands expire after 0.25 s. Reset and arm explicitly after any latched stop/expiry.</p>
<div><button onclick="control('reset')">RESET LATCH</button><button onclick="control('arm')">ARM</button>
<button onclick="stopNow('Operator stop')">STOP / DISARM</button></div>
<div><button onclick="control('fwd')">FWD</button><button onclick="control('back')">BACK</button>
<button onclick="control('left')">LEFT</button><button onclick="control('right')">RIGHT</button></div>
<p>Speed: <input type="range" min="0" max="100" value="50" id="speed" oninput="document.getElementById('sval').textContent=this.value"><span id="sval">50</span></p>
<p id="status" role="status">Disarmed. Observe the robot before arming.</p>
<details><summary>AI advisory overlay (stop-only authority)</summary><img src="/overlay.mjpg" alt="AI overlay; start the policy service separately"></details>
<script>
const session = (globalThis.crypto && crypto.randomUUID) ? crypto.randomUUID() : 'browser-' + Date.now() + '-' + Math.random().toString(36).slice(2);
let lease = null, epoch = 0;
const statusEl = document.getElementById('status');
async function post(payload, keepalive=false) {
  const response = await fetch('/motor/cmd', {method:'POST', headers:{'Content-Type':'application/json'},body:JSON.stringify(payload),keepalive});
  const result = await response.json();
  if (!response.ok || !result.ok) throw new Error(result.error || result.reason || 'Motor request failed');
  return result;
}
function payload(c) {return {c,source:'browser',session};}
async function stopNow(reason) {
  epoch++; lease = null; statusEl.textContent = reason + '; stop requested';
  try {const result = await post(payload('stop'), true); statusEl.textContent = JSON.stringify(result);}
  catch (error) {statusEl.textContent = 'STOP NOT CONFIRMED: ' + error.message;}
}
async function control(c) {
  if (c === 'reset') {epoch++; lease = null;}
  const version = epoch, data = payload(c);
  if (!['reset','arm'].includes(c)) {
    if (!lease) {statusEl.textContent='Explicit RESET (if latched) then ARM required'; return;}
    Object.assign(data,{lease,speed:Number(document.getElementById('speed').value),duration:0.25});
  }
  try {
    const result = await post(data);
    if (version !== epoch) return;
    if (c === 'arm') lease = result.lease;
    statusEl.textContent=JSON.stringify(result);
  } catch (error) {await stopNow('Command error: ' + error.message);}
}
window.addEventListener('pagehide', () => {lease=null; epoch++; fetch('/motor/cmd',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload('stop')),keepalive:true}).catch(()=>{});});
document.addEventListener('visibilitychange', () => {if (document.hidden) stopNow('Page hidden');});
// Status never refreshes a motion deadline, resets, or arms.
setInterval(async () => {try {const response=await fetch('/motor/status'); const result=await response.json(); if(!response.ok || !result.ok) throw new Error(result.error || 'status unavailable'); if(!result.armed || result.latched){lease=null; statusEl.textContent=JSON.stringify(result);}} catch(error){if(lease) await stopNow('Connection lost'); else statusEl.textContent=error.message;}},1000);
</script></body></html>'''


def create_app(camera=None, http=requests, clock=time.monotonic):
    application = Flask(__name__)
    application.config['CAMERA'] = camera
    application.config['MAX_CONTENT_LENGTH'] = 4096

    @application.route('/')
    def index():
        return render_template_string(HTML_PAGE)

    def fresh_snapshot():
        provider = application.config['CAMERA']
        item = provider.snapshot() if provider is not None else None
        if item is None:
            raise VisionError('camera unavailable')
        return require_fresh(item, clock(), provider.boot_id, 2.0)

    @application.route('/snapshot.jpg')
    def snapshot():
        try:
            item = fresh_snapshot()
        except VisionError as exc:
            return jsonify(ok=False, error=str(exc)), 503
        return Response(item.jpeg, mimetype='image/jpeg', headers={
            'Cache-Control': 'no-store', 'X-Capture-Monotonic': str(item.captured_at),
            'X-Capture-Boot-ID': item.boot_id, 'X-Camera-Session': item.camera_session,
            'X-Frame-Sequence': str(item.sequence)})

    @application.route('/stream.mjpg')
    def stream():
        def generate():
            last_identity = None
            while True:
                provider = application.config['CAMERA']
                item = provider.snapshot() if provider is not None else None
                if item is not None and (item.camera_session, item.sequence) != last_identity:
                    last_identity = (item.camera_session, item.sequence)
                    yield b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + item.jpeg + b'\r\n'
                time.sleep(1 / max(1, CAM_FPS))
        return Response(generate(), mimetype='multipart/x-mixed-replace; boundary=frame',
                        headers={'Cache-Control': 'no-store'})

    @application.route('/status')
    def status():
        try:
            item = fresh_snapshot()
            return jsonify(ok=True, camera_ready=True, sequence=item.sequence)
        except VisionError as exc:
            return jsonify(ok=False, camera_ready=False, error=str(exc)), 503

    @application.errorhandler(413)
    def request_too_large(_error):
        return jsonify(ok=False, error='request exceeds 4096 bytes'), 413

    @application.route('/motor/cmd', methods=['POST'])
    def motor_command():
        def unique_fields(pairs):
            result = {}
            for key, value in pairs:
                if key in result:
                    raise ValueError('duplicate command field')
                result[key] = value
            return result
        try:
            if not request.is_json:
                raise ValueError('JSON object required')
            body = json.loads(request.get_data(as_text=True), object_pairs_hook=unique_fields)
            if not isinstance(body, dict):
                raise ValueError('JSON object required')
        except (ValueError, UnicodeError) as exc:
            return jsonify(ok=False, error=str(exc)), 400
        # A browser proxy may not impersonate an AI or another client class.
        body['source'] = 'browser'
        try:
            response = http.post(f'{MOTOR_URL}/cmd', json=body, timeout=(0.5, 0.5))
            return jsonify(response.json()), response.status_code
        except (requests.RequestException, ValueError) as exc:
            return jsonify(ok=False, error='motor connection failed: ' + str(exc)), 502

    @application.route('/motor/status')
    def motor_status():
        try:
            response = http.get(f'{MOTOR_URL}/status', timeout=(0.5, 0.5))
            return jsonify(response.json()), response.status_code
        except (requests.RequestException, ValueError) as exc:
            return jsonify(ok=False, error='motor connection failed: ' + str(exc)), 502

    @application.route('/overlay.mjpg')
    def overlay_proxy():
        # Keep browser access same-origin; bounded read timeout ends disconnected feeds.
        try:
            remote = http.get(os.environ.get('OVERLAY_URL', 'http://127.0.0.1:8091/overlay.mjpg'),
                              stream=True, timeout=(0.5, 1.0))
            remote.raise_for_status()
        except requests.RequestException as exc:
            return jsonify(ok=False, error='overlay unavailable: ' + str(exc)), 503
        def generate():
            try:
                for chunk in remote.iter_content(chunk_size=4096):
                    yield chunk
            finally:
                remote.close()
        return Response(generate(), mimetype='multipart/x-mixed-replace; boundary=frame',
                        headers={'Cache-Control': 'no-store'})

    return application


app = create_app()  # Imports do not initialize camera hardware.

if __name__ == '__main__':
    source = CameraSource()
    source.start()
    app.config['CAMERA'] = source
    try:
        app.run(host=os.environ.get('BIND_HOST', '127.0.0.1'),
                port=int(os.environ.get('PORT', '8090')), use_reloader=False, threaded=True)
    finally:
        source.close()
