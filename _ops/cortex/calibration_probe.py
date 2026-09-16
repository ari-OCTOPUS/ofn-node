#!/usr/bin/env python3
"""calibration_probe.py — واسنجیِ برخطِ بیرونی‌گرید (Kamoi TACL 2024): Brier + AURC.

مسئله (خودگریدی ممنوع): یک ماژول نباید ادعاهای خودش را با قضاوتِ خودش «درست»
اعلام کند — این حلقهٔ خوش‌بینیِ کاذب می‌سازد. Kamoi و همکاران (TACL 2024) نشان
دادند که خود-تصحیح/خود-قضاوتِ LLM بی‌لنگرِ بیرونی غیرقابل‌اعتماد است. پس اینجا
**تنها منبعِ حقیقت، لِجِرهای بیرونیِ رویداد** است — نه خودِ ادعا.

کاری که می‌کند:
  ۱) ادعاهای اخیرِ خودِ سیستم را می‌خواند (هر ادعا: یک `key` + یک `confidence`∈[0,1]).
     این ادعاها را یک مؤلفهٔ دیگر (مثلِ خود-مدلیِ self_model یا goal_directed) می‌نویسد؛
     این ماژول فقط **می‌خواند** و هرگز به self_model سیم‌کشی نمی‌شود.
  ۲) هر ادعا را با **حقیقتِ بیرونی** از لِجِرهای state جفت می‌کند —
     `cortex/outcomes.jsonl` و `discoveries.jsonl` — که هر رکوردِ حقیقت یک `key`
     و یک نتیجهٔ دودوییِ y∈{0,1} دارد. ادعای بی‌جفت = **گرید‌نشده** (از Brier کنار
     می‌رود؛ نبودِ شاهد، شاهدِ نبود نیست).
  ۳) Brier = میانگینِ (confidence − y)²  ·  AURC = پروکسیِ ریسک-پوشش (۰/۱-loss،
     مرتب بر حسبِ confidence). آستانهٔ `abstain_below` را پیشنهاد می‌دهد: زیرِ این
     اطمینان، ادعاها بی‌اعتمادند → خودداری.

ناوردی‌ها:
  • حقیقت = فقط لِجِرِ بیرونی. هرگز از خودِ ادعا حقیقت استخراج نمی‌شود (ضدِ خودگریدی).
  • additive/shadow: صفر اثر تا وقتی env-flag `CORTEX_SELF_MONITOR` روشن شود؛ فقط
    آن‌وقت رکوردِ فراشناختی زیرِ STATE_DIR نوشته می‌شود.
  • fail-soft: لِجِرِ نبود/خالی → n=0، بدونِ کرش. هر خطا → پیش‌فرضِ امن.
  • $0 · stdlib + opslib · بی‌محتوا (فقط keyهای مات و اعداد؛ هیچ محتوای خصوصی).
"""
from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

_HERE = Path(__file__).resolve().parent
if str(_HERE.parent / "budget") not in sys.path:
    sys.path.insert(0, str(_HERE.parent / "budget"))
import opslib  # noqa: E402

STATE = opslib.STATE_DIR
# ── منابع ────────────────────────────────────────────────────────────────────
# ادعاهای خودِ سیستم (طرفِ «خود») — یک مؤلفهٔ دیگر می‌نویسد؛ اینجا فقط خوانده می‌شود.
CLAIMS = STATE / "cortex" / "self-claims.jsonl"
# حقیقتِ بیرونی (طرفِ «گرید») — فقط این لِجِرها؛ هرگز از خودِ ادعا.
OUTCOMES = STATE / "cortex" / "outcomes.jsonl"
DISCOVERIES = STATE / "discoveries.jsonl"
# WS-B (۲۰۲۶-۰۷-۲۸) — سومین لِجِرِ حقیقت: ردیف‌های {key: "selfknow.<field>",
# correct: 0/1} که self_accuracy می‌نویسد. y آن‌جا از مقایسهٔ گزارشِ خودمدل با
# ORGANISM-STATE.json/fitness-latest.json می‌آید — لنگرِ بیرونیِ واقعی، نه قضاوتِ
# خودِ ادعا؛ عددِ confidence هیچ نقشی در ساختنِ آن ندارد (ناوردیِ ضدِ خودگریدی).
# فایل تا وقتی هر دو فلگ خاموش‌اند اصلاً ساخته نمی‌شود → امروز صفر اثر.
SELF_ACCURACY = STATE / "doctor" / "self-accuracy.jsonl"
# خروجیِ فراشناختی (فقط زیرِ فلگ نوشته می‌شود)
LATEST = STATE / "cortex" / "calibration-latest.json"
HISTORY = STATE / "cortex" / "calibration-log.jsonl"

FLAG = "CORTEX_SELF_MONITOR"          # env-flag فعال‌سازیِ نوشتن (وجود/truthy = روشن)
# WS-1 (۲۰۲۶-۰۷-۲۹) — کلیدِ حقیقت = (پیشنهاد + دور). خاموش = بایت‌به‌بایتِ دیروز.
FLAG_BY_CYCLE = "CORTEX_TRUTH_BY_CYCLE"
# U1 (2026-09-07): نسخهٔ معناشناسیِ حقیقتِ دودویی — با خروجیِ probe حمل می‌شود.
TRUTH_SEMANTICS = "binary_truth.v2: unresolved=ungraded (U1 2026-09-07)"
ABSTAIN_TARGET_ACC = 0.75            # نوارِ «اعتمادپذیر»: دقتِ نگه‌داشته‌ها باید ≥ این باشد
DEFAULT_WINDOW_H = 24 * 30           # «اخیر» = ۳۰ روزِ گذشته
MAX_GRADED = 500                     # سقفِ فهرستِ برگشتی (کران)

# نامِ فیلدها — پذیرشِ چند شکل تا به شِمای واقعیِ لِجِرها انعطاف داشته باشد
_CONF_FIELDS = ("confidence", "conf", "prob", "probability", "p")
_KEY_FIELDS = ("key", "id", "claim_id", "ref", "claim", "title")
_TRUE_FIELDS = ("correct", "hit", "resolved", "confirmed", "moved", "y", "label")
_TRUTHY = {"1", "true", "yes", "hit", "correct", "confirmed", "resolved", "moved"}
# U1 (2026-09-07, truth_semantics v2): «unresolved» = مشاهدهٔ ناتمام، نه شکستِ
# دودویی — از گرید کنار گذاشته می‌شود (نه درست، نه غلط؛ §۷ سند مأموریت v4.1).
_FALSY = {"0", "false", "no", "miss", "wrong"}


# ── فلگ ──────────────────────────────────────────────────────────────────────
def _flag_on() -> bool:
    v = str(os.environ.get(FLAG, "")).strip().lower()
    return v not in ("", "0", "false", "no", "off")


def _by_cycle_on() -> bool:
    """کلیدِ حقیقت = (پیشنهاد + دور)؟ خاموش/غایب = رفتارِ دیروز (last-write-wins)."""
    v = str(os.environ.get(FLAG_BY_CYCLE, "")).strip().lower()
    return v not in ("", "0", "false", "no", "off")


# ── I/O امنِ jsonl (fail-soft) ────────────────────────────────────────────────
def _read_jsonl(path: Path, tail: int = 2000) -> list[dict]:
    """خطوطِ jsonl را می‌خواند؛ نبود/خطا → [] (هرگز کرش)."""
    try:
        if not path.exists():
            return []
        rows = []
        for ln in path.read_text("utf-8", errors="replace").splitlines()[-tail:]:
            ln = ln.strip()
            if not ln:
                continue
            try:
                rec = json.loads(ln)
            except ValueError:
                continue
            if isinstance(rec, dict):
                rows.append(rec)
        return rows
    except OSError:
        return []


def _epoch(t) -> float | None:
    """یک مقدارِ زمان (float epoch یا رشتهٔ ISO) → epoch. ناموفق → None."""
    if t is None:
        return None
    if isinstance(t, (int, float)):
        return float(t)
    try:
        import datetime as _dt
        return _dt.datetime.fromisoformat(str(t)).timestamp()
    except (ValueError, TypeError):
        return None


def _ts(rec: dict) -> float | None:
    """timestampِ رکورد را به epoch تبدیل کن (float epoch یا رشتهٔ ISO). ناموفق → None."""
    return _epoch(rec.get("ts"))


def _clamp01(x: float) -> float:
    return max(0.0, min(1.0, x))


def _confidence(rec: dict) -> float | None:
    """اطمینانِ ادعا در [0,1]. فیلدِ صریح، وگرنه impact/3.0 (هم‌مقیاسِ goal_directed)."""
    for f in _CONF_FIELDS:
        if f in rec and rec[f] is not None:
            try:
                return _clamp01(float(rec[f]))
            except (ValueError, TypeError):
                continue
    if rec.get("impact") is not None:
        try:
            return _clamp01(float(rec["impact"]) / 3.0)
        except (ValueError, TypeError):
            return None
    return None


def _key(rec: dict) -> str | None:
    for f in _KEY_FIELDS:
        v = rec.get(f)
        if v is not None and str(v).strip():
            return str(v).strip()
    return None


def _binary(rec: dict) -> int | None:
    """نتیجهٔ دودوییِ حقیقتِ بیرونی (0/1) یا None اگر رکورد گرید-پذیر نباشد.

    U1: «unresolved» (مشاهدهٔ ناتمام) → None = گرید‌نشده؛ با شکست (0) یکی نمی‌شود."""
    for f in _TRUE_FIELDS:
        if f not in rec:
            continue
        v = rec[f]
        if isinstance(v, bool):
            return 1 if v else 0
        if isinstance(v, (int, float)) and v in (0, 1):
            return int(v)
        if isinstance(v, str):
            s = v.strip().lower()
            if s in _TRUTHY:
                return 1
            if s in _FALSY:
                return 0
    return None


# ── طرفِ «خود»: ادعاها ─────────────────────────────────────────────────────────
def _load_claims(within_h: float) -> list[dict]:
    """ادعاهای اخیر: {key, confidence}. بدونِ key یا بدونِ confidence → رد.
    tsِ ناخوانا → شاملِ ادعا می‌ماند (پنجرهٔ زمانی ایمنی نیست، فقط فیلترِ تازگی)."""
    cutoff = time.time() - within_h * 3600
    out = []
    for rec in _read_jsonl(CLAIMS):
        k = _key(rec)
        c = _confidence(rec)
        if k is None or c is None:
            continue
        ts = _ts(rec)
        if ts is not None and ts < cutoff:
            continue
        # `ts_epoch` افزودنی است (قراردادِ key/confidence دست‌نخورده): جفت‌سازیِ
        # دور-محور باید بداند ادعا **پیش از** کدام دور گفته شده — بدونِ آن یا
        # نگاهِ به آینده رخ می‌دهد یا یک ادعا چند بار وزن می‌گیرد.
        out.append({"key": k, "confidence": c,
                    "ts_epoch": ts if ts is not None else float("-inf")})
    return out


# ── طرفِ «گرید»: حقیقتِ بیرونی (فقط لِجِرها) ────────────────────────────────────
_CYCLE_FIELDS = ("cycle", "cycle_id", "round", "run_id")
# عمقِ خواندنِ لِجِر در مسیرِ دور-محور. چرا لازم شد (اندازه‌گیریِ ۲۰۲۶-۰۷-۲۹):
# `outcomes.jsonl` امروز ۸۱۲ ردیف است و با آهنگِ ~۱۷۸ ردیف در روز رشد می‌کند، پس
# ظرفِ ~۷ روز از سقفِ پیش‌فرضِ tail=2000 رد می‌شود. با کلیدِ قدیمی این بی‌خطر بود
# (۸ کلید هرحال در دُم بودند)، ولی با کلیدِ (پیشنهاد+دور) هر ردیفی که از پنجره
# بیفتد یک ردیفِ حقیقتِ **از دست رفته** است — یعنی عددِ هفتگیِ مالک بی‌صدا آب
# می‌رفت. فقط مسیرِ فلگ-روشن عمیق می‌خواند؛ مسیرِ خاموش دست‌نخورده (بایت‌به‌بایت).
TRUTH_TAIL = 50_000


def _cycle(rec: dict) -> str:
    """شناسهٔ «دور» برای یک رکوردِ حقیقت.

    یافتهٔ میدانی (۲۰۲۶-۰۷-۲۹، شمارشِ کاملِ ۸۱۲ ردیفِ `cortex/outcomes.jsonl`):
    **هیچ فیلدِ cycle در این لِجِر وجود ندارد.** مجموعهٔ کلیدها دقیقاً این است —
    ts · id · title · serves_goal · impact · baseline (ردیفِ نیت) و
    ts · key · moved · kind · schema · endogenous_delta · honest (ردیفِ بستار).
    پس چیزی به نامِ cycle خوانده نمی‌شود؛ نزدیک‌ترین جایگزینِ صادق **`ts`ِ خودِ
    رکوردِ بستار** است، و این حدس نیست بلکه از سمتِ نویسنده ثابت می‌شود:
    `goal_directed._close_intents` یک بار `ts = opslib.now_iso()` می‌گیرد و همان
    مقدار را روی *همهٔ* بستارهای آن فراخوانِ `measure()` مهر می‌زند. یعنی
    «یک ts یکتا = یک فراخوانِ measure = یک دور». گواهِ تجربی: اندازهٔ دسته‌ها
    ۱ تا ۶ ردیف به‌ازای هر ts است (هم‌خوانِ `top[:3]` با/بدونِ dedupe).

    اگر روزی تولیدکننده‌ای فیلدِ صریحِ cycle بنویسد، همان ترجیح داده می‌شود.
    رکوردِ بی‌ts → رشتهٔ خالی (هم‌دستهٔ «بی‌دور») — نه دورِ ساختگی."""
    for f in _CYCLE_FIELDS:
        v = rec.get(f)
        if v is not None and str(v).strip():
            return str(v).strip()
    t = rec.get("ts")
    return str(t).strip() if t is not None and str(t).strip() else ""


def _truth_rows() -> list[dict]:
    """حقیقت به‌صورتِ **یک ردیف به‌ازای هر (پیشنهاد، دور)** — رأیِ مالک (WS-1).

    چرا: `_load_truth`ِ قدیم `truth[k] = ...` می‌کرد، پس ۲۲۴ رکوردِ حقیقت به ۸
    کلید فرومی‌ریخت و «حقیقت» به ترتیبِ نوشتن وابسته می‌شد. با کلیدِ (key, cycle)
    هر دور رأیِ خودش را نگه می‌دارد.

    تناقضِ درون-دور: ۴۱ جفتِ (key, cycle) هنوز هم y=0 و y=1 با هم دارند (زخمِ
    تاریخیِ پیش از مسلح‌شدنِ `_dedupe_intents` — تمامشان ≤ ۲۰۲۶-۰۷-۲۷ و هیچ‌کدام
    ردیفِ `honest:true` ندارند). چنین دوری **حذف** می‌شود، نه اینکه با ترتیبِ
    نوشتن حل شود: دوری که هم‌زمان «جابه‌جا شد» و «نشد» گفته، حقیقتی ندارد، و
    انتخابِ یکی از آن دو دقیقاً همان وابستگی به ترتیبِ نوشتن است که این تغییر
    برای کشتنش آمده. نبودِ شاهد، شاهدِ نبود نیست."""
    buckets: dict[tuple[str, str], dict] = {}
    for src, path in (("outcomes", OUTCOMES), ("discoveries", DISCOVERIES),
                      ("self_accuracy", SELF_ACCURACY)):
        for rec in _read_jsonl(path, tail=TRUTH_TAIL):
            k = _key(rec)
            y = _binary(rec)
            if k is None or y is None:
                continue                     # لِجِرِ توصیفیِ محض (بی-key/بی-نتیجه) → نادیده
            b = buckets.setdefault((k, _cycle(rec)), {"ys": set(), "source": src})
            b["ys"].add(y)
            b["source"] = src
    rows = []
    for (k, c), b in buckets.items():
        if len(b["ys"]) != 1:
            continue                         # دورِ خودمتناقض → گرید‌ناپذیر (حذف، نه رأی‌گیری)
        rows.append({"key": k, "cycle": c, "y": next(iter(b["ys"])),
                     "source": b["source"]})
    rows.sort(key=lambda r: (r["cycle"], r["key"]))
    return rows


def _truth_contradictions() -> int:
    """شمارِ جفت‌های (key, cycle) که حذف شدند چون درونشان y تناقض داشت."""
    buckets: dict[tuple[str, str], set] = {}
    for path in (OUTCOMES, DISCOVERIES, SELF_ACCURACY):
        for rec in _read_jsonl(path, tail=TRUTH_TAIL):
            k = _key(rec)
            y = _binary(rec)
            if k is None or y is None:
                continue
            buckets.setdefault((k, _cycle(rec)), set()).add(y)
    return sum(1 for v in buckets.values() if len(v) != 1)


def _load_truth(*, by_cycle: bool | None = None) -> dict[str, dict]:
    """نقشهٔ key → {y, source}. فقط رکوردهایی که هم key و هم نتیجهٔ دودویی دارند.

    فلگِ `CORTEX_TRUTH_BY_CYCLE` خاموش (پیش‌فرض) → رفتارِ دیروز، بایت‌به‌بایت:
    رکوردِ بعدی برای همان key قبلی را بازمی‌نویسد (تازه‌ترین حقیقت).
    فلگ روشن → ردیف‌ها با کلیدِ (key, cycle) ساخته می‌شوند و زیرِ `cycles` کنارِ
    هر key می‌نشینند؛ `y`/`source`ِ سطحِ بالا تازه‌ترین دور را نشان می‌دهد تا
    قراردادِ فراخوان‌های موجود نشکند."""
    on = _by_cycle_on() if by_cycle is None else bool(by_cycle)
    if not on:
        truth: dict[str, dict] = {}
        for src, path in (("outcomes", OUTCOMES), ("discoveries", DISCOVERIES),
                          ("self_accuracy", SELF_ACCURACY)):
            for rec in _read_jsonl(path):
                k = _key(rec)
                y = _binary(rec)
                if k is None or y is None:
                    continue                 # لِجِرِ توصیفیِ محض (بی-key/بی-نتیجه) → نادیده
                truth[k] = {"y": y, "source": src}
        return truth
    out: dict[str, dict] = {}
    for r in _truth_rows():
        e = out.setdefault(r["key"], {"y": r["y"], "source": r["source"], "cycles": []})
        e["cycles"].append({"cycle": r["cycle"], "y": r["y"]})
        e["y"] = r["y"]                      # تازه‌ترین دور (ردیف‌ها مرتب بر cycle)
        e["source"] = r["source"]
    return out


# ── متریک‌ها ──────────────────────────────────────────────────────────────────
def _brier(pairs: list[dict]) -> float | None:
    """میانگینِ (confidence − y)². خالی → None."""
    if not pairs:
        return None
    return round(sum((p["confidence"] - p["y"]) ** 2 for p in pairs) / len(pairs), 6)


def _aurc(pairs: list[dict]) -> float | None:
    """پروکسیِ AURC (ریسک-پوشش، 0/1-loss): بر حسبِ confidence نزولی مرتب کن، ریسکِ
    تجمعیِ top-k را میانگین بگیر. پایین‌تر = بهتر (مطمئن‌ها درست‌اند). خالی → None."""
    if not pairs:
        return None
    ordered = sorted(pairs, key=lambda p: -p["confidence"])
    cum_err = 0
    risks = []
    for i, p in enumerate(ordered, 1):
        cum_err += 0 if p["y"] == 1 else 1     # ادعا «درست» بود اگر y==1
        risks.append(cum_err / i)
    return round(sum(risks) / len(risks), 6)


def _abstain_below(pairs: list[dict], target: float = ABSTAIN_TARGET_ACC) -> float | None:
    """آستانهٔ خودداری: پایین‌ترین اطمینانی که مجموعهٔ نگه‌داشته (conf≥τ) هنوز دقتش
    ≥ target است، از بالا به پایین (ناحیهٔ پیوستهٔ قابل‌اعتماد از صدر).
      • خالی → None.
      • حتی صدر هم به target نرسد → کمی بالای بیشینه (یعنی «به همه شک کن»).
      • همه درست → پایین‌ترین اطمینان (خودداریِ حداقلی)."""
    if not pairs:
        return None
    confs_desc = sorted({p["confidence"] for p in pairs}, reverse=True)
    best = None
    for tau in confs_desc:
        kept = [p for p in pairs if p["confidence"] >= tau]
        acc = sum(p["y"] for p in kept) / len(kept)
        if acc >= target:
            best = tau                          # تا وقتی دقت حفظ می‌شود، τ را پایین‌تر ببر
        else:
            break                               # اولین افت → توقف (پروکسیِ ساده)
    if best is None:
        return round(min(1.0, confs_desc[0] + 0.01), 6)   # به همه شک کن
    return round(best, 6)


# ── جفت‌سازیِ دور-محور ─────────────────────────────────────────────────────────
def _pair_by_cycle(claims: list[dict]) -> tuple[list[dict], int, dict]:
    """هر ردیفِ حقیقتِ (پیشنهاد، دور) را با **آخرین ادعای پیش از آن دور** گرید کن.

    چرا این جهت و نه برعکس: ادعا در زمانِ نیت گفته می‌شود و دور بعداً بسته می‌شود،
    پس ادعا هرگز نمی‌تواند دورِ خودش را بداند — جفت‌سازی باید زمانی باشد.
      • «آخرین ادعای پیش از دور» ⇒ هیچ نگاهِ به آینده (ادعا حتماً مقدم است).
      • هر ردیفِ حقیقت **حداکثر یک بار** گرید می‌شود ⇒ تکرارِ ادعا (که در تولید
        از هر اجرای record_intent می‌آید) وزنِ Brier را جابه‌جا نمی‌کند.
      • دورِ بی‌ادعای مقدم = گرید‌نشده (نه فرضِ درست/غلط).
    ادعای بی‌tsِ خوانا epoch=-inf می‌گیرد: فقط وقتی به کار می‌آید که هیچ ادعای
    تاریخ‌دارِ مقدمی نباشد."""
    by_key: dict[str, list[dict]] = {}
    for cl in claims:
        by_key.setdefault(cl["key"], []).append(cl)
    for v in by_key.values():
        v.sort(key=lambda c: c["ts_epoch"])
    rows = _truth_rows()
    graded, used, no_claim = [], set(), 0
    for r in rows:
        cand = by_key.get(r["key"])
        if not cand:
            no_claim += 1
            continue
        cyc = _epoch(r["cycle"])
        if cyc is None:                          # دورِ بی‌زمان → آخرین ادعای همان key
            pick = cand[-1]
        else:
            prior = [c for c in cand if c["ts_epoch"] <= cyc]
            if not prior:
                no_claim += 1                    # ادعا بعد از دور گفته شده → نگاهِ به آینده
                continue
            pick = prior[-1]
        used.add(id(pick))
        graded.append({"key": r["key"], "cycle": r["cycle"],
                       "confidence": pick["confidence"], "y": r["y"],
                       "source": r["source"]})
    ungraded = sum(1 for c in claims if id(c) not in used)
    extra = {
        "pairing": "by_cycle",
        "truth_rows": len(rows),
        "truth_rows_ungraded": no_claim,
        "truth_contradictions_dropped": _truth_contradictions(),
        "truth_cycles": len({r["cycle"] for r in rows}),
        "truth_proposals": len({r["key"] for r in rows}),
    }
    return graded, ungraded, extra


# ── API ───────────────────────────────────────────────────────────────────────
def probe(within_h: float = DEFAULT_WINDOW_H, *, persist: bool | None = None,
          target_acc: float = ABSTAIN_TARGET_ACC) -> dict:
    """واسنجیِ برخط: ادعاهای اخیرِ خود را با حقیقتِ بیرونی جفت کن → Brier/AURC/آستانه.

    خروجی: {n, brier, aurc, abstain_below, graded:[...]} + شمارنده‌ها.
      n = تعدادِ ادعاهای **گرید‌شده** (جفت‌شده با لِجِرِ بیرونی).
    fail-soft: هر خطا → پیش‌فرضِ امن (n=0). نوشتن فقط اگر flag روشن (یا persist=True)."""
    safe = {"n": 0, "brier": None, "aurc": None, "abstain_below": None,
            "ungraded": 0, "target_acc": target_acc, "window_h": within_h,
            "graded": [], "ts": opslib.now_iso(), "schema": "calibration.v1",
            "truth_semantics": TRUTH_SEMANTICS}
    try:
        claims = _load_claims(within_h)
        by_cycle = _by_cycle_on()
        extra: dict = {}
        if by_cycle:
            graded, ungraded, extra = _pair_by_cycle(claims)
        else:
            truth = _load_truth()
            graded, ungraded = [], 0
            for cl in claims:
                t = truth.get(cl["key"])
                if t is None:
                    ungraded += 1               # بی‌جفت = گرید‌نشده (نه فرضِ درست/غلط)
                    continue
                graded.append({"key": cl["key"], "confidence": cl["confidence"],
                               "y": t["y"], "source": t["source"]})
        truth = _load_truth()
        result = {
            "ts": opslib.now_iso(), "schema": "calibration.v1",
            "truth_semantics": TRUTH_SEMANTICS,
            "n": len(graded),
            "brier": _brier(graded),
            "aurc": _aurc(graded),
            "abstain_below": _abstain_below(graded, target_acc),
            "ungraded": ungraded,
            "target_acc": target_acc,
            "window_h": within_h,
            "n_claims": len(claims),
            "n_truth_keys": len(truth),
            # WS-B: کوریِ جفت‌سازی باید *دیده* شود نه فقط شمرده. تا امروز `ungraded`
            # یک عددِ بی‌نام بود و کسی نمی‌فهمید کدام keyها هرگز حقیقت پیدا نمی‌کنند
            # (مثلِ `self_model.coherence` که هیچ لِجِری آن را نمی‌بندد).
            "ungraded_keys": sorted({c["key"] for c in claims
                                     if c["key"] not in truth})[:20],
            # ادعای تکراریِ یک key (هر دورِ improve یک ردیفِ نو) وزنِ Brier را جابه‌جا
            # می‌کند؛ فاصلهٔ n با n_claim_keys همان وزن‌دهی را قابلِ‌سنجش می‌کند.
            "n_claim_keys": len({c["key"] for c in claims}),
            "graded": graded[:MAX_GRADED],
        }
        result.update(extra)                    # WS-1: شمارنده‌های دور-محور (فلگ روشن)
    except Exception as e:  # noqa: BLE001 — مشاهده هرگز مصرف‌کننده را نمی‌کشد
        try:
            opslib.alert([f"calibration_probe failed: {e}"])
        except Exception:  # noqa: BLE001
            pass
        return safe

    do_write = _flag_on() if persist is None else bool(persist)
    if do_write:
        _persist(result)
    return result


def _persist(result: dict) -> None:
    """رکوردِ فراشناختی را فقط زیرِ STATE_DIR بنویس. fail-soft (کرش نکن)."""
    try:
        LATEST.parent.mkdir(parents=True, exist_ok=True)
        snap = {k: v for k, v in result.items() if k != "graded"}   # کوچک و بی‌فهرست
        with opslib.LockedJson(LATEST) as lj:
            lj.write(snap)
        opslib.append_jsonl(HISTORY, snap)
    except Exception as e:  # noqa: BLE001
        try:
            opslib.alert([f"calibration_probe persist failed: {e}"])
        except Exception:  # noqa: BLE001
            pass


if __name__ == "__main__":
    print(json.dumps(probe(), ensure_ascii=False, indent=2))