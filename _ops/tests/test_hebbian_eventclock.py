"""test_hebbian_eventclock.py — سه نقصِ اندازه‌گیری‌شدهٔ لایهٔ تداعی (۲۰۲۶-۰۷-۳۰).

حقیقتِ پایه: `_ops/state/neural/effect-shadow.jsonl` روی درختِ زنده — اسنپ‌شاتِ
۲۰۲۶-۰۷-۳۰ ۱۰:۴۲ (فایل زنده است و رشد می‌کند): ۵۱۱۴ ردیف از ۰۷-۲۷ ۱۶:۰۴، میانهٔ
فاصلهٔ ردیف ۴۳.۰s. توزیعِ اندازه‌گیری‌شدهٔ `signals`:
    ("errors_high",)                 ۳۸۰۲
    ()                               ۱۱۹۰
    ("errors_high","rhythm_amber")    ۱۱۲
    ("rhythm_amber",)                  ۱۰
یعنی ۳۹۲۴/۵۱۱۴ = ۷۶.۷٪ تیکِ سیگنال‌دار. و `neural/hebbian.json` در همان لحظه:
`[]` با mtime ~۱۶ ثانیه — یعنی یک فایلِ خالی که هر تیک بازنویسی می‌شد.

۱) **کلاکِ زوال با کلاکِ یادگیری ~۱۰۰۰× فاصله داشت.** `decay()` هر تیک؛
   هم‌رخدادی در انفجارهای ۵-۱۰ تیکی؛ فاصلهٔ اندازه‌گیری‌شدهٔ بینِ انفجارها (بر
   حسبِ ساعت): ۱.۵ · ۲.۲ · ۲.۸ · ۳.۲ · ۱۰.۱ · ۱۲.۰ · ۱۲.۴ · ۱۴.۵. با
   `DECAY_RATE=0.95` هر جفت بعد از ~۹۰ تیک زیرِ `PRUNE_THRESHOLD` می‌رفت → جدول
   ساختاراً خالی. ضمناً گیتِ `>=2` روی **هم‌زمانیِ دقیقِ یک تیک** بود، پس آن ۱۰
   تیکِ `rhythm_amber`ِ تنها هرگز جفت نشدند.
۲) **دو نام از ۸ نامِ `BCM_VOCAB` ساختاراً مرده‌اند**، پس کلِ واژگان دقیقاً یک
   جفتِ ممکن دارد. حالا صریح و ماشین‌چک‌شده اعلام می‌شود (`SIGNAL_DORMANT`) و
   گاردِ آن **دوطرفه** است.
۳) **مینِ learned_pressure.** منبعِ امروز theta≈۰ می‌دهد، ولی
   `neural_stack["bcm"]` وزنِ اشباع (۳.۹۹۵/۴.۰) دارد؛ repointِ آن یک خط با
   آستانهٔ کالیبرهٔ ۰.۳۵ یعنی `protective_halt` هر تیک. سقف **کنارِ** مقدارِ خام
   می‌نشیند (`learned_pressure_capped`) و فیلدِ خامِ مالک را دست نمی‌زند: از
   ۳۷۲۶ ردیفِ دارای `learned_pressure`، ۸۵۳ ردیف (۲۲.۹٪) از ۰.۲۵ بالاترند، پس
   سقف‌زدنِ زیرِ همان نام معنیِ یک فیلد را در میانهٔ سری عوض می‌کرد.
۴) **شمارندهٔ بادکردهٔ هم‌رخدادی** (تصحیحِ بازبینیِ متخاصم): نسخهٔ اولِ ساعتِ
   رویدادی پنجره را rolling گرفته بود و هر تیک `observe()` می‌زد — یک تیکِ
   amberِ تنها ⇒ ۲۰ فراخوانی، `co_occurrences=20`، `strength=0.9025`. حالا هر
   پنجره **یک** اعتبار می‌گیرد.

⚠️ دربارهٔ چیزی که **زنده نیست**: فیکسِ early-returnِ `neural/hebbian.py::decay`
در `2c7c14c` (۲۰۲۶-۰۷-۳۰ ۱۰:۳۵) کامیت شده، ولی پروسهٔ زندهٔ ارگانیسم ماژول را
قبل از آن بار کرده است — شاهد: `_ops/neural/hebbian.json` در ۱۰:۴۴:۲۲ همان روز،
۹ دقیقه **بعدِ** کامیت، باز با محتوای `[]` بازنویسی شده بود. پس اثرِ آن فیکس روی
درختِ زنده **صفر** است تا ری‌استارت. این تست‌ها کد را می‌سنجند، نه پروسه را.

هر تست مسیرِ **واقعی** را می‌راند (`wiring.neural_beat`)، هرگز بازنویسیِ الگوریتم.
"""
import json
import os
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))
import harness   # noqa: E402
ENV = harness.setup("hebbian-eventclock")

# ماژول‌های neural (bcm/hebbian) با نامِ کوتاه import می‌شوند
for _p in (str(harness.SELF_OPS), str(harness.SELF_OPS / "neural")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import opslib          # noqa: E402
import wiring          # noqa: E402

HEB = Path(ENV["ops"]) / "neural" / "hebbian.json"


# ═══ ابزار: بازپخشِ شکلِ اندازه‌گیری‌شدهٔ payloadِ زنده ═══════════════════════════
def _payload(amber: bool, error_rate: float) -> dict:
    """دقیقاً شکلِ `NEURAL_PAYLOAD_CONTRACT` — همان چیزی که organism.py می‌دهد."""
    return {
        "rhythm": {"mode_color": "AMBER" if amber else "GREEN"},
        "budget": {"pct": 0.0007208},                 # مقدارِ زندهٔ اندازه‌گیری‌شده
        "spectral": {"sigma": 0.0,
                     "sigma_is_replication_ratio": True,
                     "sigma_source": "replication-latest.json"},
        "sensory": {"afferent_ratio": 1.0, "error_rate": error_rate},
    }


def _replay(stack, n_ticks: int, amber_ticks: set, amber_only: bool = False,
            beat0: int = 1) -> None:
    """`error_rate` بینِ ۰.۱۷ و ۰.۲۵ نوسان می‌کند (آستانه ۰.۲) — نسبتِ زنده
    ۷۶.۷٪ تیکِ سیگنال‌دار بود، این الگو ۸۰٪ می‌دهد.
    `amber_only=True` انفجارِ amber را روی تیک‌هایی می‌گذارد که `error_rate`
    پایین است، تا آن دو انحراف **هرگز هم‌زمان** نباشند (همان ۱۰ ردیفِ زنده)."""
    for i in range(n_ticks):
        low = (i % 5 == 0)
        er = 0.17 if low else 0.25
        amber = i in amber_ticks
        if amber_only and amber:
            er = 0.17
        wiring.neural_beat(stack, beat0 + i, _payload(amber, er))


def _table() -> list:
    if not HEB.exists():
        return []
    try:
        return json.loads(HEB.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []


def _fresh_stack(eventclock: bool):
    """stackِ نو + جدولِ پاک. فلگ‌ها صریح — هیچ ارثِ محیطی."""
    os.environ["OCTOPUS_WIRE_NEURAL"] = "1"
    os.environ["OCTOPUS_HEBBIAN_RICH"] = "1"
    os.environ["OCTOPUS_HEBBIAN_EVENTCLOCK"] = "1" if eventclock else "0"
    os.environ["OCTOPUS_WIRE_BCM_FEED"] = "0"
    os.environ["OCTOPUS_NEURAL_EFFECT_SHADOW"] = "0"
    os.environ.pop("OCTOPUS_NEURAL_LEARNED_APPLY", None)
    if HEB.exists():
        HEB.unlink()
    stack = wiring.make_neural_stack()
    assert stack is not None, "make_neural_stack با فلگِ روشن None داد"
    return stack


def _pair(table, a="errors_high", b="rhythm_amber"):
    want = sorted((a, b))
    for row in table:
        if sorted(row.get("signals") or []) == want:
            return row
    return None


# ═══ ITEM 1 — ساعتِ رویدادی ═════════════════════════════════════════════════
def t_the_measured_replay_leaves_the_table_non_empty():
    """۲۰۰ تیک با شکلِ اندازه‌گیری‌شده: یک انفجارِ amberِ ۵تیکی (۲.۵٪، نسبتِ زنده
    ۲.۴٪ بود) و بعد ۱۷۵ تیک فاصله. با ساعتِ رویدادی جفت زنده می‌ماند.

    اعدادِ حساب‌شده (نه دلبخواه): ۱۶۱ تیکِ سیگنال‌دار ⇒ ۸ پنجرهٔ بسته. انفجارِ
    amber روی مرزِ پنجره می‌افتد پس **دو** پنجره اعتبار می‌گیرند و ۶ پنجرهٔ بعد
    فقط زوال: ((0.1×0.995)+0.1)×0.995×0.995⁶ ≈ ۰.۱۹۳ (بعد از تیونِ ۲۰۲۶-۰۸-۰۴:
    DECAY_RATE 0.95→0.995، PRUNE_THRESHOLD 0.01→0.005 — این عدد با نرخِ قدیم
    ۰.۱۳۶ بود)."""
    stack = _fresh_stack(eventclock=True)
    _replay(stack, 200, amber_ticks=set(range(20, 25)))
    tbl = _table()
    assert tbl, "جدول بعد از ۲۰۰ تیک خالی است — ساعتِ رویدادی کار نکرد"
    row = _pair(tbl)
    assert row is not None, f"جفتِ errors_high×rhythm_amber ثبت نشد: {tbl}"
    from hebbian import PRUNE_THRESHOLD
    assert row["strength"] > PRUNE_THRESHOLD, f"جفت زنده نماند: {row}"
    assert 0.19 < row["strength"] < 0.20, f"حسابِ قدرت drift کرد: {row}"
    # گاردِ ضدِ باد: یک انفجارِ ۵تیکی حداکثر دو پنجره را لمس می‌کند، پس ۲ است.
    # نسخهٔ بادکرده اینجا ~۱۰۰ می‌داد (هر تیکِ داخلِ پنجره یک شمارش).
    assert row["co_occurrences"] == 2, f"شمارندهٔ هم‌رخدادی درست نیست: {row}"


def t_with_the_event_clock_off_the_same_replay_survives_but_still_overcounts():
    """همان ۲۰۰ تیک، فلگ خاموش → مسیرِ ۲۰۲۶-۰۷-۲۷.

    فرضِ قدیمِ «جدول خالی» روی DECAY_RATE=0.95 بسته شده بود: با آن نرخ جفت در
    ۲۰۰ تیک زیرِ PRUNE_THRESHOLD می‌رفت. بعد از تیونِ ۲۰۲۶-۰۸-۰۴
    (DECAY_RATE 0.95→0.995، PRUNE_THRESHOLD 0.01→0.005) عمرِ جفت خیلی طولانی‌تر
    شده و ۲۰۰ تیک دیگر کافی نیست — جدول زنده می‌ماند (با این نرخ جفت حدودِ تیکِ
    ۸۹۷ می‌میرد، نه ۲۰۰؛ محاسبه‌شده با همان روشِ replay).

    discriminatorِ فیکس هنوز اینجاست، فقط جابه‌جا شده: مسیرِ قدیمی decay را
    **هر تیکِ خام** می‌زند و observe را هر تیکی که دو سیگنال هم‌زمان باشند (نه
    هر پنجره) — پس در تیک‌های ۲۱،۲۲،۲۳،۲۴ چهار بار observe می‌زند (تیکِ ۲۰
    خودش errors_high نیست چون i%5==0 ⇒ error_rate=0.17)، نه دو پنجره‌ی
    ساعتِ رویدادی. اگر روزی co_occurrences اینجا با تستِ eventclock=True یکی
    شد (هر دو ۴ یا هر دو ۲) یعنی پنجره‌بندی دیگر کار نمی‌کند."""
    stack = _fresh_stack(eventclock=False)
    _replay(stack, 200, amber_ticks=set(range(20, 25)))
    tbl = _table()
    row = _pair(tbl)
    assert row is not None, f"مسیرِ قدیمی دیگر جفت نمی‌سازد — فرضِ تست کهنه است: {tbl}"
    assert row["co_occurrences"] == 4, \
        f"شمارندهٔ per-tickِ مسیرِ قدیمی عوض شد: {row}"
    assert 0.16 < row["strength"] < 0.17, f"حسابِ قدرت drift کرد: {row}"


def t_two_deviations_minutes_apart_can_finally_associate():
    """آن ۱۰ ردیفِ زنده: `rhythm_amber` **تنها**، بدونِ `errors_high`.
    با گیتِ هم‌زمانی، `observe()` هرگز صدا زده نمی‌شد → صفر جفت، برای همیشه."""
    stack = _fresh_stack(eventclock=True)
    _replay(stack, 120, amber_ticks={20, 25, 30}, amber_only=True)
    assert _pair(_table()) is not None, \
        f"انحرافِ غیرهم‌زمان هنوز جفت نمی‌شود: {_table()}"


def t_without_the_window_non_simultaneous_deviations_never_pair():
    """همان سناریو با فلگ خاموش → هیچ جفتی، هیچ‌وقت."""
    stack = _fresh_stack(eventclock=False)
    _replay(stack, 120, amber_ticks={20, 25, 30}, amber_only=True)
    assert _table() == [], f"فرضِ تست کهنه است — مسیرِ قدیمی جفت ساخت: {_table()}"


def t_an_empty_cycle_touches_no_disk():
    """قراردادِ «چرخهٔ خالی زوال ندارد» (آینهٔ bcm.py::step، FIX #214).
    نقصِ زنده: `hebbian.json` با محتوای `[]` هر تیک بازنویسی می‌شد."""
    stack = _fresh_stack(eventclock=True)
    _replay(stack, 60, amber_ticks=set(range(10, 15)))
    assert HEB.exists()
    before_ns, before_txt = HEB.stat().st_mtime_ns, HEB.read_text(encoding="utf-8")
    # ۱۰ تیکِ کاملاً بی‌سیگنال: rhythm سبز + error_rate زیرِ آستانه
    for i in range(10):
        wiring.neural_beat(stack, 900 + i, _payload(False, 0.17))
    assert HEB.stat().st_mtime_ns == before_ns, \
        "تیکِ بی‌سیگنال هنوز فایل را می‌نویسد (mtime عوض شد)"
    assert HEB.read_text(encoding="utf-8") == before_txt, "محتوا عوض شد"


def t_decay_on_an_empty_table_writes_nothing():
    """همان قرارداد، یک لایه پایین‌تر — روی خودِ `HebbianAssociator`."""
    from hebbian import HebbianAssociator
    p = Path(ENV["ops"]) / "neural" / "heb-empty-probe.json"
    if p.exists():
        p.unlink()
    h = HebbianAssociator(data_path=p)
    h.decay()
    assert not p.exists(), "decay روی جدولِ تهی فایل ساخت"
    h.observe(["a", "b"])
    assert p.exists()
    h.decay()
    assert json.loads(p.read_text(encoding="utf-8")), "decay روی جدولِ غیرخالی باید بنویسد"


def t_one_burst_is_credited_once_per_window_not_once_per_tick():
    """شمارندهٔ هم‌رخدادی باید همان چیزی را بشمارد که نامش می‌گوید.

    اندازه‌گیریِ نسخهٔ اول (پنجرهٔ rolling + observeِ هر تیک): **یک** تیکِ amber
    روی ۶۰ تیکِ سیگنال‌دار ⇒ ۲۰ فراخوانیِ `observe()` · `co_occurrences=20` ·
    `strength=0.9025` · و `strong_associations(0.3)` جفتی را «قوی» اعلام می‌کرد
    که یک‌بار رخ داده بود. یعنی همان پنجره بیست بار اعتبار می‌گرفت.

    اینجا خودِ `observe` جاسوسی می‌شود (شمارشِ واقعی، نه استنتاج از خروجی)، پس
    برگرداندنِ اعتبار به per-tick قرمز می‌شود حتی اگر جدول شبیه بماند.
    موتاسیون: شرطِ `filled == HEBBIAN_WINDOW` را بردار → ۲۰ ≠ ۱ → قرمز."""
    stack = _fresh_stack(eventclock=True)
    heb = stack["hebbian"]
    real, calls = heb.observe, []

    def _spy(sig):
        calls.append(tuple(sorted(set(sig))))
        return real(sig)

    heb.observe = _spy
    W = wiring.HEBBIAN_WINDOW
    for i in range(W * 3):                       # هر ۶۰ تیک سیگنال‌دار است
        r = wiring._hebbian_eventclock_beat(
            stack, wiring._hebbian_signals(_payload(i == 5, 0.25)))
        assert r["fired"] >= 1, r
    assert len(calls) == 1, \
        f"یک تیکِ amber باید یک اعتبار بدهد، {len(calls)} داد: {calls}"
    assert calls[0] == ("errors_high", "rhythm_amber"), calls
    row = _pair(_table())
    assert row is not None, f"جفت ثبت نشد: {_table()}"
    assert row["co_occurrences"] == 1, f"شمارنده باد کرده: {row}"
    # ۳ پنجره: اعتبار در اولی، سپس ۳ زوال ⇒ 0.1×0.995³ ≈ ۰.۰۹۸۵ (با نرخِ قدیم
    # ۰.۹۵ همین حساب ۰.۰۸۵۷ می‌داد — DECAY_RATE تیون شد ۲۰۲۶-۰۸-۰۴)
    assert 0.09 < row["strength"] < 0.10, f"حسابِ قدرت drift کرد: {row}"
    assert not heb.strong_associations(0.3), \
        f"قدرتی که رخ نداده «قوی» اعلام شد: {heb.strong_associations(0.3)}"


def t_the_event_clock_ties_decay_to_the_learning_clock():
    """قراردادِ عددی: یک زوال به‌ازای هر `HEBBIAN_WINDOW` تیکِ **سیگنال‌دار** —
    نه به‌ازای هر تیکِ دیوار. اگر کسی این را per-tick برگرداند، قرمز می‌شود."""
    stack = _fresh_stack(eventclock=True)
    n_decay = n_signal = 0
    for i in range(100):
        er = 0.17 if i % 5 == 0 else 0.25
        r = wiring._hebbian_eventclock_beat(
            stack, wiring._hebbian_signals(_payload(False, er)))
        n_decay += 1 if r["decayed"] else 0
        n_signal += 1 if r["fired"] else 0
    assert n_signal == 80, n_signal
    assert n_decay == n_signal // wiring.HEBBIAN_WINDOW == 4, \
        f"کلاکِ زوال {n_decay} زوال روی {n_signal} تیکِ سیگنال‌دار داد"


# ═══ ITEM 2 — parityِ واژگان ════════════════════════════════════════════════
# payloadِ بیشینه‌ی «اکستریم» — فقط از کلیدهای `NEURAL_PAYLOAD_CONTRACT` ساخته
# می‌شود و کلیدهای پین‌شده (ثابتِ هاردکدِ organism) روی همان مقدارِ پین می‌مانند.
_EXTREMES = {
    "rhythm_amber":     {"rhythm": {"mode_color": "AMBER"}},
    "rhythm_yellow":    {"rhythm": {"mode_color": "YELLOW"}},
    "rhythm_red":       {"rhythm": {"mode_color": "RED"}},
    "sigma_high":       {"spectral": {"sigma": 9.9}},
    "budget_tight":     {"budget": {"pct": 0.99}},
    "budget_depleted":  {"budget": {"depleted": True}},
    "afferent_starved": {"sensory": {"afferent_ratio": 0.0}},
    "errors_high":      {"sensory": {"error_rate": 0.99}},
}


def _contract_payload(extreme: dict) -> dict:
    """payload = اکستریمِ خواسته‌شده، ولی **فیلترشده با قرارداد**: کلیدی که
    تولیدکنندهٔ زنده نمی‌دهد حذف می‌شود و کلیدِ ثابت به مقدارِ پینش برمی‌گردد.
    این همان مرزی است که «قابلِ فراخوانی» را از «قابلِ آتش در تولید» جدا می‌کند —
    و بی آن، این تست بی‌دندان می‌شد (`sigma_high` با ورودیِ آزاد سبز می‌شود)."""
    out = {}
    for group, fields in wiring.NEURAL_PAYLOAD_CONTRACT.items():
        got = extreme.get(group) or {}
        vals = {}
        for key, pinned in fields.items():
            if pinned is not wiring.FREE:
                vals[key] = pinned              # هاردکدِ organism برنده است
            elif key in got:
                vals[key] = got[key]
        out[group] = vals
    return out


def t_every_vocabulary_name_is_activatable_in_production_or_declared_dormant():
    """گاردِ **دوطرفه**: نامی که با قراردادِ زنده آتش نمی‌کند باید در
    `SIGNAL_DORMANT` باشد، و نامی که آتش می‌کند نباید باشد (لیستِ کهنه = دروغِ
    تازه). موتاسیون: نامی به BCM_VOCAB اضافه کن که هیچ مسیرِ آتش ندارد → قرمز."""
    os.environ["OCTOPUS_HEBBIAN_RICH"] = "1"
    unreachable, reachable = [], []
    for name in wiring.BCM_VOCAB:
        extreme = _EXTREMES.get(name)
        assert extreme is not None, \
            f"نامِ واژگان '{name}' هیچ payloadِ اکستریمِ شناخته‌شده ندارد"
        fired = wiring._hebbian_signals(_contract_payload(extreme))
        (reachable if name in fired else unreachable).append(name)
    missing = set(unreachable) - set(wiring.SIGNAL_DORMANT)
    assert not missing, f"سیگنالِ مردهٔ اعلام‌نشده (واژگان دروغ می‌گوید): {sorted(missing)}"
    stale = set(wiring.SIGNAL_DORMANT) & set(reachable)
    assert not stale, f"در SIGNAL_DORMANT است ولی آتش می‌کند (لیستِ کهنه): {sorted(stale)}"
    assert set(unreachable) == {"sigma_high", "budget_depleted"}, \
        f"مجموعهٔ مردهٔ اندازه‌گیری‌شده عوض شد: {sorted(unreachable)}"
    assert set(wiring.SIGNAL_DORMANT) <= set(wiring.BCM_VOCAB), "کلیدِ بیگانه در لیست"
    for name, why in wiring.SIGNAL_DORMANT.items():
        assert isinstance(why, str) and len(why) > 60, f"دلیلِ '{name}' توضیح نیست"


def t_the_dormant_names_stay_in_the_bcm_vocabulary_so_forgetting_still_works():
    """اعلام ≠ حذف: `BCM.step` فقط `known_keys` را دنبال می‌کند و کلیدِ حذف‌شده را
    **drop** می‌کند. حذفِ نامِ مرده وزنِ زندهٔ روی دیسک را پاک می‌کرد."""
    for name in wiring.SIGNAL_DORMANT:
        assert name in wiring.BCM_VOCAB, f"{name} از واژگان حذف شده"


def _balanced(src: str, start: int) -> str:
    """زیررشتهٔ `{...}`ِ متوازن از اولین `{` بعد از start، با کامنت‌های حذف‌شده.
    حذفِ کامنت لازم است چون پروزهٔ فارسیِ همان بلوک نامِ کلیدها را می‌بَرد."""
    a = src.index("{", start)
    depth = 0
    for b in range(a, len(src)):
        if src[b] == "{":
            depth += 1
        elif src[b] == "}":
            depth -= 1
            if depth == 0:
                break
    body = src[a:b + 1]
    return "\n".join(ln for ln in body.split("\n") if not ln.strip().startswith("#"))


def _scan_payload(body: str) -> dict:
    """{group: set(fieldها)} — و `None` برای گروهی که مقدارش dict-literal نیست
    (مثلاً `"rhythm": _rhythm_state or pulse.get("chrono", {})`؛ آن گروه از
    جای دیگری می‌آید و متنِ همین‌جا دربارهٔ فیلدهایش چیزی نمی‌گوید).
    اسکنِ depth-محور — نه regexِ ساده: `pulse.get("chrono", {})` یک رشتهٔ نقل‌قولی
    در depth 1 دارد که **کلید نیست** (بعدش `,` می‌آید نه `:`)."""
    import re
    out, i, depth = {}, 0, 0
    while i < len(body):
        ch = body[i]
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
        elif ch == '"' and depth == 1:
            m = re.match(r'"(\w+)"\s*:', body[i:])
            if m:
                name = m.group(1)
                rest = body[i + m.end():]
                if rest.lstrip().startswith("{"):
                    inner = _balanced(rest, 0)
                    out[name] = set(re.findall(r'"(\w+)"\s*:', inner))
                    i += m.end() + rest.index("{") + len(inner)
                    continue
                out[name] = None
                i += m.end()
                continue
        i += 1
    return out


def t_the_payload_contract_mirrors_the_live_producer_source():
    """driftِ دوطرفه با متنِ organism.py. اگر روزی `depleted` واقعاً داده شود،
    این تست قرمز می‌شود و `SIGNAL_DORMANT` را مجبور به آپدیت می‌کند."""
    src = (harness.SELF_OPS / "organism.py").read_text(encoding="utf-8")
    body = _balanced(src, src.index("_w.neural_beat(_neural_stack, _beat_n, {"))
    groups = _scan_payload(body)
    assert set(groups) == set(wiring.NEURAL_PAYLOAD_CONTRACT), \
        f"گروه‌های payload drift کردند: organism={sorted(groups)}"
    for group, fields in groups.items():
        declared = wiring.NEURAL_PAYLOAD_CONTRACT[group]
        if fields is None:
            # مقدار از جای دیگر می‌آید → هیچ ثابتی نمی‌شود دربارهٔ آن ادعا کرد
            assert all(v is wiring.FREE for v in declared.values()), \
                f"گروهِ '{group}' literal نیست ولی قرارداد مقدارِ پین‌شده ادعا می‌کند"
            continue
        assert fields == set(declared), \
            f"کلیدهای '{group}' drift کردند: organism={sorted(fields)} " \
            f"قرارداد={sorted(declared)}"
    assert '"sigma_is_replication_ratio": True' in body, \
        "ثابتِ پین‌شده در منبع نیست — SIGNAL_DORMANT['sigma_high'] بی‌پایه شد"
    assert '"depleted"' not in body, \
        "organism الان depleted می‌دهد → budget_depleted دیگر مرده نیست، لیست را آپدیت کن"


def t_the_second_producer_supplies_no_key_outside_the_contract():
    """brain_worker.py تولیدکنندهٔ دومِ همین payload است (و `spectral` را حتی
    ناقص‌تر می‌دهد: بدونِ `sigma_is_replication_ratio` → `None is False` → همان
    مرگ). زیرمجموعه‌بودنش pin می‌شود تا کلیدِ تازه آن‌جا هم دیده شود."""
    src = (harness.SELF_OPS / "brain_worker.py").read_text(encoding="utf-8")
    body = _balanced(src, src.index("w.neural_beat(ctx.wired.neural_stack, beat, {"))
    groups = _scan_payload(body)
    extra_groups = set(groups) - set(wiring.NEURAL_PAYLOAD_CONTRACT)
    assert not extra_groups, f"گروهِ خارج از قرارداد: {sorted(extra_groups)}"
    for group, fields in groups.items():
        if fields is None:
            continue
        extra = fields - set(wiring.NEURAL_PAYLOAD_CONTRACT[group])
        assert not extra, f"brain_worker در '{group}' کلیدِ بیگانه می‌دهد: {sorted(extra)}"
    assert "sigma_is_replication_ratio" not in (groups.get("spectral") or set()), \
        "brain_worker حالا آن کلید را می‌دهد — SIGNAL_DORMANT['sigma_high'] را بازبینی کن"


# ═══ ITEM 3 — سقفِ learned_pressure ═════════════════════════════════════════
def _saturated_bcm(path: Path):
    """BCMِ اشباع — همان چیزی که `state/bcm-weights.json` زنده امروز دارد
    (w تا ۳.۹۹۵ از سقفِ ۴.۰)."""
    from bcm import BCMStabilizer
    if path.exists():
        path.unlink()
    b = BCMStabilizer(persist_path=path)
    for _ in range(80):
        b.step({k: 1.0 for k in wiring.BCM_VOCAB}, known_keys=list(wiring.BCM_VOCAB))
    for k in b.keys():
        b._weights[k]["w"] = 4.0        # سقفِ w_cap — بدترین حالتِ ممکن
    return b


def t_a_saturated_bcm_cannot_push_learned_pressure_past_the_ceiling():
    """موتاسیون: خطِ سقف را بردار → مقدارِ رسیده به ترمز ≈۰.۹۹ → قرمز.

    و همین‌جا قاعدهٔ MF2 قفل می‌شود: فیلدِ **خامِ** مالک دست‌نخورده می‌ماند."""
    stack = _fresh_stack(eventclock=True)
    stack[wiring.NEURAL_EVAL_BCM_SOURCE] = _saturated_bcm(
        Path(ENV["ops"]) / "state" / "bcm-sat.json")
    r = wiring.neural_beat(stack, 5000, _payload(True, 0.25))
    bi = (r or {}).get("brain_inputs") or {}
    assert bi.get("learned_n_keys") == len(wiring.BCM_VOCAB), bi
    raw = bi["learned_pressure"]                  # ← فیلدِ مالک، خام
    assert raw > wiring.LEARNED_PRESSURE_CEILING, \
        f"BCM اشباع نشد — تست بی‌دندان است (raw={raw})"
    assert raw >= 0.95, f"بدترین‌حالت بازتولید نشد: raw={raw}"
    capped = bi[wiring.LEARNED_PRESSURE_CAPPED_KEY]
    assert capped <= wiring.LEARNED_PRESSURE_CEILING, f"سقف نگرفت: {capped}"
    assert capped == wiring.LEARNED_PRESSURE_CEILING, capped


def t_the_ceiling_never_rewrites_the_field_the_owner_reads():
    """MF2 روی **خودِ لاگی که مالک می‌خواند**، نه روی dictِ درون‌حافظه.

    `state/neural/effect-shadow.jsonl` سریِ تصمیم است (۳۷۲۶ ردیفِ دارای این
    فیلد، ۸۵۳ ردیف بالاتر از ۰.۲۵). اگر سقف زیرِ همان نام بنشیند، معنیِ فیلد در
    میانهٔ سری عوض می‌شود و مالک روی دو واحدِ مختلف رأی می‌دهد.
    موتاسیون: در `_derive_learned_pressure_cap` بنویس
    `bi["learned_pressure"] = ...` → قرمز."""
    stack = _fresh_stack(eventclock=True)
    stack[wiring.NEURAL_EVAL_BCM_SOURCE] = _saturated_bcm(
        Path(ENV["ops"]) / "state" / "bcm-sat3.json")
    log = Path(ENV["ops"]) / "state" / "neural" / "effect-shadow.jsonl"
    if log.exists():
        log.unlink()
    os.environ["OCTOPUS_NEURAL_EFFECT_SHADOW"] = "1"
    try:
        wiring.neural_beat(stack, 5002, _payload(True, 0.25))
    finally:
        os.environ["OCTOPUS_NEURAL_EFFECT_SHADOW"] = "0"
    assert log.exists(), "سایه نوشته نشد — تست بی‌دندان است"
    rows = [json.loads(ln) for ln in
            log.read_text(encoding="utf-8").splitlines() if ln.strip()]
    assert rows, "ردیفی ثبت نشد"
    row = rows[-1]
    assert row["learned_pressure"] > wiring.LEARNED_PRESSURE_CEILING, \
        f"فیلدِ مالک سقف‌خورده ثبت شد (سری بی‌اعتبار می‌شود): {row}"
    assert row["learned_pressure"] >= 0.95, row
    assert row[wiring.LEARNED_PRESSURE_CAPPED_KEY] == \
        wiring.LEARNED_PRESSURE_CEILING, row


def t_the_ceiling_keeps_learning_from_halting_the_organism_alone():
    """حسابِ ایمنی: بیشینهٔ دردِ اندازه‌گیری‌شده روی ۵۱۱۴ تیک ۰.۱۵۲ بود و
    ضریبِ ترکیب ۰.۵ است. با آستانهٔ کالیبرهٔ ۰.۳۵ باید حاشیه بماند."""
    from nociceptor import PROTECTIVE_THRESHOLD_CALIBRATED as thr
    worst = 0.152 + wiring.LEARNED_PRESSURE_CEILING * 0.5
    assert worst < float(thr), f"سقف بی‌اثر است: {worst} >= {thr}"
    unclamped = 0.152 + 1.0 * 0.5
    assert unclamped > float(thr), "بدونِ سقف halt نمی‌شد — فرضِ تست کهنه است"


def t_the_ceiling_reaches_the_real_apply_path():
    """ADR-034: سقف روی shadow fold (PROPOSAL) اثر می‌گذارد — هرگز protective_halt.

    همان نتیجهٔ neural_beat با PROPOSAL+آستانهٔ کالیبره:
    (۱) با کلید سقف → action != protective_halt (و معمولاً none)
    (۲) بی‌سقف → ممکن است protective_proposal شود (نه halt)
    (۳) سقف=خام → protective_proposal + reason_codes شامل shadow_fold
    """
    stack = _fresh_stack(eventclock=True)
    stack[wiring.NEURAL_EVAL_BCM_SOURCE] = _saturated_bcm(
        Path(ENV["ops"]) / "state" / "bcm-sat2.json")
    r = wiring.neural_beat(stack, 5001, _payload(True, 0.25))
    os.environ["OCTOPUS_NEURAL_PROTECTIVE_PROPOSAL"] = "1"
    os.environ["OCTOPUS_PAIN_THRESHOLD_CALIBRATED"] = "1"
    os.environ["OCTOPUS_NEURAL_LEARNED_APPLY"] = "0"
    try:
        got = wiring.protective_override(r)
        assert got["action"] != "protective_halt", f"APPLY=0 forbid halt: {got}"
        assert got["executable"] is False
        raw_result = json.loads(json.dumps(r))
        bi = raw_result["brain_inputs"]
        raw = bi["learned_pressure"]
        bi.pop(wiring.LEARNED_PRESSURE_CAPPED_KEY)
        bad = wiring.protective_override(raw_result)
        assert bad["action"] != "protective_halt"
        assert bad["executable"] is False
        # uncapped may reach proposal under calibrated thr
        assert bad["action"] in ("protective_proposal", "none"), bad
        forced = json.loads(json.dumps(r))
        forced["brain_inputs"][wiring.LEARNED_PRESSURE_CAPPED_KEY] = raw
        hit = wiring.protective_override(forced)
        assert hit["action"] != "protective_halt"
        assert hit["executable"] is False
        if hit["action"] == "protective_proposal":
            codes = (hit.get("assessment") or {}).get("reason_codes") or ()
            assert "learned_pressure_shadow_fold" in codes, hit
    finally:
        os.environ.pop("OCTOPUS_NEURAL_PROTECTIVE_PROPOSAL", None)
        os.environ.pop("OCTOPUS_PAIN_THRESHOLD_CALIBRATED", None)
        os.environ.pop("OCTOPUS_NEURAL_LEARNED_APPLY", None)


def t_a_result_without_the_cap_key_behaves_exactly_as_before():
    """APPLY=1 folds uncapped learned → halt; PROPOSAL alone → proposal; off → none."""
    os.environ["OCTOPUS_NEURAL_LEARNED_APPLY"] = "1"
    os.environ.pop("OCTOPUS_PAIN_THRESHOLD_CALIBRATED", None)
    os.environ.pop("OCTOPUS_NEURAL_PROTECTIVE_PROPOSAL", None)
    try:
        legacy = {"pain": {"level": 0.3}, "reflexes": [],
                  "brain_inputs": {"learned_pressure": 0.9,
                                   "learned_top_signal": "k1"}}
        got = wiring.protective_override(legacy)
        assert got["override"] is True and got["action"] == "protective_halt", got
        assert got["executable"] is True
        os.environ["OCTOPUS_NEURAL_LEARNED_APPLY"] = "0"
        os.environ["OCTOPUS_NEURAL_PROTECTIVE_PROPOSAL"] = "1"
        prop = wiring.protective_override(legacy)
        assert prop["override"] is False and prop["executable"] is False
        assert prop["action"] == "protective_proposal", prop
        os.environ.pop("OCTOPUS_NEURAL_PROTECTIVE_PROPOSAL", None)
        os.environ.pop("OCTOPUS_NEURAL_LEARNED_APPLY", None)
        off = wiring.protective_override(legacy)
        assert off["override"] is False and off["action"] == "none", off
    finally:
        os.environ.pop("OCTOPUS_NEURAL_LEARNED_APPLY", None)
        os.environ.pop("OCTOPUS_NEURAL_PROTECTIVE_PROPOSAL", None)


def t_the_eval_bcm_source_is_named_and_is_not_the_latent_index():
    """`neural_stack["bcm"]` ایندکسِ latent است و وزنش اشباع؛ اگر منبع به آن
    repoint شود سقف تنها خطِ دفاع می‌ماند. نامِ منبع اینجا pin می‌شود."""
    import inspect
    assert wiring.NEURAL_EVAL_BCM_SOURCE == "bcm_signals", wiring.NEURAL_EVAL_BCM_SOURCE
    src = inspect.getsource(wiring.neural_beat)
    head = src[:src.index("result = driver.evaluate(")]
    assert "NEURAL_EVAL_BCM_SOURCE" in head, "منبع دیگر نامدار نیست"
    assert 'neural_stack.get("bcm")' not in src, "منبع به ایندکسِ latent repoint شد"
    assert "_derive_learned_pressure_cap(result)" in src, "سقف از مسیر برداشته شد"


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'OK' if not failed else 'FAIL'} test_hebbian_eventclock: "
          f"{len(checks) - failed}/{len(checks)} passed, {failed} failed")
    sys.exit(1 if failed else 0)
