#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_discovery_nudge_high_water_errorhunt — TypeError زندهٔ mark_nudged.

شاهد: governor-alerts ۱۱ بار «mark_nudged() missing 1 required positional
argument: 'high_water'». ثبت در run_all: گزارش شود (WORKLOCK).
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import harness  # noqa: E402

ENV = harness.setup("discovery-nudge-high-water-errorhunt")
_OPS = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_OPS))
sys.path.insert(0, str(_OPS / "cortex"))
sys.path.insert(0, str(_OPS / "budget"))

import discoveries as d  # noqa: E402
import wiring  # noqa: E402


def t_call_site_passes_high_water_arg():
    src = (Path(__file__).resolve().parent.parent / "wiring.py").read_text(
        encoding="utf-8")
    assert "discoveries.mark_nudged()" not in src, \
        "فراخوانِ بی‌آرگومان همان TypeError زنده است"
    assert "discoveries.mark_nudged(" in src


class _Ok:
    wired = True

    def send_text(self, text, reply_markup=None, chat_id=None, stream=None):
        return True


def t_successful_delta_nudge_writes_marker():
    d.record("learn", "الف")
    os.environ["OCTOPUS_WIRE_NEEDS_NUDGE"] = "1"
    os.environ["OCTOPUS_DISCOVERY_NUDGE_DELTA"] = "1"
    epoch0 = wiring._DISCOVERY_STATE["last_epoch"]
    try:
        wiring._DISCOVERY_STATE["last_epoch"] = 0
        r = wiring.discovery_nudge_beat(_Ok(), beat=480)
        assert r and r.get("sent") is True, r
        assert d.NUDGED.exists(), "ارسال موفق باید high_water بنویسد"
        assert d.unseen_since_nudge() == 0
    finally:
        os.environ.pop("OCTOPUS_WIRE_NEEDS_NUDGE", None)
        os.environ.pop("OCTOPUS_DISCOVERY_NUDGE_DELTA", None)
        wiring._DISCOVERY_STATE["last_epoch"] = epoch0


CHECKS = [
    ("call-site دیگر mark_nudged() بی‌آرگومان ندارد", t_call_site_passes_high_water_arg),
    ("ارسال موفق + delta ⇒ نشانگر نوشته می‌شود نه TypeError", t_successful_delta_nudge_writes_marker),
]

if __name__ == "__main__":
    failed = harness.run(CHECKS)
    sys.exit(1 if failed else 0)
