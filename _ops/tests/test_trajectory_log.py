"""test_trajectory_log — W3 (G0)، معیارهای پذیرشِ قراردادِ GENOME LOCK.

قیدِ اصلی یکی است و بقیه دورش می‌چرخند: **دفترِ مسیر بدترین جای ممکن برای نشتِ
راز است**، چون کلِ دلیلِ وجودش این است که بعداً به یک مدل خورانده شود. هر بایتی
که این‌جا بنشیند، روزی وزنِ یک مدل می‌شود. پس شکستِ redaction باید یعنی
«ننویس»، نه «خام بنویس» — و افتادنِ رکورد باید **شمرده** شود، وگرنه یک محافظِ
خراب شبیهِ یک دفترِ خالی به‌نظر می‌رسد.
"""
import json
import os
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))
import harness   # noqa: E402
ENV = harness.setup("trajectory-log")

_OPS = harness.REAL_VAULT / "_ops"
for _p in (str(_OPS), str(_OPS / "budget")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import opslib             # noqa: E402
import trajectory_log as tl   # noqa: E402

TOKEN_SHAPED = "12345678:AA" + "b" * 34      # شکلِ توکنِ بات — نه توکنِ واقعی
HEX64 = "a" * 64


def _on(v=True):
    if v:
        os.environ[tl.FLAG] = "1"
    else:
        os.environ.pop(tl.FLAG, None)


def _reset():
    for p in (tl._path(), tl._rotated()):
        try:
            p.unlink()
        except OSError:
            pass
    tl._DROPPED["n"] = 0
    tl._DROPPED["why"] = ""


# ─── ۱: fail-closed، قیدِ اصلی ─────────────────────────────────────────────
def t_a_broken_redactor_drops_the_record_it_never_writes_raw():
    """معیارِ پذیرش: redact ِ fail-closed."""
    _on()
    _reset()
    real = tl._safe
    try:
        def boom(v):
            raise RuntimeError("لایهٔ redaction افتاد")
        tl._safe = boom
        assert tl.step(traj_id="t1", phase="decide", state="هرچیزی") is False
        assert not tl._path().exists(), "رکورد با redactorِ شکسته نوشته شد"
        assert tl.dropped()["n"] == 1, tl.dropped()
    finally:
        tl._safe = real
        _on(False)


def t_the_drop_counter_is_visible_not_silent():
    """محافظِ خراب نباید شبیهِ دفترِ خالی به‌نظر برسد."""
    _on()
    _reset()
    real = tl._safe
    try:
        tl._safe = lambda v: (_ for _ in ()).throw(RuntimeError("x"))
        for i in range(3):
            tl.step(traj_id=f"t{i}", phase="decide", state="x")
        assert tl.dropped()["n"] == 3
        body = tl.card()
        assert "افتاد" in body and "redaction" in body, body
    finally:
        tl._safe = real
        _on(False)


def t_secret_shaped_text_never_reaches_the_file():
    _on()
    _reset()
    try:
        tl.step(traj_id="t1", phase="decide",
                state={"note": f"کلید {TOKEN_SHAPED} این‌جاست"},
                action=f"sk-{'a' * 25}")
        raw = tl._path().read_text("utf-8")
        assert TOKEN_SHAPED not in raw, "توکن در دفترِ مسیر نشست"
        assert "sk-" + "a" * 25 not in raw, "کلید در دفترِ مسیر نشست"
    finally:
        _on(False)


def t_hex64_is_masked_per_match_not_whole_body():
    _on()
    _reset()
    try:
        tl.step(traj_id="t1", phase="decide", state={"h": HEX64, "keep": "بماند"})
        raw = tl._path().read_text("utf-8")
        assert HEX64 not in raw
        assert "بماند" in raw, "کلِ رکورد به‌خاطرِ یک hash نابود شد"
    finally:
        _on(False)


def t_nesting_and_lists_are_redacted_too():
    """نشت معمولاً از فیلدِ سطحِ اول نمی‌آید — از تودرتو می‌آید."""
    _on()
    _reset()
    try:
        tl.step(traj_id="t1", phase="decide",
                state={"a": {"b": [{"c": TOKEN_SHAPED}]}})
        assert TOKEN_SHAPED not in tl._path().read_text("utf-8")
    finally:
        _on(False)


# ─── ۲: فلگ خاموش = صفر اثر ────────────────────────────────────────────────
def t_flag_off_writes_nothing_at_all():
    _on(False)
    _reset()
    assert tl.step(traj_id="t1", phase="decide", state="x") is False
    assert not tl._path().exists()


# ─── ۳: شکلِ داده ──────────────────────────────────────────────────────────
def t_a_trajectory_spans_two_moments_and_stays_append_only():
    """تصمیم و نتیجه یک لحظه نیستند — و رکوردِ اول هرگز بازنویسی نمی‌شود."""
    _on()
    _reset()
    try:
        assert tl.step(traj_id="t1", phase="decide", action="کاری", state={"x": 1})
        assert tl.outcome(traj_id="t1", result="ok", reward=0.8)
        rows = [json.loads(x) for x in tl._path().read_text("utf-8").splitlines() if x.strip()]
        assert len(rows) == 2, rows
        assert rows[0]["phase"] == "decide" and rows[1]["phase"] == "outcome"
        assert rows[0]["action"] == "کاری", "رکوردِ تصمیم بازنویسی شد"
        assert {r["traj_id"] for r in rows} == {"t1"}
    finally:
        _on(False)


def t_an_unfinished_trajectory_is_itself_data():
    """«تصمیم گرفتیم و هیچ‌وقت نفهمیدیم چه شد» باید در کارت دیده شود."""
    _on()
    _reset()
    try:
        tl.step(traj_id="open-1", phase="decide", action="کار")
        tl.step(traj_id="closed-1", phase="decide", action="کار")
        tl.outcome(traj_id="closed-1", result="ok")
        body = tl.card()
        assert "۱" in body or "1" in body, body
        assert "هنوز نه" in body, body
    finally:
        _on(False)


def t_every_record_carries_schema_and_time():
    _on()
    _reset()
    try:
        tl.step(traj_id="t1", phase="decide", state="x")
        r = json.loads(tl._path().read_text("utf-8").splitlines()[0])
        assert r["schema"] == tl.SCHEMA and r["ts"]
    finally:
        _on(False)


# ─── ۴: کرانِ رشد ──────────────────────────────────────────────────────────
def t_the_ledger_rotates_instead_of_growing_forever():
    """دفترِ بی‌مرز روزی دیسک را پر می‌کند و آن روز ارگانیسم می‌خوابد."""
    _on()
    _reset()
    real = tl.MAX_LINES
    try:
        tl.MAX_LINES = 5
        for i in range(9):
            tl.step(traj_id=f"t{i}", phase="decide", state={"i": i})
        assert tl._rotated().exists(), "چرخش انجام نشد"
        live = tl._path().read_text("utf-8").splitlines() if tl._path().exists() else []
        assert len(live) <= tl.MAX_LINES + 1, len(live)
        # قاعدهٔ اولِ vault: منتقل، نه حذف — کهنه‌ها باید هنوز خواندنی باشند.
        assert tl._rotated().read_text("utf-8").strip(), "دادهٔ کهنه ناپدید شد"
    finally:
        tl.MAX_LINES = real
        _on(False)


def t_hostile_input_never_raises():
    _on()
    _reset()
    try:
        for st in (None, {}, [], "x" * 50_000, {"k": None}, 3, True,
                   {"deep": {"a": {"b": {"c": "d"}}}}):
            tl.step(traj_id="t", phase="decide", state=st)
        assert tl.dropped()["n"] == 0, tl.dropped()
    finally:
        _on(False)


def t_long_fields_are_bounded():
    _on()
    _reset()
    try:
        tl.step(traj_id="t1", phase="decide", state="ب" * 50_000)
        r = json.loads(tl._path().read_text("utf-8").splitlines()[0])
        assert len(r["state"]) <= tl.MAX_FIELD, len(r["state"])
    finally:
        _on(False)


# ─── ۵: مرزِ ماژول ─────────────────────────────────────────────────────────
def t_the_logger_only_records():
    import ast
    tree = ast.parse(Path(tl.__file__).read_text("utf-8"))
    banned = {"subprocess", "urllib", "requests", "socket", "shutil"}
    imported = set()
    for n in ast.walk(tree):
        if isinstance(n, ast.Import):
            imported.update(a.name.split(".")[0] for a in n.names)
        elif isinstance(n, ast.ImportFrom) and n.module:
            imported.add(n.module.split(".")[0])
    assert not (banned & imported), sorted(banned & imported)


def t_the_fallback_redactors_match_the_real_one():
    """دو نسخهٔ محلیِ fail-closed باید با الگوهای سختِ مرجع هم‌راستا بمانند.

    تکرارِ عمدی است (fallback نباید به ماژولِ افتاده تکیه کند) — ولی تکرارِ
    واگرا بدتر از نبودن است، پس این‌جا قفل می‌شود."""
    import cockpit_readmodel as crm
    ref = [p.pattern for p in crm.HARD_SECRET_PATTERNS]
    src = (_OPS / "live" / "server.py").read_text("utf-8")
    src += (_OPS / "budget" / "approval_channel.py").read_text("utf-8")
    for pat in ref:
        assert src.count(pat) >= 2, f"الگوی سختِ «{pat}» در هر دو fallback نیست"


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'✅' if not failed else '❌'} test_trajectory_log: "
          f"{len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
