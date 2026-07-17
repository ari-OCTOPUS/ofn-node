#!/usr/bin/env python3
"""تستِ txn_categorize — دستیارِ دسته‌بندیِ صفِ بازبینی (2026-07-16، $0 آفلاین).

اثبات می‌کند (مرزهای امنیتیِ پول واقعی + PIIِ شخصِ‌ثالث):
  (الف) هیچ مبلغی هرگز در promptِ ارسالی به مدل نیست (prompt capture → assertِ نبودِ cents/amount).
  (ب) tier='local' پیش‌فرض؛ ابری (primary) فقط با use_cloud=True + پرچمِ OCTOPUS_WIRE_ACCT_CLOUD.
  (پ) scrub_pii نامِ fixture + عددِ ۶رقمی را قبل از ابری حذف می‌کند (و محلی descِ خام می‌بیند).
  (ت) suggestion ست می‌شود ولی review همان needs_review می‌ماند (هرگز auto-confirm).
  (ث) JSONِ خرابِ مدل → txn دست‌نخورده (fail-soft).

ask مونکی‌پچ (بدونِ ollama/شبکه)؛ state ایزوله.
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import harness  # noqa: E402
ENV = harness.setup("txn-categorize")

_OPS = harness.REAL_VAULT / "_ops"
for _p in (str(_OPS), str(_OPS / "legs"), str(_OPS / "budget"), str(_OPS / "cortex")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import model_router     # noqa: E402
import txn_categorize as tc   # noqa: E402


# نامِ همکار + عددِ ۶رقمی برای تستِ scrub؛ desc *بدونِ* مبلغِ تراکنش (مبلغ در amount_cents است)
_NAME = "Reza"
_SIX = "482913"
_GOOD_LOCAL = '{"owner":"armin","ptype":"expense","category":"materials"}'
_LOW_LOCAL = '{"owner":"unknown","ptype":"unknown","category":""}'
_GOOD_CLOUD = '{"owner":"business","ptype":"transfer","category":"transfer"}'


def _txn(desc, amount_cents=-25000, review="needs_review", tid="1"):
    return {"id": tid, "date": "2026-07-01", "amount_cents": amount_cents,
            "desc": desc, "account": "armin-main",
            "owner": "unknown", "ptype": "unknown", "review": review,
            "basis": "unmatched:needs-owner-label"}


class _Capture:
    """ask را جایگزین می‌کند و promptها را برای assert نگه می‌دارد."""
    def __init__(self, local_text=_GOOD_LOCAL, cloud_text=_GOOD_CLOUD):
        self.calls = []
        self.local_text, self.cloud_text = local_text, cloud_text

    def ask(self, task, prompt, system="", max_tokens=400, tier=None, **kw):
        self.calls.append({"task": task, "prompt": prompt, "system": system, "tier": tier})
        text = self.cloud_text if tier == "primary" else self.local_text
        return {"ok": True, "tier": tier, "text": text}

    def tiers(self):
        return [c["tier"] for c in self.calls]

    def prompt_for(self, tier):
        for c in self.calls:
            if c["tier"] == tier:
                return c["prompt"]
        return None


def _patch(cap):
    orig = model_router.ask
    model_router.ask = cap.ask
    return orig


# ── (الف) هیچ مبلغی در prompt ────────────────────────────────────────────────
def t_a_amount_never_in_prompt():
    cap = _Capture()
    orig = _patch(cap)
    try:
        # مبلغ‌ها فقط در amount_cents؛ descِ خالص از عدد
        txns = [_txn("BUNNINGS Warehouse hardware", amount_cents=-25000),
                _txn("job deposit from client", amount_cents=1200000, tid="2")]
        tc.suggest(txns, use_cloud=False)
        assert cap.calls, "باید حداقل یک ask صدا شود"
        for c in cap.calls:
            blob = (c["prompt"] or "") + (c["system"] or "")
            for forbidden in ("25000", "250.00", "1200000", "12000.00", "amount_cents"):
                assert forbidden not in blob, f"مبلغ در prompt نشت کرد: {forbidden}"
    finally:
        model_router.ask = orig


# ── (ب) محلی پیش‌فرض؛ ابری فقط با flag + use_cloud ───────────────────────────
def t_b_local_default_cloud_only_with_flag():
    # پیش‌فرض: فقط محلی، هیچ primary
    cap = _Capture()
    orig = _patch(cap)
    os.environ.pop("OCTOPUS_WIRE_ACCT_CLOUD", None)
    try:
        tc.suggest([_txn("something ambiguous xyz")], use_cloud=False)
        assert cap.tiers() == ["local"], cap.tiers()
    finally:
        model_router.ask = orig

    # use_cloud=True ولی flag خاموش → همچنان فقط محلی
    cap2 = _Capture(local_text=_LOW_LOCAL)
    orig = _patch(cap2)
    os.environ.pop("OCTOPUS_WIRE_ACCT_CLOUD", None)
    try:
        tc.suggest([_txn("something ambiguous xyz")], use_cloud=True)
        assert cap2.tiers() == ["local"], f"flag خاموش نباید ابری بزند: {cap2.tiers()}"
    finally:
        model_router.ask = orig

    # use_cloud=True + flag روشن + محلیِ کم‌سیگنال → escalate به primary
    cap3 = _Capture(local_text=_LOW_LOCAL)
    orig = _patch(cap3)
    os.environ["OCTOPUS_WIRE_ACCT_CLOUD"] = "1"
    try:
        r = tc.suggest([_txn("something ambiguous xyz")], use_cloud=True)
        assert cap3.tiers() == ["local", "primary"], cap3.tiers()
        assert r["suggested_cloud"] == 1 and r["suggested_local"] == 0, r
    finally:
        model_router.ask = orig
        os.environ.pop("OCTOPUS_WIRE_ACCT_CLOUD", None)


# ── (پ) scrub قبل از ابری؛ محلی descِ خام می‌بیند ────────────────────────────
def t_c_scrub_pii_before_cloud():
    # unit: scrub مستقیم
    cleaned = tc.scrub_pii(f"transfer to {_NAME} account {_SIX} deposit", blocklist=[_NAME])
    assert _NAME not in cleaned and _SIX not in cleaned, cleaned
    assert "⟦name⟧" in cleaned and "⟦num⟧" in cleaned, cleaned

    # regression (audit R-money-to-llm): مبلغِ جداشده با کاما/اعشار هم باید حذف شود —
    # قبلاً \d{4,} فقط رشتهٔ ≥۴رقمِ *پیوسته* را می‌گرفت و '5,000'/'$1,234.56' فرار می‌کرد.
    import re as _re
    for amt in ("payment 5,000 done", "INV 4521 $1,234.56 paid", "fee $99.99", "x 250 y"):
        s = tc.scrub_pii(amt, blocklist=[])
        assert not _re.search(r"\d", s), f"رقم نشت کرد به LLM: {s!r} (از {amt!r})"

    # مسیرِ کامل: blocklist از env؛ محلیِ کم‌سیگنال → ابری با promptِ scrub‌شده
    cap = _Capture(local_text=_LOW_LOCAL)
    orig = _patch(cap)
    os.environ["OCTOPUS_WIRE_ACCT_CLOUD"] = "1"
    os.environ["ACCT_NAME_BLOCKLIST"] = _NAME
    try:
        desc = f"payment to {_NAME} ref {_SIX} works"
        tc.suggest([_txn(desc)], use_cloud=True)
        cloud_p = cap.prompt_for("primary")
        local_p = cap.prompt_for("local")
        assert cloud_p is not None and local_p is not None
        # ابری: نام/عدد پاک شده
        assert _NAME not in cloud_p and _SIX not in cloud_p, cloud_p
        # محلی (روی دستگاه): descِ خام مجاز — نام هست
        assert _NAME in local_p, local_p
    finally:
        model_router.ask = orig
        os.environ.pop("OCTOPUS_WIRE_ACCT_CLOUD", None)
        os.environ.pop("ACCT_NAME_BLOCKLIST", None)


# ── (ت) suggestion ست؛ review همان needs_review (propose-only) ───────────────
def t_d_suggestion_set_review_stays():
    cap = _Capture()
    orig = _patch(cap)
    try:
        txns = [_txn("BUNNINGS Warehouse")]
        r = tc.suggest(txns, use_cloud=False)
        s = txns[0].get("suggestion")
        assert s is not None, "suggestion باید ست شود"
        assert s["owner"] == "armin" and s["ptype"] == "expense", s
        assert s["by"] == "local" and s["basis"].startswith("llm-suggest:"), s
        # هرگز auto-confirm
        assert txns[0]["review"] == "needs_review", txns[0]["review"]
        assert r["suggested_local"] == 1, r
    finally:
        model_router.ask = orig


# ── (ث) JSONِ خراب → txn دست‌نخورده (fail-soft) ──────────────────────────────
def t_e_bad_json_leaves_txn_unchanged():
    cap = _Capture(local_text="ببخشید نمی‌دانم، این یک جوابِ بدونِ JSON است.")
    orig = _patch(cap)
    try:
        txns = [_txn("gibberish vendor zzz")]
        before = dict(txns[0])
        r = tc.suggest(txns, use_cloud=False)
        assert "suggestion" not in txns[0], "JSONِ خراب نباید suggestion بسازد"
        assert txns[0] == before, "txn باید دست‌نخورده بماند"
        assert r["skipped"] == 1 and r["suggested_local"] == 0, r
    finally:
        model_router.ask = orig


if __name__ == "__main__":
    failed = harness.run([
        ("(الف) هیچ مبلغی در promptِ LLM نیست", t_a_amount_never_in_prompt),
        ("(ب) محلی پیش‌فرض؛ ابری فقط با flag+use_cloud", t_b_local_default_cloud_only_with_flag),
        ("(پ) scrub نام+عددِ ۶رقمی قبل از ابری", t_c_scrub_pii_before_cloud),
        ("(ت) suggestion ست؛ review همان needs_review", t_d_suggestion_set_review_stays),
        ("(ث) JSONِ خراب → txn دست‌نخورده", t_e_bad_json_leaves_txn_unchanged),
    ])
    sys.exit(1 if failed else 0)
