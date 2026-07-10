"""test_stress.py — هومئوستاتِ استرس/ترس (کورتیزولِ ارگانیسم، جلسه ۴۶).

بدکارکردنِ زیرسیستم → استرس↑؛ عبور از آستانه → ترس؛ ترس → خود-تغییری مکث (fail-closed)؛
بهبود → فروکش (هومئوستاز). ترس = محافظه‌کاری، نه تخریب.
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
ENV = harness.setup("stress")

import stress    # noqa: E402
import opslib    # noqa: E402


def _set_money(aud):
    with opslib.LockedJson(opslib.STATE_DIR / "telemetry-latest.json") as lj:
        lj.write({"month": {"aud": aud}})


def _set_sigma(s):
    with opslib.LockedJson(opslib.STATE_DIR / "replication-latest.json") as lj:
        lj.write({"sigma": {"sigma_effective": s}})


def t_a_money_stress_rises_toward_cap():
    _set_money(0)
    assert stress._money_stress()[0] == 0.0
    _set_money(15)
    assert 0.4 <= stress._money_stress()[0] <= 0.6      # نیمهٔ سقف = استرسِ متوسط
    _set_money(29)
    assert stress._money_stress()[0] >= stress.FEAR_THRESHOLD   # نزدیکِ سقف = ترس


def t_b_heart_sigma_stress_and_cancer_axis():
    _set_sigma(0.0)
    assert stress._heart_stress()[0] == 0.0
    _set_sigma(0.95)
    assert stress._heart_stress()[0] >= stress.FEAR_THRESHOLD   # σ→۱ = محورِ سرطان = ترس


def t_c_assess_organism_stress_is_max():
    _set_money(29)   # مالی در ترس
    _set_sigma(0.0)  # قلب آرام
    a = stress.assess()
    assert a["organism_stress"] == a["subsystems"]["money"]["stress"]   # بیشینه
    assert "money" in a["in_fear"] and a["level"] == "🔴 ترس"


def t_d_calm_when_all_good():
    _set_money(0)
    _set_sigma(0.0)
    a = stress.assess()
    assert a["organism_stress"] < 0.4 and a["level"] == "🟢 آرام" and a["in_fear"] == []


def t_e_fear_pauses_auto_modification():
    """ترس → auto_approve.self_test رد (خود-تغییری تحتِ استرس مکث؛ fail-closed)."""
    import auto_approve, improve, capability_gate
    # همه‌چیزِ دیگر سبز کن تا فقط ترس عاملِ رد باشد
    improve.ACT_AUTO.parent.mkdir(parents=True, exist_ok=True)
    improve.ACT_AUTO.write_text("owner", "utf-8")
    (opslib.STATE_DIR / "ORGANISM-STATE.json").write_text("{}", "utf-8")
    if improve.AUTO_STATE_PATH.exists():
        improve.AUTO_STATE_PATH.unlink()
    capability_gate.mark_capability("green")
    try:
        _set_money(0); _set_sigma(0.0)
        assert auto_approve.self_test()[0] is True        # آرام → مجاز
        _set_money(29)                                    # مالی وارد ترس شد
        ok, why = auto_approve.self_test()
        assert ok is False and "ترس" in why               # ترس → مکث
    finally:
        improve.ACT_AUTO.unlink()


def t_f_homeostasis_recovers():
    """بهبودِ عملکرد → استرس فروکش (هومئوستاز)."""
    _set_money(29)
    assert stress.organism_in_fear()[0] is True
    _set_money(2)                                          # خرج کم شد
    assert stress.organism_in_fear()[0] is False


def t_g_persist_emits_event_on_new_fear():
    """ورودِ نو به ترس → رویدادِ task.blocked (به مالک هشدار)، ضدِ اسپم (فقط ورودِ نو)."""
    sys.path.insert(0, str(_HERE.parent))
    import events
    _set_money(0); _set_sigma(0.0)
    stress.persist()                                      # آرام
    n0 = len(events.recent(50))
    _set_money(29)                                        # وارد ترس
    stress.persist()
    log = events.recent(50)
    assert any("ترس" in (e.get("summary") or "") for e in log)
    # چرخهٔ دوم بدونِ تغییر → رویدادِ نو نمی‌سازد (ضدِ اسپم)
    n1 = len(events.recent(50))
    stress.persist()
    assert len(events.recent(50)) == n1


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'✅' if not failed else '❌'} test_stress: {len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
