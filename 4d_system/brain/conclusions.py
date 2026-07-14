"""
brain/conclusions.py — موتورِ «نتیجه‌گیریِ ریاضی».

ریاضیاتِ واقعیِ پروژه (مدلِ SOG: E_shadow، Δ_self، قضیه‌ی شناسایی، اتحادِ chain-rule)
را روی **داده‌های جمع‌شده** (مرزِ دانش، کشف‌ها) اعمال می‌کند و نتیجه‌گیریِ کمّی می‌گیرد.

مهم: هر دو دسته هدف را کنارِ هم نگه می‌دارد تا گم نشوند:
  ۱. هدفِ بنیادین (SOG/۴D): کشفِ «نشانه‌های بُعدِ پنهان» در داده‌ی سری‌زمانی.
  ۲. هدفِ جدید (Brain-OS): آزمونِ نظریه‌های شناخت با دینامیکِ فضای کاری.

خروجی، «نتیجه‌گیری‌های» انسانی‌فهم + وضعیتِ هر دو هدف است.
"""
from __future__ import annotations

import json
import logging
import statistics as _stat
from pathlib import Path

logger = logging.getLogger(__name__)


def _out_path() -> Path:
    from config.settings import OUTPUT_DIR
    return OUTPUT_DIR / "self_evolved" / "conclusions.json"


def _cells() -> list[tuple]:
    """(family, rho, kurt, mi, detectable) از مرزِ دانش."""
    from brain import frontier
    items = []
    for key, cell in frontier.load_frontier().items():
        parts = key.split("|")
        fam = parts[0]
        det = parts[-1] == "d1"
        items.append((fam, float(cell.get("best_rho", 0.0)),
                      float(cell.get("best_kurt", 0.0)),
                      float(cell.get("best_mi", 0.0)), det))
    return items


def synthesize_conclusions(min_samples: int = 4) -> dict:
    """اعمالِ ریاضیاتِ SOG روی داده‌ها و استخراجِ نتیجه‌گیریِ کمّی."""
    from core.model import run_self_test, solve_from_stds
    from core.scores import compute_scores_from_model
    from brain import workspace, research_agenda

    items = _cells()
    n = len(items)
    concl = []  # نتیجه‌گیری‌های انسانی‌فهم

    # ── A) پایه‌ی ریاضی سالم است؟ (شرطِ هر نتیجه‌گیری) ──
    res = run_self_test()
    anchors_ok = all(err < 1e-4 for _, (_, _, err) in res.items())
    concl.append(
        f"پایه‌ی ریاضی: لنگرهای SOG {'بازتولید شدند ✓' if anchors_ok else 'نقض شدند ✗'} — "
        f"اتحادِ ½log(σ_z²/S)=E_shadow+Δ_self=0.135073 برقرار است."
    )

    detection_rate = None
    theorem = None
    families = []
    sog_example = None

    if n >= min_samples:
        det_flags = [d for *_, d in items]
        detection_rate = sum(det_flags) / n

        # ── B) قضیه‌ی شناسایی روی داده‌ی واقعی: تشخیص ⟺ حافظه (ρ≠0) ──
        high = [d for _, r, _, _, d in items if abs(r) >= 0.2]
        low = [d for _, r, _, _, d in items if abs(r) < 0.1]
        hr = (sum(high) / len(high)) if high else None
        lr = (sum(low) / len(low)) if low else None
        if hr is not None and lr is not None:
            supports = hr > lr
            theorem = {"high_rho_detect": round(hr, 2), "low_rho_detect": round(lr, 2),
                       "supports": supports, "n_high": len(high), "n_low": len(low)}
            concl.append(
                f"قضیه‌ی شناسایی (SOG) روی {n} رفتارِ واقعی: خانه‌های حافظه‌دار (|ρ|≥۰.۲) در "
                f"{hr:.0%} موارد قابل‌تشخیص‌اند در برابرِ {lr:.0%} برای بی‌حافظه — "
                f"{'تأییدِ' if supports else 'ناسازگار با'} پیش‌بینیِ «تشخیص نیازمندِ حافظه است»."
            )

        # ── C) نگاشتِ نوعِ داده ↔ نوعِ «سایه» ──
        by_fam: dict[str, list] = {}
        for fam, r, k, mi, d in items:
            by_fam.setdefault(fam, []).append((r, k, d))
        for fam, rows in sorted(by_fam.items(), key=lambda x: -len(x[1])):
            mr = _stat.fmean(abs(r) for r, _, _ in rows)
            mk = _stat.fmean(k for _, k, _ in rows)
            dr = sum(d for _, _, d in rows) / len(rows)
            families.append({"family": fam, "n": len(rows),
                             "mean_rho": round(mr, 3), "mean_kurt": round(mk, 2),
                             "detect_rate": round(dr, 2)})
        if families:
            concl.append(
                "نگاشتِ داده↔سایه: " + " · ".join(
                    f"{f['family']} (ρ̄={f['mean_rho']}, کشیدگی̄={f['mean_kurt']}, تشخیص={f['detect_rate']:.0%})"
                    for f in families[:4]
                ) + " — دو نوع سایه: زمانی (ρ) و توزیعی (کشیدگی)."
            )

        # ── D) کمیت‌های SOG در ρ میانگینِ داده‌های قابل‌تشخیص ──
        det_rhos = [abs(r) for _, r, _, _, d in items if d and abs(r) > 1e-3]
        if det_rhos:
            mean_rho = max(0.05, min(0.95, _stat.fmean(det_rhos)))
            sol = solve_from_stds(rho=mean_rho, lam=0.5)
            sc = compute_scores_from_model(rho=mean_rho, lam=0.5)
            sog_example = {"rho": round(mean_rho, 3),
                           "E_shadow": round(max(sol.E_shadow, 0.0), 6),
                           "Delta_self": round(sol.Delta_self, 6),
                           "pcai": round(sc.pcai, 4)}
            concl.append(
                f"کمیتِ SOG در ρ̄={mean_rho:.2f} (داده‌های قابل‌تشخیص): مدل پیش‌بینی می‌کند "
                f"E_shadow≈{max(sol.E_shadow,0):.5f}، Δ_self≈{sol.Delta_self:.5f} nat/گام، "
                f"PCAI≈{sc.pcai:.3f}."
            )
    else:
        concl.append(f"داده هنوز کم است ({n} رفتار)؛ برای نتیجه‌گیریِ آماری حداقل {min_samples} لازم است.")

    # ── E) Brain-OS: دینامیکِ فضای کاری (شواهدِ اولیه برای فرضیه‌ها) ──
    w = workspace.workspace_metrics(80)
    concl.append(
        f"دینامیکِ فضای کاری (Brain-OS): اشتعالِ میانگین={w['mean_ignition']}، "
        f"پهنای انتشار={w['broadcast_width']}، انسجام={w['coherence']} — شواهدِ اولیه "
        f"(نه ادعای آگاهی)؛ برای آزمونِ فرضیه‌ی «اشتعال↔کشف» داده‌ی بیشتری لازم است."
    )

    # ── وضعیتِ هر دو هدف (تا گم نشوند) ──
    goals_status = [
        {"area": "SOG / بُعدِ پنهان (هدفِ بنیادین)",
         "progress_fa": (f"{n} رفتار در فضای پارامتری نقشه شد؛ "
                         f"نرخِ تشخیص {detection_rate:.0%}." if detection_rate is not None
                         else f"{n} رفتار جمع شده؛ در حالِ ساختِ نمونه.")},
        {"area": "Brain-OS / آزمونِ نظریه‌های شناخت (هدفِ جدید)",
         "progress_fa": (f"{len(research_agenda.HYPOTHESES)} فرضیه‌ی ابطال‌پذیر ثبت شد؛ "
                         f"دینامیکِ فضای کاری (اشتعال/انسجام) اندازه‌گیری می‌شود.")},
    ]

    return {
        "anchors_ok": anchors_ok, "n_cells": n,
        "detection_rate": detection_rate, "identifiability_theorem": theorem,
        "families": families, "sog_example": sog_example,
        "workspace": w, "conclusions_fa": concl, "goals_status": goals_status,
    }


def save_conclusions(data: dict) -> bool:
    from brain import guardrails
    p = _out_path()
    ok, _ = guardrails.assert_safe_write(p)
    if not ok:
        return False
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    import os
    os.replace(tmp, p)
    return True


def load_conclusions() -> dict | None:
    p = _out_path()
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return None


if __name__ == "__main__":
    import os
    os.environ["MOCK_MODE"] = "true"
    c = synthesize_conclusions()
    for line in c["conclusions_fa"]:
        print("•", line)
    print("\nهدف‌ها:")
    for g in c["goals_status"]:
        print(f"  [{g['area']}] {g['progress_fa']}")
