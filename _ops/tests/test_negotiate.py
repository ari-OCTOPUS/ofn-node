"""test_negotiate.py — تستِ متخاصمِ مذاکره: جوابِ سوم.

هر کارتِ امروز دو جواب دارد (آره/نه). این ماژول جوابِ سوم را اضافه می‌کند:
«شرط بگذار». خطرِ اصلی این است که کلمهٔ «مذاکره» کسی را به این باور برساند که
«قبول» یعنی کاری انجام شد. **نمی‌شود** — و اولین تستِ این فایل همان را قفل می‌کند.
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
ENV = harness.setup("negotiate")

import negotiate as ng   # noqa: E402
import ask_brain as ab   # noqa: E402

GOOD = json.dumps({
    "عنوان": "متر را قبل از شیر درست کن",
    "می‌خواهم": "eval واقعی برای measured_lift بسازم",
    "شرط‌ها": ["یک ساعت از توجهت", "در عوض نرخِ بهبود صادق می‌شود"],
    "هزینه": "دو تماسِ مغز، بدونِ ریسکِ بیرونی",
    "اگر_نه": "هر merge روی سیگنالِ جعلی سوار می‌ماند",
    "غلط_است_اگر": "eval تازه همان عددِ قبلی را بدهد",
}, ensure_ascii=False)


def _on(v=True):
    for f in (ng.FLAG, ab.FLAG):
        if v:
            os.environ[f] = "1"
        else:
            os.environ.pop(f, None)


def _reset():
    for p in (ng.OFFERS, ng.CORRECTIONS, ab.STATE):
        try:
            p.unlink()
        except OSError:
            pass
    ab._MEMO.update(date="", used=0, last_ts=0.0)


def _fn(text=GOOD, ok=True, tier="primary", calls=None):
    calls = calls if calls is not None else []

    def f(task, prompt, system="", max_tokens=400, **kw):
        calls.append({"prompt": prompt, "system": system, "tier": kw.get("tier")})
        return {"ok": ok, "text": text, "model": "fugu", "tier": tier}

    f._calls = calls
    return f


# ─── مرزِ اصلی ──────────────────────────────────────────────────────────────
def t_accepting_an_offer_executes_absolutely_nothing():
    """«مذاکره» نباید کسی را به این باور برساند که «قبول» یعنی کاری شد."""
    import ast
    tree = ast.parse(Path(ng.__file__).read_text("utf-8"))
    banned = {"subprocess", "urllib", "requests", "socket",
              "capability_gate", "arm_gate", "effector_gate", "organ_gate"}
    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(a.name.split(".")[0] for a in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module.split(".")[0])
    assert not (banned & imported), sorted(banned & imported)
    _on()
    _reset()
    try:
        r = ng.make_offer(ask_fn=_fn(), now=1000.0)
        oid = r["offer"]["id"]
        out = ng.respond(oid, "accept")
        assert out["ok"] and out["status"] == "accepted", out
        # وضع فقط ثبت شد؛ هیچ فایلِ اجرایی/گیتی لمس نشد
        rec = ng.effective()[oid]
        assert rec["status"] == "accepted" and "executed" not in rec
    finally:
        _on(False)


def t_flag_off_is_silent():
    _on(False)
    _reset()
    f = _fn()
    assert ng.make_offer(ask_fn=f, now=1000.0) == {"ok": False, "reason": "flag-off"}
    assert not f._calls and not ng.OFFERS.exists()


# ─── جوابِ سوم ──────────────────────────────────────────────────────────────
def t_a_counter_is_stored_and_shapes_the_revision():
    """قلبِ مذاکره: شرطِ مالک باید در پیشنهادِ بعدی دیده شود."""
    _on()
    _reset()
    try:
        os.environ["TG_ASK_BRAIN_DAILY"] = "20"
        r = ng.make_offer(ask_fn=_fn(), now=1000.0)
        oid = r["offer"]["id"]
        out = ng.respond(oid, "counter", counter="فقط اگر بدونِ ری‌استارت باشد")
        assert out["ok"] and out["status"] == "countered", out
        assert "بدونِ ری‌استارت" in " ".join(ng.terms_history(oid))
        f2 = _fn()
        rev = ng.make_offer(ask_fn=f2, revise_of=oid,
                            now=1000.0 + ab.MIN_GAP_S + 1)
        assert rev["ok"], rev
        p = f2._calls[0]["prompt"]
        assert "بدونِ ری‌استارت" in p, "شرطِ مالک به پیشنهادِ بازنگری نرسید"
        assert "پیشنهادِ_قبلیِ_من" in p, "بازنگری پیشنهادِ قبلی را نمی‌بیند"
        assert rev["offer"]["revision"] == 2, rev["offer"]["revision"]
    finally:
        os.environ.pop("TG_ASK_BRAIN_DAILY", None)
        _on(False)


def t_a_counter_also_lands_in_the_correction_ledger():
    """مذاکره و گفتگو باید یک حافظه داشته باشند، نه دو تا."""
    _on()
    _reset()
    try:
        r = ng.make_offer(ask_fn=_fn(), now=1000.0)
        ng.respond(r["offer"]["id"], "counter", counter="اول نقاشی، بعد بقیه")
        raw = ng.CORRECTIONS.read_text("utf-8")
        assert "اول نقاشی" in raw, "شرط به دفترِ تصحیح‌ها نرسید"
        assert "telegram-negotiate" in raw
    finally:
        _on(False)


def t_an_empty_counter_is_refused():
    _on()
    _reset()
    try:
        r = ng.make_offer(ask_fn=_fn(), now=1000.0)
        out = ng.respond(r["offer"]["id"], "counter", counter="   ")
        assert not out["ok"] and out["reason"] == "empty-counter", out
        assert ng.effective()[r["offer"]["id"]]["status"] == "open"
    finally:
        _on(False)


# ─── ضدِ دوباره‌پاسخ و ضدِ فشار ─────────────────────────────────────────────
def t_an_answered_offer_cannot_be_answered_twice():
    _on()
    _reset()
    try:
        r = ng.make_offer(ask_fn=_fn(), now=1000.0)
        oid = r["offer"]["id"]
        assert ng.respond(oid, "accept")["ok"]
        again = ng.respond(oid, "reject")
        assert not again["ok"] and "already" in again["reason"], again
    finally:
        _on(False)


def t_unknown_offer_and_bad_verdict_are_refused():
    _on()
    _reset()
    try:
        assert ng.respond("of-nope", "accept")["reason"] == "unknown-offer"
        r = ng.make_offer(ask_fn=_fn(), now=1000.0)
        assert ng.respond(r["offer"]["id"], "maybe")["reason"] == "bad-verdict"
    finally:
        _on(False)


def t_open_offers_are_capped_so_the_owner_is_not_flooded():
    _on()
    _reset()
    try:
        os.environ["TG_ASK_BRAIN_DAILY"] = "20"
        t = 1000.0
        made = 0
        for i in range(5):
            t += ab.MIN_GAP_S + 1
            title = json.dumps({**json.loads(GOOD), "عنوان": f"پیشنهاد {i}"},
                               ensure_ascii=False)
            if ng.make_offer(ask_fn=_fn(text=title), now=t).get("ok"):
                made += 1
        assert made == ng.MAX_OPEN, f"{made} پیشنهادِ باز — سقف {ng.MAX_OPEN}"
    finally:
        os.environ.pop("TG_ASK_BRAIN_DAILY", None)
        _on(False)


# ─── کیفیتِ پیشنهاد ─────────────────────────────────────────────────────────
def t_a_malformed_answer_is_discarded_not_guessed():
    _on()
    _reset()
    try:
        for bad in ("خب به نظرم این کار را بکن", '{"عنوان": "بدونِ می‌خواهم"}',
                    "{ناقص", ""):
            _reset()
            r = ng.make_offer(ask_fn=_fn(text=bad), now=1000.0)
            assert not r["ok"], (bad[:20], r)
            assert not ng.open_offers(), f"پیشنهادِ بدشکل ثبت شد: {bad[:20]}"
    finally:
        _on(False)


def t_a_free_brain_answer_is_refused():
    _on()
    _reset()
    try:
        r = ng.make_offer(ask_fn=_fn(tier="local"), now=1000.0)
        assert not r["ok"] and r["reason"] == "not-a-paid-brain", r
    finally:
        _on(False)


def t_the_offer_comes_from_its_own_agenda():
    """پیشنهاد باید از تشخیصِ خودش بیاید، نه از لیستِ دست‌ساز."""
    import opslib
    p = opslib.STATE_DIR / "cortex" / "upgrades-digest.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps({"top": [{"id": "up-x", "priority": "P0",
                                      "title": "گافِ نشان‌دار"}],
                             "improvement_rate": 0.42}, ensure_ascii=False), "utf-8")
    _on()
    _reset()
    try:
        f = _fn()
        ng.make_offer(ask_fn=f, now=1000.0)
        p2 = f._calls[0]["prompt"]
        assert "گافِ نشان‌دار" in p2, "صفِ اهدافِ خودش در prompt نیست"
        assert "0.42" in p2
        assert "مذاکره" in f._calls[0]["system"], "لحنِ مذاکره در system نیست"
    finally:
        _on(False)


def t_the_card_offers_three_answers_not_two():
    _on()
    _reset()
    try:
        r = ng.make_offer(ask_fn=_fn(), now=1000.0)
        body, kb = ng.card(r["offer"])
        verbs = [b["callback_data"].split(":")[1] for row in kb for b in row]
        assert sorted(verbs) == ["a", "c", "r"], verbs
        assert "شرط بگذار" in json.dumps(kb, ensure_ascii=False)
        assert "غلط است اگر" in body, "شرطِ ابطال در کارت نیست"
        for row in kb:
            for b in row:
                assert len(b["callback_data"].encode()) <= 64, b
    finally:
        _on(False)


def t_card_escapes_hostile_text():
    body, _ = ng.card({"id": "of1", "عنوان": "<script>x</script>",
                       "می‌خواهم": "a & b", "شرط‌ها": []})
    assert "<script>" not in body and "&lt;script&gt;" in body, body


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'✅' if not failed else '❌'} test_negotiate: "
          f"{len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
