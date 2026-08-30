"""test_cockpit_truthful.py — P3 (2026-07-15): فرمان‌های راست‌گوی کابین (/wiring, /health).
قانونِ سخت: هیچ فایلِ غایب یا snapshotِ کهنه هرگز 🟢 رندر نمی‌شود؛ فایلِ تازه 🟢 می‌شود."""
import os
import sys
import tempfile
import time
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent))
sys.path.insert(0, str(_HERE.parent / "budget"))

import harness
ENV = harness.setup("cockpit_truthful")

from approval_channel import TelegramApprovalChannel  # noqa: E402


def _chan(state_dir):
    return TelegramApprovalChannel(state_dir=str(state_dir))


def t_a_wiring_missing_never_green():
    with tempfile.TemporaryDirectory() as td:
        ch = _chan(td)
        out = ch._cmd_wiring()
        assert "اتصال" in out
        assert "🟢 تازه: 0" in out, out          # همه غایب → صفر سبز


def t_b_wiring_fresh_heart_is_green():
    with tempfile.TemporaryDirectory() as td:
        st = Path(td)
        (st / "pulse").mkdir(parents=True)
        (st / "pulse" / "heart-shadow-latest.json").write_text("{}", "utf-8")
        ch = _chan(st)
        out = ch._cmd_wiring()
        assert "🟢" in out and "Heart" in out, out


def t_c_health_money_gate_closed_by_default():
    with tempfile.TemporaryDirectory() as td:
        ch = _chan(td)
        out = ch._cmd_health()
        assert "گیتِ پول" in out and "🔒" in out, out    # LIVE-ENABLED غایب → بسته
        assert "Capability marker: 🔴" in out, out       # marker غایب → قرمز


def t_d_health_capability_present_green():
    with tempfile.TemporaryDirectory() as td:
        st = Path(td)
        (st / "CAPABILITY-OK.flag").write_text("{}", "utf-8")
        ch = _chan(st)
        out = ch._cmd_health()
        assert "Capability marker: 🟢" in out, out


if __name__ == "__main__":
    for f in (t_a_wiring_missing_never_green, t_b_wiring_fresh_heart_is_green,
              t_c_health_money_gate_closed_by_default, t_d_health_capability_present_green):
        f()
        print("ok", f.__name__)
    print("PASS test_cockpit_truthful")
