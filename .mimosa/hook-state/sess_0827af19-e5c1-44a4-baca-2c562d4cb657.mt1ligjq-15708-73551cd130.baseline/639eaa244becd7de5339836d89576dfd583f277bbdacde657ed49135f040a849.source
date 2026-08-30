#!/usr/bin/env python3
"""test_tg_site_fire_log.py — ADR-042 Phase 0: fire log never changes send result.

UNREGISTERED in run_all.py (worklock). Run: python _ops/tests/test_tg_site_fire_log.py
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent))
sys.path.insert(0, str(_HERE.parent / "budget"))
sys.path.insert(0, str(_HERE.parent / "telegram_center"))

import harness  # noqa: E402
ENV = harness.setup("tg-site-fire-log")

os.environ["OCTOPUS_TG_SITE_FIRE_LOG"] = "1"
os.environ.pop("TELEGRAM_BOT_TOKEN", None)

import tg_site_fire_log as fire  # noqa: E402
import opslib  # noqa: E402


def _log_path() -> Path:
    return Path(opslib.STATE_DIR) / "tg-site-fire.jsonl"


def t_flag_off_zero_io():
    os.environ["OCTOPUS_TG_SITE_FIRE_LOG"] = "0"
    p = _log_path()
    before = p.exists()
    fire.record_call(sender="test")
    os.environ["OCTOPUS_TG_SITE_FIRE_LOG"] = "1"
    if before:
        return
    assert not p.exists(), "flag off must not create the log"


def t_record_appends_without_text():
    fire.record_call(sender="unit")
    p = _log_path()
    assert p.exists(), "flag on must append"
    row = json.loads(p.read_text(encoding="utf-8").strip().splitlines()[-1])
    assert "text" not in row and "token" not in row
    assert row.get("sender") == "unit"
    assert row.get("caller_func") == "t_record_appends_without_text"


def t_unwired_send_text_still_false_and_logs():
    import approval_channel as ac  # noqa: WPS433
    ch = ac.TelegramApprovalChannel(state_dir=str(opslib.STATE_DIR))
    # no token → not wired → False (existing contract)
    ok = ch.send_text("phase0-probe")
    assert ok is False
    rows = [json.loads(x) for x in _log_path().read_text(encoding="utf-8").splitlines() if x.strip()]
    assert any(r.get("sender") == "approval_channel.send_text" for r in rows), rows[-3:]


def t_catalog_has_84():
    cat = fire._load_catalog()
    assert len(cat) == 84, len(cat)


if __name__ == "__main__":
    fails = []
    for fn in (t_flag_off_zero_io, t_record_appends_without_text,
               t_unwired_send_text_still_false_and_logs, t_catalog_has_84):
        try:
            fn()
            print("ok", fn.__name__)
        except Exception as e:  # noqa: BLE001
            fails.append((fn.__name__, type(e).__name__, str(e)))
            print("FAIL", fn.__name__, type(e).__name__, e)
    print("FAIL" if fails else "PASS", "— test_tg_site_fire_log")
    raise SystemExit(1 if fails else 0)
