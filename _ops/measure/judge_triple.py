#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""judge_triple.py — K=9 سه‌بذر برای بستن D6.

Authority: PRE-REG-K9-THREE-SEED-2026-08-20 §۶ — امضاشده با رأی چت مالک
2026-08-20 (~13:50 +10:00؛ «امضا + اجرای امروز») + رأی «پین FX کن».
اجرای FX زیر پین معتبر FX-PIN-20260819-02 (تا 2026-08-20T06:00Z).

منجمد طبق کارت:
  - ابزار classify: فقط measure/swap_consistency.py (canonical؛ sha256 ثبت‌شده در
    STATE-RECHECK-2026-08-20) — تغییرش وسط سری = VOID.
  - هارنس: GATE3 منجمد + داور V3 تک‌کلیدی + fallback تک‌توکن @8؛ دومین ناخوانا = VOID.
  - بذرها: k9-triple-2026-08-20/{A,B,C} — هر بذر یک جفت NEW (temp=0).
  - هر ترتیب: ۹ معتبر هدف، حداکثر ۱۳ تلاش؛ VOID می‌سوزد.
  - سقف: ۸۰ فراخوان کل / AU$2 (سقف تماس این‌جا enforce؛ AUD توسط گیت‌های router).
  - حکم ازپیش‌ثبت: هر سه CONSISTENT و RS_BA≥۰.۹ و k=۹ → STABLE_ACROSS_SEEDS؛
    هر اختلاف/کم‌توانی → BETWEEN_RUN_VARIANCE؛ تغییر ابزار → VOID.
  - Fisher بین اجراها: دوطرفه α=۰.۰۵ (فقط گزارش؛ گیتِ حکم طبق جدول بالا).

استفاده:
  python _ops/measure/judge_triple.py --dry-run
  python _ops/measure/judge_triple.py --run
"""
from __future__ import annotations

import hashlib
import json
import math
import re
import sys
import time
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_OPS = _HERE.parent
_ROOT = _HERE.parents[1]

L4 = _ROOT / "06-EVIDENCE" / "CL01-191-20260818-2233" / "live4"
SEEDS = ("k9-triple-2026-08-20/A", "k9-triple-2026-08-20/B", "k9-triple-2026-08-20/C")
MAX_CALLS_TOTAL = 80
CAP_AUD = 2.00
TARGET_VALID = 9
MAX_ATTEMPTS_PER_ORDER = 13
OUT_DIR = _OPS / "state" / "pipeline"
EVID_DIR = _ROOT / "06-EVIDENCE" / "K9-THREE-SEED-2026-08-20"

for _p in (str(_OPS), str(_OPS / "cortex"), str(_OPS / "measure"), str(L4)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from live4_harness import load_fx, judge_choice_v3, parse_single_token, JUDGE_PROMPT_V3  # noqa: E402


def _load_q() -> str:
    src = (L4 / "live4_driver.py").read_text("utf-8")
    m = re.search(r'Q = TAX = \((.+?)\)\n', src, re.S)
    if not m:
        raise RuntimeError("Q not found in frozen driver")
    q = m.group(1).strip().strip('"')
    return re.sub(r'"\s*\n\s*"', "", q)


def _receipt(kind: str, **kw) -> None:
    row = {"schema": "k9-triple-receipt/1", "kind": kind, "ts": time.strftime("%Y-%m-%dT%H:%M:%S"), **kw}
    p = OUT_DIR / "k9-triple-receipts.jsonl"
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")


def _budget() -> dict:
    p = OUT_DIR / "k9-triple-budget.json"
    if not p.exists():
        b = {"schema": "k9-triple-budget/1", "seeds": list(SEEDS),
             "max_calls_total": MAX_CALLS_TOTAL, "cap_aud": CAP_AUD,
             "target_valid_per_order": TARGET_VALID,
             "max_attempts_per_order": MAX_ATTEMPTS_PER_ORDER,
             "judge_contract": "V3 single-key {choice:A|B|TIE} @512 + single-token fallback @8",
             "provider": "tier=primary via model_router (per-run pinned seed, temp0)",
             "fx_gate": "required ≤24h (fx_timestamp_utc)",
             "authority": "PRE-REG-K9-THREE-SEED-2026-08-20 §۶ — رأی چت مالک 2026-08-20",
             "ts": time.strftime("%Y-%m-%dT%H:%M:%S")}
        p.write_text(json.dumps(b, ensure_ascii=False, indent=1), "utf-8")
        _receipt("BUDGET_PRE_REGISTERED", budget=b)
    return json.loads(p.read_text("utf-8"))


class _Calls:
    def __init__(self) -> None:
        self.used = 0

    def ask(self, mr, task: str, prompt: str, max_tokens: int, seed_int: int) -> dict:
        if self.used >= MAX_CALLS_TOTAL:
            _receipt("HARD_STOP", used=self.used, cap=MAX_CALLS_TOTAL)
            raise RuntimeError(f"HARD_STOP: call cap {MAX_CALLS_TOTAL}")
        self.used += 1
        r = mr.ask(task=task, prompt=prompt, max_tokens=max_tokens,
                   tier="primary", temperature=0.0, seed=seed_int)
        _receipt("CALL", task=task, max_tokens=max_tokens, ok=bool(r.get("ok")),
                 model=r.get("model"), tier=r.get("tier"),
                 text_sha=hashlib.sha256(str(r.get("text") or "").encode("utf-8", "replace")
                                         ).hexdigest()[:16])
        return r


def _judge_order(mr, calls: _Calls, q: str, a1: str, a2: str, order: str,
                 seed_int: int) -> dict:
    attempts, valid, consistent, ties, voids = 0, 0, 0, 0, []
    while valid < TARGET_VALID and attempts < MAX_ATTEMPTS_PER_ORDER:
        attempts += 1
        pa, pb = (a1, a2) if order == "AB" else (a2, a1)
        prompt = JUDGE_PROMPT_V3.replace("{q}", q).replace("{a}", pa).replace("{b}", pb)
        r = calls.ask(mr, "k9-triple-judge", prompt, 512, seed_int)
        text = str(r.get("text") or "")
        verdict = judge_choice_v3(text, cond_position=order[0])["verdict"]
        if verdict == "UNREADABLE":
            r2 = calls.ask(mr, "k9-triple-judge-fallback", prompt, 8, seed_int)
            st = parse_single_token(str(r2.get("text") or ""), cond_position=order[0])
            verdict = st.get("verdict")
            if verdict is None:
                voids.append({"attempt": attempts, "why": "judge-unreadable-after-fallback"})
                _receipt("VOID", order=order, attempt=attempts, why="unreadable-after-fallback")
                continue
        if verdict == "TIE":
            ties += 1
            valid += 1
            continue
        winner_arm = "arm1" if (verdict == "A") == (order == "AB") else "arm2"
        if winner_arm == "arm1":
            consistent += 1
        valid += 1
    return {"order": order, "attempts": attempts, "valid": valid,
            "consistent_arm1": consistent, "ties": ties, "voids": voids}


def _fisher_two_sided(s1: int, n1: int, s2: int, n2: int) -> float:
    """Fisher exact دوطرفه روی جدول ۲×۲ — stdlib فقط (قفل روش کارت §۰.۱)."""
    if n1 <= 0 or n2 <= 0:
        return float("nan")
    row1, row2, col1 = s1 + s2, (n1 + n2) - (s1 + s2), s1 + s2

    def _p(a: int) -> float:
        return (math.comb(row1, a) * math.comb(row2, col1 - a)
                / math.comb(row1 + row2, col1))

    lo = max(0, col1 - row2)
    hi = min(row1, col1)
    p_obs = _p(s1)
    return min(1.0, sum(_p(a) for a in range(lo, hi + 1) if _p(a) <= p_obs * (1 + 1e-9)))


def _run_one(mr, calls: _Calls, seed: str) -> dict:
    seed_int = int(hashlib.sha256(seed.encode()).hexdigest()[:8], 16)
    q = _load_q()
    a1 = str(calls.ask(mr, "k9-triple-arm1", q, 200, seed_int).get("text") or "").strip()
    a2 = str(calls.ask(mr, "k9-triple-arm2", q, 300, seed_int).get("text") or "").strip()
    if not (a1 and a2):
        _receipt("BLOCKED", seed=seed, why="pair-build-failed")
        return {"seed": seed, "status": "BLOCKED", "why": "pair-build-failed"}
    _receipt("PAIR_BUILT", seed=seed,
             arm1_sha=hashlib.sha256(a1.encode()).hexdigest()[:16],
             arm2_sha=hashlib.sha256(a2.encode()).hexdigest()[:16])
    ab = _judge_order(mr, calls, q, a1, a2, "AB", seed_int)
    ba = _judge_order(mr, calls, q, a1, a2, "BA", seed_int)
    from measure.swap_consistency import classify_swap, swap_consistency_rate
    classify = classify_swap(ab["consistent_arm1"], ab["valid"],
                            ba["consistent_arm1"], ba["valid"])
    rate_ab = swap_consistency_rate(ab["consistent_arm1"], ab["valid"])
    rate_ba = swap_consistency_rate(ba["consistent_arm1"], ba["valid"])
    underpowered = ab["valid"] < TARGET_VALID or ba["valid"] < TARGET_VALID
    run_stable = (not underpowered and classify["verdict"] == "CONSISTENT"
                  and (rate_ab.get("rate") or 0) >= 0.9
                  and (rate_ba.get("rate") or 0) >= 0.9)
    return {"schema": "k9-triple-run/1", "seed": seed, "grade": "MEASURED",
            "status": "OK", "pair": {
                "arm1_text": a1, "arm2_text": a2,
                "arm1_sha": hashlib.sha256(a1.encode()).hexdigest()[:16],
                "arm2_sha": hashlib.sha256(a2.encode()).hexdigest()[:16]},
            "ab": ab, "ba": ba, "classify": classify,
            "rs_ab": rate_ab.get("rate"), "rs_ba": rate_ba.get("rate"),
            "underpowered": underpowered, "run_stable": run_stable,
            "ts": time.strftime("%Y-%m-%dT%H:%M:%S")}


def run(dry: bool) -> dict:
    _budget()
    fx = load_fx()
    if not fx["pass"]:
        _receipt("BLOCKED", why=f"fx-gate:{fx.get('reason')}")
        return {"status": "BLOCKED", "why": f"fx:{fx.get('reason')}", "fx": fx}
    if dry:
        return {"status": "DRY_RUN", "fx": fx, "seeds": list(SEEDS),
                "q_sample": _load_q()[:120]}
    import model_router as mr
    calls = _Calls()
    runs = []
    for seed in SEEDS:
        try:
            runs.append(_run_one(mr, calls, seed))
        except RuntimeError as exc:
            runs.append({"seed": seed, "status": "HARD_STOP", "why": str(exc)})
            break
    ok_runs = [r for r in runs if r.get("status") == "OK"]
    all_stable = len(ok_runs) == len(SEEDS) and all(r["run_stable"] for r in ok_runs)
    any_underpowered = any(r.get("underpowered") for r in ok_runs)
    verdict = ("STABLE_ACROSS_SEEDS" if all_stable else "BETWEEN_RUN_VARIANCE")
    fisher = None
    if len(ok_runs) >= 2:
        lo = min(ok_runs, key=lambda r: r["rs_ba"] if r["rs_ba"] is not None else -1)
        hi = max(ok_runs, key=lambda r: r["rs_ba"] if r["rs_ba"] is not None else -1)
        if lo["ba"]["valid"] and hi["ba"]["valid"]:
            fisher = {"between": [lo["seed"], hi["seed"]],
                      "p_two_sided": round(_fisher_two_sided(
                          lo["ba"]["consistent_arm1"], lo["ba"]["valid"],
                          hi["ba"]["consistent_arm1"], hi["ba"]["valid"]), 4)}
    summary = {"schema": "k9-triple-summary/1", "grade": "MEASURED",
               "authority": "PRE-REG-K9-THREE-SEED-2026-08-20 (chat-signed 2026-08-20)",
               "runs": [{k: v for k, v in r.items() if k != "pair"} for r in runs],
               "per_run_pair_shas": {r["seed"]: (r.get("pair", {}).get("arm1_sha"),
                                                 r.get("pair", {}).get("arm2_sha"))
                                     for r in ok_runs},
               "calls_used": calls.used, "cap_calls": MAX_CALLS_TOTAL,
               "cap_aud": CAP_AUD,
               "any_underpowered": any_underpowered,
               "fisher_max_divergence": fisher,
               "verdict": verdict,
               "d6_effect": ("D6 CLOSED — canonical reproducible" if all_stable
                             else "D6 CLOSED — no single-instrument truth; escalate owner"
                             if len(ok_runs) == len(SEEDS)
                             else "D6 OPEN — series incomplete"),
               "ts": time.strftime("%Y-%m-%dT%H:%M:%S")}
    stamp = time.strftime("%Y%m%dT%H%M%S")
    EVID_DIR.mkdir(parents=True, exist_ok=True)
    for r in ok_runs:
        tag = r["seed"].rsplit("/", 1)[-1]
        (EVID_DIR / f"RESULT-{tag}.json").write_text(
            json.dumps(r, ensure_ascii=False, indent=1), "utf-8")
        (OUT_DIR / f"k9-triple-run-{tag}-{stamp}.json").write_text(
            json.dumps(r, ensure_ascii=False, indent=1), "utf-8")
    (EVID_DIR / "SUMMARY.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=1), "utf-8")
    _receipt("TRIPLE_DONE", verdict=verdict, calls=calls.used)
    return summary


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--run", action="store_true")
    args = ap.parse_args()
    print(json.dumps(run(dry=args.dry_run), ensure_ascii=False, indent=1))
