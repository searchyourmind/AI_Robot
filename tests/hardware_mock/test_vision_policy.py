"""No model clients, cameras, network connections, or GPIO devices are used."""
import builtins
import importlib
import json
import sys
from types import SimpleNamespace

import pytest

from pi_robot import vision_policy_daemon as daemon
from pi_robot.vision_safety import Observation, VisionError, parse_policy, require_fresh

FALSE_DETECTIONS = '{"person":{"present":false},"stop_sign":{"present":false}}'
JPEG = b'\xff\xd8test\xff\xd9'


def observation(captured_at=10.0, boot='test-boot'):
    return Observation(JPEG, captured_at, boot, 'camera-session', 1)


def test_false_booleans_do_not_detect_stop_sign_or_authorize_motion():
    policy = parse_policy(FALSE_DETECTIONS)
    assert policy['valid'] is True
    assert policy['action'] == 'none'
    assert 'not clearance' in policy['recommendation']


@pytest.mark.parametrize('text', [
    '', None, 'not JSON', '[]', '{}', '{"person":{}}',
    '{"person":{"present":false},"stop_sign":{"present":"false"}}',
    '{"person":{"present":0},"stop_sign":{"present":false}}',
    '{"person":{"present":true},"stop_sign":{"present":false}}',
    '{"person":{"present":true,"distance":"unknown"},"stop_sign":{"present":false}}',
    '{"person":{"present":false,"present":true},"stop_sign":{"present":false}}',
    '{"person":{"present":false,"distance":NaN},"stop_sign":{"present":false}}',
    '{"person":{"present":false,"distance":99},"stop_sign":{"present":false}}',
    '```json\n' + FALSE_DETECTIONS + '\n```', 'x' * 4097,
])
def test_malformed_missing_or_non_boolean_results_fail_closed(text):
    policy = parse_policy(text)
    assert policy['valid'] is False
    assert policy['action'] == 'stop'


@pytest.mark.parametrize('distance,action', [('near', 'stop'), ('mid', 'stop'), ('far', 'none')])
def test_person_recommendation_never_issues_go_or_slow_motion(distance, action):
    policy = parse_policy(json.dumps({'person': {'present': True, 'distance': distance},
                                     'stop_sign': {'present': False}}))
    assert policy['valid'] is True
    assert policy['action'] == action


def test_true_stop_sign_stops():
    assert parse_policy('{"person":{"present":false},"stop_sign":{"present":true}}')['action'] == 'stop'


@pytest.mark.parametrize('stamp,now,boot', [
    (10.0, 12.01, 'test-boot'), (10.1, 10.0, 'test-boot'),
    (10.0, 10.0, 'other-boot'), (10.0, 10.0, None),
    (float('nan'), 10.0, 'test-boot'), (10.0, float('inf'), 'test-boot'),
])
def test_capture_freshness_rejects_stale_future_or_wrong_boot(stamp, now, boot):
    with pytest.raises(VisionError):
        require_fresh(observation(stamp), now, boot)


class Response:
    def __init__(self, data=JPEG, headers=None):
        self.status_code = 200
        self.data = data
        self.headers = {'Content-Type': 'image/jpeg', 'Content-Length': str(len(data)),
                        'X-Capture-Monotonic': '10', 'X-Capture-Boot-ID': 'test-boot',
                        'X-Camera-Session': 'camera-session', 'X-Frame-Sequence': '1'}
        if headers:
            self.headers.update(headers)
        self.closed = False
        self.read_size = None

    def raise_for_status(self):
        pass

    def iter_content(self, chunk_size):
        self.read_size = chunk_size
        for byte in self.data:
            yield bytes([byte])

    def close(self):
        self.closed = True


class Http:
    def __init__(self, response):
        self.response = response
        self.calls = []

    def get(self, url, **kwargs):
        self.calls.append((url, kwargs))
        return self.response


def fetch(response, clock=lambda: 10.5, **kwargs):
    http = Http(response)
    result = daemon.get_frame_from_stream(http=http, clock=clock, boot_id='test-boot', **kwargs)
    assert http.calls[0][1]['timeout'] == (0.5, 0.5)
    assert http.calls[0][1]['allow_redirects'] is False
    return result


def test_bounded_snapshot_keeps_capture_timestamp_and_closes_response():
    response = Response()
    result = fetch(response)
    assert result.captured_at == 10.0
    assert result.jpeg == JPEG
    assert response.closed
    assert response.read_size == 1


@pytest.mark.parametrize('headers', [
    {'X-Capture-Boot-ID': 'wrong-host'}, {'X-Capture-Monotonic': '1'},
    {'X-Capture-Monotonic': 'nan'}, {'Content-Length': str(daemon.MAX_FRAME_BYTES + 1)},
    {'Content-Type': 'multipart/x-mixed-replace'}, {'X-Frame-Sequence': '0'},
])
def test_snapshot_rejects_invalid_stale_and_unbounded_inputs(headers):
    response = Response(headers=headers)
    with pytest.raises(VisionError):
        fetch(response)
    assert response.closed


def test_missing_capture_header_is_not_replaced_by_arrival_time():
    response = Response()
    del response.headers['X-Capture-Monotonic']
    with pytest.raises(VisionError):
        fetch(response)
    assert response.closed


def test_trickle_response_has_total_deadline_in_addition_to_idle_timeout():
    response = Response()
    times = iter([10.0, 10.1, 10.2, 10.3, 11.0])
    with pytest.raises(VisionError, match='total deadline'):
        fetch(response, clock=lambda: next(times), total_timeout=0.5)
    assert response.closed


def test_content_length_caps_buffer_even_if_peer_sends_more():
    response = Response(data=JPEG * 10, headers={'Content-Length': '8'})
    with pytest.raises(VisionError, match='exceeds declared length'):
        fetch(response)
    assert response.closed


@pytest.mark.parametrize('url', ['http://camera.local/snapshot.jpg', 'http://192.168.1.2/snapshot.jpg',
                                 'https://127.0.0.1/snapshot.jpg'])
def test_cross_host_clock_contract_rejected_before_http(url):
    http = Http(Response())
    with pytest.raises(VisionError):
        daemon.get_frame_from_stream(url=url, http=http)
    assert not http.calls


def test_model_response_arrival_never_renews_observation():
    times = iter([10.5, 12.1])
    applied = []
    _, policy = daemon.policy_step(fetch_frame=observation, model=lambda _: FALSE_DETECTIONS,
                                   clock=lambda: next(times), boot_id='test-boot', apply=applied.append)
    assert policy['action'] == 'stop' and not policy['valid']
    assert 'stale' in policy['reason']
    assert applied == [policy]


def test_stale_frame_prevents_model_call():
    called = []
    _, policy = daemon.policy_step(fetch_frame=observation, model=lambda _: called.append(True),
                                   clock=lambda: 30, boot_id='test-boot', apply=lambda _: None)
    assert not called
    assert policy['action'] == 'stop'


def test_missing_frame_and_model_exception_stop():
    def broken_model(_):
        raise RuntimeError('model unavailable')
    for fetcher, model in [(lambda: None, broken_model), (observation, broken_model)]:
        stops = []
        _, policy = daemon.policy_step(fetch_frame=fetcher, model=model, clock=lambda: 10.5,
                                       boot_id='test-boot', apply=stops.append)
        assert stops[0]['action'] == 'stop'
        assert not policy['valid']


def test_ai_apply_never_arms_resets_or_moves_even_for_go_like_policy():
    calls = []
    response = SimpleNamespace(raise_for_status=lambda: None, json=lambda: {'ok': True})
    http = SimpleNamespace(post=lambda url, **kw: calls.append(kw) or response)
    daemon.apply_policy(parse_policy(FALSE_DETECTIONS), http=http)
    assert calls == []
    for policy in [{'action': 'go', 'valid': True}, {'action': 'slow', 'valid': True},
                   {'action': 'none', 'valid': False}, {'action': 'stop', 'valid': True}]:
        daemon.apply_policy(policy, http=http)
    assert all(call['json']['c'] == 'stop' and call['json']['source'] == 'ai' for call in calls)


def test_model_client_is_injected_and_not_closed_by_call():
    calls = []
    response = SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=FALSE_DETECTIONS))])
    fake = SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(
        create=lambda **kwargs: calls.append(kwargs) or response)))
    assert daemon.call_openai_on_frame(observation(), client=fake) == FALSE_DETECTIONS
    assert calls[0]['response_format'] == {'type': 'json_object'}


def test_stop_delivery_error_is_visible():
    def failed_stop(_):
        raise RuntimeError('stop transport down')
    with pytest.raises(RuntimeError, match='stop transport down'):
        daemon.policy_step(fetch_frame=lambda: None, apply=failed_stop)


def test_imports_never_import_camera_or_model_sdk_or_perform_http(monkeypatch):
    real_import = builtins.__import__
    def guarded_import(name, *args, **kwargs):
        if name in ('cv2', 'openai', 'RPi.GPIO'):
            raise AssertionError('hardware/model module loaded at import: ' + name)
        return real_import(name, *args, **kwargs)
    def forbidden(*args, **kwargs):
        raise AssertionError('network call during import')
    monkeypatch.setattr(builtins, '__import__', guarded_import)
    monkeypatch.setattr(daemon.requests, 'get', forbidden)
    monkeypatch.setattr(daemon.requests, 'post', forbidden)
    for name in ('pi_robot.vision_policy_daemon', 'pi_robot.web_vision_drive_picam_ai',
                 'pi_robot.voice_ai_motor_simple'):
        importlib.reload(importlib.import_module(name))
