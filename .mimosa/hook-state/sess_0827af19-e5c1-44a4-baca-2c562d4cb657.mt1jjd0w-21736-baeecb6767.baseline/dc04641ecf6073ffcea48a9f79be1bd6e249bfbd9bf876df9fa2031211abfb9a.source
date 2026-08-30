#!/usr/bin/env python3
"""test_consolidation_compress_and_recall.py — WS-D: تثبیت باید **فشرده** کند، نه کپی.

پس‌زمینهٔ اندازه‌گیری‌شده (فایلِ زندهٔ `_ops/neural/consolidation.json`، ۲۰۲۶-۰۷-۲۸):
  ۵۳۸ ردیف · ۲۴ امضای محتواییِ یکتا (۴.۵٪) · ۲۵ جملهٔ یکتا از ۶۱۷ نمونه (۴.۱٪)
  ۱۸۱ ردیف عیناً «آگاهیِ میانگین: 0.02» — و **هیچ‌کدام متوالی نبودند**، برای همین
  گاردِ ۰۷-۲۷ که فقط با `history[-1]` مقایسه می‌کرد صفر اثر داشت.

$0 آفلاین، stdlib فقط، همهٔ نوشتن‌ها در tmpdir. هیچ لمسِ state واقعی.
"""
import json
import os
import sys
import tempfile
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent))
sys.path.insert(0, str(_HERE.parent / "budget"))
import harness
ENV = harness.setup("consolidation-compress")   # ایزولاسیون — قبل از هر importِ opslib

from neural import consolidation as C
from neural.consolidation import ConsolidationCycle, recall_reach


# ─── ابزارِ تست ────────────────────────────────────────────────────────────────

class _Clock:
    """ساعتِ **کاملاً** تزریق‌شده — `consolidation._now` جایگزین می‌شود.

    نسخهٔ اولِ همین تست `time.time` را patch می‌کرد و **قرمز شد**: دیتاکلاسِ
    `ConsolidatedInsight` با `default_factory=time.time` ارجاع را در زمانِ تعریفِ
    کلاس بسته بود، پس `timestamp` همچنان ساعتِ واقعی می‌خواند و فقط مسیرِ fallback
    ساعتِ تست را می‌دید — ساعتِ نیمه‌تزریقی، دقیقاً همان بمبِ ساعتی. فیکس در خودِ
    ماژول رفت (`_now()` تنها منبعِ زمان)، و این کلاس همان را patch می‌کند.
    """

    def __init__(self, t0=1_000_000.0):
        self.t = t0

    def __call__(self):
        return self.t

    def advance(self, seconds):
        self.t += seconds

    def __enter__(self):
        self._real = C._now
        C._now = self
        return self

    def __exit__(self, *exc):
        C._now = self._real
        return False


def _fresh(tmp=None):
    d = tmp or Path(tempfile.mkdtemp())
    return ConsolidationCycle(data_path=d / "consolidation.json")


def _aw(v):
    """منبعِ verifiedِ school_awareness که به insight «آگاهیِ میانگین: v» می‌رسد."""
    return {"school_awareness": {"mean_awareness": v}}


def _set(flag_on, floor=None):
    if flag_on:
        os.environ["OCTOPUS_CONSOLIDATION_COMPRESS"] = "1"
    else:
        os.environ.pop("OCTOPUS_CONSOLIDATION_COMPRESS", None)
    if floor is None:
        os.environ.pop("OCTOPUS_CONSOLIDATION_FLOOR_SEC", None)
    else:
        os.environ["OCTOPUS_CONSOLIDATION_FLOOR_SEC"] = str(floor)


def _drive(cyc, values, clock=None, step_s=600.0):
    for v in values:
        cyc.run(_aw(v))
        if clock is not None:
            clock.advance(step_s)


# ─── ۱. پیش‌فرض خاموش، و خاموش = رفتارِ امروز ────────────────────────────────

def t_default_off():
    """بدونِ env، فشرده‌سازی خاموش است و کف مقدارِ مستندشده را دارد."""
    _set(False)
    assert C._compress_on() is False, "پیش‌فرض باید خاموش باشد"
    os.environ["OCTOPUS_CONSOLIDATION_COMPRESS"] = "0"
    assert C._compress_on() is False, "مقدارِ '0' هم یعنی خاموش"
    _set(False)
    assert C._floor_seconds() == 21600.0, "کفِ پیش‌فرض = ۶ ساعت"
    os.environ["OCTOPUS_CONSOLIDATION_FLOOR_SEC"] = "not-a-number"
    assert C._floor_seconds() == 21600.0, "مقدارِ خراب باید به پیش‌فرض برگردد"
    _set(False)


def t_flag_off_is_todays_behaviour():
    """flag خاموش: دقیقاً همان قراردادِ ۰۷-۲۷ — فقط تکرارِ **متوالی** تا می‌شود."""
    _set(False)
    c = _fresh()
    _drive(c, [0.02, 0.02, 0.04, 0.02])     # A A B A
    h = c.history
    assert len(h) == 3, f"مسیرِ قدیمی باید ۳ ردیف بدهد، داد {len(h)}"
    assert h[0]["repeats"] == 2 and h[0]["last_cycle"] == 2, "تاشدنِ متوالی"
    assert h[1]["repeats"] == 1 and h[2]["repeats"] == 1
    assert [r["cycle"] for r in h] == [1, 3, 4]
    assert all("last_ts" not in r for r in h), "flag خاموش نباید کلیدِ تازه بنویسد"


# ─── ۲. هستهٔ فیکس: تکرارِ **غیرِ متوالی** ──────────────────────────────────

def t_alternating_repeat_compresses():
    """A B A B A — دقیقاً الگویی که ۱۸۱ ردیفِ «0.02» را ساخت.
    خاموش → ۵ ردیف (وضعِ امروز). روشن → ۲ ردیف."""
    _set(False)
    off = _fresh()
    _drive(off, [0.02, 0.04, 0.02, 0.04, 0.02])
    assert len(off.history) == 5, f"پیش از فیکس باید ۵ ردیف باشد، شد {len(off.history)}"

    _set(True)
    on = _fresh()
    _drive(on, [0.02, 0.04, 0.02, 0.04, 0.02])
    h = on.history
    assert len(h) == 2, f"با فشرده‌سازی باید ۲ ردیف بماند، شد {len(h)}"
    assert h[0]["repeats"] == 3 and h[1]["repeats"] == 2, f"repeats غلط: {[r['repeats'] for r in h]}"
    assert h[0]["last_cycle"] == 5 and h[1]["last_cycle"] == 4
    assert on.cycle_count == 5, "شمارندهٔ سیکل نباید فشرده شود — فقط ردیف‌ها"
    _set(False)


def t_live_pathology_ratio():
    """بازپخشِ الگویِ واقعی: ۵ سطحِ آگاهی که چرخشی تکرار می‌شوند.
    نسبتِ یکتا/کل باید از ~۲٪ به ۱۰۰٪ برسد."""
    seq = [0.00, 0.02, 0.04, 0.08, 0.12] * 40      # ۲۰۰ سیکل، ۵ محتوای یکتا
    _set(False)
    off = _fresh()
    _drive(off, seq)
    n_off = len(off.history)
    assert n_off == 200, f"پیش از فیکس هر سیکل یک ردیف: انتظار ۲۰۰، شد {n_off}"

    _set(True)
    on = _fresh()
    _drive(on, seq, step_s=0.0)
    n_on = len(on.history)
    assert n_on == 5, f"بعد از فیکس باید ۵ ردیف بماند، شد {n_on}"
    assert sum(r["repeats"] for r in on.history) == 200, "هیچ رویدادی نباید گم شود"
    ratio_off, ratio_on = 5 / n_off, 5 / n_on
    assert ratio_off == 0.025 and ratio_on == 1.0, f"{ratio_off} → {ratio_on}"
    _set(False)


def t_signature_has_no_counter():
    """امضا فقط محتوایی است. دو رکورد با محتوای یکسان ولی سیکل/تکرارِ متفاوت باید
    امضای یکسان بدهند — درسِ «شمارنده در کلیدِ dedup»."""
    a = {"insights": ["x"], "verified_sources": ["s"], "discarded_sources": [],
         "cycle": 1, "repeats": 1, "last_cycle": 1, "timestamp": 10.0}
    b = dict(a, cycle=999, repeats=77, last_cycle=999, timestamp=99999.0)
    assert ConsolidationCycle._signature(a) == ConsolidationCycle._signature(b)
    c = dict(a, insights=["y"])
    assert ConsolidationCycle._signature(a) != ConsolidationCycle._signature(c)


# ─── ۳. کفِ زمانی ─────────────────────────────────────────────────────────────

def t_time_floor_opens_new_row():
    """محتوای یکسان اما فراتر از کف = رویدادِ نو، نه تکرار. بدونِ این، ساختارِ
    زمانی نابود می‌شود و یافتهٔ روزِ نوزدهم داخلِ ردیفِ روزِ اول تا می‌شود."""
    _set(True, floor=3600)
    try:
        with _Clock() as clock:
            c = _fresh()
            c.run(_aw(0.5))
            assert c.history[0]["last_ts"] == clock.t, "last_ts باید از ساعتِ تزریقی بیاید"
            clock.advance(600)          # زیرِ کف
            c.run(_aw(0.5))
            assert len(c.history) == 1, "زیرِ کف باید تا شود"
            assert c.history[0]["repeats"] == 2
            clock.advance(7200)         # فراتر از کف
            c.run(_aw(0.5))
            assert len(c.history) == 2, "فراتر از کف باید ردیفِ نو بسازد"
            assert c.history[1]["repeats"] == 1
            # کف روی **آخرین** مشاهده می‌سنجد نه اولین
            clock.advance(600)
            c.run(_aw(0.5))
            assert len(c.history) == 2 and c.history[1]["repeats"] == 2
            # ...و بعد از کفِ دیگری، ردیفِ سوم
            clock.advance(3601)
            c.run(_aw(0.5))
            assert len(c.history) == 3, "کف باید بارها اعمال شود، نه یک‌بار"
    finally:
        _set(False)


# ─── ۴. ردیفِ غنی (بردارِ latent) هرگز قربانیِ فشرده‌سازی نمی‌شود ────────────

def t_rich_row_never_folded_into():
    """از ۵۳۸ ردیفِ زنده فقط ۲ تا بردار دارند. تا کردنِ ردیفِ نو داخلِ آن‌ها تنها
    دادهٔ کمیابِ فایل را می‌کشد."""
    _set(True, floor=10**9)
    c = _fresh()
    c.run(_aw(0.5))
    c.history[0]["latent_vector"] = [0.1] * 4      # شبیه‌سازیِ ردیفِ غنی
    c._history[0]["latent_vector"] = [0.1] * 4
    c.run(_aw(0.5))
    assert len(c._history) == 2, "ردیفِ غنی نباید مقصدِ تا شدن باشد"
    assert c._history[0]["latent_vector"] == [0.1] * 4, "بردار باید دست‌نخورده بماند"
    _set(False)


# ─── ۵. sync_latent باید ردیفِ تاشده را پیدا کند ─────────────────────────────

class _Res:
    def __init__(self, cycle, vec, keys):
        self.cycle, self.latent_vector, self.similar_keys = cycle, vec, keys


def t_sync_latent_finds_folded_row():
    """با فشرده‌سازی، رکوردِ سیکلِ جاری دیگر `[-1]` نیست. اگر sync_latent هنوز فقط
    آخرین ردیف را نگاه کند، بردار **بی‌صدا دور ریخته می‌شود** — همان باگی که
    ۵۳۶ ردیفِ بدونِ بردار ساخت، این بار از سمتِ دیگر."""
    _set(True, floor=10**9)
    c = _fresh()
    _drive(c, [0.02, 0.04, 0.02], step_s=0.0)     # سیکلِ ۳ داخلِ ردیفِ ۰ تا می‌شود
    assert len(c._history) == 2 and c._history[0]["last_cycle"] == 3
    ok = c.sync_latent(_Res(3, [0.5] * 4, ["cycle-1"]))
    assert ok is True, "sync_latent باید ردیفِ تاشدهٔ قدیمی‌تر را پیدا کند"
    assert c._history[0]["latent_vector"] == [0.5] * 4
    assert c._history[-1].get("latent_vector") is None, "ردیفِ دیگر نباید آلوده شود"
    _set(False)


def t_sync_latent_flag_off_scans_one_row():
    """گاردِ عدم‌رگرسیون: با flag خاموش دامنهٔ جست‌وجو دقیقاً یک ردیف است، یعنی رفتار
    بایت‌به‌بایت همان نسخهٔ قبلی. اگر کسی این را به جست‌وجوی کامل تبدیل کند، رکوردِ
    سیکلِ دیگری ممکن است غنی شود."""
    _set(False)
    c = _fresh()
    _drive(c, [0.02, 0.04])
    c._history[0]["last_cycle"] = 99          # طعمه در ردیفِ قدیمی
    assert c.sync_latent(_Res(99, [0.9], ["k"])) is False, "flag خاموش نباید عقب برود"
    assert c._history[0].get("latent_vector") is None
    assert c.sync_latent(_Res(2, [0.9], ["k"])) is True, "ردیفِ آخر باید کار کند"


def t_sync_latent_rejects_foreign_cycle():
    _set(True, floor=10**9)
    c = _fresh()
    _drive(c, [0.02], step_s=0.0)
    assert c.sync_latent(_Res(4242, [0.1], ["k"])) is False
    assert c.sync_latent(_Res(None, [0.1], ["k"])) is False
    _set(False)


# ─── ۶. دوام روی دیسک + سازگاریِ عقب‌رو با ۵۳۸ ردیفِ موجود ────────────────────

def t_persist_and_reload_legacy_rows():
    """ردیف‌های قدیمی `last_ts` ندارند. بارگذاریِ دوباره نباید بترکد و باید
    `timestamp` را به‌عنوانِ آخرین مشاهده بخواند."""
    _set(True, floor=3600)
    try:
        with _Clock() as clock:
            d = Path(tempfile.mkdtemp())
            legacy = [{"cycle": 1, "insights": ["آگاهیِ میانگین: 0.02"],
                       "verified_sources": ["school_awareness"], "discarded_sources": [],
                       "timestamp": clock.t - 60.0, "repeats": 7, "last_cycle": 7}]
            (d / "consolidation.json").write_text(json.dumps(legacy, ensure_ascii=False),
                                                  encoding="utf-8")
            c = ConsolidationCycle(data_path=d / "consolidation.json")
            # ۲۰۲۶-۰۷-۳۰ — پیش‌تر `== 1` بود: assertِ بی‌پیام که **خودِ باگ را pin کرده بود**.
            # فیکسچرِ همین تست `repeats: 7, last_cycle: 7` است ⇒ هفت شلیک رخ داده، پس نمونهٔ
            # بازخوانده باید از ۷ ادامه دهد. `== 1` بازتابِ `_cycle_count = len(self._history)`
            # بود که شمارنده را به تعدادِ **ردیف** گره می‌زد و هر ری‌استارت عدد را بازتولید
            # می‌کرد (روی دیسکِ زنده: ردیفی با `repeats: 13` که ۱۲ شلیک همه «سیکلِ ۵۳۸» مهر
            # خورده بودند). ضمناً خطِ ۱۳۱ همین فایل صریح می‌گوید «شمارندهٔ سیکل نباید فشرده
            # شود — فقط ردیف‌ها»، پس `== 1` با قصدِ خودِ این فایل هم در تناقض بود.
            assert c.cycle_count == 7, "شمارنده از بیشترین سیکلِ ثبت‌شده seed می‌شود، نه از شمارِ ردیف‌ها"
            c.run(_aw(0.02))
            assert len(c._history) == 1, "ردیفِ قدیمیِ هم‌محتوا (بدونِ last_ts) باید مقصدِ تا شدن باشد"
            assert c._history[0]["repeats"] == 8, "شمارشِ قدیمی باید ادامه پیدا کند نه ری‌ست"
            back = json.loads((d / "consolidation.json").read_text(encoding="utf-8"))
            assert len(back) == 1 and back[0]["repeats"] == 8, "روی دیسک هم باید فشرده باشد"
            # همان ردیفِ قدیمی، ولی فراتر از کف → ردیفِ نو (نه تا شدنِ ابدی)
            clock.advance(7200)
            c.run(_aw(0.02))
            assert len(c._history) == 2
    finally:
        _set(False)


# ─── ۷. متریکِ «بردِ بازیابی» ─────────────────────────────────────────────────

def t_recall_reach_baseline_shape():
    """شکلِ خطِ پایهٔ امروز (۲۰۲۶-۰۷-۲۸): دو رویداد، هشت کلید، بردِ حداکثر ۲ سیکل."""
    hist = [
        {"cycle": 537, "similar_keys": ["cycle-538:school_awareness",
                                        "cycle-539:school_awareness",
                                        "cycle-539", "cycle-537"]},
        {"cycle": 538, "similar_keys": ["cycle-539:school_awareness", "cycle-538",
                                        "cycle-538:school_awareness", "cycle-537"]},
    ] + [{"cycle": i} for i in range(536)]
    m = recall_reach(hist)
    assert m["events"] == 2, m
    assert m["keys"] == 8, m
    assert m["reach_median"] == 1.0, m
    assert m["reach_max"] == 2, m
    assert abs(m["self_ratio"] - 0.375) < 1e-9, m
    assert abs(m["coverage"] - 2 / 538) < 1e-9, m


def t_recall_reach_rises_only_with_distant_recall():
    """متریک با «بیشتر نوشتن» بالا نمی‌رود — فقط با یادآوریِ گذشتهٔ دور."""
    near = [{"cycle": 100, "similar_keys": ["cycle-99", "cycle-101"]}]
    far = [{"cycle": 100, "similar_keys": ["cycle-3", "cycle-7"]}]
    assert recall_reach(near)["reach_median"] == 1.0
    assert recall_reach(far)["reach_median"] == 95.0   # میانهٔ |100-3|=97 و |100-7|=93
    # نوشتنِ ۱۰۰۰ ردیفِ بی‌بازیابی نباید برد را بالا ببرد
    padded = near + [{"cycle": i} for i in range(1000)]
    assert recall_reach(padded)["reach_median"] == 1.0
    assert recall_reach(padded)["coverage"] < recall_reach(near)["coverage"]


def t_recall_reach_empty_and_junk():
    assert recall_reach([])["events"] == 0
    assert recall_reach([{"cycle": 1, "similar_keys": ["not-a-cycle-key"]}])["keys"] == 0
    assert recall_reach([{"cycle": "x", "similar_keys": ["cycle-1"]}])["keys"] == 0
    assert recall_reach(None)["events"] == 0


if __name__ == "__main__":
    failed = harness.run([
        ("پیش‌فرض خاموش + کفِ مستند", t_default_off),
        ("flag خاموش = رفتارِ امروز (فقط متوالی)", t_flag_off_is_todays_behaviour),
        ("تکرارِ غیرمتوالی فشرده می‌شود (۵→۲)", t_alternating_repeat_compresses),
        ("بازپخشِ الگویِ زنده: ۲۰۰→۵", t_live_pathology_ratio),
        ("امضا هیچ شمارنده‌ای ندارد", t_signature_has_no_counter),
        ("کفِ زمانی ردیفِ نو باز می‌کند", t_time_floor_opens_new_row),
        ("ردیفِ غنی هرگز مقصدِ تا شدن نیست", t_rich_row_never_folded_into),
        ("sync_latent ردیفِ تاشده را پیدا می‌کند", t_sync_latent_finds_folded_row),
        ("sync_latent با flag خاموش یک ردیف می‌بیند", t_sync_latent_flag_off_scans_one_row),
        ("sync_latent سیکلِ بیگانه را رد می‌کند", t_sync_latent_rejects_foreign_cycle),
        ("دوام + سازگاریِ عقب‌رو با ردیفِ قدیمی", t_persist_and_reload_legacy_rows),
        ("متریک: خطِ پایهٔ امروز", t_recall_reach_baseline_shape),
        ("متریک: فقط با یادآوریِ دور بالا می‌رود", t_recall_reach_rises_only_with_distant_recall),
        ("متریک: ورودیِ خالی/خراب", t_recall_reach_empty_and_junk),
    ])
    sys.exit(1 if failed else 0)
