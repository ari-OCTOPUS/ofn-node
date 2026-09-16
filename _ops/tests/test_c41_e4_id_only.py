#!/usr/bin/env python3
"""test_c41_e4_id_only — C4.1: close the E4 id-only single-effect authorization bypass.

C4 closed BATCH release of money, but left a hole: an id-only approval routed to
release_one() could release ONE money effect with only effect_id match (no content_hash/
action_kind/target_ref/expiry/anti-replay). C4.1 makes release_one REFUSE E4/money —
money is releasable ONLY via release_effect (exact binding + human ledger reference).

Architect invariant:  E4 + effect_id only  =>  ZERO AUTHORIZATION.

Run: python -X utf8 test_c41_e4_id_only.py
"""
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent))
sys.path.insert(0, str(_HERE.parent / "budget"))
import harness   # noqa: E402
ENV = harness.setup("c41-e4-id-only")
import chrono    # noqa: E402
import opslib    # noqa: E402

_FAILED = 0


def check(name, cond):
    global _FAILED
    print(("PASS" if cond else "FAIL"), "-", name)
    if not cond:
        _FAILED += 1


db = chrono.ChronoDB(path=opslib.STATE_DIR / "c41.db")
gate = chrono.EffectorGate(db)


def _appr(eid, *, approval_id, effect_id=None, content_hash=None, action_kind=None,
          target_ref=None, expires_at=None, release_ref="LEDGER-REF"):
    r = db.q("SELECT content_hash, action_kind, target_ref FROM gated_effect WHERE effect_id=?",
             (eid,))[0]
    return {"effect_id": eid if effect_id is None else effect_id, "approval_id": approval_id,
            "content_hash": r[0] if content_hash is None else content_hash,
            "action_kind": r[1] if action_kind is None else action_kind,
            "target_ref": r[2] if target_ref is None else target_ref,
            "expires_at": expires_at, "release_ref": release_ref}


# 1) E4 (pay) via release_one id-only → ZERO (the bypass, now closed)
e1 = gate.request("pay", "order-c41-1", target_ref="acct-1")
r1 = gate.release_one(e1, {"hash": "human-append-x"})
check("E4 id-only via release_one → False", r1 is False)
check("  money effect NOT released (stays pending)", gate.status_of(e1) == "pending")

# 2) E4 + wrong binding via release_effect → ZERO
e2 = gate.request("pay", "order-c41-2", target_ref="acct-2")
check("E4 wrong-binding via release_effect → False",
      gate.release_effect(e2, _appr(e2, approval_id="A-2", content_hash="WRONG")) is False)

# 3) E4 exact binding + valid ledger ref → ONE authorization
e3 = gate.request("pay", "order-c41-3", target_ref="acct-3")
check("E4 exact binding + ledger ref → True + releasable",
      gate.release_effect(e3, _appr(e3, approval_id="A-3")) is True
      and gate.status_of(e3) == "releasable")

# 4) non-E4 (lead_outbound) via release_one id-only → STILL WORKS (explicit non-E4 policy)
e4 = gate.request("lead_outbound", "cust-c41", target_ref="cust-1")
check("non-E4 lead_outbound via release_one id-only → True (releasable)",
      gate.release_one(e4, {"hash": "human-append-cust"}) is True
      and gate.status_of(e4) == "releasable")

# 5) unrelated/generic human append (no effect_id) → ZERO money released
e5 = gate.request("pay", "order-c41-5", target_ref="acct-5")
gate.release_gated_effects({"hash": "generic-append"})
check("generic append (no effect_id) → money stays pending", gate.status_of(e5) == "pending")

# 6) replayed approval_id → ZERO
e6a = gate.request("pay", "order-c41-6a", target_ref="acct-6")
e6b = gate.request("pay", "order-c41-6b", target_ref="acct-6")
gate.release_effect(e6a, _appr(e6a, approval_id="A-REPLAY-41"))
check("replayed approval_id on 2nd money effect → False",
      gate.release_effect(e6b, _appr(e6b, approval_id="A-REPLAY-41")) is False
      and gate.status_of(e6b) == "pending")

# 7) missing human ledger reference (release_ref empty) → ZERO
e7 = gate.request("pay", "order-c41-7", target_ref="acct-7")
check("missing human ledger reference (empty release_ref) → False",
      gate.release_effect(e7, _appr(e7, approval_id="A-7", release_ref="")) is False)

# 8) legacy unbound money (content_hash NULL) via release_one → NEEDS_OWNER_REVIEW
db.ex("INSERT INTO gated_effect(effect_id,kind,payload_ref,created_ts,status) "
      "VALUES ('legacy-money-1','pay','legacy-p',1,'pending')")
gate.release_one("legacy-money-1", {"hash": "human-append-legacy"})
check("legacy-unbound money id-only → NEEDS_OWNER_REVIEW (never auto-released)",
      gate.status_of("legacy-money-1") == "NEEDS_OWNER_REVIEW")

# 9) integration: on_human_judgment routes money id-only → NOT released
import os
os.environ["OCTOPUS_WIRE_HUMAN_APPEND_GUARD"] = "0"


class _FakeLedger:
    def append(self, event_type, judgment, actor, is_human):
        return {"actor": actor, "is_human": is_human, "hash": "H-INTEG"}

    def last_age_tick(self):
        return 0


e9 = gate.request("pay", "order-c41-9", target_ref="acct-9")
chrono.on_human_judgment({"effect_id": e9}, gate=gate, ledger=_FakeLedger())  # id-only, no binding
check("on_human_judgment money id-only → NOT released (bypass closed)",
      gate.status_of(e9) == "pending")


if __name__ == "__main__":
    print(f"\n== {_FAILED} failure(s) ==")
    print("OK test_c41_e4_id_only" if _FAILED == 0 else "FAIL test_c41_e4_id_only")
    sys.exit(1 if _FAILED else 0)
