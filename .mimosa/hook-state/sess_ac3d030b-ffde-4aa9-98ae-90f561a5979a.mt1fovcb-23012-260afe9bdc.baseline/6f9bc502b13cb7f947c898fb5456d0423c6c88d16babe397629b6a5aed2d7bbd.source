#!/usr/bin/env python3
"""test_d5_halt_integration — D5: the combined halt scenario, deterministic virtual time.

The D5 acceptance scenario from the phase-0 plan, end to end in one hermetic run:
  1. normal controlled activity works (request → exact release → claim → receipt → settled);
  2. raise the sandbox HALT-ALL;
  3. advance "virtual time" beyond scheduler/watchdog intervals (deterministic timestamp
     backdating — no wall-clock sleeps) and poke every schedule-driven entry point:
     model router, watchdog, effector lane, sweeps;
  4. model/provider calls, releases, claims, settles, revivals all stay at ZERO —
     and the settled-count is bit-identical before/after the halted window;
  5. the in-flight effect cannot duplicate (its completion under halt becomes
     RECONCILE_REQUIRED — recorded once, executed zero extra times);
  6. clear ONLY the sandbox halt flag;
  7. clean recovery: watchdog may revive, a fresh effect flows end-to-end, and the
     reconcile lane resolves the interrupted effect with evidence.

Run: python -X utf8 test_d5_halt_integration.py
"""
import sys
import time
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent))
sys.path.insert(0, str(_HERE.parent / "budget"))
sys.path.insert(0, str(_HERE.parent / "cortex"))
import harness   # noqa: E402
ENV = harness.setup("d5-halt-integration")
import chrono    # noqa: E402
import opslib    # noqa: E402
import watchdog  # noqa: E402
import model_router  # noqa: E402

_FAILED = 0


def check(name, cond):
    global _FAILED
    print(("PASS" if cond else "FAIL"), "-", name)
    if not cond:
        _FAILED += 1


def _appr(db, eid, aid):
    r = db.q("SELECT content_hash, action_kind, target_ref FROM gated_effect "
             "WHERE effect_id=?", (eid,))[0]
    return {"effect_id": eid, "approval_id": aid, "content_hash": r[0],
            "action_kind": r[1], "target_ref": r[2], "expires_at": None,
            "release_ref": "ref-" + str(aid)}


def _settled_count(db):
    return db.q("SELECT COUNT(*) FROM gated_effect WHERE status='settled'")[0][0]


def _ms_ago(hours):
    return int((time.time() - hours * 3600) * 1000)


db = chrono.ChronoDB(path=opslib.STATE_DIR / "d5.db")
gate = chrono.EffectorGate(db)

# ── phase 1: normal controlled activity works ───────────────────────────────────
e1 = gate.request("pay", "d5-normal", target_ref="acct-1")
assert gate.release_effect(e1, _appr(db, e1, "A-1")) is True
x1 = gate.begin_execution(e1, worker_ref="W1")
check("phase1: full lane works before halt (request→release→claim→receipt→settled)",
      gate.complete_execution(e1, x1, "RCPT-1") is True and gate.status_of(e1) == "settled")

# staged state for the halted window: one in-flight, one authorized, one pending
e_fly = gate.request("pay", "d5-fly", target_ref="acct-2")
assert gate.release_effect(e_fly, _appr(db, e_fly, "A-2")) is True
x_fly = gate.begin_execution(e_fly, worker_ref="W2")
e_auth = gate.request("pay", "d5-auth", target_ref="acct-3")
assert gate.release_effect(e_auth, _appr(db, e_auth, "A-3")) is True
e_new = gate.request("send", "d5-pending", target_ref="chan")

settled_before = _settled_count(db)

# ── phase 2: raise the sandbox HALT-ALL ─────────────────────────────────────────
opslib.HALT_ALL.parent.mkdir(parents=True, exist_ok=True)
opslib.HALT_ALL.write_text("D5", "utf-8")
try:
    # ── phase 3: advance virtual time + poke every schedule-driven entry ────────
    db.ex("UPDATE gated_effect SET execution_started_at=? WHERE effect_id=?",
          (_ms_ago(100), e_fly))
    db.ex("UPDATE gated_effect SET approved_at=? WHERE effect_id=?",
          (_ms_ago(100), e_auth))
    db.ex("UPDATE gated_effect SET created_ts=? WHERE effect_id=?",
          (_ms_ago(100), e_new))

    r = model_router.ask("think", "poke")
    check("phase3: model router refuses (zero provider calls)",
          r.get("ok") is False and r.get("reason") == "kill-switch")

    should, reason = watchdog.should_revive(port_alive=False, state_exists=True)
    check("phase3: watchdog yields under HALT-ALL (zero revivals)",
          should is False and "yield" in reason)

    check("phase3: no new authorization (release under halt refused)",
          gate.release_gated_effects({"hash": "h"}) == 0
          and gate.status_of(e_new) == "pending")
    check("phase3: no new claim (authorized effect refused, fail-closed)",
          gate.begin_execution(e_auth) is None)
    check("phase3: no settle under halt", gate.settle(e_auth) is False)

    # ── phase 4/5: in-flight cannot duplicate; settled-count frozen ─────────────
    check("phase5: in-flight completion under halt → RECONCILE_REQUIRED once",
          gate.complete_execution(e_fly, x_fly, "RCPT-FLY") is False
          and gate.status_of(e_fly) == "RECONCILE_REQUIRED")
    check("phase5: repeated stale completion attempts change nothing",
          gate.complete_execution(e_fly, x_fly, "RCPT-FLY") is False
          and gate.status_of(e_fly) == "RECONCILE_REQUIRED")
    check("phase4: settled-count bit-identical across the halted window",
          _settled_count(db) == settled_before)
finally:
    # ── phase 6: clear ONLY the sandbox halt ────────────────────────────────────
    opslib.HALT_ALL.unlink(missing_ok=True)

# ── phase 7: clean recovery ─────────────────────────────────────────────────────
should, reason = watchdog.should_revive(port_alive=False, state_exists=True)
check("phase7: watchdog may revive after halt clears", should is True)

e2 = gate.request("pay", "d5-recovery", target_ref="acct-9")
assert gate.release_effect(e2, _appr(db, e2, "A-9")) is True
x2 = gate.begin_execution(e2, worker_ref="W9")
check("phase7: fresh effect flows end-to-end after recovery",
      gate.complete_execution(e2, x2, "RCPT-9") is True and gate.status_of(e2) == "settled")
check("phase7: interrupted effect resolves through the reconcile lane (no duplicate)",
      gate.reconcile_effect(e_fly, "settled", "BANK-EV-FLY", "owner") is True
      and db.q("SELECT external_receipt_ref FROM gated_effect WHERE effect_id=?",
               (e_fly,))[0][0] == "RCPT-FLY")


if __name__ == "__main__":
    print(f"\n== {_FAILED} failure(s) ==")
    print("OK test_d5_halt_integration" if _FAILED == 0 else "FAIL test_d5_halt_integration")
    sys.exit(1 if _FAILED else 0)
