"""Exercise real Flask routes with in-memory HTTP and camera/model doubles."""
from urllib.parse import urlparse

import requests
import pytest

from pi_robot.motor_control import MotorController
from pi_robot import web_motor, web_vision_drive_picam_ai as camera_web
from pi_robot import vision_policy_daemon as vision
from pi_robot.vision_safety import Observation


class Clock:
    now = 100.0

    def __call__(self):
        return self.now


class Response:
    def __init__(self, response):
        self.response = response
        self.status_code = response.status_code
        self.headers = response.headers
        self.closed = False

    def json(self):
        return self.response.get_json()

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(str(self.status_code))

    def iter_content(self, chunk_size):
        data = self.response.data
        for offset in range(0, len(data), chunk_size):
            yield data[offset:offset + chunk_size]

    def close(self):
        self.closed = True


class HTTP:
    def __init__(self, client):
        self.client = client
        self.calls = []

    def get(self, url, **_kwargs):
        self.calls.append(('GET', urlparse(url).path, None))
        return Response(self.client.get(urlparse(url).path))

    def post(self, url, json, **_kwargs):
        self.calls.append(('POST', urlparse(url).path, dict(json)))
        return Response(self.client.post(urlparse(url).path, json=json))


class Camera:
    boot_id = 'test-boot'

    def __init__(self, clock):
        self.item = Observation(b'\xff\xd8test-jpeg\xff\xd9', clock(),
                                self.boot_id, 'test-camera', 1)

    def snapshot(self):
        return self.item


def test_browser_camera_ai_stop_and_old_lease_rejection():
    clock = Clock()
    controller = MotorController(clock=clock)
    motor_http = HTTP(web_motor.create_app(controller).test_client())
    source = Camera(clock)
    browser = camera_web.create_app(source, motor_http, clock).test_client()
    camera_http = HTTP(browser)

    identity = {'source': 'browser', 'session': 'browser_session_01'}
    armed = browser.post('/motor/cmd', json={**identity, 'c': 'arm'})
    lease = armed.get_json()['lease']
    command = {**identity, 'lease': lease, 'c': 'fwd', 'speed': 30, 'duration': 0.25}
    assert browser.post('/motor/cmd', json=command).status_code == 200
    assert all(value == 30 for value in controller.status()['outputs'].values())

    def fetch():
        return vision.get_frame_from_stream(http=camera_http, clock=clock,
                                            boot_id=source.boot_id)

    def apply(policy):
        vision.apply_policy(policy, http=motor_http)

    before = len(motor_http.calls)
    _, policy = vision.policy_step(fetch, lambda _: (
        '{"person":{"present":false},"stop_sign":{"present":false}}'),
        apply, clock, source.boot_id)
    assert policy['action'] == 'none'
    assert len(motor_http.calls) == before  # No motion, speed, arm, or heartbeat.

    _, policy = vision.policy_step(fetch, lambda _: (
        '{"person":{"present":false},"stop_sign":{"present":true}}'),
        apply, clock, source.boot_id)
    assert policy['action'] == 'stop'
    state = controller.status()
    assert state['latched'] and not state['armed'] and not any(state['outputs'].values())
    assert browser.post('/motor/cmd', json=command).status_code == 409
    assert browser.post('/motor/cmd', json={**identity, 'c': 'arm'}).status_code == 409
    assert browser.post('/motor/cmd', json={**identity, 'c': 'reset'}).status_code == 200
    new_lease = browser.post('/motor/cmd', json={**identity, 'c': 'arm'}).get_json()['lease']
    assert new_lease != lease
    assert browser.post('/motor/cmd', json=command).status_code == 409
    assert not any(controller.status()['outputs'].values())


def test_stale_camera_snapshot_stops_without_calling_model():
    clock = Clock()
    controller = MotorController(clock=clock)
    motor_http = HTTP(web_motor.create_app(controller).test_client())
    source = Camera(clock)
    source.item = Observation(source.item.jpeg, clock() - 3, source.boot_id,
                              'test-camera', 1)
    camera_http = HTTP(camera_web.create_app(source, motor_http, clock).test_client())
    identity = {'source': 'manual', 'session': 'manual_session_01'}
    lease = controller.execute({**identity, 'c': 'arm'})['lease']
    controller.execute({**identity, 'lease': lease, 'c': 'fwd'})

    def model(_observation):
        raise AssertionError('stale capture must not reach model transport')

    _, policy = vision.policy_step(
        lambda: vision.get_frame_from_stream(http=camera_http, clock=clock,
                                             boot_id=source.boot_id),
        model, lambda result: vision.apply_policy(result, http=motor_http),
        clock, source.boot_id)
    assert not policy['valid'] and policy['action'] == 'stop'
    assert controller.status()['latched']
    assert not any(controller.status()['outputs'].values())


def test_status_polling_cannot_extend_command_expiry():
    clock = Clock()
    controller = MotorController(clock=clock)
    client = web_motor.create_app(controller).test_client()
    identity = {'source': 'manual', 'session': 'manual_session_01'}
    lease = client.post('/cmd', json={**identity, 'c': 'arm'}).get_json()['lease']
    client.post('/cmd', json={**identity, 'lease': lease, 'c': 'fwd', 'duration': 0.25})
    for _ in range(3):
        clock.now += 0.1
        result = client.get('/status').get_json()
    assert result['reason'] == 'command-expired'
    assert result['latched'] and not any(result['outputs'].values())


def test_ai_stop_delivery_surfaces_actual_motor_disable_failure():
    clock = Clock()
    controller = MotorController(clock=clock)
    motor_http = HTTP(web_motor.create_app(controller).test_client())
    identity = {'source': 'manual', 'session': 'manual_session_01'}
    lease = controller.execute({**identity, 'c': 'arm'})['lease']
    controller.execute({**identity, 'lease': lease, 'c': 'fwd'})

    def failed_disable():
        raise OSError('injected stuck mock output')

    controller.backend.disable = failed_disable
    with pytest.raises(requests.HTTPError):
        vision.apply_policy({'action': 'stop', 'valid': True}, http=motor_http)
    state = controller.status()
    assert state['state'] == 'fault' and not state['disable_confirmed']
    assert state['outputs_uncertain']
