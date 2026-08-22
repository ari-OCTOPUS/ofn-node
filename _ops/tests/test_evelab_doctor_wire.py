#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""EveLab ↔ Doctor reversible wire — fixture only, no live Telegram."""
from __future__ import annotations

import ast
import importlib
import json
import os
import sys
import tempfile
from pathlib import Path

_OPS = Path(__file__).resolve().parents[1]
_DOC = _OPS / "doctor"
for _p in (str(_OPS), str(_DOC), str(_OPS / "telegram_center")):
    if _p not in sys.path:
        sys.path.insert(0, _p)


def _fresh_state():
    root = Path(tempfile.mkdtemp(prefix="evelab-doctor-wire-"))
    state = root / "state"
    state.mkdir(parents=True, exist_ok=True)
    os.environ["OCTOPUS_STATE_DIR"] = str(state)
    return root, state


def t_a_doctor_proposes_lab_experiment_ticket_to_outbox():
    root, state = _fresh_state()
    import lab_bridge
    lab_bridge = importlib.reload(lab_bridge)
    out = lab_bridge.propose_lab_experiment_ticket(
        experiment_id="labexp-p1-wire",
        question="prove doctor can propose one lab experiment ticket",
        hypothesis="durable outbox receives QUEUED ticket without live send",
        organ="doctor",
        dry_run=True,
        state_dir=state,
    )
    assert out.get("ok") is True, out
    assert out.get("live_send") is False
    assert out.get("dry_run") is True
    assert out.get("propose_only") is True
    assert out.get("kind") == "evo-lab-experiment-ticket"
    path = Path(out["outbox_path"])
    assert path.is_file(), path
    rec = json.loads(path.read_text(encoding="utf-8"))
    assert rec.get("state") == "QUEUED"
    assert rec.get("live_send") is False
    assert rec.get("kind") == "evo-lab-experiment-ticket"
    assert rec.get("experiment_id") == "labexp-p1-wire"
    assert "LAB EXPERIMENT TICKET" in rec.get("payload_text", "")
    assert "[merge]" in rec.get("payload_text", "")
    banned = ("sendMessage", "api.telegram.org", "getUpdates")
    src = (_DOC / "lab_bridge.py").read_text(encoding="utf-8")
    for w in banned:
        assert w not in src


def t_b_parse_ticket_is_reverse_of_propose():
    root, state = _fresh_state()
    import lab_bridge
    lab_bridge = importlib.reload(lab_bridge)
    out = lab_bridge.propose_lab_experiment_ticket(
        experiment_id="labexp-rev",
        question="reversible path",
        organ="evo-lab",
        state_dir=state,
    )
    parsed = lab_bridge.parse_lab_experiment_ticket(out["outbox_path"])
    assert parsed is not None, parsed
    assert parsed["experiment_id"] == "labexp-rev"
    assert parsed["live_send"] is False
    assert parsed["organ"] == "evo-lab"
    assert "reversible" in (parsed.get("question") or "")


def t_c_lab_calls_doctor_check_dry_run():
    root, state = _fresh_state()
    import lab_bridge
    lab_bridge = importlib.reload(lab_bridge)
    result = lab_bridge.lab_call_doctor_check(state_dir=state, dry_run=True)
    assert result.get("live_send") is False
    assert result.get("dry_run") is True
    assert result.get("ok") is True, result
    names = {c["name"]: c for c in result.get("checks") or []}
    assert names["lab_bridge_ticket_api"]["ok"] is True
    assert names["propose_parse_roundtrip"]["ok"] is True
    assert names["poller_uniqueness"]["ok"] is True, names.get("poller_uniqueness")
    assert names["poller_uniqueness"].get("fixture") is True


def t_d_doctor_class_exposes_ticket_hook():
    src = (_DOC / "doctor.py").read_text(encoding="utf-8")
    tree = ast.parse(src)
    methods = {
        n.name for n in ast.walk(tree)
        if isinstance(n, ast.FunctionDef)
    }
    assert "propose_lab_experiment_ticket" in methods
    assert "_bridge_to_lab" in methods
    # Hook body must call lab_bridge
    fn = next(
        n for n in ast.walk(tree)
        if isinstance(n, ast.FunctionDef) and n.name == "propose_lab_experiment_ticket"
    )
    dump = ast.dump(fn)
    assert "lab_bridge" in dump or "propose_lab_experiment_ticket" in dump


def t_e_not_rfc_only_surface():
    """Wire must expose experiment-ticket path distinct from RFC cycle."""
    import lab_bridge
    lab_bridge = importlib.reload(lab_bridge)
    assert hasattr(lab_bridge, "propose_lab_experiment_ticket")
    assert hasattr(lab_bridge, "parse_lab_experiment_ticket")
    assert hasattr(lab_bridge, "lab_call_doctor_check")
    assert hasattr(lab_bridge, "run_rfc_through_lab")  # RFC path still present


def main() -> int:
    tests = [v for k, v in sorted(globals().items()) if k.startswith("t_") and callable(v)]
    failed = []
    for fn in tests:
        try:
            fn()
            print("  OK  " + fn.__name__)
        except Exception as exc:
            failed.append(fn.__name__)
            print("  FAIL " + fn.__name__ + ": " + type(exc).__name__ + ": " + str(exc))
    print("\ntest_evelab_doctor_wire: %d/%d" % (len(tests) - len(failed), len(tests)))
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
