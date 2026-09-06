"""Deterministic serialization and rejection-only output guard."""
import hashlib
import json
import math


def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False,
                      separators=(",", ":"), allow_nan=False)


def digest(value):
    return hashlib.sha256(canonical(value).encode("utf-8")).hexdigest()


def finite_number(value):
    if type(value) not in (int, float):
        return False
    try:
        return math.isfinite(value)
    except OverflowError:
        return False


def strict_json(raw):
    def pairs(items):
        out = {}
        for key, val in items:
            if key in out:
                raise ValueError("duplicate JSON key: " + key)
            out[key] = val
        return out
    def invalid(value):
        raise ValueError("nonfinite JSON number: " + value)
    value = json.loads(raw, object_pairs_hook=pairs, parse_constant=invalid)
    canonical(value)  # Also rejects overflow such as 1e999.
    return value


def assert_shadow(value, path="$"):
    if isinstance(value, dict):
        for key, val in value.items():
            if key == "executable" and val is not False:
                raise ValueError("non-shadow executable at " + path)
            assert_shadow(val, path + "." + key)
    elif isinstance(value, list):
        for index, val in enumerate(value):
            assert_shadow(val, path + "[" + str(index) + "]")
    return True
