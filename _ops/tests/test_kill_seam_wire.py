#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_kill_seam_wire.py — «/stop» باید جلوی **خرج** را هم بگیرد، نه فقط افکتورها.

درزی که این تست می‌بندد (ممیزیِ کیل‌سوییچ):

  `opslib.halted()` سه سوییچ را می‌بیند — STOP ِ معمار، STOP-METABOLIC،
  STOP-DEBATE — ولی `_ops/STOP-ORGANISM` را **نه**؛ و همان فایلی است که `/stop` ِ
  تلگرام و کیلِ داشبورد می‌نویسند. افکتورها خودشان STOP-ORGANISM را چک می‌کنند،
  ولی مرجعِ خرج (`organ_gate.reserve`) و مناظرهٔ پولی (`debate_loop.run_debate`)
  از `halted()` رد می‌شوند. یعنی یک‌تپِ توقفِ مالک یک رزروِ پولی را متوقف نمی‌کرد.

  گاردِ M5 **اضافه** می‌کند، برنمی‌دارد: با فلگِ خاموش رفتار بایت‌به‌بایتِ دیروز است.

و باگی که ۲۰۲۶-۰۸-۰۱ پیدا شد و این تست دیگر نمی‌گذارد برگردد:

  هر دو صداکننده گزاره را با `__import__("now_moves.kill_seam_closer", …)` صدا
  می‌زدند، ولی هیچ‌کدام `_ops` را روی `sys.path` ندارند (`debate_loop` فقط
  `_ops/debate` و `_ops/budget` می‌گذارد؛ `cortex/model_router` هم همین‌طور).
  پس **مسلح‌کردنِ فلگ deny نمی‌کرد، بلکه `ModuleNotFoundError` می‌داد** — و چون
  آن خط پیش از هر `try` بود، حتی یک ردیفِ لاگ هم ثبت نمی‌شد (نقضِ «ثبت همیشه»).
  `t_f` دقیقاً همان شکلِ sys.path ِ تولیدی را بازمی‌سازد.

قواعدی که این‌جا قفل می‌شوند:
  · فلگِ خاموش = صفر تغییر (STOP-ORGANISM حاضر باشد و باز هم رزرو اجازه بگیرد).
  · مسلح + STOP-ORGANISM = deny با دلیلِ خوانا، **و یک ردیفِ لاگ**.
  · دلیلِ توقفِ قبلی هرگز بازنویسی نمی‌شود (`not stop`).
  · `halted()` — SoT ِ مشترک — دست‌نخورده می‌ماند؛ گارد بیرونِ آن است.
  · فلگ در `PAPER_FULL_FLAGS` نیست؛ پس بوت هرگز خودش مسلحش نمی‌کند.
"""
import json
import os
import re
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))

import harness  # noqa: E402

ENV = harness.setup("kill-seam-wire")     # قبل از هر importی که state می‌نویسد

# فلگ‌های شلِ مالک نباید قطعیتِ تست را بخورند (همان تلهٔ DEFECT-W4 در test_debate).
os.environ.pop("OCTOPUS_WIRE_KILL_SEAM", None)
os.environ.pop("OCTOPUS_WIRE_DEBATE_LOCAL", None)

import opslib       # noqa: E402
import organ_gate   # noqa: E402
import debate_loop  # noqa: E402
import topics       # noqa: E402

FLAG = "OCTOPUS_WIRE_KILL_SEAM"
_OPS_SELF = _HERE.parent            # <worktree>/_ops


def _arm():
    os.environ[FLAG] = "1"


def _disarm():
    os.environ.pop(FLAG, None)


def _stop_on():
    opslib.STOP_ORGANISM.parent.mkdir(parents=True, exist_ok=True)
    opslib.STOP_ORGANISM.write_text("stop (test)", "utf-8")


def _stop_off():
    if opslib.STOP_ORGANISM.exists():
        opslib.STOP_ORGANISM.unlink()


def _clean():
    _disarm()
    _stop_off()
    if opslib.STOP_METABOLIC.exists():
        opslib.STOP_METABOLIC.unlink()


def _log_rows():
    if not opslib.ORGAN_LOG.exists():
        return []
    return [json.loads(ln) for ln in
            opslib.ORGAN_LOG.read_text("utf-8").splitlines() if ln.strip()]


def _topic():
    return {"id": "seam-0", "source": "SEED_TOPICS", "text": topics.SEED_TOPICS[0]}


# سه آینهٔ مستقلِ «کدام flag در profileِ بوت است». هر سه باید بررسی شوند؛ اگر یکی
# پیدا نشد (rename/refactor) تست قرمز می‌شود، نه اینکه بی‌صدا از رویش رد شود.
_PROFILE_MIRRORS = ("wiring.py", "budget/cockpit_readmodel.py", "dashboard/server.py")
_OPENERS = {"(": ")", "{": "}", "[": "]"}


def _paper_full_block(rel: str) -> str | None:
    """متنِ **کاملِ** مجموعهٔ `PAPER_FULL_FLAGS` یک فایل — با شمارشِ متوازنِ براکت.

    چرا نه پنجرهٔ کاراکتریِ ثابت: نسخهٔ اولِ این گارد ۱۲۰۰ کاراکترِ اولِ بعد از نام
    را می‌خواند، ولی تاپلِ `wiring.py` همین امروز ۱۵۰۴ کاراکتر است — یعنی گارد از
    قبل ~۲۰٪ کور بود و با هر flagِ تازه کورتر می‌شد. سنجیده شد: درجِ همین FLAG
    درست پیش از پرانتزِ بسته، تست را **سبز** نگه می‌داشت. یعنی دقیقاً همان قاعده‌ای
    که این بند قرار بود قفلش کند از ته فهرست قابلِ دور زدن بود.
    """
    src = (_OPS_SELF / rel).read_text("utf-8", errors="replace")
    m = re.search(r"PAPER_FULL_FLAGS\s*=\s*([({\[])", src)
    if not m:
        return None
    o = m.group(1)
    c = _OPENERS[o]
    depth = 0
    for i in range(m.start(1), len(src)):
        if src[i] == o:
            depth += 1
        elif src[i] == c:
            depth -= 1
            if depth == 0:
                return src[m.start():i + 1]
    return None


def t_a_flag_off_means_stop_organism_is_ignored_by_the_spender():
    """اثباتِ «صفر تغییر»: STOP-ORGANISM هست، فلگ خاموش ⇒ رزرو مثل دیروز اجازه می‌گیرد.

    این بند دربارهٔ چیزی است که **نباید** بشود. اگر گارد بی‌فلگ اثر بگذارد،
    یک تغییرِ رفتاریِ اعلام‌نشده روی مسیرِ پول نشسته است."""
    _clean()
    _stop_on()
    try:
        r = organ_gate.reserve("ZIMAN", 0.001, task="seam-off")
        assert r.get("allow") is True, r
    finally:
        _clean()


def t_b_armed_seam_denies_a_paid_reservation_and_records_it():
    """مسلح + STOP-ORGANISM ⇒ deny با دلیلِ خوانا، و **ثبت** (نه سکوت)."""
    _clean()
    _arm()
    _stop_on()
    try:
        before = len(_log_rows())
        r = organ_gate.reserve("ZIMAN", 0.001, task="seam-on")
        assert r.get("allow") is False, r
        assert r.get("reason") == "halted:STOP(organism)", r
        rows = _log_rows()
        assert len(rows) == before + 1, f"deny باید ثبت شود: {before} → {len(rows)}"
        assert rows[-1].get("reason") == "halted:STOP(organism)", rows[-1]
    finally:
        _clean()


def t_c_armed_without_the_stop_file_changes_nothing():
    """گارد فقط با فایلِ توقف می‌بندد؛ مسلح‌بودن به‌تنهایی هیچ‌چیز را deny نمی‌کند."""
    _clean()
    _arm()
    try:
        assert opslib.kill_seam_denies() is False
        r = organ_gate.reserve("ZIMAN", 0.001, task="seam-armed-nostop")
        assert r.get("allow") is True, r
    finally:
        _clean()


def t_d_an_existing_halt_reason_is_never_overwritten():
    """اگر `halted()` از قبل دلیلی داده، گارد آن را با «STOP(organism)» عوض نمی‌کند.

    دلیلِ درست، اقدامِ درستِ مالک را می‌سازد؛ دلیلِ عوض‌شده او را دنبالِ فایلِ
    اشتباه می‌فرستد."""
    _clean()
    _arm()
    _stop_on()
    opslib.STOP_METABOLIC.write_text("metabolic (test)", "utf-8")
    try:
        r = organ_gate.reserve("ZIMAN", 0.001, task="seam-precedence")
        assert r.get("allow") is False, r
        assert r.get("reason") == "halted:STOP-METABOLIC", r
    finally:
        _clean()


def t_e_armed_seam_stops_the_paid_debate_too():
    """همان درز در `debate_loop.run_debate` — چون آن هم از `halted()` رد می‌شود."""
    _clean()
    _arm()
    _stop_on()
    try:
        r = debate_loop.run_debate(_topic())
        assert r.get("status") == "halted", r
        assert r.get("reason") == "STOP(organism)", r
    finally:
        _clean()

    # و روی دیگرِ سکه: فلگ خاموش ⇒ همان STOP-ORGANISM مناظره را متوقف نمی‌کند.
    _stop_on()
    try:
        r2 = debate_loop.run_debate(_topic())
        assert r2.get("status") != "halted", r2
    finally:
        _clean()


def t_f_the_armed_seam_survives_a_production_shaped_syspath():
    """رگرسیونِ ۰۸-۰۱: صداکنندهٔ واقعی `_ops` را روی sys.path ندارد.

    این‌جا دقیقاً همان شکل بازسازی می‌شود — `_ops` از مسیر برداشته و
    `now_moves` از `sys.modules` پاک می‌شود. گاردِ مسلح باید **deny** بدهد،
    نه `ModuleNotFoundError`. (با سیم‌کشیِ قبلی همین‌جا می‌ترکید.)"""
    _clean()
    saved_path = list(sys.path)
    saved_mods = {k: v for k, v in sys.modules.items()
                  if k == "now_moves" or k.startswith("now_moves.")}
    sys.path[:] = [p for p in sys.path if Path(p or ".").resolve() != _OPS_SELF]
    for k in saved_mods:
        del sys.modules[k]
    try:
        try:
            import now_moves  # noqa: F401
            raise AssertionError("بازسازیِ محیط شکست خورد: now_moves هنوز import می‌شود")
        except ImportError:
            pass
        _arm()
        _stop_on()
        r = organ_gate.reserve("ZIMAN", 0.001, task="seam-noimport")
        assert r.get("allow") is False, r
        assert r.get("reason") == "halted:STOP(organism)", r
    finally:
        sys.path[:] = saved_path
        sys.modules.update(saved_mods)
        _clean()


def t_g_the_shared_halted_source_of_truth_is_untouched():
    """گارد **کنارِ** `halted()` نشسته، نه داخلش.

    اگر روزی کسی STOP-ORGANISM را به خودِ `halted()` اضافه کند، دامنه‌اش از دو
    صداکنندهٔ سنجیده‌شده به همهٔ صداکننده‌های `halted()` می‌پرد — تغییری که رأیِ
    مالک می‌خواهد، نه یک ریفکتور."""
    _clean()
    _arm()
    _stop_on()
    try:
        assert opslib.halted() is None, opslib.halted()
        assert opslib.halted(for_debate=True) is None, opslib.halted(for_debate=True)
        assert opslib.kill_seam_denies() is True
    finally:
        _clean()


def t_h_the_flag_is_off_by_default_and_out_of_the_boot_profile():
    """خانه‌قاعده: فلگِ نو خاموش می‌ماند و بوت خودش مسلحش نمی‌کند.

    `apply_profile` هر عضوِ `PAPER_FULL_FLAGS` را که در env نباشد ۱ می‌کند —
    یعنی برای آن فهرست «غیاب یعنی روشن». اگر این نام آن‌جا برود، مسلح‌سازی از
    دستِ مالک درمی‌آید بی‌آنکه کسی خطی نوشته باشد."""
    _clean()
    assert opslib.kill_seam_denies() is False
    _stop_on()
    try:
        assert opslib.kill_seam_denies() is False, "بدونِ فلگ نباید ببندد"
    finally:
        _clean()
    checked = 0
    for rel in _PROFILE_MIRRORS:
        block = _paper_full_block(rel)
        if block is None:
            continue
        checked += 1
        assert FLAG not in block, f"{rel}: {FLAG} نباید در PAPER_FULL_FLAGS باشد"
    assert checked == len(_PROFILE_MIRRORS), (
        f"گاردِ profile کور شد: فقط {checked} از {len(_PROFILE_MIRRORS)} آینه خوانده شد")


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'✅' if not failed else '❌'} test_kill_seam_wire: "
          f"{len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
