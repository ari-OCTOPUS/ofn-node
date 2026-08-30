#!/usr/bin/env python3
"""test_doctor_rfc_stale_dedup.py — T8 (2026-07-25): صفِ RFC وضعیتی را درمان می‌کرد که نیست.

گواه (state/doctor/rfcs.json اسکن ۱۱:۱۲): ۱۰ RFC، ۸ تای‌شان متنِ گلوگاهِ یکسانِ
«σ≈1 (σ=1.00)؛ gap=0.000» — در حالی که هر سه منبعِ زنده σ=0.0 می‌گفتند و یکی هم
«ارگانیسم FREEZE است» می‌گفت با frozen:false. هر ۳ critic_review = unvalidated.

این تست ادعا می‌کند:
  ۱) dedupe: propose_rfc با همان رشتهٔ گلوگاهِ یک RFCِ باز → نسخهٔ نو نمی‌سازد.
  ۲) reconcile: RFCی σ≈1 روی traceِ سالم (گرافِ خطا خالی) → stale-input با دلیل.
  ۳) reconcile: RFCی FREEZE روی trace با frozen=false → stale-input.
  ۴) RFCی که شرطش هنوز برقرار است (گرافِ خطا با σ≈1) → stale-input نمی‌شود.
  ۵) submit_for_approval روی RFCی submitted کارتِ تکراری نمی‌فرستد (idempotent).
  ۶) RFCی stale-input دیگر dedupe را بلاک نمی‌کند (باز محسوب نمی‌شود).
"""
from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
OPS = HERE.parent
sys.path.insert(0, str(OPS / "doctor"))
sys.path.insert(0, str(OPS / "budget"))

import opslib  # noqa: E402

_TMP = Path(tempfile.mkdtemp(prefix="oct-t8-rfc-"))
opslib.ORG_ROOT = _TMP
opslib.STATE_DIR = _TMP / "state"
opslib.STATE_DIR.mkdir(parents=True, exist_ok=True)

# ledgerِ واقعی هرگز: _note به opslib.ledger_note می‌زند — fake می‌کنیم
_orig_ledger_note = opslib.ledger_note
opslib.ledger_note = lambda *a, **k: {"hash": "f" * 64}

import doctor as dmod  # noqa: E402

fails = []


def check(cond, msg):
    if cond:
        print(f"  ✅ {msg}")
    else:
        fails.append(msg)
        print(f"  ❌ {msg}")


def _mk_doctor():
    return dmod.Doctor(state_dir=str(_TMP / "state"),
                       knowledge_dir=str(_TMP / "kn"))


class _FakeChannel:
    def __init__(self):
        self.cards = []
        self._owner = "x"

    def rfc_card(self, rfc_id, text):
        self.cards.append(rfc_id)
        return True

    def send_text(self, *a, **k):
        return True


# ═══ ۱) dedupe ════════════════════════════════════════════════════════════════
doc = _mk_doctor()
b = {"bottleneck": "σ≈1 (σ=1.00 = نزدیکِ گذارِ فاز/SOC)؛ شکافِ طیفیِ کوچک (gap=0.000 = شکننده)"}
r1 = doc.propose_rfc(b, fix="فیکسِ پیشنهادیِ اول برای تست", expected_lift="x")
r2 = doc.propose_rfc(b, fix="فیکسِ متفاوتِ دوم برای تست", expected_lift="y")
check(r1.rfc_id == r2.rfc_id, "dedupe: propose دوم همان RFCِ باز را برمی‌گرداند")
check(len(doc._rfcs) == 1, "dedupe: فقط یک RFC در registry است")

# ═══ ۲) reconcile σ روی trace سالم ════════════════════════════════════════════
trace_salem = {"organs": {}, "errors": [], "frozen": False, "sigma_effective": 0.0}
res = doc._reconcile_input_validity(trace_salem)
check(res["stale_marked"] == 1, "reconcile: RFCی σ≈1 روی trace سالم stale-input شد")
check(r1.status == "stale-input", "وضعیت = stale-input")
check("stale_reason" in (r1.critic_review or {}), "دلیلِ staleness در رکورد ثبت شد")

# ═══ ۳) RFCی FREEZE با frozen=false ═══════════════════════════════════════════
doc2 = _mk_doctor()
rf = doc2.propose_rfc({"bottleneck": "ارگانیسم در حالت FREEZE است (حسابداری نامعلوم)"},
                      fix="رفعِ تعارضِ تلمتری که FREEZE کرده", expected_lift="x")
rs = doc2.propose_rfc({"bottleneck": "σ_effective=1.3 > ۱ (خطِ قرمزِ سرطان)"},
                      fix="افزایشِ گاردِ replication", expected_lift="x")
rk = doc2.propose_rfc({"bottleneck": "knob:CHRONO_NUDGE_EVERY_N_BEATS — بدونِ مقدارِ صریح (unset)"},
                      fix="knob ست شود", expected_lift="x", change_level="tune",
                      knob="CHRONO_NUDGE_EVERY_N_BEATS")
res2 = doc2._reconcile_input_validity(trace_salem)
check(res2["stale_marked"] == 2, "reconcile: FREEZE و σ_effective هر دو stale-input شدند")
check(rf.status == "stale-input", "FREEZE با frozen=false → stale-input")
check(rs.status == "stale-input", "σ_effective با σ=0.0 → stale-input")
check(rk.status == "drafted", "knob-RFC دست‌نخورده (وابسته به trace نیست)")

# ═══ ۴) شرطِ برقرار → stale نمی‌شود ═══════════════════════════════════════════
doc3 = _mk_doctor()
r4 = doc3.propose_rfc(b, fix="فیکسِ پیشنهادیِ معتبر برای تست", expected_lift="x")
trace_bimар = {"organs": {"A": {"errors": 2}, "B": {"errors": 1}},
               "errors": [{"organ": "A"}, {"organ": "B"}],
               "frozen": False, "sigma_effective": 0.0}
res3 = doc3._reconcile_input_validity(trace_bimар)
check(res3["stale_marked"] == 0, "شرطِ طیفیِ برقرار (σ≈1 واقعی) → stale-input نمی‌شود")
check(r4.status == "drafted", "RFC سالم می‌ماند")

# ═══ ۵) submit idempotent ═════════════════════════════════════════════════════
doc4 = _mk_doctor()
ch = _FakeChannel()
doc4._channel = ch
r5 = doc4.propose_rfc({"bottleneck": "گلوگاهِ تستیِ پنجم برای بررسیِ idempotency"},
                      fix="فیکسِ کافیِ بلند برای تست", expected_lift="x")
r5.status = "submitted"
ok = doc4.submit_for_approval(r5)
check(ok is True, "submit روی RFCی submitted=True برمی‌گردد")
check(len(ch.cards) == 0, "هیچ کارتِ تکراری فرستاده نشد")

# ═══ ۶) stale-input دیگر dedupe را بلاک نمی‌کند ════════════════════════════════
doc5 = _mk_doctor()
r6 = doc5.propose_rfc(b, fix="فیکسِ اول برای تستِ ششم", expected_lift="x")
r6.status = "stale-input"
r7 = doc5.propose_rfc(b, fix="فیکسِ دوم برای تستِ ششم", expected_lift="y")
check(r7.rfc_id != r6.rfc_id, "بازگشتِ شرط پس از staleness → RFCِ نو مجاز است")
check(r7.status == "drafted", "RFCِ نو در وضعیتِ عادی است")

opslib.ledger_note = _orig_ledger_note

print(f"\n{'PASS' if not fails else 'FAIL'} — test_doctor_rfc_stale_dedup")
for f in fails:
    print(f"  - {f}")
sys.exit(1 if fails else 0)
