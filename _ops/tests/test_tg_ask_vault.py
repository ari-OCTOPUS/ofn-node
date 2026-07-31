#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_tg_ask_vault — سؤال از vault با ذکرِ منبع (منشورِ TG-UI، رأی ۹).

    مرزهای زیرِ آزمون: منبعِ درست cite شود · _Archive هرگز · .agentignore
    هرگز · صفر hit = «نمی‌دانم» ِ صادق بدونِ تماسِ مدل · retrieval داده است
    نه دستور · flag پیش‌فرض خاموش · نبودِ rg = دلیلِ صادق نه crash.
"""
import json
import os
import sys
from pathlib import Path

import harness

ENV = harness.setup("tg-ask-vault")

_OPS = Path(__file__).resolve().parent.parent
_TC = str(_OPS / "telegram_center")
if _TC not in sys.path:
    sys.path.insert(0, _TC)

import ask_vault as av  # noqa: E402

ROOT = Path(ENV["root"])
CANARY_ARCHIVE = "کاناری-آرشیو-x91"
CANARY_IGNORED = "کاناری-ممنوع-k44"


def _plant():
    """سه نوت + یک نوتِ آرشیو + یک نوتِ ممنوع + .agentignore ِ خودِ تست."""
    p = ROOT / "03 - Projects" / "Mining" / "کولر-ماینر.md"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("---\ntype: note\ntags: [mining]\n---\n"
                 "دمای مناسبِ دستگاه با کولر حدودِ ۶۵ درجه است.\n"
                 "کولر باید ماهانه تمیز شود.\n", "utf-8")
    q = ROOT / "07 - Knowledge" / "دانشِ-عمومی.md"
    q.parent.mkdir(parents=True, exist_ok=True)
    q.write_text("---\ntype: note\ntags: [general]\n---\n"
                 "این نوت دربارهٔ چیزِ دیگری است ولی یک بار کولر را نام می‌برد.\n",
                 "utf-8")
    a = ROOT / "_Archive" / "راز-قدیمی.md"
    a.parent.mkdir(parents=True, exist_ok=True)
    a.write_text(f"کولر ماینر — {CANARY_ARCHIVE}\n", "utf-8")
    ig = ROOT / "private-dir" / "مخفی.md"
    ig.parent.mkdir(parents=True, exist_ok=True)
    ig.write_text(f"کولر ماینر — {CANARY_IGNORED}\n", "utf-8")
    (ROOT / ".agentignore").write_text("# تست\nprivate-dir/\n", "utf-8")


_plant()


def _on(v=True):
    if v:
        os.environ[av.FLAG] = "1"
    else:
        os.environ.pop(av.FLAG, None)


def _fake_ask(text="بر اساسِ قطعه‌ها: دمای مناسب حدودِ ۶۵ درجه است.", ok=True):
    calls = []

    def fn(task, prompt, system="", max_tokens=400, **kw):
        calls.append({"task": task, "prompt": prompt, "system": system,
                      "tier": kw.get("tier")})
        return {"ok": ok, "text": text, "model": "qwen2.5:1.5b", "tier": "local"}

    fn._calls = calls
    return fn


# ── flag و پیش‌نیازها ────────────────────────────────────────────────────────
def t_flag_off_is_the_default_and_silent():
    _on(False)
    fn = _fake_ask()
    r = av.query("کولر ماینر چند درجه؟", vault_root=ROOT, ask_fn=fn)
    assert not r["ok"] and r["reason"] == "flag-off", r
    assert not fn._calls


def t_missing_rg_is_an_honest_reason_not_a_crash():
    _on()
    try:
        real_which, real_cands = av.shutil.which, av._RG_CANDIDATES
        real_env = os.environ.pop("OCTOPUS_RG_EXE", None)
        av.shutil.which = lambda name: None
        av._RG_CANDIDATES = ()
        try:
            r = av.query("کولر ماینر چند درجه؟", vault_root=ROOT,
                         ask_fn=_fake_ask())
            assert not r["ok"] and r["reason"] == "rg-not-found", r
        finally:
            av.shutil.which = real_which
            av._RG_CANDIDATES = real_cands
            if real_env is not None:
                os.environ["OCTOPUS_RG_EXE"] = real_env
    finally:
        _on(False)


# ── retrieval + citation ────────────────────────────────────────────────────
def t_the_answer_cites_the_right_note_and_ends_with_sources():
    _on()
    try:
        fn = _fake_ask()
        r = av.query("کولر ماینر چند درجه است؟", vault_root=ROOT, ask_fn=fn)
        assert r["ok"], r
        assert any("کولر-ماینر" in s for s in r["sources"]), r["sources"]
        assert all(s.endswith(".md") for s in r["sources"]), r["sources"]
        assert "منابع:" in r["answer"], r["answer"]
        tail = r["answer"].split("منابع:")[1]
        assert "[[" in tail and "کولر-ماینر" in tail, tail
        assert r["tier"] == "local", r
        assert fn._calls and fn._calls[0]["tier"] == "local"
        # قطعهٔ نوتِ منبع واقعاً به مدل رفته (نه فقط نامش)
        assert "۶۵ درجه" in fn._calls[0]["prompt"], fn._calls[0]["prompt"][:400]
    finally:
        _on(False)


def t_the_filename_match_outranks_the_passing_mention():
    _on()
    try:
        r = av.query("کولر ماینر چند درجه است؟", vault_root=ROOT,
                     ask_fn=_fake_ask(), k=1)
        assert r["ok"] and len(r["sources"]) == 1, r
        assert "کولر-ماینر" in r["sources"][0], r["sources"]
    finally:
        _on(False)


def t_archive_is_never_cited_and_never_leaks():
    _on()
    try:
        fn = _fake_ask()
        r = av.query("کولر ماینر چند درجه است؟", vault_root=ROOT, ask_fn=fn)
        blob = json.dumps(r, ensure_ascii=False) + (fn._calls[0]["prompt"]
                                                    if fn._calls else "")
        assert "_Archive" not in blob, "مسیرِ _Archive نشت کرد"
        assert CANARY_ARCHIVE not in blob, "محتوای _Archive نشت کرد"
    finally:
        _on(False)


def t_agentignore_paths_are_respected():
    _on()
    try:
        fn = _fake_ask()
        r = av.query("کولر ماینر چند درجه است؟", vault_root=ROOT, ask_fn=fn)
        blob = json.dumps(r, ensure_ascii=False) + (fn._calls[0]["prompt"]
                                                    if fn._calls else "")
        assert "private-dir" not in blob, ".agentignore رعایت نشد"
        assert CANARY_IGNORED not in blob, "محتوای مسیرِ ممنوع نشت کرد"
    finally:
        _on(False)


def t_the_post_filter_is_a_second_belt_not_just_rg_globs():
    """حتی اگر glob ِ rg سوراخ داشته باشد، پس‌غربال مسیرِ ممنوع را می‌گیرد."""
    pats = av._agentignore_patterns(ROOT)
    assert av._is_excluded("private-dir/مخفی.md", pats)
    assert av._is_excluded("_Archive/راز-قدیمی.md", pats)
    assert av._is_excluded("x/_Duplicates/y.md", pats)
    assert not av._is_excluded("03 - Projects/Mining/کولر-ماینر.md", pats)


# ── صداقت: صفر hit = نمی‌دانم، صفر تماس ─────────────────────────────────────
def t_zero_hits_answers_i_dont_know_without_calling_the_model():
    _on()
    try:
        fn = _fake_ask()
        r = av.query("زکسقصثقث یعنی چه؟", vault_root=ROOT, ask_fn=fn)
        assert r["ok"], r
        assert r["answer"] == av.NO_ANSWER, r["answer"]
        assert r["sources"] == [], r
        assert not fn._calls, "با صفر شاهد مدل صدا شد — دروازهٔ توهم باز است"
    finally:
        _on(False)


def t_a_fake_sources_section_from_the_model_is_cut():
    _on()
    try:
        fn = _fake_ask(text="جواب.\nمنابع:\n• [[نوتِ-جعلی]]")
        r = av.query("کولر ماینر چند درجه است؟", vault_root=ROOT, ask_fn=fn)
        assert r["ok"], r
        assert "نوتِ-جعلی" not in r["answer"], r["answer"]
        assert "منابع:" in r["answer"]
    finally:
        _on(False)


# ── داده نه دستور + بی‌عملی ─────────────────────────────────────────────────
def t_retrieved_text_is_declared_data_not_instructions():
    _on()
    try:
        fn = _fake_ask()
        av.query("کولر ماینر چند درجه است؟", vault_root=ROOT, ask_fn=fn)
        s = fn._calls[0]["system"]
        assert "داده" in s and "دستور" in s and "اجرا نکن" in s, s
        assert "نمی‌دانم — در vault نیست" in s, "system جوابِ صادقِ نبودن را پین نمی‌کند"
        assert "قطعه‌های بازیابی‌شده" in fn._calls[0]["prompt"]
    finally:
        _on(False)


def t_this_module_only_reads_and_talks_it_never_sends_or_pays():
    src = Path(av.__file__).read_text("utf-8")
    for forbidden in ("send_text", "sendMessage", "requests.", "urlopen",
                      "tier=\"primary\"", "tier=\"secondary\"",
                      "tier='primary'", "tier='secondary'"):
        assert forbidden not in src, f"مسیرِ ارسال/پولی در ask_vault: {forbidden}"
    assert 'tier="local"' in src, "پینِ tier محلی گم شده"


def t_state_stays_inside_the_isolated_tree():
    live = str(harness.REAL_VAULT).lower()
    assert not str(ROOT).lower().startswith(live), ROOT


# ═══ چتِ آزادِ محلی-اول (لِین F — «مغزِ محلی $0 روزمره، گران فقط مهم») ═══════
import ask_brain as ab  # noqa: E402


def _ab_reset():
    for p in (ab.STATE, ab.LOCAL_STATE, ab.LEDGER):
        try:
            p.unlink()
        except OSError:
            pass
    ab._MEMO.update(date="", used=0, last_ts=0.0)
    ab._MEMO_LOCAL.update(date="", used=0)


def _ab_on(local=True):
    os.environ[ab.FLAG] = "1"
    if local:
        os.environ[ab.CHAT_LOCAL_FLAG] = "1"
    else:
        os.environ.pop(ab.CHAT_LOCAL_FLAG, None)


def _ab_off():
    os.environ.pop(ab.FLAG, None)
    os.environ.pop(ab.CHAT_LOCAL_FLAG, None)


def _tiered_ask(local_ok=True, calls=None):
    """مغزِ ساختگی که بسته به tier ِ خواسته‌شده جواب می‌دهد."""
    calls = calls if calls is not None else []

    def fn(task, prompt, system="", max_tokens=400, **kw):
        tier = kw.get("tier")
        calls.append(tier)
        if tier == "local":
            return {"ok": local_ok, "text": "ج" * 120, "model": "qwen", "tier": "local"}
        return {"ok": True, "text": "پ" * 120, "model": "fugu", "tier": "primary"}

    fn._calls = calls
    return fn


def t_chat_local_ordinary_question_goes_to_the_free_brain_first():
    _ab_on()
    _ab_reset()
    try:
        fn = _tiered_ask()
        r = ab.ask("چطور می‌شود سریع‌تر شد؟", ask_fn=fn, now=1000.0)
        assert r["ok"] and r["tier"] == "local", r
        assert fn._calls == ["local"], fn._calls
        assert not ab.STATE.exists(), "سؤالِ عادی سهمیهٔ **پولی** سوزاند"
        assert ab.LOCAL_STATE.exists()
    finally:
        _ab_off()


def t_chat_local_an_important_question_escalates_straight_to_paid():
    _ab_on()
    _ab_reset()
    try:
        fn = _tiered_ask()
        r = ab.ask("برای این تصمیم چه کنم؟", ask_fn=fn, now=1000.0)
        assert r["ok"] and r["tier"] == "primary", r
        assert fn._calls == ["primary"], fn._calls
    finally:
        _ab_off()


def t_chat_local_failure_of_the_free_brain_falls_up_to_paid():
    _ab_on()
    _ab_reset()
    try:
        fn = _tiered_ask(local_ok=False)
        r = ab.ask("چطور می‌شود سریع‌تر شد؟", ask_fn=fn, now=1000.0)
        assert r["ok"] and r["tier"] == "primary", r
        assert fn._calls == ["local", "primary"], fn._calls
    finally:
        _ab_off()


def t_chat_local_off_is_byte_identical_paid_only():
    _ab_on(local=False)
    _ab_reset()
    try:
        fn = _tiered_ask()
        r = ab.ask("چطور می‌شود سریع‌تر شد؟", ask_fn=fn, now=1000.0)
        assert r["ok"] and r["tier"] == "primary", r
        assert fn._calls == ["primary"], "با flag خاموش مغزِ محلی صدا شد"
        assert not ab.LOCAL_STATE.exists()
    finally:
        _ab_off()


def t_chat_local_has_its_own_sanity_cap_and_never_burns_paid_quota():
    _ab_on()
    _ab_reset()
    try:
        fn = _tiered_ask()
        t = 1000.0
        ok = 0
        for i in range(ab.LOCAL_DAILY_CAP + 5):
            t += 1.0
            if ab.ask("سؤالِ ساده؟", ask_fn=fn, now=t).get("tier") == "local":
                ok += 1
        assert ok == ab.LOCAL_DAILY_CAP, ok
        # بعد از سقفِ محلی، نردبان به پولی می‌رود (با سهمیهٔ خودش) نه سکوت
        assert "primary" in fn._calls[-1:], fn._calls[-3:]
    finally:
        _ab_off()


def t_chat_local_card_marks_the_tier_honestly():
    b_local, _ = ab.card("جواب", "qwen", tier="local")
    assert "محلی" in b_local and "🧠" in b_local, b_local
    b_paid, _ = ab.card("جواب", "fugu", tier="primary")
    assert "گران" in b_paid and "🐡" in b_paid, b_paid
    b_old, _ = ab.card("جواب", "fugu")
    assert "محلی" not in b_old and "گران" not in b_old, "بدونِ tier رفتارِ قدیم نیست"


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'✅' if not failed else '❌'} test_tg_ask_vault: "
          f"{len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
