"""test_improve_learning_loop — رأیِ مالک باید به یادگیرنده برسد.

یافتهٔ ۲۰۲۶-۰۷-۲۷ با دو شاهدِ فیزیکی:
  ۱) `cortex/improve.py` خطِ ۱۹ می‌نویسد «یادگیری: verdictهای مالک روی پیشنهادها
     دسته‌های ردشده را جریمه می‌کنند» — ولی `improve.record_verdict` در کلِ مخزن
     **صفر صداکننده** داشت.
  ۲) `state/cortex/improve-verdicts.jsonl` روی دیسکِ زنده **وجود نداشت** — یعنی
     آن جریمه هرگز حتی یک بار محاسبه نشده بود.

نتیجهٔ عملی: مالک «نه» می‌گفت و همان جنسِ پیشنهاد دوباره می‌آمد. رأی **دیده**
می‌شد ولی چیزی از آن **یاد گرفته** نمی‌شد — و سند ادعای عکسش را می‌کرد.

مرزی که این تست محافظت می‌کند: یادگیری حق ندارد چیزی را اجرا کند. تنها اثرِ
مجازش این است که دستهٔ ردشده دفعهٔ بعد **کمتر پیشنهاد شود**.
"""
import ast
import json
import os
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))
import harness   # noqa: E402
ENV = harness.setup("improve-learning")

_OPS = harness.SELF_OPS
for _p in (str(_OPS), str(_OPS / "budget"), str(_OPS / "cortex")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import opslib      # noqa: E402
import improve     # noqa: E402
import live_loop   # noqa: E402

FLAG = "OCTOPUS_WIRE_IMPROVE_LEARN"


def _on(v=True):
    if v:
        os.environ[FLAG] = "1"
    else:
        os.environ.pop(FLAG, None)


def _clear():
    try:
        improve.VERDICTS_PATH.unlink()
    except OSError:
        pass


def _rows():
    try:
        return [json.loads(x) for x in
                improve.VERDICTS_PATH.read_text("utf-8").splitlines() if x.strip()]
    except OSError:
        return []


class _Loop(live_loop.LiveLoop):
    """کمترین نمونه‌ای که متدِ زیرِ آزمون را دارد."""
    def __init__(self):
        pass


# ─── ۱: حلقه واقعاً بسته است ──────────────────────────────────────────────
def t_a_rejection_reaches_the_learner():
    """قلبِ باگ: «نه»ی مالک باید در فایلِ یادگیری بنشیند."""
    _on()
    _clear()
    try:
        _Loop()._feed_improve_learner({"proposal_id": "p1", "category": "seo"}, "rejected")
        rows = _rows()
        assert len(rows) == 1, rows
        assert rows[0]["verdict"] == "reject" and rows[0]["category"] == "seo", rows
    finally:
        _on(False)


def t_all_three_verdicts_map_to_the_learner_vocabulary():
    _on()
    try:
        for mapped, want in (("approved", "accept"), ("rejected", "reject"),
                             ("deferred", "later")):
            _clear()
            _Loop()._feed_improve_learner({"proposal_id": "p", "category": "c"}, mapped)
            assert _rows()[0]["verdict"] == want, (mapped, _rows())
    finally:
        _on(False)


def t_a_rejection_actually_penalises_that_category():
    """اگر ثبت شود ولی روی امتیاز اثر نگذارد، حلقه باز مانده — فقط شکلش عوض شده."""
    _on()
    _clear()
    try:
        before = improve._load_verdict_penalty()
        for i in range(3):
            _Loop()._feed_improve_learner({"proposal_id": f"p{i}", "category": "seo"},
                                          "rejected")
        after = improve._load_verdict_penalty()
        assert after.get("seo") and after != before, (before, after)
    finally:
        _on(False)


def t_an_unknown_verdict_is_not_invented():
    _on()
    _clear()
    try:
        for bad in ("", None, "maybe", "approved_ish", "ok"):
            _Loop()._feed_improve_learner({"proposal_id": "p", "category": "c"}, bad)
        assert _rows() == [], _rows()
    finally:
        _on(False)


def t_a_missing_category_becomes_unknown_not_a_guess():
    """دستهٔ حدسی یعنی جریمه‌خوردنِ چیزی که مالک اصلاً ردش نکرده."""
    _on()
    _clear()
    try:
        _Loop()._feed_improve_learner({"proposal_id": "p"}, "rejected")
        assert _rows()[0]["category"] == "unknown", _rows()
    finally:
        _on(False)


# ─── ۲: فلگ خاموش = رفتارِ امروز ──────────────────────────────────────────
def t_flag_off_writes_nothing():
    _on(False)
    _clear()
    _Loop()._feed_improve_learner({"proposal_id": "p", "category": "c"}, "rejected")
    assert not improve.VERDICTS_PATH.exists()


# ─── ۳: مرز — یادگیری اجرا نیست ───────────────────────────────────────────
def t_the_learner_hook_cannot_execute_anything():
    src = Path(live_loop.__file__).read_text("utf-8")
    i = src.index("_feed_improve_learner")
    j = src.index("def ", src.index("def _feed_improve_learner") + 10)
    body = src[src.index("def _feed_improve_learner"):j]
    for d in ("subprocess", "os.system", "apply", "settle", "pay", "release",
              "commit", "unlink", "rmtree"):
        assert d not in body, f"هوکِ یادگیری عمل می‌کند: {d}"


def t_a_broken_learner_never_kills_the_verdict_path():
    """رأیِ مالک مقدس است — یادگیریِ خراب نباید ثبتش را ببرد."""
    _on()
    real = improve.record_verdict
    try:
        improve.record_verdict = lambda *a, **k: (_ for _ in ()).throw(RuntimeError("x"))
        _Loop()._feed_improve_learner({"proposal_id": "p", "category": "c"}, "rejected")
    finally:
        improve.record_verdict = real
        _on(False)


def t_hostile_metadata_never_raises():
    _on()
    _clear()
    try:
        for meta in ({}, {"proposal_id": None}, {"category": 5},
                     {"category": "ب" * 500}, {"proposal_id": ["x"]}):
            _Loop()._feed_improve_learner(meta, "rejected")
    finally:
        _on(False)


# ─── ۴: گاردِ رگرسیون — قوس دوباره بریده نشود ─────────────────────────────
def t_the_learner_has_at_least_one_live_caller():
    """اصلِ باگ این بود که این تابع صفر صداکننده داشت. حالا باید داشته باشد."""
    hits = []
    for f in _OPS.rglob("*.py"):
        if set(f.parts) & {"tests", "_code", "__pycache__"}:
            continue
        try:
            src = f.read_text("utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        if "record_verdict(" in src and "improve" in src and f.name != "improve.py":
            hits.append(f.name)
    assert hits, "improve.record_verdict دوباره یتیم شد"


def t_the_documented_learning_claim_matches_reality():
    """سندِ ماژول ادعای یادگیری می‌کند؛ اگر مسیرش نباشد، سند دروغ است."""
    src = Path(improve.__file__).read_text("utf-8")
    assert "improve-verdicts.jsonl" in src
    tree = ast.parse(src)
    names = {n.name for n in ast.walk(tree)
             if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}
    assert "record_verdict" in names and "_load_verdict_penalty" in names


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'✅' if not failed else '❌'} test_improve_learning_loop: "
          f"{len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
