#!/usr/bin/env python3
"""Paired test for RUN-TO-COMPLETION item 3 — provider attribution + per-provider cap.

RED before patch_budget_attribution.py (no PROVIDER_ATTRIBUTION_REQUIRED, settle
rows unnamed, no cap), GREEN after. No network, no secrets; ledger + contract
redirected to a tmp dir. Convention follows tests/test_provider_failover.py.
"""
import importlib.util
import json
import shutil
import sys
import tempfile
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
SRC = HERE.parent / "api_budget.py"
spec = importlib.util.spec_from_file_location("ab", SRC)
ab = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ab)

PASS, FAIL = [], []


def check(name, ok, detail=""):
    print(("PASS" if ok else "FAIL"), name, detail if not ok else "")
    (PASS if ok else FAIL).append(name)


tmp = Path(tempfile.mkdtemp(prefix="ab-attrib-"))
ab.ROOT = tmp
ab.LEDGER = tmp / "budget-ledger.jsonl"
ab.LOCK = tmp / "broker.lock"
cfg = tmp / "config"
cfg.mkdir(parents=True)
ab.CONTRACT = cfg / "api-budget-contract.json"
ab.CONTRACT.write_text(json.dumps({
    "schema": "octopus.api-budget.v1", "currency": "USD",
    "budget_epoch_start_utc": "2026-09-01T00:00:00+00:00",
    "max_calls_per_task": 50, "max_usd_per_task": 10.0,
    "max_usd_monthly": 100.0, "per_provider_cap_usd_24h": 0.25,
}), encoding="utf-8")
ab.LOCK.write_text("", encoding="utf-8")
ab.LEDGER.write_text("", encoding="utf-8")
now = time.time()


def rows():
    return [json.loads(l) for l in ab.LEDGER.read_text(encoding="utf-8")
            .splitlines() if l.strip()]


# -- T1: unnamed provider refused, nothing recorded --------------------------
n0 = len(rows())
r = ab.reserve("t-attrib", "unit-test", 100, 50, "test", provider=None, model="m", now=now)
check("T1 reserve(provider=None) refused",
      r.get("error") == "PROVIDER_ATTRIBUTION_REQUIRED", str(r))
r = ab.reserve("t-attrib", "unit-test", 100, 50, "test", provider="unknown", model="m", now=now)
check("T1b provider='unknown' refused",
      r.get("error") == "PROVIDER_ATTRIBUTION_REQUIRED", str(r))
r = ab.reserve("t-attrib", "unit-test", 100, 50, "test", provider="   ", model="m", now=now)
check("T1c blank provider refused",
      r.get("error") == "PROVIDER_ATTRIBUTION_REQUIRED", str(r))
check("T1d no rows recorded for refused reserves", len(rows()) == n0)

# -- T2: settle rows carry the provider --------------------------------------
r = ab.reserve("t-p1a", "unit-test", 2400, 1000, "test", provider="prov-a", model="m", now=now)
check("T2a reserve prov-a ok", r.get("ok") is True, str(r))
s = ab.settle(r["request_id"], 2400, 1000, 0.5, "deadbeef", True, "")
check("T2b settle ok", s.get("ok") is True, str(s))
last = rows()[-1]
check("T2c settle row attributed",
      last.get("kind") == "settle" and last.get("provider") == "prov-a",
      str(last.get("provider")))

# -- T3: per-provider rolling cap 0.25 (prov-a already at 0.10 settled) ------
r = ab.reserve("t-p1b", "unit-test", 2400, 1000, "test", provider="prov-a", model="m", now=now)
check("T3a second prov-a ok (0.10+0.10<=0.25)", r.get("ok") is True, str(r))
s = ab.settle(r["request_id"], 2400, 1000, 0.5, "deadbeef", True, "")
check("T3a2 settle ok", s.get("ok") is True, str(s))
r = ab.reserve("t-p1c", "unit-test", 2400, 1000, "test", provider="prov-a", model="m", now=now)
check("T3b third prov-a capped",
      r.get("error") == "PROVIDER_CAP_REACHED", str(r))
check("T3b2 error names the provider", r.get("provider") == "prov-a", str(r))
r = ab.reserve("t-p2a", "unit-test", 2400, 1000, "test", provider="prov-b", model="m", now=now)
check("T3c other provider not blocked", r.get("ok") is True, str(r))

# -- T4: default cap 0.25 applies without the contract key -------------------
c = json.loads(ab.CONTRACT.read_text(encoding="utf-8"))
c.pop("per_provider_cap_usd_24h", None)
ab.CONTRACT.write_text(json.dumps(c), encoding="utf-8")
r = ab.reserve("t-p1d", "unit-test", 2400, 1000, "test", provider="prov-a", model="m", now=now)
check("T4 default 0.25 without contract key",
      r.get("error") == "PROVIDER_CAP_REACHED", str(r))

# -- T5: chain still valid + zero unnamed new rows ---------------------------
try:
    ab._rows()
    check("T5 hash chain valid after new rows", True)
except ValueError as e:
    check("T5 hash chain valid after new rows", False, str(e))
unnamed = [x for x in rows() if x.get("kind") in ("reserve", "settle")
           and not x.get("provider")]
check("T5b zero unnamed reserve/settle rows", not unnamed, str(unnamed[:1]))

shutil.rmtree(tmp, ignore_errors=True)
print(f"-- {len(PASS)} checks, {len(FAIL)} failed")
sys.exit(1 if FAIL else 0)
