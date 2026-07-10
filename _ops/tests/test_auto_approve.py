"""test_auto_approve.py — موتورِ تصمیمِ درجه‌بندیِ خطر (جلسه ۴۶، رأی مالک
«براساس درجه خطر و اهداف تنظیم کنه مجوز بده»).

اثبات: کد/پول/ژنوم همیشه high→مالک؛ فقط knobِ کم‌خطر + هم‌راستا + سوییتِ سبز اعمال
می‌شود؛ بدونِ پرچمِ مالک هیچ اعمالی نیست؛ اعمال در ledger و برگشت‌پذیر.
"""
import json
import os
import sys
import time
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent))
sys.path.insert(0, str(_HERE.parent / "budget"))
sys.path.insert(0, str(_HERE.parent / "cortex"))

import harness
ENV = harness.setup("auto-approve")

import auto_approve as aa   # noqa: E402
import improve             # noqa: E402
import opslib              # noqa: E402


def _p(title, action, level="tune"):
    return {"title": title, "action": action, "change_level": level, "auto_ok": True}


def t_a_classify_high_risk_never_auto():
    """کد/پول/spawn/ژنوم/human-append → همیشه high (رأیِ مالک)."""
    for kw in ("کدِ production را عوض کن", "پول بیشتری خرج کن", "یک سلولِ نو spawn کن",
               "ژنوم را تغییر بده", "human-append را دور بزن", "apply_merge را اجرا کن"):
        assert aa.classify(_p(kw, kw, "tune")) == "high", kw
    assert aa.classify(_p("x", "y", "code")) == "high"        # هر code = high
    assert aa.classify(_p("کادنس را تندتر کن", "HEART_SAMPLE_INTERVAL_S", "tune")) == "low"
    assert aa.classify(_p("بازپیکربندیِ ساده", "چیزی", "reconfig")) == "medium"


def t_b_high_risk_escalates_even_with_permission():
    improve.ACT_AUTO.parent.mkdir(parents=True, exist_ok=True)
    improve.ACT_AUTO.write_text("owner", "utf-8")
    try:
        d = aa.decide(_p("پول بیشتر خرج کن", "budget را بالا ببر", "reconfig"))
        assert d["action"] == "escalate" and d["risk"] == "high"
    finally:
        improve.ACT_AUTO.unlink()


def t_c_no_permission_no_apply():
    """بدونِ پرچمِ مالک، هیچ اعمالِ خودکار — فقط درجه‌بندی."""
    if improve.ACT_AUTO.exists():
        improve.ACT_AUTO.unlink()
    res = aa.run([_p("کادنس", "HEART_SAMPLE_INTERVAL_S را تنظیم کن")])
    assert res["permission"] is False and res["applied"] == []
    assert res["escalated"] and "مجوز" in res["escalated"][0]["why"]


def t_d_self_test_gates_apply():
    """بدونِ سوییتِ سبز (CAPABILITY-OK) → escalate حتی با پرچم و knobِ درست."""
    improve.ACT_AUTO.write_text("owner", "utf-8")
    # ORGANISM-STATE تازه (مشاهده زنده)
    (opslib.STATE_DIR / "ORGANISM-STATE.json").write_text("{}", "utf-8")
    try:
        # CAPABILITY-OK وجود ندارد → self_test رد
        ok, why = aa.self_test()
        assert ok is False
        d = aa.decide(_p("کادنس", "HEART_SAMPLE_INTERVAL_S را تنظیم کن"))
        assert d["action"] == "escalate" and "تستِ خود" in d["reason"]
    finally:
        improve.ACT_AUTO.unlink()


def t_e_full_green_gate_applies_knob_bounded_and_reversible():
    """با پرچم + مشاهدهٔ زنده + سوییتِ سبزِ معتبر → knob در کرانِ امن اعمال و در ledger ثبت."""
    import capability_gate
    improve.ACT_AUTO.write_text("owner", "utf-8")
    (opslib.STATE_DIR / "ORGANISM-STATE.json").write_text("{}", "utf-8")
    if improve.AUTO_STATE_PATH.exists():
        improve.AUTO_STATE_PATH.unlink()
    capability_gate.mark_capability("green: test")     # سیستم خودش را سبز تست کرد
    try:
        assert aa.self_test()[0] is True
        res = aa.run([_p("کادنسِ نمونه", "HEART_SAMPLE_INTERVAL_S را به میانه ببر")])
        assert len(res["applied"]) == 1
        knob = res["applied"][0]["knob"]
        val = res["applied"][0]["value"]
        lo, hi = improve.AUTO_KNOBS[knob]
        assert lo <= val <= hi                          # درونِ کرانِ امن
        disk = json.loads(aa.KNOBS_PATH.read_text("utf-8"))
        assert disk[knob] == val                        # persist (برگشت‌پذیر: فایل را پاک کن)
        assert os.environ.get(knob) == str(val)         # اثرِ runtime
    finally:
        improve.ACT_AUTO.unlink()


def t_f_only_one_apply_per_run_refractory():
    """در هر run فقط یک اعمال (گامِ کوچک) + ثبتِ refractory تا دومی نیفتد."""
    import capability_gate
    improve.ACT_AUTO.write_text("owner", "utf-8")
    (opslib.STATE_DIR / "ORGANISM-STATE.json").write_text("{}", "utf-8")
    if improve.AUTO_STATE_PATH.exists():
        improve.AUTO_STATE_PATH.unlink()
    capability_gate.mark_capability("green: test")
    try:
        res = aa.run([_p("k1", "HEART_SAMPLE_INTERVAL_S"),
                      _p("k2", "CORTEX_THINK_EVERY_N")])
        assert len(res["applied"]) == 1        # فقط یکی
        # دومین run بلافاصله → refractory بسته → هیچ اعمال
        res2 = aa.run([_p("k3", "CORTEX_THINK_EVERY_N")])
        assert res2["applied"] == []
    finally:
        improve.ACT_AUTO.unlink()


def t_g_persisted_knobs_restored_within_bounds():
    with opslib.LockedJson(aa.KNOBS_PATH) as lj:
        lj.write({"CORTEX_THINK_EVERY_N": 6, "BOGUS_KNOB": 999,
                  "HEART_SAMPLE_INTERVAL_S": 999999})  # یکی خارج از کران
    os.environ.pop("CORTEX_THINK_EVERY_N", None)
    os.environ.pop("HEART_SAMPLE_INTERVAL_S", None)
    aa.load_persisted_knobs()
    assert os.environ.get("CORTEX_THINK_EVERY_N") == "6"       # درونِ کران → بازگردانده شد
    assert os.environ.get("HEART_SAMPLE_INTERVAL_S") is None   # خارج از کران → رد
    assert os.environ.get("BOGUS_KNOB") is None                # غیرِwhitelist → رد


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'✅' if not failed else '❌'} test_auto_approve: {len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
