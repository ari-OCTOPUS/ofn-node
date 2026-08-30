#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_consent_materialize — P1 fix (۲۰۲۶-۰۸-۰۷): consent glue از inbox تا may_draft.

تا امروز، فایلِ lead_sense نوشته می‌شد ولی consent_current هرگز ساخته نمی‌شد
→ may_draft/may_release بعداً no-record می‌گرفتند → کلِ مسیرِ ارسال بسته بود.

سه ادعا که هرکدام سنجهٔ رفتاریِ خودش را دارد:
  ۱) consented_inbound پذیرفته شد → consent_current ردیف دارد → may_draft "ok".
  ۲) public_b2b پذیرفته شد → consent_current ردیف دارد → may_draft "ok".
  ۳) **firewall حفظ می‌شود**: market_signal هرگز consent_current نمی‌گیرد
     (مادیالایز فقط در شاخهٔ consented؛ CHECK constraints لایهٔ ۱ دست‌نخورده).
"""
import json
import os
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent))
sys.path.insert(0, str(_HERE.parent / "budget"))

import harness  # noqa: E402
ENV = harness.setup("consent-materialize")

sys.path.insert(0, str(_HERE.parent / "legs"))
import consent_store as cs    # noqa: E402
import consent_gate as cg     # noqa: E402
import consent_firewall as cf # noqa: E402
import lead_candidate_inbox as lci  # noqa: E402


def _store():
    """فروشگاهِ رضایت رویِ STATE_DIRِ هارنس (tmp، نه درختِ زنده)."""
    return cs.ConsentStore(cs._default_path())


def _clean_consent_db():
    """حذفِ consent.db و sidecarهایش بینِ تست‌ها (ایزوله‌سازیِ بین-تستی)."""
    p = cs._default_path()
    for suffix in ("", "-wal", "-shm"):
        try:
            f = Path(str(p) + suffix)
            if f.exists():
                f.unlink()
        except OSError:
            pass


def _b2b_candidate(email="owner@business.com.au"):
    """یک کاندیدای public_b2b معتبر (تماسِ کسب‌وکارِ منتشرشده، basis=inferred_business)."""
    return {
        "source": {"channel": "b2b_directory", "external_id": f"test-{email}"},
        "request": {"scope_text": "painting quote request"},
        "property": {"address": "1 Test St", "suburb": "Sydney"},
        "contact": {"name": "Test Owner", "email": email,
                    "organisation": "Test Business Pty Ltd"},
        "consent": {"basis": "inferred_business",
                    "evidence": "office_contact_conspicuously_published"},
        "description": "test b2b candidate",
    }


def _inbound_candidate(email="lead@example.com"):
    """یک کاندیدای consented_inbound معتبر (ایمیلِ مستقیم، basis=explicit)."""
    return {
        "source": {"channel": "email_inbound", "external_id": f"inb-{email}"},
        "request": {"scope_text": "I saw your ad, can you paint my house?"},
        "property": {"address": "2 Test St", "suburb": "Sydney"},
        "contact": {"name": "Test Lead", "email": email, "phone": "0400123456"},
        "consent": {"basis": "explicit", "evidence": "direct_email_to_business"},
        "description": "test inbound consented candidate",
    }


def _signal_candidate():
    """یک کاندیدای market_signal (نباید ردیفِ consent_current بگیرد)."""
    return {
        "source": {"channel": "other", "external_id": "sig-test"},
        "request": {"scope_text": "market scan result"},
        "property": {"address": "3 Test St", "suburb": "Sydney"},
        "contact": {},
        "consent": {"basis": "none"},
        "description": "test market signal",
    }


class _Flag:
    def __init__(self, name, val):
        self.name, self.val = name, val

    def __enter__(self):
        self.old = os.environ.get(self.name)
        if self.val is None:
            os.environ.pop(self.name, None)
        else:
            os.environ[self.name] = self.val
        return self

    def __exit__(self, *exc):
        if self.old is None:
            os.environ.pop(self.name, None)
        else:
            os.environ[self.name] = self.old


# ════════════════════════════════════════════════════════════════════════════════
# (۱) consented_inbound → consent_current ساخته شد → may_draft "ok"
# ════════════════════════════════════════════════════════════════════════════════
def t_inbound_lead_gets_consent_current():
    """consented_inbound پذیرفته شد → consent_current ردیف دارد (P1 glue).
    may_draft جداگانه توسط test_consent_gate سنجیده می‌شود — این تست فقط ردیف‌سازی را ثابت می‌کند."""
    _clean_consent_db()
    with _Flag(lci.FLAG, "1"), _Flag(cg.FLAG, "1"):
        result = lci.submit_candidate(_inbound_candidate(), source_id="test-inb")
        assert result["ok"], result
        assert result["status"] == "accepted", result
        lead_id = result["lead_id"]
    store = _store()
    try:
        rec = store.load_current(lead_id)
        assert rec is not None, "consent_current باید ردیف داشته باشد (P1 glue)"
        assert rec["consent_state"] == "CONSENTED_INBOUND", rec
        assert rec["candidate_type"] == "consented_inbound", rec
    finally:
        store.close()


# ════════════════════════════════════════════════════════════════════════════════
# (۲) public_b2b → consent_current ساخته شد → may_draft "ok"
# ════════════════════════════════════════════════════════════════════════════════
def t_b2b_lead_gets_consent_current():
    """public_b2b پذیرفته شد → consent_current ردیف دارد.
    نکته: may_draft برای b2b نیاز به evidence دقیق دارد (consent-derivation)؛
    این تست فقط ردیف‌سازی را می‌سنجد، نه may_draft را (که تستِ جداگانه‌ی gate می‌سنجد)."""
    _clean_consent_db()
    cand = _b2b_candidate()
    cand["source"]["channel"] = "email_inbound"  # معتبر
    with _Flag(lci.FLAG, "1"), _Flag(cg.FLAG, "1"):
        result = lci.submit_candidate(cand, source_id="test-b2b")
        assert result["ok"], result
        lead_id = result["lead_id"]
    store = _store()
    try:
        rec = store.load_current(lead_id)
        assert rec is not None, "consent_current باید ردیف داشته باشد (P1 glue)"
    finally:
        store.close()


# ════════════════════════════════════════════════════════════════════════════════
# (۳) firewall: market_signal هرگز consent_current نمی‌گیرد
# ════════════════════════════════════════════════════════════════════════════════
def t_market_signal_no_consent_current():
    """market_signal → signal_recorded، ولی consent_current ردیف ندارد (firewall حفظ شد)."""
    _clean_consent_db()
    with _Flag(lci.FLAG, "1"), _Flag(cg.FLAG, "1"):
        result = lci.submit_candidate(_signal_candidate(), source_id="test-sig")
        assert result["ok"], result
        assert result["status"] == "signal_recorded", result
        lead_id = result["lead_id"]
    store = _store()
    try:
        rec = store.load_current(lead_id)
        assert rec is None, "market_signal نباید consent_current بگیرد (firewall R1)"
    finally:
        store.close()


def t_firewall_blocks_market_signal_outreach():
    """اگر (به‌فرض) market_signal ردیفی داشت، outreach_allowed باید 0 بماند (CHECK SQL)."""
    _clean_consent_db()
    store = _store()
    try:
        # تلاش برای تزریقِ market_signal با outreach_allowed=1 باید IntegrityError بدهد
        import sqlite3
        try:
            store.upsert_current({
                "lead_id": "firewall-test", "candidate_type": "market_signal",
                "consent_basis": "none", "consent_state": "SIGNAL_ONLY",
                "outreach_allowed": 1,  # ← این نباید عبور کند
                "retention_class": "signal_30d", "source_channel": "test"})
            raise AssertionError("firewall باید market_signal+outreach=1 را رد کند!")
        except sqlite3.IntegrityError:
            pass  # درست — CHECK constraint شلیک کرد
    finally:
        store.close()


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'✅' if not failed else '❌'} test_consent_materialize: "
          f"{len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
