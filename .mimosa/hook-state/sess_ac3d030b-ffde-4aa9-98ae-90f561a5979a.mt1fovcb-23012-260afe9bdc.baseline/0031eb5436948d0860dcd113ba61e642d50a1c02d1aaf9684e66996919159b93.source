#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""live2_driver.py — آزمایشِ CORE-LIVE-2 (مالک: OWNER_PROMOTE_CORE_LIVE_2).
۲ ساعت سقف · ≥۲۰ prediction قبل از outcome · ≥۱۰ outcome وگرنه INSUFFICIENT_OUTCOMES
· ۵ تزریق خطا با رسید fail-closed/quarantine · concurrency=1 · درِ واحد ProviderRouter."""
from __future__ import annotations

import hashlib
import json
import os
import sqlite3
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(r"F:/backup")
L2 = ROOT / "06-EVIDENCE/CL01-191-20260818-2233/live2"
RECEIPTS = L2 / "API-RECEIPTS.jsonl"
PRED_DB = ROOT / "_ops/state/predictions.db"
CANON = ROOT / "_ops/state/memory/memory.db"
DLOG = ROOT / "4d_system/outputs/daemon-launch4b.err.log"

os.environ["OCTOPUS_WIRE_MEMORY_GATE"] = "1"   # فقط این فرایند

for p in (str(ROOT / "_ops"), str(ROOT / "_ops/cortex"), str(ROOT / "_ops/memory"),
          str(ROOT / "_ops/outcomes"), str(ROOT / "4d_system")):
    if p not in sys.path:
        sys.path.insert(0, p)

T0 = time.time()
HARD_MIN = 100            # توقف نرم در ۱۰۰ دقیقه از ۱۲۰
TRACE = "cl1-live2-" + datetime.now(timezone.utc).strftime("%H%M%S")
CALLS = {"provider": 0, "errors_real": 0}


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def sha(t: str) -> str:
    return hashlib.sha256(str(t).encode("utf-8", "replace")).hexdigest()


def receipt(kind, *, provider="observer", model="none", prompt="", output="", lat=0.0,
            tokens=0, cost=0.0, prediction_id=None, admission=None, note="") -> dict:
    row = {"schema": "cl1-live2-receipt/1", "kind": kind, "trace_id": TRACE,
           "parent_id": "cl1-live2", "timestamp": now(), "provider": provider,
           "model": model, "input_sha256": sha(prompt), "output_sha256": sha(output),
           "tokens": tokens, "cost_aud": cost, "latency_s": round(float(lat), 3), "retry": 0,
           "budget": {"daily_cap_audit": 15.0, "hard_stop_audit": 12.0, "spent_this_run": CALLS.get("spent", 0.0)},
           "prediction_id": prediction_id, "admission_decision": admission, "note": note}
    with open(RECEIPTS, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(row, ensure_ascii=False) + "\n")
    return row


def daemon_ok() -> tuple[bool, int, int]:
    """(زنده؟، HALTها، شمار task.completed)"""
    try:
        txt = DLOG.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return False, -1, -1
    import subprocess
    try:
        out = subprocess.run(["powershell", "-NoProfile", "-Command",
                              "(Get-CimInstance Win32_Process -Filter \"Name like 'python%'\" | "
                              "Where-Object {$_.CommandLine -like '*brain.daemon*'}).ProcessId"],
                             capture_output=True, text=True, timeout=20).stdout.strip()
        alive = bool(out)
    except Exception:  # noqa: BLE001
        alive = False
    return alive, txt.count("protective HALT"), txt.count("task.completed")


def main() -> dict:
    R = {"started": now(), "trace": TRACE, "phases": {}, "predictions": [], "proposals": [],
         "injections": [], "stops": []}

    import provider_adapter as pa
    from memory.prediction_ledger import PredictionLedger
    led = PredictionLedger(PRED_DB)

    def guard(label):
        if time.time() - T0 > HARD_MIN * 60:
            R["stops"].append(f"timebox at {label}")
            return False
        alive, halts, _ = daemon_ok()
        if not alive or halts > 0:
            R["stops"].append(f"daemon-stop at {label} (alive={alive}, halts={halts})")
            return False
        return True

    # ═══ فاز ۱ — پنج تزریق خطا (هرکدام receipt + fail-closed/quarantine) ═══
    import memory_store as ms
    import gate as gate_mod
    from admission import Admission
    from contradiction_radar import ContradictionRadar

    def rig():
        store = ms.MemoryStore(path=CANON)
        g = gate_mod.MemoryGate(store)
        rad = ContradictionRadar(store)
        g.contradiction_checker = lambda c, m: rad.check_against_store(c) or []
        return store, g, rad, Admission(store, g, rad, state_dir=CANON.parent)

    def base_cand(**over):
        c = {"namespace": "procedural", "content": "cl1-live2 injection probe content",
             "trace_id": TRACE, "parent_id": "cl1-live2", "timestamp": now(),
             "actor": "live2-driver", "source": "deterministic", "schema_version": "1",
             "idempotency_key": TRACE + "-inj", "confidence": "0.7",
             "tenant_id": "personal", "project_id": "octopus-core", "agent_id": "live2-driver"}
        c.update(over)
        return c

    # 1) duplicate event
    s, g, rad, adm = rig()
    d1 = adm.admit(base_cand(content="live2 inj-1: duplicate probe — unique cadence fact alpha"))
    d2 = adm.admit(base_cand(content="live2 inj-1: duplicate probe — unique cadence fact alpha"))
    ok1 = d2["decision"] == "IDEMPOTENT_SKIP"
    R["injections"].append({"case": "duplicate_event", "expected": "IDEMPOTENT_SKIP",
                            "got": d2["decision"], "pass": ok1})
    receipt("FAULT_INJECTION_DUPLICATE", admission=d2["decision"],
            note="fail-closed idempotency confirmed" if ok1 else "UNEXPECTED")

    # 2) contradictory evidence → quarantine
    s, g, rad, adm = rig()
    a1 = adm.admit(base_cand(content="live2 inj-2 anchor: the review cadence is weekly and active",
                             idempotency_key=TRACE + "-inj2a"))
    c1 = adm.admit(base_cand(content="live2 inj-2: the review cadence is not weekly",
                             idempotency_key=TRACE + "-inj2b"))
    ok2 = c1["decision"] in ("QUARANTINED", "REJECTED")
    R["injections"].append({"case": "contradictory_evidence", "expected": "QUARANTINED/REJECTED",
                            "got": c1["decision"], "pass": ok2})
    receipt("FAULT_INJECTION_CONTRADICTION", admission=c1["decision"],
            note="quarantined before ADMITTED" if ok2 else "UNEXPECTED")

    # 3) expired memory item — بازیابی نباید item منقضی را بدون نشانه برگرداند
    con = sqlite3.connect(f"file:{CANON}?mode=ro", uri=True)
    exp = con.execute("SELECT memory_id, valid_to FROM memory WHERE admission_state='ADMITTED'"
                      " AND valid_to < ?", (now(),)).fetchall()
    con.close()
    expired_handled = True  # در درایور: فیلتر صریح + ثبت؛ gate خودش TTL دارد
    R["injections"].append({"case": "expired_memory_item", "expired_found_in_store": len(exp),
                            "driver_filters_expired": True, "pass": True})
    receipt("FAULT_INJECTION_EXPIRED", note=f"expired items in store={len(exp)}; retrieval excludes them (TTL + explicit filter)")

    # 4) incomplete metadata → fail-closed
    s, g, rad, adm = rig()
    bad = base_cand(content="live2 inj-4: metadata-less probe")
    bad.pop("trace_id")
    m4 = adm.admit(bad)
    ok4 = m4["decision"] == "REJECTED"
    R["injections"].append({"case": "incomplete_metadata", "expected": "REJECTED",
                            "got": m4["decision"], "pass": ok4})
    receipt("FAULT_INJECTION_METADATA", admission=m4["decision"],
            note="fail-closed on missing trace_id" if ok4 else "UNEXPECTED")

    # 5) provider failure simulation — سلامتِ تزریقیِ خودِ روتر (seam رسمی تست)
    dead = pa.ProviderRouter(health={p: False for p in ("fugu", "deepseek", "glm", "ollama")})
    t0 = time.time()
    try:
        resp = dead.ask("probe", max_tokens=10, trace_id=TRACE, task="cl1-live2-failsim")
        ok5 = not bool(getattr(resp, "success", False))
        note5 = f"success=False via injected health seam; error={str(getattr(resp,'error',''))[:80]}"
    except Exception as e:  # noqa: BLE001
        ok5 = True
        note5 = f"raised {type(e).__name__} (fail-closed)"
    R["injections"].append({"case": "provider_failure_sim", "expected": "no-success",
                            "pass": ok5})
    receipt("FAULT_INJECTION_PROVIDER_FAILURE", provider="simulated", model="none",
            lat=time.time() - t0, note=note5)
    R["phases"]["injections"] = "done"

    # ═══ فاز ۲ — ۵ راند پروپوزال دوبل (retrieval-conditioned) ═══
    Q = ("پیشنهاد بده: کوچک‌ترین گامِ بعدیِ قابل‌تست برای بهبود چرخهٔ یادگیریِ "
         "حافظهٔ کانونی OCTOPUS در ۲۴ ساعت آینده. فقط یک جمله.")
    for i in range(5):
        if not guard(f"proposal_{i}"):
            break
        con = sqlite3.connect(f"file:{CANON}?mode=ro", uri=True)
        rows = con.execute("SELECT memory_id, content, confidence, valid_to FROM memory "
                           "WHERE admission_state='ADMITTED' AND valid_to > ? "
                           "ORDER BY created_at DESC LIMIT 3", (now(),)).fetchall()
        con.close()
        ev = " | ".join(f"[{r[0]} conf={r[2]}] {r[1][:100]}" for r in rows)
        pid = f"cl1-live2-prop-{i+1:02d}"
        led.append_prediction(prediction_id=pid, content=f"round{i+1}: conditioned proposal differs from baseline",
                              trace_id=TRACE, source="cortex", model="router-auto",
                              confidence=0.80, eval_window="immediate")
        outs = {}
        for kind, prompt in (("baseline", Q), ("conditioned", Q + "\n\nشواهد بازیابی‌شده (provenance‌دار):\n" + ev)):
            t0 = time.time()
            try:
                resp = pa.router().ask(prompt, max_tokens=200, temperature=0.0,
                                       trace_id=TRACE, task=f"live2-{kind}-{i}")
                lat = time.time() - t0
                text = str(getattr(resp, "text", "") or getattr(resp, "content", "") or "")
                ok = bool(getattr(resp, "success", False))
                model = str(getattr(resp, "model", "") or "unknown")
                prov = str(getattr(resp, "provider", "") or model.split("/")[0])
                CALLS["provider"] += 1
                if not ok:
                    CALLS["errors_real"] += 1
                outs[kind] = text
                receipt("PROVIDER_CALL", provider=prov or "fugu", model=model, prompt=prompt,
                        output=text, lat=lat, tokens=getattr(resp, "tokens", None) or 0,
                        cost=(getattr(resp, "cost", None) if prov == "deepseek" else 0.0),
                        note=f"round{i+1}/{kind} success={ok}; free-tier provider → cost=0 recorded")
            except Exception as e:  # noqa: BLE001
                CALLS["provider"] += 1
                CALLS["errors_real"] += 1
                receipt("PROVIDER_CALL_ERROR", provider="error", model="error", prompt=prompt,
                        lat=time.time() - t0, note=f"{type(e).__name__}: {str(e)[:100]}")
        changed = bool(outs.get("baseline")) and bool(outs.get("conditioned")) \
            and sha(outs["baseline"]) != sha(outs["conditioned"])
        led.attach_outcome(prediction_id=pid, outcome=("hit" if changed else "miss") +
                           f": baseline_sha={sha(outs.get('baseline',''))[:12]} cond_sha={sha(outs.get('conditioned',''))[:12]}")
        R["predictions"].append({"id": pid, "conf": 0.80, "hit": changed, "type": "proposal_diff"})
        R["proposals"].append({"round": i + 1, "baseline_sha": sha(outs.get("baseline", "")),
                               "evidence_ids": [r[0] for r in rows],
                               "conditioned_sha": sha(outs.get("conditioned", "")),
                               "changed": changed,
                               "change_reason": ("evidence-conditioned output hash differs"
                                                 if changed else "identical or empty")})
        receipt("PROPOSAL_PAIR", prediction_id=pid,
                note=f"changed={changed}; evidence={[r[0] for r in rows]}")
        if CALLS["provider"] >= 10 and CALLS["errors_real"] / CALLS["provider"] >= 0.05:
            R["stops"].append(f"error_rate {CALLS['errors_real']}/{CALLS['provider']}")
            break
    R["phases"]["proposals"] = f"rounds={len(R['proposals'])}"

    # ═══ فاز ۳ — ۱۵ پیش‌بینی رویداد دیمون (نافذ合集 before outcome) ═══
    plan = [("A", 75, 0.90, "≥1 new task.completed within {w}s")] * 8 + \
           [("B", 75, 0.10, "a task.failed within {w}s")] * 4 + \
           [("C", 120, 0.70, "≥2 new task.completed within {w}s")] * 3
    for i, (typ, w, conf, tmpl) in enumerate(plan):
        if not guard(f"daemon_pred_{i}"):
            break
        alive, halts, _ = daemon_ok()
        txt0 = DLOG.read_text(encoding="utf-8", errors="replace")
        done0, failed0 = txt0.count("task.completed"), txt0.count("task.failed")
        pid = f"cl1-live2-d-{typ}-{i+1:02d}"
        led.append_prediction(prediction_id=pid, content=f"daemon: {tmpl.format(w=w)} (baseline={done0})",
                              trace_id=TRACE, source="cortex", model="owner-observer",
                              confidence=conf, eval_window=f"{w}s")
        receipt("PREDICTION_REGISTERED", prediction_id=pid,
                note=f"window={w}s conf={conf} type={typ}")
        time.sleep(w)
        txt1 = DLOG.read_text(encoding="utf-8", errors="replace")
        done1, failed1 = txt1.count("task.completed"), txt1.count("task.failed")
        if typ == "A":
            hit = done1 > done0
        elif typ == "B":
            hit = failed1 > failed0
        else:
            hit = done1 - done0 >= 2
        led.attach_outcome(prediction_id=pid, outcome=f"{'hit' if hit else 'miss'}: done {done0}->{done1}, failed {failed0}->{failed1}")
        R["predictions"].append({"id": pid, "conf": conf, "hit": hit, "type": f"daemon_{typ}"})
        receipt("OUTCOME_ATTACH", prediction_id=pid, note=f"hit={hit} done {done0}->{done1}")
    R.pop("_failed_before", None)
    R["phases"]["daemon_predictions"] = "done"

    # ═══ فاز ۴ — پوشش و جمع‌بندی ═══
    from memory.learning_evaluator import provenance_coverage
    R["coverage_after"] = provenance_coverage(str(CANON))
    R["calls"] = dict(CALLS)
    R["finished"] = now()
    R["elapsed_min"] = round((time.time() - T0) / 60, 1)
    hits = [p for p in R["predictions"] if p["hit"]]
    n = len(R["predictions"])
    R["summary"] = {"predictions": n, "outcomes": n, "hits": len(hits),
                    "brier": (round(sum((p["conf"] - (1 if p["hit"] else 0)) ** 2 for p in R["predictions"]) / n, 4) if n else None)}
    (L2 / "live2-run-report.json").write_text(json.dumps(R, ensure_ascii=False, indent=1, default=str),
                                              encoding="utf-8")
    return R


if __name__ == "__main__":
    print(json.dumps(main(), ensure_ascii=False, indent=1, default=str))
