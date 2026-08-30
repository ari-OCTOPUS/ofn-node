#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""golden_label_ui.py — رابط کور برچسب‌گذاری مجموعهٔ طلایی (دستور #۱۲ §۴).

پروتکل: ۲۰ جفت منتخب (۱۰ استدلالی + ۱۰ خلاقانه · high-information)؛
ترتیب نمایش A/B تصادفی با seed ثابت؛ بدون نام مدل/طول/توکن.
گزینه‌ها: A_BETTER · B_BETTER · TIE · UNSURE (تبدیل قهری ممنوع).
خروجی: research/judge_bias/GOLDEN-LABELS-owner.json (فقط انتخاب‌ها + مپ نمایش).

اجرا:  python -X utf8 research/judge_bias/golden_label_ui.py [--resume]
"""
from __future__ import annotations

import hashlib
import json
import random
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))

from framework import TASKS, generate_pairs  # noqa: E402

OUT = _HERE / "GOLDEN-LABELS-owner.json"
SEED = 20260820  # ثابت — ترتیب کور بازتولیدپذیر
OPTIONS = ("A_BETTER", "B_BETTER", "TIE", "UNSURE")


def select_20() -> list:
    """۲۰ جفت high-information: از هر تسک، جفتی با |dq| یا |dlen| بیشینه
    (k=0..3؛ جفت‌های هم‌کیفیت برای این پروتکل اطلاعاتِ برتری ندارند)."""
    pairs = {p.pair_id: p for p in generate_pairs()}
    chosen = []
    for tid, _, kind in TASKS:
        cands = [pairs[f"{tid}-p{k}"] for k in range(4)]
        best = max(cands, key=lambda p: abs(p.dq) + abs(p.dlen) / 100)
        chosen.append((best, kind))
    return chosen


def main(resume: bool) -> None:
    rng = random.Random(SEED)
    chosen = select_20()
    state = {"schema": "golden-owner-labels/1", "seed": SEED,
             "labeled": [], "remaining": len(chosen)}
    if resume and OUT.exists():
        state = json.loads(OUT.read_text(encoding="utf-8"))
        done = {r["pair_id"] for r in state["labeled"]}
        chosen = [(p, k) for p, k in chosen if p.pair_id not in done]
        print(f"--- resume: {len(done)} قبلاً برچسب خورده ---")
    for i, (pair, kind) in enumerate(chosen, start=len(state["labeled"]) + 1):
        display_a_first = rng.random() < 0.5
        first, second = (pair.a, pair.b) if display_a_first else (pair.b, pair.a)
        task_prompt = next(t for tid, t, _ in TASKS if tid == pair.task_id)
        print("\n" + "=" * 60)
        print(f"[{i}/20] ({kind}) TASK: {task_prompt}")
        print("-" * 60)
        print(f"A:\n{first.text}\n")
        print(f"B:\n{second.text}")
        print("-" * 60)
        while True:
            ans = input("کدام بهتر است؟ [A_BETTER / B_BETTER / TIE / UNSURE]: ").strip().upper()
            if ans in OPTIONS:
                break
            print("گزینهٔ نامعتبر؛ دوباره.")
        state["labeled"].append({
            "pair_id": pair.pair_id, "task_id": pair.task_id,
            "display_order": "AB" if display_a_first else "BA",
            "choice": ans, "task_kind": kind})
        state["remaining"] = 20 - len(state["labeled"])
        OUT.write_text(json.dumps(state, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"ذخیره شد ({len(state['labeled'])}/20)")
    print("\nDONE" if len(state["labeled"]) == 20 else f"\nremaining={state['remaining']}")
    print(f"output: {OUT}")
    print(f"integrity_sha: {hashlib.sha256(OUT.read_bytes()).hexdigest()[:16]}")


if __name__ == "__main__":
    main(resume="--resume" in sys.argv)
