"""test_improve_smallest_fix_proposal.py — وصلهٔ smallest_fix → proposal (propose-only) — ۲۰۲۶-۰۸-۰۷.

پیش‌زمینه: `deep_dive.smallest_fix` (دقیق‌ترین خروجیِ تشخیصیِ دکتر) تا امروز
DEAD-OUTPUT بود — فقط در کارتِ تلگرام/چت نمایش داده می‌شد، هرگز به یک proposal
تبدیل نمی‌شد. این وصله آن را به‌صورتِ **additive + propose-only** به `generate_proposals`
می‌رساند: یک proposal با `source=smallest_fix`, `auto_applicable=False`, `status=proposed`
— یعنی فقط کارتِ تأیید، نه اجرای خودکار. هم‌الگو با منابعِ audit/doctor/synth.

قواعدِ وصله (همه این تست رویشان نگهبان است):
- additive: smallest_fix خالی → صفر proposalِ نو (بایت‌به‌بایتِ امروز).
- propose-only: هرگز auto_applicable=True (human gate همیشه زنده).
- fail-soft: نبود/خراب‌بودنِ self-knowledge → بدون crash، صفر proposal.
- محتوای proposal دقیقاً متنِ smallest_fix است.

اجرا: python -X utf8 test_improve_smallest_fix_proposal.py
"""
import json
import os
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent))
sys.path.insert(0, str(_HERE.parent / "budget"))
sys.path.insert(0, str(_HERE.parent / "cortex"))

import harness
ENV = harness.setup("cortex")

import importlib  # noqa: E402
import improve  # noqa: E402
importlib.reload(improve)
IMP = improve

STATE = Path(ENV["ops"]) / "state"
SK = STATE / "doctor" / "self-knowledge-latest.json"


def _base_signals(sf=""):
    """سیگنال‌های حداقلی با smallest_fix قابل تنظیم. ماتریسِ خالی = هیچ گافِ audit."""
    return {
        "matrix": {"gaps": [], "maturity_pct": 0},
        "doctor_rfcs": [],
        "synthesis": {},
        "smallest_fix": sf,
    }


def t_a_empty_smallest_fix_no_proposal():
    """smallest_fix خالی → صفر proposal از این منبع (بایت‌به‌بایتِ امروز)."""
    props = IMP.generate_proposals(_base_signals(""))
    sf_props = [p for p in props if p.get("source") == "smallest_fix"]
    assert sf_props == [], f"خالی نباید proposal بسازد: {len(sf_props)}"


def t_b_nonempty_smallest_fix_makes_one_proposal():
    """smallest_fix پر → دقیقاً یک proposal با source=smallest_fix."""
    props = IMP.generate_proposals(_base_signals("تعریف منبع داده‌ای واقعی"))
    sf_props = [p for p in props if p.get("source") == "smallest_fix"]
    assert len(sf_props) == 1, f"باید یک proposal بسازد: {len(sf_props)}"
    p = sf_props[0]
    assert p["status"] == "proposed", "همیشه proposed"
    assert p["auto_applicable"] is False, "propose-only — هرگز auto"
    assert "منبع داده‌ای واقعی" in p["title"], "محتوا در title باید باشد"
    assert "منبع داده‌ای واقعی" in p["suggested_action"], "محتوا در suggested_action"


def t_c_proposal_always_propose_only_never_auto():
    """تحتِ هیچ شرایطی smallest_fix نباید auto_applicable باشد."""
    for sf in ["x", "long " * 100, "تعریفِ منبع"]:
        props = IMP.generate_proposals(_base_signals(sf))
        for p in props:
            if p.get("source") == "smallest_fix":
                assert p["auto_applicable"] is False, "propose-only نقض شد"
                assert p["status"] == "proposed"


def t_d_dedup_on_same_content():
    """دو بار generate_proposals با همان smallest_fix → همان id (idempotent)."""
    p1 = IMP.generate_proposals(_base_signals("فیکسِ یکسان"))
    p2 = IMP.generate_proposals(_base_signals("فیکسِ یکسان"))
    id1 = [p["id"] for p in p1 if p.get("source") == "smallest_fix"]
    id2 = [p["id"] for p in p2 if p.get("source") == "smallest_fix"]
    assert id1 == id2 and len(id1) == 1, f"id باید پایدار/idempotent باشد: {id1} vs {id2}"


def t_e_gather_signals_reads_smallest_fix_from_disk():
    """gather_signals واقعاً self-knowledge-latest.json را می‌خواند."""
    SK.parent.mkdir(parents=True, exist_ok=True)
    SK.write_text(json.dumps({"deep_dive": {"smallest_fix": "یک فیکسِ واقعی"}}), "utf-8")
    try:
        sig = IMP.gather_signals()
        assert sig.get("smallest_fix") == "یک فیکسِ واقعی", \
            f"باید از دیسک بخواند: {sig.get('smallest_fix')!r}"
    finally:
        if SK.exists():
            SK.unlink()


def t_f_fail_soft_on_missing_self_knowledge():
    """نبودِ self-knowledge → gather_signals بدون crash، smallest_fix=''."""
    if SK.exists():
        SK.unlink()
    sig = IMP.gather_signals()   # نباید استثنا بپرد
    assert sig.get("smallest_fix") == "", "نبود فایل باید '' بدهد"


def t_g_fail_soft_on_corrupt_self_knowledge():
    """self-knowledge خراب (نه JSON) → بدون crash، smallest_fix=''."""
    SK.parent.mkdir(parents=True, exist_ok=True)
    SK.write_text("{not valid json", "utf-8")
    try:
        sig = IMP.gather_signals()   # نباید استثنا بپرد
        assert sig.get("smallest_fix") == "", "خرابی باید '' بدهد"
    finally:
        if SK.exists():
            SK.unlink()


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'✅' if not failed else '❌'} test_improve_smallest_fix_proposal: "
          f"{len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
