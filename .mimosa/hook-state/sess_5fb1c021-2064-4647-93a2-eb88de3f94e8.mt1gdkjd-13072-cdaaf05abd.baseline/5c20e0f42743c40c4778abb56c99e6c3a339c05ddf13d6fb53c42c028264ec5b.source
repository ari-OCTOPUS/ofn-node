#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""S1-04_test_cockpit_stop_guard.py — گاردِ STOPِ مالک (Stage-1 P2، مدلِ ساختاریِ review-3).

ناوردیِ سخت: **هیچ مسیرِ خودکاری هرگز STOP-ORGANISMِ مالک را نمی‌نویسد/overwrite/حذف
نمی‌کند.** مدلِ جدید (بدونِ compare-then-delete، صفر TOCTOU):
- کاکپیت restart را با نوشتنِ فقط `RESTART-REQUESTED` سیگنال می‌دهد (نه STOP-ORGANISM).
- organism روی RESTART-REQUESTED هم clean-exit می‌کند.
- launcher فقط RESTART-REQUESTED را پاک می‌کند و **هرگز** STOP-ORGANISM را حذف نمی‌کند؛
  restart فقط اگر STOPِ مالک غایب باشد.
- اگر STOPِ مالک حاضر باشد، کاکپیت restart را رد می‌کند.

$0 آفلاین؛ OPS یک mini-vaultِ موقت (opslib.OPS از env). start-cortex پورتِ واقعیِ 8772 را
probe می‌کند → monkeypatch تا مسیرِ گارد قطعی طی شود (هرگز Popen واقعی رخ نمی‌دهد).
"""
import re
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))
sys.path.insert(0, str(_HERE.parent))
sys.path.insert(0, str(_HERE.parent / "budget"))
sys.path.insert(0, str(_HERE.parent / "live"))

import harness      # noqa: E402
ENV = harness.setup("s1-04-stop-guard")

import importlib    # noqa: E402
import server as live  # noqa: E402
importlib.reload(live)
import opslib        # noqa: E402

OPS = Path(ENV["ops"])


def _clear():
    for n in ("STOP-ORGANISM", "STOP-CORTEX", "RESTART-REQUESTED"):
        p = OPS / n
        if p.exists():
            p.unlink()


# ── restart-organism: هرگز STOP-ORGANISM ننویسد ──────────────────────────────
def t_a_restart_refused_when_owner_stop_present():
    """STOP-ORGANISMِ مالک (هر محتوا) هست → restart رد؛ فایل byte-identical؛ بدونِ RESTART."""
    _clear()
    (OPS / "STOP-ORGANISM").write_text("telegram kill-switch 2026-07-19", "utf-8")
    r = live.do_action("restart-organism")
    assert r["ok"] is False
    assert (OPS / "STOP-ORGANISM").read_text("utf-8") == "telegram kill-switch 2026-07-19"
    assert not (OPS / "RESTART-REQUESTED").exists()


def t_b_restart_writes_only_restart_req_never_stop():
    """بدونِ STOP → restart موفق: RESTART-REQUESTED ساخته می‌شود ولی STOP-ORGANISM هرگز."""
    _clear()
    r = live.do_action("restart-organism")
    assert r["ok"] is True
    assert (OPS / "RESTART-REQUESTED").exists()
    assert not (OPS / "STOP-ORGANISM").exists(), "restart هرگز نباید STOP-ORGANISM بنویسد"


def t_c_restart_never_creates_stop_even_repeated():
    """تکرارِ restart هم هرگز STOP-ORGANISM نمی‌سازد (ناوردیِ ساختاری)."""
    _clear()
    for _ in range(3):
        live.do_action("restart-organism")
        assert not (OPS / "STOP-ORGANISM").exists()


def t_d_multiline_owner_stop_survives_restart():
    """STOPِ مالکِ چندخطی که markerِ قدیمیِ کاکپیت را به‌عنوان یک خط دارد (بردارِ findstr) →
    restart رد و فایل byte-identical (اثباتِ رفعِ باگِ line-based)."""
    _clear()
    owner = "restart via live cockpit\nowner hold — do not restart"
    (OPS / "STOP-ORGANISM").write_text(owner, "utf-8")
    r = live.do_action("restart-organism")
    assert r["ok"] is False
    assert (OPS / "STOP-ORGANISM").read_text("utf-8") == owner
    assert not (OPS / "RESTART-REQUESTED").exists()


# ── start-cortex: هرگز STOP-CORTEX را unlink نکند ────────────────────────────
def t_e_start_cortex_never_unlinks_stop():
    """STOP-CORTEX هست → start رد و فایل دست‌نخورده (هرگز unlink)."""
    _clear()
    (OPS / "STOP-CORTEX").write_text("via owner", "utf-8")
    orig = live._port_alive
    live._port_alive = lambda *a, **k: False   # مغز «خاموش» تا مسیرِ گارد طی شود
    try:
        r = live.do_action("start-cortex")
    finally:
        live._port_alive = orig
    assert r["ok"] is False
    assert (OPS / "STOP-CORTEX").exists()


def t_f_unknown_action_refused_no_write():
    """اقدامِ ناشناخته → ok=False، بدونِ هیچ فایلِ STOP/RESTART."""
    _clear()
    r = live.do_action("delete-everything")
    assert r["ok"] is False
    assert not (OPS / "STOP-ORGANISM").exists()
    assert not (OPS / "RESTART-REQUESTED").exists()


# ── ناوردیِ ساختاریِ launcher: هیچ حذفِ خودکارِ STOP-ORGANISM ──────────────────
def t_g_launcher_never_deletes_stop_organism():
    """RUN-ORGANISM.bat: (۱) صفر دستورِ `del ...STOP-ORGANISM` (invariant با construction)،
    (۲) RESTART-REQUESTED قبل از relaunch پاک می‌شود (بدونِ boot-exit loop)، (۳) پیش از هر
    relaunch، حضورِ STOPِ مالک به `goto stopped` می‌رود (STOP زنده می‌ماند)."""
    bat = _HERE.parent / "RUN-ORGANISM.bat"
    text = bat.read_text("utf-8", errors="replace")
    # (۱) هیچ حذفِ خودکارِ STOP-ORGANISM
    assert not re.search(r"del\s+[^\n]*STOP-ORGANISM", text), \
        "launcher نباید هیچ‌گاه STOP-ORGANISM را حذف کند"
    # (۲) سیگنالِ restart = RESTART-REQUESTED و قبل از `goto loop` پاک می‌شود
    m_del = re.search(r"del\s+[^\n]*RESTART-REQUESTED", text)
    assert m_del, "launcher باید markerِ خودش (RESTART-REQUESTED) را پاک کند"
    i_loop = text.find("goto loop", m_del.end())
    assert i_loop > m_del.end(), \
        "RESTART-REQUESTED باید قبل از relaunch (goto loop) پاک شود تا boot-exit loop نسازد"
    # (۳) در همان شاخهٔ restart، حضورِ STOP → goto stopped (پیش از goto loop)
    branch = text[m_del.end():i_loop]
    assert re.search(r'if exist\s+"[^"]*STOP-ORGANISM"\s+goto stopped', branch), \
        "پیش از relaunch باید حضورِ STOPِ مالک بررسی و به stopped برود"


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'OK' if not failed else 'FAIL'} S1-04_cockpit_stop_guard: "
          f"{len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
