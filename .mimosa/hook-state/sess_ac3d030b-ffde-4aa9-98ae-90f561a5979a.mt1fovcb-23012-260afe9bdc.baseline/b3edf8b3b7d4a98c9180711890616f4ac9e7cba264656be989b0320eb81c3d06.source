#!/usr/bin/env python3
"""test_acct_beat.py — ضربانِ زندهٔ حسابداری (2026-07-16).
اثبات: فلگ خاموش → None (بایت‌به‌بایت رفتارِ امروز) · kill-switch مقدم · cadence ·
با فلگِ روشن: شمارش‌های صادق + سایدکارِ اتمیکِ ORGANISM-STATE.accounting · بدونِ
ACCT_BEAT_SYNC هیچ pullِ شبکه (synced=False). mini-vault harness."""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent))
sys.path.insert(0, str(_HERE.parent / "budget"))
sys.path.insert(0, str(_HERE.parent / "legs"))

import harness  # noqa: E402
ENV = harness.setup("acct_beat")

import opslib   # noqa: E402
import wiring   # noqa: E402


def _seed_store(n_confirmed=3, n_review=2):
    p = opslib.ORG_ROOT / "03 - Projects" / "Accounting" / "personal" / "txn-store.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    txns = [{"id": f"c{i}", "desc": f"BUNNINGS W {i}", "owner": "armin", "ptype": "expense",
             "review": "confirmed", "amount_cents": -1000, "date": "2026-07-01",
             "source": "pocketsmith-api"} for i in range(n_confirmed)]
    txns += [{"id": f"r{i}", "desc": f"UNKNOWN SHOP {i}", "owner": "unknown",
              "ptype": "unknown", "review": "needs_review", "amount_cents": -500,
              "date": "2026-07-02", "source": "pocketsmith-api"} for i in range(n_review)]
    p.write_text(json.dumps({"txns": txns}, ensure_ascii=False), "utf-8")


def _off():
    for k in ("OCTOPUS_WIRE_ACCT_BEAT", "ACCT_BEAT_SYNC", "CHRONO_ACCT_EVERY_N_BEATS"):
        os.environ.pop(k, None)
    wiring._ACCT_STATE["last_epoch"] = 0               # ریستِ پنجرهٔ epoch بینِ تست‌ها


def t_a_flag_off_none():
    _off()
    assert wiring.acct_beat(beat=240) is None


def t_b_epoch_window_once_per_epoch():
    """الگوی ضدِ aliasing (اسکن #26): در هر epoch دقیقاً یک شلیک — حتی اگر tick دقیقهٔ
    دقیقِ سررسید را نمونه‌برداری نکند (beat=241 هم epochِ 1 است و باید شلیک شود)."""
    _off()
    _seed_store()
    os.environ["OCTOPUS_WIRE_ACCT_BEAT"] = "1"
    os.environ["CHRONO_ACCT_EVERY_N_BEATS"] = "240"
    try:
        assert wiring.acct_beat(beat=100) is None          # epoch 0 — هنوز نه
        assert isinstance(wiring.acct_beat(beat=241), dict)  # epoch 1 — شلیک (modulo این را می‌باخت)
        assert wiring.acct_beat(beat=300) is None          # همان epoch — دوباره نه
        assert isinstance(wiring.acct_beat(beat=485), dict)  # epoch 2 — شلیکِ بعدی
    finally:
        _off()


def t_c_runs_and_writes_sidecar():
    _off()
    _seed_store()
    os.environ["OCTOPUS_WIRE_ACCT_BEAT"] = "1"
    os.environ["CHRONO_ACCT_EVERY_N_BEATS"] = "1"
    try:
        r = wiring.acct_beat(beat=1)
        assert isinstance(r, dict), r
        assert r["synced"] is False                    # بدونِ ACCT_BEAT_SYNC هیچ شبکه
        assert r["memory_active"] == 1, r              # قاعدهٔ bunnings (۳ نمونه)
        assert r["pending_review"] == 2, r
        assert r["drift_alarm"] is False, r
        sp = opslib.STATE_DIR / "ORGANISM-STATE.accounting"
        assert sp.exists(), "سایدکار نوشته نشده"
        d = json.loads(sp.read_text("utf-8"))
        assert d["memory_active"] == 1 and "updated_at" in d, d
    finally:
        _off()


def t_d_killswitch_first():
    _off()
    os.environ["OCTOPUS_WIRE_ACCT_BEAT"] = "1"
    os.environ["CHRONO_ACCT_EVERY_N_BEATS"] = "1"
    stop = opslib.STOP_ORGANISM
    try:
        stop.parent.mkdir(parents=True, exist_ok=True)
        stop.write_text("test", "utf-8")
        assert wiring.acct_beat(beat=1) is None        # kill-switch مقدم بر همه
    finally:
        if stop.exists():
            stop.unlink()
        _off()


if __name__ == "__main__":
    for f in (t_a_flag_off_none, t_b_epoch_window_once_per_epoch, t_c_runs_and_writes_sidecar,
              t_d_killswitch_first):
        f()
        print("ok", f.__name__)
    print("PASS test_acct_beat")
