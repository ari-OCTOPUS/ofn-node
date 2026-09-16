"""
brain/frontier.py — مرزِ دانش (Knowledge Frontier).

آرشیوِ کیفیت-تنوع (quality-diversity, به‌سبکِ MAP-Elites): هر کشف را بر اساسِ
«نشانگرِ رفتاری‌اش» در یک خانه (cell) قرار می‌دهد و فقط بهترینِ هر خانه را نگه می‌دارد.

نشانگرِ رفتاری = (خانواده‌ی منبع، باندِ MI، باندِ ρ، تشخیص‌پذیری)

«پوششِ مرز» (coverage) = تعدادِ خانه‌های کشف‌شده. رشدِ این عدد = پیشرفتِ **واقعی و
انباشتی** — نه یک نمره‌ی سقف‌دار. چون:
  • کشفِ ناحیه‌ی نو ⇒ پوشش +۱ (پاداشِ تازگی)
  • کشفِ دوباره‌ی چیزِ بلدشده ⇒ صفر (ضدِ «چرخ را دوباره اختراع کردن»)
  • بهبودِ بهترینِ یک خانه ⇒ عمقِ بیشتر (کیفیت در کنارِ تنوع)

حافظه کران‌دار است (تعدادِ خانه‌ها متناهی‌ست؛ per-cell فقط خلاصه ذخیره می‌شود).
"""
from __future__ import annotations

import os
import json
import copy
import math
import logging
from pathlib import Path
from datetime import datetime

from brain import guardrails

logger = logging.getLogger(__name__)

# لبه‌های باندبندی — دو محورِ رفتاریِ **مستقل**:
#   ρ  = حافظه/خودهمبستگی
#   کشیدگی = شکلِ توزیع (غیرگوسی‌بودن) — مستقل از ρ
# محورِ MI حذف شد چون تابعِ قطعیِ ρ بود (temporal_mi = -½ln(1-ρ²)) و فضا را زائد می‌کرد.
RHO_EDGES = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]     # → 10 باند
KURT_EDGES = [-0.5, 0.5, 1.5, 3.0, 6.0, 12.0]                 # → 7 باند (زیرگوسی..دُم‌سنگین)
SOURCE_FAMILIES = ["synthetic", "physical", "real", "other"]

# سقفِ نظریِ خانه‌ها (مخرجِ نمایشِ پیشرفت)
TOTAL_CELLS = len(SOURCE_FAMILIES) * (len(RHO_EDGES) + 1) * (len(KURT_EDGES) + 1) * 2


def _frontier_path() -> Path:
    from config.settings import OUTPUT_DIR
    return OUTPUT_DIR / "self_evolved" / "frontier.json"


def _band(value: float, edges: list[float], signed: bool = False) -> int:
    """اندیسِ باندِ یک مقدار (۰..len(edges)).

    signed=True برای محورهایی که لبه‌ی منفی دارند (مثل کشیدگی: لبه‌ی -۰٫۵ برای
    زیرگوسی). قبلاً abs() روی همه اعمال می‌شد → باندِ ۰ کشیدگی دست‌نیافتنی بود و
    سریِ زیرگوسی (kurt=-۰٫۶) با فوق‌گوسی (kurt=+۰٫۶) در یک خانه می‌افتاد.
    """
    v = float(value) if signed else abs(float(value))
    for i, e in enumerate(edges):
        if v < e:
            return i
    return len(edges)


def _family(source: str) -> str:
    fam = str(source).split(":", 1)[0].strip().lower()
    return fam if fam in SOURCE_FAMILIES else "other"


def cell_key(source: str, rho: float, kurt: float, detectable: bool) -> str:
    """کلیدِ خانه‌ی رفتاری — دو محورِ مستقل (ρ، کشیدگی) + خانواده + تشخیص."""
    return (f"{_family(source)}|rho{_band(rho, RHO_EDGES)}"
            f"|k{_band(kurt, KURT_EDGES, signed=True)}|d{int(bool(detectable))}")


# ════════════════════════════════════════════════════════════════════════
#  بارگذاری / ذخیره
# ════════════════════════════════════════════════════════════════════════

def load_frontier() -> dict:
    path = _frontier_path()
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:
        # فایلِ اصلی خراب/نیمه‌نوشته است — از backup بازیابی کن (نه صفرکردنِ خاموش)
        logger.error("load_frontier failed (%s); trying backup", e)
        bak = path.parent / (path.name + ".bak")
        if bak.exists():
            try:
                return json.loads(bak.read_text(encoding="utf-8"))
            except Exception:
                pass
        return {}


def _save_frontier(archive: dict) -> bool:
    path = _frontier_path()
    ok, reason = guardrails.assert_safe_write(path)
    if not ok:
        logger.error("guardrails BLOCKED frontier write: %s", reason)
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    # backup نسخه‌ی سالمِ فعلی قبل از بازنویسی
    if path.exists():
        try:
            (path.parent / (path.name + ".bak")).write_text(
                path.read_text(encoding="utf-8"), encoding="utf-8")
        except Exception:
            pass
    # نوشتنِ اتمیک: temp + os.replace (جلوگیری از خواندنِ نیمه‌کاره / از‌دست‌رفتنِ پوشش)
    tmp = path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(archive, ensure_ascii=False, indent=1), encoding="utf-8")
    os.replace(tmp, path)
    return True


# ════════════════════════════════════════════════════════════════════════
#  ثبت و اندازه‌گیری
# ════════════════════════════════════════════════════════════════════════

def record(source: str, mi: float, rho: float, kurt: float, detectable: bool,
           archive: dict | None = None, persist: bool = True) -> dict:
    """
    ثبتِ یک کشف در مرز. بهترینِ هر خانه (بیشترین MI) نگه داشته می‌شود.
    برمی‌گرداند: {new_cell, improved, key}
    """
    # گاردِ محدودبودن — مقادیرِ NaN/inf ثبت نمی‌شوند (وگرنه JSON نامعتبر و خانه‌ی قفل)
    if not (math.isfinite(mi) and math.isfinite(rho) and math.isfinite(kurt)):
        return {"new_cell": False, "improved": False, "key": None}

    own = archive is None
    if own:
        archive = load_frontier()

    key = cell_key(source, rho, kurt, detectable)
    mi = float(mi)
    res = {"new_cell": False, "improved": False, "key": key}

    if key not in archive:
        archive[key] = {"best_mi": mi, "best_rho": float(rho), "best_kurt": float(kurt),
                        "count": 1, "source": source,
                        "first_seen": datetime.now().isoformat(timespec="seconds")}
        res["new_cell"] = True
    else:
        cell = archive[key]
        cell["count"] = cell.get("count", 0) + 1
        if mi > cell.get("best_mi", float("-inf")):
            cell["best_mi"] = mi
            cell["best_rho"] = float(rho)
            cell["best_kurt"] = float(kurt)
            cell["source"] = source
            res["improved"] = True

    if own and persist:
        _save_frontier(archive)
    return res


def novelty_gain(batch: list[tuple]) -> dict:
    """
    ارزیابیِ خشکِ (dry-run) یک دسته کشف در برابرِ مرزِ فعلی — بدونِ نوشتن.

    batch: لیستی از (source, mi, rho, kurt, detectable)
    برمی‌گرداند: {new_cells, improved, distinct, open_score}
    """
    archive = load_frontier()
    working = copy.deepcopy(archive)
    seen_in_batch = set()
    new_cells = 0
    improved = 0

    for source, mi, rho, kurt, det in batch:
        if not (math.isfinite(mi) and math.isfinite(rho) and math.isfinite(kurt)):
            continue
        key = cell_key(source, rho, kurt, det)
        seen_in_batch.add(key)
        if key not in working:
            working[key] = {"best_mi": float(mi)}
            new_cells += 1
        elif float(mi) > working[key].get("best_mi", float("-inf")):
            working[key]["best_mi"] = float(mi)
            improved += 1

    distinct = len(seen_in_batch)
    # نمره‌ی هدف = فقط تازگیِ واقعی (خانه‌ی نو / بهبود). کشفِ دوباره‌ی خانه‌ی بلدشده
    # هیچ پاداشی ندارد — «چرخ را دوباره اختراع نکن».
    open_score = 2.0 * new_cells + 0.5 * improved
    return {"new_cells": new_cells, "improved": improved,
            "distinct": distinct, "open_score": open_score}


def coverage() -> int:
    return len(load_frontier())


def stats() -> dict:
    archive = load_frontier()
    cov = len(archive)
    best_mi = max((c.get("best_mi", 0.0) for c in archive.values()), default=0.0)
    total_hits = sum(c.get("count", 0) for c in archive.values())
    return {
        "coverage": cov,
        "total_cells": TOTAL_CELLS,
        "best_mi": best_mi,
        "total_discoveries": total_hits,
        "coverage_pct": round(100.0 * cov / max(TOTAL_CELLS, 1), 1),
    }


def clear() -> int:
    n = coverage()
    p = _frontier_path()
    if p.exists():
        p.unlink()
    return n


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    clear()
    print("TOTAL_CELLS:", TOTAL_CELLS)
    print(record("physical:Lorenz", 0.87, 0.6, 2.0, True))
    print(record("physical:Lorenz", 0.90, 0.6, 2.0, True))    # improved (same cell)
    print(record("real:S&P500", 0.02, -0.06, 5.0, True))      # new cell (real, fat-tailed)
    print("coverage:", coverage(), "stats:", stats())
    print("novelty of a new batch:",
          novelty_gain([("real:BTC", 0.01, 0.05, 9.0, True),
                        ("synthetic:Gaussian", 0.0001, 0.0, 0.0, False)]))
