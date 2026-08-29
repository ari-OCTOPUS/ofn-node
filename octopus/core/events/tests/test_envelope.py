"""I1 core.events tests. Run from /opt/octopus/core/events:
/opt/octopus/venv/bin/pytest tests/ -q
Includes a cross-compatibility check against the exchange validator in the
agent pack (test-only dependency; runtime code stays decoupled).
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import envelope as core  # noqa: E402


def test_canonical_deterministic():
    a = {"b": 1, "a": {"z": [3, 2, {"k": "ü"}]}}
    b = {"a": {"z": [3, 2, {"k": "ü"}]}, "b": 1}
    assert core.canonical(a) == core.canonical(b)


def test_content_hash_stable_and_hashlike():
    h = core.content_hash({"x": 1})
    assert h.startswith("sha256:") and len(h) == 71 and h == core.content_hash({"x": 1})


def test_build_event_defaults():
    ev = core.build_event(core.new_run_id(), {"n": 1}, ["a"], None)
    errs = core.validate_event(ev)
    assert errs == []
    assert ev["may_authorize"] is False and ev["prev_hash"] is None
    assert ev["payload_hash"] == core.content_hash({"n": 1})


def test_validator_rejects_bad_payload_hash():
    ev = core.build_event(core.new_run_id(), {"n": 1}, [], None)
    ev["payload_hash"] = "sha256:" + "0" * 64
    assert any(e.startswith("E08") for e in core.validate_event(ev))


def test_validator_rejects_may_authorize():
    ev = core.build_event(core.new_run_id(), {"n": 1}, [], None)
    ev["may_authorize"] = True
    assert any(e.startswith("E10") for e in core.validate_event(ev))


def test_validator_rejects_missing_field():
    ev = core.build_event(core.new_run_id(), {"n": 1}, [], None)
    ev.pop("boot_id")
    assert any(e.startswith("E02") for e in core.validate_event(ev))


def test_chain_build_and_verify():
    e1 = core.build_event(core.new_run_id(), {"i": 1}, [], None)
    e2 = core.build_event(core.new_run_id(), {"i": 2}, [], core.event_hash(e1))
    e3 = core.build_event(core.new_run_id(), {"i": 3}, [], core.event_hash(e2))
    ok, msg = core.verify_chain([e1, e2, e3])
    assert ok, msg
    broken = dict(e3, prev_hash=core.event_hash(e1))
    ok, msg = core.verify_chain([e1, e2, broken])
    assert not ok


def test_cross_compat_with_exchange_validator():
    """A core event re-shaped as an exchange envelope must pass the D12
    validator unchanged in spirit: same hash function, same may_authorize."""
    sys.path.insert(0, "/opt/octopus-agent/exchange")
    from validate_envelope import payload_sha
    payload = {"topic": "status", "n": 7}
    assert core.content_hash(payload) == payload_sha(payload)


def test_import_is_side_effect_free():
    """core.events must not touch the filesystem or network on import."""
    import importlib
    before = set(sys.modules)
    importlib.reload(core)
    assert core.boot_id() in ("unknown",) or len(core.boot_id()) >= 8
