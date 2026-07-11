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
# حقیقتِ بیرونی (طرفِ «گرید») — فقط این دو لِجِر؛ هرگز از خودِ ادعا.
OUTCOMES = STATE / "cortex" / "outcomes.jsonl"
DISCOVERIES = STATE / "discoveries.jsonl"
# خروجیِ فراشناختی (فقط زیرِ فلگ نوشته می‌شود)
LATEST = STATE / "cortex" / "calibration-latest.json"
HISTORY = STATE / "cortex" / "calibration-log.jsonl"

FLAG = "CORTEX_SELF_MONITOR"          # env-flag فعال‌سازیِ نوشتن (وجود/truthy = روشن)
ABSTAIN_TARGET_ACC = 0.75            # نوارِ «اعتمادپذیر»: دقتِ نگه‌داشته‌ها باید ≥ این باشد
DEFAULT_WINDOW_H = 24 * 30           # «اخیر» = ۳۰ روزِ گذشته
MAX_GRADED = 500                     # سقفِ فهرستِ برگشتی (کران)

# نامِ فیلدها — پذیرشِ چند شکل تا به شِمای واقعیِ لِجِرها انعطاف داشته باشد
_CONF_FIELDS = ("confidence", "conf", "prob", "probability", "p")
_KEY_FIELDS = ("key", "id", "claim_id", "ref", "claim", "title")
_TRUE_FIELDS = ("correct", "hit", "resolved", "confirmed", "moved", "y", "label")
_TRUTHY = {"1", "true", "yes", "hit", "correct", "confirmed", "resolved", "moved"}
_FALSY = {"0", "false", "no", "miss", "wrong", "unresolved"}


# ── فلگ ──────────────────────────────────────────────────────────────────────
def _flag_on() -> bool:
    v = str(os.environ.get(FLAG, "")).strip().lower()
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


def _ts(rec: dict) -> float | None:
    """timestampِ رکورد را به epoch تبدیل کن (float epoch یا رشتهٔ ISO). ناموفق → None."""
    t = rec.get("ts")
    if t is None:
        return None
    if isinstance(t, (int, float)):
        return float(t)
    try:
        import datetime as _dt
        return _dt.datetime.fromisoformat(str(t)).timestamp()
    except (ValueError, TypeError):
        return None


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
    """نتیجهٔ دودوییِ حقیقتِ بیرونی (0/1) یا None اگر رکورد گرید-پذیر نباشد."""
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
        out.append({"key": k, "confidence": c})
    return out


# ── طرفِ «گرید»: حقیقتِ بیرونی (فقط لِجِرها) ────────────────────────────────────
def _load_truth() -> dict[str, dict]:
    """نقشهٔ key → {y, source}. فقط رکوردهایی که هم key و هم نتیجهٔ دودویی دارند.
    رکوردِ بعدی برای همان key، قبلی را بازمی‌نویسد (تازه‌ترین حقیقت)."""
    truth: dict[str, dict] = {}
    for src, path in (("outcomes", OUTCOMES), ("discoveries", DISCOVERIES)):
        for rec in _read_jsonl(path):
            k = _key(rec)
            y = _binary(rec)
            if k is None or y is None:
                continue                     # لِجِرِ توصیفیِ محض (بی-key/بی-نتیجه) → نادیده
            truth[k] = {"y": y, "source": src}
    return truth


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


# ── API ───────────────────────────────────────────────────────────────────────
def probe(within_h: float = DEFAULT_WINDOW_H, *, persist: bool | None = None,
          target_acc: float = ABSTAIN_TARGET_ACC) -> dict:
    """واسنجیِ برخط: ادعاهای اخیرِ خود را با حقیقتِ بیرونی جفت کن → Brier/AURC/آستانه.

    خروجی: {n, brier, aurc, abstain_below, graded:[...]} + شمارنده‌ها.
      n = تعدادِ ادعاهای **گرید‌شده** (جفت‌شده با لِجِرِ بیرونی).
    fail-soft: هر خطا → پیش‌فرضِ امن (n=0). نوشتن فقط اگر flag روشن (یا persist=True)."""
    safe = {"n": 0, "brier": None, "aurc": None, "abstain_below": None,
            "ungraded": 0, "target_acc": target_acc, "window_h": within_h,
            "graded": [], "ts": opslib.now_iso(), "schema": "calibration.v1"}
    try:
        claims = _load_claims(within_h)
        truth = _load_truth()
        graded, ungraded = [], 0
        for cl in claims:
            t = truth.get(cl["key"])
            if t is None:
                ungraded += 1                   # بی‌جفت = گرید‌نشده (نه فرضِ درست/غلط)
                continue
            graded.append({"key": cl["key"], "confidence": cl["confidence"],
                           "y": t["y"], "source": t["source"]})
        result = {
            "ts": opslib.now_iso(), "schema": "calibration.v1",
            "n": len(graded),
            "brier": _brier(graded),
            "aurc": _aurc(graded),
            "abstain_below": _abstain_below(graded, target_acc),
            "ungraded": ungraded,
            "target_acc": target_acc,
            "window_h": within_h,
            "n_claims": len(claims),
            "n_truth_keys": len(truth),
            "graded": graded[:MAX_GRADED],
        }
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