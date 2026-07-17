#!/usr/bin/env python3
"""test_review_telegram.py — لایهٔ تلگرامِ حسابدارِ گفتگومحور (2026-07-16).
اثبات: (الف) /review کارتِ سوال با کیبورد می‌دهد؛ (ب) callback rev:a اعمال+سوالِ بعدی؛
(پ) rev:f حالتِ متنِ آزاد، بعد متن → پیشنهادِ تأییدشدنی؛ (ت) تأییدِ متن اعمال می‌کند؛
(ث) rev:x توقف؛ (ج) صفر دکمهٔ پول (app:/act:/card:) در کارتِ مرور. ایزوله با mini-vault harness."""
import re
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))
sys.path.insert(0, str(_HERE.parent))
sys.path.insert(0, str(_HERE.parent / "budget"))
sys.path.insert(0, str(_HERE.parent / "legs"))

import harness  # noqa: E402
ENV = harness.setup("review_telegram")

import json  # noqa: E402
from approval_channel import TelegramApprovalChannel  # noqa: E402
import acct_review as ar  # noqa: E402


def _seed_store():
    """دو تراکنشِ needs_review در txn-store مینی‌والت."""
    p = ar._store_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    txns = [{"id": "big", "date": "2026-01-02", "amount_cents": -90000,
             "desc": "BUNNINGS ACCT 12345678", "owner": "unknown", "ptype": "unknown",
             "review": "needs_review", "basis": "unmatched"},
            {"id": "sml", "date": "2026-01-03", "amount_cents": 30000,
             "desc": "PAYPAL DEPOSIT", "owner": "unknown", "ptype": "unknown",
             "review": "needs_review", "basis": "unmatched"}]
    p.write_text(json.dumps({"txns": txns}, ensure_ascii=False), "utf-8")
    # جلسهٔ قبلی را پاک کن
    sp = ar._session_path()
    if sp.exists():
        sp.unlink()


def _ch():
    return TelegramApprovalChannel()


def t_a_review_start_gives_question_card():
    _seed_store()
    out = _ch().handle_command("/review")
    assert isinstance(out, dict) and "reply_markup" in out, out
    assert "(1/2)" in out["text"], out                 # header فارسیِ ساده (UX-SPEC §۳.۲)
    assert "900.00" in out["text"], out                # بزرگ‌ترین اول ($900 > $300)
    assert "12345678" not in out["text"], out          # شماره‌حساب scrub شد
    assert "خروجی" in out["text"], out                 # 🔴 خروجی (نه «sign + AUD»)
    cds = [b["callback_data"] for row in out["reply_markup"]["inline_keyboard"] for b in row]
    # صفر دکمهٔ پول/act/card
    for cd in cds:
        assert not cd.startswith(("app:", "act:", "card:")), cd
    assert any(c.startswith("rev:a:") for c in cds), cds
    # دکمه‌های فارسیِ روزمره (UX-SPEC)
    labels = " ".join(b["text"] for row in out["reply_markup"]["inline_keyboard"] for b in row)
    assert "خرجِ آرمین" in labels, labels
    assert "فقط رد شد" in labels, labels


def _cbs(card):
    return [b["callback_data"] for row in card["reply_markup"]["inline_keyboard"] for b in row]


def t_b_callback_answer_applies_and_advances():
    _seed_store()
    ch = _ch()
    card = ch.handle_command("/review")                 # سوال ۱ = big
    armin_exp = next(c for c in _cbs(card) if c.endswith(":a:e"))   # rev:a:big:a:e (هویت‌دار)
    r = ch.dispatch_callback(armin_exp)
    assert isinstance(r, dict) and "ثبت شد" in r["text"], r
    assert "(2/2)" in r["text"], r                      # سوالِ بعدی (header فارسیِ ساده)
    doc = json.loads(ar._store_path().read_text("utf-8"))
    big = next(t for t in doc["txns"] if t["id"] == "big")
    assert big["owner"] == "armin" and big["ptype"] == "expense" and big["review"] == "confirmed", big


def t_c_freetext_flow_proposes_then_confirms():
    _seed_store()
    ch = _ch()
    card = ch.handle_command("/review")
    free_cb = next(c for c in _cbs(card) if c.startswith("rev:f:"))   # rev:f:big
    f = ch.dispatch_callback(free_cb)
    assert isinstance(f, dict) and "بنویس" in f["text"], f
    assert ar.is_awaiting_free() is True
    # متنِ آزاد → پیشنهاد
    prop = ch.handle_command("مالِ عباسه، خرجه")
    assert isinstance(prop, dict) and "تأیید کنم" in prop["text"], prop
    ok = next(c for c in _cbs(prop) if c.startswith("rev:a:"))
    assert ":b:e" in ok, ok                             # abbas / expense استخراج شد
    r = ch.dispatch_callback(ok)
    assert "ثبت شد" in r["text"], r
    doc = json.loads(ar._store_path().read_text("utf-8"))
    big = next(t for t in doc["txns"] if t["id"] == "big")
    assert big["owner"] == "abbas" and big["ptype"] == "expense", big


def t_f_need_clarify_keeps_listening():
    """رفعِ dead-end: «نفهمیدم» حالتِ متنِ آزاد را نمی‌بندد؛ مالک دوباره می‌نویسد."""
    _seed_store()
    ch = _ch()
    card = ch.handle_command("/review")
    ch.dispatch_callback(next(c for c in _cbs(card) if c.startswith("rev:f:")))
    ch.handle_command("یه چیزی که معلوم نیست")           # مبهم → need-clarify
    assert ar.is_awaiting_free() is True, "باید هنوز گوش بدهد"
    prop = ch.handle_command("عباس خرج")                 # دوباره نوشتن کار می‌کند
    assert isinstance(prop, dict) and "تأیید" in prop["text"], prop


def t_g_slash_clears_awaiting():
    """رفعِ sticky-flag: دستورِ / وسطِ حالتِ متن آن را می‌بندد تا پیامِ بعدیِ نامرتبط دزدیده نشود."""
    _seed_store()
    ch = _ch()
    card = ch.handle_command("/review")
    ch.dispatch_callback(next(c for c in _cbs(card) if c.startswith("rev:f:")))
    assert ar.is_awaiting_free() is True
    ch.handle_command("/finance")                        # تغییرِ زمینه
    assert ar.is_awaiting_free() is False
    assert ch.handle_command("سلام") is None             # پیامِ نامرتبط به حسابدار نمی‌رود


def t_d_stop_ends():
    _seed_store()
    ch = _ch()
    ch.handle_command("/review")
    r = ch.dispatch_callback("rev:x")
    assert "ایستاد" in str(r) or "جلسه" in str(r), r
    assert ar.is_active() is False


def t_e_freetext_ignored_when_not_in_review():
    _seed_store()
    ar.stop()                                           # جلسه فعال نیست
    ch = _ch()
    # پیامِ آزادِ نامرتبط نباید چیزی برگرداند (None = نادیده)
    assert ch.handle_command("سلام خوبی") is None


if __name__ == "__main__":
    for f in (t_a_review_start_gives_question_card, t_b_callback_answer_applies_and_advances,
              t_c_freetext_flow_proposes_then_confirms, t_f_need_clarify_keeps_listening,
              t_g_slash_clears_awaiting, t_d_stop_ends,
              t_e_freetext_ignored_when_not_in_review):
        f()
        print("ok", f.__name__)
    print("PASS test_review_telegram")
