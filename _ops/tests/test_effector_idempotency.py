#!/usr/bin/env python3
"""تست EffectorGate.request_idempotent — 2027 Standards backlog #2 (P-08 diff-الف).
اثبات: exactly-once روی idempotency_key؛ request() اصلی کاملاً دست‌نخورده (رفتارِ
امروز بدونِ idempotency_key)؛ مسیرِ settle/release هم برای effectِ idempotent کار
می‌کند. اجرا: python3 test_effector_idempotency.py"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import harness  # noqa: E402

ENV = harness.setup("effector-idempotency")
import opslib  # noqa: E402
import chrono  # noqa: E402


class _C:
    failed = 0


def check(name: str, cond: bool) -> None:
    print(("PASS" if cond else "FAIL"), "-", name)
    if not cond:
        _C.failed += 1


db = chrono.ChronoDB(path=opslib.STATE_DIR / "idem-test-chrono.db")   # ایزوله (harness OPS_DIR)
gate = chrono.EffectorGate(db)

# ۱) request() اصلی: بدونِ idempotency_key، دو فراخوان = دو effect_id مجزا (امروز)
e1 = gate.request("SEND", "payload-a")
e2 = gate.request("SEND", "payload-a")
check("request() legacy: no dedup (byte-identical with today)", e1 != e2)

# ۲) request_idempotent: همان key دوبار → همان effect_id، is_new فقط بارِ اول True
eid_a, new_a = gate.request_idempotent("SELL", "crypto-order-42", "idem-key-1")
eid_b, new_b = gate.request_idempotent("SELL", "crypto-order-42", "idem-key-1")
check("request_idempotent: same key -> same effect_id", eid_a == eid_b)
check("request_idempotent: is_new True then False", new_a is True and new_b is False)

# ۳) key متفاوت → effect_id متفاوت
eid_c, new_c = gate.request_idempotent("SELL", "crypto-order-43", "idem-key-2")
check("request_idempotent: different key -> different effect_id", eid_c != eid_a)
check("request_idempotent: different key -> is_new True", new_c is True)

# ۴) idempotency_key خالی → ValueError (باید request() معمولی صدا زده شود)
try:
    gate.request_idempotent("SELL", "x", "")
    check("empty idempotency_key rejected", False)
except ValueError:
    check("empty idempotency_key rejected", True)

# ۵) مسیرِ settle برای effectِ idempotent دست‌نخورده است (release -> settle عادی کار می‌کند)
entry = {"hash": "fake-ledger-hash-abc"}
released = gate.release_gated_effects(entry)
check("release_gated_effects releases idempotent pending too", released >= 1)
ok_settle = gate.settle(eid_a)
check("settle() works on an idempotent effect_id", ok_settle is True)
check("status_of reflects settled", gate.status_of(eid_a) == "settled")

# ۶) بعد از settle، همان key هنوزم effect_id ِ settled‌شده را برمی‌گرداند (نه ردیفِ نو)
eid_d, new_d = gate.request_idempotent("SELL", "crypto-order-42", "idem-key-1")
check("replay after settle returns the SAME (already-settled) effect_id",
      eid_d == eid_a and new_d is False)
check("caller can see it is already settled via status_of (no re-execution needed)",
      gate.status_of(eid_d) == "settled")

# ۷) دو راز/kind متفاوت با یک payload_ref، ولی key یکی -> هنوز dedup می‌شود
#    (kind/payload_ref فقط توصیفی‌اند؛ کلیدِ حقیقتِ exactly-once فقط idempotency_key است)
eid_e, new_e = gate.request_idempotent("PUBLISH", "different-payload", "idem-key-1")
check("dedup keys purely on idempotency_key regardless of kind/payload_ref",
      eid_e == eid_a and new_e is False)

db.close()
print("\n== %d failure(s) ==" % _C.failed)
sys.exit(1 if _C.failed else 0)
