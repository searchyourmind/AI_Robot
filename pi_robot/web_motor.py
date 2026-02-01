#!/usr/bin/env python3
import time
from flask import Flask, request, jsonify
import RPi.GPIO as GPIO
import os

# --- PIN MAP (BCM) ---
PWMA = 18
AIN1 = 23
AIN2 = 24

PWMB = 13
BIN1 = 5
BIN2 = 6

STBY = 25

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

for pin in [PWMA, AIN1, AIN2, PWMB, BIN1, BIN2, STBY]:
    GPIO.setup(pin, GPIO.OUT)
    GPIO.output(pin, GPIO.LOW)

pwmA = GPIO.PWM(PWMA, 1000)  # 1 kHz
pwmB = GPIO.PWM(PWMB, 1000)
pwmA.start(0)
pwmB.start(0)

speed = 50  # 0–100
app = Flask(__name__)

def standby(on: bool):
    GPIO.output(STBY, GPIO.HIGH if on else GPIO.LOW)

def stop_all():
    global speed
    standby(True)
    for pin in [AIN1, AIN2, BIN1, BIN2]:
        GPIO.output(pin, GPIO.LOW)
    pwmA.ChangeDutyCycle(0)
    pwmB.ChangeDutyCycle(0)

def set_speed(val: int):
    global speed
    speed = max(0, min(100, int(val)))

def forward():
    standby(True)
    GPIO.output(AIN1, GPIO.HIGH)
    GPIO.output(AIN2, GPIO.LOW)
    GPIO.output(BIN1, GPIO.HIGH)
    GPIO.output(BIN2, GPIO.LOW)
    pwmA.ChangeDutyCycle(speed)
    pwmB.ChangeDutyCycle(speed)

def backward():
    standby(True)
    GPIO.output(AIN1, GPIO.LOW)
    GPIO.output(AIN2, GPIO.HIGH)
    GPIO.output(BIN1, GPIO.LOW)
    GPIO.output(BIN2, GPIO.HIGH)
    pwmA.ChangeDutyCycle(speed)
    pwmB.ChangeDutyCycle(speed)

def left():
    standby(True)
    # left: A backwards, B forward
    GPIO.output(AIN1, GPIO.LOW)
    GPIO.output(AIN2, GPIO.HIGH)
    GPIO.output(BIN1, GPIO.HIGH)
    GPIO.output(BIN2, GPIO.LOW)
    pwmA.ChangeDutyCycle(speed)
    pwmB.ChangeDutyCycle(speed)

def right():
    standby(True)
    # right: A forward, B backwards
    GPIO.output(AIN1, GPIO.HIGH)
    GPIO.output(AIN2, GPIO.LOW)
    GPIO.output(BIN1, GPIO.LOW)
    GPIO.output(BIN2, GPIO.HIGH)
    pwmA.ChangeDutyCycle(speed)
    pwmB.ChangeDutyCycle(speed)

@app.route("/cmd")
def cmd():
    global speed
    c = request.args.get("c", "").lower()
    val = request.args.get("v")
    if c == "stop":
        stop_all()
    elif c == "fwd":
        forward()
    elif c == "back":
        backward()
    elif c == "left":
        left()
    elif c == "right":
        right()
    elif c == "speed" and val is not None:
        set_speed(val)
    elif c == "pulse_fwd":
        forward()
        time.sleep(float(val) if val else 0.5)
        stop_all()
    else:
        return jsonify({"ok": False, "error": "unknown cmd"}), 400

    return jsonify({"ok": True, "cmd": c, "speed": speed})

@app.route("/status")
def status():
    return jsonify({"ok": True, "speed": speed})

if __name__ == "__main__":
    try:
        standby(True)
        port = int(os.environ.get("PORT", "8088"))
        app.run(host="0.0.0.0", port=port)
    finally:
        stop_all()
        GPIO.cleanup()
