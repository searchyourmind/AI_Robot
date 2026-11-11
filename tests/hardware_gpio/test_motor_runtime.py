"""Configuration and launcher lifecycle without a GPIO chip or HTTP listener."""
import importlib
import json

import pytest

from pi_robot import motor_runtime, web_motor
from pi_robot.motor_backend import MockBackend


def config_file(tmp_path, data=None, *, raw=None):
    path = tmp_path / "motor.json"
    path.write_text(raw if raw is not None else json.dumps(
        data if data is not None else {"left_polarity": 1, "right_polarity": -1}))
    return str(path)


def test_default_mock_and_unknown_backend_rejected():
    controller = motor_runtime.create_controller_from_env({})
    assert controller.backend.name == "mock"
    controller.shutdown()
    with pytest.raises(ValueError, match="MOTOR_BACKEND"):
        motor_runtime.create_controller_from_env({"MOTOR_BACKEND": "drv8874_typo"})
    with pytest.raises(ValueError, match="MOTOR_CONFIG"):
        motor_runtime.create_controller_from_env({"MOTOR_BACKEND": "drv8874_reva"})
    with pytest.raises(ValueError, match="MOTOR_CONFIG"):
        motor_runtime.create_controller_from_env({"MOTOR_CONFIG": "ignored.json"})


@pytest.mark.parametrize("raw", [
    "[]", "null", "{}", "{broken", '{"left_polarity":1}',
    '{"left_polarity":1,"right_polarity":1,"right_polarity":-1}',
    '{"left_polarity":1,"right_polarity":1,"pins":[1,2,3]}',
    '{"left_polarity":null,"right_polarity":null}',
    '{"left_polarity":true,"right_polarity":1}',
    '{"left_polarity":1,"right_polarity":1,"pwm_hz":NaN}',
    " " * 4097,
])
def test_invalid_configuration_fails_before_gpio(tmp_path, raw):
    with pytest.raises(ValueError):
        motor_runtime.create_controller_from_env({
            "MOTOR_BACKEND": "drv8874_reva",
            "MOTOR_CONFIG": config_file(tmp_path, raw=raw),
        })


def test_explicit_backend_uses_reva_identities_and_configuration(tmp_path, monkeypatch):
    from pi_robot import drv8874_backend

    class RecordingBackend(MockBackend):
        name = "drv8874_reva"

        def __init__(self, config):
            super().__init__(("motor_1", "motor_2", "motor_3", "motor_4"))
            self.config = config

    monkeypatch.setattr(drv8874_backend, "DRV8874RevABackend", RecordingBackend)
    controller = motor_runtime.create_controller_from_env({
        "MOTOR_BACKEND": "drv8874_reva", "MOTOR_CONFIG": config_file(tmp_path),
    })
    assert [ch.driver for ch in controller.channels] == ["U20", "U22", "U21", "U23"]
    assert [ch.polarity for ch in controller.channels] == [1, 1, -1, -1]
    assert controller.backend.config.pwm_hz == 1000
    assert not controller.armed and not any(controller.outputs.values())
    controller.shutdown()


def test_factory_closes_backend_on_controller_startup_failure(tmp_path, monkeypatch):
    from pi_robot import drv8874_backend
    calls = []

    class BrokenStartup:
        def __init__(self, config):
            calls.append("opened")

        def close(self):
            calls.append("closed")

    def fail_controller(**_kwargs):
        raise RuntimeError("controller initialization failed")

    monkeypatch.setattr(drv8874_backend, "DRV8874RevABackend", BrokenStartup)
    monkeypatch.setattr(motor_runtime, "MotorController", fail_controller)
    with pytest.raises(RuntimeError, match="initialization failed"):
        motor_runtime.create_controller_from_env({
            "MOTOR_BACKEND": "drv8874_reva", "MOTOR_CONFIG": config_file(tmp_path),
        })
    assert calls == ["opened", "closed"]


def test_import_does_not_select_hardware_or_start_ticker(monkeypatch):
    monkeypatch.setenv("MOTOR_BACKEND", "drv8874_reva")
    monkeypatch.setenv("MOTOR_CONFIG", "/nonexistent/should-not-be-read.json")
    module = importlib.reload(web_motor)
    assert module.app.extensions["motor_controller"].backend.name == "mock"
    assert module.app.test_client().get("/status").json["physical_actuation_enabled"] is False


def test_launcher_cleans_up_after_server_and_shutdown_failures(monkeypatch):
    calls = []

    class Controller:
        def shutdown(self):
            calls.append("shutdown")
            raise RuntimeError("cleanup failed")

    class Event:
        def set(self):
            calls.append("ticker-stopped")

    class Thread:
        def join(self, timeout):
            calls.append("ticker-joined")

    class App:
        def run(self, **kwargs):
            assert kwargs == {"host": "127.0.0.1", "port": 8088,
                              "threaded": True, "use_reloader": False}
            calls.append("server-run")
            raise RuntimeError("server failed")

    monkeypatch.delenv("PORT", raising=False)
    monkeypatch.setattr(web_motor, "create_controller_from_env", Controller)
    monkeypatch.setattr(web_motor, "create_app", lambda _controller: App())
    monkeypatch.setattr(web_motor, "start_ticker", lambda _controller: (Event(), Thread()))
    monkeypatch.setattr(web_motor.signal, "signal", lambda *_: None)
    with pytest.raises(RuntimeError, match="cleanup failed"):
        web_motor.main()
    assert calls == ["server-run", "ticker-stopped", "shutdown", "ticker-joined"]


def test_invalid_port_rejected_before_creating_backend(monkeypatch):
    monkeypatch.setenv("PORT", "0")

    def forbidden():
        raise AssertionError("must not initialize GPIO for invalid service options")

    monkeypatch.setattr(web_motor, "create_controller_from_env", forbidden)
    with pytest.raises(SystemExit, match="PORT"):
        web_motor.main()
