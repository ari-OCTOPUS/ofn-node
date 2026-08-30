#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""live4_fg_runner.py — اجرای foreground تکه‌ای (تست به test batchهای background حل شد).
usage: python -X utf8 live4_fg_runner.py <batch 1..4>  — هر جفت بی‌درنگ در live4-pairs.jsonl می‌نشیند."""
import json, sys, time, os
from pathlib import Path
ROOT = Path(r"F:/backup"); L4 = ROOT/"06-EVIDENCE/CL01-191-20260818-2233/live4"
sys.path.insert(0, str(ROOT/"_ops")); sys.path.insert(0, str(ROOT/"_ops/cortex")); sys.path.insert(0, str(ROOT/"_ops/budget"))
sys.path.insert(0, str(ROOT/"_ops/memory")); sys.path.insert(0, str(ROOT/"_ops/outcomes")); sys.path.insert(0, str(L4)); sys.path.insert(0, str(ROOT/"4d_system"))
os.environ["OCTOPUS_WIRE_MEMORY_GATE"] = "1"
import live4_driver as D          # توابع و ثابت‌ها؛ main() اجرا نمی‌شود
import live4_reservation as LR
PAIRS = L4/"live4-pairs.jsonl"; PREDS = L4/"live4-preds.jsonl"
# V4 (2026-08-19): جداسازی مکانیکی — batchهای primary (1-4) به primary-pairs.jsonl
# می‌روند؛ E2E/probe (batch 9) به e2e-pairs.jsonl؛ live4-pairs.jsonl از این پس
# فقط تاریخِ pilot/V2 است (read-only historical).
def _pairs_path(b):
    return L4/("primary-pairs.jsonl" if b in (1, 2, 3, 4) else "e2e-pairs.jsonl")

def emit(path, obj): path.open("a", encoding="utf-8").write(json.dumps(obj, ensure_ascii=False, default=str)+"\n")

b = int(sys.argv[1]); NPAIRS = int(sys.argv[2]) if len(sys.argv) > 2 else 15; t0 = time.time()
START = int(sys.argv[3]) if len(sys.argv) > 3 else 0  # resume-from-pair (crash recovery 2026-08-19)
for i in range(START, NPAIRS):
    if time.time()-t0 > 520:  # حاشیهٔ امنِ timeout ابزار
        print(f"BATCH {b} PARTIAL at pair {i}"); break
    rows = D.retrieve_evidence()
    ev = " | ".join(f"[{r[0]} conf={r[2]}] {r[1][:90]}" for r in rows)
    # V3: pid زمان‌دار — ریشهٔ exc:IntegrityErrorهای قبلی، PKِ تکراری در اجرای مجدد بود
    pid = f"{D.TRACE}-b{b}-{i+1:02d}"
    try:
        D.LED.append_prediction(prediction_id=pid,
            content=f"L4fg batch{b} pair{i+1}: blind judge prefers evidence-conditioned proposal",
            trace_id=D.TRACE, source="cortex", model="deepseek-v4-flash+blind-judge",
            confidence=0.55, eval_window="immediate")
        D.receipt("PREDICTION_REGISTERED", prediction_id=pid)
        base_txt, bok, bmod = D.ask_fugu(D.Q, f"live4-b{b}-base-{i}")
        D.receipt("PROVIDER_CALL_FREE", provider="deepseek", model=bmod, note=f"ok={bok} baseline-arm")
        cond_txt, cok, cnote = D.ask_paid(D.Q + "\n\nشواهد بازیابی‌شده (provenance‌دار):\n" + ev, f"live4-b{b}-cond-{i}")
        if not (bok and cok and base_txt.strip() and cond_txt.strip()):
            D.ST["availability_voids"] += 1
            D.LED.attach_outcome(prediction_id=pid, outcome="VOID_PROVIDER_UNAVAILABLE")
            D.receipt("PAIR_VOID", prediction_id=pid, note=f"base_ok={bok} cond={cnote}")
            emit(_pairs_path(b), {"batch": b, "pair": i+1, "void": True, "why": f"base={bok}/{bmod} cond={cnote}"})
            continue
        bp = D.H.blind_pair(base_txt, cond_txt, seed=100*b + i, template=D.H.JUDGE_PROMPT_V3)
        j_txt, jok, jmod = D.ask_fugu(bp["judge_prompt"].replace("{TASK}", D.Q), f"live4-b{b}-judge-{i}", max_tokens=512)
        jc = D.H.judge_choice_v3(j_txt if jok else "", bp["cond_position"],
                                judge_provider="deepseek", judge_model=jmod or "deepseek-v4-flash",
                                trace_id=f"{pid}-judge")
        jc["judge_independence_limited"] = True  # same provider family as arms (fugu dead, local unusable)
        if jc["void"]:
            # V3: ضبطِ خامِ خروجیِ ناخوانا برای تشخیص (شکافِ مشاهده‌پذیریِ قبلی)
            emit(L4/"live4-judge-raws.jsonl", {"pid": pid, "attempt": 1, "raw": (j_txt or "")[:1200],
                                               "raw_sha256": jc["raw_output_sha256"], "ts": D.now()})
            # D-B/V3: دقیقاً یک re-ask رسیددار (بدون حدسِ برنده) — ناخوانای دوم = VOID قطعی
            D.receipt("JUDGE_REASK", prediction_id=pid, note="unreadable-1st contract=v3")
            j_txt, jok, jmod = D.ask_fugu(bp["judge_prompt"].replace("{TASK}", D.Q) + D.H.SINGLE_TOKEN, f"live4-b{b}-judge2-{i}", max_tokens=8)
            jc = D.H.parse_single_token(j_txt if jok else "", bp["cond_position"])
            jc.update({"judge_provider": "deepseek-v4a-512", "judge_model": jmod or "deepseek-v4-flash",
                       "trace_id": f"{pid}-judge2", "reasked": True, "fallback": "single-token"})
            jc["judge_independence_limited"] = True
            jc["reasked"] = True
        won = jc["winner"]
        if jc["void"]:
            emit(L4/"live4-judge-raws.jsonl", {"pid": pid, "attempt": 2, "raw": (j_txt or "")[:1200],
                                               "raw_sha256": jc["raw_output_sha256"], "ts": D.now()})
            D.ST["availability_voids"] += 1
            D.LED.attach_outcome(prediction_id=pid, outcome="VOID_JUDGE_UNREADABLE")
            D.receipt("PAIR_VOID", prediction_id=pid, note=f"judge-{jc['verdict']}")
            emit(_pairs_path(b), {"batch": b, "pair": i+1, "void": True, "why": "judge"})
            continue
        hit = (won == "conditioned")
        D.LED.attach_outcome(prediction_id=pid, outcome=f"{'hit' if hit else 'miss'}: pos={bp['cond_position']}")
        D.receipt("PAIR_COMPLETE", prediction_id=pid, note=f"cond_won={hit} pos={bp['cond_position']}")
        emit(_pairs_path(b), {"batch": b, "pair": i+1, "void": False, "cond_won": hit,
                     "cond_position": bp["cond_position"], "evidence_ids": [r[0] for r in rows],
                     "contract": "judge-choice-v3/1", "judge": jc})
        emit(PREDS, {"id": pid, "conf": 0.55, "hit": hit})
        LR.record("pair")
        print(f"b{b}p{i+1}: {'WIN' if hit else 'LOSS'} ({bp['cond_position']}) spent={D.ST['spent_aud']:.4f}")
    except Exception as e:  # noqa: BLE001
        emit(_pairs_path(b), {"batch": b, "pair": i+1, "void": True, "why": f"exc:{type(e).__name__}"})
        print(f"b{b}p{i+1}: EXC {type(e).__name__}")
print(f"BATCH {b} DONE spent={D.ST['spent_aud']:.4f} paid={D.ST['paid_calls']} voids={D.ST['availability_voids']}")
