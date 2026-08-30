#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_evidence_envelope_handshake.py — WAVE0 typed envelope.

Not registered in run_all.py (WORKLOCK).
Run: python -X utf8 _ops/tests/test_evidence_envelope_handshake.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

_OPS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_OPS))

from handshake.envelope import (
    RECEIVER_SENSORIUM,
    SCHEMA,
    dumps,
    make_envelope,
    validate_envelope,
    write_atomic,
)


def _ok_raw():
    return [{"command": "echo ok", "stdout": "ok\n", "stderr": "", "exit": 0, "ts": "t"}]


def _base(**kw):
    d = dict(
        receiver=RECEIVER_SENSORIUM,
        task_id="t",
        claim="c",
        raw=_ok_raw(),
        reproduction_command="echo ok",
        goal="g",
        decisions=[],
        artifacts=[],
        uncertainty_notes=[],
        escalation_on_fail="owner",
    )
    d.update(kw)
    return make_envelope(**d)


def t_valid_roundtrip():
    env = _base()
    assert validate_envelope(env) == []
    env2 = json.loads(dumps(env).decode("utf-8"))
    assert env2["schema"] == SCHEMA
    assert validate_envelope(env2) == []


def t_reject_claim_without_raw():
    env = _base()
    env["evidence"]["raw"] = []
    assert "claim-without-raw-evidence" in validate_envelope(env)


def t_reject_claim_without_repro():
    env = _base()
    env["evidence"]["reproduction_command"] = ""
    assert "claim-without-reproduction-command" in validate_envelope(env)


def t_reject_autonomy_delta():
    env = _base()
    env["authority"]["autonomy_delta"] = 1
    env["authority"]["may_authorize"] = True
    errs = validate_envelope(env)
    assert "autonomy-delta-must-be-zero" in errs
    assert "may_authorize-must-be-false-in-wave0" in errs


def t_retry_cap():
    env = _base()
    env["escalation"]["max_retries"] = 9
    assert "max_retries-out-of-range" in validate_envelope(env)
    env["escalation"]["max_retries"] = 3
    assert validate_envelope(env) == []


def t_atomic_write_nonzero(tmp: Path):
    p = tmp / "e.json"
    data = b'{"ok":true}\n'
    r = write_atomic(p, data)
    assert r["ok"], r
    assert r["bytes"] == len(data)
    assert p.read_bytes() == data
    r2 = write_atomic(p, b'{"ok":false}\n')
    assert r2["ok"], r2
    assert p.read_bytes() == b'{"ok":false}\n'
    r0 = write_atomic(p, b"")
    assert not r0["ok"]
    assert r0["reason"] == "zero-byte-after-write"


def main() -> int:
    import tempfile
    t_valid_roundtrip()
    t_reject_claim_without_raw()
    t_reject_claim_without_repro()
    t_reject_autonomy_delta()
    t_retry_cap()
    with tempfile.TemporaryDirectory() as td:
        t_atomic_write_nonzero(Path(td))
    print("test_evidence_envelope_handshake: 6/6 PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
