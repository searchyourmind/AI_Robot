"""Pure validation for advisory vision; no camera, HTTP, GPIO, or model access."""
from dataclasses import dataclass
import json
import math
from pathlib import Path


class VisionError(ValueError):
    """An observation cannot be used even for an advisory policy."""


def local_boot_id():
    """Linux boot identity shared by camera and policy processes on the same host."""
    try:
        value = Path('/proc/sys/kernel/random/boot_id').read_text().strip()
        return value or None
    except OSError:
        return None


@dataclass(frozen=True)
class Observation:
    jpeg: bytes
    captured_at: float
    boot_id: str
    camera_session: str
    sequence: int


def require_fresh(observation, now, boot_id, max_age=2.0):
    if not boot_id or observation.boot_id != boot_id:
        raise VisionError('capture clock host/boot is unverified')
    if (not math.isfinite(now) or not math.isfinite(observation.captured_at)
            or not math.isfinite(max_age) or max_age <= 0):
        raise VisionError('invalid capture clock')
    age = now - observation.captured_at
    if age < 0 or age > max_age:
        raise VisionError('capture is future-dated or stale')
    if not observation.camera_session or observation.sequence < 1:
        raise VisionError('missing capture identity')
    return observation


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise VisionError('duplicate JSON field')
        result[key] = value
    return result


def _invalid_constant(value):
    raise VisionError('nonstandard JSON number: ' + value)


def parse_policy(text):
    """Parse nested Boolean detections. No result ever authorizes motion.

    Missing/malformed results inhibit; false detections mean only that this
    observation reported no selected hazard, never that the route is safe.
    """
    try:
        if not isinstance(text, str) or not text or len(text) > 4096:
            raise VisionError('missing or oversized model result')
        data = json.loads(text, object_pairs_hook=_unique_object, parse_constant=_invalid_constant)
        if not isinstance(data, dict):
            raise VisionError('expected JSON object')
        person, stop = data.get('person'), data.get('stop_sign')
        if not isinstance(person, dict) or not isinstance(stop, dict):
            raise VisionError('missing detection objects')
        if type(person.get('present')) is not bool or type(stop.get('present')) is not bool:
            raise VisionError('present fields must be JSON booleans')
        if (person['present'] or 'distance' in person) and person.get('distance') not in ('near', 'mid', 'far'):
            raise VisionError('person distance must be near/mid/far when supplied or present')
        if stop['present']:
            return {'action': 'stop', 'valid': True, 'reason': 'stop sign detected',
                    'recommendation': 'stop'}
        if person['present'] and person['distance'] in ('near', 'mid'):
            return {'action': 'stop', 'valid': True, 'reason': 'person near path',
                    'recommendation': 'slow/stop; manual reassessment required'}
        return {'action': 'none', 'valid': True, 'reason': 'no selected close hazard reported',
                'recommendation': 'manual control only; not clearance to move'}
    except (ValueError, TypeError) as exc:
        return {'action': 'stop', 'valid': False, 'reason': str(exc),
                'recommendation': 'invalid observation; stop and reassess'}
