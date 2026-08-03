#!/usr/bin/env python3
"""تستِ رفتاریِ P-M2: سیم‌کشیِ canonical_consolidation در حلقهٔ زنده.

گپِ recon: canonical_consolidation فقط در تست‌ها صدا می‌شود؛ در حلقهٔ زنده
سیم‌کشی نشده بود → ادعای «یک مسیرِ حافظهٔ واحد» محقق نشده بود (هنوز دو مسیرِ
جدا: school_bridge.learn_from + ConsolidationCycle). حالا پشتِ flagِ نو
OCTOPUS_WIRE_CONSOLIDATION سیم‌کشی شد.

این تست اثبات می‌کند:
  (الف) flag روشن + beat مضربِ N → consolidation_beat fire و منبعِ School را
      می‌گنجاند (school_awareness در verified_sources) — با SchoolBridgeِ واقعی.
  (ب) flag خاموش → consolidation_beat no-op (None) برمی‌گرداند (no regression).
  (ج) beat غیرِ مضربِ N → no-op (فقط هر N beat).
  (د) kill-switch (STOP) فعال → no-op حتی با flag روشن.
  (هـ) consolidation در organism tick واقعاً صدا زده می‌شود (structural: wired).
$0 آفلاین، stdlib-only.
"""
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import harness  # noqa: E402
ENV = harness.setup("consolidation-wiring")

_OPS = (harness.SELF_OPS)
for _p in [str(_OPS), str(_OPS / "neural"), str(_OPS / "afferent")]:
    if _p not in sys.path:
        sys.path.insert(0, _p)
_SM = (harness.REAL_VAULT / r"07 - Knowledge\school-memory")
if str(_SM) not in sys.path:
    sys.path.insert(0, str(_SM))

import wiring  # noqa: E402
from school_bridge import SchoolBridge  # noqa: E402
from sensory_bus import AfferentEvent  # noqa: E402

ORGANISM_SRC = (_OPS / "organism.py").read_text("utf-8")


def _stack():
    os.environ["OCTOPUS_WIRE_NEURAL"] = "1"
    s = wiring.make_neural_stack()
    os.environ.pop("OCTOPUS_WIRE_NEURAL")
    return s


def _real_bridge():
    """SchoolBridge واقعی با یک AfferentEvent تزریق‌شده (awareness > 0)."""
    sb = SchoolBridge(state_path=str(Path(ENV["root"]) / "aw-pm2.json"))
    ev = AfferentEvent(source="test-leg", obs_type="lead",
                       topic_ids=["A01", "B01"], ledger_event_type="OBSERVE",
                       intensity=0.5, afferent=True)
    sb.learn_from([ev], persist=False)
    return sb


# ════════════════════════════════════════════════════════════════════════════════
# (الف) flag روشن + beat مضربِ N → fire + منبعِ School
# ════════════════════════════════════════════════════════════════════════════════

def t_flag_on_fires_with_school_source():
    """flag روشن + beat مضربِ 720 → consolidation fire و school_awareness در verified."""
    stack = _stack()
    if stack is None:
        return  # import skip
    os.environ["OCTOPUS_WIRE_CONSOLIDATION"] = "1"
    sb = _real_bridge()
    result = wiring.consolidation_beat(stack, school_bridge=sb, beat=720)
    os.environ.pop("OCTOPUS_WIRE_CONSOLIDATION")
    assert result is not None, "consolidation باید fire شود (beat=720 مضربِ N)"
    assert "school_awareness" in result.verified_sources, \
        f"منبعِ School باید بیاید. verified_sources={result.verified_sources}"


def t_flag_on_school_in_insights():
    """flag روشن → insightِ school_awareness تولید می‌شود."""
    stack = _stack()
    if stack is None:
        return
    os.environ["OCTOPUS_WIRE_CONSOLIDATION"] = "1"
    sb = _real_bridge()
    result = wiring.consolidation_beat(stack, school_bridge=sb, beat=1440)
    os.environ.pop("OCTOPUS_WIRE_CONSOLIDATION")
    assert result is not None
    assert any("آگاهی" in i or "awareness" in i.lower() for i in result.insights), \
        f"insightِ school باید تولید شود. insights={result.insights}"


# ════════════════════════════════════════════════════════════════════════════════
# (ب) flag خاموش → no-op (no regression)
# ════════════════════════════════════════════════════════════════════════════════

def t_flag_off_is_noop():
    """flag خاموش → consolidation_beat None برمی‌گرداند (no-op)."""
    os.environ.pop("OCTOPUS_WIRE_CONSOLIDATION", None)
    stack = _stack()
    sb = _real_bridge()
    result = wiring.consolidation_beat(stack, school_bridge=sb, beat=720)
    assert result is None, "flag خاموز باید no-op باشد (no regression)"


def t_flag_off_in_summary():
    """wire_summary باید wire_consolidation را نشان دهد (پیش‌فرض خاموز)."""
    os.environ.pop("OCTOPUS_WIRE_CONSOLIDATION", None)
    s = wiring.wire_summary()
    assert "wire_consolidation" in s
    assert s["wire_consolidation"] is False, "پیش‌فرض باید خاموز باشد"


# ════════════════════════════════════════════════════════════════════════════════
# (ج) فقط هر N beat (نه هر tick)
# ════════════════════════════════════════════════════════════════════════════════

def t_non_multiple_beat_is_noop():
    """beat غیرِ مضربِ N → no-op (حتی با flag روشن)."""
    stack = _stack()
    if stack is None:
        return
    os.environ["OCTOPUS_WIRE_CONSOLIDATION"] = "1"
    sb = _real_bridge()
    # N=720 پیش‌فرض؛ beat=100 مضرب نیست
    result = wiring.consolidation_beat(stack, school_bridge=sb, beat=100)
    os.environ.pop("OCTOPUS_WIRE_CONSOLIDATION")
    assert result is None, "beat غیرِ مضربِ N نباید fire شود"


def t_zero_beat_is_noop():
    """beat=0 → no-op (bootstrap، هنوز نباید fire)."""
    stack = _stack()
    if stack is None:
        return
    os.environ["OCTOPUS_WIRE_CONSOLIDATION"] = "1"
    result = wiring.consolidation_beat(stack, beat=0)
    os.environ.pop("OCTOPUS_WIRE_CONSOLIDATION")
    assert result is None, "beat=0 نباید fire شود"


# ════════════════════════════════════════════════════════════════════════════════
# (د) kill-switch
# ════════════════════════════════════════════════════════════════════════════════

def t_killswitch_blocks_consolidation():
    """STOP فعال → consolidation no-op حتی با flag روشن."""
    stack = _stack()
    if stack is None:
        return
    os.environ["OCTOPUS_WIRE_CONSOLIDATION"] = "1"
    sb = _real_bridge()
    import opslib
    opslib.STOP_ORGANISM.write_text("kill", "utf-8")
    try:
        result = wiring.consolidation_beat(stack, school_bridge=sb, beat=720)
    finally:
        try:
            opslib.STOP_ORGANISM.unlink()
        except OSError:
            pass
    os.environ.pop("OCTOPUS_WIRE_CONSOLIDATION")
    assert result is None, "kill-switch باید consolidation را بلوک کند"


# ════════════════════════════════════════════════════════════════════════════════
# (هـ) سیم‌کشیِ واقعی در organism.py (structural)
# ════════════════════════════════════════════════════════════════════════════════

def t_organism_calls_consolidation_beat():
    """organism.py باید consolidation_beat را در tick صدا بزند (سیم‌کشی واقعی)."""
    assert "consolidation_beat" in ORGANISM_SRC, \
        "organism باید consolidation_beat را در tick صدا بزند"


def t_organism_makes_school_bridge():
    """organism.py باید SchoolBridge را در startup بسازد وقتی flag روشن است."""
    assert "make_school_bridge" in ORGANISM_SRC, \
        "organism باید make_school_bridge را در startup صدا بزند"


def t_organism_consolidation_gated_on_protective():
    """consolidation باید زیرِ گاردِ not _protective_skip باشد (مانندِ doctor)."""
    # بلوکِ consolidation را پیدا کن
    idx = ORGANISM_SRC.find("consolidation_beat")
    assert idx > 0
    # قبل از آن باید not _protective_skip باشد (در همان گارد)
    before = ORGANISM_SRC[max(0, idx - 400):idx]
    assert "_protective_skip" in before, \
        "consolidation باید روی not _protective_skip گیت باشد (مانندِ doctor)"


def t_organism_consolidation_alerts_on_error():
    """§۴: بلوکِ consolidation نباید except: pass بی‌صدا باشد — باید alert."""
    idx = ORGANISM_SRC.find("consolidation_beat")
    assert idx > 0
    block = ORGANISM_SRC[idx:idx + 400]
    assert "opslib.alert" in block, \
        "§۴: consolidation error باید alert شود (خطای خاموش ممنون)"


# ════════════════════════════════════════════════════════════════════════════════
# verification-gate حفظ شده
# ════════════════════════════════════════════════════════════════════════════════

def t_unverified_school_discarded():
    """verification-gate: اگر school awareness عددی نباشد، discard می‌شود."""
    stack = _stack()
    if stack is None:
        return
    os.environ["OCTOPUS_WIRE_CONSOLIDATION"] = "1"

    class BadBridge:
        def mean_awareness(self):
            return "not a number"   # غیرِ عددی → باید discard شود

    # بدونِ منبعِ verified دیگر → bare ConsolidatedInsight (نه None — تمایز Phase 1)
    result = wiring.consolidation_beat(stack, school_bridge=BadBridge(), beat=720)
    os.environ.pop("OCTOPUS_WIRE_CONSOLIDATION")
    from neural.consolidation import ConsolidatedInsight
    assert isinstance(result, ConsolidatedInsight), \
        f"school غیرعددی → bare object انتظار می‌رود، نه None یا {type(result)}"
    assert result.insights == [], "هیچ منبعی نباید insights تولید کند"


if __name__ == "__main__":
    failed = harness.run([
        # (الف) flag on + fire + school
        ("flag on → fire + school_awareness", t_flag_on_fires_with_school_source),
        ("flag on → school در insights", t_flag_on_school_in_insights),
        # (ب) no-op
        ("flag off → no-op", t_flag_off_is_noop),
        ("flag off در summary", t_flag_off_in_summary),
        # (ج) every N beats
        ("beat غیرِ مضربِ N → no-op", t_non_multiple_beat_is_noop),
        ("beat=0 → no-op", t_zero_beat_is_noop),
        # (د) kill-switch
        ("kill-switch → no-op", t_killswitch_blocks_consolidation),
        # (هـ) wiring real
        ("organism consolidation_beat صدا می‌زند", t_organism_calls_consolidation_beat),
        ("organism make_school_bridge", t_organism_makes_school_bridge),
        ("consolidation روی not _protective_skip", t_organism_consolidation_gated_on_protective),
        ("consolidation error alert", t_organism_consolidation_alerts_on_error),
        # verification-gate
        ("verification-gate: school غیرعددی discard", t_unverified_school_discarded),
    ])
    sys.exit(1 if failed else 0)
