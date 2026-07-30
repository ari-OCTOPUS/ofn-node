"""test_initiative_and_autonomy.py — اختاپوس شروع می‌کند، و مرزِ اختیارش.

دو رأیِ مالک ۲۰۲۶-۰۷-۲۷:
  · «آره، و حتی از من سؤال بپرسد» — رابطه دوطرفه شود.
  · اختیار روی سه دستهٔ بی‌خطر: فقط‌خواندنی، تمیزکاریِ خودش، ریتمِ خودش.

خطرِ اصلیِ اولی **سرریز** است: ابتکارِ پرحرف کاری می‌کند که مالک کلِ کانال را
خاموش کند، و آن‌وقت همه‌چیز را از دست می‌دهیم. پس سکوت باید پیش‌فرض باشد.
خطرِ اصلیِ دومی **لغزشِ مرز** است: «فقط‌خواندنی» نباید کم‌کم به کاری تبدیل شود
که پول یا ارسال را لمس می‌کند.
"""
import json
import os
import sys
import time
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))
import harness   # noqa: E402
ENV = harness.setup("initiative-autonomy")

_OPS = harness.REAL_VAULT / "_ops"
for _p in (str(_OPS), str(_OPS / "budget"), str(_OPS / "telegram_center")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import opslib             # noqa: E402
import initiative as iv   # noqa: E402
import autonomy_grant as ag  # noqa: E402

# ⚠️ زمانِ پایه باید از epoch بزرگ‌تر از MIN_GAP_S باشد. نسخهٔ اولِ این فایل
# `now=1000.0` می‌داد و **همهٔ** تست‌ها too-soon می‌گرفتند — یعنی سبز که نبود،
# ولی بدتر: اگر گاردِ فاصله را برمی‌داشتم، همان تست‌ها سبز می‌شدند و باگ را
# پنهان می‌کردند. اشتباه در ابزارِ سنجش بود نه در کد.
_T0 = 1_800_000_000.0

GOOD = json.dumps({"نوع": "سوال", "متن": "ا" * 90,
                   "چرا_حالا": "چون هدفِ ماه به آن گره خورده",
                   "ارزشش_را_ندارد": False}, ensure_ascii=False)


def _on(v=True):
    if v:
        os.environ[iv.FLAG] = "1"
    else:
        os.environ.pop(iv.FLAG, None)


def _reset():
    for p in (iv.STATE, iv.LEDGER):
        try:
            p.unlink()
        except OSError:
            pass


def _fn(text=GOOD, ok=True, tier="primary", calls=None):
    calls = calls if calls is not None else []

    def f(task, prompt, system="", max_tokens=400, **kw):
        calls.append({"prompt": prompt, "system": system, "tier": kw.get("tier")})
        return {"ok": ok, "text": text, "model": "fugu", "tier": tier}

    f._calls = calls
    return f


# ─── ابتکار: سکوت پیش‌فرض است ───────────────────────────────────────────────
def t_flag_off_never_speaks():
    _on(False)
    _reset()
    f = _fn()
    assert iv.speak(ask_fn=f)["reason"] == "flag-off"
    assert not f._calls and not iv.STATE.exists()


def t_the_daily_cap_is_small_and_the_gap_is_hours():
    """پرحرفی = خاموش‌شدنِ کلِ کانال. سقف باید تنگ باشد."""
    assert iv.DAILY_DEFAULT <= 3, iv.DAILY_DEFAULT
    assert iv.MIN_GAP_S >= 3600, iv.MIN_GAP_S
    _on()
    _reset()
    try:
        f = _fn()
        t = _T0
        spoke = 0
        for _ in range(8):
            t += iv.MIN_GAP_S + 1
            if iv.speak(ask_fn=f, now=t).get("ok"):
                spoke += 1
        assert spoke == iv.DAILY_DEFAULT, f"{spoke} پیام — سقف {iv.DAILY_DEFAULT}"
    finally:
        _on(False)


def t_two_messages_cannot_arrive_back_to_back():
    _on()
    _reset()
    try:
        f = _fn()
        assert iv.speak(ask_fn=f, now=_T0)["ok"]
        r = iv.speak(ask_fn=f, now=_T0 + 60)
        assert not r["ok"] and r["reason"] == "too-soon", r
        assert len(f._calls) == 1, "پیامِ دوم یک تماسِ گران زد"
    finally:
        _on(False)


def t_it_stays_silent_during_quiet_hours():
    _on()
    _reset()
    real = iv._quiet_now
    iv._quiet_now = lambda now=None: True  # امضا حالا زمان می‌گیرد
    try:
        f = _fn()
        r = iv.speak(ask_fn=f, now=_T0)
        assert r["reason"] == "quiet-hours", r
        assert not f._calls, "در ساعتِ سکوت مغز صدا شد"
        assert not iv.STATE.exists(), "در ساعتِ سکوت سهمیه سوخت"
    finally:
        iv._quiet_now = real
        _on(False)


def t_the_model_may_decline_to_speak():
    """سکوت جوابِ محترمی است — و باید ثبت شود تا بدانیم چند بار پیش آمد."""
    _on()
    _reset()
    try:
        quiet = json.dumps({"نوع": "خبر", "متن": "چیزی نیست",
                            "ارزشش_را_ندارد": True}, ensure_ascii=False)
        r = iv.speak(ask_fn=_fn(text=quiet), now=_T0)
        assert not r["ok"] and r["reason"] == "self-declined", r
        rows = [json.loads(x) for x in iv.LEDGER.read_text("utf-8").splitlines() if x.strip()]
        assert rows and rows[-1]["reason"] == "self-declined"
    finally:
        _on(False)


def t_the_quota_burns_before_the_call():
    _on()
    _reset()
    try:
        def boom(*a, **k):
            raise RuntimeError("مغز مرد")
        r = iv.speak(ask_fn=boom, now=_T0)
        assert not r["ok"], r
        assert json.loads(iv.STATE.read_text("utf-8"))["used"] == 1, \
            "سهمیه بعد از انفجار نسوخت — هر تیک یک تماسِ گران"
    finally:
        _on(False)


def t_quieter_halves_the_cap_and_never_reaches_zero():
    """دکمهٔ «کمتر حرف بزن» باید واقعاً کم کند، ولی هرگز کاملاً خفه نکند."""
    _reset()
    caps = []
    for _ in range(5):
        caps.append(iv.quieter()["cap"])
    assert caps[0] < iv.DAILY_DEFAULT or iv.DAILY_DEFAULT == 1, caps
    assert caps[-1] >= iv.DAILY_MIN >= 1, caps
    assert all(c >= 1 for c in caps), caps


def t_a_free_brain_answer_is_refused():
    _on()
    _reset()
    try:
        r = iv.speak(ask_fn=_fn(tier="local"), now=_T0)
        assert r["reason"] == "not-a-paid-brain", r
    finally:
        _on(False)


def t_a_malformed_answer_produces_no_message():
    _on()
    _reset()
    try:
        for bad in ("حرفِ آزاد", '{"نوع":"خبر"}', "{ناقص"):
            _reset()
            r = iv.speak(ask_fn=_fn(text=bad), now=_T0)
            assert not r["ok"], (bad[:20], r)
    finally:
        _on(False)


def t_the_system_prompt_invites_a_question_not_only_a_report():
    """قلبِ رأیِ مالک: «حتی از من سؤال بپرسد»."""
    assert "سوال" in iv._SYSTEM and "نمی‌دانی" in iv._SYSTEM
    assert "سکوت جوابِ محترمی است" in iv._SYSTEM


def t_the_card_offers_a_way_to_shut_it_up():
    body, kb = iv.card({"kind": "سوال", "text": "متن", "why": "چون"})
    verbs = {b["callback_data"].split(":")[0] for row in kb for b in row}
    assert "iv" in verbs, "دکمهٔ کمتر حرف بزن نیست"
    assert "سؤال" in body


def t_initiative_only_talks():
    import ast
    tree = ast.parse(Path(iv.__file__).read_text("utf-8"))
    banned = {"subprocess", "urllib", "requests", "socket"}
    imported = set()
    for n in ast.walk(tree):
        if isinstance(n, ast.Import):
            imported.update(a.name.split(".")[0] for a in n.names)
        elif isinstance(n, ast.ImportFrom) and n.module:
            imported.add(n.module.split(".")[0])
    assert not (banned & imported), sorted(banned & imported)


# ─── اختیار: مرز نباید بلغزد ────────────────────────────────────────────────
def t_autonomy_is_off_until_granted():
    os.environ.pop(ag.FLAG, None)
    for cat in ag.GRANTED:
        assert not ag.may(cat, "x")["ok"], cat


def t_the_three_granted_categories_work():
    os.environ[ag.FLAG] = "1"
    try:
        assert ag.may("read_only", "اسکنِ کد")["ok"]
        assert ag.may("self_cleanup", "state/telegram/old.json")["ok"]
        assert ag.may("own_rhythm", "daily_beat_cap", 1500)["ok"]
    finally:
        os.environ.pop(ag.FLAG, None)


def t_anything_not_granted_is_refused():
    """allowlist، نه denylist — دستهٔ ناشناخته یعنی نه."""
    os.environ[ag.FLAG] = "1"
    try:
        for cat in ("apply_code", "send_message", "pay", "", None, "READ_ONLY"):
            assert not ag.may(cat, "x")["ok"], cat
    finally:
        os.environ.pop(ag.FLAG, None)


def t_the_hard_boundary_beats_the_category():
    """حتی «فقط‌خواندنی» اگر بوی پول/ارسال/راز بدهد رد می‌شود."""
    os.environ[ag.FLAG] = "1"
    try:
        for target in ("ارسال به مشتری", "pay the invoice", "read .env",
                       "apply patch", "08 - Partner/x", "توکن را بخوان",
                       "تغییرِ flag"):
            r = ag.may("read_only", target)
            assert not r["ok"], (target, r)
    finally:
        os.environ.pop(ag.FLAG, None)


def t_cleanup_cannot_escape_state():
    os.environ[ag.FLAG] = "1"
    try:
        for bad in ("budget/budgets.yaml", "../secrets", "state/../budget/x",
                    "", "OCTOPUS-flags.cmd", "/etc/passwd"):
            assert not ag.may("self_cleanup", bad)["ok"], bad
        assert ag.may("self_cleanup", "state/deep-think/old.jsonl")["ok"]
    finally:
        os.environ.pop(ag.FLAG, None)


def t_rhythm_stays_inside_the_owners_bounds():
    os.environ[ag.FLAG] = "1"
    try:
        lo, hi = ag.RHYTHM_BOUNDS["daily_beat_cap"]
        assert ag.may("own_rhythm", "daily_beat_cap", lo)["ok"]
        assert ag.may("own_rhythm", "daily_beat_cap", hi)["ok"]
        assert not ag.may("own_rhythm", "daily_beat_cap", hi + 1)["ok"]
        assert not ag.may("own_rhythm", "daily_beat_cap", lo - 1)["ok"]
        assert not ag.may("own_rhythm", "unknown_knob", 5)["ok"]
        assert not ag.may("own_rhythm", "daily_beat_cap", "خیلی")["ok"]
    finally:
        os.environ.pop(ag.FLAG, None)


def t_the_grant_module_cannot_act():
    """این ماژول فقط **قضاوت** می‌کند؛ هیچ اجرایی در آن نیست."""
    import ast
    tree = ast.parse(Path(ag.__file__).read_text("utf-8"))
    called = {getattr(n.func, "attr", None) or getattr(n.func, "id", None)
              for n in ast.walk(tree) if isinstance(n, ast.Call)}
    for d in ("unlink", "write_text", "rmtree", "system", "run", "send"):
        assert d not in called, f"ماژولِ مرز خودش عمل می‌کند: {d}"


def t_the_injected_clock_controls_quiet_hours_too():
    """۲۰۲۶-۰۷-۲۸ — باگی که همان شب خودش را نشان داد.

    `speak(now=…)` ساعت می‌پذیرفت ولی `_quiet_now()` **نادیده‌اش می‌گرفت** و
    ساعتِ دیوار را می‌خواند. پس این فایل روزها سبز بود و **هر شب بین ۰ تا ۷
    قرمز** — یک بمبِ ساعتی که فقط وقتی مالک بیدار نبود منفجر می‌شد.

    و پیامدِ بدترش در مسیرِ زنده بود: تابعی که نیمی از رفتارش از ساعتِ تزریقی
    می‌آید و نیمِ دیگر از ساعتِ دیوار، در تست و در واقعیت دو چیزِ متفاوت است.

    این تست **مستقل از ساعتِ اجرا** است — همان چیزی که از اول باید می‌بود."""
    import datetime as _dt

    def _at(hour: int) -> float:
        d = _dt.datetime(2026, 7, 28, hour, 30, 0)
        return d.timestamp()

    # ساعتِ سکوتِ مالک ۰ تا ۷ است؛ از خودِ منبع خوانده می‌شود نه هاردکد
    import approval_channel as _ac
    a, b = _ac._quiet_hours()
    quiet_h = a if a != b else None
    if quiet_h is None:
        return                                  # سکوتی تعریف نشده — سنجیدنی نیست
    loud_h = (b + 2) % 24

    assert iv._quiet_now(_at(quiet_h)) is True, f"ساعتِ {quiet_h} باید سکوت باشد"
    assert iv._quiet_now(_at(loud_h)) is False, f"ساعتِ {loud_h} نباید سکوت باشد"

    # و مهم‌تر: `speak` باید همان ساعتِ تزریقی را ببیند، نه ساعتِ دیوار
    _on()
    _reset()
    try:
        r = iv.speak(ask_fn=_fn(), now=_at(quiet_h))
        assert r["reason"] == "quiet-hours", r
        _reset()
        r2 = iv.speak(ask_fn=_fn(), now=_at(loud_h))
        assert r2.get("reason") != "quiet-hours", r2
    finally:
        _on(False)


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'✅' if not failed else '❌'} test_initiative_and_autonomy: "
          f"{len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
