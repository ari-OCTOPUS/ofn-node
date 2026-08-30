#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_blackbox_and_bridge.py — blackbox_scanner + romajan_bridge + heart_wires.

همه read-only / propose-only. $0, no network. از tempdir برای state استفاده می‌کند.
"""
import json
import os
import sys
import tempfile
from pathlib import Path

_TMP = tempfile.mkdtemp(prefix="bb-bridge-")
os.environ["OPS_DIR"] = str(Path(_TMP) / "_ops")
os.environ["OCTOPUS_WIRE_BLACKBOX_MAP"] = "1"
os.environ["OCTOPUS_WIRE_ROMAJAN_PROBES"] = "1"
os.environ["OCTOPUS_WIRE_IDENTITY_EQ"] = "1"
os.environ["OCTOPUS_WIRE_THESIS_QUEUE"] = "1"
os.environ["OCTOPUS_WIRE_COHERENCE"] = "1"
os.environ["OCTOPUS_WIRE_C6_PRODUCER"] = "1"
os.environ["OCTOPUS_WIRE_COLLAB_CODING"] = "1"
os.environ["ROMAJAN_LAB_PATH"] = str(Path(_TMP) / "romajan")

_HERE = Path(__file__).resolve().parent
_OPS = _HERE.parent
for _p in (str(_OPS), str(_OPS / "budget"), str(_OPS / "outcomes"),
           str(_OPS / "telegram_center")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

# mock opslib state for tests
import types as _types
_ol = _types.ModuleType("opslib")
_OPS_DIR = Path(_TMP) / "_ops"
_STATE_DIR = _OPS_DIR / "state"
_STATE_DIR.mkdir(parents=True, exist_ok=True)
_ol.OPS = _OPS_DIR
_ol.STATE_DIR = _STATE_DIR
_ol.alert = lambda msg: None
_ol.master_halted = lambda: None
_ol.STOP_ORGANISM = _OPS_DIR / "STOP-ORGANISM"
sys.modules["opslib"] = _ol

# create activation flag
(_OPS_DIR / "ACTIVATION-C6-RESEARCH.flag").write_text("1")

# create empty c6 queue
qd = _STATE_DIR / "c6"
qd.mkdir(parents=True, exist_ok=True)
(qd / "hypothesis-queue.jsonl").write_text("")

# create romajan mock ledger
rm = Path(os.environ["ROMAJAN_LAB_PATH"])
rm.mkdir(parents=True, exist_ok=True)
(rm / "propagation").mkdir(exist_ok=True)
(rm / "propagation" / "claims_ledger.json").write_text(
    json.dumps([
        {"id": "claim-001", "claim": "A000041 closed form rediscovered via PSLQ",
         "status": "verified", "evidence": "matched Ramanujan congruences"},
        {"id": "claim-002", "claim": "trivial interpolation",
         "status": "falsified", "evidence": "r²=0.12"},
        {"id": "claim-003", "claim": "Hardy-Ramanujan convergence rate measured",
         "status": "executed", "evidence": "n=1000, tol=1e-6"},
    ]),
    "utf-8",
)

fails = []


def check(cond, label):
    if not cond:
        fails.append(label)


# 1) blackbox scanner
import blackbox_scanner as bbs  # noqa: E402
rep = bbs.scan()
check(rep.get("ok") is True or "n" in rep, "scanner runs")
# should detect romajan-lab (from env) and maybe some dirs under F:\
# the scanner won't find much from a temp dir; that's OK — it must not crash
check(isinstance(rep.get("n"), int), "scanner returns n")


# 2) blackbox map
import blackbox_map as bm  # noqa: E402
cat = bm.survey()
check(cat["n"] >= 5, "catalog has 5+ entries")
check(any(i["id"] == "romajan_lab" for i in cat["items"]), "romajan in catalog")
check(any(i["id"] == "coherence_organ" for i in cat["items"]), "coherence organ")


# 3) romajan bridge
import romajan_bridge as rb  # noqa: E402
check(rb.enabled(), "romajan bridge enabled")
res = rb.sync()
check(res.get("ok") is True, f"romajan sync ok: {res}")
check(res.get("added", 0) >= 1, f"at least 1 claim added: {res}")
# re-sync should be idempotent
res2 = rb.sync()
check(res2.get("added", 0) == 0, f"idempotent re-sync: {res2}")
# queue should have rows
qrows = json.loads((_STATE_DIR / "c6" / "hypothesis-queue.jsonl").read_text()) if False else []
if (_STATE_DIR / "c6" / "hypothesis-queue.jsonl").exists():
    for ln in (_STATE_DIR / "c6" / "hypothesis-queue.jsonl").read_text("utf-8").splitlines():
        if ln.strip():
            d = json.loads(ln)
            check(d.get("kind") == "romajan_claim", "queue row is romajan_claim")
            check(d.get("romajan_claim_id") in ("claim-001", "claim-003"), "correct claim id")
    qrows = [json.loads(ln) for ln in
             (_STATE_DIR / "c6" / "hypothesis-queue.jsonl").read_text("utf-8").splitlines()
             if ln.strip()]


# 4) heart wires
import heart_wires as hw  # noqa: E402
hw.OUT = _STATE_DIR / "heart-wires-latest.json"
hw.opslib = _ol
beat = hw.beat(run_romajan=False)
check("thesis" in beat, "thesis wire in beat")
check("coherence" in beat, "coherence wire in beat")
check("identity" in beat, "identity wire in beat")
check("seed_killer" in beat, "seed killer in beat")


# 5) seed killer
# add seed to queue
(qd / "hypothesis-queue.jsonl").write_text(
    (qd / "hypothesis-queue.jsonl").read_text("utf-8") +
    json.dumps({"id": "seed-default", "source": "seed", "kind": "seed_default", "status": "PENDING"}) + "\n"
)
sk = hw.seed_killer_wire()
check(sk.get("deleted", 0) >= 1, f"seed killer deleted: {sk}")


# 6) collab coding flag-off safety
import collab_coding as cc  # noqa: E402
cc.STATE = _STATE_DIR / "collab"
cc.QUEUE = cc.STATE / "proposals.jsonl"
os.environ["OCTOPUS_WIRE_COLLAB_CODING"] = "0"
r = cc.propose("test flag off")
check(r.get("ok") is False and "flag-off" in r.get("reason", ""), "collab flag-off rejected")
os.environ["OCTOPUS_WIRE_COLLAB_CODING"] = "1"


# 7) identity equations
import identity_equations as ie  # noqa: E402
ie.STATE = _STATE_DIR
# with missing state, falls back gracefully
rpt = ie.evaluate({})
ids = rpt.get("identities") or {}
check(0.0 <= ids.get("organism", {}).get("value", 0) <= 1.0, "identity with empty signals")


# 8) live_commands routing
import live_commands as lc  # noqa: E402
for cmd in ("/live", "/id earner", "/box c6_live_loop", "/code propose add test"):
    out = lc.dispatch(cmd)
    check(len(out) > 20, f"dispatch '{cmd[:20]}...' returns text")


# 9) thesis queue register
import outcomes.thesis_queue as tq  # noqa: E402
tq._ledger_path = lambda *a, **kw: _STATE_DIR / "thesis" / "thesis-ledger.json"
check("identity-O" in tq.EXPERIMENT_REGISTRY, "identity-O registered")
check("lead-direct" in tq.EXPERIMENT_REGISTRY, "lead-direct registered")


print("FAIL" if fails else "PASS", f"— test_blackbox_and_bridge — {len(fails)} failures")
for f in fails:
    print("  -", f)
sys.exit(1 if fails else 0)
