#!/usr/bin/env python3
"""Local mock motor API. See hardware/rev_a/docs/software_safety_api.md."""
import json
import os
import signal
import threading

from flask import Flask, jsonify, request
from werkzeug.exceptions import HTTPException

try:
    from .motor_control import CommandError, MotorController
    from .motor_config import TICK_INTERVAL_S
except ImportError:
    from motor_control import CommandError, MotorController
    from motor_config import TICK_INTERVAL_S


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON fields are not accepted")
        result[key] = value
    return result


def create_app(controller: MotorController | None = None) -> Flask:
    application = Flask(__name__)
    application.config["MAX_CONTENT_LENGTH"] = 4096
    controller = controller if controller is not None else MotorController()
    application.extensions["motor_controller"] = controller

    @application.route("/cmd", methods=["GET", "POST"])
    def cmd():
        try:
            if request.method == "POST":
                if not request.is_json:
                    raise CommandError("POST requires application/json")
                try:
                    data = json.loads(request.get_data(), object_pairs_hook=_unique_object)
                except (ValueError, UnicodeDecodeError, RecursionError):
                    raise CommandError("invalid or duplicate JSON fields") from None
            else:
                if any(len(request.args.getlist(key)) != 1 for key in request.args):
                    raise CommandError("duplicate query fields are not accepted")
                data = request.args.to_dict()
            return jsonify(controller.execute(data))
        except CommandError as exc:
            if exc.status == 400:
                controller.fault("invalid-request")
            result = controller.status()
            return jsonify({**result, "ok": False, "error": str(exc)}), exc.status

    @application.route("/status")
    def status():
        try:
            return jsonify(controller.status())
        except CommandError as exc:
            return jsonify({**controller.status(), "ok": False, "error": str(exc)}), exc.status

    @application.errorhandler(HTTPException)
    def http_error(exc):
        if request.path == "/cmd":
            controller.fault("invalid-http-request")
        return jsonify({"ok": False, "error": exc.description}), exc.code

    return application


def start_ticker(controller: MotorController):
    stopped = threading.Event()

    def run():
        while not stopped.wait(TICK_INTERVAL_S):
            try:
                controller.tick()
            except Exception:
                controller.fault("ticker-failed")

    thread = threading.Thread(target=run, name="motor-software-watchdog", daemon=True)
    thread.start()
    return stopped, thread


app = create_app()


def main():
    if os.environ.get("MOTOR_BACKEND", "mock") != "mock":
        raise SystemExit("Only MOTOR_BACKEND=mock is available; GPIO pins and electrical requirements remain unverified.")
    controller = app.extensions["motor_controller"]
    stop_event, thread = start_ticker(controller)

    def terminate(_signum, _frame):
        raise SystemExit(0)

    signal.signal(signal.SIGTERM, terminate)
    try:
        app.run(host="127.0.0.1", port=int(os.environ.get("PORT", "8088")), threaded=True, use_reloader=False)
    finally:
        controller.shutdown()
        stop_event.set()
        thread.join(timeout=1)


if __name__ == "__main__":
    main()
