#!/usr/bin/env python3
"""Security and determinism contract for digest-only Test Intelligence traces."""
from __future__ import annotations

import json
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_OPS = _HERE.parent
sys.path.insert(0, str(_OPS))

import harness  # noqa: E402
ENV = harness.setup("ti-trace-contract")

from test_intelligence.trace_schema import (  # noqa: E402
    SCHEMA, TraceEvent, TraceSink, digest, make_event, trace_shape,
)

ROOT = Path(ENV["root"])


def _event(event_id="ev-1"):
    return make_event(
        trace_id="tr-1", event_id=event_id,
        component="octopus.test.router", kind="decision", status="blocked",
        inputs={"prompt": "synthetic private input", "chat_id": "fixture-chat"},
        outputs={"reply": "synthetic private output"},
        attempted=True, authorized=False, executed=False,
        tool_calls=[{"tool": "send", "args": "private"}],
        state_mutations=[{"store": "memory", "value": "private"}],
        reason_code="policy-blocked", now=123.0)


def t_a_digest_is_stable_and_value_sensitive():
    assert digest({"b": 2, "a": 1}) == digest({"a": 1, "b": 2})
    assert digest({"a": 1}) != digest({"a": 2})
    assert digest({"a": 1}).startswith("sha256:")


def t_b_raw_values_never_enter_the_record():
    blob = json.dumps(_event().as_record(), ensure_ascii=False)
    for forbidden in ("synthetic private input", "fixture-chat",
                      "synthetic private output", '"value": "private"'):
        assert forbidden not in blob
    assert blob.count("sha256:") >= 4


def t_c_attempt_authorize_execute_are_independent():
    event = _event()
    assert event.attempted is True
    assert event.authorized is False
    assert event.executed is False
    assert event.validate() == []


def t_d_execution_without_authorization_is_invalid():
    bad = TraceEvent("tr", "ev", "octopus.test", "decision", "ok",
                     digest("in"), digest("out"), attempted=True,
                     authorized=False, executed=True)
    assert "executed-without-authorization" in bad.validate()


def t_e_authorization_without_attempt_is_invalid():
    bad = TraceEvent("tr", "ev", "octopus.test", "decision", "ok",
                     digest("in"), digest("out"), attempted=False,
                     authorized=True, executed=False)
    assert "authorized-without-attempt" in bad.validate()


def t_f_sink_appends_and_never_truncates():
    path = ROOT / "traces" / "events.jsonl"
    sink = TraceSink(path)
    sink.append(_event("ev-1"))
    first = path.read_bytes()
    sink.append(_event("ev-2"))
    second = path.read_bytes()
    assert second.startswith(first)
    assert len(second.splitlines()) == 2


def t_g_shape_is_content_free_and_snapshot_stable():
    shape = trace_shape(_event().as_record())
    assert shape == {
        "schema": SCHEMA,
        "component": "octopus.test.router",
        "kind": "decision",
        "status": "blocked",
        "attempted": True,
        "authorized": False,
        "executed": False,
        "tool_call_count": 1,
        "state_mutation_count": 1,
        "reason_code": "policy-blocked",
    }


def t_h_invalid_namespace_is_digest_mapped_not_echoed():
    raw = "not allowed / private path"
    event = make_event(trace_id="tr", event_id="ev", component=raw,
                       kind="decision", status="ok", inputs=None, outputs=None)
    assert event.component.startswith("octopus.digest-")
    assert raw not in json.dumps(event.as_record())


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'OK' if not failed else 'FAIL'} test_ti_trace_contract: "
          f"{len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
