"""
brain/self_evolve.py — خودتحولِ راستی‌آزمایی‌شده («اول تست، بعد تغییر»).

سیستم «کدِ رفتاریِ خودش» را عوض می‌کند — استراتژی، سیاستِ کاوش، و وزن‌های فرمولِ
«قابل‌توجه‌بودن» — ولی هر تغییر پیش از اعمال از یک گیتِ آزمون عبور می‌کند:

  ۱. فرمول‌های ریاضی: لنگرهای core باید بازتولید شوند (run_self_test).
  ۲. تجربه:          کاندیدا در چند آزمایشِ واقعی اجرا و سنجیده می‌شود.
  ۳. سلامتِ سیستم:   check_invariants (ثابت‌های سخت).
  ۴. عدمِ پس‌رفت:    fitnessِ کاندیدا نباید بدتر از خط‌مبنا باشد.

اگر پاس شد → با پشتیبان‌گیری اعمال می‌شود؛ اگر نه → rollback و ثبتِ دلیل.

ایمنی (پرریسک ولی محافظت‌شده):
  • هرگز کدِ منبعِ *.py را exec یا ویرایش نمی‌کند.
  • استراتژی فقط داده‌ی ساختاریافته (JSON) است، نه Pythonِ اجراشونده.
  • نوشتن فقط در sandbox (outputs/self_evolved/) و از میانِ guardrails.
"""
from __future__ import annotations

import json
import copy
import random
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional

from brain import guardrails

logger = logging.getLogger(__name__)


def _sandbox_dir() -> Path:
    from config.settings import OUTPUT_DIR
    return OUTPUT_DIR / "self_evolved"


STRATEGY_NAME = "strategy.json"
BACKUP_NAME = "strategy.backup.json"


# استراتژیِ رفتاریِ پیش‌فرض — «کدِ» قابلِ تحولِ سیستم
DEFAULT_STRATEGY: dict = {
    "novelty_threshold": 0.85,
    "rho_bias": 0.50,
    "creativity": 0.50,
    "explore_points": 3000,
    "source_policy": ["synthetic", "physical", "synthetic", "physical"],
    "notable_weights": {"mi": 0.60, "rho": 0.40},   # فرمولِ «قابل‌توجه‌بودن»
    "_fitness": None,                               # آخرین fitnessِ تاییدشده
    "_generation": 0,                               # نسلِ تحول
}

_SOURCE_MENU = ["synthetic", "physical"]


# ════════════════════════════════════════════════════════════════════════
#  بارگذاری / ذخیره (sandbox + guardrails + backup)
# ════════════════════════════════════════════════════════════════════════

def load_strategy() -> dict:
    """بارگذاریِ استراتژیِ فعلی (یا پیش‌فرض اگر نبود)."""
    path = _sandbox_dir() / STRATEGY_NAME
    if not path.exists():
        return copy.deepcopy(DEFAULT_STRATEGY)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        merged = copy.deepcopy(DEFAULT_STRATEGY)
        merged.update({k: v for k, v in data.items() if k in DEFAULT_STRATEGY})
        return merged
    except Exception as e:
        logger.error("load_strategy failed, using default: %s", e)
        return copy.deepcopy(DEFAULT_STRATEGY)


def _save_json(path: Path, data: dict) -> tuple[bool, str]:
    # C1 fix: نوشتنِ اتمیک با guardrail — جایگزینِ write_textِ بی‌قفل.
    # atomic_write_json خودش assert_safe_write را صدا می‌زند.
    from brain._io_utils import atomic_write_json
    ok = atomic_write_json(path, data, indent=2)
    if not ok:
        return False, "guardrail رد کرد یا خطای نوشتن"
    return True, "ذخیره شد"


def save_strategy(strategy: dict, backup_current: bool = True) -> tuple[bool, str]:
    """
    ذخیره‌ی استراتژیِ جدید. قبلش نسخه‌ی فعلی را backup می‌گیرد (rollbackِ ممکن).

    C1 fix: کلِ عملیاتِ backup+save داخلِ file_lock اجرا می‌شود تا daemon
    و dashboard همزمان نتوانند آخرین‌نویسنده-می‌برد کنند یا JSON را فاسد کنند.
    """
    from brain._io_utils import file_lock
    d = _sandbox_dir()
    target = d / STRATEGY_NAME
    with file_lock(target):
        if backup_current:
            cur = d / STRATEGY_NAME
            if cur.exists():
                try:
                    _save_json(d / BACKUP_NAME, json.loads(cur.read_text(encoding="utf-8")))
                except Exception as e:
                    logger.warning("backup failed (continuing): %s", e)
        return _save_json(d / STRATEGY_NAME, strategy)


def rollback() -> bool:
    """بازگردانی به آخرین backup (داخلِ file_lock — C1 fix)."""
    from brain._io_utils import file_lock
    d = _sandbox_dir()
    bak = d / BACKUP_NAME
    if not bak.exists():
        return False
    target = d / STRATEGY_NAME
    with file_lock(target):
        try:
            data = json.loads(bak.read_text(encoding="utf-8"))
            _save_json(d / STRATEGY_NAME, data)
            return True
        except Exception as e:
            logger.error("rollback failed: %s", e)
            return False


# ════════════════════════════════════════════════════════════════════════
#  پیشنهادِ تغییر (bolder از mutateِ کوچک)
# ════════════════════════════════════════════════════════════════════════

def propose(current: dict, seed: int = 0) -> tuple[dict, str]:
    """
    یک کاندیدای تحول تولید می‌کند (تغییرِ ساختاری‌تر). فقط داده — بدونِ کد.
    برمی‌گرداند: (کاندیدا, توضیحِ تغییر)
    """
    rng = random.Random(seed * 977 + 13)
    cand = copy.deepcopy(current)
    # فقط ابعادی که آزمونِ تجربی واقعاً آن‌ها را اعمال می‌کند (explore_points, source_policy).
    # باقیِ پارامترها (novelty_threshold/rho_bias/creativity) روی نتیجه‌ی آزمون اثر ندارند،
    # پس اینجا تغییر داده نمی‌شوند تا تحول رد-تمبرِ کور نشود — آن‌ها را mutateِ درون‌جلسه‌ای تنظیم می‌کند.
    dim = rng.choice(["explore_points", "source_policy"])

    if dim == "explore_points":
        factor = rng.choice([0.6, 0.8, 1.25, 1.5])
        new = int(guardrails.clamp_param("explore_points", current["explore_points"] * factor))
        cand["explore_points"] = new
        desc = f"explore_points × {factor} → {new}"

    elif dim == "source_policy":
        # سیاستِ منبع را بازچینی/بازوزن کن
        k = rng.randint(3, 5)
        cand["source_policy"] = [rng.choice(_SOURCE_MENU) for _ in range(k)]
        desc = f"source_policy → {cand['source_policy']}"

    elif dim == "notable_weights":
        mi = round(rng.uniform(0.2, 0.9), 2)
        cand["notable_weights"] = {"mi": mi, "rho": round(1 - mi, 2)}
        desc = f"فرمولِ توجه: mi={mi}, rho={round(1-mi,2)}"

    else:  # پارامترهای عددیِ محدودشده
        step = rng.choice([-0.15, -0.1, 0.1, 0.15])
        ok, safe, _ = guardrails.guard_param_change(dim, current[dim], current[dim] + step)
        cand[dim] = safe if ok else current[dim]
        desc = f"{dim}: {current[dim]:.2f} → {cand[dim]:.2f}"

    return cand, desc


# ════════════════════════════════════════════════════════════════════════
#  گیتِ آزمون — «اول تست»
# ════════════════════════════════════════════════════════════════════════

def test_candidate(candidate: dict, n_experiments: int = 4) -> dict:
    """
    آزمونِ کاندیدا پیش از هر اعمال:
      ۱. لنگرهای ریاضی (فرمول‌ها)
      ۲. آزمایش‌های واقعی (تجربه) با استراتژیِ کاندیدا
      ۳. سلامتِ سیستم (ثابت‌ها)
    برمی‌گرداند dict شاملِ passed و fitness و گزارش.
    """
    report = {"anchors_ok": False, "invariants_ok": False,
              "valid_fraction": 0.0, "detect_fraction": 0.0,
              "errors": 0, "fitness": 0.0, "passed": False, "reason": "",
              "open_score": 0.0, "new_cells": 0, "distinct": 0}

    # ۱. فرمول‌های ریاضی — لنگرهای core
    try:
        from core.model import run_self_test
        res = run_self_test()
        report["anchors_ok"] = all(err < 1e-4 for _, (_, _, err) in res.items())
    except Exception as e:
        report["reason"] = f"anchor test error: {e}"
        return report
    if not report["anchors_ok"]:
        report["reason"] = "لنگرهای ریاضی بازتولید نشدند"
        return report

    # ۲. تجربه — اجرای واقعیِ آزمایش‌ها با استراتژیِ کاندیدا (بدونِ ذخیره)
    try:
        from brain.autoloop import AutoLoopEngine, AutoLoopConfig
        cfg = AutoLoopConfig(
            auto_save=False, use_llm=False,
            explore_points=int(candidate.get("explore_points", 3000)),
            sources=list(candidate.get("source_policy",
                                       DEFAULT_STRATEGY["source_policy"])),
        )
        eng = AutoLoopEngine(cfg)
        valid = 0
        detect = 0
        batch = []                     # (source, mi, rho, detectable) برای سنجشِ تازگی
        for i in range(n_experiments):
            r = eng.run_step(i, past_results=eng.history)
            if r.source == "error":
                report["errors"] += 1
                continue
            mi = r.scores.get("temporal_mi", 0.0)
            import math
            if math.isfinite(mi) and r.series_stats.get("n", 0) >= 20:
                valid += 1
                det = bool(r.scores.get("detectable"))
                if det:
                    detect += 1
                batch.append((r.source, mi, r.scores.get("rho_hat", 0.0),
                              r.scores.get("kurtosis", 0.0), det))
        report["valid_fraction"] = valid / n_experiments
        report["detect_fraction"] = detect / max(valid, 1)

        # هدفِ باز: تازگی نسبت به مرزِ دانش (سقف‌ناپذیر، ضدِ تکرار)
        from brain import frontier
        nov = frontier.novelty_gain(batch)
        report["open_score"] = nov["open_score"]
        report["new_cells"] = nov["new_cells"]
        report["distinct"] = nov["distinct"]
    except Exception as e:
        report["reason"] = f"experiment error: {type(e).__name__}: {e}"
        report["errors"] += 1
        return report

    # ۳. سلامتِ سیستم — ثابت‌های سخت
    inv = guardrails.check_invariants()
    report["invariants_ok"] = inv["anchors_ok"]

    # نمره‌ی برازش: اعتبار مهم‌تر است؛ کیفیتِ تشخیص امتیازِ افزوده
    report["fitness"] = report["valid_fraction"] * (0.6 + 0.4 * report["detect_fraction"])

    report["passed"] = (
        report["anchors_ok"]
        and report["invariants_ok"]
        and report["errors"] == 0
        and report["valid_fraction"] >= 1.0     # هیچ آزمایشی نباید نامعتبر باشد
    )
    report["reason"] = "پاس" if report["passed"] else "آزمونِ تجربی/ثابت‌ها پاس نشد"
    return report


# ════════════════════════════════════════════════════════════════════════
#  حلقه‌ی تحول — «اول تست، بعد تغییر یا بازگردانی»
# ════════════════════════════════════════════════════════════════════════


def _reject_reason(cand_score: float, baseline: float) -> str:
    """Q3b (OWNER-QUEUE-RESOLUTION §Q3): پیامِ ردِ صادقانه — گیت «اکیداً بیشتر»
    عمدی است (تساوی رد می‌شود)؛ پیامِ قبلی برای حالتِ تساوی دروغ می‌گفت («کمتر»)."""
    if cand_score == baseline:
        return (f"رد شد — تازگیِ بدونِ بهبود (برابر: {cand_score:.1f} == {baseline:.1f}؛ "
                f"گیتِ پذیرش اکیداً-بیشتر است)")
    return f"رد شد — تازگیِ کمتر ({cand_score:.1f} < {baseline:.1f})"


def evolve(seed: int = 0, n_experiments: int = 4, apply: bool = True) -> dict:
    """
    یک گامِ خودتحولِ راستی‌آزمایی‌شده با هدفِ **باز** (تازگی، نه نمره‌ی سقف‌دار).

    A/B: استراتژیِ فعلی و کاندیدا هر دو تازه سنجیده می‌شوند؛ کاندیدا اعمال می‌شود اگر
    ایمن باشد (لنگرها + تجربه‌ی معتبر) و در کشفِ **نواحیِ تازه** بهتر یا هم‌سطحِ فعلی باشد.
    چون معیار «تازگی نسبت به مرزِ دانش» است، هیچ سقفی ندارد و تکرار پاداش نمی‌گیرد.
    """
    current = load_strategy()

    # A/B منصفانه: هر دو در برابرِ مرزِ فعلی سنجیده می‌شوند
    cur_report = test_candidate(current, n_experiments)
    candidate, desc = propose(current, seed=seed)
    cand_report = test_candidate(candidate, n_experiments)

    baseline = cur_report["open_score"] if cur_report["passed"] else 0.0
    cand_score = cand_report["open_score"]

    result = {
        "applied": False, "desc": desc,
        "open_score": cand_score, "baseline_open": baseline,
        "report": cand_report, "reason": "",
    }

    # گیتِ ایمنی برقرار است؛ معیارِ پذیرش = تازگیِ **اکیداً بیشتر** (تساوی رد-تمبر نمی‌شود)
    if cand_report["passed"] and cand_score > baseline:
        candidate["_open_score"] = cand_score
        candidate["_fitness"] = cand_report["fitness"]     # برای سازگاری
        candidate["_generation"] = int(current.get("_generation", 0)) + 1
        if not apply:
            # B9 (فلگِ اختیاری، پیش‌فرض بی‌اثر): حالتِ «پیشنهاد بدونِ اعمال» —
            # کاندیدای قبول‌شده فقط در strategy_proposed.json ثبت می‌شود تا مالک
            # تأیید کند. با apply=True (پیش‌فرض) رفتار دقیقاً مثل قبل است.
            try:
                p = _sandbox_dir() / "strategy_proposed.json"
                p.write_text(json.dumps(candidate, ensure_ascii=False, indent=1),
                             encoding="utf-8")
            except Exception as e:
                logger.warning("write strategy_proposed failed: %s", e)
            result["proposed"] = True
            result["generation"] = candidate["_generation"]
            result["reason"] = (f"پیشنهاد ثبت شد (منتظرِ تأییدِ مالک) — تازگی "
                                f"{baseline:.1f} → {cand_score:.1f}")
            return result
        ok, _ = save_strategy(candidate, backup_current=True)
        result["applied"] = ok
        result["generation"] = candidate["_generation"]
        result["reason"] = (f"اعمال شد (نسل {candidate['_generation']}, "
                            f"تازگی {baseline:.1f} → {cand_score:.1f}, "
                            f"+{cand_report['new_cells']} ناحیه)") if ok \
            else "ذخیره‌ی استراتژی مسدود شد"
    else:
        # rollback ضمنی: چیزی ننوشتیم، استراتژیِ فعلی دست‌نخورده می‌ماند
        if not cand_report["passed"]:
            result["reason"] = f"رد شد — {cand_report['reason']}"
        else:
            result["reason"] = _reject_reason(cand_score, baseline)

    return result


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    import os
    os.environ["MOCK_MODE"] = "true"
    print("current:", {k: v for k, v in load_strategy().items() if not k.startswith("_")})
    for s in range(4):
        r = evolve(seed=s, n_experiments=3)
        print(f"seed {s}: applied={r['applied']} · {r['desc']} · {r['reason']}")
    print("evolved:", {k: v for k, v in load_strategy().items()})
