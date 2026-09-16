#!/usr/bin/env python3
"""test_pain_input_census.py — WS-2: fusionِ شش‌ترمی که پنج ترمش صفر است.

یافتهٔ اندازه‌گیری‌شده که این فایل قفلش می‌کند (۲۰۲۶-۰۸-۰۱، روی
`_ops/state/neural/effect-shadow.jsonl` — ۸۵۱۱ ردیف، ۰۷-۲۷T۱۶:۰۴:۳۵ →
۰۸-۰۱T۱۰:۲۵:۱۸، فایلِ زنده):

  · ۴۵ مقدارِ یکتای درد، بازهٔ [۰.۰۴۳ ، ۰.۱۵۲]، protective=false روی ۸۵۱۱/۸۵۱۱
  · هر ۴۵ مقدار دقیقاً `۰.۲۵ × error_rate` → پنج ترمِ دیگر صفرِ **دقیق**
  · شاهدِ مستقلِ هم‌زمان: cortex/stress-latest.json:organism_stress=۰.۴۱ (۱۰:۲۶)
    و تازه‌ترین ردیفِ سایه pain=۰.۱۰۲ = round(۰.۲۵×۰.۴۱, ۳)

و **علتِ ساختاریِ اینکه این کشف ۸۵۱۱ ردیف بازسازیِ آفلاین لازم داشت**:
`PainSignal.contributors` دو کلید (`freeze`, `sigma`) را وقتی ترمشان خاموش است
اصلاً نمی‌سازد، و `neural_driver.evaluate` هم `contributors` را برنمی‌گرداند.
پس نه در حافظه و نه در لاگ، «صفر بود» از «اندازه‌گیری نشد» جدا نبود.

$0 آفلاین. صفر لمسِ stateِ واقعی — همهٔ اعداد frozen sample‌اند.
⚠️ این فایل آستانهٔ درد را نه می‌خواند نه تغییر می‌دهد. مسیرِ ترمز دست‌نخورده.
"""
import os
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent))
sys.path.insert(0, str(_HERE.parent / "budget"))
import harness                                     # noqa: E402
ENV = harness.setup("pain-input-census")           # ایزولاسیون — قبل از هر importِ دیگر

import wiring                                      # noqa: E402
from neural import nociceptor as noci              # noqa: E402
from neural.neural_driver import (NeuralDriver,    # noqa: E402
                                  PAIN_BREAKDOWN_FLAG, breakdown_enabled)

BD = PAIN_BREAKDOWN_FLAG


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


# ── payloadِ **دقیقاً** تولیدی ─────────────────────────────────────────────────
# آینهٔ organism.py:616-637. عمداً `partner_stress` ندارد — چون تولید هم ندارد.
# اعداد = مقادیرِ زندهٔ خوانده‌شده در ۲۰۲۶-۰۸-۰۱T۱۰:۲۶.
LIVE_ERROR_RATE = 0.41        # cortex/stress-latest.json:organism_stress
LIVE_PAIN = 0.102             # تازه‌ترین ردیفِ effect-shadow.jsonl (beat 21015)
LIVE_BUDGET_PCT = 0.0         # ۰۸-۰۱ ماه چرخید؛ بیشینهٔ ژوئیه ۰.۰۰۰۷۲
LIVE_SIGMA = 0.0              # replication-latest.json: spawn_approved/parents = 0/1
LIVE_AFFERENT = 1.0           # organism.py:489 پیش‌فرض؛ afferent_beat هر ۱۴۴۰ ضربان


def _production_payload(error_rate=LIVE_ERROR_RATE):
    return dict(
        rhythm={"mode_color": "AMBER", "readiness": 0.7, "mode_focus": "STEADY"},
        budget={"pct": LIVE_BUDGET_PCT},
        spectral={"sigma": LIVE_SIGMA, "sigma_is_replication_ratio": True,
                  "sigma_source": "replication-latest.json"},
        sensory={"afferent_ratio": LIVE_AFFERENT, "error_rate": error_rate},
    )


# ── بازسازیِ رفتارِ پیش‌از-اصلاح (دندانِ تست) ──────────────────────────────────
def _census_the_old_way(contributors: dict) -> set:
    """تنها سرشماری‌ای که **قبل از** این تغییر ممکن بود: از `contributors`.
    این تابع عمداً باگِ قدیمی را بازتولید می‌کند تا نشان دهد چرا کور بود."""
    return set(contributors)


def t_old_contributors_cannot_see_two_of_six():
    """دندان: با payloadِ تولیدی، `contributors` فقط ۴ کلید از ۶ دارد.
    `freeze` و `sigma` **غایب**‌اند — یعنی از روی این dict نمی‌شود گفت صفر بودند
    یا اصلاً اندازه گرفته نشدند. این همان نقصی است که این WS می‌بندد."""
    p = _production_payload()
    sig = noci.Nociceptor().measure(
        budget_pct=p["budget"]["pct"], error_rate=p["sensory"]["error_rate"],
        freeze_active=(p["rhythm"]["mode_color"] == "RED"),
        afferent_ratio=p["sensory"]["afferent_ratio"], sigma=p["spectral"]["sigma"])
    old = _census_the_old_way(sig.contributors)
    assert len(old) == 4, f"انتظار ۴ کلیدِ قدیمی، دیدم {len(old)}: {sorted(old)}"
    assert "freeze" not in old and "sigma" not in old, \
        "اگر این دو حالا حاضرند، نقصِ قدیمی رفع شده — این تست را بازبین کن"
    # و با اصلاح: هر شش ترم حاضر
    sig2 = noci.Nociceptor().measure(
        budget_pct=p["budget"]["pct"], error_rate=p["sensory"]["error_rate"],
        freeze_active=False, afferent_ratio=p["sensory"]["afferent_ratio"],
        sigma=p["spectral"]["sigma"], breakdown=True)
    assert set(sig2.contributions) == set(noci.PAIN_INPUTS), \
        f"تفکیک باید هر شش ترم را داشته باشد، دیدم {sorted(sig2.contributions)}"


def t_five_of_six_are_exactly_zero_on_production_payload():
    """سنجهٔ مرکزیِ WS-2: با payloadِ تولیدی، دقیقاً پنج ترم صفرِ **دقیق** است."""
    p = _production_payload()
    r = NeuralDriver()
    with _Flag(BD):
        out = r.evaluate(beat=1, **p)
    c = out["pain"]["contributions"]
    zero = set(out["pain"]["zero_terms"])
    assert zero == {"budget", "freeze", "partner_stress", "afferent_deficit", "sigma"}, \
        f"مجموعهٔ ترم‌های صفر عوض شده: {sorted(zero)}"
    assert len(zero) == 5 and c["errors"] > 0, "باید دقیقاً ۵ صفر و errors تنها زنده باشد"
    for k in zero:
        assert c[k] == 0.0, f"{k} باید صفرِ دقیق باشد، دیدم {c[k]}"


def t_pain_equals_quarter_of_error_rate_on_live_numbers():
    """پینِ عددیِ زنده: organism_stress=۰.۴۱ → درد ۰.۱۰۲، همان که سایه ثبت کرد."""
    out = NeuralDriver().evaluate(beat=1, **_production_payload())
    assert out["pain"]["level"] == LIVE_PAIN, \
        f"انتظار {LIVE_PAIN}، دیدم {out['pain']['level']}"
    assert round(0.25 * LIVE_ERROR_RATE, 3) == LIVE_PAIN


def t_contributions_conserve_pain():
    """ناوردیِ بقا (دندانِ ضدِ رگرسیون): جمعِ تفکیک = خودِ درد.
    اگر کسی ثبتِ یکی از شش ترم را بیندازد یا وزنی را عوض کند، این می‌شکند —
    حتی اگر آن ترم امروز صفر باشد، چون حالتِ غیرصفرش هم آزموده می‌شود."""
    cases = [
        dict(budget_pct=0.0, error_rate=0.41, freeze_active=False,
             partner_stress=0.0, afferent_ratio=1.0, sigma=0.0),      # امروز
        dict(budget_pct=0.95, error_rate=0.6, freeze_active=True,
             partner_stress=0.7, afferent_ratio=0.05, sigma=0.9),     # هر شش زنده
        dict(budget_pct=0.85, error_rate=0.0, freeze_active=False,
             partner_stress=0.0, afferent_ratio=0.19, sigma=0.81),    # لبهٔ گیت‌ها
    ]
    n = noci.Nociceptor()
    for kw in cases:
        s = n.measure(breakdown=True, **kw)
        total = min(1.0, sum(s.contributions.values()))
        assert round(total, 3) == s.pain_level, \
            f"بقا شکست: جمعِ تفکیک {round(total,3)} ≠ درد {s.pain_level} برای {kw}"


def t_weights_mirror_does_not_drift():
    """PAIN_WEIGHTS آینهٔ `measure` است — با تک‌تحریکِ هر ترم راستی‌آزمایی می‌شود."""
    n = noci.Nociceptor()
    # هر ترم را تنها و در حالتِ اشباع تحریک کن، سهمش باید = وزنش باشد
    probes = {
        "budget": dict(budget_pct=1.0, afferent_ratio=1.0),            # bp=0.6→0.18
        "errors": dict(error_rate=1.0, afferent_ratio=1.0),
        "freeze": dict(freeze_active=True, afferent_ratio=1.0),
        "partner_stress": dict(partner_stress=1.0, afferent_ratio=1.0),
        "afferent_deficit": dict(afferent_ratio=0.0),                  # deficit=0.6→0.06
        "sigma": dict(sigma=1.0, afferent_ratio=1.0),
    }
    saturating = {"errors", "freeze", "partner_stress", "sigma"}
    for term, kw in probes.items():
        s = n.measure(breakdown=True, **kw)
        others = {k: v for k, v in s.contributions.items() if k != term}
        assert all(v == 0.0 for v in others.values()), \
            f"probeِ {term} ترمِ دیگری را هم روشن کرد: {others}"
        if term in saturating:
            assert round(s.contributions[term], 6) == noci.PAIN_WEIGHTS[term], \
                f"وزنِ {term} drift کرد: {s.contributions[term]} ≠ {noci.PAIN_WEIGHTS[term]}"
        else:
            assert s.contributions[term] > 0.0, f"{term} باید غیرصفر شود"


def t_flag_off_is_byte_identical():
    """با فلگ خاموش: dictِ pain دقیقاً دو کلید دارد و PainSignal دست‌نخورده است."""
    os.environ.pop(BD, None)
    assert breakdown_enabled() is False, "غیاب باید خاموش باشد (این نام در PAPER_FULL_FLAGS نیست)"
    out = NeuralDriver().evaluate(beat=1, **_production_payload())
    assert set(out["pain"]) == {"level", "protective"}, \
        f"فلگ خاموش نباید کلیدِ تازه بدهد: {sorted(out['pain'])}"
    s = noci.Nociceptor().measure(error_rate=0.41)
    assert s.contributions is None and s.zero_terms == ()
    # حتی == و repr هم باید یکسان بمانند (compare=False, repr=False)
    s2 = noci.Nociceptor().measure(error_rate=0.41, breakdown=True)
    assert s == s2, "فیلدهای تازه نباید در == شرکت کنند"
    assert "contributions" not in repr(s2), "فیلدهای تازه نباید در repr بیایند"


def t_breakdown_never_changes_the_brake():
    """گاردِ ایمنی: breakdown نه درد را عوض می‌کند نه protective را — روی هر دو
    حالتِ فلگ و روی نمونه‌ای که از آستانه هم رد می‌شود."""
    n = noci.Nociceptor()
    for kw in [dict(error_rate=0.41),
               dict(error_rate=1.0, freeze_active=True, afferent_ratio=0.0,
                    partner_stress=1.0, budget_pct=1.0, sigma=1.0)]:
        a = n.measure(**kw)
        b = n.measure(breakdown=True, **kw)
        assert a.pain_level == b.pain_level, f"درد عوض شد: {a.pain_level} ≠ {b.pain_level}"
        assert a.protective_mode == b.protective_mode
        assert a.contributors == b.contributors and a.detail == b.detail


def t_partner_stress_has_no_producer_in_the_contract():
    """تریپ‌وایر: قراردادِ payloadِ تولید هنوز `partner_stress` ندارد.
    اگر روزی اضافه شد، این قرمز می‌شود و INPUT_CENSUS باید بازبینی شود —
    چون تنها هم‌نامِ موجود، خروجیِ `pain*0.8` است و وصلش حلقهٔ بازخوردِ مثبت
    روی مسیرِ ترمز می‌سازد."""
    sens = wiring.NEURAL_PAYLOAD_CONTRACT.get("sensory", {})
    assert "partner_stress" not in sens, \
        "partner_stress حالا در قرارداد هست — بازخوردِ pain→partner_stress→pain را بررسی کن"
    assert set(sens) == {"afferent_ratio", "error_rate"}, \
        f"شکلِ sensory عوض شد: {sorted(sens)} — سرشماری را به‌روز کن"
    # و همان هم‌نامِ خطرناک هنوز از درد مشتق می‌شود:
    bi = NeuralDriver().snapshot_to_brain_inputs({"pain_level": 0.5})
    assert bi["partner_stress"] == 0.4, \
        "partner_stressِ خروجی دیگر pain*0.8 نیست — استدلالِ حلقهٔ بازخورد را بازبین کن"


def t_census_covers_every_term_and_matches_measurement():
    """INPUT_CENSUS دقیقاً همان شش ترم را پوشش می‌دهد و هر ردیفش کامل است."""
    assert set(noci.INPUT_CENSUS) == set(noci.PAIN_INPUTS)
    assert set(noci.PAIN_WEIGHTS) == set(noci.PAIN_INPUTS)
    for term, row in noci.INPUT_CENSUS.items():
        # ⚠️ `row.get(k)` اینجا غلط است: `observed_max=0.0` صادقانه صفر است ولی
        # falsy — دقیقاً همان اشتباهی که «صفر» را با «غایب» یکی می‌کند و کلِ این
        # WS دربارهٔ آن است. پس حضورِ کلید و نوع را جدا می‌سنجیم.
        for k in ("source", "gate", "why_zero", "verdict"):
            assert isinstance(row.get(k), str) and row[k].strip(), \
                f"{term}: فیلدِ {k} خالی است"
        assert "observed_max" in row and isinstance(row["observed_max"], float), \
            f"{term}: observed_max باید عددِ اعشاری و حاضر باشد (حتی وقتی ۰.۰)"
    # تنها ترمی که بیشینهٔ مشاهده‌شده‌اش غیرصفر است باید `errors` باشد
    nonzero = {t for t, r in noci.INPUT_CENSUS.items() if r["observed_max"] > 0}
    assert nonzero == {"errors", "budget"}, f"بیشینه‌های غیرصفر: {sorted(nonzero)}"
    # و budget بیشینه‌اش سه مرتبه زیرِ گیتِ ۰.۸ است
    assert noci.INPUT_CENSUS["budget"]["observed_max"] < 0.8 / 1000


if __name__ == "__main__":
    failed = harness.run([
        ("دندان: contributorsِ قدیمی ۲ ترم از ۶ را نمی‌بیند",
         t_old_contributors_cannot_see_two_of_six),
        ("۵ از ۶ ترم روی payloadِ تولیدی صفرِ دقیق‌اند",
         t_five_of_six_are_exactly_zero_on_production_payload),
        ("پینِ زنده: درد = ۰.۲۵ × error_rate",
         t_pain_equals_quarter_of_error_rate_on_live_numbers),
        ("ناوردیِ بقا: جمعِ تفکیک = درد", t_contributions_conserve_pain),
        ("آینهٔ وزن‌ها drift ندارد", t_weights_mirror_does_not_drift),
        ("فلگ خاموش = بایت‌به‌بایتِ امروز", t_flag_off_is_byte_identical),
        ("breakdown هرگز ترمز را عوض نمی‌کند", t_breakdown_never_changes_the_brake),
        ("partner_stress هیچ تولیدکننده‌ای در قرارداد ندارد",
         t_partner_stress_has_no_producer_in_the_contract),
        ("سرشماری هر شش ترم را پوشش می‌دهد", t_census_covers_every_term_and_matches_measurement),
    ])
    sys.exit(1 if failed else 0)
