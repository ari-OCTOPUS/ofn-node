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


def t_alert_stress_measures_now_not_all_of_history():
    """۲۰۲۸-۰۷-۲۸ — یک شمارندهٔ یک‌طرفه نمی‌تواند سلامتِ **فعلی** را نشان دهد.

    نسخهٔ قبلی خطوطِ کلِ یک فایلِ append-only را می‌شمرد و روی
    `clamp(n/400)*0.5` اشباع می‌کرد. فایلِ زنده ۲۵۶۳ خط داشت، پس عدد از مدت‌ها
    پیش روی سقفِ ۰.۵ **قفل** بود و دیگر هرگز پایین نمی‌آمد.

    اثرش زنجیره‌ای بود و تا قلبِ یادگیری می‌رفت: `organism_stress` پین →
    `error_rate` پین → آستانهٔ `>0.2` → سیگنالِ `errors_high` در **هر** تیک
    (اندازه‌گیریِ زنده: ۷۰۳ از ۷۰۳). و ورودیِ ثابت اطلاعات ندارد؛ BCM روی یک
    ثابت چیزی یاد نمی‌گیرد.

    ناوردیِ این تست: **تاریخِ کهنه نباید استرسِ امروز را بالا نگه دارد.**"""
    import datetime as _dt
    al = opslib.OPS / "governor" / "governor-alerts.md"
    al.parent.mkdir(parents=True, exist_ok=True)
    old = al.read_text("utf-8") if al.exists() else None
    now = _dt.datetime.now()

    def _blk(when, n=1):
        t = when.strftime("%Y-%m-%dT%H:%M:%S")
        return "".join(f"## {t} (x)\n- alert\n\n" for _ in range(n))

    try:
        # ۵۰۰۰ خطِ **کهنه** (۳۰ روز پیش) — نسخهٔ قبلی این را سقف می‌خواند
        al.write_text(_blk(now - _dt.timedelta(days=30), 400), "utf-8")
        v_old, d_old = stress._alerts_stress()
        assert v_old == 0.0, f"تاریخِ کهنه هنوز استرس می‌سازد: {v_old} ({d_old})"

        # همان حجم ولی **امروز** — باید بالا برود
        al.write_text(_blk(now - _dt.timedelta(hours=1), 40), "utf-8")
        v_new, _ = stress._alerts_stress()
        assert v_new > 0.0, "هشدارِ امروز استرس نساخت"

        # و سقف رعایت شود
        assert 0.0 <= v_new <= 0.5, v_new
    finally:
        if old is not None:
            al.write_text(old, "utf-8")
        elif al.exists():
            al.unlink()          # از اول نبود → نباید بماند و تستِ بعدی را بشکند


def t_alert_stress_can_actually_come_down():
    """قلبِ باگ: عدد باید **برگشت‌پذیر** باشد، وگرنه سیگنال نیست."""
    import datetime as _dt
    al = opslib.OPS / "governor" / "governor-alerts.md"
    al.parent.mkdir(parents=True, exist_ok=True)
    old = al.read_text("utf-8") if al.exists() else None
    now = _dt.datetime.now()
    try:
        _t1 = (now - _dt.timedelta(minutes=5)).strftime("%Y-%m-%dT%H:%M:%S")
        al.write_text("".join(f"## {_t1} (x)\n- alert\n\n" for _ in range(30)), "utf-8")
        hi, _ = stress._alerts_stress()
        _t2 = (now - _dt.timedelta(days=5)).strftime("%Y-%m-%dT%H:%M:%S")
        al.write_text("".join(f"## {_t2} (x)\n- alert\n\n" for _ in range(30)), "utf-8")
        lo, _ = stress._alerts_stress()
        assert hi > lo, f"استرس برنگشت: {hi} → {lo}"
        assert lo == 0.0, lo
    finally:
        if old is not None:
            al.write_text(old, "utf-8")
        elif al.exists():
            al.unlink()          # از اول نبود → نباید بماند و تستِ بعدی را بشکند


# ─── ۲۰۲۶-۰۷-۲۸: کالیبراسیون از دادهٔ واقعی ──────────────────────────────
# فیکسِ صبح پنجره را ۲۴ساعته کرد ولی سقف را نگه داشت (`clamp(n/20)*0.5`)، پس از
# n=۲۰ به بعد صاف می‌شد. توزیعِ واقعیِ ۱۸ روز (۶۹ پنجره از `governor-alerts.md`):
#     میانه ۰ · صدکِ ۷۵ = ۵۴ · صدکِ ۹۰ = ۱۱۸ · بیشینه ۴۰۱ · میانهٔ روزهای فعال ۵۹
# یعنی نقطهٔ اشباع زیرِ صدکِ ۷۵ بود: هر روزِ فعالی همان ۰.۵ را می‌داد.
#
# ⚠️ تصحیحِ صادقانه‌ای که همین اندازه‌گیری ساخت: سیگنالِ دودویی `errors_high`
# روی همان ۱۸ روز ۴۷٪ شلیک می‌کرده (آنتروپیِ ۰.۹۹۹ بیت). پس «اطلاعات ندارد»
# دربارهٔ پنجرهٔ اخیر درست بود، نه دربارهٔ کلِ تاریخ. سودِ واقعی: پیوستگی + امکانِ
# رسیدن به ترس، که با سقفِ ۰.۵ ساختاراً ناممکن بود.

def _set_alerts(n: int):
    """n هشدارِ تاریخ‌دارِ امروز در درختِ ایزوله بساز.

    ⚠️ حتماً `_restore_alerts()` را در `finally` صدا بزن. نسخهٔ اولِ این تست‌ها
    این کار را نمی‌کرد و `t_d_calm_when_all_good` را قرمز کرد — تست‌ها به ترتیبِ
    الفبا می‌دوند و `t_c…` چهارصد هشدار برای `t_d…` باقی گذاشته بود. تستی که
    وضعیتِ مشترک را پاک نکند، همسایه‌اش را می‌شکند نه خودش را.
    """
    import datetime as _dt
    al = opslib.OPS / "governor" / "governor-alerts.md"
    al.parent.mkdir(parents=True, exist_ok=True)
    now = _dt.datetime.now() - _dt.timedelta(minutes=5)
    al.write_text("".join(
        f"## {now.strftime('%Y-%m-%dT%H:%M:%S')}\n- ⚠️ x\n" for _ in range(n)), "utf-8")
    return al


def _restore_alerts():
    al = opslib.OPS / "governor" / "governor-alerts.md"
    try:
        al.unlink()
    except OSError:
        pass


def _calib(v):
    if v:
        os.environ["OCTOPUS_STRESS_CALIBRATED"] = "1"
    else:
        os.environ.pop("OCTOPUS_STRESS_CALIBRATED", None)


def t_flag_off_keeps_the_old_formula_exactly():
    """خاموش = بایت‌به‌بایتِ قبلی. این تغییر روی مسیرِ ترس است؛ خاموشیِ نصفه ممنوع."""
    _set_alerts(40)
    _calib(False)
    try:
        s, _ = stress._alerts_stress()
        assert s == 0.5, s                 # ۴۰ ≥ ۲۰ → اشباع، مثل قبل
    finally:
        _calib(False)
        _restore_alerts()


def t_calibrated_never_saturates():
    """قلبِ تغییر: ۲۰ و ۴۰۱ نباید یک عدد بدهند."""
    _calib(True)
    try:
        vals = []
        for n in (20, 54, 118, 401):
            _set_alerts(n)
            vals.append(stress._alerts_stress()[0])
        assert vals == sorted(vals), vals
        assert len(set(vals)) == 4, f"اشباع شد: {vals}"
        assert vals[-1] < 1.0, vals
    finally:
        _calib(False)
        _restore_alerts()


def t_the_half_point_comes_from_data_not_a_guess():
    """ثابت باید مستند و در دامنهٔ توزیعِ مشاهده‌شده باشد."""
    assert 6 <= stress._ALERT_HALF_POINT <= 401
    src = Path(stress.__file__).read_text("utf-8")
    i = src.index("_ALERT_HALF_POINT")
    assert "صدکِ" in src[max(0, i - 700):i], "اشتقاقِ عدد مستند نشده"


def t_a_typical_active_day_lands_near_the_middle():
    """k = میانهٔ روزهای فعال ⇒ همان n باید ≈۰.۵ بدهد."""
    _calib(True)
    try:
        _set_alerts(stress._ALERT_HALF_POINT)
        s, _ = stress._alerts_stress()
        assert 0.45 <= s <= 0.55, s
    finally:
        _calib(False)
        _restore_alerts()


def t_fear_becomes_reachable_but_stays_exceptional():
    """با سقفِ ۰.۵ زیرسیستمِ هشدار **هرگز** به آژیرِ خودش نمی‌رسید.
    حالا می‌رسد — ولی فقط در روزِ استثنایی، نه روزِ شلوغ."""
    _calib(True)
    try:
        _set_alerts(60)                      # روزِ فعالِ معمولی
        assert stress._alerts_stress()[0] < stress.FEAR_THRESHOLD
        _set_alerts(400)                     # نزدیکِ بیشینهٔ تاریخی
        assert stress._alerts_stress()[0] >= stress.FEAR_THRESHOLD
    finally:
        _calib(False)
        _restore_alerts()


def t_zero_alerts_is_zero_in_both_modes():
    for on in (False, True):
        _calib(on)
        try:
            _set_alerts(0)
            assert stress._alerts_stress()[0] == 0.0
        finally:
            _calib(False)
            _restore_alerts()
        _restore_alerts()


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'✅' if not failed else '❌'} test_stress: {len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
