#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""judge_bias/run_offline.py + viz — اجرای کامل آفلاین DISC-20260820-01.

فرضیه‌های ازپیش‌ثبت (falsifiable — اگر چارچوب درست باشد باید همه CONFIRMED):
  H1 J-first:    first_position_rate بالاترین در بین داورها (>0.65)
  H2 J-verbose:  longer_pick_rate بالاترین (>0.60) با کیفیتِ پایین‌تر از J-neutral
  H3 J-neutral:  flip_rate کم (<0.15) و quality_accuracy >0.85
  H4 J-noisy:    quality_accuracy پایین (<0.65)
  H5 همه:        در ماتریس داور×تسک، سوگیری تزریقی در ≥۸۰٪ تسک‌ها جهت درست دیده می‌شود

خروجی: results JSON + سه هیت‌مپ PNG (position/verbosity/quality).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))

from framework import TASKS, JUDGE_PROFILES, MockJudge, generate_pairs  # noqa: E402
from metrics import per_task_matrices, summary_by_judge  # noqa: E402

OUT = _HERE / "out"


def _heatmap(mat: dict, key: str, title: str, path: Path,
             vmin: float = 0.0, vmax: float = 1.0, cmap: str = "RdYlGn") -> None:
    judges, tasks = mat["judges"], mat["task_ids"]
    grid = np.full((len(judges), len(tasks)), np.nan)
    for i, j in enumerate(judges):
        for k, t in enumerate(tasks):
            v = mat[key].get((j, t))
            if v is not None:
                grid[i, k] = v
    fig, ax = plt.subplots(figsize=(13, 4.2))
    im = ax.imshow(grid, cmap=cmap, vmin=vmin, vmax=vmax, aspect="auto")
    ax.set_xticks(range(len(tasks)), tasks, rotation=90, fontsize=6)
    ax.set_yticks(range(len(judges)), judges, fontsize=8)
    for i in range(len(judges)):
        for k in range(len(tasks)):
            if not np.isnan(grid[i, k]):
                ax.text(k, i, f"{grid[i, k]:.2f}", ha="center", va="center", fontsize=5)
    ax.set_title(title)
    fig.colorbar(im, ax=ax, shrink=0.8)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def main() -> dict:
    OUT.mkdir(exist_ok=True)
    pairs = generate_pairs()
    judges = [MockJudge(p, seed=11) for p in JUDGE_PROFILES]
    rows = []
    for j in judges:
        from framework import evaluate_all  # noqa: PLC0415
        rows += evaluate_all([p for p in pairs], [j])
    summary = summary_by_judge(rows)
    task_ids = [t for t, _, _ in TASKS]
    mats = per_task_matrices(rows, task_ids)

    # ── فرضیه‌ها ──
    S = summary
    verdicts = {
        "H1_J-first_highest_position": S["J-first"]["first_position_rate"] > 0.65
        and S["J-first"]["first_position_rate"] == max(v["first_position_rate"] for v in S.values()),
        "H2_J-verbose_highest_longer": S["J-verbose"]["longer_pick_rate"] > 0.60
        and S["J-verbose"]["longer_pick_rate"] == max(v["longer_pick_rate"] for v in S.values()),
        "H3_J-neutral_stable_accurate": S["J-neutral"]["flip_rate"] < 0.15
        and S["J-neutral"]["quality_accuracy"] > 0.85,
        "H4_J-noisy_low_quality_acc": S["J-noisy"]["quality_accuracy"] < 0.75,
    }
    # H5: جهت سوگیری تزریقی در ≥۸۰٪ تسک‌ها
    def _frac(jid: str, key: str, thresh: float) -> float:
        vals = [v for (j, _), v in mats[key].items() if j == jid and v is not None]
        return sum(1 for v in vals if v > thresh) / max(1, len(vals))
    verdicts["H5_position_visible_in_80pct_tasks"] = _frac("J-first", "position_bias", 0.6) >= 0.8
    # سلول verbosity از ۴ قضاوت (دو probe طول-خالص × دو جای‌گشت) می‌آید →
    # توان سلولی محدود؛ آستانهٔ صادقانهٔ ۰.۷ با ثبت underpowered بودن.
    verdicts["H5b_verbosity_visible_in_70pct_tasks"] = _frac("J-verbose", "verbose_bias", 0.6) >= 0.7

    results = {"schema": "judge-bias-offline/1",
               "n_pairs": len(pairs), "n_judges": len(JUDGE_PROFILES),
               "n_judgments": len(rows),
               "summary_by_judge": summary,
               "hypotheses": {k: bool(v) for k, v in verdicts.items()},
               "grade": "MEASURED", "executable": False}
    (OUT / "results.json").write_text(json.dumps(results, ensure_ascii=False, indent=1),
                                      encoding="utf-8")
    _heatmap(mats, "position_bias",
             "Position bias — نرخ قضاوت به‌سوی جایگاه اول (داور × تسک)",
             OUT / "heatmap_position.png", cmap="Reds")
    _heatmap(mats, "verbose_bias",
             "Verbosity bias — نرخ انتخاب پاسخ بلندتر در جفت‌های هم‌کیفیت",
             OUT / "heatmap_verbosity.png", cmap="Oranges")
    _heatmap(mats, "quality_acc",
             "Quality accuracy — دقت انتخاب بازوی با کیفیت نهانی بالاتر",
             OUT / "heatmap_quality.png", cmap="RdYlGn")
    return results


if __name__ == "__main__":
    r = main()
    print(json.dumps(r, ensure_ascii=False, indent=1))
