#!/usr/bin/env python3
"""test_c4_exact_authorization — C4: exact, per-effect, fail-closed money/E4 authorization.

Proves (hermetic, fixture-only, no live DB):
  * money ("pay") is NEVER batch-released by a generic approval (release_gated_effects) —
    it stays pending; a non-money kind ("send") still batches.
  * release_effect() releases EXACTLY the bound effect only when id + content_hash +
    action_kind + target_ref all match, approval_id is present & single-use, and it is
    not expired and still pending — then settle() carries it to the world.
  * every mismatch / empty-id / expiry / replay / non-pending / kill-switch → False,
    zero release (fail-closed).
  * on_human_judgment routing: money judgment WITH binding → release_effect;
    generic (no effect_id) → batch (money excluded).

Run: python -X utf8 test_c4_exact_authorization.py
"""
import hashlib
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent))
sys.path.insert(0, str(_HERE.parent / "budget"))
import harness   # noqa: E402
ENV = harness.setup("c4-exact-authorization")
import chrono    # noqa: E402
import opslib    # noqa: E402

_FAILED = 0


def check(name, cond):
    global _FAILED
    print(("PASS" if cond else "FAIL"), "-", name)
    if not cond:
        _FAILED += 1


def _db(tag):
    return chrono.ChronoDB(path=opslib.STATE_DIR / f"c4-{tag}.db")


def _appr(db, eid, *, approval_id, effect_id=None, content_hash=None,
          action_kind=None, target_ref=None, expires_at=None):
    """approval درست از bindingِ واقعیِ ردیف؛ هر آرگومان = دستکاریِ عمدی برای تستِ mismatch."""
    r = db.q("SELECT content_hash, action_kind, target_ref FROM gated_effect WHERE effect_id=?",
             (eid,))[0]
    return {"effect_id": eid if effect_id is None else effect_id,
            "approval_id": approval_id,
            "content_hash": r[0] if content_hash is None else content_hash,
            "action_kind": r[1] if action_kind is None else action_kind,
            "target_ref": r[2] if target_ref is None else target_ref,
            "expires_at": expires_at, "release_ref": "ref-" + str(approval_id)}


# 1) money NEVER batches; non-money still does
db = _db("batch")
gate = chrono.EffectorGate(db)
e_pay = gate.request("pay", "order-1", target_ref="acct-1")
e_send = gate.request("send", "internal-1", target_ref="chan-1")
released = gate.release_gated_effects({"hash": "generic-append"})
check("money 'pay' NOT batch-released by generic approval",
      gate.status_of(e_pay) == "pending")
check("non-money 'send' IS batch-released", gate.status_of(e_send) == "releasable")

# 2) release_effect exact OK → releasable → settle → settled
e = gate.request("pay", "order-2", target_ref="acct-2")
ok = gate.release_effect(e, _appr(db, e, approval_id="A-2"))
check("release_effect exact binding → True", ok is True)
check("  effect now releasable", gate.status_of(e) == "releasable")
check("  settle() carries releasable → settled", gate.settle(e) is True and gate.status_of(e) == "settled")

# 3-6) binding mismatches → False, effect stays pending
for tag, kw in (("content_hash", {"content_hash": "deadbeef"}),
                ("action_kind", {"action_kind": "WRONG"}),
                ("target_ref", {"target_ref": "acct-EVIL"}),
                ("effect_id", {"effect_id": "not-this-one"})):
    em = gate.request("pay", f"order-mm-{tag}", target_ref="acct-x")
    r = gate.release_effect(em, _appr(db, em, approval_id=f"A-mm-{tag}", **kw))
    check(f"release_effect {tag} mismatch → False + still pending",
          r is False and gate.status_of(em) == "pending")

# 7) empty approval_id → False
e7 = gate.request("pay", "order-7", target_ref="acct-7")
check("release_effect empty approval_id → False",
      gate.release_effect(e7, _appr(db, e7, approval_id="")) is False)

# 8) expired approval → False
e8 = gate.request("pay", "order-8", target_ref="acct-8")
check("release_effect expired approval → False",
      gate.release_effect(e8, _appr(db, e8, approval_id="A-8", expires_at=1)) is False)

# 9) replay: an approval_id used once cannot release a second effect
e9a = gate.request("pay", "order-9a", target_ref="acct-9")
e9b = gate.request("pay", "order-9b", target_ref="acct-9")
check("release_effect first use of approval_id → True",
      gate.release_effect(e9a, _appr(db, e9a, approval_id="A-REPLAY")) is True)
check("release_effect replayed approval_id on 2nd effect → False + 2nd pending",
      gate.release_effect(e9b, _appr(db, e9b, approval_id="A-REPLAY")) is False
      and gate.status_of(e9b) == "pending")

# 10) non-pending (already releasable) → False
e10 = gate.request("pay", "order-10", target_ref="acct-10")
gate.release_effect(e10, _appr(db, e10, approval_id="A-10a"))
check("release_effect on already-releasable → False",
      gate.release_effect(e10, _appr(db, e10, approval_id="A-10b")) is False)

# 11) kill-switch (STOP-ORGANISM) → refused, zero release
e11 = gate.request("pay", "order-11", target_ref="acct-11")
opslib.STOP_ORGANISM.write_text("test", "utf-8")
try:
    r11 = gate.release_effect(e11, _appr(db, e11, approval_id="A-11"))
    check("release_effect under STOP → False + refused",
          r11 is False and gate.status_of(e11) == "refused")
finally:
    opslib.STOP_ORGANISM.unlink(missing_ok=True)

# 12) on_human_judgment routing (fake gate/ledger, guard off = authorized)
import os
os.environ["OCTOPUS_WIRE_HUMAN_APPEND_GUARD"] = "0"


class _FakeLedger:
    def append(self, event_type, judgment, actor, is_human):
        return {"actor": actor, "is_human": is_human, "hash": "H-ROUTE"}

    def last_age_tick(self):
        return 0


class _FakeGate:
    def __init__(self):
        self.calls = []

    def release_effect(self, effect_id, approval):
        self.calls.append(("exact", effect_id, approval.get("approval_id")))
        return True

    def release_one(self, effect_id, entry):
        self.calls.append(("one", effect_id))
        return True

    def release_gated_effects(self, entry):
        self.calls.append(("batch", None))
        return 0


g1 = _FakeGate()
chrono.on_human_judgment(
    {"effect_id": "E-money", "content_hash": "ch", "action_kind": "pay",
     "target_ref": "acct", "approval_id": "AP-1"}, gate=g1, ledger=_FakeLedger())
check("routing: money judgment WITH binding → release_effect (exact)",
      g1.calls == [("exact", "E-money", "AP-1")])

g2 = _FakeGate()
chrono.on_human_judgment({"note": "generic, no effect_id"}, gate=g2, ledger=_FakeLedger())
check("routing: generic (no effect_id) → batch (money excluded)",
      g2.calls == [("batch", None)])

g3 = _FakeGate()
chrono.on_human_judgment({"effect_id": "E-plain"}, gate=g3, ledger=_FakeLedger())
check("routing: id-only, no binding → release_one (legacy customer path)",
      g3.calls == [("one", "E-plain")])


if __name__ == "__main__":
    total = sum(1 for _ in ())  # placeholder; counts printed inline
    print(f"\n== {_FAILED} failure(s) ==")
    print("OK test_c4_exact_authorization" if _FAILED == 0 else "FAIL test_c4_exact_authorization")
    sys.exit(1 if _FAILED else 0)
