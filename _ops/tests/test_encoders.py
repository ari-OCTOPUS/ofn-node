#!/usr/bin/env python3
"""test_encoders.py — تستِ per-layer encoders (deterministic, R^32, normalized).

$0 آفلاین.
"""
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent))
import harness

import numpy as np
from neural.encoders import (encode_observation, encode_awareness, encode_rfc,
                              encode_phi_t, encode_calibration)


def t_observation_deterministic():
    """همان input → همیشه همان output."""
    v1 = encode_observation("lead", "A01")
    v2 = encode_observation("lead", "A01")
    assert np.allclose(v1, v2, atol=1e-12), "encoder must be deterministic"


def t_observation_different_inputs():
    """input متفاوت → output متفاوت."""
    v1 = encode_observation("lead", "A01")
    v2 = encode_observation("error", "E03")
    # shouldn't be identical (statistically near-impossible with hash)
    assert not np.allclose(v1, v2, atol=1e-6)


def t_observation_dim32():
    """output dim=32."""
    v = encode_observation("test", "label")
    assert v.shape == (32,)


def t_observation_normalized():
    """output normalized (||v|| ≈ 1)."""
    v = encode_observation("test", "label")
    norm = np.linalg.norm(v)
    assert abs(norm - 1.0) < 1e-6, f"expected ||v||=1, got {norm}"


def t_awareness_vector():
    """awareness vector → R^32."""
    aw = [0.1, 0.3, 0.5, 0.7, 0.9]
    v = encode_awareness(aw)
    assert v.shape == (32,)
    norm = np.linalg.norm(v)
    assert abs(norm - 1.0) < 1e-6


def t_awareness_none():
    """None → zero vector."""
    v = encode_awareness(None)
    assert v.shape == (32,)
    assert np.allclose(v, np.zeros(32))


def t_awareness_pad():
    """vector کم‌بعد → pad با صفر."""
    aw = [0.5]
    v = encode_awareness(aw)
    assert v.shape == (32,)
    assert v[0] > 0  # first element preserved


def t_rfc_deterministic():
    """RFC encoder deterministic."""
    v1 = encode_rfc("RFC-abc123", "error rate high", "high")
    v2 = encode_rfc("RFC-abc123", "error rate high", "high")
    assert np.allclose(v1, v2, atol=1e-12)


def t_rfc_severity_effect():
    """severity مختلف → vector متفاوت (حداقل dims اول)."""
    v_crit = encode_rfc("RFC-x", "bug", "critical")
    v_low = encode_rfc("RFC-x", "bug", "low")
    # first 4 dims are scaled by severity weight — should differ
    assert not np.allclose(v_crit, v_low, atol=1e-6)


def t_phi_t_with_vector():
    """phi_t با vector + sigma."""
    phi = np.random.randn(8).astype(np.float64)
    v = encode_phi_t(phi, sigma=0.85)
    assert v.shape == (32,)
    norm = np.linalg.norm(v)
    assert norm > 0.1  # nonzero


def t_phi_t_none():
    """phi_t None → hash-based fallback."""
    v = encode_phi_t(None, sigma=0.9)
    assert v.shape == (32,)


def t_calibration_verdicts():
    """calibration verdicts → R^32."""
    verdicts = [
        {"verdict": "approve"},
        {"verdict": "approve"},
        {"verdict": "reject"},
    ]
    v = encode_calibration(verdicts)
    assert v.shape == (32,)


def t_calibration_empty():
    """calibration خالی → zero vector."""
    v = encode_calibration(None)
    assert np.allclose(v, np.zeros(32))


def t_calibration_none():
    """calibration None → zero vector."""
    v = encode_calibration([])
    assert np.allclose(v, np.zeros(32))


if __name__ == "__main__":
    failed = harness.run([
        ("observation deterministic", t_observation_deterministic),
        ("observation different inputs", t_observation_different_inputs),
        ("observation dim=32", t_observation_dim32),
        ("observation normalized", t_observation_normalized),
        ("awareness vector", t_awareness_vector),
        ("awareness None", t_awareness_none),
        ("awareness pad", t_awareness_pad),
        ("RFC deterministic", t_rfc_deterministic),
        ("RFC severity effect", t_rfc_severity_effect),
        ("phi_t with vector", t_phi_t_with_vector),
        ("phi_t None fallback", t_phi_t_none),
        ("calibration verdicts", t_calibration_verdicts),
        ("calibration empty", t_calibration_empty),
        ("calibration None", t_calibration_none),
    ])
    sys.exit(1 if failed else 0)
