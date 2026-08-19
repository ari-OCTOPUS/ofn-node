#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""live3_driver.py — CORE-LIVE-3 (مالک: OWNER_PROMOTE_CORE_LIVE_3).
≥۴۰ prediction قبل از outcome · ≥۳۰ outcome واجد شرایط · ≥۱۵ جفت پروپوزال هم‌کلاس با outcome پیوندی
· سیاست provider: fugu فقط پرامپت کوتاه (≤500 کاراکتر)؛ fallback رسیددار به deepseek برای
conditioned بلند یا پس از یک شکست رسیددار fugu · هزینهٔ نامعلومِ پرداختی = COST_UNOBSERVABLE + توقف پرداختی‌ها."""
from __future__ import annotations

import hashlib, json, os, random, sqlite3, subprocess, sys, time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(r"F:/backup")
L3 = ROOT / "06-EVIDENCE/CL01-191-20260818-2233/live3"
RECEIPTS = L3 / "API-RECEIPTS.jsonl"
PRED_DB = ROOT / "_ops/state/predictions.db"
CANON = ROOT / "_ops/state/memory/memory.db"
DLOG = ROOT / "4d_system/outputs/daemon-launch4b.err.log"
os.environ["OCTOPUS_WIRE_MEMORY_GATE"] = "1"
for p in (str(ROOT/"_ops"), str(ROOT/"_ops/cortex"), str(ROOT/"_ops/memory"), str(ROOT/"_ops/outcomes"), str(ROOT/"4d_system")):
    if p not in sys.path: sys.path.insert(0, p)

T0 = time.time(); HARD_MIN = 110
TRACE = "cl1-live3-" + datetime.now(timezone.utc).strftime("%H%M%S")
ST = {"calls": 0, "fugu_fail": 0, "errors": 0, "fallbacks": 0, "paid_blocked": False, "spent_aud": 0.0}
FUGU_SAFE = 500

def now(): return datetime.now(timezone.utc).isoformat(timespec="seconds")
def sha(t): return hashlib.sha256(str(t).encode("utf-8","replace")).hexdigest()

def receipt(kind, *, provider="observer", model="none", prompt="", output="", lat=0.0, tokens=0,
            cost=0.0, prediction_id=None, admission=None, note="", fallback=None):
    row = {"schema":"cl1-live3-receipt/1","kind":kind,"trace_id":TRACE,"parent_id":"cl1-live3",
           "timestamp":now(),"provider":provider,"model":model,"input_sha256":sha(prompt),
           "output_sha256":sha(output or ""),"tokens":tokens,"cost_aud":cost,"latency_s":round(float(lat),3),
           "retry":0,"budget_remaining":{"daily_cap_audit":15.0,"hard_stop_audit":12.0,"spent_this_run_aud":ST["spent_aud"]},
           "prediction_id":prediction_id,"admission_decision":admission,"note":note}
    if fallback: row["fallback"] = fallback
    RECEIPTS.open("a",encoding="utf-8").write(json.dumps(row,ensure_ascii=False)+"\n")
    return row

import provider_adapter as pa
import model_router as mr
from memory.prediction_ledger import PredictionLedger
LED = PredictionLedger(PRED_DB)
KEYS = mr.keys_present()
DEEPSEEK_OK = bool(KEYS.get("deepseek"))

def call(prompt, kind, pid=None):
    """سیاست provider مالک را اجرا می‌کند. خروجی: (text|None, meta)."""
    long = len(prompt) > FUGU_SAFE
    want_fugu = (kind != "conditioned") or (not long and ST["fugu_fail"] == 0)
    t0 = time.time()
    if want_fugu:
        try:
            r = pa.router().ask(prompt, max_tokens=200, temperature=0.0, trace_id=TRACE, task=f"live3-{kind}")
            ok = bool(getattr(r,"success",False)); ST["calls"] += 1
            text = str(getattr(r,"text","") or getattr(r,"content","") or "")
            model = str(getattr(r,"model","") or "fugu")
            if not ok: ST["fugu_fail"] += 1; ST["errors"] += 1
            receipt("PROVIDER_CALL", provider="fugu", model=model, prompt=prompt, output=text,
                    lat=time.time()-t0, tokens=getattr(r,"tokens",None) or 0, cost=0.0, prediction_id=pid,
                    note=f"{kind} success={ok} prompt_size={len(prompt)} free-tier cost=0")
            return (text if ok else None), {"provider":"fugu","ok":ok}
        except Exception as e:  # noqa: BLE001
            ST["calls"] += 1; ST["fugu_fail"] += 1; ST["errors"] += 1
            receipt("PROVIDER_CALL", provider="fugu", model="error", prompt=prompt, lat=time.time()-t0,
                    note=f"{kind} exception {type(e).__name__}")
            return None, {"provider":"fugu","ok":False}
    # fallback مجاز: conditioned بلند یا پس از یک شکست fugu
    reason = "prompt>500" if long else "after-1-fugu-failure"
    if not DEEPSEEK_OK or ST["paid_blocked"]:
        receipt("FALLBACK_UNAVAILABLE", prompt=prompt, note=f"reason={reason}; deepseek_key={DEEPSEEK_OK}; paid_blocked={ST['paid_blocked']} — availability hit")
        return None, {"provider":"none","ok":False,"unavailable":True}
    try:
        r = pa.router().ask(prompt + "\n[provider:deepseek]", max_tokens=200, temperature=0.0, trace_id=TRACE, task=f"live3-{kind}-fb")
        ST["calls"] += 1; ST["fallbacks"] += 1
        ok = bool(getattr(r,"success",False))
        text = str(getattr(r,"text","") or getattr(r,"content","") or "")
        model = str(getattr(r,"model","") or "deepseek")
        cost = getattr(r,"cost",None)
        if ok and cost is None:
            ST["paid_blocked"] = True
            receipt("PROVIDER_CALL", provider="deepseek", model=model, prompt=prompt, output=text,
                    lat=time.time()-t0, tokens=getattr(r,"tokens",None) or 0, cost=None, prediction_id=pid,
                    fallback={"fallback_reason":reason,"provider":"deepseek","exact_model":model,"prompt_size":len(prompt)},
                    note="COST_UNOBSERVABLE — paid calls STOPPED per hard stop")
            return None, {"provider":"deepseek","ok":False,"cost_unobservable":True}
        c = float(cost or 0.0); ST["spent_aud"] += c
        if ST["spent_aud"] >= 12.0:
            receipt("HARD_STOP_BUDGET", note=f"spent {ST['spent_aud']}"); raise SystemExit(3)
        receipt("PROVIDER_CALL", provider="deepseek", model=model, prompt=prompt, output=text,
                lat=time.time()-t0, tokens=getattr(r,"tokens",None) or 0, cost=c, prediction_id=pid,
                fallback={"fallback_reason":reason,"provider":"deepseek","exact_model":model,"prompt_size":len(prompt)},
                note=f"{kind} success={ok} cost={c}")
        return (text if ok else None), {"provider":"deepseek","ok":ok}
    except SystemExit: raise
    except Exception as e:  # noqa: BLE001
        ST["calls"] += 1; ST["errors"] += 1
        receipt("PROVIDER_CALL", provider="deepseek", model="error", prompt=prompt, lat=time.time()-t0,
                fallback={"fallback_reason":reason,"provider":"deepseek","prompt_size":len(prompt)},
                note=f"exception {type(e).__name__}")
        return None, {"provider":"deepseek","ok":False}

def daemon_alive():
    try:
        out = subprocess.run(["powershell","-NoProfile","-Command",
            "(Get-CimInstance Win32_Process -Filter \"Name like 'python%'\" | Where-Object {$_.CommandLine -like '*brain.daemon*'}).ProcessId"],
            capture_output=True, text=True, timeout=20).stdout.strip()
        txt = DLOG.read_text(encoding="utf-8", errors="replace")
        return bool(out) and txt.count("protective HALT") == 0
    except Exception:  # noqa: BLE001
        return False

def main():
    R = {"started": now(), "trace": TRACE, "deepseek_key": DEEPSEEK_OK,
         "predictions": [], "pairs": [], "voided": [], "stops": []}
    rng = random.Random(20260818)

    # ═══ فاز ۱ — ۱۵ جفت پروپوزال (هم‌کلاس، با پیش‌بینی پیوندی و داور کور) ═══
    Q = ("پیشنهاد بده: کوچک‌ترین گامِ بعدیِ قابل‌تست برای بهبود چرخهٔ یادگیریِ حافظهٔ کانونی OCTOPUS در ۲۴ ساعت آینده. فقط یک جمله.")
    for i in range(15):
        if time.time()-T0 > HARD_MIN*60 or not daemon_alive():
            R["stops"].append(f"pair_{i}"); break
        con = sqlite3.connect(f"file:{CANON}?mode=ro", uri=True)
        rows = con.execute("SELECT memory_id, content, confidence, valid_to FROM memory WHERE admission_state='ADMITTED' "
                           "AND confidence IS NOT NULL AND confidence!='' AND valid_to IS NOT NULL AND valid_to!='' "
                           "ORDER BY created_at DESC LIMIT 3").fetchall()
        con.close()
        ev = " | ".join(f"[{r[0]} conf={r[2]}] {r[1][:90]}" for r in rows)
        pid = f"cl1-live3-pair-{i+1:02d}"
        LED.append_prediction(prediction_id=pid,
            content=f"pair{i+1}: blind judge prefers evidence-conditioned proposal over baseline",
            trace_id=TRACE, source="cortex", model="router-auto", confidence=0.55, eval_window="immediate")
        base_txt, mb = call(Q, "baseline", pid)
        cond_txt, mc = call(Q + "\n\nشواهد بازیابی‌شده (provenance‌دار):\n" + ev, "conditioned", pid)
        if base_txt is None or cond_txt is None:
            R["voided"].append({"pair": i+1, "base_ok": mb.get("ok"), "cond_meta": mc})
            LED.attach_outcome(prediction_id=pid, outcome="VOID_PROVIDER_FAILURE (availability-only, not miss)")
            receipt("PAIR_VOID", prediction_id=pid, note=f"base_ok={mb.get('ok')} cond={mc}")
            continue
        a_is_cond = rng.random() < 0.5
        A, B = (cond_txt, base_txt) if a_is_cond else (base_txt, cond_txt)
        judge_q = (f"کدام پیشنهاد برای سؤال زیر خاص‌تر و قابل‌تست‌تر است؟ فقط جواب بده: A یا B.\n"
                   f"سؤال: {Q}\nA: {A[:180]}\nB: {B[:180]}")
        j_txt, mj = call(judge_q[:FUGU_SAFE], "judge", pid)
        cond_won = None
        if j_txt:
            j = j_txt.strip().upper()[:4]
            if j.startswith("A"): cond_won = a_is_cond
            elif j.startswith("B"): cond_won = not a_is_cond
        if cond_won is None:
            R["voided"].append({"pair": i+1, "judge": mj})
            LED.attach_outcome(prediction_id=pid, outcome="VOID_JUDGE_UNREADABLE")
            receipt("PAIR_VOID", prediction_id=pid, note="judge output unreadable")
            continue
        LED.attach_outcome(prediction_id=pid, outcome=f"{'hit' if cond_won else 'miss'}: blind judge, cond_was={'A' if a_is_cond else 'B'}")
        R["predictions"].append({"id": pid, "conf": 0.55, "hit": cond_won, "type": "pair_judged"})
        R["pairs"].append({"round": i+1, "baseline_sha": sha(base_txt), "cond_sha": sha(cond_txt),
                           "evidence_ids": [r[0] for r in rows], "cond_won": cond_won,
                           "cond_position": "A" if a_is_cond else "B",
                           "task_class": "next-testable-step-24h"})
        receipt("PAIR_COMPLETE", prediction_id=pid, note=f"cond_won={cond_won}")
        if ST["calls"] >= 10 and ST["errors"]/ST["calls"] >= 0.05 and ST["fallbacks"] == 0:
            R["stops"].append("error-rate-no-fallback"); break

    # ═══ فاز ۲ — ۳۰ پیش‌بینی رویداد دیمون ═══
    plan = [("A",75,0.90,"≥1 new task.completed within {w}s")]*16 + [("B",75,0.10,"a task.failed within {w}s")]*8 + [("C",120,0.70,"≥2 new task.completed within {w}s")]*6
    for i,(typ,w,conf,tmpl) in enumerate(plan):
        if time.time()-T0 > HARD_MIN*60 or not daemon_alive():
            R["stops"].append(f"dpred_{i}"); break
        txt0 = DLOG.read_text(encoding="utf-8", errors="replace")
        d0,f0 = txt0.count("task.completed"), txt0.count("task.failed")
        pid = f"cl1-live3-d-{typ}-{i+1:02d}"
        LED.append_prediction(prediction_id=pid, content=f"daemon: {tmpl.format(w=w)} (d={d0},f={f0})",
                              trace_id=TRACE, source="cortex", model="owner-observer",
                              confidence=conf, eval_window=f"{w}s")
        receipt("PREDICTION_REGISTERED", prediction_id=pid, note=f"w={w}s conf={conf} type={typ}")
        time.sleep(w)
        txt1 = DLOG.read_text(encoding="utf-8", errors="replace")
        d1,f1 = txt1.count("task.completed"), txt1.count("task.failed")
        hit = (d1>d0) if typ=="A" else ((f1>f0) if typ=="B" else (d1-d0>=2))
        LED.attach_outcome(prediction_id=pid, outcome=f"{'hit' if hit else 'miss'}: d {d0}->{d1}, f {f0}->{f1}")
        R["predictions"].append({"id":pid,"conf":conf,"hit":hit,"type":f"daemon_{typ}"})
        receipt("OUTCOME_ATTACH", prediction_id=pid, note=f"hit={hit} d {d0}->{d1}")

    # ═══ فاز ۳ — پوشش رکوردهای واجد شرایط + جمع‌بندی ═══
    con = sqlite3.connect(f"file:{CANON}?mode=ro", uri=True)
    elig = con.execute("SELECT COUNT(*), SUM(valid_to IS NOT NULL AND valid_to!=''), SUM(confidence IS NOT NULL AND confidence!=''),"
                       " SUM(provenance_json IS NOT NULL AND provenance_json!=''), SUM(created_at IS NOT NULL AND created_at!='')"
                       " FROM memory WHERE admission_state='ADMITTED' AND created_at > '2026-08-18T23:00'").fetchone()
    con.close()
    R["coverage_eligible"] = {"n": elig[0], "expiry": elig[1], "confidence": elig[2], "provenance": elig[3], "timestamp": elig[4]}
    elig_preds = R["predictions"]
    n = len(elig_preds)
    R["summary"] = {"eligible_outcomes": n, "hits": sum(1 for p in elig_preds if p["hit"]),
                    "brier": round(sum((p["conf"]-(1 if p["hit"] else 0))**2 for p in elig_preds)/n,4) if n else None,
                    "voided": len(R["voided"]), "calls": dict(ST)}
    R["finished"] = now(); R["elapsed_min"] = round((time.time()-T0)/60,1)
    (L3/"live3-run-report.json").write_text(json.dumps(R,ensure_ascii=False,indent=1,default=str),encoding="utf-8")
    return R

if __name__ == "__main__":
    print(json.dumps(main(), ensure_ascii=False, indent=1, default=str))
