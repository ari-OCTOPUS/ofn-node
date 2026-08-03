"""test_teacher_loop — W4 (G1)، معیارهای پذیرشِ قراردادِ GENOME LOCK.

سه چیز باید ساختاراً غیرممکن باشد:
  ۱) خرجِ پول با فلگِ خاموش، یا بعد از سقفِ روزانه.
  ۲) ثبتِ جفتی که «معلم» ندارد (وقتی مسیر به مغزِ محلی افتاده) — دو جوابِ یک
     مغز، جفتِ معلم/شاگرد نیست و ذخیره‌اش به آن اسم دروغ است.
  ۳) نوشتنِ متنِ خام وقتی redaction در دسترس نیست — این فایل متنِ کامل دارد،
     پس خطرناک‌ترین فایلِ ماست.

و یک قیدِ صداقت: جفتِ بی‌نمره باید **بی‌نمره** بماند، نه اینکه صفر یا یک بگیرد.
"""
import json
import os
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))
import harness   # noqa: E402
ENV = harness.setup("teacher-loop")

_OPS = harness.SELF_OPS
for _p in (str(_OPS), str(_OPS / "budget"), str(_OPS / "cortex")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import opslib               # noqa: E402
import teacher_loop as tp   # noqa: E402
import trajectory_log as tl  # noqa: E402

_T0 = 1_800_000_000.0
TOKEN_SHAPED = "12345678:AA" + "b" * 34


def _on(v=True):
    if v:
        os.environ[tp.FLAG] = "1"
        os.environ[tl.FLAG] = "1"
    else:
        os.environ.pop(tp.FLAG, None)
        os.environ.pop(tl.FLAG, None)


def _reset():
    for p in (tp._state_path(), tp._pairs_path(), tl._path()):
        try:
            p.unlink()
        except OSError:
            pass


def _teacher(text="{}", tier="primary", ok=True, calls=None):
    calls = calls if calls is not None else []

    def f(task, prompt, system="", max_tokens=700, **kw):
        calls.append(task)
        return {"ok": ok, "text": text, "tier": tier, "model": "fugu"}
    f._calls = calls
    return f


def _student(text="{}"):
    # امضای شاگرد = امضای معلم؛ هر دو از `model_router.ask` می‌روند.
    def f(task, prompt, system="", max_tokens=700, **kw):
        assert kw.get("tier") == "local", "شاگرد به ردهٔ محلی پین نشده"
        return {"ok": True, "text": text}
    return f


# ─── ۱: پول ────────────────────────────────────────────────────────────────
def t_flag_off_spends_nothing():
    _on(False)
    _reset()
    t = _teacher()
    r = tp.pair(task="x", prompt="p", teacher_fn=t, student_fn=_student())
    assert r["reason"] == "flag-off" and not t._calls
    assert not tp._pairs_path().exists()


def t_the_daily_cap_actually_stops_the_spending():
    _on()
    _reset()
    try:
        os.environ["OCTOPUS_TEACHER_DAILY"] = "3"
        t = _teacher()
        made = sum(1 for _ in range(7)
                   if tp.pair(task="x", prompt="p", teacher_fn=t,
                              student_fn=_student(), now=_T0)["ok"])
        assert made == 3, made
        assert len(t._calls) == 3, len(t._calls)
    finally:
        os.environ.pop("OCTOPUS_TEACHER_DAILY", None)
        _on(False)


def t_the_quota_burns_before_the_call_not_after():
    """اگر بعد بسوزد، هر انفجارِ وسطِ راه یعنی تیکِ بعدی دوباره پول خرج می‌کند."""
    _on()
    _reset()
    try:
        def boom(*a, **k):
            raise RuntimeError("معلم مرد")
        tp.pair(task="x", prompt="p", teacher_fn=boom,
                student_fn=_student(), now=_T0)
        st = json.loads(tp._state_path().read_text("utf-8"))
        assert st["used"] == 1, st
    finally:
        _on(False)


def t_the_cap_is_bounded_and_survives_garbage():
    for v, want in (("5", 5), ("0", tp.DAILY_DEFAULT), ("999", tp.DAILY_DEFAULT),
                    ("x", tp.DAILY_DEFAULT), ("", tp.DAILY_DEFAULT)):
        os.environ["OCTOPUS_TEACHER_DAILY"] = v
        try:
            assert tp.daily_cap() == want, (v, tp.daily_cap())
        finally:
            os.environ.pop("OCTOPUS_TEACHER_DAILY", None)


# ─── ۲: جفتی که معلم ندارد ─────────────────────────────────────────────────
def t_a_pair_without_a_real_teacher_is_marked_unusable():
    """مسیر به محلی افتاد → دو جوابِ یک مغز. جفتِ معلم/شاگرد نیست."""
    _on()
    _reset()
    try:
        r = tp.pair(task="x", prompt="p", now=_T0,
                    teacher_fn=_teacher(tier="local"), student_fn=_student())
        p = r["pair"]
        assert p["teacher"]["ok"] is False, p["teacher"]
        assert "محلی" in p["teacher"]["err"], p["teacher"]["err"]
        assert p["usable_for_distill"] is False
    finally:
        _on(False)


def t_a_fallback_marked_answer_is_also_refused():
    _on()
    _reset()
    try:
        def f(task, prompt, system="", max_tokens=700, **kw):
            return {"ok": True, "text": "{}", "tier": "primary",
                    "fallback_from": "primary"}
        r = tp.pair(task="x", prompt="p", teacher_fn=f,
                    student_fn=_student(), now=_T0)
        assert r["pair"]["usable_for_distill"] is False
    finally:
        _on(False)


def t_usable_requires_the_teacher_to_actually_be_better():
    """جفتی که شاگرد در آن مساوی یا بهتر است، دادهٔ تقطیر نیست."""
    _on()
    _reset()
    try:
        g = lambda t: tp.grade_json(t, required=["a"])   # noqa: E731
        both_good = tp.pair(task="x", prompt="p", grader=g, now=_T0,
                            teacher_fn=_teacher('{"a":1}'),
                            student_fn=_student('{"a":1}'))["pair"]
        assert both_good["usable_for_distill"] is False, "مساوی، ولی usable شد"
        teacher_better = tp.pair(task="x", prompt="p", grader=g, now=_T0,
                                 teacher_fn=_teacher('{"a":1}'),
                                 student_fn=_student("حرفِ آزاد"))["pair"]
        assert teacher_better["usable_for_distill"] is True
    finally:
        _on(False)


# ─── ۳: صداقتِ نمره ────────────────────────────────────────────────────────
def t_an_ungraded_pair_stays_ungraded_not_zero():
    """نمرهٔ بی‌پایه بدتر از نبودِ نمره است — بعداً جداکردنشان ناممکن می‌شود."""
    _on()
    _reset()
    try:
        p = tp.pair(task="x", prompt="p", now=_T0,
                    teacher_fn=_teacher("متنِ آزاد"),
                    student_fn=_student("متنِ آزاد"))["pair"]
        assert p["teacher"]["grade"]["graded"] is False
        assert p["teacher"]["grade"]["score"] is None, p["teacher"]["grade"]
        assert p["usable_for_distill"] is False
    finally:
        _on(False)


def t_the_json_grader_is_unambiguous():
    assert tp.grade_json("نه‌JSON")["score"] == 0.0
    assert tp.grade_json('{"a":1}', required=["a"])["score"] == 1.0
    mid = tp.grade_json('{"a":1}', required=["a", "b"])
    assert 0.0 < mid["score"] < 1.0 and "b" in mid["why"]
    for t in (None, "", "{", "[]", "null"):
        g = tp.grade_json(t)
        assert g["graded"] is True and 0.0 <= g["score"] <= 1.0


def t_the_card_says_when_the_data_is_not_worth_distilling():
    _on()
    _reset()
    try:
        for _ in range(5):
            tp.pair(task="x", prompt="p", now=_T0,
                    teacher_fn=_teacher("آزاد"), student_fn=_student("آزاد"))
        body = tp.card()
        assert "حجم داده نیست" in body, body
    finally:
        _on(False)


# ─── ۴: متنِ خام، خطرناک‌ترین فایل ─────────────────────────────────────────
def t_secret_shaped_text_never_lands_in_the_pair_file():
    _on()
    _reset()
    try:
        tp.pair(task="x", prompt=f"کلید {TOKEN_SHAPED}", now=_T0,
                teacher_fn=_teacher(f"جواب {TOKEN_SHAPED}"),
                student_fn=_student("ok"))
        raw = tp._pairs_path().read_text("utf-8")
        assert TOKEN_SHAPED not in raw, "توکن در فایلِ جفت‌ها نشست"
    finally:
        _on(False)


def t_a_broken_redactor_writes_no_pair_at_all():
    _on()
    _reset()
    real = tl._safe
    try:
        tl._safe = lambda v: (_ for _ in ()).throw(RuntimeError("افتاد"))
        tp.pair(task="x", prompt="p", now=_T0,
                teacher_fn=_teacher("جواب"), student_fn=_student("ok"))
        assert not tp._pairs_path().exists(), "با redactorِ شکسته جفت نوشته شد"
    finally:
        tl._safe = real
        _on(False)


# ─── ۵: مرزِ ماژول ─────────────────────────────────────────────────────────
def t_the_loop_changes_no_weights_and_applies_nothing():
    import ast
    tree = ast.parse(Path(tp.__file__).read_text("utf-8"))
    banned = {"subprocess", "urllib", "requests", "socket", "shutil"}
    imported = set()
    for n in ast.walk(tree):
        if isinstance(n, ast.Import):
            imported.update(a.name.split(".")[0] for a in n.names)
        elif isinstance(n, ast.ImportFrom) and n.module:
            imported.add(n.module.split(".")[0])
    assert not (banned & imported), sorted(banned & imported)
    called = {getattr(n.func, "attr", None) or getattr(n.func, "id", None)
              for n in ast.walk(tree) if isinstance(n, ast.Call)}
    for d in ("apply", "apply_approved", "train", "fit", "system", "run"):
        assert d not in called, f"حلقهٔ معلم چیزی را اعمال می‌کند: {d}"


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'✅' if not failed else '❌'} test_teacher_loop: "
          f"{len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
