#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""S1-04_test_cockpit_stop_guard.py — گاردِ P2 (Stage-1 Security، 2026-07-20).

ناوردی: هیچ endpointِ کاکپیت (`do_action`) حق ندارد STOPِ مالک را حذف/overwrite/revoke
کند. تنها markerِ byte-sensitiveِ خودِ کاکپیت («restart via live cockpit») «قابلِ ادامه»
است؛ هر محتوای دیگر = STOP مالک → رد. فایلِ ناخوانا = fail-closed.

$0 آفلاین، بدونِ شبکه/پروسه — OPS یک mini-vaultِ موقت (opslib.OPS از env). start-cortex
پورتِ واقعیِ 8772 را probe می‌کند؛ برای قطعیت probe را monkeypatch می‌کنیم تا «خاموش»
دیده شود و مسیرِ گارد طی شود (هرگز Popen واقعی رخ نمی‌دهد چون RUN-CORTEX.bat در tmp نیست).
"""
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
_MARK = "restart via live cockpit"


def _clear():
    for n in ("STOP-ORGANISM", "STOP-CORTEX", "RESTART-REQUESTED"):
        p = OPS / n
        if p.exists():
            p.unlink()


# ── restart-organism ─────────────────────────────────────────────────────────
def t_a_restart_refused_when_owner_stop_present():
    """STOP-ORGANISMِ مالک (محتوای دلخواه) هست → restart رد؛ فایل دست‌نخورده، بدونِ RESTART."""
    _clear()
    (OPS / "STOP-ORGANISM").write_text("telegram kill-switch 2026-07-19", "utf-8")
    r = live.do_action("restart-organism")
    assert r["ok"] is False
    assert (OPS / "STOP-ORGANISM").read_text("utf-8") == "telegram kill-switch 2026-07-19", "STOP مالک نباید overwrite شود"
    assert not (OPS / "RESTART-REQUESTED").exists(), "نباید restart درخواست شود"


def t_b_restart_allowed_when_no_stop():
    """بدونِ STOP → restart ادامه می‌یابد (رفتارِ قبلی: STOP + RESTART ساخته می‌شود)."""
    _clear()
    r = live.do_action("restart-organism")
    assert r["ok"] is True
    assert (OPS / "STOP-ORGANISM").exists() and (OPS / "RESTART-REQUESTED").exists()
    assert (OPS / "STOP-ORGANISM").read_text("utf-8").strip() == _MARK


def t_c_restart_allowed_when_only_cockpit_marker():
    """STOPِ حاویِ markerِ خودِ کاکپیت → قابلِ ادامه (رفتارِ restart دوباره مجاز)."""
    _clear()
    (OPS / "STOP-ORGANISM").write_text(_MARK, "utf-8")
    r = live.do_action("restart-organism")
    assert r["ok"] is True
    assert (OPS / "RESTART-REQUESTED").exists()


def t_d_restart_marker_is_byte_sensitive():
    """نزدیک‌ولی‌ناهمسانِ marker (spacing/متنِ دیگر) = STOP مالک → رد (byte-sensitive)."""
    _clear()
    for near in ("Restart via live cockpit", "restart via  live cockpit",
                 "restart via live cockpit!", "کاربر restart"):
        (OPS / "STOP-ORGANISM").write_text(near, "utf-8")
        r = live.do_action("restart-organism")
        assert r["ok"] is False, near
        assert (OPS / "STOP-ORGANISM").read_text("utf-8") == near, near


def t_e_restart_failclosed_on_unreadable_stop(monkeypatch=None):
    """اگر خواندنِ STOP خطا دهد → fail-closed (رد)، هرگز overwrite/relaunch."""
    _clear()
    (OPS / "STOP-ORGANISM").write_text("owner", "utf-8")
    orig = Path.read_text

    def _boom(self, *a, **k):
        if self.name == "STOP-ORGANISM":
            raise OSError("simulated unreadable")
        return orig(self, *a, **k)
    Path.read_text = _boom
    try:
        r = live.do_action("restart-organism")
    finally:
        Path.read_text = orig
    assert r["ok"] is False
    assert not (OPS / "RESTART-REQUESTED").exists()


# ── start-cortex ─────────────────────────────────────────────────────────────
def t_f_start_cortex_never_unlinks_stop():
    """STOP-CORTEX هست → start رد و فایل دست‌نخورده (هرگز unlink)."""
    _clear()
    (OPS / "STOP-CORTEX").write_text("via owner", "utf-8")
    orig_probe = live._port_alive
    live._port_alive = lambda *a, **k: False   # مغز «خاموش» تا مسیرِ گارد طی شود
    try:
        r = live.do_action("start-cortex")
    finally:
        live._port_alive = orig_probe
    assert r["ok"] is False
    assert (OPS / "STOP-CORTEX").exists(), "STOP-CORTEX هرگز نباید حذف شود"


def t_g_unknown_action_refused_no_write():
    """اقدامِ ناشناخته → ok=False، بدونِ ساختِ هیچ فایلِ STOP/RESTART."""
    _clear()
    r = live.do_action("delete-everything")
    assert r["ok"] is False
    assert not (OPS / "STOP-ORGANISM").exists()
    assert not (OPS / "RESTART-REQUESTED").exists()


def t_h_claim_is_atomic_create_only():
    """_claim_cockpit_stop: create-only با O_EXCL. اثباتِ نتیجهٔ TOCTOU — اگر STOPِ مالک
    (حتی چندخطی، بردارِ findstr) موجود باشد، هرگز overwrite نمی‌شود."""
    _clear()
    sp = OPS / "STOP-ORGANISM"
    # غایب → markerِ کاکپیت را atomically می‌سازد
    assert live._claim_cockpit_stop(sp) is True
    assert sp.read_text("utf-8").strip() == _MARK
    # markerِ خودِ کاکپیت موجود → refreshِ امن مجاز
    assert live._claim_cockpit_stop(sp) is True
    # STOPِ مالکِ چندخطی که markerِ کاکپیت را به‌عنوان یک خط دارد → رد (findstr می‌افتاد)
    sp.write_text("restart via live cockpit\nowner hold — do not restart", "utf-8")
    assert live._claim_cockpit_stop(sp) is False
    assert sp.read_text("utf-8") == "restart via live cockpit\nowner hold — do not restart"


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'OK' if not failed else 'FAIL'} S1-04_cockpit_stop_guard: "
          f"{len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
