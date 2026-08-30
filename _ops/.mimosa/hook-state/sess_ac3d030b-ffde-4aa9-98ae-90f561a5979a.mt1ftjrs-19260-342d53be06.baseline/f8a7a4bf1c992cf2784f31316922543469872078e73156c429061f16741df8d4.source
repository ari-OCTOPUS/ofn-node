#!/usr/bin/env python3
"""test_books_telegram.py — لایهٔ تلگرامِ /books (فازِ ۱، 2026-07-16).
اثبات: /books کارتِ پیشنهاد با دکمه‌های هویت‌دار (txn_id) · jrn:a ثبتِ واقعی در ledger +
کارتِ بعدی · تپِ تکراری امن («قبلاً تصمیم‌گرفته»، بدونِ ثبتِ دوم) · jrn:r رد · صفِ خالی
صادق · بخشِ دفتر در /finance. mini-vault harness (profile واقعیِ live لود نمی‌شود چون
ORG_ROOT هارنسی است — profile مصنوعی در مسیرِ هارنس می‌نویسیم)."""
import json
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))
sys.path.insert(0, str(_HERE.parent))
sys.path.insert(0, str(_HERE.parent / "budget"))
sys.path.insert(0, str(_HERE.parent / "legs"))

import harness  # noqa: E402
ENV = harness.setup("books_telegram")

from approval_channel import TelegramApprovalChannel  # noqa: E402
import journal_bridge as jb  # noqa: E402
import ledger_core as lc     # noqa: E402


def _seed():
    """store با یک confirmedِ قابلِ‌ثبت + profile در مسیرِ هارنس؛ صف/دفترِ قبلی پاک."""
    sp = jb._store_path()
    sp.parent.mkdir(parents=True, exist_ok=True)
    sp.write_text(json.dumps({"txns": [
        {"id": "b1", "date": "2026-07-10", "amount_cents": 594000,
         "desc": "PAYMENT FROM CLIENT 12345678", "owner": "abbas", "ptype": "income",
         "review": "confirmed", "source": "pocketsmith-api"},
        {"id": "b2", "date": "2026-07-11", "amount_cents": -11000,
         "desc": "BUNNINGS", "owner": "armin", "ptype": "expense", "review": "confirmed",
         "source": "pocketsmith-api"},
    ]}, ensure_ascii=False), "utf-8")
    lc._profile_path().parent.mkdir(parents=True, exist_ok=True)
    lc._profile_path().write_text(json.dumps(
        {"entities": [{"entity_id": "armin-abn", "gst_registered": True}],
         "lock_date": None}, ensure_ascii=False), "utf-8")
    qp = jb._queue_path()
    if qp.exists():
        qp.unlink()
    jdir = lc._ledger_dir()
    for f in ("journals.jsonl", "audit.jsonl"):
        p = jdir / f
        if p.exists():
            p.unlink()


def _cbs(card):
    return [b["callback_data"] for row in card["reply_markup"]["inline_keyboard"] for b in row]


def t_a_books_shows_proposal_card():
    _seed()
    out = TelegramApprovalChannel().handle_command("/books")
    assert isinstance(out, dict) and "reply_markup" in out, out
    # از 2026-07-18 (UX-SPEC §۳.۴): header «ثبتِ نهایی»، بدونِ Dr/Cr/ثبتِ دوطرفه
    assert "ثبتِ نهایی" in out["text"], out
    assert "Dr" not in out["text"], "Dr نباید در نسخهٔ ساده دیده شود"
    assert "ثبتِ دوطرفه" not in out["text"], "اصطلاحِ double-entry نباید دیده شود"
    assert "12345678" not in out["text"], "شماره‌حساب باید scrub شده باشد"
    cds = _cbs(out)
    assert any(c.startswith("jrn:a:") for c in cds), cds
    for c in cds:                                    # صفر مسیرِ پول/act
        assert not c.startswith(("app:", "act:")), c


def t_b_approve_posts_and_double_tap_safe():
    _seed()
    ch = TelegramApprovalChannel()
    card = ch.handle_command("/books")
    ok_cb = next(c for c in _cbs(card) if c.startswith("jrn:a:"))
    r = ch.dispatch_callback(ok_cb)
    assert isinstance(r, dict) and "ثبت شد" in r["text"], r
    tb = lc.trial_balance()
    assert tb["balanced"] and tb["total_debit_cents"] > 0, tb
    n1 = len(lc._read_ledger(None)["journals"])
    # تپِ دوبارهٔ همان دکمه (کارتِ کهنه) → امن، بدونِ ثبتِ دوم
    r2 = ch.dispatch_callback(ok_cb)
    assert "قبلاً" in str(r2), r2
    assert len(lc._read_ledger(None)["journals"]) == n1


def t_c_reject_then_empty_honest():
    _seed()
    ch = TelegramApprovalChannel()
    card = ch.handle_command("/books")
    # ردِ هر دو
    for _ in range(2):
        cds = _cbs(card) if isinstance(card, dict) else []
        rej = next((c for c in cds if c.startswith("jrn:r:")), None)
        if rej is None:
            break
        card = ch.dispatch_callback(rej)
    out = ch.handle_command("/books")
    # از 2026-07-18: «چیزی برای ثبتِ نهایی نیست» (header فارسیِ ساده، UX-SPEC §۳.۴)
    txt = out if isinstance(out, str) else (out.get("text", "") if isinstance(out, dict) else str(out))
    assert "نیست" in txt or "خالی" in txt, txt


def t_d_finance_shows_ledger_section():
    """بخشِ دفتر/ATO فقط در نسخهٔ EXPERT (مالک) — نسخهٔ ساده برای آرمین/عباس این‌ها را نمی‌بیند.
    از 2026-07-18: _finance_text ساده است؛ بخشِ دوطرفه در _finance_text_expert."""
    _seed()
    ch = TelegramApprovalChannel()
    card = ch.handle_command("/books")
    ch.dispatch_callback(next(c for c in _cbs(card) if c.startswith("jrn:a:")))
    txt_expert = ch._finance_text_expert()
    assert "دفترِ داخلی" in txt_expert, txt_expert       # ریلِ خانوادگی (two-rails)
    assert "ریلِ شرکت" in txt_expert, txt_expert         # ریلِ ATO (خاموشِ صادق در هارنس)
    assert "Dr" in txt_expert and "Cr" in txt_expert, txt_expert
    # و نسخهٔ ساده این‌ها را پنهان می‌کند:
    txt_simple = ch._finance_text()
    assert "Dr" not in txt_simple, "نسخهٔ ساده نباید Dr را نشان دهد"
    assert "دفترِ داخلی" not in txt_simple, "نسخهٔ ساده نباید دفترِ داخلی را نشان دهد"


def t_e_acct_sync_dispatch_via_callback():
    """Regression guard (2026-07-18، فاز ۵.۳): callback acct:sync باید از طریقِ
    dispatch_callback به _cmd_acct_sync برسد (همانند /sync مستقیم). قبل از این، فقط
    /sync دستی تست می‌شد، نه مسیرِ دکمه."""
    _seed()
    ch = TelegramApprovalChannel()
    # مسیرِ callback (دکمهٔ «🔄 تازه‌ها» در finance tab)
    out = ch.dispatch_callback("acct:sync")
    # _cmd_acct_sync همیشه dict با text+reply_markup برمی‌گرداند
    assert isinstance(out, dict) and "text" in out and "reply_markup" in out, out
    # header فارسیِ ساده (UX-SPEC §۳.۳)
    assert "تازه‌ها" in out["text"], out["text"]


def t_f_finance_expert_command_and_callback():
    """Regression guard (2026-07-18، فاز ۲.۲/۲.۳): /finance! و acct:finance_expert هر دو
    به نسخهٔ expert می‌رسند، و دکمهٔ برگشت به ساده را دارند."""
    _seed()
    ch = TelegramApprovalChannel()
    # مسیرِ دستور
    out_cmd = ch.handle_command("/finance!")
    assert isinstance(out_cmd, dict), out_cmd
    assert "expert" in out_cmd["text"].lower() or "دارایی" in out_cmd["text"], out_cmd["text"]
    # دکمهٔ برگشت به ساده
    cds = _cbs(out_cmd) if isinstance(out_cmd, dict) and "reply_markup" in out_cmd else []
    assert any("menu:finance" in c for c in cds), f"دکمهٔ برگشت به ساده نیست: {cds}"
    # مسیرِ callback (دکمهٔ «🔬 نسخهٔ کامل» در finance tab)
    out_cb = ch.dispatch_callback("acct:finance_expert")
    assert isinstance(out_cb, dict) and "text" in out_cb, out_cb


if __name__ == "__main__":
    for f in (t_a_books_shows_proposal_card, t_b_approve_posts_and_double_tap_safe,
              t_c_reject_then_empty_honest, t_d_finance_shows_ledger_section,
              t_e_acct_sync_dispatch_via_callback, t_f_finance_expert_command_and_callback):
        f()
        print("ok", f.__name__)
    print("PASS test_books_telegram")
