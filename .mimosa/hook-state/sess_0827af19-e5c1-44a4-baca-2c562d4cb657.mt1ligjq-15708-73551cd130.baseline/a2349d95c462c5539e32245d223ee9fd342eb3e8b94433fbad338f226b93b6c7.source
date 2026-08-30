#!/usr/bin/env python3
"""test_company_books.py — آداپتورِ ریلِ شرکت (2026-07-16).
اثبات: فلگ خاموش = no-opِ صادق · providerِ ناشناخته/غایب = خاموشِ صادق (نه crash) ·
create_draft_invoice فقط DRAFT (تحمیلِ مرز حتی با ورودیِ مخرب) · providerِ تزریقی
درست صدا زده می‌شود · هیچ secret در خروجی. ایزوله با env-patch. $0."""
import os
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent / "legs"))
sys.path.insert(0, str(_HERE.parent / "budget"))
import company_books as cb  # noqa: E402


class _FakeProvider:
    def __init__(self):
        self.calls = []

    def connect_check(self):
        self.calls.append("connect")
        return {"ok": True, "org": "FAKE ORG", "note": "sandbox"}

    def list_invoices(self, status=None, limit=20):
        self.calls.append(("list", status, limit))
        return {"ok": True, "invoices": [{"id": "INV-1", "status": "DRAFT"}], "note": ""}

    def create_draft_invoice(self, inv):
        self.calls.append(("draft", inv))
        assert inv["status"] == "DRAFT"
        return {"ok": True, "draft_id": "d-1", "note": ""}


def _env(flag=None, provider=None):
    for k in ("OCTOPUS_WIRE_COMPANY_BOOKS", "COMPANY_BOOKS_PROVIDER"):
        os.environ.pop(k, None)
    if flag is not None:
        os.environ["OCTOPUS_WIRE_COMPANY_BOOKS"] = flag
    if provider is not None:
        os.environ["COMPANY_BOOKS_PROVIDER"] = provider


def t_a_flag_off_honest():
    _env()
    s = cb.status()
    assert s["wired"] is False and "خاموش" in s["note"], s
    assert cb.list_invoices()["ok"] is False
    assert cb.create_draft_invoice({"line_items": [1]})["ok"] is False


def t_b_unknown_or_missing_provider_honest():
    _env(flag="1")                                     # فلگ روشن، provider تنظیم نشده
    s = cb.status()
    assert s["wired"] is False and "provider" in s["note"], s
    _env(flag="1", provider="ghostapp")                # ناشناخته
    assert cb.status()["wired"] is False
    _env(flag="1", provider="xero")                    # شناخته؛ books_xero import می‌شود و
    s3 = cb.status()                                   # connect_checkِ صادق برمی‌گرداند (creds نیست).
    # صادقانه‌ی واقعی: wired=False با دلیلِ قابلِ‌فهم (creds نیست/اتصال ناموفق) — نه
    # مسیرِ مبهمِ «پیاده». قبلاً تست انتظارِ «پیاده» داشت در حالی که books_xero ساخته شده
    # و فقط creds ندارد؛ این دقیق‌تر است.
    assert s3["wired"] is False and s3["provider"] == "xero", s3
    assert any(k in s3["note"] for k in (".env", "اتصال", "ناموفق")), s3


def t_c_draft_only_enforced():
    """گاردِ مرز: حتی ورودیِ مخرب با status=AUTHORISED رد می‌شود، قبل از provider."""
    _env(flag="1", provider="xero")
    fake = _FakeProvider()
    orig = cb._load_provider
    cb._load_provider = lambda: fake
    try:
        bad = cb.create_draft_invoice({"line_items": [{"description": "x"}],
                                       "status": "AUTHORISED"})
        assert bad["ok"] is False and "DRAFT" in bad["note"], bad
        assert fake.calls == [], "ورودیِ غیرDRAFT هرگز نباید به provider برسد"
        ok = cb.create_draft_invoice({"line_items": [{"description": "x"}]})
        assert ok["ok"] and ok["draft_id"] == "d-1", ok
        assert fake.calls and fake.calls[0][1]["status"] == "DRAFT"
    finally:
        cb._load_provider = orig


def t_d_injected_provider_paths():
    _env(flag="1", provider="xero")
    fake = _FakeProvider()
    orig = cb._load_provider
    cb._load_provider = lambda: fake
    try:
        s = cb.status()
        assert s["wired"] is True and s["org"] == "FAKE ORG", s
        li = cb.list_invoices(status_filter="DRAFT", limit=5)
        assert li["ok"] and li["invoices"][0]["id"] == "INV-1", li
    finally:
        cb._load_provider = orig


def t_e_no_secret_in_status():
    """هیچ مقدارِ env-مانندِ secret در خروجیِ status echo نمی‌شود."""
    _env(flag="1", provider="xero")
    os.environ["XERO_CLIENT_SECRET"] = "SUPER-SECRET-VALUE-XYZ"
    try:
        blob = repr(cb.status())
        assert "SUPER-SECRET" not in blob, blob
    finally:
        os.environ.pop("XERO_CLIENT_SECRET", None)


if __name__ == "__main__":
    for f in (t_a_flag_off_honest, t_b_unknown_or_missing_provider_honest,
              t_c_draft_only_enforced, t_d_injected_provider_paths, t_e_no_secret_in_status):
        f()
        print("ok", f.__name__)
    print("PASS test_company_books")
