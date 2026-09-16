#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_evaluator_holdout — DA-1-L1 (PHASE02 STEP2).

پوشش: طلای آشکار در بسته نیست · نمره فقط تجمیعی است · بری‌ری درست محاسبه
می‌شود · نمک/هش جدا از بستهٔ عمومی · بازتولیدپذیری انجماد (seed).
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import harness  # noqa: E402

ENV = harness.setup("evaluator-holdout")
sys.path.insert(0, r"F:\backup\_ops\evaluator-holdout")

import evaluator as ev  # noqa: E402
import json  # noqa: E402


def t_no_plaintext_gold_in_bundle():
    src = (Path(r"F:\backup\_ops\evaluator-holdout\holdout_items.json")
           .read_text(encoding="utf-8"))
    items = json.loads(src)["items"]
    assert all("gold_hash" in it and "gold" not in it for it in items)
    # طلای آشکار (0/1 خام) در متن بسته نیست
    assert '"gold":' not in src


def t_score_is_aggregate_only():
    r = ev.score({it["item_id"]: 0.5 for it in ev.items_observable()})
    assert set(r.keys()) == {"n", "brier"}, r
    assert r["n"] > 0 and 0.0 <= r["brier"] <= 1.0


def t_brier_math_correct_on_known_case():
    # همه 1.0: بری‌ری = میانگین (1-y)^2 — از gold محلی برای تستِ ریاضی
    gold = json.loads((Path(r"F:\backup\_ops\evaluator-holdout")
                       / "gold.local-only.json").read_text(encoding="utf-8"))
    subs = {k: 1.0 for k in gold}
    expected = sum((1.0 - y) ** 2 for y in gold.values()) / len(gold)
    got = ev.score(subs)["brier"]
    assert abs(got - round(expected, 4)) < 1e-9, (got, expected)


def t_freeze_is_reproducible():
    import subprocess
    out = subprocess.run(
        ["py", "-X", "utf8", r"F:\backup\_ops\evaluator-holdout\build_holdout.py"],
        capture_output=True, text=True, timeout=60)
    assert "60 items از 351" in out.stdout, out.stdout + out.stderr
    # seed ثابت ⇒ همان هش‌ها
    items = json.loads((Path(r"F:\backup\_ops\evaluator-holdout")
                        / "holdout_items.json").read_text(encoding="utf-8"))["items"]
    assert items[0]["gold_hash"] and len(items) == 60


CHECKS = [
    ("طلای آشکار در بسته نیست", t_no_plaintext_gold_in_bundle),
    ("نمره فقط تجمیعی (نشت صفر)", t_score_is_aggregate_only),
    ("ریاضی بری‌ری روی مورد معلوم", t_brier_math_correct_on_known_case),
    ("انجماد بازتولیدپذیر (seed)", t_freeze_is_reproducible),
]

if __name__ == "__main__":
    failed = harness.run(CHECKS)
    sys.exit(1 if failed else 0)
