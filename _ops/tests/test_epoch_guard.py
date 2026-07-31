"""test_epoch_guard — کادنسی که ری‌استارت آن را دور نزند.

اندازه‌گیریِ ۲۰۲۶-۰۷-۲۸: کارتِ «نیازت دارم» با تناوبِ **۶ ساعت** چهار بار در یک
ساعت آمد. تناوب درست بود؛ آن ساعت چهار ری‌استارت داشت.

ریشه یک **الگو** بود نه یک باگ: هفت حالتِ «آخرین پنجرهٔ شلیک‌شده» همه در حافظه
بودند — `_EPOCH_STATE` (۱۲ صداکننده) به‌علاوهٔ شش حالتِ دست‌ساز
(`_INGEST_STATE` · `_HEART_STATE` · `_ACCT_STATE` · `_NUDGE_STATE` ·
`_HEARTBEAT_STATE` · `_DISCOVERY_STATE`). هر بوت صفرشان می‌کرد، پس اولین تیک
**هر هجده کادنس** را بی‌قید شلیک می‌کرد.

چرا این بدتر از یک باگِ ساده است: از بیرون شبیهِ «پرحرفی» است نه نقص — و هر کسی
که تناوب را بلندتر کند مشکل را عمیق‌تر می‌کند، چون علت تناوب نیست، **فراموشیِ
هنگام بوت** است.

مهم‌ترین چکِ این فایل آخری است: می‌سنجد الگوی دست‌ساز **برنگشته باشد**. بستنِ
شش شکاف بی‌فایده است اگر هفتمی فردا نوشته شود.
"""
import os
import re
import sys
import tempfile
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))
import harness   # noqa: E402
ENV = harness.setup("epoch-guard")

_OPS = harness.REAL_VAULT / "_ops"
for _p in (str(_OPS), str(_OPS / "budget")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import epoch_guard as eg   # noqa: E402
import wiring              # noqa: E402


def _on(v=True):
    if v:
        os.environ[eg.FLAG] = "1"
    else:
        os.environ.pop(eg.FLAG, None)


def _fresh():
    eg._path().unlink(missing_ok=True)
    wiring._EPOCH_STATE.clear()


# ─── ۱: خودِ گارد ─────────────────────────────────────────────────────────
def t_flag_off_is_a_complete_no_op():
    """خاموشی نصفه یعنی کادنسی که بی‌صدا خفه می‌شود."""
    _on(False)
    assert eg.already_fired("x", 5) is False
    assert eg.mark_fired("x", 5) is False
    assert eg.already_fired("x", 5) is False


def t_a_fired_window_is_remembered():
    _on()
    try:
        _fresh()
        assert eg.already_fired("probe", 3) is False
        assert eg.mark_fired("probe", 3) is True
        assert eg.already_fired("probe", 3) is True
    finally:
        _on(False)


def t_a_later_window_still_fires():
    """گارد نباید کادنس را برای همیشه ببندد — فقط همان پنجره را."""
    _on()
    try:
        _fresh()
        eg.mark_fired("probe", 3)
        assert eg.already_fired("probe", 4) is False
    finally:
        _on(False)


def t_the_counter_never_goes_backwards():
    _on()
    try:
        _fresh()
        eg.mark_fired("probe", 7)
        assert eg.mark_fired("probe", 2) is False
        assert eg.already_fired("probe", 7) is True
    finally:
        _on(False)


def t_cadences_do_not_share_a_window():
    _on()
    try:
        _fresh()
        eg.mark_fired("a", 3)
        assert eg.already_fired("b", 3) is False
    finally:
        _on(False)


def t_a_broken_store_fails_towards_speaking():
    """گم‌شدنِ کارت بدتر از کارتِ اضافه است — شکست باید به‌سمتِ گفتن بیفتد."""
    _on()
    real = eg._path
    eg._path = lambda: Path("/\x00نامعتبر/x.json")
    try:
        assert eg.already_fired("probe", 1) is False   # یعنی «شلیک کن»
        assert eg.mark_fired("probe", 1) is False
    finally:
        eg._path = real
        _on(False)


# ─── ۲: رفتارِ واقعی زیرِ ری‌استارت ───────────────────────────────────────
def t_five_restarts_produce_five_fires_when_off():
    """خطِ پایه — این همان چیزی است که چهار کارت در یک ساعت ساخت."""
    _on(False)
    _fresh()
    fires = sum(1 for _ in range(5)
                if (wiring._EPOCH_STATE.clear() or
                    wiring._epoch_fire("probe", beat=800, every_n=360)))
    assert fires == 5, fires


def t_five_restarts_produce_one_fire_when_on():
    """قلبِ فیکس."""
    _on()
    try:
        _fresh()
        fires = sum(1 for _ in range(5)
                    if (wiring._EPOCH_STATE.clear() or
                        wiring._epoch_fire("probe", beat=800, every_n=360)))
        assert fires == 1, fires
    finally:
        _on(False)


def t_the_hand_rolled_sites_are_guarded_too():
    """شش کادنسی که از `_epoch_fire` رد نمی‌شدند."""
    _on()
    try:
        for name, state, mn in (("ingest", {}, 1), ("heart", {}, 1),
                                ("accounting", {}, 1), ("needs_nudge", {}, 1),
                                ("heartbeat", {}, 0), ("discovery", {}, 1)):
            _fresh()
            first = wiring._epoch_window(name, 3, state, min_epoch=mn)
            state.clear()                      # ری‌استارت
            second = wiring._epoch_window(name, 3, state, min_epoch=mn)
            assert first is True and second is False, (name, first, second)
    finally:
        _on(False)


# ─── ۳: قاعده برنگردد ────────────────────────────────────────────────────
def t_no_hand_rolled_epoch_check_remains():
    """⚠️ مهم‌ترین چکِ این فایل.

    بستنِ شش شکاف بی‌فایده است اگر هفتمی فردا نوشته شود. این چک الگوی
    دست‌ساز را در کلِ `wiring.py` ممنوع می‌کند، پس کادنسِ تازه یا باید از
    `_epoch_fire` بیاید یا از `_epoch_window`.
    """
    src = (_OPS / "wiring.py").read_text("utf-8")
    bad = re.findall(r'epoch <= _[A-Z_]+STATE\["last_epoch"\]', src)
    assert not bad, f"{len(bad)} چکِ دست‌سازِ پنجره برگشت: {bad[:3]}"


def t_both_helpers_consult_the_disk_guard():
    """اگر یکی‌شان گارد را صدا نزند، نیمی از کادنس‌ها بی‌محافظ می‌مانند."""
    src = (_OPS / "wiring.py").read_text("utf-8")
    for fn in ("_epoch_fire", "_epoch_window"):
        i = src.index(f"def {fn}(")
        j = src.index("\ndef ", i + 10)
        assert "epoch_guard" in src[i:j], f"{fn} گاردِ دیسکی را صدا نمی‌زند"


def t_the_guard_module_decides_nothing_else():
    """فقط «این پنجره شلیک شد؟». هیچ ارسالی، هیچ تصمیمی."""
    import ast
    tree = ast.parse(Path(eg.__file__).read_text("utf-8"))
    imported = set()
    for n in ast.walk(tree):
        if isinstance(n, ast.Import):
            imported.update(a.name.split(".")[0] for a in n.names)
        elif isinstance(n, ast.ImportFrom) and n.module:
            imported.add(n.module.split(".")[0])
    assert not (imported & {"requests", "urllib", "socket", "subprocess"}), imported


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'✅' if not failed else '❌'} test_epoch_guard: "
          f"{len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
