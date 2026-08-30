"""test_mirror_room.py — تستِ متخاصمِ اتاقِ آینه (گفتگو با لایهٔ خودآگاهی).

این اتاق سه چیزِ تازه دارد که هیچ‌کدام قبلاً وجود نداشت: حافظهٔ گفتگو، لایهٔ
تصحیحِ ماندگارِ مالک، و contextِ خودشناسی. هر سه سطحِ حمله‌اند:
  · حافظه‌ای که با یک خطِ خراب کور شود، بی‌صدا گفتگو را یتیم می‌کند.
  · تصحیحی که ثبت نشود یا بازنویسی شود، یعنی همان اشتباه فردا تکرار می‌شود.
  · و مثلِ بقیهٔ مسیرهای گران: مغزِ رایگان نباید جای مغزِ پولی بنشیند.

و مهم‌ترین مرزِ این اتاق: **فقط حرف**. هیچ اجرا.
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
ENV = harness.setup("mirror-room")

import mirror_room as mr   # noqa: E402
import ask_brain as ab     # noqa: E402


def _on(v=True):
    if v:
        os.environ[mr.FLAG] = "1"
        os.environ[ab.FLAG] = "1"
    else:
        os.environ.pop(mr.FLAG, None)
        os.environ.pop(ab.FLAG, None)


def _reset():
    for p in (mr.HISTORY, mr.CORRECTIONS, ab.STATE):
        try:
            p.unlink()
        except OSError:
            pass
    ab._MEMO.update(date="", used=0, last_ts=0.0)


def _fn(text="ج" * 200, ok=True, tier="primary", fallback=None, calls=None):
    calls = calls if calls is not None else []

    def f(task, prompt, system="", max_tokens=400, **kw):
        calls.append({"prompt": prompt, "system": system,
                      "max_tokens": max_tokens, "tier": kw.get("tier")})
        out = {"ok": ok, "text": text, "model": "fugu", "tier": tier}
        if fallback:
            out["fallback_from"] = fallback
        return out

    f._calls = calls
    return f


# ─── گیت ────────────────────────────────────────────────────────────────────
def t_flag_off_is_silent():
    _on(False)
    _reset()
    f = _fn()
    r = mr.ask("سلام", ask_fn=f)
    assert r == {"ok": False, "reason": "flag-off"}, r
    assert not f._calls and not mr.HISTORY.exists()


# ─── حافظهٔ گفتگو ───────────────────────────────────────────────────────────
def t_the_conversation_actually_remembers():
    """بدونِ حافظه، «همان قبلی را ادامه بده» بی‌معنی است."""
    _on()
    _reset()
    try:
        f = _fn(text="جوابِ اول " * 20)
        mr.ask("سؤالِ یکم", ask_fn=f, now=1000.0)
        f2 = _fn(text="جوابِ دوم " * 20)
        mr.ask("سؤالِ دوم", ask_fn=f2, now=1000.0 + ab.MIN_GAP_S + 1)
        p = f2._calls[0]["prompt"]
        assert "سؤالِ یکم" in p, "نوبتِ قبلی در promptِ دوم نیست — حافظه کار نمی‌کند"
        assert "جوابِ اول" in p, "جوابِ قبلیِ خودش را نمی‌بیند"
        assert len(mr.recent_turns()) == 2
    finally:
        _on(False)


def t_history_is_windowed_not_unbounded():
    """گفتگوی طولانی نباید prompt را بی‌کران بزرگ کند."""
    _on()
    _reset()
    try:
        t = 1000.0
        for i in range(mr.TURNS + 6):
            t += ab.MIN_GAP_S + 1
            os.environ["TG_ASK_BRAIN_DAILY"] = "40"
            mr.ask(f"سؤال {i}", ask_fn=_fn(text=f"جواب {i} " * 20), now=t)
        assert len(mr.recent_turns()) == mr.TURNS, len(mr.recent_turns())
    finally:
        os.environ.pop("TG_ASK_BRAIN_DAILY", None)
        _on(False)


def t_one_corrupt_history_line_does_not_blind_the_memory():
    _on()
    _reset()
    try:
        mr._append(mr.HISTORY, {"q": "خوب", "a": "باشد"})
        with open(mr.HISTORY, "a", encoding="utf-8") as f:
            f.write('{"q": "نصفه\n')
        mr._append(mr.HISTORY, {"q": "دوم", "a": "بله"})
        turns = mr.recent_turns()
        assert len(turns) == 2, f"خطِ خراب حافظه را کور کرد: {turns}"
    finally:
        _on(False)


# ─── لایهٔ تصحیح (قلبِ «با هم بهترش کنیم») ──────────────────────────────────
def t_a_correction_is_detected_and_persisted():
    _on()
    _reset()
    try:
        f = _fn()
        r = mr.ask("نه، این اشتباه است — لگِ ماینینگ اصلاً هدفِ من نیست",
                   ask_fn=f, now=1000.0)
        assert r["ok"] and r["recorded_correction"] is True, r
        c = mr.corrections()
        assert c and "ماینینگ" in c[0], c
    finally:
        _on(False)


def t_a_plain_question_is_not_mistaken_for_a_correction():
    _on()
    _reset()
    try:
        for q in ("وضعت چطور است؟", "چه چیزی یاد گرفتی؟", "امروز چه کردی"):
            r = mr.ask(q, ask_fn=_fn(), now=1000.0 + len(q) * 100)
            assert not r.get("recorded_correction"), q
        assert not mr.corrections(), mr.corrections()
    finally:
        _on(False)


def t_corrections_reach_the_next_conversation():
    """اگر تصحیح به contextِ بعدی نرود، ماندگاری‌اش بی‌معنی است."""
    _on()
    _reset()
    try:
        mr.record_correction("نه، درآمدِ زیمان صفر نیست")
        f = _fn()
        mr.ask("وضعِ زیمان؟", ask_fn=f, now=1000.0)
        assert "درآمدِ زیمان صفر نیست" in f._calls[0]["prompt"], \
            "تصحیحِ ثبت‌شده به گفتگوی بعدی نرسید"
    finally:
        _on(False)


def t_corrections_are_append_only_never_overwritten():
    _reset()
    mr.record_correction("اول")
    mr.record_correction("دوم")
    mr.record_correction("سوم")
    c = mr.corrections()
    assert c == ["اول", "دوم", "سوم"], c
    raw = mr.CORRECTIONS.read_text("utf-8").splitlines()
    assert len(raw) == 3, "تصحیح بازنویسی شد"


def t_an_empty_correction_is_not_recorded():
    _reset()
    assert mr.record_correction("") is False
    assert mr.record_correction("   ") is False
    assert not mr.corrections()


# ─── context ────────────────────────────────────────────────────────────────
def t_the_context_is_self_knowledge_not_raw_state():
    """تفاوتِ این اتاق با ask_brain همین است: فهمِ خودش، نه وضعیتِ خام."""
    _on()
    _reset()
    try:
        import opslib
        p = opslib.STATE_DIR / "doctor" / "self-knowledge-latest.json"
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps({
            "version": 27, "focus": "خطای پرتکرار", "stable_cycles": 11,
            "understanding": {"anatomy": "۵ لِگ", "physiology": "درآمد>۰",
                              "pathology": [{"symptom": "س", "root_cause": "نامعلوم"}]},
            "trajectory": {"converging": False},
        }, ensure_ascii=False), "utf-8")
        f = _fn()
        mr.ask("خودت را چطور می‌بینی؟", ask_fn=f, now=1000.0)
        p2 = f._calls[0]["prompt"]
        assert "فهمِ_من_از_خودم" in p2 and "خطای پرتکرار" in p2, p2[:300]
        card = mr.know_card()
        assert "نسخهٔ 27" in card and "۵ لِگ" in card, card
    finally:
        _on(False)


def t_missing_self_knowledge_does_not_crash():
    import opslib
    p = opslib.STATE_DIR / "doctor" / "self-knowledge-latest.json"
    bak = p.read_text("utf-8") if p.exists() else None
    try:
        if p.exists():
            p.unlink()
        assert isinstance(mr.self_context(), dict)
        assert isinstance(mr.know_card(), str)
    finally:
        if bak is not None:
            p.write_text(bak, "utf-8")


# ─── مرزهای مشترک ───────────────────────────────────────────────────────────
def t_a_free_brain_answer_is_refused():
    _on()
    _reset()
    try:
        for kw in ({"fallback": "primary: failed"}, {"tier": "local"}):
            _reset()
            r = mr.ask("سؤال", ask_fn=_fn(**kw), now=1000.0)
            assert not r["ok"] and r["reason"] == "not-a-paid-brain", (kw, r)
    finally:
        _on(False)


def t_the_quota_is_shared_with_ask_brain_not_doubled():
    """دو شمارنده یعنی مالک می‌تواند دو برابرِ سقف خرج کند بی‌آنکه بداند."""
    _on()
    _reset()
    try:
        os.environ["TG_ASK_BRAIN_DAILY"] = "2"
        t = 1000.0
        ok = 0
        for _ in range(6):
            t += ab.MIN_GAP_S + 1
            if mr.ask("سؤال", ask_fn=_fn(), now=t)["ok"]:
                ok += 1
        assert ok == 2, f"{ok} از ۶ — سهمیه مشترک نیست"
    finally:
        os.environ.pop("TG_ASK_BRAIN_DAILY", None)
        _on(False)


def t_this_room_only_talks():
    """مرزِ اصلی. سنجش روی **کد** است نه متن: نسخهٔ اولِ این تست روی رشتهٔ خام
    grep می‌کرد و کلمهٔ «effector» را در همان جمله‌ای گرفت که وجودِ effector را
    نفی می‌کرد. حالا AST پارس می‌شود و فقط import/call واقعی شمرده می‌شود."""
    import ast
    tree = ast.parse(Path(mr.__file__).read_text("utf-8"))
    banned = {"subprocess", "urllib", "requests", "socket", "http",
              "capability_gate", "arm_gate", "effector_gate"}
    imported, called = set(), set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(a.name.split(".")[0] for a in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module.split(".")[0])
        elif isinstance(node, ast.Call):
            fn = node.func
            name = getattr(fn, "attr", None) or getattr(fn, "id", None)
            if name:
                called.add(name)
    leaked = banned & imported
    assert not leaked, f"ماژولِ اجرا/شبکه import شده: {sorted(leaked)}"
    for danger in ("system", "popen", "exec", "eval", "apply_approved", "send"):
        assert danger not in called, f"فراخوانِ خطرناک در اتاقِ گفتگو: {danger}"


def t_the_system_prompt_forbids_claiming_consciousness():
    """مرزِ صداقت: این اتاق دربارهٔ خودآگاهی است، پس دقیقاً همین‌جا وسوسهٔ
    ادعای بزرگ بیشترین است."""
    s = mr._SYSTEM
    assert "احساس" in s and "آگاهی" in s, "system prompt مرزِ ادعا را نمی‌بندد"
    assert "نمی‌دانم" in s, "اجازهٔ «نمی‌دانم» داده نشده — مدل حدس می‌زند"


def t_the_card_marks_a_recorded_correction():
    body, kb = mr.card("جواب", "fugu", corrected=True)
    assert "ثبت شد" in body, body
    assert kb and len(kb[0]) == 2
    body2, _ = mr.card("جواب", "fugu", corrected=False)
    assert "ثبت شد" not in body2


def t_the_mirror_topic_has_no_periodic_digest():
    """اتاقِ گفتگو نباید با نویزِ روزانه پر شود."""
    sys.path.insert(0, str(_HERE.parent / "telegram_center"))
    import render as r
    assert r.render_leg_digest("mirror", {"status": "⚪", "detail": "x"}) == ""
    assert r.render_leg_digest("lead", {"status": "🟢", "detail": "x"}) != ""
    assert "mirror" in r.LEGS and r.LEG_ICONS.get("mirror")


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'✅' if not failed else '❌'} test_mirror_room: "
          f"{len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
