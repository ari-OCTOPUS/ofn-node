#!/usr/bin/env python3
"""test_pain_calibration.py — WS-C: کالیبراسیونِ درد + قراردادِ ADR-034 proposal-only.

سه یافتهٔ اندازه‌گیری‌شده که این فایل آن‌ها را قفل می‌کند:

  ۱) توزیعِ واقعیِ درد روی ۲۲۱۴ تیکِ ثبت‌شده (`state/neural/effect-shadow.jsonl`)
     بازهٔ [۰.۱۰۲ ، ۰.۱۵۰] است و آستانه ۰.۷۰ — رفلکس روی هیچ ورودیِ مشاهده‌شده‌ای
     نمی‌تواند شلیک کند. آستانهٔ داده‌محورِ ۰.۳۵ (پشتِ فلگ) روی همان ۲۲۱۴ تیک
     **صفر** شلیک می‌دهد ولی یک بحرانِ واقعی را می‌گیرد.

  ۲) `severity` در تصویرِ تولید حذف می‌شود (neural_driver.py:126-127)، پس دو
     شاخهٔ critical/high در `protective_override` روی مسیرِ زنده مرده‌اند.

  ۳) متغیرِ تنظیم‌شوندهٔ قلب (velocity) روی سقفِ beat قفل است: در کلِ دامنهٔ
     عملگر [۳۰s..۹۰۰s] مقدارش دقیقاً ۰.۱۲۵ می‌ماند → بهرهٔ حلقه صفر.

**۲۰۲۶-۰۸-۱۱ (Integration Wave, رأی مالک):** این تست به ADR-034 هم‌راستا شد.
پیش از ADR-034، `protective_override` در pain بالا `override=True` /
`action=protective_halt` برمی‌گرداند. ADR-034 این مسیر را به proposal-only
تنزل داد: `override=False`، `executable=False`، `action=protective_proposal` /
`throttle_proposal`. halt اجرایی فقط از `request_protective_halt` + PolicyGate.
علومِ کالیبراسیون (هیستوگرام، پاکتِ سالم، قیود، سقف، partner_stress) دست‌نخورده‌اند؛
فقط assertionهای halt به assertionهای proposal-only تغییر کردند.

$0 آفلاین. هیچ لمسِ state واقعی: همهٔ اعداد frozen sample هستند.
"""
import os
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent))
sys.path.insert(0, str(_HERE.parent / "budget"))
import harness                                   # noqa: E402
ENV = harness.setup("pain-calibration")          # ایزولاسیون — قبل از هر importِ دیگر
os.environ["OCTOPUS_NEURAL_LEARNED_APPLY"] = "0"  # ADR-034 path under test; ADR-035 has its own suite

import wiring                                    # noqa: E402
from neural import nociceptor as noci            # noqa: E402
from neural.neural_driver import NeuralDriver    # noqa: E402
from neural.reflex import ReflexArc              # noqa: E402
from heart import control_law                    # noqa: E402

CAL = "OCTOPUS_PAIN_THRESHOLD_CALIBRATED"
SEV = "OCTOPUS_REFLEX_SEVERITY_RECOVER"


class _Flag:
    """ست/ریستِ امنِ فلگ — هیچ فلگی بعد از تست باقی نمی‌ماند."""

    def __init__(self, name, value="1"):
        self.name, self.value, self.old = name, value, None

    def __enter__(self):
        self.old = os.environ.get(self.name)
        os.environ[self.name] = self.value
        return self

    def __exit__(self, *a):
        if self.old is None:
            os.environ.pop(self.name, None)
        else:
            os.environ[self.name] = self.old
        return False


# ── نمونهٔ منجمدِ توزیعِ زنده ────────────────────────────────────────────────────
# استخراج‌شده از ۲۲۱۴ سطرِ `_ops/state/neural/effect-shadow.jsonl`
# (۲۰۲۶-۰۷-۲۷T۱۶:۰۴:۳۵ → ۲۰۲۶-۰۷-۲۸T۲۱:۴۰:۰۸). {مقدارِ درد: شمار}
RECORDED_PAIN_HISTOGRAM = {
    0.102: 28, 0.105: 130, 0.107: 54, 0.110: 42, 0.115: 4, 0.117: 99,
    0.120: 9, 0.122: 16, 0.125: 1629, 0.128: 2, 0.130: 101, 0.150: 100,
}
# بلوکِ velocityِ زنده، منجمد از `state/pulse/heart-signals-latest.json`
# (۲۰۲۶-۰۷-۲۸T۲۱:۳۸). فقط ستون‌های لازمِ تحلیلِ اشباع.
RECORDED_VELOCITY_BLOCK = {
    "velocity_per_hr": 0.125,
    "window_hours": 24.0,
    "components": {"confirmed": 0, "effects": 0, "consolidation": 3,
                   "beats": 1318, "cognition": None},
    "real_components": {"fuel_calls": None, "fuel_musd": None},
    "honest_pulse": {"enabled": True, "beat_cap": 3.0, "capped_beat_units": 3.0},
    "metronome_share": 0.9777,
}


def _neural(pain, reflexes=None):
    return {"pain": {"level": pain}, "reflexes": reflexes or [], "brain_inputs": {}}


# ═══ ۱ · توزیع و کالیبراسیون ═════════════════════════════════════════════════

def t_histogram_matches_recorded_total():
    """نمونهٔ منجمد باید همان ۲۲۱۴ تیک باشد (اگر کسی عدد را دست‌کاری کرد، قرمز)."""
    n = sum(RECORDED_PAIN_HISTOGRAM.values())
    assert n == 2214, f"شمارِ تیک‌ها {n} ≠ ۲۲۱۴"
    assert max(RECORDED_PAIN_HISTOGRAM) == noci.HEALTHY_ENVELOPE["max"] == 0.150
    assert min(RECORDED_PAIN_HISTOGRAM) == noci.HEALTHY_ENVELOPE["min"] == 0.102


def t_legacy_threshold_unreachable_on_recorded_data():
    """یافتهٔ اصلی: روی ۲۲۱۴/۲۲۱۴ تیکِ ضبط‌شده، آستانهٔ ۰.۷۰ صفر بار باز می‌شود."""
    fired = sum(n for p, n in RECORDED_PAIN_HISTOGRAM.items()
                if wiring.protective_override(_neural(p))["override"])
    assert fired == 0, f"انتظار صفر شلیک با آستانهٔ تاریخی، ولی {fired}"


def t_calibrated_threshold_zero_false_halt_on_recorded_data():
    """قیدِ C1: آستانهٔ کالیبره هم روی رژیمِ سالمِ ضبط‌شده صفر halt می‌دهد.

    این تستِ ایمنیِ اصلی است: اگر کسی آستانه را زیرِ پاکتِ سالم (بیشینه ۰.۱۵۰)
    بیاورد، ارگانیسم دائم halt می‌شود و همین‌جا قرمز می‌شود."""
    with _Flag(CAL):
        fired = sum(n for p, n in RECORDED_PAIN_HISTOGRAM.items()
                    if wiring.protective_override(_neural(p))["override"])
    assert fired == 0, f"آستانهٔ کالیبره {fired} halt کاذب روی دادهٔ سالم داد"
    assert noci.PROTECTIVE_THRESHOLD_CALIBRATED > max(RECORDED_PAIN_HISTOGRAM), \
        "آستانه باید بالای بیشینهٔ مشاهده‌شده باشد"


def t_calibration_constraints_hold():
    """هر سه قیدِ داده‌محور (C1/C2/C3) روی مقدارِ انتخاب‌شده برقرارند."""
    th = noci.PROTECTIVE_THRESHOLD_CALIBRATED
    env = noci.HEALTHY_ENVELOPE
    assert th > env["max"] + 3 * env["sd"], "C1: باید بالای پاکتِ سالم + ۳σ باشد"
    assert th < env["structural_single_fault_max"], \
        "C2: باید زیرِ بزرگ‌ترین نقصِ ساختاریِ تک‌عاملی (RED=۰.۴۰) باشد"
    assert th > env["noisy_channel_ceiling"], \
        "C3: باید بالای سقفِ کانالِ نویزیِ error_rate (۰.۲۵) باشد"
    # فاصله بر حسبِ انحرافِ معیارِ رژیمِ سالم
    sigmas = (th - env["mean"]) / env["sd"]
    assert sigmas > 20, f"فاصلهٔ {sigmas:.1f}σ کافی نیست"


def t_calibrated_never_less_protective():
    """ناوردیِ ایمنیِ ADR-034: نه legacy نه کالیبره halt اجرایی می‌سازند.

    پیش از ADR-034 این تست می‌سنجید که «کالیبره کم‌محافظ‌تر از legacy نیست»
    (ابرمجموعه). اکنون هر دو مسیر proposal-only‌اند (`override=False`,
    `executable=False`)، پس ناوردیِ واقعی که باید قفل شود این است: **هیچ
    سطحِ دردی halt اجرایی تولید نمی‌کند**، و کالیبره همچنان حداقل همین
   Proposal سطحِ هشدار را در هر جایی legacy هشدار می‌دهد نگه می‌دارد."""
    for i in range(0, 1001):
        p = i / 1000.0
        legacy = wiring.protective_override(_neural(p))
        with _Flag(CAL):
            cal = wiring.protective_override(_neural(p))
        # ADR-034: هر دو همیشه non-executable
        assert legacy["override"] is False and cal["override"] is False
        assert legacy["executable"] is False and cal["executable"] is False
        # کالیبره کم‌محافظ‌تر نیست: اگر legacy proposal می‌دهد، cal هم می‌دهد
        if legacy["action"] != "none":
            assert cal["action"] != "none", f"pain={p} legacy هشدار داد ولی cal نه"


# ═══ ۲ · شلیکِ واقعی با ورودیِ واقع‌گرایانه (معیارِ پذیرش) ═══════════════════════

def t_calibrated_fires_on_realistic_emergency():
    """ورودیِ واقع‌گرایانه از مسیرِ کاملِ تولید → protective_proposal (نه halt).

    ADR-034: pain=۰.۵۵ بالای آستانهٔ کالیبره (۰.۳۵) است، پس سیستم یک
    protective_proposal / SHADOW_ALERT تولید می‌کند — ولی `override=False`،
    `executable=False`. halt اجرایی فقط از request_protective_halt + PolicyGate."""
    r = NeuralDriver().evaluate(
        beat=1,
        rhythm={"mode_color": "RED"},
        sensory={"error_rate": 0.6, "afferent_ratio": 1.0},
        spectral={"sigma": 0.0},
        budget={"pct": 0.00072})
    assert abs(r["pain"]["level"] - 0.55) < 1e-9, r["pain"]

    off = wiring.protective_override(r)
    assert off["action"] == "none", "بدون CAL: pain=0.55 زیرِ آستانهٔ legacy 0.7"

    with _Flag(CAL):
        on = wiring.protective_override(r)
    assert on["action"] == "protective_proposal", on
    assert on["override"] is False, "ADR-034: override همیشه False"
    assert on["executable"] is False, "ADR-034: halt اجرایی نیست"
    assert on["shadow_alert"] is True, "باید SHADOW_ALERT باشد"
    assert "pain=0.55" in on["reason"], on["reason"]


def t_legacy_silent_on_worst_two_fault_crisis():
    """بدترین ترکیبِ دو-نقصی (RED + خطای ۱۰۰٪) → pain=۰.۶۵.

    ADR-034: legacy (آستانه ۰.۷) هنوز صفر proposal می‌دهد (۰.۶۵<۰.۷)؛
    کالیبره (۰.۳۵) آن را به‌عنوان protective_proposal کشف می‌کند — نه halt."""
    r = NeuralDriver().evaluate(beat=1, rhythm={"mode_color": "RED"},
                                sensory={"error_rate": 1.0, "afferent_ratio": 1.0},
                                spectral={"sigma": 0.0}, budget={"pct": 0.00072})
    assert abs(r["pain"]["level"] - 0.65) < 1e-9, r["pain"]
    assert wiring.protective_override(r)["action"] == "none", "legacy: 0.65<0.7"
    with _Flag(CAL):
        cal = wiring.protective_override(r)
    assert cal["action"] == "protective_proposal"
    assert cal["executable"] is False and cal["override"] is False


def t_attainable_ceiling_as_wired():
    """سقفِ دست‌یافتنیِ درد با سیم‌کشیِ امروز ۰.۷۱ است — ۰.۰۱ بالای آستانه.

    یعنی ترمزِ فعلی فقط در ۱.۴٪ بالای دامنهٔ ممکن باز می‌شود و به هم‌زمانیِ
    *سه* نقصِ حداکثری گره خورده. با حذفِ هر یک از سه، دوباره خاموش می‌شود."""
    n = noci.Nociceptor()
    worst = n.measure(budget_pct=0.00072, error_rate=1.0, freeze_active=True,
                      partner_stress=0.0, afferent_ratio=0.0, sigma=0.0)
    assert abs(worst.pain_level - 0.71) < 1e-9, worst.pain_level
    assert worst.protective_mode is True
    assert worst.pain_level == noci.HEALTHY_ENVELOPE["attainable_max_as_wired"]
    # حاشیه چقدر تنگ است: با RED **و** کوریِ کاملِ حسی، خطا هم باید ≳۰.۹۶ باشد
    # (۰.۲۵e + ۰.۴ + ۰.۰۶ > ۰.۷ ⇔ e > ۰.۹۶) — تضعیفِ هر کدام از سه، ترمز را می‌بندد.
    for kw in ({"error_rate": 0.95}, {"freeze_active": False}, {"afferent_ratio": 0.1}):
        base = dict(budget_pct=0.00072, error_rate=1.0, freeze_active=True,
                    partner_stress=0.0, afferent_ratio=0.0, sigma=0.0)
        base.update(kw)
        assert n.measure(**base).protective_mode is False, \
            f"با تضعیفِ {kw} نباید هنوز شلیک کند"


def t_partner_stress_is_never_passed_by_production():
    """گاردِ ادعا: هیچ فراخوانِ تولیدی `partner_stress` را به لایهٔ عصبی نمی‌دهد.

    منبعِ حقیقت متنِ خودِ فراخوان‌هاست — نه یادِ آدم. اگر روزی وصل شد، این تست
    قرمز می‌شود و کالیبراسیون باید بازبینی شود (یک ورودیِ صفر، زنده شده)."""
    for name in ("organism.py", "brain_worker.py"):
        src = (_HERE.parent / name).read_text("utf-8")
        i = src.find("neural_beat(")
        assert i > 0, f"{name}: فراخوانِ neural_beat پیدا نشد"
        call = src[i:i + 1800]
        assert "partner_stress" not in call, \
            f"{name}: partner_stress حالا پاس داده می‌شود — کالیبراسیون را بازبین کن"


# ═══ ۳ · byte-identical بودنِ حالتِ خاموش ════════════════════════════════════════

def t_flag_off_is_byte_identical():
    """با فلگِ خاموش، خروجی ADR-034 proposal-only است: override/executable همیشه False.

    trace_id پویا است، پس فقط کلیدهای پایدار را مقایسه می‌کنیم."""
    def _stable(d):
        return {k: d[k] for k in ("override", "action", "reason",
                                  "suppressible", "executable", "shadow_alert")}
    r_none = wiring.protective_override(None)
    assert r_none["action"] == "none" and r_none["reason"] == "no neural data"
    assert r_none["override"] is False and r_none["executable"] is False
    assert _stable(wiring.protective_override(_neural(0.1))) == {
        "override": False, "action": "none", "reason": "all clear",
        "suppressible": True, "executable": False, "shadow_alert": False}
    # pain بالا → protective_proposal (نه halt)
    r85 = wiring.protective_override(_neural(0.85))
    assert r85["action"] == "protective_proposal"
    assert r85["override"] is False and r85["executable"] is False
    assert r85["shadow_alert"] is True
    # critical reflex → throttle_proposal (نه throttle-halt)
    rc = wiring.protective_override(_neural(0.5, [
        {"name": "sigma-throttle", "triggered": True, "severity": "critical"}]))
    assert rc["action"] == "throttle_proposal"
    assert rc["override"] is False and rc["executable"] is False
    assert rc["shadow_alert"] is True
    # high reflex → warn
    rh = wiring.protective_override(_neural(0.2, [
        {"name": "budget-slow", "triggered": True, "severity": "high"}]))
    assert rh["action"] == "warn"
    assert rh["override"] is False and rh["shadow_alert"] is False


# ═══ ۴ · severityِ گم‌شده در تصویرِ تولید ═════════════════════════════════════════

def t_production_projection_drops_severity():
    """اندازه‌گیری: خروجیِ زندهٔ NeuralDriver اصلاً کلیدِ severity ندارد."""
    r = NeuralDriver().evaluate(beat=1, rhythm={"mode_color": "RED"},
                                sensory={"error_rate": 1.0, "afferent_ratio": 0.0},
                                spectral={"sigma": 2.0}, budget={"pct": 0.95})
    trig = [x for x in r["reflexes"] if x.get("triggered")]
    assert len(trig) == 5, f"انتظار ۵ رفلکسِ شلیک‌شده: {trig}"
    assert all("severity" not in x for x in trig), \
        f"severity باید غایب باشد (وگرنه این یافته کهنه است): {trig}"


def t_critical_branch_dead_without_recovery():
    """شاخهٔ critical روی رکوردِ *تولیدی* (بدونِ severity) باز نمی‌شود.

    با SEV (severity recover): critical → throttle_proposal (ADR-034: نه throttle-halt)."""
    prod_reflex = [{"name": "sigma-throttle", "triggered": True, "action": "throttle"}]
    off = wiring.protective_override(_neural(0.1, prod_reflex))
    assert off["action"] == "none", off
    with _Flag(SEV):
        on = wiring.protective_override(_neural(0.1, prod_reflex))
    assert on["action"] == "throttle_proposal", on
    assert on["override"] is False and on["executable"] is False
    assert on["shadow_alert"] is True


def t_high_branch_dead_without_recovery():
    """همین برای شاخهٔ high (warn) — با SEV: high → warn (نه halt)."""
    prod_reflex = [{"name": "red-pause", "triggered": True, "action": "pause"}]
    assert wiring.protective_override(_neural(0.1, prod_reflex))["action"] == "none"
    with _Flag(SEV):
        r = wiring.protective_override(_neural(0.1, prod_reflex))
    assert r["action"] == "warn" and r["override"] is False
    assert r["executable"] is False and r["shadow_alert"] is False


def t_severity_map_matches_reflex_module():
    """گاردِ drift: نقشهٔ نام→severity باید با خودِ reflex.py یکی باشد.

    نقشه را با ساختنِ *واقعیِ* هر رفلکس می‌سنجیم، نه با خواندنِ متن."""
    arc = ReflexArc()
    produced = {}
    for snap in (
        {"spectral": {"sigma": 2.0}},
        {"budget": {"pct": 0.95}},
        {"sensory": {"afferent_ratio": 0.0}},
        {"rhythm": {"mode_color": "RED"}},
        {"pain_level": 0.9},
        {},                       # هیچ خطری → all-clear
    ):
        for a in arc.evaluate(snap):
            produced[a.name] = a.severity
    assert produced, "هیچ رفلکسی تولید نشد"
    for name, sev in produced.items():
        assert wiring._REFLEX_SEVERITY.get(name) == sev, \
            f"drift: reflex.py می‌گوید {name}={sev} ولی نقشهٔ wiring می‌گوید " \
            f"{wiring._REFLEX_SEVERITY.get(name)}"
    missing = set(wiring._REFLEX_SEVERITY) - set(produced)
    assert not missing, f"نام‌های اضافی در نقشه که reflex.py نمی‌سازد: {missing}"


# ═══ ۵ · اشباعِ plant در قلب (بهرهٔ حلقه = صفر) ══════════════════════════════════

def t_velocity_plant_is_saturated_across_actuation_range():
    """velocity در کلِ دامنهٔ عملگر ثابت است → حلقه هیچ پهنای‌باندی ندارد."""
    s = control_law.plant_saturation(RECORDED_VELOCITY_BLOCK)
    assert s["saturated"] is True, s
    assert s["loop_gain"] == 0.0, s
    assert abs(s["velocity_locked_at"] - 0.125) < 1e-9, s
    assert s["velocity_locked_at"] == RECORDED_VELOCITY_BLOCK["velocity_per_hr"], \
        "مقدارِ محاسبه‌شده باید دقیقاً همان velocityِ ثبت‌شده باشد"
    # حتی در کندترین ضربانِ مجاز (MAX_S) هم واحدهای beat از سقف بیشترند
    assert s["beat_units_at_slowest_period"] >= s["beat_cap"], s
    assert s["beats_at_slowest_period"] == 96.0, s     # ۲۴س ÷ ۹۰۰s


def t_plant_desaturates_when_actuator_could_matter():
    """ضدنمونه: اگر پنجره/سقف طوری باشد که عملگر اثر کند، saturated=False."""
    blk = dict(RECORDED_VELOCITY_BLOCK)
    blk["honest_pulse"] = {"enabled": True, "beat_cap": 50.0}
    s = control_law.plant_saturation(blk)
    assert s["saturated"] is False and s["loop_gain"] is None, s
    # و با سوختِ واقعی (کانالِ غیرِ متronome) هم دیگر ثابت نیست
    blk2 = dict(RECORDED_VELOCITY_BLOCK)
    blk2["real_components"] = {"fuel_calls": 40}
    assert control_law.plant_saturation(blk2)["saturated"] is False


def t_plant_saturation_honest_off_is_not_claimed():
    """اگر honest-pulse خاموش باشد، این تحلیل ادعایی نمی‌کند (fail-quiet)."""
    blk = dict(RECORDED_VELOCITY_BLOCK)
    blk["honest_pulse"] = {"enabled": False, "beat_cap": 3.0}
    s = control_law.plant_saturation(blk)
    assert s["saturated"] is False and s["loop_gain"] is None
    assert control_law.plant_saturation(None)["saturated"] is False


def t_beat_weight_mirror_matches_producers():
    """گاردِ drift: وزنِ beat در این تحلیل باید با producers.velocity_meter یکی باشد."""
    src = (_HERE.parent / "heart" / "producers.py").read_text("utf-8")
    assert '"beats": 0.1' in src, "وزنِ beat در producers عوض شده — آینه را به‌روز کن"
    assert control_law._BEAT_UNIT_WEIGHT == 0.1


def t_saturation_telemetry_is_flag_gated():
    """کلیدِ تله‌متری فقط با فلگ نوشته می‌شود (پیش‌فرض: هیچ تغییری در state)."""
    src = (_HERE.parent / "heart" / "control_law.py").read_text("utf-8")
    i = src.find('gates["plant_saturation"]')
    assert i > 0, "تله‌متری باید وجود داشته باشد"
    assert 'OCTOPUS_HEART_SATURATION_TELEMETRY' in src[max(0, i - 400):i], \
        "نوشتنِ تله‌متری باید پشتِ فلگ باشد"


if __name__ == "__main__":
    failed = harness.run([
        ("توزیعِ منجمد = ۲۲۱۴ تیکِ ضبط‌شده", t_histogram_matches_recorded_total),
        ("آستانهٔ ۰.۷۰ روی ۲۲۱۴/۲۲۱۴ تیک غیرقابلِ‌رسیدن است",
         t_legacy_threshold_unreachable_on_recorded_data),
        ("آستانهٔ کالیبره: صفر halt کاذب روی دادهٔ سالم",
         t_calibrated_threshold_zero_false_halt_on_recorded_data),
        ("قیدهای C1/C2/C3 کالیبراسیون برقرارند", t_calibration_constraints_hold),
        ("ناوردی: کالیبره هرگز کم‌محافظ‌تر نیست", t_calibrated_never_less_protective),
        ("[پذیرش] بحرانِ واقع‌گرایانه ترمز را باز می‌کند",
         t_calibrated_fires_on_realistic_emergency),
        ("بدترین بحرانِ دو-نقصی امروز بی‌صداست", t_legacy_silent_on_worst_two_fault_crisis),
        ("سقفِ دست‌یافتنیِ درد با سیم‌کشیِ امروز ۰.۷۱", t_attainable_ceiling_as_wired),
        ("partner_stress هنوز از تولید پاس داده نمی‌شود",
         t_partner_stress_is_never_passed_by_production),
        ("فلگ خاموش = بایت‌به‌بایتِ امروز", t_flag_off_is_byte_identical),
        ("تصویرِ تولید severity را می‌اندازد", t_production_projection_drops_severity),
        ("شاخهٔ critical بدونِ بازیابی مرده است", t_critical_branch_dead_without_recovery),
        ("شاخهٔ high بدونِ بازیابی مرده است", t_high_branch_dead_without_recovery),
        ("نقشهٔ severity با reflex.py drift ندارد", t_severity_map_matches_reflex_module),
        ("velocity در کلِ دامنهٔ عملگر ثابت است (بهره صفر)",
         t_velocity_plant_is_saturated_across_actuation_range),
        ("ضدنمونهٔ اشباع", t_plant_desaturates_when_actuator_could_matter),
        ("honest-pulse خاموش → ادعایی نمی‌کند", t_plant_saturation_honest_off_is_not_claimed),
        ("وزنِ beat با producers drift ندارد", t_beat_weight_mirror_matches_producers),
        ("تله‌متریِ اشباع پشتِ فلگ است", t_saturation_telemetry_is_flag_gated),
    ])
    sys.exit(1 if failed else 0)
