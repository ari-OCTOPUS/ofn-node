#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""judge_pilot.py — پایلوت K=9 سازگاری جایگاه (swap consistency) — مجوز مالک 2026-08-19.

روش (همه از هارنسِ منجمد GATE3، نه بازسازی):
  - قالب داور: JUDGE_PROMPT_V3 (فایل منجمد live4_harness.py) — تک‌کلید {"choice":A|B|TIE}.
  - فراخوان: model_router.ask(tier="primary") با seed پین‌شده + temperature=0.
  - fallback: re-ask ۸ توکنی + parse_single_token؛ دومین ناخوانا = VOID با دلیل.
  - جفت: دو بازو از همان TASK منجمد (Q در live4_driver.py)؛ ۹ قضاوت معتبر در هر ترتیب.
  - گیت‌ها: بودجهٔ ازپیش‌ثبت (≤۳۰ فراخوان، سقف AU$1)؛ FX ≤24h؛ LIVE4_RESERVATION
    (DEFERRED = BLOCKED رسیددار)؛ هر فراتررفتن = HARD_STOP fail-closed.
  - برچسب حداکثر MEASURED؛ هر فراخوان رسید append-only دارد.

استفاده:
  python _ops/measure/judge_pilot.py --dry-run   # ساخت promptها بدون فراخوان
  python _ops/measure/judge_pilot.py --run       # اجرای واقعی با بودجهٔ ثبت‌شده
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import re
import sys
import time
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_OPS = _HERE.parent
_ROOT = _HERE.parents[1]

L4 = _ROOT / "06-EVIDENCE" / "CL01-191-20260818-2233" / "live4"
SEED = "k9-pilot-20260819"
SEED_INT = int(hashlib.sha256(SEED.encode()).hexdigest()[:8], 16)
MAX_CALLS = 30          # بودجهٔ ازپیش‌ثبت (۲ بازو + ۲۶ داور + fallback)
CAP_AUD = 1.00
TARGET_VALID = 9
MAX_ATTEMPTS_PER_ORDER = 13
OUT_DIR = _OPS / "state" / "pipeline"
EVID_DIR = _ROOT / "06-EVIDENCE" / "PILOT-K9-20260819"

for _p in (str(_OPS), str(_OPS / "cortex"), str(_OPS / "measure"), str(L4)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from live4_harness import load_fx, judge_choice_v3, parse_single_token, JUDGE_PROMPT_V3  # noqa: E402


def _load_q() -> str:
    """TASK منجمد از live4_driver.py (فایل منجمد؛ بدون اجرای ماژول)."""
    src = (L4 / "live4_driver.py").read_text("utf-8")
    m = re.search(r'Q = TAX = \((.+?)\)\n', src, re.S)
    if not m:
        raise RuntimeError("Q not found in frozen driver")
    q = m.group(1).strip().strip('"')
    # اتصال رشتههای ضمنیِ چندخطی: "... " \n "..." → "... ..."
    return re.sub(r'"\s*\n\s*"', "", q)


def _receipt(kind: str, **kw) -> None:
    row = {"schema": "k9-pilot-receipt/1", "kind": kind, "seed": SEED,
           "ts": time.strftime("%Y-%m-%dT%H:%M:%S"), **kw}
    p = OUT_DIR / "pilot-k9-receipts.jsonl"
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")


def _budget() -> dict:
    p = OUT_DIR / "pilot-k9-budget.json"
    if not p.exists():
        b = {"schema": "k9-pilot-budget/1", "seed": SEED,
             "max_calls": MAX_CALLS, "cap_aud": CAP_AUD,
             "target_valid_per_order": TARGET_VALID,
             "max_attempts_per_order": MAX_ATTEMPTS_PER_ORDER,
             "judge_contract": "V3 single-key {choice:A|B|TIE} @512 + single-token fallback @8",
             "provider": "tier=primary via model_router (seed+pinned temp0)",
             "fx_gate": "required ≤24h", "reservation_gate": "LIVE4_RESERVATION honored",
             "ts": time.strftime("%Y-%m-%dT%H:%M:%S")}
        p.write_text(json.dumps(b, ensure_ascii=False, indent=1), "utf-8")
        _receipt("BUDGET_PRE_REGISTERED", budget=b)
    return json.loads(p.read_text("utf-8"))


def _ask(mr, task: str, prompt: str, max_tokens: int) -> dict:
    """فراخوان پولی با seed پین‌شده؛ خروجی شامل رسید فراخوان."""
    r = mr.ask(task=task, prompt=prompt, max_tokens=max_tokens,
               tier="primary", temperature=0.0, seed=SEED_INT)
    _receipt("CALL", task=task, max_tokens=max_tokens, ok=bool(r.get("ok")),
             model=r.get("model"), tier=r.get("tier"),
             text_sha=hashlib.sha256(str(r.get("text") or "").encode("utf-8", "replace")
                                     ).hexdigest()[:16])
    return r


def _build_pair(mr, q: str) -> tuple[str, str, list]:
    """دو بازوی جفت از TASK منجمد (همان مسیر live4: primary، طول‌های ۲۰۰/۳۰۰)."""
    a1 = _ask(mr, "k9-pilot-arm1", q, 200)
    a2 = _ask(mr, "k9-pilot-arm2", q, 300)
    t1, t2 = str(a1.get("text") or "").strip(), str(a2.get("text") or "").strip()
    _receipt("PAIR_BUILT", arm1_len=len(t1), arm2_len=len(t2))
    return t1, t2, [a1, a2]


def _judge_order(mr, q: str, a1: str, a2: str, order: str,
                 calls: list) -> dict:
    """۹ قضاوت معتبر در یک ترتیب؛ fallback تک‌توکنی؛ VOID با دلیل."""
    attempts, valid, consistent, ties, voids = 0, 0, 0, 0, []
    while valid < TARGET_VALID and attempts < MAX_ATTEMPTS_PER_ORDER:
        attempts += 1
        if order == "AB":
            pa, pb = a1, a2
        else:
            pa, pb = a2, a1
        prompt = JUDGE_PROMPT_V3.replace("{q}", q).replace("{a}", pa).replace("{b}", pb)
        r = _ask(mr, "k9-pilot-judge", prompt, 512)
        calls.append(r)
        text = str(r.get("text") or "")
        parsed = judge_choice_v3(text, cond_position=order[0])
        verdict = parsed["verdict"]
        if verdict == "UNREADABLE":
            r2 = _ask(mr, "k9-pilot-judge-fallback", prompt, 8)
            calls.append(r2)
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
            "consistent_arm1": consistent, "ties": ties, "voids": voids,
            "stopped_midway": valid < TARGET_VALID}


def run(dry: bool) -> dict:
    _budget()
    fx = load_fx()
    if not fx["pass"]:
        _receipt("BLOCKED", why=f"fx-gate:{fx.get('reason')}")
        return {"status": "BLOCKED", "why": f"fx:{fx.get('reason')}", "fx": fx}
    if dry:
        q = _load_q()
        return {"status": "DRY_RUN", "q": q, "judge_prompt_sample": JUDGE_PROMPT_V3
                .replace("{q}", q).replace("{a}", "[arm1]").replace("{b}", "[arm2]")}
    import model_router as mr
    q = _load_q()
    calls: list = []
    a1, a2, pair_calls = _build_pair(mr, q)
    calls += pair_calls
    if not (a1 and a2):
        _receipt("BLOCKED", why="pair-build-failed")
        return {"status": "BLOCKED", "why": "pair-build-failed (empty arms)"}
    ab = _judge_order(mr, q, a1, a2, "AB", calls)
    ba = _judge_order(mr, q, a1, a2, "BA", calls)
    total_calls = len(calls)
    if total_calls > MAX_CALLS:
        _receipt("HARD_STOP", calls=total_calls)
        return {"status": "HARD_STOP", "calls": total_calls, "ab": ab, "ba": ba}
    from measure.swap_consistency import classify_swap, swap_consistency_rate
    verdict = classify_swap(ab["consistent_arm1"], ab["valid"],
                            ba["consistent_arm1"], ba["valid"])
    rate_ab = swap_consistency_rate(ab["consistent_arm1"], ab["valid"])
    rate_ba = swap_consistency_rate(ba["consistent_arm1"], ba["valid"])
    result = {
        "schema": "k9-pilot-result/1", "seed": SEED, "grade": "MEASURED",
        "pair": {"arm1_sha": hashlib.sha256(a1.encode("utf-8")).hexdigest()[:16],
                 "arm2_sha": hashlib.sha256(a2.encode("utf-8")).hexdigest()[:16]},
        "ab": ab, "ba": ba, "classify": verdict,
        "rate_ab_arm1": rate_ab, "rate_ba_arm1": rate_ba,
        "calls": total_calls, "spent_aud_cap": CAP_AUD,
        "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "rs_ab_label": ("STABLE" if verdict["verdict"] == "CONSISTENT"
                        and (rate_ab.get("rate") or 0) >= 0.9 else
                        "INSTABILITY_SIGNIFICANT" if verdict["verdict"] != "RANDOMNESS_UNRESOLVED"
                        else "UNDERPOWERED"),
    }
    f = OUT_DIR / f"pilot-k9-result-{time.strftime('%Y%m%dT%H%M%S')}.json"
    f.write_text(json.dumps(result, ensure_ascii=False, indent=1), "utf-8")
    EVID_DIR.mkdir(parents=True, exist_ok=True)
    (EVID_DIR / "RESULT.json").write_text(json.dumps(result, ensure_ascii=False, indent=1), "utf-8")
    _receipt("PILOT_DONE", status=result["classify"]["verdict"], calls=total_calls)
    return result


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--run", action="store_true")
    args = ap.parse_args()
    print(json.dumps(run(dry=args.dry_run), ensure_ascii=False, indent=1))
