#!/usr/bin/env python3
"""Advisory AI with stop-only authority. Imports never open a camera or model client."""
import base64
import ipaddress
import os
import threading
import time
import uuid
from urllib.parse import urlparse

import requests
from flask import Flask, Response

try:
    from .vision_safety import Observation, VisionError, local_boot_id, parse_policy, require_fresh
except ImportError:
    from vision_safety import Observation, VisionError, local_boot_id, parse_policy, require_fresh

MOTOR_URL = os.environ.get('MOTOR_URL', 'http://127.0.0.1:8088')
# MJPEG remains a display interface. Policy accepts only bounded snapshots with provenance.
FRAME_URL = os.environ.get('FRAME_URL', 'http://127.0.0.1:8090/snapshot.jpg')
MODEL = os.environ.get('AI_MODEL', 'gpt-4o-mini')
PERIOD = float(os.environ.get('AI_PERIOD', '2.0'))
MAX_AGE = 2.0
MAX_FRAME_BYTES = 1024 * 1024
app = Flask(__name__)
latest_overlay = None
_overlay_lock = threading.Lock()
_ai_session = str(uuid.uuid4())


def get_frame_from_stream(url=FRAME_URL, http=requests, clock=time.monotonic,
                          boot_id=None, max_age=MAX_AGE, total_timeout=2.0):
    """Compatibility name; fetch one JPEG, never accumulate an MJPEG stream.

    Only same-host literal-loopback HTTP is supported: monotonic timestamps are
    meaningful only with the matching Linux boot identity. Each one-byte read
    checks a total deadline; socket idle timeout is bounded separately.
    """
    parsed = urlparse(url)
    try:
        same_host = parsed.scheme == 'http' and ipaddress.ip_address(parsed.hostname).is_loopback
    except (ValueError, TypeError):
        same_host = False
    if not same_host:
        raise VisionError('FRAME_URL must use a literal loopback IP on the same host')
    started = clock()
    response = http.get(url, stream=True, timeout=(0.5, 0.5), allow_redirects=False)
    try:
        response.raise_for_status()
        if response.status_code != 200:
            raise VisionError('snapshot HTTP status is not 200')
        if response.headers.get('Content-Type', '').split(';')[0] != 'image/jpeg':
            raise VisionError('snapshot must be image/jpeg')
        try:
            observation = Observation(
                b'', float(response.headers['X-Capture-Monotonic']),
                response.headers['X-Capture-Boot-ID'], response.headers['X-Camera-Session'],
                int(response.headers['X-Frame-Sequence']))
            length = int(response.headers['Content-Length'])
        except (KeyError, ValueError) as exc:
            raise VisionError('missing or invalid snapshot provenance/length') from exc
        expected_boot = local_boot_id() if boot_id is None else boot_id
        require_fresh(observation, clock(), expected_boot, max_age)
        if not 4 <= length <= MAX_FRAME_BYTES:
            raise VisionError('snapshot size outside limit')
        body = bytearray()
        for chunk in response.iter_content(chunk_size=1):
            if clock() - started > total_timeout:
                raise VisionError('snapshot total deadline exceeded')
            body.extend(chunk)
            if len(body) > length or len(body) > MAX_FRAME_BYTES:
                raise VisionError('snapshot exceeds declared length')
        if len(body) != length or not body.startswith(b'\xff\xd8') or not body.endswith(b'\xff\xd9'):
            raise VisionError('incomplete JPEG snapshot')
        observation = Observation(bytes(body), observation.captured_at, observation.boot_id,
                                  observation.camera_session, observation.sequence)
        return require_fresh(observation, clock(), expected_boot, max_age)
    finally:
        response.close()


def call_openai_on_frame(observation, client=None):
    """Paid call only when explicitly invoked; tests inject a fake model client."""
    owned = client is None
    if owned:
        from openai import OpenAI
        client = OpenAI(timeout=5.0, max_retries=0)
    try:
        response = client.chat.completions.create(
            model=MODEL, temperature=0.2, response_format={'type': 'json_object'},
            messages=[{'role': 'user', 'content': [
                {'type': 'text', 'text': (
                    'Describe this robot camera image as JSON only: '
                    '{"person":{"present":true,"distance":"near"},'
                    '"stop_sign":{"present":false}}. Both present fields must be '
                    'booleans. If person is present, distance must be near, mid, or far. '
                    'Report observations only; never issue movement commands.')},
                {'type': 'image_url', 'image_url': {'url': 'data:image/jpeg;base64,' +
                    base64.b64encode(observation.jpeg).decode('ascii')}}]}])
        return response.choices[0].message.content
    finally:
        if owned:
            client.close()


def apply_policy(policy, http=requests):
    """Only emit stop. No AI result can arm, reset, change speed, or move."""
    if policy.get('action') != 'none' or policy.get('valid') is not True:
        response = http.post(f'{MOTOR_URL}/cmd', json={
            'c': 'stop', 'source': 'ai', 'session': _ai_session}, timeout=(0.5, 0.5))
        response.raise_for_status()
        if response.json().get('ok') is not True:
            raise VisionError('motor server rejected AI stop')


def policy_step(fetch_frame=get_frame_from_stream, model=call_openai_on_frame,
                apply=apply_policy, clock=time.monotonic, boot_id=None):
    """One injectable cycle; camera/model errors fail closed to a latched stop."""
    observation = None
    try:
        observation = fetch_frame()
        expected_boot = local_boot_id() if boot_id is None else boot_id
        require_fresh(observation, clock(), expected_boot, MAX_AGE)
        text = model(observation)
        # The model's arrival time does not renew the capture-time deadline.
        require_fresh(observation, clock(), expected_boot, MAX_AGE)
        policy = parse_policy(text)
    except Exception as exc:
        policy = {'action': 'stop', 'valid': False, 'reason': str(exc),
                  'recommendation': 'unavailable/stale vision; stop and reassess'}
    apply(policy)  # Failure is surfaced; never claim an undelivered stop succeeded.
    return observation, policy


def update_overlay(observation, policy):
    global latest_overlay
    import cv2
    import numpy as np
    frame = (cv2.imdecode(np.frombuffer(observation.jpeg, dtype=np.uint8), cv2.IMREAD_COLOR)
             if observation else None)
    if frame is None:
        frame = np.zeros((240, 640, 3), dtype=np.uint8)
    label = f"AI advisory: {policy['action']} ({'valid' if policy['valid'] else 'invalid/stale'})"
    cv2.putText(frame, label, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)
    cv2.putText(frame, policy['recommendation'][:80], (10, 55),
                cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 255), 1)
    ok, jpeg = cv2.imencode('.jpg', frame)
    if ok:
        with _overlay_lock:
            latest_overlay = jpeg.tobytes()


def policy_loop(stop_event=None):
    stop_event = stop_event or threading.Event()
    while not stop_event.is_set():
        try:
            observation, policy = policy_step()
            update_overlay(observation, policy)
            print('[AI ADVISORY]', policy, flush=True)
        except Exception as exc:
            print('[ERROR] policy or stop delivery failed:', exc, flush=True)
            try:
                update_overlay(None, {'action': 'stop', 'valid': False,
                    'recommendation': 'stop NOT confirmed; inspect motor service'})
            except Exception as overlay_error:
                print('[ERROR] overlay update failed:', overlay_error, flush=True)
        stop_event.wait(max(0.1, PERIOD))


@app.route('/overlay.mjpg')
def overlay_stream():
    def generate():
        while True:
            with _overlay_lock:
                data = latest_overlay
            if data is not None:
                yield b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + data + b'\r\n'
            time.sleep(0.1)
    return Response(generate(), mimetype='multipart/x-mixed-replace; boundary=frame')


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--enable-paid-model', action='store_true',
                        help='explicitly enable camera requests and paid model calls')
    args = parser.parse_args()
    if not args.enable_paid_model:
        parser.error('running AI requires --enable-paid-model; import/tests never call the model')
    worker_stop = threading.Event()
    worker = threading.Thread(target=policy_loop, args=(worker_stop,), daemon=True)
    worker.start()
    try:
        app.run(host=os.environ.get('BIND_HOST', '127.0.0.1'),
                port=int(os.environ.get('POLICY_PORT', '8091')), use_reloader=False)
    finally:
        worker_stop.set()
        try:
            apply_policy({'action': 'stop', 'valid': False})
        except Exception as exc:
            print('[ERROR] shutdown stop delivery failed:', exc)
