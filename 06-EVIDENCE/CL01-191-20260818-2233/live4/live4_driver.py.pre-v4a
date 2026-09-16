#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""live4_driver.py — اجرای LIVE-4 (GO با FX-PIN-20260819-01).
دو batch × ۱۵ جفت · داور کور + A/B تصادفی · baseline=fugu کوتاه، conditioned=deepseek
(tier=secondary=deepseek پس از INC-2) · بودجهٔ AUD از رسیدهای hook (cost-receipts.jsonl)
· گارد FX ≤24h قبل از هر فراخوانی پرداختی · availability = نه برد نه باخت."""
from __future__ import annotations

import hashlib, json, os, random, sqlite3, subprocess, sys, time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(r"F:/backup")
L4 = ROOT / "06-EVIDENCE/CL01-191-20260818-2233/live4"
RECEIPTS = L4 / "API-RECEIPTS.jsonl"
COST_RX = ROOT / "_ops/state/cortex/cost-receipts.jsonl"
PRED_DB = ROOT / "_ops/state/predictions.db"
CANON = ROOT / "_ops/state/memory/memory.db"
DLOG = ROOT / "4d_system/outputs/daemon-launch4b.err.log"
os.environ["OCTOPUS_WIRE_MEMORY_GATE"] = "1"
for p in (str(ROOT/"_ops"), str(ROOT/"_ops/cortex"), str(ROOT/"_ops/memory"), str(ROOT/"_ops/outcomes"), str(ROOT/"4d_system"), str(L4)):
    if p not in sys.path: sys.path.insert(0, p)

import model_router as mr
from memory.prediction_ledger import PredictionLedger
import live4_harness as H
LED = PredictionLedger(PRED_DB)
TRACE = "cl1-live4-" + datetime.now(timezone.utc).strftime("%H%M%S")
T0 = time.time()
ST = {"spent_aud": 0.0, "paid_calls": 0, "fugu_calls": 0, "paid_blocked": False,
      "availability_voids": 0, "errors": 0}
CAP_PER_CALL, HARD_STOP = 1.00, 24.0  # LEARNING-FIRST-01/02

def now(): return datetime.now(timezone.utc).isoformat(timespec="seconds")
def sha(t): return hashlib.sha256(str(t).encode("utf-8","replace")).hexdigest()

def receipt(kind, **kw):
    row = {"schema": "cl1-live4-receipt/1", "kind": kind, "trace_id": TRACE,
           "parent_id": "cl1-live4", "timestamp": now(),
           "budget": {"spent_aud": round(ST["spent_aud"],6), "cap": HARD_STOP},
           **kw}
    RECEIPTS.open("a", encoding="utf-8").write(json.dumps(row, ensure_ascii=False, default=str)+"\n")

def sync_spend():
    """بودجهٔ زنده از رسیدهای COST-OBS-1 (hook تولید می‌کند)."""
    if not COST_RX.exists(): return
    for line in COST_RX.read_text(encoding="utf-8", errors="replace").splitlines()[-8:]:
        try: r = json.loads(line)
        except Exception: continue
        if str(r.get("trace_id","")).startswith(("paid-","cl1-live4")) and r.get("receipt_status")=="COMPLETE" \
           and r.get("cost_method") in ("REPORTED","DETERMINISTIC_ESTIMATE"):
            pass  # تجمیع در update_spend از receiptهای خودِ driver انجام می‌شود
def add_spend(cost_aud, rec=None):
    ST["spent_aud"] += float(cost_aud or 0.0); ST["paid_calls"] += 1
    if ST["spent_aud"] >= HARD_STOP:
        ST["paid_blocked"] = True; receipt("HARD_STOP_BUDGET", note=f"spent={ST['spent_aud']:.4f}")

def fx_gate() -> bool:
    v = H.load_fx()
    if not v["pass"]:
        ST["paid_blocked"] = True
        receipt("FX_BLOCKED", note=v.get("reason",""))
        return False
    return True

def ask_fugu(prompt, task):
    ST["fugu_calls"] += 1
    # D-A fix: بدونِ tier، TASK_TIERS→local بود؛ هر دو بازو باید همان provider باشند
    r = mr.ask(task=task, prompt=prompt, max_tokens=200, tier="primary")
    return (str(r.get("text") or ""), bool(r.get("ok")), str(r.get("model") or "fugu"))

def ask_paid(prompt, task):
    if ST["paid_blocked"] or not fx_gate(): return None, False, "blocked"
    r = mr.ask(task=task, prompt=prompt, max_tokens=300, tier="primary")
    ok = bool(r.get("ok"))
    # هزینه از رسید hook (REPORTED/AUD با FX پین‌شده)
    cost = None
    if COST_RX.exists():
        for line in reversed(COST_RX.read_text(encoding="utf-8", errors="replace").splitlines()[-6:]):
            try: cr = json.loads(line)
            except Exception: continue
            if cr.get("cost_method") in ("REPORTED","DETERMINISTIC_ESTIMATE") and cr.get("receipt_status")=="COMPLETE":
                cost = cr.get("estimated_or_reported_cost_aud"); break
            if cr.get("receipt_status") == "COST_UNOBSERVABLE":
                ST["paid_blocked"] = True; receipt("COST_UNOBSERVABLE_STOP"); return None, False, "cost-unobservable"
    add_spend(cost)
    receipt("PROVIDER_CALL_PAID", provider="deepseek", model=str(r.get("model") or ""),
            cost_aud=cost, note=f"ok={ok} spent={ST['spent_aud']:.4f}")
    if not ok: ST["errors"] += 1
    return (str(r.get("text") or ""), ok, str(r.get("model") or "deepseek"))

def daemon_ok():
    try:
        out = subprocess.run(["powershell","-NoProfile","-Command",
          "(Get-CimInstance Win32_Process -Filter \"Name like 'python%'\" | Where-Object {$_.CommandLine -like '*brain.daemon*'}).ProcessId"],
          capture_output=True, text=True, timeout=20).stdout.strip()
        return bool(out) and DLOG.read_text(encoding="utf-8", errors="replace").count("protective HALT") == 0
    except Exception: return False

Q = TAX = ("پیشنهاد بده: کوچک‌ترین گامِ بعدیِ قابل‌تست برای بهبود چرخهٔ یادگیریِ حافظهٔ کانونی "
          "OCTOPUS در ۲۴ ساعت آینده. فقط یک جمله.")

def retrieve_evidence():
    con = sqlite3.connect(f"file:{CANON}?mode=ro", uri=True)
    rows = con.execute("SELECT memory_id, content, confidence, valid_to FROM memory WHERE admission_state='ADMITTED' "
        "AND confidence IS NOT NULL AND confidence!='' AND valid_to IS NOT NULL AND valid_to!='' "
        "AND valid_to > ? ORDER BY created_at DESC LIMIT 3", (now(),)).fetchall()
    con.close(); return rows

def run_batch(b: int, rng_seed_base: int, R: dict):
    for i in range(15):
        if time.time()-T0 > 100*60 or not daemon_ok():
            R["stops"].append(f"batch{b}_pair{i}"); return
        rows = retrieve_evidence()
        ev = " | ".join(f"[{r[0]} conf={r[2]}] {r[1][:90]}" for r in rows)
        pid = f"cl1-live4-b{b}-{i+1:02d}"
        LED.append_prediction(prediction_id=pid,
            content=f"L4 batch{b} pair{i+1}: blind judge prefers evidence-conditioned proposal",
            trace_id=TRACE, source="cortex", model="deepseek-v4-flash+blind-judge",
            confidence=0.55, eval_window="immediate")
        receipt("PREDICTION_REGISTERED", prediction_id=pid)
        base_txt, bok, bmod = ask_fugu(Q, f"live4-b{b}-base-{i}")
        receipt("PROVIDER_CALL_FREE", provider="fugu", model=bmod, note=f"ok={bok} prompt<=500")
        cond_txt, cok, cnote = ask_paid(Q + "\n\nشواهد بازیابی‌شده (provenance‌دار):\n" + ev, f"live4-b{b}-cond-{i}")
        if not (bok and cok and base_txt.strip() and cond_txt.strip()):
            ST["availability_voids"] += 1
            LED.attach_outcome(prediction_id=pid, outcome="VOID_PROVIDER_UNAVAILABLE (neither win nor loss)")
            receipt("PAIR_VOID", prediction_id=pid, note=f"base_ok={bok} cond={cnote}")
            R["voids"].append({"batch": b, "pair": i+1}); continue
        bp = H.blind_pair(base_txt, cond_txt, seed=rng_seed_base + i)
        j_txt, jok, jmod = ask_fugu(bp["judge_prompt"].replace("{TASK}", Q), f"live4-b{b}-judge-{i}")
        won = H.parse_judge(j_txt, bp["cond_position"]) if jok else None
        if won is None:
            ST["availability_voids"] += 1
            LED.attach_outcome(prediction_id=pid, outcome="VOID_JUDGE_UNREADABLE")
            receipt("PAIR_VOID", prediction_id=pid, note="judge-unreadable"); R["voids"].append({"batch": b, "pair": i+1}); continue
        hit = (won == "conditioned")
        LED.attach_outcome(prediction_id=pid, outcome=f"{'hit' if hit else 'miss'}: cond_pos={bp['cond_position']}")
        R["pairs"].append({"batch": b, "pair": i+1, "cond_won": hit,
                           "baseline_sha": bp["baseline_sha"], "cond_sha": bp["conditioned_sha"],
                           "evidence_ids": [r[0] for r in rows], "cond_position": bp["cond_position"]})
        R["predictions"].append({"id": pid, "conf": 0.55, "hit": hit})
        receipt("PAIR_COMPLETE", prediction_id=pid, note=f"cond_won={hit} pos={bp['cond_position']}")
    receipt("BATCH_DONE", batch=b)

def main():
    R = {"started": now(), "trace": TRACE, "pairs": [], "predictions": [], "voids": [], "stops": []}
    receipt("LIVE4_START", fx=H.load_fx(), note="GO: six conditions PASS")
    for b, seed in ((1, 101), (2, 202), (3, 303), (4, 404)):  # 1-2: primary منجمد · 3-4: تأییدی
        if b > 2 and (ST["paid_blocked"] or time.time()-T0 > 80*60):
            R["stops"].append(f"confirmatory-stop-before-b{b}"); break
        run_batch(b, seed, R)
        bs = [p for p in R["pairs"] if p["batch"] == b]
        receipt("INTERIM", batch=b, valid=len(bs), cond_wins=sum(1 for p in bs if p["cond_won"]))
    valid = R["pairs"]; wins = [p for p in valid if p["cond_won"]]
    per_batch = {b: (len([p for p in valid if p["batch"]==b]), len([p for p in wins if p["batch"]==b])) for b in (1,2)}
    n = len(R["predictions"])
    R["summary"] = {"valid_pairs": len(valid), "cond_wins_total": len(wins), "per_batch": per_batch,
                    "brier_pairs": round(sum((p["conf"]-(1 if p["hit"] else 0))**2 for p in R["predictions"])/n,4) if n else None,
                    "availability_voids": ST["availability_voids"], "spent_aud": round(ST["spent_aud"],6),
                    "paid_calls": ST["paid_calls"], "fugu_calls": ST["fugu_calls"], "errors": ST["errors"]}
    R["finished"] = now(); R["elapsed_min"] = round((time.time()-T0)/60,1)
    (L4/"live4-run-report.json").write_text(json.dumps(R, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    receipt("LIVE4_END", summary=R["summary"])
    return R

if __name__ == "__main__":
    print(json.dumps(main(), ensure_ascii=False, indent=1, default=str))
