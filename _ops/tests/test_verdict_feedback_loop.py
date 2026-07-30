#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_verdict_feedback_loop — حکمِ مالک واقعاً به تصمیمِ بعدی برسد (۰۷-۳۱).

ممیزی نشان داد هر دو مصرف‌کنندهٔ زندهٔ حافظه از عدم‌تطابقِ شکلِ داده گرسنه‌اند:
  · `lead_outcome_recorder._memory_prior` توکنِ `verdict=` + `category=` می‌خواهد
    و هیچ نویسنده‌ای در تولید هر دو را نمی‌نوشت (accepted بی‌توکن؛ rejected اصلاً
    یاد گرفته نمی‌شد).
  · `doctor` هر verdict را با `bottleneck_key=""` ثبت می‌کرد پس فراموشیِ
    ردشده‌ها (۳ reject → skip) ساختاراً مرده بود.

این تست‌ها round-trip واقعی‌اند: نوشتن از مسیرِ تولید، خواندن از مسیرِ تولید.
همه‌چیز در tmp؛ صفر لمسِ درخت/state ِ زنده.
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path

_TMP = Path(tempfile.mkdtemp(prefix="vfl-")).resolve()
os.environ["ORG_ROOT"] = str(_TMP)
os.environ["OPS_DIR"] = str(_TMP / "_ops")
os.environ["OCTOPUS_STATE_DIR"] = str(_TMP / "_ops" / "state")
os.environ["OCTOPUS_WIRE_VERDICT_OUTCOME"] = "1"
os.environ["OCTOPUS_WIRE_MEMORY_GATE"] = "1"
(_TMP / "_ops" / "state").mkdir(parents=True, exist_ok=True)

_HERE = Path(__file__).resolve().parent
_OPS = _HERE.parent
for _p in (str(_OPS), str(_OPS / "budget"), str(_OPS / "outcomes"),
           str(_OPS / "memory"), str(_OPS / "spine"), str(_OPS / "doctor")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import opslib                      # noqa: E402
import memory_store as msx         # noqa: E402
import verdict_recorder as vr      # noqa: E402
import lead_outcome_recorder as lor  # noqa: E402
import calibration                 # noqa: E402

assert str(opslib.STATE_DIR).startswith(str(_TMP)), opslib.STATE_DIR

CORR = "corr_abc123def456"
CAT = "painting_interior"


def _seed_decision_memory():
    """شبیه‌سازیِ ردیفی که مسیرِ learn ِ wiring هنگامِ تصمیم می‌نویسد."""
    mdir = opslib.STATE_DIR / "memory"
    mdir.mkdir(parents=True, exist_ok=True)
    m = msx.MemoryStore(path=mdir / "memory.db")
    m.insert({"namespace": "semantic", "mkey": CORR,
              "content": (f"lead-decision category={CAT} score=5 action=draft "
                          f"value_aud=1200 proposal=P-seed"),
              "trust": "DETERMINISTIC"})
    m.close()


def _semantic_recs(query: str) -> list:
    m = msx.MemoryStore(path=opslib.STATE_DIR / "memory" / "memory.db")
    try:
        return list(m.search(query, namespace="semantic", k=6))
    finally:
        m.close()


def t_a_rejected_verdict_returns_to_lead_memory_with_tokens():
    _seed_decision_memory()
    out = vr.record_verdict_durably(proposal_id="P-rej-1", verdict="rejected",
                                    correlation_id=CORR, leg_id="lead")
    assert out.get("recorded") is True, out
    recs = _semantic_recs(f"lead-decision category={CAT}")
    tok_rows = [r for r in recs
                if f"category={CAT}" in str(r.get("content"))
                and "verdict=rejected" in str(r.get("content"))]
    assert tok_rows, ("حکمِ رد به حافظهٔ لید برنگشت", [r.get("content") for r in recs])
    prior = lor._memory_prior(recs, CAT)
    assert prior["demote"] is True, ("خوانندهٔ تولید demote نکرد", prior)


def t_b_accepted_verdict_is_learned_with_tokens_but_promote_stays_owner_gated():
    """پذیرشِ مالک با توکن‌ها یاد گرفته می‌شود (learned=True + verdict=accepted).

    قراردادِ صادقانهٔ فعلی: گیتِ حافظه برای namespace=semantic هرگز بالاتر از
    GRADED نمی‌دهد (gate._grade: scrub_salience_bar) در حالی که promote ِ
    خواننده OWNER_CONFIRMED می‌خواهد ⇒ promote از مسیرِ تولید ساختاراً ناممکن
    است — و این جهتِ **محافظه‌کارانه** است (جسورترشدن بدونِ رأیِ ساختاریِ
    مالک نه). حل‌کردنِ تضاد = کارتِ VQ-PROMOTE-TRUST-001، نه بازنویسیِ گارد."""
    _seed_decision_memory()
    out = vr.record_verdict_durably(proposal_id="P-acc-1", verdict="approved",
                                    correlation_id=CORR, leg_id="lead",
                                    value_aud_claimed=900.0)
    assert out.get("recorded") is True, out
    assert out.get("learned") is True, ("پذیرش یاد گرفته نشد", out)
    assert out.get("learn_tokens") is True, ("category پیدا نشد", out)
    recs = _semantic_recs(f"lead-decision category={CAT}")
    acc = [r for r in recs if "verdict=accepted" in str(r.get("content"))]
    assert acc, ("ردیفِ پذیرش با توکن نوشته نشد",
                 [r.get("content") for r in recs])
    prior = lor._memory_prior(recs, CAT)
    assert prior["promote"] is False, \
        ("promote بدونِ OWNER_CONFIRMED ممکن شد — سیاست عوض شده؟", prior)


def t_c_verdict_without_prior_category_stays_honest():
    """بدونِ خاطرهٔ تصمیمِ هم‌corr، توکنِ جعلی نمی‌سازیم — متنِ آزادِ قبلی می‌ماند."""
    out = vr.record_verdict_durably(proposal_id="P-nocat-1", verdict="rejected",
                                    correlation_id="corr_unknown_xyz",
                                    leg_id="lead")
    assert out.get("recorded") is True, out
    assert out.get("learn_tokens") is False, out


# ── GAP-6: فراموشیِ ردشده‌های doctor ────────────────────────────────────────
class _FakeDb:
    """چرخِ chrono.db برای calibration: فقط ex/q روی duration_marker."""

    def __init__(self):
        self.rows = {}

    def ex(self, sql, params):
        eid, _p, _l, _w, label = params
        self.rows[eid] = label

    def q(self, sql):
        return [(label,) for eid, label in self.rows.items()
                if eid.startswith("verdict-")]


def t_d_doctor_verdict_carries_bottleneck_key_and_forgetting_fires():
    db = _FakeDb()
    for i in range(3):
        ok = calibration.record_verdict(db, f"RFC-{i}", "rejected",
                                        bottleneck_key="error-rate-high")
        assert ok is True
    hist = calibration.get_verdict_history(db, "error-rate-high")
    assert len(hist) == 3, hist
    skip, reason = calibration.should_skip_bottleneck(db, "error-rate-high")
    assert skip is True, (skip, reason)
    # کلیدِ دیگر → skip نمی‌شود (فیلتر واقعاً کلیدی است)
    skip2, _ = calibration.should_skip_bottleneck(db, "other-key")
    assert skip2 is False


def t_e_rfc_dataclass_persists_evidence_key():
    sys.path.insert(0, str(_OPS / "doctor"))
    import doctor as doctor_mod
    rfc = doctor_mod.RFC(rfc_id="RFC-x", bottleneck="نرخِ خطا بالا",
                         fix="فیکس", expected_lift="کمتر شدنِ خطا",
                         evidence_key="error-rate-high")
    d = rfc.to_dict()
    assert d.get("evidence_key") == "error-rate-high", d


def t_f_claim_site_passes_the_key_source_contract():
    """سنجهٔ منبع روی نقطهٔ مصرفِ حکم: بدونِ پاس‌دادنِ bottleneck_key، رگرسیون
    به کلیدِ خالی بی‌صداست (تاریخچه match نمی‌شود و skip هرگز شلیک نمی‌کند)."""
    src = (_OPS / "doctor" / "doctor.py").read_text("utf-8")
    i = src.find("claim_rfc_verdicts(worker)")
    assert i >= 0
    seg = src[i:i + 800]
    assert "bottleneck_key=" in seg and "evidence_key" in seg, \
        "record_verdict دوباره بی‌کلید صدا می‌خورد"


if __name__ == "__main__":
    tests = [(k, v) for k, v in sorted(globals().items()) if k.startswith("t_")]
    failed = 0
    for name, fn in tests:
        try:
            fn()
            print(f"  ✅ {name}")
        except AssertionError as e:
            failed += 1
            print(f"  ❌ {name}: {e}")
        except Exception as e:  # noqa: BLE001
            failed += 1
            print(f"  💥 {name}: {type(e).__name__}: {e}")
    print(f"\n{'✅' if not failed else '❌'} test_verdict_feedback_loop: "
          f"{len(tests) - failed}/{len(tests)} passed, {failed} failed")
    sys.exit(1 if failed else 0)
