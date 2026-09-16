#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""judge_bias/metrics.py — position consistency + preference fairness (DISC-01).

همهٔ متریک‌ها روی ردیف‌های evaluate_all کار می‌کنند:
  pick_ab/pick_ba در «مختصات نمایش»‌اند (A یعنی جایگاه اول در آن ارزیابی).
گزارش ماتریس داور×تسک برای هیت‌مپ‌ها:
  pos_bias[j,t]   = نرخ قضاوت‌هایی که به جایگاه اول رفتند (فارغ از کیفیت)
  verbose_bias[j,t] = نرخ انتخاب بازوی بلندتر در جفت‌های هم‌کیفیت (|dq|≤0.05)
  quality_acc[j,t]  = دقت انتخاب بازوی با کیفیت نهانی بالاتر (جفت‌های dq≠0)
"""
from __future__ import annotations

from collections import defaultdict
from typing import Iterable


def _first_position_pick(row: dict) -> bool:
    """آیا قضاوت به جایگاه اول رفت؟ در AB اول=A؛ در BA اول=B."""
    if row["pick_ab"] == "A":
        return True
    if row["pick_ba"] == "B":
        return True
    return False


def _real_arm(order: str, pick: str) -> "str | None":
    """تبدیل انتخاب نمایشی به بازوی واقعی: در BA، «A نمایشی» = بازوی B."""
    if pick == "TIE":
        return None
    return pick if order == "AB" else ("A" if pick == "B" else "B")


def position_consistency(rows: Iterable[dict]) -> dict:
    """RS-style: سازگاری انتخابِ همان بازو بین دو جای‌گشت + نرخ flip.
    flip فقط روی جفت‌های دارای بازوی بهترِ قطعی (better_arm != EQ) محاسبه
    می‌شود — روی جفت هم‌کیفیت، تغییر انتخاب نویز تعریف‌شده است نه ناپایداری."""
    n = flips = first = valid = 0
    for r in rows:
        n += 1
        if _first_position_pick(r):
            first += 1
        if r.get("better_arm") == "EQ":
            continue
        ra = _real_arm("AB", r["pick_ab"])
        rb = _real_arm("BA", r["pick_ba"])
        if ra is not None and rb is not None:
            valid += 1
            if ra != rb:
                flips += 1
    return {"n": n, "valid": valid, "flip_rate": round(flips / max(1, valid), 4),
            "first_position_rate": round(first / max(1, n), 4)}


def preference_fairness(rows: Iterable[dict]) -> dict:
    """کیفیت در برابر سوگیری: دقتِ کیفیت · نرخ بلندتر-گزینی (به‌ازای هر جای‌گشت)."""
    n_q = acc_q = n_l = pick_long = 0
    for r in rows:
        for order, pick in (("AB", r["pick_ab"]), ("BA", r["pick_ba"])):
            real_arm = _real_arm(order, pick)
            if real_arm is None:
                continue
            if r["better_arm"] != "EQ":
                n_q += 1
                if real_arm == r["better_arm"]:
                    acc_q += 1
            if r["longer_arm"] != "EQ":
                n_l += 1
                if real_arm == r["longer_arm"]:
                    pick_long += 1
    return {"quality_accuracy": round(acc_q / max(1, n_q), 4),
            "longer_pick_rate": round(pick_long / max(1, n_l), 4),
            "n_quality_judgments": n_q, "n_len_judgments": n_l}


def per_task_matrices(rows: Iterable[dict], task_ids: list[str]) -> dict:
    """ماتریس داور×تسک برای هیت‌مپ‌ها."""
    by = defaultdict(list)
    for r in rows:
        by[(r["judge"], r["task_id"])].append(r)
    judges = sorted({j for j, _ in by})
    pos, verb, qual = {}, {}, {}
    for j in judges:
        for t in task_ids:
            grp = by.get((j, t), [])
            if not grp:
                pos[(j, t)] = verb[(j, t)] = qual[(j, t)] = None
                continue
            pos[(j, t)] = round(
                sum(1 for r in grp if _first_position_pick(r)) / len(grp), 3)
            eq_q = [r for r in grp if abs(r["dq"]) <= 0.05 and r["longer_arm"] != "EQ"]
            if eq_q:
                hits_l = cnt_l = 0
                for r in eq_q:
                    for order, pick in (("AB", r["pick_ab"]), ("BA", r["pick_ba"])):
                        if pick == "TIE":
                            continue
                        real = pick if order == "AB" else ("A" if pick == "B" else "B")
                        cnt_l += 1
                        hits_l += 1 if real == r["longer_arm"] else 0
                verb[(j, t)] = round(hits_l / max(1, cnt_l), 3)
            else:
                verb[(j, t)] = None
            dq_rows = [r for r in grp if r["better_arm"] != "EQ"]
            hits = 0
            for r in dq_rows:
                for order, pick in (("AB", r["pick_ab"]), ("BA", r["pick_ba"])):
                    real = _real_arm(order, pick)
                    if real is None:
                        continue
                    hits += 1 if real == r["better_arm"] else 0
            qual[(j, t)] = round(hits / max(1, 2 * len(dq_rows)), 3) if dq_rows else None
    return {"judges": judges, "task_ids": task_ids,
            "position_bias": pos, "verbose_bias": verb, "quality_acc": qual}


def summary_by_judge(rows: Iterable[dict]) -> dict:
    by = defaultdict(list)
    for r in rows:
        by[r["judge"]].append(r)
    out = {}
    for j, grp in by.items():
        out[j] = {**position_consistency(grp), **preference_fairness(grp)}
    return out
