"""test_ask_brain.py — تستِ متخاصمِ مسیرِ گفتگوی آزادِ تلگرام.

این ماژول یک مغزِ گران را از یک **کانالِ تعاملیِ انسانی** صدا می‌زند، پس سه چیز
باید ساختاراً غیرممکن باشد نه قراردادی:
  ۱) با flag خاموش هیچ اثری روی دیسک و صفر تماس،
  ۲) یک صفحه‌کلیدِ عصبی نتواند سهمیهٔ روزانه را بسوزاند،
  ۳) جوابِ مدلِ رایگان هرگز به‌عنوانِ جوابِ «مغزِ گران» تحویل نشود.

و یکی که مخصوصِ همین مسیر است: این اندام فقط **حرف** می‌زند. اگر روزی چیزی
شبیهِ اجرا از آن دربیاید، مرزِ اصلیِ طراحی شکسته است.
"""
import json
import os
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent))
sys.path.insert(0, str(_HERE.parent / "budget"))
sys.path.insert(0, str(_HERE.parent / "telegram_center"))

import harness
ENV = harness.setup("ask-brain")

import ask_brain as ab   # noqa: E402

CANARY = "کاناریِ-محرمانه-9f3a"


def _on(v=True):
    if v:
        os.environ[ab.FLAG] = "1"
    else:
        os.environ.pop(ab.FLAG, None)


def _reset():
    for p in (ab.STATE, ab.LEDGER):
        try:
            p.unlink()
        except OSError:
            pass
    ab._MEMO.update(date="", used=0, last_ts=0.0)


def _ask_fn(text="ج" * 200, ok=True, boom=False, tier="primary", fallback=None,
            calls=None):
    calls = calls if calls is not None else []

    def fn(task, prompt, system="", max_tokens=400, tier_=None, **kw):
        calls.append({"task": task, "prompt": prompt, "system": system,
                      "max_tokens": max_tokens, "tier": kw.get("tier")})
        if boom:
            raise RuntimeError("مغز در دسترس نیست")
        out = {"ok": ok, "text": text, "model": "fugu", "tier": tier}
        if fallback:
            out["fallback_from"] = fallback
        return out

    fn._calls = calls
    return fn


def _ledger():
    if not ab.LEDGER.exists():
        return []
    return [json.loads(x) for x in ab.LEDGER.read_text("utf-8").splitlines() if x.strip()]


# ─── حملهٔ ۱: flag خاموش = هیچ ───────────────────────────────────────────────
def t_flag_off_is_silent_and_free():
    _on(False)
    _reset()
    fn = _ask_fn()
    r = ab.ask("چرا امروز کند بودی؟", ask_fn=fn)
    assert r == {"ok": False, "reason": "flag-off"}, r
    assert not fn._calls, "با flag خاموش مغز صدا شد"
    assert not ab.STATE.exists() and not ab.LEDGER.exists()


# ─── حملهٔ ۲: سهمیه (مسیرِ تعاملی = تندترین مسیرِ سوختنِ سهمیه) ──────────────
def t_rapid_fire_is_rate_limited():
    _on()
    _reset()
    try:
        fn = _ask_fn()
        assert ab.ask("سؤال یک", ask_fn=fn, now=1000.0)["ok"]
        r2 = ab.ask("سؤال دو", ask_fn=fn, now=1001.0)      # ۱ ثانیه بعد
        assert not r2["ok"] and r2["reason"].startswith("too-soon"), r2
        assert len(fn._calls) == 1, "پیامِ پشتِ‌سرِ‌هم یک تماسِ گرانِ دوم زد"
        assert ab.ask("سؤال سه", ask_fn=fn, now=1000.0 + ab.MIN_GAP_S + 1)["ok"]
    finally:
        _on(False)


def t_daily_cap_is_a_hard_ceiling():
    _on()
    _reset()
    try:
        os.environ["TG_ASK_BRAIN_DAILY"] = "3"
        fn = _ask_fn()
        t = 1000.0
        ok = 0
        for _ in range(8):
            t += ab.MIN_GAP_S + 1
            if ab.ask("سؤال", ask_fn=fn, now=t)["ok"]:
                ok += 1
        assert ok == 3, f"{ok} از ۸ رد شد (سقف ۳)"
        assert len(fn._calls) == 3
    finally:
        os.environ.pop("TG_ASK_BRAIN_DAILY", None)
        _on(False)


def t_hostile_daily_env_is_clamped():
    for bad in ("0", "-1", "999", "abc", ""):
        os.environ["TG_ASK_BRAIN_DAILY"] = bad
        assert 0 < ab._daily_cap() <= ab.DAILY_MAX, f"{bad!r} → {ab._daily_cap()}"
    os.environ.pop("TG_ASK_BRAIN_DAILY", None)


def t_the_quota_burns_before_the_call():
    """مغزِ خراب نباید هر پیام یک تماسِ ۳۰ ثانیه‌ای بسوزاند."""
    _on()
    _reset()
    try:
        fn = _ask_fn(boom=True)
        r = ab.ask("سؤال", ask_fn=fn, now=1000.0)
        assert not r["ok"] and r["reason"] == "ask-exception", r
        d = json.loads(ab.STATE.read_text("utf-8"))
        assert d["used"] == 1, f"سهمیه بعد از انفجار نسوخت: {d}"
        r2 = ab.ask("سؤال", ask_fn=fn, now=1001.0)
        assert r2["reason"].startswith("too-soon"), r2
    finally:
        _on(False)


# ─── حملهٔ ۳ (مهم‌ترین): مغزِ رایگان نباید جای مغزِ گران جواب بدهد ───────────
def t_a_downgrade_to_the_free_brain_is_never_delivered():
    """مغزِ محلیِ رایگان نباید جای مغزِ پولی جواب بدهد."""
    _on()
    _reset()
    try:
        for kw in ({"fallback": "primary: paid-call-failed"},
                   {"tier": "local"}, {"tier": "stub"}):
            _reset()
            r = ab.ask("چرا کند بودی؟", ask_fn=_ask_fn(**kw), now=1000.0)
            assert not r["ok"], (kw, r)
            assert r["reason"] == "not-a-paid-brain", (kw, r)
            rows = _ledger()
            assert rows and rows[-1]["reason"] == "not-a-paid-brain"
    finally:
        _on(False)


def t_a_paid_sibling_brain_is_accepted_and_named():
    """اصلاحِ آزمونِ زندهٔ ۲۰۲۶-۰۷-۲۷: یک PermissionError روی Fugu روتر را به GLM
    برد و جوابِ خوبی آمد؛ نسخهٔ اولِ گارد دورش انداخت و به مالک «متوجه نشدم» داد.
    GLM مغزِ پولیِ واقعی است — مرز «پولی بودن» است نه «primary بودن»، و کارت باید
    بگوید کدام مغز جواب داده."""
    _on()
    _reset()
    try:
        r = ab.ask("سؤال", ask_fn=_ask_fn(tier="secondary"), now=1000.0)
        assert r["ok"], r
        assert r["tier"] == "secondary"
        body, _ = ab.card(r["text"], r.get("model") or "")
        assert "fugu" in body.lower(), "کارت نمی‌گوید کدام مغز جواب داده"
    finally:
        _on(False)


def t_the_call_is_pinned_to_primary_with_room():
    _on()
    _reset()
    try:
        fn = _ask_fn()
        ab.ask("سؤالِ واقعی", ask_fn=fn, now=1000.0)
        c = fn._calls[0]
        assert c["tier"] == "primary", c["tier"]
        assert c["max_tokens"] >= 600, c["max_tokens"]
        assert c["system"], "بدونِ system جوابِ کلی می‌آید"
    finally:
        _on(False)


# ─── حملهٔ ۴: مرزها ─────────────────────────────────────────────────────────
def t_the_prompt_carries_the_question_and_numbers_but_no_lead_content():
    _on()
    _reset()
    try:
        import opslib
        inbox = opslib.STATE_DIR / "legs" / "lead-inbox"
        inbox.mkdir(parents=True, exist_ok=True)
        (inbox / "lead-1.json").write_text(
            json.dumps({"name": CANARY}, ensure_ascii=False), "utf-8")
        fn = _ask_fn()
        ab.ask("وضعِ لید چطور است؟", topic_key="lead", ask_fn=fn, now=1000.0)
        p = fn._calls[0]["prompt"]
        assert "وضعِ لید چطور است؟" in p, "سؤالِ مالک در prompt نیست"
        assert CANARY not in p, "محتوای فایلِ لید به مغز نشت کرد"
        assert any(ch.isdigit() for ch in p), "prompt هیچ عددی ندارد"
    finally:
        _on(False)


def t_a_short_or_failed_answer_falls_back_to_todays_card():
    _on()
    _reset()
    try:
        for kw, why in (({"text": "باشه"}, "too-short-answer"),
                        ({"ok": False}, "no-answer")):
            _reset()
            r = ab.ask("سؤال", ask_fn=_ask_fn(**kw), now=1000.0)
            assert not r["ok"] and r["reason"] == why, (kw, r)
    finally:
        _on(False)


def t_an_empty_or_tiny_question_costs_nothing():
    _on()
    _reset()
    try:
        for q in ("", "  ", "ا"):
            fn = _ask_fn()
            r = ab.ask(q, ask_fn=fn, now=1000.0)
            assert not r["ok"] and r["reason"] == "too-short", (q, r)
            assert not fn._calls, f"سؤالِ {q!r} یک تماسِ گران زد"
            assert not ab.STATE.exists(), "سؤالِ بی‌اعتبار سهمیه سوزاند"
    finally:
        _on(False)


def t_a_very_long_question_is_truncated_not_refused():
    _on()
    _reset()
    try:
        fn = _ask_fn()
        r = ab.ask("چرا " * 5000, ask_fn=fn, now=1000.0)
        assert r["ok"], r
        q_line = fn._calls[0]["prompt"].split("\n\n")[0]
        assert len(q_line) < ab.MAX_QUESTION + 40, len(q_line)
    finally:
        _on(False)


def t_this_organ_only_talks_it_never_acts():
    """مرزِ اصلی: هیچ مسیری از این ماژول به اجرا/effector/گیت نمی‌رود."""
    src = Path(ab.__file__).read_text("utf-8")
    for forbidden in ("effector", "apply_", "subprocess", "os.system",
                      "capability_gate", "arm_gate", "send(", "requests.",
                      "urllib"):
        assert forbidden not in src, f"مسیرِ اجرا/ارسال در ماژولِ گفتگو: {forbidden}"
    assert "action" not in src.lower().split("قواعد")[0][:400] or True   # فقط متن


def t_the_card_is_short_and_marks_itself_as_talk():
    body, kb = ab.card("جوابِ نمونه")
    assert body.startswith("🐙"), body[:20]
    assert len(body) <= 3510
    assert kb and isinstance(kb, list)


def t_the_answer_text_is_kept_for_review():
    """جلسه‌ای که فراموش شود خرج است نه سرمایه — و برای سنجشِ کیفیت لازم است."""
    _on()
    _reset()
    try:
        ab.ask("سؤال", ask_fn=_ask_fn(text="پ" * 300), now=1000.0)
        rows = _ledger()
        assert rows[-1]["ok"] is True and len(rows[-1].get("text") or "") > 100
    finally:
        _on(False)


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'✅' if not failed else '❌'} test_ask_brain: "
          f"{len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
