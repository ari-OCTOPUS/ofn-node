#!/usr/bin/env python3
"""تست Brain Cockpit + Content Studio + Project-F Brain ($0).

آیتم ۲: کاکپیتِ چندپروژه‌ای — صفِ تجمیعی، Project-F فقط «درفت در صف»، آلارم RED.
هیچ import از production. PIIProject-F صفر رسانه/هویت.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import harness  # noqa: E402

ENV = harness.setup("cockpit")
for _p in (str((harness.REAL_VAULT / r"_ops\brain")), str((harness.REAL_VAULT / r"_ops"))):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from cockpit import BrainCockpit, ApprovalItem, LEGS  # noqa: E402


# ════════════════════════════════════════════════════════════════════════════════
# Brain Cockpit
# ════════════════════════════════════════════════════════════════════════════════

def t_cockpit_main_menu():
    """منوی اصلی با mode color."""
    cp = BrainCockpit(state_dir=ENV["ops"] / "state")
    m = cp.main_menu()
    assert "🧠" in m and ("🟢" in m or "🟡" in m or "🔴" in m)


def t_cockpit_organism_status():
    """وضعیت ارگانیسم."""
    cp = BrainCockpit(state_dir=ENV["ops"] / "state")
    s = cp.organism_status()
    assert "🐙" in s


def t_cockpit_approval_queue_aggregated():
    """صفِ تأییدِ تجمیعی از چند پا."""
    cp = BrainCockpit(state_dir=ENV["ops"] / "state")
    cp.add_approval("Lead-نقاشی", "تأییدِ quote", 50.0)
    cp.add_approval("Project-F", "تأییدِ درفت", 0.0)
    cp.add_approval("Crypto", "تأییدِ trade", 100.0)
    q = cp.approval_queue_html()
    assert "Lead-نقاشی" in q and "Project-F" in q and "Crypto" in q
    assert "AU$50.00" in q


def t_cockpit_project_f_no_media_identity():
    """Project-F فقط «درفت در صف» — صفر رسانه/هویت/PII در کاکپیت."""
    cp = BrainCockpit(state_dir=ENV["ops"] / "state")
    cp.add_approval("Project-F", "تأییدِ درفت", 0.0)
    q = cp.approval_queue_html()
    # نباید هیچ رسانه/هویت/PII باشد — فقط metadata
    for forbidden in ("media", "photo", "video", "face", "identity", "real name", "saba"):
        assert forbidden.lower() not in q.lower(), f"Project-F نباید {forbidden} لو بدهد"


def t_cockpit_legs_status():
    """وضعیت ۶ پا."""
    cp = BrainCockpit(state_dir=ENV["ops"] / "state")
    s = cp.legs_status()
    for leg in LEGS:
        assert leg["name"] in s


def t_cockpit_money_shadow():
    """نمای پولِ shadow با قفل."""
    cp = BrainCockpit(state_dir=ENV["ops"] / "state")
    m = cp.money_shadow()
    assert "🔒" in m and "shadow" in m


def t_cockpit_alarms_red_only():
    """آلارم‌ها فقط RED."""
    cp = BrainCockpit(state_dir=ENV["ops"] / "state")
    a = cp.alarms()
    assert "🔔" in a


def t_cockpit_daily_brief():
    """بریفِ روز."""
    cp = BrainCockpit(state_dir=ENV["ops"] / "state")
    b = cp.daily_brief()
    assert "📅" in b and "تأیید" in b


def t_cockpit_no_production_import():
    """cockpit هیچ import از *_gate/chrono/money ندارد."""
    import cockpit
    src = open(cockpit.__file__, encoding="utf-8").read()
    forbidden = ["import chrono", "from chrono", "organ_gate", "money_gate",
                 "capability_gate", "budget_gate", "EffectorGate", "opslib"]
    for f in forbidden:
        assert f not in src, f"خطِ قرمز: {f}"


def t_cockpit_empty_queue():
    """صف خالی → پیامِ خالی."""
    cp = BrainCockpit(state_dir=ENV["ops"] / "state")
    q = cp.approval_queue_html()
    assert "خالی" in q


if __name__ == "__main__":
    failed = harness.run([
        ("[BC] منوی اصلی", t_cockpit_main_menu),
        ("[BC] وضعیت ارگانیسم", t_cockpit_organism_status),
        ("[BC] صفِ تأییدِ تجمیعی", t_cockpit_approval_queue_aggregated),
        ("[BC] Project-F صفر رسانه/هویت", t_cockpit_project_f_no_media_identity),
        ("[BC] وضعیت ۶ پا", t_cockpit_legs_status),
        ("[BC] پول shadow", t_cockpit_money_shadow),
        ("[BC] آلارم RED", t_cockpit_alarms_red_only),
        ("[BC] بریف روز", t_cockpit_daily_brief),
        ("[BC] no production import", t_cockpit_no_production_import),
        ("[BC] صف خالی", t_cockpit_empty_queue),
    ])
    sys.exit(1 if failed else 0)
