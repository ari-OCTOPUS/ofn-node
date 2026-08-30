#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""live1_driver.py — آزمایشِ CORE-LIVE-1 (مالک: OWNER_PROMOTE_CORE_LIVE_1).

پنجره: ۳۰ دقیقه سقف · provider فقط از درِ واحدِ موجود (ProviderRouter→model_router)
· per_call_cap 0.50 AUD · hard_stop 12 AUD · concurrency=1 · external_action=PROPOSE_ONLY.
اجباری: dry-receipt محلی پیش از اولین فراخوانی؛ prediction پیش از outcome؛
پروپوزالِ baseline در برابر evidence-conditioned؛ admission فقط از گیت.
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(r"F:/backup")
L1 = ROOT / "06-EVIDENCE/CL01-191-20260818-2233/live1"
RECEIPTS = L1 / "API-RECEIPTS.jsonl"
PRED_DB = ROOT / "_ops/state/predictions.db"
CANON = ROOT / "_ops/state/memory/memory.db"
DAEMON_LOG = ROOT / "4d_system/outputs/daemon-launch4b.err.log"

os.environ["OCTOPUS_WIRE_MEMORY_GATE"] = "1"   # فقط در همین فرایندِ آزمایش

for p in (str(ROOT / "_ops"), str(ROOT / "_ops/cortex"), str(ROOT / "_ops/memory"),
          str(ROOT / "_ops/outcomes"), str(ROOT / "4d_system")):
    if p not in sys.path:
        sys.path.insert(0, p)

RUN_T0 = time.time()
TRACE = "cl1-live1-" + datetime.now(timezone.utc).strftime("%H%M%S")
PER_CALL_CAP_AUD = 0.50


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _sha(t: str) -> str:
    return hashlib.sha256(str(t).encode("utf-8", "replace")).hexdigest()


def _budget_remaining() -> dict:
    try:
        b = json.loads((ROOT / "_ops/budget/budget-state.json").read_text(encoding="utf-8"))
        return {"date": b.get("date"), "spent_today_usd": b.get("spent_today_usd"),
                "halted": b.get("halted"), "cap_audit": 15.0, "hard_stop_audit": 12.0}
    except Exception as e:  # noqa: BLE001
        return {"error": type(e).__name__}


def receipt(*, provider, model, prompt, output, latency_s, tokens, cost,
            kind, prediction_id=None, admission=None, note="") -> dict:
    row = {"schema": "cl1-live1-receipt/1", "kind": kind, "trace_id": TRACE,
           "parent_id": "cl01-core-live-1", "timestamp": _now(), "provider": provider,
           "model": model, "input_sha256": _sha(prompt), "output_sha256": _sha(output or ""),
           "tokens": tokens, "cost_aud": cost, "latency_s": round(float(latency_s), 3),
           "retry": 0, "budget": _budget_remaining(), "per_call_cap_audit": PER_CALL_CAP_AUD,
           "prediction_id": prediction_id, "admission_decision": admission, "note": note}
    with open(RECEIPTS, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(row, ensure_ascii=False) + "\n")
    return row


def main() -> dict:
    report = {"started": _now(), "trace": TRACE, "steps": []}

    # ── گیت ورود: dry-receipt محلی، پیش از هر فراخوانی provider ──
    receipt(provider="dry-run", model="none", prompt="preflight", output="", latency_s=0.0,
            tokens=0, cost=0.0, kind="DRY_LOCAL_RECEIPT",
            note="valid local dry receipt emitted before first provider request")
    report["steps"].append("dry_receipt_ok")

    import provider_adapter as pa                                 # درِ واحد موجود
    from memory.prediction_ledger import PredictionLedger            # noqa: E402 (4d path)
    led = PredictionLedger(PRED_DB)

    # ── ۱) prediction پیش از outcome — رویداد مستقلِ دیمون ──
    log_before = DAEMON_LOG.read_text(encoding="utf-8", errors="replace").count("task.completed")
    pid1 = "cl1-pred-0001"
    led.append_prediction(prediction_id=pid1,
                          content=(f"در ۹۰ ثانیهٔ آینده، لاگ دیمون ۴d حداقل یک "
                                   f"'task.completed' تازه ثبت می‌کند (baseline count={log_before})"),
                          trace_id=TRACE, source="cortex", model="owner-observer",
                          confidence=0.85, eval_window="90s")
    report["steps"].append("prediction_recorded_before_outcome")

    # ── ۲) بازیابی از canonical (با provenance) ──
    import sqlite3
    con = sqlite3.connect(f"file:{CANON}?mode=ro", uri=True)
    rows = con.execute("SELECT memory_id, content, trust, provenance_json, confidence, valid_to "
                       "FROM memory WHERE admission_state='ADMITTED' ORDER BY created_at DESC LIMIT 5"
                       ).fetchall()
    con.close()
    evidence_txt = " | ".join(f"[{r[0]} t={r[2]} conf={r[4]} exp={r[5]}] {r[1][:120]}" for r in rows[:3])
    report["retrieval"] = {"n_admitted_sampled": len(rows),
                           "provenance_present": all(r[3] for r in rows),
                           "evidence_preview": evidence_txt[:200]}
    report["steps"].append("retrieval_from_canonical")

    # ── ۳) پروپوزال دوبل: baseline بدون شاهد در برابر evidence-conditioned ──
    Q = ("پیشنهاد بده: کوچک‌ترین گام بعدیِ قابل‌تست برای بهبود چرخهٔ یادگیریِ "
         "حافظهٔ کانونی OCTOPUS در ۲۴ ساعت آینده. فقط یک جمله، executable=false.")
    outs = {}
    for kind, prompt in (("baseline", Q),
                         ("evidence_conditioned", Q + "\n\nشواهد بازیابی‌شده از حافظهٔ کانونی (با provenance):\n" + evidence_txt)):
        t0 = time.time()
        try:
            resp = pa.router().ask(prompt, max_tokens=200, temperature=0.0,
                                   trace_id=TRACE, task="cl1-live1-" + kind)
            lat = time.time() - t0
            text = getattr(resp, "text", None) or str(getattr(resp, "content", "") or "")
            ok = bool(getattr(resp, "success", False))
            model = str(getattr(resp, "model", "") or getattr(resp, "provider", "") or "unknown")
            tokens = getattr(resp, "tokens", None) or getattr(resp, "usage", None)
            cost = getattr(resp, "cost", None)
            outs[kind] = text
            receipt(provider=model.split("/")[0], model=model, prompt=prompt, output=text,
                    latency_s=lat, tokens=tokens, cost=cost, kind="PROVIDER_CALL_" + kind.upper(),
                    note=f"success={ok}")
            report["steps"].append(f"ask_{kind}_ok={ok}")
        except Exception as e:  # noqa: BLE001 — خطا هم شاهد است
            receipt(provider="error", model="error", prompt=prompt, output="",
                    latency_s=time.time() - t0, tokens=0, cost=None,
                    kind="PROVIDER_CALL_" + kind.upper(),
                    note=f"{type(e).__name__}: {str(e)[:120]}")
            report["steps"].append(f"ask_{kind}_failed:{type(e).__name__}")

    changed = bool(outs.get("baseline")) and bool(outs.get("evidence_conditioned")) \
        and outs["baseline"].strip() != outs["evidence_conditioned"].strip()
    report["evidence_changed_proposal"] = changed
    report["proposal_baseline"] = (outs.get("baseline") or "")[:400]
    report["proposal_evidence_conditioned"] = (outs.get("evidence_conditioned") or "")[:400]

    # ── ۴) admission از مسیر گیت (خروجی LLM + شاهد = receiptها) ──
    adm_decision = "SKIPPED_NO_LLM_OUTPUT"
    if outs.get("evidence_conditioned"):
        import memory_store as ms
        import gate as gate_mod
        from admission import Admission
        from contradiction_radar import ContradictionRadar
        store = ms.MemoryStore(path=CANON)
        g = gate_mod.MemoryGate(store)
        radar = ContradictionRadar(store)
        g.contradiction_checker = lambda content, mid: radar.check_against_store(content) or []
        cand = {"namespace": "procedural", "content": "cl1-live1: " + outs["evidence_conditioned"][:300],
                "trace_id": TRACE, "parent_id": "cl01-core-live-1", "timestamp": _now(),
                "actor": "live1-driver", "source": "llm", "schema_version": "1",
                "idempotency_key": TRACE + "-mem1", "confidence": "0.6",
                "evidence_ref": "API-RECEIPTS.jsonl#" + TRACE,
                "tenant_id": "personal", "project_id": "octopus-core", "agent_id": "live1-driver"}
        out = Admission(store, g, radar, state_dir=CANON.parent).admit(cand)
        adm_decision = out["decision"]
        report["steps"].append(f"admission={adm_decision}")

    # ── ۵) outcome پیش‌بینی (بعد از ۹۰ ثانیه) ──
    time.sleep(max(0.0, 90 - (time.time() - RUN_T0)))
    log_after = DAEMON_LOG.read_text(encoding="utf-8", errors="replace").count("task.completed")
    hit = log_after > log_before
    led.attach_outcome(prediction_id=pid1, outcome=f"{'hit' if hit else 'miss'}: count {log_before}->{log_after}")
    report["prediction_outcome"] = {"id": pid1, "hit": hit,
                                    "before": log_before, "after": log_after}
    receipt(provider="observer", model="none", prompt="daemon-log-watch", output=str(hit),
            latency_s=90.0, tokens=0, cost=0.0, kind="OUTCOME_ATTACH",
            prediction_id=pid1, admission=adm_decision)
    report["finished"] = _now()
    report["elapsed_s"] = round(time.time() - RUN_T0, 1)
    (L1 / "live1-run-report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
    return report


if __name__ == "__main__":
    print(json.dumps(main(), ensure_ascii=False, indent=1))
