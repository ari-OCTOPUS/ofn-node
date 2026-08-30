"""test_clock_guard — نقطهٔ کورِ ۱۳۵: ساعتی که به عقب می‌پرد، انقضا را می‌کُشد.

`time.time()` قابلِ تنظیم است — NTP، دستِ کاربر، باتریِ ساعتِ سخت‌افزاری. اگر
عقب برود، هر مهلتی که گذشته بود **دوباره باز می‌شود**؛ روی مسیرِ تأییدِ پول یعنی
یک تأییدِ سوخته می‌تواند زنده شود.

سه چیز باید هم‌زمان درست باشد و دوتای اولش با هم در کشمکش‌اند:
  ۱) پرشِ واقعی گرفته شود (وگرنه محافظ بی‌فایده است).
  ۲) نویزِ عادیِ NTP آلارم ندهد (وگرنه محافظ خاموش می‌شود چون آزاردهنده است).
  ۳) در ابهام، **منقضی** — نه معتبر. اگر ندانیم ساعت چند است، نمی‌توانیم بگوییم
     هنوز وقت هست.
"""
import ast
import json
import sys
import time
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))
import harness   # noqa: E402
ENV = harness.setup("clock-guard")

_OPS = harness.REAL_VAULT / "_ops"
for _p in (str(_OPS), str(_OPS / "budget")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import opslib          # noqa: E402
import clock_guard as cg   # noqa: E402

T0 = 1_800_000_000.0


def _reset(high=None):
    try:
        cg._path().unlink()
    except OSError:
        pass
    cg._last_write[0] = 0.0
    if high is not None:
        cg._write_high(high)


# ─── ۱: پرشِ واقعی گرفته می‌شود ────────────────────────────────────────────
def t_a_backwards_jump_is_detected():
    _reset(high=T0)
    c = cg.check(now=T0 - 3600)
    assert c["trusted"] is False, c
    assert "عقب" in c["why"], c


def t_an_unexpired_deadline_becomes_expired_when_the_clock_jumps_back():
    """قلبِ باگ: کارتی با یک ساعت اعتبار نباید با پرشِ ساعت زنده بماند."""
    _reset(high=T0)
    gone, why = cg.is_expired(T0 + 3600, now=T0 - 600)
    assert gone is True, (gone, why)
    assert "fail-closed" in why, why


def t_the_tolerance_is_wide_enough_for_ntp_but_not_for_a_real_jump():
    """محافظی که سرِ نویزِ عادی آلارم بدهد، خاموش می‌شود."""
    _reset(high=T0)
    assert cg.check(now=T0 - 1)["trusted"] is True
    assert cg.check(now=T0 - cg.BACKWARD_TOLERANCE_S + 5)["trusted"] is True
    assert cg.check(now=T0 - cg.BACKWARD_TOLERANCE_S - 5)["trusted"] is False
    assert 30 <= cg.BACKWARD_TOLERANCE_S <= 600, cg.BACKWARD_TOLERANCE_S


def t_moving_forward_is_always_fine():
    _reset(high=T0)
    for d in (0, 1, 3600, 86_400 * 365):
        assert cg.check(now=T0 + d)["trusted"] is True, d


# ─── ۲: fail-closed در ابهام ──────────────────────────────────────────────
def t_an_unreadable_deadline_is_expired():
    _reset(high=T0)
    for bad in (None, "", "فردا", float("nan"), -1, 0, [], {}):
        gone, why = cg.is_expired(bad, now=T0)
        assert gone is True, (bad, gone)
        assert why, bad


def t_a_normal_deadline_still_works_in_both_directions():
    """گاردی که همه‌چیز را منقضی کند، گارد نیست — بی‌مصرف‌کننده‌اش می‌کند."""
    _reset(high=T0)
    assert cg.is_expired(T0 + 60, now=T0)[0] is False
    assert cg.is_expired(T0 - 60, now=T0)[0] is True


def t_check_never_raises_on_any_input():
    _reset(high=T0)
    for n in (None, 0, -1, 1e18, float("inf")):
        try:
            c = cg.check(now=n)
        except OverflowError:
            continue                      # زمانِ غیرقابلِ نمایش، نه خطای منطقی
        assert set(c) >= {"now", "trusted", "why", "high_water"}


# ─── ۳: خطِ بیشینه ────────────────────────────────────────────────────────
def t_the_high_water_mark_survives_a_restart():
    """بدونِ ماندگاری، ری‌استارت محافظ را صفر می‌کند و پرش نامرئی می‌شود."""
    _reset(high=T0)
    assert cg._read_high() == T0
    c = cg.check(now=T0 - 3600)
    assert c["trusted"] is False, "بعد از خواندنِ دیسک هم باید بگیرد"


def t_the_first_ever_observation_is_trusted():
    """سیستمِ تازه نباید خودش را قفل کند."""
    _reset()
    c = cg.check(now=T0)
    assert c["trusted"] is True and "اولین" in c["why"]
    assert cg._read_high() == T0


def t_the_mark_is_not_rewritten_on_every_call():
    """نوشتنِ هر تماس روی دیسک، یک چکِ ارزان را گران می‌کند."""
    _reset(high=T0)
    cg._last_write[0] = T0
    before = cg._path().stat().st_mtime_ns
    for i in range(5):
        cg.check(now=T0 + i)
    assert cg._path().stat().st_mtime_ns == before, "خطِ بیشینه هر تماس نوشته شد"
    cg.check(now=T0 + cg._WRITE_EVERY_S + 1)
    assert cg._read_high() > T0, "بعد از فاصلهٔ لازم هم به‌روز نشد"


def t_a_read_only_disk_does_not_break_the_check():
    real = cg._path
    try:
        cg._path = lambda: Path("Z:/nope/clock.json")
        c = cg.check(now=T0)
        assert isinstance(c["trusted"], bool)
    finally:
        cg._path = real


# ─── ۴: مرزِ ماژول ────────────────────────────────────────────────────────
def t_the_guard_only_judges_time():
    tree = ast.parse(Path(cg.__file__).read_text("utf-8"))
    banned = {"subprocess", "urllib", "requests", "socket", "shutil"}
    imported = set()
    for n in ast.walk(tree):
        if isinstance(n, ast.Import):
            imported.update(a.name.split(".")[0] for a in n.names)
        elif isinstance(n, ast.ImportFrom) and n.module:
            imported.add(n.module.split(".")[0])
    assert not (banned & imported), sorted(banned & imported)


def t_the_approval_path_actually_uses_it():
    """ماژولِ بی‌مصرف‌کننده باگ را نمی‌بندد — فقط شبیهِ بستنش است."""
    src = (_OPS / "telegram_center" / "center.py").read_text("utf-8")
    assert "clock_guard" in src, "مسیرِ تأیید هنوز از ساعتِ خام استفاده می‌کند"
    i = src.index("clock_guard")
    around = src[max(0, i - 900):i + 400]
    assert "expired" in around, "clock_guard وصل است ولی نه روی مسیرِ انقضا"


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'✅' if not failed else '❌'} test_clock_guard: "
          f"{len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
