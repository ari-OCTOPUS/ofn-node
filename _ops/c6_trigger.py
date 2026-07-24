#!/usr/bin/env python3
"""c6_trigger.py — runtime trigger برای حلقهٔ self-improvement C6 (مرحلهٔ ۴).

تولید مثل = خودبهبودیِ کد. این trigger روزی یک‌بار (از daily tick) صدا زده می‌شود،
یک فرضیه از `_ops/state/c6/hypothesis-queue.jsonl` برمی‌دارد، آن را به‌صورتِ یک
آزمایشِ sandbox اجرا می‌کند، و نتیجه را به‌عنوانِ RFC card (propose-only) به مالک
می‌دهد. **هیچِ auto-apply/merge/deploy** (governance مرزِ نهایی).

گیت‌ها (همگی لازم):
  - OCTOPUS_WIRE_C6_RESEARCH (env، پیش‌فرض خاموش)
  - ACTIVATION-C6-RESEARCH.flag (فایلِ مالک — فقط خودش می‌سازد)
  - organ_gate ARCHITECT_SYS (از داخلِ run_experiment اگر پولی باشد)
  - governance: فقط test_in_sandbox مجاز است.
سقف: ۱ آزمایش/روز (daily tick)، AU$0.50، ۵۰k token، ۱۲۰s.

صدا زدن:
  from c6_trigger import c6_research_beat
  c6_research_beat(state_dir=..., channel=..., beat=N)

fail-soft: هر خطا → alert + ادامه (هرگز daily tick را نمی‌کشد).
"""
from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

_HERE = Path(__file__).resolve().parent
for _p in (str(_HERE), str(_HERE / "outcomes"), str(_HERE / "memory"), str(_HERE / "budget")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import opslib  # noqa: E402

ENV_FLAG = "OCTOPUS_WIRE_C6_RESEARCH"
ACT_FLAG = opslib.OPS / "ACTIVATION-C6-RESEARCH.flag"
QUEUE = opslib.STATE_DIR / "c6" / "hypothesis-queue.jsonl"
LEDGER = opslib.STATE_DIR / "c6" / "research-ledger.jsonl"
# سقفِ روزانهٔ محافظه‌کارانه (نیمی از ARCHITECT_SYS floor، با headroom).
DAILY_BUDGET = {"cost_aud": 0.50, "time_s": 120, "tokens": 50000, "max_experiments": 1}


def flag_on() -> bool:
    """هر دو گیت لازم: env flag + فایلِ فعال‌سازیِ مالک."""
    if not str(os.environ.get(ENV_FLAG, "")).strip().lower() in ("1", "true", "yes", "on"):
        return False
    if not ACT_FLAG.exists():
        return False
    return True


def _pop_next_hypothesis() -> "dict | None":
    """اولین فرضیهٔ status=PENDING را برمی‌دارد و آن را می‌بندد (idempotent-safe)."""
    if not QUEUE.exists():
        return None
    try:
        lines = QUEUE.read_text("utf-8").splitlines()
    except Exception:  # noqa: BLE001
        return None
    out, found = [], None
    for ln in lines:
        ln = ln.strip()
        if not ln:
            continue
        try:
            d = json.loads(ln)
        except ValueError:
            out.append(ln)   # preserve malformed line
            continue
        if found is None and d.get("status") == "PENDING":
            d["status"] = "RUNNING"
            d["taken_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            found = d
        out.append(json.dumps(d, ensure_ascii=False))
    if found is not None:
        try:
            QUEUE.parent.mkdir(parents=True, exist_ok=True)
            QUEUE.write_text("\n".join(out) + "\n", encoding="utf-8")
        except Exception:  # noqa: BLE001
            return None
    return found


def _build_contract(h: dict) -> dict:
    """یک spec ساده از hypothesis می‌سازد (caller بعداً make_contract می‌زند)."""
    return {
        "question": str(h.get("question", "Can we improve a self-process?"))[:500],
        "hypothesis": str(h.get("hypothesis", ""))[:500],
        "stop_condition": str(h.get("stop_condition", "benchmarkGain measured or 1 run"))[:300],
        "verifier": str(h.get("verifier", "compare_frozen_baselines"))[:200],
        "expected_artifact": str(h.get("expected_artifact", "benchmark delta number"))[:200],
        "falsification_criteria": h.get("falsification_criteria",
                                        ["no measurable benchmark delta"]),
        "budget": DAILY_BUDGET,
        "tools": h.get("tools", ["test_in_sandbox", "compare_frozen_baselines"]),
        "created_at_hint": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }


def c6_research_beat(*, state_dir: str, channel=None, beat: int = 0) -> dict:
    """روزانه: یک فرضیه → آزمایش → RFC card. پشتِ دو گیت. fail-soft. صفر auto-apply."""
    if not flag_on():
        return {"ran": False, "reason": "flag-off"}
    try:
        import research_contract as _rc
        import research_loop as _rl
        import memory_store as _msx
        import gate as _gx
        import decision_receipt as _drx
        import outcome_store as _osx
        import learning_gate as _lg
    except Exception as e:  # noqa: BLE001
        opslib.alert([f"c6_research_beat import failed: {type(e).__name__}: {e}"])
        return {"ran": False, "reason": f"import-failed:{type(e).__name__}"}

    h = _pop_next_hypothesis()
    if h is None:
        return {"ran": False, "reason": "no-pending-hypothesis"}

    spec = _build_contract(h)
    try:
        contract = _rc.make_contract(spec)
    except Exception as e:  # noqa: BLE001 — فرضیهٔ بد نباید daily tick را بکشد
        opslib.alert([f"c6 contract invalid (hypothesis closed): {type(e).__name__}: {e}"])
        return {"ran": False, "reason": f"contract-invalid:{type(e).__name__}"}

    # experiment_fn + verifier_fn: از hypothesis.kind مشتق می‌شوند.
    experiment_fn, verifier_fn = _derive_fns(h, contract)

    sd = Path(state_dir)
    # storesِ واقعی (production learning stack — همان مسیرِ verdict).
    try:
        mdir = sd / "memory"; mdir.mkdir(parents=True, exist_ok=True)
        rdir = sd / "receipts"; rdir.mkdir(parents=True, exist_ok=True)
        odir = sd / "outcomes"; odir.mkdir(parents=True, exist_ok=True)
        _mem = _msx.MemoryStore(path=mdir / "memory.db")
        _rcp = _drx.DecisionReceiptStore(rdir / "receipts.db")
        _outc = _osx.OutcomeStore(path=odir / "outcomes.db")
        _gate = _gx.MemoryGate(_mem)
        budget = _rl.Budget(contract["budget"])
        ledger = _rl.ResearchLedger(LEDGER)
        result = _rl.run_experiment(
            contract=contract, experiment_fn=experiment_fn, verifier_fn=verifier_fn,
            budget=budget, ledger=ledger,
            receipt_store=_rcp, memory_gate=_gate, outcome_store=_outc,
            state_dir=str(sd), held_out_eval=_lg.fast_ledger_eval,
            cost_aud=0.0, tokens=0)
    except Exception as e:  # noqa: BLE001
        opslib.alert([f"c6 run_experiment failed: {type(e).__name__}: {e}"])
        return {"ran": False, "reason": f"run-failed:{type(e).__name__}"}

    verdict = result.get("verdict", "?")
    # M3: record the unified reproduction lifecycle (fail-soft; derives, holds no
    # authority). ADMITTED needs the memory gate; TRANSPLANTED (generational birth) is
    # an owner tap ONLY — never emitted here (merge_or_deploy stays FORBIDDEN).
    try:
        import c6_state_machine as _sm
        _cid = contract.get("contract_id", f"c6-{beat}")
        _sm.transition(state_dir=str(sd), contract_id=_cid, to_state="RUNNING",
                       result=result, receipt_store=_rcp)
        _final = _sm.derive(result)
        if _final in ("REJECTED", "QUARANTINED", "TERMINATED", "VERIFIED_NOT_ADMITTED"):
            _sm.transition(state_dir=str(sd), contract_id=_cid, to_state=_final,
                           result=result, receipt_store=_rcp)
        elif _final in ("ADMITTED", "PENDING_ADMISSION"):
            _sm.transition(state_dir=str(sd), contract_id=_cid, to_state="VERIFIED",
                           result=result, receipt_store=_rcp)
            _sm.transition(state_dir=str(sd), contract_id=_cid,
                           to_state="PENDING_ADMISSION", result=result, receipt_store=_rcp)
    except Exception as _e:  # noqa: BLE001 — recorder never kills the beat
        opslib.alert([f"c6 state-machine record skipped: {type(_e).__name__}: {_e}"])
    # نتیجه → RFC card به مالک (فقط اگر چیز ارزشمندی برای گفتن باشد).
    summary = _summarize(h, result)
    delivered = False
    # اگر کانال داده نشد (organism آن را پاس نمی‌دهد)، lazy از wiring بساز.
    _chan = channel
    if _chan is None:
        try:
            import wiring as _wiring
            _chan = _wiring.make_telegram_channel()
        except Exception:  # noqa: BLE001
            _chan = None
    if _chan is not None and hasattr(_chan, "rfc_card"):
        try:
            cid = contract.get("contract_id", f"c6-{beat}")[:60]
            delivered = _chan.rfc_card(rfc_id=f"c6-{cid}",
                                       summary=summary[:800])
        except Exception as e:  # noqa: BLE001 — کارت نباید beat را بکشد
            opslib.alert([f"c6 rfc_card delivery failed: {type(e).__name__}: {e}"])
    # بستنِ hypothesis با نتیجه
    _mark_hypothesis(h.get("id") or contract.get("contract_id"), verdict, delivered)
    return {"ran": True, "verdict": verdict, "delivered": delivered, "summary": summary}


def _derive_fns(h: dict, contract: dict):
    """experiment_fn + verifier_fn از نوعِ hypothesis. v1: فقط 'micro_benchmark'."""
    kind = str(h.get("kind", "micro_benchmark"))

    def experiment_fn(c, *, _h=h):
        # v1: یک micro-benchmark ساده که به‌صورتِ آفلاین اجرا می‌شود. مثالِ seed:
        # اندازه‌گیریِ latency search() روی memory (محصولاتِ دست‌نخورده، $0).
        # خروجی: dict با benchmarkGain قابلِ تفسیر.
        try:
            bench = _h.get("bench_fn") or _default_bench
            baseline = float(_h.get("baseline_ms", 0.0))
            measured = float(bench(_h))
            gain = max(0.0, baseline - measured) if baseline > 0 else 0.0
            return {"measured_ms": measured, "baseline_ms": baseline,
                    "benchmark_gain_ms": gain, "raw": _h.get("bench_label", "default")}
        except Exception as e:  # noqa: BLE001
            return {"error": f"{type(e).__name__}: {e}", "benchmark_gain_ms": 0.0}

    def verifier_fn(c, result):
        gain = float(result.get("benchmark_gain_ms", 0.0))
        return {"supported": gain > 0.0,
                "evidence": json.dumps(result, ensure_ascii=False)[:500],
                "benchmark_gain": gain,
                "risk": 0.1}

    return experiment_fn, verifier_fn


def _default_bench(h: dict) -> float:
    """بنچ‌مارکِ پیش‌فرضِ بی‌خطر و $0: latency یک عملیات خواندن.
    (در v1: فقط time.time دورِ یک read سبک؛ قابلِ تعویض با bench_fn در hypothesis.)"""
    t0 = time.time()
    # یک read سبک از state (صفر network/LLM) — نمونهٔ قابلِ تکرار.
    try:
        (opslib.STATE_DIR / "ORGANISM-STATE.json").read_bytes()
    except Exception:  # noqa: BLE001
        pass
    return (time.time() - t0) * 1000.0


def _summarize(h: dict, result: dict) -> str:
    v = result.get("verdict", "?")
    q = str(h.get("question", "?"))[:120]
    reason = str(result.get("reason", ""))[:160]
    mid = result.get("memory_id", "")
    return (f"C6 آزمایشِ خودبهبودی — verdict: {v}\n"
            f"پرسش: {q}\n"
            f"دلیل: {reason}\n"
            + (f"خاطره: {mid}\n" if mid else "")
            + "این یک proposal است؛ اعمال فقط با رأیِ شما.")


def _mark_hypothesis(hid: str, verdict: str, delivered: bool) -> None:
    """صف را با نتیجهٔ نهایی به‌روز کن."""
    if not QUEUE.exists() or not hid:
        return
    try:
        lines = QUEUE.read_text("utf-8").splitlines()
        out = []
        for ln in lines:
            ln = ln.strip()
            if not ln:
                continue
            try:
                d = json.loads(ln)
            except ValueError:
                out.append(ln)
                continue
            if d.get("id") == hid or d.get("status") == "RUNNING":
                d["status"] = "DONE"
                d["verdict"] = verdict
                d["card_delivered"] = bool(delivered)
                d["done_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            out.append(json.dumps(d, ensure_ascii=False))
        QUEUE.write_text("\n".join(out) + "\n", encoding="utf-8")
    except Exception:  # noqa: BLE001
        pass


def seed_default_hypothesis() -> bool:
    """اگر صف خالی است، یک فرضیهٔ نمونهٔ بی‌خطر اضافه کن (با اولین بوت)."""
    try:
        QUEUE.parent.mkdir(parents=True, exist_ok=True)
        if QUEUE.exists() and QUEUE.read_text("utf-8").strip():
            return False
        h = {
            "id": "seed-memory-latency-bench",
            "status": "PENDING",
            "kind": "micro_benchmark",
            "question": "Can we reduce self-process read latency below baseline?",
            "hypothesis": "A cached state read is faster than a re-parse each tick.",
            "stop_condition": "benchmarkGain measured in one offline run",
            "verifier": "compare_frozen_baselines",
            "expected_artifact": "measured latency delta in ms",
            "falsification_criteria": ["no measurable latency delta"],
            "baseline_ms": 5.0,
            "bench_label": "state-read",
            "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }
        with QUEUE.open("a", encoding="utf-8") as f:
            f.write(json.dumps(h, ensure_ascii=False) + "\n")
        return True
    except Exception:  # noqa: BLE001
        return False
