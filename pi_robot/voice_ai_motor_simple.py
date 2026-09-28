#!/usr/bin/env python3
"""Explicitly armed CLI controller; importing this module does not send requests."""
import os
import uuid
import requests

MOTOR_URL = os.environ.get('MOTOR_URL', 'http://127.0.0.1:8088')
HELP = '''Commands:
  reset         clear stop/fault latch; remains disarmed
  arm           explicitly request a new control lease
  f / forward, b / back, l / left, r / right   move for 0.25 s
  s / stop      stop and disarm; reset + arm required afterwards
  sp <0-100>    change speed (does not extend a command)
  q            stop and quit
Motion expiry latches stop. No heartbeat or automatic rearm is used.
'''


class MotorClient:
    def __init__(self, http=requests, motor_url=MOTOR_URL):
        self.http = http
        self.motor_url = motor_url
        self.session = str(uuid.uuid4())
        self.lease = None

    def command(self, command, **values):
        body = {'c': command, 'source': 'voice', 'session': self.session, **values}
        if command in ('stop', 'reset'):
            self.lease = None
        elif command not in ('arm',):
            if not self.lease:
                raise ValueError('explicit reset (if latched) and arm required')
            body['lease'] = self.lease
        if command in ('fwd', 'back', 'left', 'right'):
            body['duration'] = 0.25
        try:
            response = self.http.post(self.motor_url + '/cmd', json=body, timeout=(0.5, 0.5))
            result = response.json()
            if response.status_code >= 400 or result.get('ok') is not True:
                raise ValueError(result.get('error') or result.get('reason') or 'motor request failed')
            if command == 'arm':
                token = result.get('lease')
                if not isinstance(token, str) or not token:
                    raise ValueError('server did not issue a control lease')
                self.lease = token
            return result
        except Exception:
            self.lease = None
            raise

    def stop_best_effort(self, output=print):
        try:
            self.command('stop')
        except Exception as exc:
            output('STOP NOT CONFIRMED: ' + str(exc))


def main(input_fn=input, output=print, client=None):
    client = client or MotorClient()
    output('[AI] Manual CLI motor control; AI does not authorize movement')
    output(HELP)
    aliases = {'f': 'fwd', 'forward': 'fwd', 'b': 'back', 'back': 'back',
               'l': 'left', 'left': 'left', 'r': 'right', 'right': 'right',
               's': 'stop', 'stop': 'stop', 'arm': 'arm', 'reset': 'reset'}
    try:
        while True:
            try:
                line = input_fn('> ').strip().lower()
            except (EOFError, KeyboardInterrupt):
                break
            if line == 'q':
                break
            if not line:
                continue
            try:
                if line in aliases:
                    result = client.command(aliases[line])
                elif line.startswith('sp '):
                    parts = line.split()
                    if len(parts) != 2 or not parts[1].isascii() or not parts[1].isdigit():
                        raise ValueError('speed must be an integer from 0 to 100')
                    value = int(parts[1])
                    if not 0 <= value <= 100:
                        raise ValueError('speed must be from 0 to 100')
                    result = client.command('speed', v=value)
                else:
                    output(HELP)
                    continue
                output(str(result))
            except Exception as exc:
                output('Command rejected/connection lost: ' + str(exc))
                client.stop_best_effort(output)
    finally:
        client.stop_best_effort(output)


if __name__ == '__main__':
    main()
