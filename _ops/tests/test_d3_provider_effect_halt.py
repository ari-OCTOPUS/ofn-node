#!/usr/bin/env python3
"""test_d3_provider_effect_halt — D3: providers/external effects under the GLOBAL halt.

Proves (hermetic, fixture-only; HALT-ALL is the sandbox vault's, never the live one):
  * model_router.ask under HALT-ALL and under architect-STOP → {"ok": False,
    "reason": "kill-switch"} — zero provider/model calls.
  * ps_writeback.flush with its wire-flag ON but HALT active → honest no-op,
    zero writes, queue untouched.
  * The FULL EffectorGate authorization/execution lane refuses under HALT-ALL
    (supreme flag, not just STOP-ORGANISM): release_effect, release_one,
    release_gated_effects (D3 defense-in-depth added), begin_execution, settle,
    reconcile_effect, redrive_approval. complete_execution of an in-flight
    effect under halt → RECONCILE_REQUIRED (honest, never a fake refuse).

Run: python -X utf8 test_d3_provider_effect_halt.py
"""
import os
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent))
sys.path.insert(0, str(_HERE.parent / "budget"))
sys.path.insert(0, str(_HERE.parent / "cortex"))
sys.path.insert(0, str(_HERE.parent / "legs"))
import harness   # noqa: E402
ENV = harness.setup("d3-provider-effect-halt")
import chrono    # noqa: E402
import opslib    # noqa: E402

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


class _halt:
    """context manager: پرچمِ halt سراسریِ sandbox را بالا می‌برد و همیشه پاک می‌کند."""

    def __init__(self, flag):
        self.flag = flag

    def __enter__(self):
        self.flag.parent.mkdir(parents=True, exist_ok=True)
        self.flag.write_text("test", "utf-8")

    def __exit__(self, *a):
        self.flag.unlink(missing_ok=True)


# ── 1) model_router: zero model calls under global halt ─────────────────────────
import model_router  # noqa: E402

with _halt(opslib.HALT_ALL):
    r = model_router.ask("think", "hello")
    check("model_router.ask under HALT-ALL → kill-switch, no call",
          r.get("ok") is False and r.get("reason") == "kill-switch")
with _halt(opslib.STOP_ARCHITECT):
    r = model_router.ask("think", "hello")
    check("model_router.ask under architect STOP → kill-switch, no call",
          r.get("ok") is False and r.get("reason") == "kill-switch")

# ── 2) ps_writeback: wire-flag ON + halt → honest no-op, queue untouched ────────
import ps_writeback  # noqa: E402

os.environ[ps_writeback.FLAG] = "1"
try:
    with _halt(opslib.HALT_ALL):
        r = ps_writeback.flush()
        check("ps_writeback.flush under HALT-ALL → zero writes, queue untouched",
              r.get("ok") is False and r.get("written") == 0
              and "HALT" in str(r.get("note", "")))
finally:
    os.environ.pop(ps_writeback.FLAG, None)

# ── 3) EffectorGate lane under HALT-ALL (supreme flag) ──────────────────────────
db = chrono.ChronoDB(path=opslib.STATE_DIR / "d3.db")
gate = chrono.EffectorGate(db)

# in-flight BEFORE halt (claimed via the healthy path)
e_fly = gate.request("pay", "order-fly", target_ref="acct-fly")
assert gate.release_effect(e_fly, _appr(db, e_fly, "A-FLY")) is True
x_fly = gate.begin_execution(e_fly, worker_ref="W")

# candidates for refusal under halt
e_pend = gate.request("pay", "order-p", target_ref="acct-p")
e_send = gate.request("send", "internal-p", target_ref="chan")
e_one = gate.request("lead_outbound", "cust-p", target_ref="cust")
e_rel = gate.request("pay", "order-rel", target_ref="acct-rel")
assert gate.release_effect(e_rel, _appr(db, e_rel, "A-REL")) is True

with _halt(opslib.HALT_ALL):
    check("release_effect under HALT-ALL → False + refused",
          gate.release_effect(e_pend, _appr(db, e_pend, "A-H")) is False
          and gate.status_of(e_pend) == "refused")
    check("release_one under HALT-ALL → False (D3 defense-in-depth)",
          gate.release_one(e_one, {"hash": "h"}) is False
          and gate.status_of(e_one) == "pending")
    check("release_gated_effects under HALT-ALL → 0 released",
          gate.release_gated_effects({"hash": "h"}) == 0
          and gate.status_of(e_send) == "pending")
    check("begin_execution under HALT-ALL → None + refused",
          gate.begin_execution(e_rel) is None and gate.status_of(e_rel) == "refused")
    check("settle under HALT-ALL → False",
          gate.settle(e_rel) is False)
    check("complete_execution of in-flight under HALT-ALL → RECONCILE_REQUIRED",
          gate.complete_execution(e_fly, x_fly, "RCPT-FLY") is False
          and gate.status_of(e_fly) == "RECONCILE_REQUIRED")
    check("reconcile_effect under HALT-ALL → False (no reconciliation under halt)",
          gate.reconcile_effect(e_fly, "settled", "EV", "owner") is False
          and gate.status_of(e_fly) == "RECONCILE_REQUIRED")
    e_rd = gate.request("pay", "order-rd", target_ref="acct-rd")
    check("redrive_approval under HALT-ALL → False",
          chrono.redrive_approval(_appr(db, e_rd, "A-RD"), "H-RD", gate) is False
          and gate.status_of(e_rd) == "pending")

# recovery after clearing the halt: the lane works again
check("after halt clear: reconcile works again",
      gate.reconcile_effect(e_fly, "settled", "BANK-EV", "owner") is True
      and gate.status_of(e_fly) == "settled")


if __name__ == "__main__":
    print(f"\n== {_FAILED} failure(s) ==")
    print("OK test_d3_provider_effect_halt" if _FAILED == 0
          else "FAIL test_d3_provider_effect_halt")
    sys.exit(1 if _FAILED else 0)
