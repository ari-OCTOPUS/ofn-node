#!/usr/bin/env python3
"""Offline, hermetic test for M1 (now_moves/ledger_integrity_probe).

Stdlib-only · no network · NO live-state writes (OPS_DIR/ORG_ROOT redirected to a
tmp dir at import; the emit test additionally redirects events.LOG). Builds
synthetic ledgers with the REAL genome Ledger class and checks:
  clean / scarred / broken detection · flag-OFF no-op · incident emission.
Runs standalone (python test_ledger_integrity_probe.py → exit 0/1), matching the
run_all.py subprocess convention; also exposes test_* functions.
"""
import importlib.util
import json
import os
import sys
import tempfile
from pathlib import Path

# ── isolate any accidental state write to a tmp tree BEFORE importing events ──
_TMPBASE = tempfile.mkdtemp(prefix="m1_ledgerprobe_")
os.environ["ORG_ROOT"] = _TMPBASE
os.environ["OPS_DIR"] = str(Path(_TMPBASE) / "_ops")
os.environ.pop("OCTOPUS_WIRE_LEDGER_PROBE", None)      # ensure flag OFF by default

HERE = Path(__file__).resolve().parent                 # _ops/tests
OPS = HERE.parent                                      # _ops
ROOT = OPS.parent                                      # repo root
for _p in (str(OPS / "now_moves"), str(OPS), str(OPS / "budget")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import ledger_integrity_probe as P                      # noqa: E402


def _Ledger():
    py = ROOT / "07 - Knowledge" / "genome-system" / "ledger" / "ledger.py"
    spec = importlib.util.spec_from_file_location("_lg_test", str(py))
    m = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = m               # required before exec: @dataclass reads sys.modules[__module__]
    spec.loader.exec_module(m)
    return m.Ledger


def _clean(path, n=5):
    lg = _Ledger()(path)
    for i in range(n):
        lg.append("OBSERVE", {"i": i}, actor="test")
    return path


def _tamper(path, idx=2, payload=None):
    lines = Path(path).read_text("utf-8").splitlines()
    rec = json.loads(lines[idx]); rec["payload"] = payload or {"z": 1}
    lines[idx] = json.dumps(rec, ensure_ascii=False)
    Path(path).write_text("\n".join(lines) + "\n", "utf-8")
    return path


def _clear_baseline():
    bp = P._baseline_path()
    if bp and bp.exists():
        bp.unlink()


def _redirect_events(d):
    import events
    events.LOG = Path(d) / "events.jsonl"
    return events.LOG


def test_clean():
    with tempfile.TemporaryDirectory() as d:
        p = _clean(Path(d) / "ledger.jsonl")
        v = P.verify_ledger(p)
        assert v["verdict"] == "clean", v
        assert v["ok"] is True and v["strict_ok"] is True, v
    print("  ok clean chain            -> verdict=clean, ok=True")


def test_broken():
    with tempfile.TemporaryDirectory() as d:
        p = _clean(Path(d) / "ledger.jsonl")
        lines = Path(p).read_text("utf-8").splitlines()
        rec = json.loads(lines[2]); rec["payload"] = {"i": 999}    # tamper, hash now wrong
        lines[2] = json.dumps(rec, ensure_ascii=False)
        Path(p).write_text("\n".join(lines) + "\n", "utf-8")
        v = P.verify_ledger(p)
        assert v["verdict"] == "broken" and v["ok"] is False, v
        assert v["scar_ok"] is False, v
    print("  ok tampered chain         -> verdict=broken, ok=False")


def test_scarred():
    with tempfile.TemporaryDirectory() as d:
        p = _clean(Path(d) / "ledger.jsonl")
        lines = Path(p).read_text("utf-8").splitlines()
        h2 = json.loads(lines[2])["hash"]              # record idx3 chains to this hash
        lines[2] = '{"id": "torn", "payload": {oops ' + h2   # torn but anchored to h2
        Path(p).write_text("\n".join(lines) + "\n", "utf-8")
        v = P.verify_ledger(p)
        assert v["strict_ok"] is False, v              # strict verify fails
        assert v["scar_ok"] is True, v                 # scar-aware salvages the anchor
        assert v["verdict"] == "scarred" and v["ok"] is True, v
    print("  ok torn-but-anchored      -> verdict=scarred (scar-aware OK)")


def test_flag_off_noop():
    os.environ.pop("OCTOPUS_WIRE_LEDGER_PROBE", None)
    assert P.on_beat(999999) is None                   # flag OFF => no import, no probe
    print("  ok flag OFF               -> on_beat() no-op (None)")


def test_emit_incident():
    _clear_baseline()
    with tempfile.TemporaryDirectory() as d:
        p = _tamper(_clean(Path(d) / "ledger.jsonl"))
        ev_log = _redirect_events(d)
        v = P.probe(emit=True, ledger_path=p)
        assert v["verdict"] == "broken" and v["emitted"] is True, v
        blob = ev_log.read_text("utf-8")
        assert "incident.opened" in blob, blob
        assert '"R4"' in blob and '"approval_state": "required"' in blob, blob
    print("  ok broken + emit=True     -> incident.opened (R4, approval=required)")


def test_baseline_suppresses_repeat():
    _clear_baseline()
    with tempfile.TemporaryDirectory() as d:
        p = _tamper(_clean(Path(d) / "ledger.jsonl"))
        ev_log = _redirect_events(d)
        v1 = P.probe(emit=True, ledger_path=p)          # first sight → emits
        n1 = ev_log.read_text("utf-8").count("incident.opened")
        v2 = P.probe(emit=True, ledger_path=p)          # same state → must NOT re-emit
        n2 = ev_log.read_text("utf-8").count("incident.opened")
        assert v1["emitted"] is True and n1 == 1, (v1, n1)
        assert v2["emitted"] is False and n2 == 1, (v2, n2)
    print("  ok same state twice       -> emits once, then silent (no alarm fatigue)")


def test_worsening_reemits():
    _clear_baseline()
    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / "ledger.jsonl"
        _clean(p)
        lines = p.read_text("utf-8").splitlines()
        h2 = json.loads(lines[2])["hash"]
        lines[2] = '{"id": "torn", "payload": {oops ' + h2       # scarred (torn-but-anchored)
        p.write_text("\n".join(lines) + "\n", "utf-8")
        ev_log = _redirect_events(d)
        v1 = P.probe(emit=True, ledger_path=p)
        assert v1["verdict"] == "scarred" and v1["emitted"] is True, v1
        _tamper(p, idx=3)                                # now also tamper → broken (worse)
        v2 = P.probe(emit=True, ledger_path=p)
        assert v2["verdict"] == "broken" and v2["emitted"] is True, v2
        assert ev_log.read_text("utf-8").count("incident.opened") == 2
    print("  ok worsening scar->break  -> re-emits (severity escalation detected)")


def test_acknowledge_suppresses():
    _clear_baseline()
    with tempfile.TemporaryDirectory() as d:
        p = _tamper(_clean(Path(d) / "ledger.jsonl"))
        ev_log = _redirect_events(d)
        a = P.acknowledge(ledger_path=p)                # owner accepts current state
        assert a["verdict"] == "broken" and a["acknowledged"] is True, a
        v = P.probe(emit=True, ledger_path=p)           # already accepted → no incident
        assert v["emitted"] is False, v
        assert not ev_log.exists() or "incident.opened" not in ev_log.read_text("utf-8")
    print("  ok acknowledge then probe -> accepted state stays silent")


def _run():
    tests = [test_clean, test_broken, test_scarred, test_flag_off_noop,
             test_emit_incident, test_baseline_suppresses_repeat,
             test_worsening_reemits, test_acknowledge_suppresses]
    print("test_ledger_integrity_probe (M1) — offline, hermetic")
    for t in tests:
        t()
    print(f"PASS {len(tests)}/{len(tests)}")


if __name__ == "__main__":
    try:
        _run()
    except AssertionError as e:
        print("FAIL:", e); sys.exit(1)
    except Exception as e:  # noqa: BLE001
        print("ERROR:", type(e).__name__, e); sys.exit(1)
    sys.exit(0)
