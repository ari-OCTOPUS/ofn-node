#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""v4_probe.py — V4 E2E gate: 8 fresh foreground cases, judge = GLM (different family).

Per: OWNER-CONSENTS §1 (V4a) + WAR24-LOCK §4 (different-family judge, incl. primary,
owner accepted two-variable caveat) + V4-FREEZE-PREP-LINES (fallback ladder, sizing).
Arms: DeepSeek tier=primary (both). Judge: GLM via GLMClientSync.chat (strict
single-key contract; one receipted re-ask; fallback re-ask = single-token contract;
second unreadable = VOID). Gate: 8/8 readable."""
import json, sys, time
from pathlib import Path

ROOT = Path(r"F:/backup")
L4 = ROOT / "06-EVIDENCE/CL01-191-20260818-2233/live4"
sys.path.insert(0, str(ROOT / "_ops")); sys.path.insert(0, str(ROOT / "_ops/cortex"))
sys.path.insert(0, str(ROOT / "_ops/memory")); sys.path.insert(0, str(ROOT / "4d_system")); sys.path.insert(0, str(L4))
import live4_driver as D
import live4_harness as H
from llm.glm_client import GLMClientSync

glm = GLMClientSync()
PAIRS = L4 / "live4-pairs.jsonl"
def emit(p, o): p.open("a", encoding="utf-8").write(json.dumps(o, ensure_ascii=False, default=str) + "\n")

def glm_judge(prompt: str, max_tokens: int) -> tuple[str, str]:
    txt = glm.chat([{"role": "user", "content": prompt}], temperature=0.0, max_tokens=max_tokens)
    return str(txt or ""), "glm"

SINGLE_TOKEN = ("\n\nANSWER NOW with exactly ONE character: A or B or T. "
                "If truly equal, T. Nothing else.")
N = 8
t0 = time.time()
results = []
for i in range(N):
    pid = f"{D.TRACE}-v4p-{i+1:02d}"
    rows = D.retrieve_evidence()
    ev = " | ".join(f"[{r[0]} conf={r[2]}] {r[1][:90]}" for r in rows)
    try:
        D.LED.append_prediction(prediction_id=pid,
            content=f"V4 probe case{i+1}: GLM judge reads the blind pair",
            trace_id=D.TRACE, source="cortex", model="deepseek-arms+glm-judge",
            confidence=0.55, eval_window="immediate")
        base_txt, bok, bmod = D.ask_fugu(D.Q, f"live4-v4p-base-{i}", max_tokens=200)
        cond_txt, cok, cnote = D.ask_paid(D.Q + "\n\nشواهد بازیابی‌شده (provenance‌دار):\n" + ev, f"live4-v4p-cond-{i}")
        if not (bok and cok and base_txt.strip() and cond_txt.strip()):
            D.LED.attach_outcome(prediction_id=pid, outcome="VOID_PROVIDER_UNAVAILABLE")
            emit(PAIRS, {"batch": 9, "pair": i+1, "void": True, "why": f"arms base={bok} cond={cnote}", "probe": "v4"})
            results.append({"i": i+1, "readable": False, "void": True, "why": "arms"}); continue
        bp = H.blind_pair(base_txt, cond_txt, seed=400 + i, template=H.JUDGE_PROMPT_V3)
        j_txt, jmod = glm_judge(bp["judge_prompt"].replace("{TASK}", D.Q), 256)
        jc = H.judge_choice_v3(j_txt, bp["cond_position"], judge_provider="glm",
                               judge_model=jmod, trace_id=f"{pid}-judge")
        if jc["void"]:
            D.receipt("JUDGE_REASK", prediction_id=pid, note="unreadable-1st contract=v3")
            j_txt, jmod = glm_judge(bp["judge_prompt"].replace("{TASK}", D.Q) + SINGLE_TOKEN, 8)
            jc = H.judge_choice_v3(j_txt, bp["cond_position"], judge_provider="glm",
                                   judge_model=jmod, trace_id=f"{pid}-judge2")
            jc["reasked"] = True; jc["fallback"] = "single-token"
        readable = not jc["void"]
        won = jc["winner"]
        if not readable:
            D.LED.attach_outcome(prediction_id=pid, outcome="VOID_JUDGE_UNREADABLE")
            emit(PAIRS, {"batch": 9, "pair": i+1, "void": True, "why": "judge", "probe": "v4"})
        else:
            hit = (won == "conditioned")
            D.LED.attach_outcome(prediction_id=pid, outcome=f"{'hit' if hit else 'miss'}: pos={bp['cond_position']}")
            emit(PAIRS, {"batch": 9, "pair": i+1, "void": False, "cond_won": hit,
                         "cond_position": bp["cond_position"], "evidence_ids": [r[0] for r in rows],
                         "contract": "judge-choice-v3/1-glm", "probe": "v4", "judge": jc})
        results.append({"i": i+1, "readable": readable, "void": not readable,
                        "pos": bp["cond_position"], "verdict": jc["verdict"]})
        print(f"case{i+1}: readable={readable} verdict={jc['verdict']} pos={bp['cond_position']} reasked={jc.get('reasked', False)}")
    except Exception as e:  # noqa: BLE001
        emit(PAIRS, {"batch": 9, "pair": i+1, "void": True, "why": f"exc:{type(e).__name__}", "probe": "v4"})
        results.append({"i": i+1, "readable": False, "void": True, "why": type(e).__name__})
        print(f"case{i+1}: EXC {type(e).__name__}")
ok = sum(1 for r in results if r.get("readable"))
print(f"\nV4 GATE: {ok}/{N} readable | {'PASS' if ok == N else 'FAIL'} | spent={D.ST['spent_aud']:.4f} | {time.time()-t0:.0f}s")
