from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
import yaml
from nacl.signing import SigningKey

from octopus_sensorium.verify import (
    ConfigValidityError,
    SignatureError,
    assert_validity_window,
    content_hash,
    load_signed,
)


def test_signed_roundtrip(tmp_path: Path):
    key = SigningKey.generate()
    payload = b'{"ok": true}\n'
    sig = key.sign(payload).signature
    doc = tmp_path / "board.yaml"
    sig_path = tmp_path / "board.yaml.sig"
    doc.write_bytes(payload)
    sig_path.write_bytes(sig)
    out = load_signed(doc, bytes(key.verify_key))
    assert out == payload
    assert content_hash(payload).startswith("sha256:")


def test_bad_signature(tmp_path: Path):
    key = SigningKey.generate()
    other = SigningKey.generate()
    payload = b"hello"
    (tmp_path / "board.yaml").write_bytes(payload)
    (tmp_path / "board.yaml.sig").write_bytes(other.sign(payload).signature)
    with pytest.raises(SignatureError):
        load_signed(tmp_path / "board.yaml", bytes(key.verify_key))


def test_validity_window():
    now = datetime.now(timezone.utc)
    doc = {
        "not_before": (now - timedelta(days=1)).isoformat(),
        "not_after": (now + timedelta(days=1)).isoformat(),
    }
    assert_validity_window(doc, now)
    expired = {
        "not_before": (now - timedelta(days=10)).isoformat(),
        "not_after": (now - timedelta(days=1)).isoformat(),
    }
    with pytest.raises(ConfigValidityError):
        assert_validity_window(expired, now)


def test_board_yaml_has_stable_id():
    doc = yaml.safe_load(Path("/etc/octopus/config/board.yaml").read_text(encoding="utf-8"))
    assert doc["board"]["board_id"] == "sensorium-opi5pro-68e44cdf"
    assert doc["board"]["hostname"] == "DietPi"
    assert doc["safety"]["safety_state"] == "SOFTWARE_ONLY"
    assert doc["power"]["power_state"] == "NOT_INSTRUMENTED"
