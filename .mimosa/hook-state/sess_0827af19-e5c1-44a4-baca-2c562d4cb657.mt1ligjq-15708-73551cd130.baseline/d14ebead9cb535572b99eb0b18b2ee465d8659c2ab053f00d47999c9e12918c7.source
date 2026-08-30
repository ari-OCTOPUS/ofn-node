"""test_ui_truth.py — 2026-07-15: حذفِ دکمه‌های مرده + toastِ صادق + گاردِ stalenessِ کانال‌ها.
دکمه‌های ideas/school/ingest که صف می‌شدند و هرگز اجرا نمی‌شدند حذف شدند؛ toast دیگر دروغِ
«اجرا می‌شود» نمی‌گوید؛ کارتِ کانال‌ها snapshotِ کهنه را 🟢 نشان نمی‌دهد."""
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
ENV = harness.setup("ui_truth")

from approval_channel import TelegramApprovalChannel  # noqa: E402


def _chan(sd=None):
    return TelegramApprovalChannel(state_dir=str(sd) if sd else None)


def t_a_dead_buttons_removed_from_all_tabs():
    ch = _chan()
    for page in ("brain", "school", "doctor", "organs", "safety", "alerts"):
        cds = [b["callback_data"] for row in ch._tab_keyboard(page)["inline_keyboard"] for b in row]
        for verb in ("ideas", "school", "ingest"):
            assert not any(cd.startswith(f"act:{verb}:") for cd in cds), f"{verb} هنوز در {page}"
    # consolidate + doctor (flag-دار، واقعی) باید بمانند
    brain = [b["callback_data"] for row in ch._tab_keyboard("brain")["inline_keyboard"] for b in row]
    assert any(cd.startswith("act:consolidate:run:") for cd in brain), brain
    doctor = [b["callback_data"] for row in ch._tab_keyboard("doctor")["inline_keyboard"] for b in row]
    assert any(cd.startswith("act:doctor:run:") for cd in doctor)


def t_b_toast_no_longer_lies():
    with tempfile.TemporaryDirectory() as td:
        ch = _chan(td)
        os.environ.pop("OCTOPUS_TG_EXEC", None)
        # verbِ بی‌مصرف‌کننده → صادقانه می‌گوید مصرف‌کننده ندارد
        r_ideas = ch._run_act("ideas", "rebuild")
        assert "مصرف‌کنندهٔ اجرا ندارد" in r_ideas, r_ideas
        assert "مصرف می‌کند" not in r_ideas       # دروغِ قدیمی رفته
        # doctor با اجرای خاموش → می‌گوید خاموش است
        r_doc = ch._run_act("doctor", "run")
        assert "اجرا خاموش" in r_doc, r_doc
        # با اجرای روشن → صادقانه «اجرا می‌کند»
        os.environ["OCTOPUS_TG_EXEC"] = "1"
        try:
            assert "اجرا می‌کند" in ch._run_act("consolidate", "run")
        finally:
            os.environ.pop("OCTOPUS_TG_EXEC", None)


def t_c_channels_card_stale_never_green():
    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "channel-status.json"
        p.write_text(json.dumps({"channels": {"telegram": {"live": True, "mode": "poll"}}}), "utf-8")
        old = time.time() - 8 * 24 * 3600
        os.utime(p, (old, old))
        card = _chan(td)._render_card("alerts", "channels")
        assert "⚪" in card and "کهنه" in card, card
        assert "🟢" not in card                    # snapshotِ کهنه هرگز سبز


if __name__ == "__main__":
    for f in (t_a_dead_buttons_removed_from_all_tabs, t_b_toast_no_longer_lies,
              t_c_channels_card_stale_never_green):
        f()
        print("ok", f.__name__)
    print("PASS test_ui_truth")
