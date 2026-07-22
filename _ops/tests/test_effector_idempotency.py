#!/usr/bin/env python3
"""test_effector_idempotency — REVIVED at C3 (owner directive #7).

The old phantom targeted a `request_idempotent(...)` method that never existed.
C3 folds idempotency into `EffectorGate.request(..., idempotency_key=...)` with a
DB-enforced UNIQUE(idempotency_key). The SEMANTICS are preserved AND strengthened:
a keyless request still creates a distinct effect; a keyed request is deduped;
and — stronger than the old test — the SAME key with a DIFFERENT canonical request
is a fail-closed IdempotencyConflict (never a divergent second row).

Run: python -X utf8 test_effector_idempotency.py
"""
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent))
sys.path.insert(0, str(_HERE.parent / "budget"))
import harness  # noqa: E402
ENV = harness.setup("effector-idempotency")
import chrono   # noqa: E402
import opslib   # noqa: E402


class _C:
    failed = 0


def check(name, cond):
    print(("PASS" if cond else "FAIL"), "-", name)
    if not cond:
        _C.failed += 1


db = chrono.ChronoDB(path=opslib.STATE_DIR / "idem-test-chrono.db")
gate = chrono.EffectorGate(db)

# 1) keyless request(): two calls = two distinct effects (today's behavior preserved)
e1 = gate.request("send", "payload-a")
e2 = gate.request("send", "payload-a")
check("keyless request(): no dedup, two distinct effects", e1 != e2)

# 2) same idempotency_key + same canonical request -> same effect_id (deduped)
a1 = gate.request("pay", "order-42", idempotency_key="idem-1", target_ref="acct-1")
a2 = gate.request("pay", "order-42", idempotency_key="idem-1", target_ref="acct-1")
check("keyed request(): same key -> same effect_id", a1 == a2)
check("keyed request(): dedup created exactly one row",
      db.q("SELECT COUNT(*) FROM gated_effect WHERE idempotency_key='idem-1'")[0][0] == 1)

# 3) different key -> different effect_id
b1 = gate.request("pay", "order-43", idempotency_key="idem-2", target_ref="acct-1")
check("keyed request(): different key -> different effect_id", b1 != a1)

# 4) STRONGER than the old test: same key, DIFFERENT canonical request -> conflict
try:
    gate.request("pay", "order-999-DIFFERENT", idempotency_key="idem-1", target_ref="acct-1")
    check("same key + different content -> IdempotencyConflict", False)
except chrono.IdempotencyConflict:
    check("same key + different content -> IdempotencyConflict", True)

# 5) settle path works for a keyed (idempotent) effect (release -> settle)
gate.release_one(a1, {"hash": "fake-ledger-hash-abc"})
ok = gate.settle(a1)
check("settle() works on an idempotent effect", ok is True)
check("status_of reflects settled", gate.status_of(a1) == "settled")

# 6) replay after settle (same key + same content) returns the SAME settled effect,
#    never a re-executed new row
a3 = gate.request("pay", "order-42", idempotency_key="idem-1", target_ref="acct-1")
check("replay after settle -> same (already-settled) effect_id", a3 == a1)
check("caller sees it is already settled (no re-execution)", gate.status_of(a3) == "settled")

db.close()
print("\n== %d failure(s) ==" % _C.failed)
sys.exit(1 if _C.failed else 0)
