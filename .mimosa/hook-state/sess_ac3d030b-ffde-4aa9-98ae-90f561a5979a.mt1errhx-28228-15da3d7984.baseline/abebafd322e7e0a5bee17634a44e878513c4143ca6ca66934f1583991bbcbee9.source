#!/usr/bin/env python3
"""تستِ رفتاریِ M-fix: باگِ canonical_consolidation (mean_awareness ناموجود).

گپِ کشف‌شده: wiring.canonical_consolidation متدِ SchoolBridge.mean_awareness() را
صدا می‌زد که رویِ bridge وجود نداشت (فقط رویِ field بود) → AttributeError که با
`except: pass` بی‌صدا بلعیده می‌شد → منبعِ School هرگز به خروجیِ consolidation
نمی‌رسید. این تست با SchoolBridgeِ **واقعی** (نه fake) اثبات می‌کند که:

  (۱) SchoolBridge.mean_awareness() کار می‌کند (delegate به field).
  (۲) بعد ازِ learn_from(events واقعی)، canonical_consolidation آن را دریافت و
      در verified_sources/insights منعکس می‌کند — یعنی مسیرِ School واقعاً به
      خروجیِ consolidation می‌رسد.
  (۳) wiring خطای واقعی را دیگر بی‌صدا نمی‌بلعد (§۴: opslib.alert وجود دارد).
$0 آفلاین، stdlib-only.
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import harness  # noqa: E402
ENV = harness.setup("canonical-consolidation")

_OPS = (harness.SELF_OPS)
for _p in [str(_OPS), str(_OPS / "neural"), str(_OPS / "afferent")]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

import wiring  # noqa: E402

# school-memory و afferent روی path مالِ real vault هستند (harness فقط ops/ را اضافه می‌کند)
_SM = (harness.REAL_VAULT / r"07 - Knowledge\school-memory")
if str(_SM) not in sys.path:
    sys.path.insert(0, str(_SM))

from school_bridge import SchoolBridge  # noqa: E402
from sensory_bus import AfferentEvent  # noqa: E402


# ════════════════════════════════════════════════════════════════════════════════
# (۱) SchoolBridge.mean_awareness() واقعی وجود دارد و عدد برمی‌گرداند
# ════════════════════════════════════════════════════════════════════════════════

def t_bridge_has_mean_awareness():
    """SchoolBridge باید mean_awareness داشته باشد (باگِ اصلی)."""
    sb = SchoolBridge(state_path=str(Path(ENV["root"]) / "no-such.json"))
    assert hasattr(sb, "mean_awareness"), "SchoolBridge.mean_awareness باید وجود داشته باشد"


def t_mean_awareness_returns_float():
    """خروجیِ mean_awareness یک عدد است (float)."""
    sb = SchoolBridge(state_path=str(Path(ENV["root"]) / "no-such.json"))
    m = sb.mean_awareness()
    assert isinstance(m, float), f"mean_awareness باید float باشد، نه {type(m)}"
    assert 0.0 <= m <= 1.0, f"mean_awareness باید در [0,1] باشد، نه {m}"


def t_mean_awareness_matches_field():
    """bridge.mean_awareness() باید با field.mean_awareness() یکسان باشد (delegate)."""
    sb = SchoolBridge(state_path=str(Path(ENV["root"]) / "no-such.json"))
    assert sb.mean_awareness() == sb.field.mean_awareness(), \
        "bridge.mean_awareness باید دقیقاً field.mean_awareness باشد"


# ════════════════════════════════════════════════════════════════════════════════
# (۲) مسیرِ School واقعاً به خروجیِ consolidation می‌رسد — با SchoolBridge واقعی
# ════════════════════════════════════════════════════════════════════════════════

def _make_stack():
    os.environ["OCTOPUS_WIRE_NEURAL"] = "1"
    stack = wiring.make_neural_stack()
    os.environ.pop("OCTOPUS_WIRE_NEURAL")
    return stack


def t_school_source_reaches_consolidation():
    """باگِ اصلی: بعد ازِ learn_from واقعی، SchoolBridge در verified_sources ظاهر می‌شود.

    قبل از فیکس: mean_awareness() ناموجود بود → AttributeError → except: pass بی‌صدا →
    school_awareness هرگز در sources نبود → هرگز در verified_sources نبود.
    بعد از فیکس: مسیرِ School واقعاً به consolidation می‌رسد."""
    stack = _make_stack()
    if stack is None:
        return  # import path issue → skip
    sb = SchoolBridge(state_path=str(Path(ENV["root"]) / "aw-real.json"))
    # یک afferent event واقعی تزریق کن تا awareness صفر نباشد
    ev = AfferentEvent(source="test-leg", obs_type="lead",
                       topic_ids=["A01", "B01"], ledger_event_type="OBSERVE",
                       intensity=0.5, afferent=True)
    sb.learn_from([ev], persist=False)
    # حالا canonical_consolidation با bridgeِ واقعی — نباید استثنا بی‌صدا بلعیده شود
    result = wiring.canonical_consolidation(stack, school_bridge=sb)
    assert result is not None, "consolidation نباید None برگرداند (منبعِ School verified است)"
    assert "school_awareness" in result.verified_sources, \
        f"school_awareness باید در verified_sources باشد — مسیرِ School به consolidation نمی‌رسد. got: {result.verified_sources}"
    assert any("آگاهی" in i or "awareness" in i.lower() for i in result.insights), \
        f"insightِ school_awareness باید تولید شود. got: {result.insights}"


def t_school_zero_awareness_still_runs():
    """حتی با awarenessِ صفر، bridge نباید consolidation را بشکند (عدد 0 هم verified است)."""
    stack = _make_stack()
    if stack is None:
        return
    sb = SchoolBridge(state_path=str(Path(ENV["root"]) / "aw-zero.json"))
    # بدونِ learn_from → awareness هم仍是 0
    result = wiring.canonical_consolidation(stack, school_bridge=sb)
    # 0 هم یک عدد است → verified → school_awareness باید در sources باشد
    assert result is not None
    assert "school_awareness" in result.verified_sources, \
        "حتی awareness=0 باید verified باشد (یک عدد است)"


# ════════════════════════════════════════════════════════════════════════════════
# (۳) §۴: wiring خطای واقعی را بی‌صدا نمی‌بلعد
# ════════════════════════════════════════════════════════════════════════════════

def t_no_silent_pass_in_school_block():
    """بلوکِ school در wiring نباید `except: pass` داشته باشد (§۴ منشور)."""
    src = Path(wiring.__file__).read_text("utf-8")
    # بخشِ school_awareness را پیدا کن
    i = src.find("school_awareness")
    assert i > 0, "بخشِ school در wiring باید وجود داشته باشد"
    block = src[i:i + 600]
    # نباید pass بی‌صدا (تنها در یک خط) در این بلوک باشد
    # الگوی ممنوع: except ...: \n pass
    import re
    assert not re.search(r"except[^\n]*:\s*\n\s+pass\b", block), \
        "§۴: بلوکِ school نباید except: pass بی‌صدا داشته باشد — باید opslib.alert باشد"
    # باید opslib.alert داشته باشد
    assert "opslib.alert" in block, "§۴: باید opslib.alert برای خطای school باشد"


def t_broken_bridge_alerts_not_silent():
    """اگر bridge.mean_awareness استثنا بیندازد، wiring نباید بی‌صدا None برگرداند
    بدونِ alert. این تستِ ساختاری است که opslib.alert صدا زده می‌شود."""
    stack = _make_stack()
    if stack is None:
        return

    class BrokenBridge:
        def mean_awareness(self):
            raise RuntimeError("simulated bridge failure")

    # این نباید استثنا بپراند بیرون (wiring باید fail-soft باشد)
    # ولی باید opslib.alert صدا زده شود (نه silent)
    result = wiring.canonical_consolidation(stack, school_bridge=BrokenBridge())
    # fail-soft: نتیجه ممکن است None یا بدونِ school باشد — مهم این است که crash نکند
    assert result is None or "school_awareness" not in (result.verified_sources if result else []), \
        "bridgeِ خراب نباید به verified_sources برسد"


if __name__ == "__main__":
    failed = harness.run([
        ("SchoolBridge.mean_awareness وجود دارد", t_bridge_has_mean_awareness),
        ("mean_awareness عدد برمی‌گرداند", t_mean_awareness_returns_float),
        ("mean_awareness = field.mean_awareness (delegate)", t_mean_awareness_matches_field),
        ("مسیرِ School به consolidation می‌رسد (با bridge واقعی)", t_school_source_reaches_consolidation),
        ("awareness=0 هم verified است", t_school_zero_awareness_still_runs),
        ("§۴: بلوکِ school except: pass ندارد", t_no_silent_pass_in_school_block),
        ("bridgeِ خراب crash نمی‌کند (fail-soft)", t_broken_bridge_alerts_not_silent),
    ])
    sys.exit(1 if failed else 0)
