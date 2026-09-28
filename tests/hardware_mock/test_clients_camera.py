"""Camera acquisition, browser proxy and CLI tested with injected dependencies."""
from types import SimpleNamespace
import requests
import pytest

from pi_robot import web_vision_drive_picam_ai as web
from pi_robot.voice_ai_motor_simple import MotorClient, main
from pi_robot.vision_safety import Observation

JPEG = b'\xff\xd8mock\xff\xd9'


def test_camera_timestamp_precedes_read_and_encoding():
    now = [10.0]
    events = []
    def read():
        events.append('read')
        now[0] = 11.0
        return True, object()
    def encode(ext, frame):
        events.append('encode')
        now[0] = 11.5
        return True, SimpleNamespace(tobytes=lambda: JPEG)
    fake_cv = SimpleNamespace(imencode=encode)
    source = web.CameraSource(cv=fake_cv, clock=lambda: now[0], boot_id='test-boot')
    source.cap = SimpleNamespace(read=read)
    result = source.capture_once()
    assert events == ['read', 'encode']
    assert result.captured_at == 10.0
    assert source.snapshot() == result
    assert now[0] == 11.5


def test_snapshot_and_mjpeg_preserved_without_camera_access():
    observation = Observation(JPEG, 10, 'boot', 'session', 1)
    provider = SimpleNamespace(snapshot=lambda: observation, boot_id='boot')
    client = web.create_app(camera=provider, clock=lambda: 10.5).test_client()
    response = client.get('/snapshot.jpg')
    assert response.status_code == 200 and response.data == JPEG
    assert response.headers['X-Capture-Monotonic'] == '10'
    assert response.headers['Cache-Control'] == 'no-store'
    assert response.headers['X-Capture-Boot-ID'] == 'boot'
    stream = client.get('/stream.mjpg', buffered=False)
    assert JPEG in next(iter(stream.response))
    stream.close()
    assert client.get('/status').json['camera_ready']


def test_missing_stale_and_unverified_camera_returns_error():
    for provider in [None,
                     SimpleNamespace(snapshot=lambda: Observation(JPEG, 1, 'boot', 'session', 1), boot_id='boot'),
                     SimpleNamespace(snapshot=lambda: Observation(JPEG, 10, None, 'session', 1), boot_id=None)]:
        client = web.create_app(camera=provider, clock=lambda: 10.5).test_client()
        assert client.get('/snapshot.jpg').status_code == 503
        assert client.get('/status').status_code == 503


class Http:
    def __init__(self):
        self.calls = []
        self.result = {'ok': True, 'lease': 'fake-lease-token', 'armed': True}
        self.code = 200
        self.error = None

    def post(self, url, **kwargs):
        self.calls.append((url, kwargs))
        if self.error:
            raise self.error
        return SimpleNamespace(json=lambda: self.result, status_code=self.code)

    def get(self, url, **kwargs):
        return self.post(url, **kwargs)


def test_browser_uses_same_origin_proxy_and_displays_errors():
    http = Http()
    client = web.create_app(http=http).test_client()
    html = client.get('/').data.decode()
    assert "fetch('/motor/cmd'" in html
    assert 'RESET LATCH' in html and 'ARM' in html
    assert 'pagehide' in html and 'visibilitychange' in html
    assert 'STOP NOT CONFIRMED' in html
    assert 'AI advisory overlay' in html
    response = client.post('/motor/cmd', json={'c': 'stop', 'source': 'ai', 'session': 'browser-session'})
    assert response.status_code == 200
    assert http.calls[0][1]['json']['source'] == 'browser'
    assert http.calls[0][1]['timeout'] == (0.5, 0.5)
    http.result, http.code = {'ok': False, 'error': 'latched'}, 409
    assert client.post('/motor/cmd', json={'c': 'arm'}).status_code == 409
    assert client.get('/motor/status').status_code == 409
    http.error = requests.ConnectionError('disconnected')
    assert client.post('/motor/cmd', json={'c': 'stop'}).status_code == 502
    assert client.get('/motor/status').status_code == 502
    assert client.post('/motor/cmd', data='not JSON').status_code == 400


def test_cli_requires_explicit_arm_and_forwards_lease_and_duration():
    http = Http()
    client = MotorClient(http=http)
    with pytest.raises(ValueError, match='arm required'):
        client.command('fwd')
    assert not http.calls
    client.command('arm')
    client.command('fwd')
    body = http.calls[-1][1]['json']
    assert body['source'] == 'voice'
    assert body['lease'] == 'fake-lease-token'
    assert body['duration'] == 0.25
    client.command('stop')
    assert client.lease is None
    with pytest.raises(ValueError):
        client.command('fwd')


def test_cli_errors_revoke_local_lease_and_do_not_auto_rearm():
    http = Http()
    client = MotorClient(http=http)
    client.command('arm')
    http.result, http.code = {'ok': False, 'reason': 'command expired'}, 409
    with pytest.raises(ValueError, match='command expired'):
        client.command('fwd')
    assert client.lease is None
    assert [call[1]['json']['c'] for call in http.calls] == ['arm', 'fwd']


@pytest.mark.parametrize('ending', ['q', EOFError, KeyboardInterrupt])
def test_cli_quit_eof_and_interrupt_best_effort_stop(ending):
    http = Http()
    def input_fn(_):
        if isinstance(ending, type):
            raise ending()
        return ending
    main(input_fn=input_fn, output=lambda _: None, client=MotorClient(http=http))
    assert http.calls[-1][1]['json']['c'] == 'stop'


def test_cli_rejects_unbounded_and_noninteger_speeds_and_stops():
    http = Http()
    inputs = iter(['sp 101', 'sp -1', 'sp 2.5', 'sp 10 20', 'q'])
    lines = []
    main(input_fn=lambda _: next(inputs), output=lines.append, client=MotorClient(http=http))
    assert all(call[1]['json']['c'] == 'stop' for call in http.calls)
    assert any('speed must' in line for line in lines)


def test_cli_network_failure_reports_unconfirmed_stop():
    http = Http()
    http.error = requests.ConnectionError('offline')
    lines = []
    main(input_fn=lambda _: 'q', output=lines.append, client=MotorClient(http=http))
    assert any('STOP NOT CONFIRMED' in line for line in lines)


def test_browser_proxy_rejects_duplicate_and_oversized_commands_before_http():
    http = Http()
    client = web.create_app(http=http).test_client()
    for body in ('{"c":"stop","c":"fwd"}', '{"c":"stop","source":"ai","source":"browser"}'):
        response = client.post('/motor/cmd', data=body, content_type='application/json')
        assert response.status_code == 400
        assert 'duplicate' in response.json['error']
    response = client.post('/motor/cmd', data=' ' * 4097, content_type='application/json')
    assert response.status_code == 413
    assert not http.calls
