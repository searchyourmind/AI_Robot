"""In-process HTTP only: no listening socket or physical/paid service."""
import pytest

from pi_robot.motor_control import MotorController
from pi_robot.web_motor import create_app


@pytest.fixture
def client():
    controller = MotorController(clock=lambda: 10.0)
    app = create_app(controller)
    app.config["TESTING"] = True
    return app.test_client(), controller


def arm(client):
    http, _ = client
    identity = {"source": "manual", "session": "test_session"}
    response = http.post("/cmd", json={"c": "arm", **identity})
    assert response.status_code == 200
    return {**identity, "lease": response.json["lease"]}


def test_get_compatibility_and_status_no_token(client):
    http, _ = client
    owner = arm(client)
    response = http.get("/cmd", query_string={"c": "pulse_fwd", "v": ".2", **owner})
    assert response.status_code == 200 and response.json["standby"]
    assert "lease" not in http.get("/status").json
    assert http.get("/cmd?c=stop").json["latched"]
    assert http.get("/cmd?c=fwd").status_code in (403, 409)


@pytest.mark.parametrize("data,content_type", [
    ('{"c":"stop","c":"fwd"}', "application/json"),
    ('{"c":', "application/json"),
    ('[]', "application/json"),
    ('{"c":true}', "application/json"),
    ('null', "application/json"),
    ('c=fwd', "application/x-www-form-urlencoded"),
])
def test_invalid_http_payload_fails_closed(client, data, content_type):
    http, controller = client
    owner = arm(client)
    http.post("/cmd", json={"c": "fwd", **owner})
    response = http.post("/cmd", data=data, content_type=content_type)
    assert response.status_code == 400
    assert response.json["ok"] is False
    assert not controller.backend.standby
    assert controller.status()["state"] == "fault"


def test_duplicate_query_rejected(client):
    http, controller = client
    response = http.get("/cmd?c=stop&c=fwd")
    assert response.status_code == 400
    assert controller.status()["latched"]


def test_oversize_payload_latches(client):
    http, controller = client
    response = http.post("/cmd", data='{"c":"' + "x" * 5000 + '"}', content_type="application/json")
    assert response.status_code == 413
    assert controller.status()["latched"]


def test_json_boolean_and_nonfinite_rejected(client):
    http, controller = client
    owner = arm(client)
    response = http.post("/cmd", json={"c": "fwd", "speed": True, **owner})
    assert response.status_code == 400
    assert not controller.backend.standby


def test_stop_requires_no_authorization(client):
    http, controller = client
    owner = arm(client)
    http.post("/cmd", json={"c": "fwd", **owner})
    response = http.post("/cmd", json={"c": "stop", "source": "ai"})
    assert response.status_code == 200
    assert not response.json["armed"]
    assert controller.backend.standby is False


def test_excessive_json_nesting_fails_closed(client):
    http, controller = client
    owner = arm(client)
    http.post("/cmd", json={"c": "fwd", **owner})
    response = http.post("/cmd", data="[" * 1500 + "]" * 1500, content_type="application/json")
    assert response.status_code == 400
    assert not controller.backend.standby


def test_stop_disable_failure_reports_503_and_uncertain_outputs(client):
    http, controller = client
    owner = arm(client)
    http.post("/cmd", json={"c": "fwd", **owner})

    def fail_disable():
        raise OSError("simulated disable failure")

    controller.backend.disable = fail_disable
    response = http.post("/cmd", json={"c": "stop", "source": "ai"})
    assert response.status_code == 503
    assert response.json["ok"] is False
    assert response.json["disable_confirmed"] is False
    assert response.json["outputs_uncertain"] is True
    assert response.json["latched"] is True
    assert response.json["armed"] is False
    assert response.json["state"] == "fault"
    assert controller.backend.standby
