"""test_channel_status_stale_not_green.py — P1 (2026-07-15): قانونِ کابینِ راست‌گو —
snapshot ِ بی‌نویسنده هرگز سبز رندر نمی‌شود. readmodel متادیتای stale می‌دهد و
truth-cards برای فایلِ کهنه/غایب آیکنِ غیرسبز برمی‌گرداند."""
import json
import os
import sys
import tempfile
import time
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent))
sys.path.insert(0, str(_HERE.parent / "budget"))

import harness
ENV = harness.setup("channel_status_stale")

from cockpit_readmodel import CockpitReadModel  # noqa: E402


def t_a_stale_snapshot_flagged():
    with tempfile.TemporaryDirectory() as td:
        st = Path(td)
        p = st / "channel-status.json"
        p.write_text(json.dumps({"channels": {"telegram": {"live": True}}}), "utf-8")
        old = time.time() - 7 * 24 * 3600
        os.utime(p, (old, old))
        rm = CockpitReadModel(state_dir=str(st))
        d = rm.read_channels()
        assert d.get("_stale") is True, d
        assert "_snapshot_ts" in d
        cards = {c["id"]: c for c in rm.read_truth_cards()}
        assert cards["channel_status"]["icon"] != "🟢", cards["channel_status"]


def t_b_missing_files_never_green():
    with tempfile.TemporaryDirectory() as td:
        rm = CockpitReadModel(state_dir=td)
        for c in rm.read_truth_cards():
            assert c["icon"] != "🟢", c


def t_c_fresh_file_is_green():
    with tempfile.TemporaryDirectory() as td:
        st = Path(td)
        (st / "pulse").mkdir(parents=True)
        (st / "pulse" / "heart-shadow-latest.json").write_text("{}", "utf-8")
        rm = CockpitReadModel(state_dir=str(st))
        cards = {c["id"]: c for c in rm.read_truth_cards()}
        assert cards["heart_shadow"]["icon"] == "🟢", cards["heart_shadow"]


if __name__ == "__main__":
    for f in (t_a_stale_snapshot_flagged, t_b_missing_files_never_green,
              t_c_fresh_file_is_green):
        f()
        print("ok", f.__name__)
    print("PASS test_channel_status_stale_not_green")
