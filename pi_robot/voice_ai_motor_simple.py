#!/usr/bin/env python3
import os
import requests

MOTOR_URL = os.environ.get("MOTOR_URL", "http://127.0.0.1:8088")

HELP = """
Commands:
  f / forward   - go forward
  b / back      - go backward
  l / left      - turn left
  r / right     - turn right
  s / stop      - stop
  sp <0-100>    - set speed
  q             - quit
"""

print("[AI] Simple CLI motor control")
print("[INFO] MOTOR_URL =", MOTOR_URL)
print(HELP)

while True:
    try:
        line = input("> ").strip().lower()
    except (EOFError, KeyboardInterrupt):
        print("\n[AI] Bye.")
        break

    if not line:
        continue
    if line == "q":
        break
    if line in ("f", "forward"):
        requests.get(f"{MOTOR_URL}/cmd", params={"c": "fwd"})
    elif line in ("b", "back"):
        requests.get(f"{MOTOR_URL}/cmd", params={"c": "back"})
    elif line in ("l", "left"):
        requests.get(f"{MOTOR_URL}/cmd", params={"c": "left"})
    elif line in ("r", "right"):
        requests.get(f"{MOTOR_URL}/cmd", params={"c": "right"})
    elif line in ("s", "stop"):
        requests.get(f"{MOTOR_URL}/cmd", params={"c": "stop"})
    elif line.startswith("sp "):
        try:
            val = int(line.split()[1])
            requests.get(f"{MOTOR_URL}/cmd", params={"c": "speed", "v": val})
        except Exception:
            print("Bad speed. Example: sp 60")
    else:
        print(HELP)
