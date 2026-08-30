#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""research_loop.py — C6: حلقهٔ پژوهشِ حاکمیت‌شده (proposal-only، owner-gated، ضدخودفریبی).

می‌سازد ON: قرارداد (research_contract) + گاردهای constitution (governance.self_improvement_permits،
utility، consensus_promotes) + falsification + held-out (C3) + learning_gate (نتیجه فقط با verifier+outcome
وارد memory) + decision_receipt + durable_journal (checkpoint/restart) + research ledger.

قواعدِ سختِ مأموریت C6:
  - هر اکشن از `self_improvement_permits` می‌گذرد (fail-closed؛ merge/deploy/edit-verifier ممنوع).
  - budgetِ سخت (cost/time/token/experiments)؛ سرریز → terminate (`budget-exceeded`).
  - **bad conjecture terminate، نه بازنویسیِ بی‌نهایت:** falsify → hypothesis REJECTED، حلقه می‌ایستد.
  - هر آزمایش رسیدِ durable + outcome دارد؛ حلقه از durable_journal checkpoint/resume می‌کند.
  - نتیجه فقط وقتی وارد memory می‌شود که verifier سبز + held-out سبز + outcome ثبت (learning_gate).
  - regression/uncertaintyِ بالا → quarantine (نه commit).
  - **صفر auto-apply/merge/deploy/external-effect** — تولیدِ patch فقط پیشنهاد (owner gate).
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
import time
from pathlib import Path

_HERE = Path(__file__).resolve().parent
for _p in (str(_HERE), str(_HERE.parent), str(_HERE.parent / "budget"),
           str(_HERE.parent.parent / "PRE-0")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

FLAG = "OCTOPUS_WIRE_MEMORY_GATE"   # پژوهش نتیجه را از همان دروازهٔ memory می‌گذراند
MAX_REWRITES = 3                    # سقفِ بازنویسیِ conjecture (ضدِ حلقهٔ بی‌نهایت)
_TERMINAL_VERDICTS = ("accepted", "rejected", "quarantined", "verified-not-admitted")


def _governance():
    import governance  # noqa: WPS433
    return governance


def _permit(action: str) -> bool:
    try:
        return bool(_governance().self_improvement_permits(action))
    except Exception:  # noqa: BLE001 — بدونِ constitution → fail-closed
        return False


class ResearchLedger:
    """دفترِ پژوهشِ append-only: accepted/rejected/quarantined hypotheses + evidence."""

    def __init__(self, path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def append(self, rec: dict) -> None:
        self.append_strict(rec)

    def append_strict(self, rec: dict) -> bool:
        """C7-S3 (audit #4): appendِ acceptance-critical خطا را نمی‌بلعد — با fsync، و bool
        برمی‌گرداند تا accept بتواند به شکستِ ledger واکنش دهد."""
        try:
            with open(self.path, "a", encoding="utf-8") as f:
                f.write(json.dumps(rec, ensure_ascii=False, sort_keys=True) + "\n")
                f.flush()
                os.fsync(f.fileno())
            return True
        except Exception:  # noqa: BLE001
            return False

    def entries(self) -> list:
        if not self.path.exists():
            return []
        out = []
        for ln in self.path.read_text("utf-8").splitlines():
            if ln.strip():
                try:
                    out.append(json.loads(ln))
                except ValueError:
                    pass
        return out

    def find_completed(self, experiment_key: str) -> "dict | None":
        """C7.1 (B10/idempotency): آخرین ردیفِ terminalِ همین experiment_key (contract|rewrite).
        وجودش یعنی این آزمایش قبلاً کامل شده → دوباره اجرا نشود، artifactِ تکراری ساخته نشود."""
        for rec in reversed(self.entries()):
            if rec.get("experiment_key") != experiment_key:
                continue
            if rec.get("verdict") == "admission-promoted" and \
                    rec.get("admission_state") == "ADMITTED":
                return {**rec, "verdict": "accepted"}
            if rec.get("verdict") not in _TERMINAL_VERDICTS:
                continue
            # An accepted row is terminal only after two-phase memory admission.
            # Older rows have no field and remain backward-compatible.
            if rec.get("verdict") == "accepted" and rec.get("admission_state") == "PENDING":
                continue
            return rec
        return None


class Budget:
    """budgetِ سختِ cost/time/token/experiments — مأموریت step 11."""

    def __init__(self, contract_budget: dict, now=None):
        self.limits = contract_budget
        self._clock = now or (lambda: time.time())
        self.t0 = self._clock()
        self.spent = {"cost_aud": 0.0, "tokens": 0, "experiments": 0}

    def charge(self, *, cost_aud=0.0, tokens=0, experiment=False):
        self.spent["cost_aud"] += float(cost_aud)
        self.spent["tokens"] += int(tokens)
        if experiment:
            self.spent["experiments"] += 1

    def exceeded(self) -> "str | None":
        if self.spent["cost_aud"] > self.limits.get("cost_aud", 0.0):
            return "cost"
        if self.spent["tokens"] > self.limits.get("tokens", 0):
            return "tokens"
        if self.spent["experiments"] > self.limits.get("max_experiments", 0):
            return "experiments"
        if self.limits.get("time_s", 0) and (self._clock() - self.t0) > self.limits["time_s"]:
            return "time"
        return None


def _journal(state_dir, run_id, step, status, **meta):
    try:
        import durable_journal as _dj  # noqa: WPS433
        p = Path(state_dir) / "journal" / "research-journal.jsonl" if state_dir else None
        _dj.record(run_id, step, status, path=p, **meta)
    except Exception:  # noqa: BLE001
        pass


def _artifact_path(state_dir, experiment_key: str) -> "Path | None":
    if state_dir is None:
        return None
    safe = hashlib.sha256(str(experiment_key).encode("utf-8")).hexdigest()[:24]
    return Path(state_dir) / "research" / "artifacts" / f"{safe}.json"


def _load_experiment_artifact(state_dir, experiment_key: str) -> "dict | None":
    p = _artifact_path(state_dir, experiment_key)
    try:
        if p is None or not p.exists():
            return None
        d = json.loads(p.read_text("utf-8"))
        payload = d.get("result")
        canon = json.dumps(payload, ensure_ascii=False, sort_keys=True,
                           separators=(",", ":")).encode("utf-8")
        if not hmac_compare(d.get("sha256"), hashlib.sha256(canon).hexdigest()):
            return None
        return d
    except Exception:
        return None


def hmac_compare(a, b) -> bool:
    import hmac
    try:
        return hmac.compare_digest(str(a), str(b))
    except Exception:
        return False


def _persist_experiment_artifact(state_dir, experiment_key: str, result) -> "dict | None":
    """Durably checkpoint the experiment output before any verifier sees it.

    A non-JSON/oversized result is rejected rather than silently becoming non-resumable.
    """
    p = _artifact_path(state_dir, experiment_key)
    if p is None:
        return None
    try:
        canon = json.dumps(result, ensure_ascii=False, sort_keys=True,
                           separators=(",", ":")).encode("utf-8")
        if len(canon) > 1_000_000:
            return None
        rec = {"schema": "research-artifact.v1", "experiment_key": experiment_key,
               "result": result, "sha256": hashlib.sha256(canon).hexdigest(),
               "created_at": time.time(), "state": "EXPERIMENT_DONE"}
        p.parent.mkdir(parents=True, exist_ok=True)
        tmp = p.with_suffix(".tmp")
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(rec, f, ensure_ascii=False, sort_keys=True)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, p)
        return rec
    except Exception:
        return None


def run_experiment(*, contract: dict, experiment_fn, verifier_fn, held_out_eval=None,
                   budget: "Budget", ledger: "ResearchLedger", receipt_store=None,
                   memory_gate=None, outcome_store=None, state_dir=None,
                   cost_aud=0.0, tokens=0, uncertainty=0.0, rewrite_count=0,
                   preregistration=None) -> dict:
    """یک آزمایشِ حاکمیت‌شده. خروجی: {verdict, reason, receipt_id?, memory_id?, ledger_entry}.
    verdict ∈ accepted|rejected|quarantined|terminated. هرگز raise نمی‌کند؛ هرگز apply/merge."""
    run_id = f"research-{contract.get('contract_id', 'rc')}"
    # Ledger path scopes an execution lineage. The same deterministic contract can be
    # evaluated in independent sandboxes without accidentally consuming another run's artifact.
    lineage = hashlib.sha256(str(getattr(ledger, "path", "default")).encode()).hexdigest()[:12]
    exp_key = f"{contract.get('contract_id')}|{int(rewrite_count)}|{lineage}"
    try:
        # (0) governance: فقط اکشن‌های مجاز؛ test_in_sandbox پیش‌شرطِ اجراست
        if not _permit("test_in_sandbox"):
            return {"verdict": "terminated", "reason": "governance denied test_in_sandbox"}
        # C7.1 (B10/idempotency، Mission C «no duplicate artifacts»): اگر این آزمایش
        # (contract|rewrite) قبلاً به ردیفِ terminal رسیده، **دوباره اجرا نکن** — بیداری/بوتِ
        # دوبار نباید experiment_fn را دوباره بزند یا ledger/رسید/خاطرهٔ تکراری بسازد. resume نه restart.
        prior = ledger.find_completed(exp_key)
        if prior is not None:
            _journal(state_dir, run_id, "resume", "ok", experiment_index=int(rewrite_count),
                     verdict=prior.get("verdict"), resumed=True)
            return {"verdict": prior.get("verdict"),
                    "reason": f"resumed (already completed): {prior.get('reason')}",
                    "receipt_id": prior.get("receipt_id"), "memory_id": prior.get("memory_id"),
                    "ledger_entry": prior, "resumed": True}
        # bad-conjecture terminate: بازنویسیِ بی‌نهایت ممنوع
        if rewrite_count >= MAX_REWRITES:
            _journal(state_dir, run_id, "conjecture", "error", reason="max-rewrites")
            e = {"contract_id": contract.get("contract_id"), "experiment_key": exp_key,
                 "hypothesis": contract.get("hypothesis"),
                 "verdict": "rejected", "reason": "bad conjecture — max rewrites reached (terminated)"}
            ledger.append(e)
            return {"verdict": "rejected", "reason": e["reason"], "ledger_entry": e}
        # A prior accepted-PENDING row means all artifacts landed but promotion crashed.
        # Finish that exact transaction idempotently; never rerun experiment/verifier.
        pending_rows = [r for r in ledger.entries()
                        if r.get("experiment_key") == exp_key
                        and r.get("verdict") == "accepted"
                        and r.get("admission_state") == "PENDING"]
        if pending_rows and memory_gate is not None:
            p = pending_rows[-1]
            try:
                import learning_gate as _lg_recover  # noqa: WPS433
                rr = _lg_recover.finalize_pending_learning(
                    memory_gate=memory_gate, memory_id=p.get("memory_id"), admit=True)
            except Exception:
                rr = {"ok": False}
            if rr.get("ok"):
                promoted = {**p, "verdict": "admission-promoted",
                            "admission_state": "ADMITTED", "recovered": True}
                ledger.append_strict(promoted)
                return {"verdict": "accepted", "reason": "recovered pending admission",
                        "receipt_id": p.get("receipt_id"), "memory_id": p.get("memory_id"),
                        "ledger_entry": promoted, "resumed": True}
            return {"verdict": "verified-not-admitted",
                    "reason": "pending admission recovery failed", "resumed": True}

        # budget: پیش از اجرا
        why = budget.exceeded()
        if why:
            _journal(state_dir, run_id, "budget", "error", reason=why)
            return {"verdict": "terminated", "reason": f"budget-exceeded:{why}"}

        # (1) اجرای آزمایش در sandbox (تزریق‌پذیر؛ صفر اثرِ بیرونی — مسئولیتِ caller/sandbox)
        # C7.1 (Mission B): checkpointِ ساختاریافته — contract_id/experiment_index/budget/rewrite
        # تا plan_recovery نقطهٔ resume را از research-journal بازسازی کند.
        artifact = _load_experiment_artifact(state_dir, exp_key)
        resumed_after_experiment = artifact is not None
        if artifact is None:
            _journal(state_dir, run_id, "experiment", "start",
                     contract_id=contract.get("contract_id"),
                     experiment_index=int(rewrite_count), rewrite_count=int(rewrite_count),
                     budget_spent=dict(budget.spent), state="EXPERIMENT_RUNNING")
            budget.charge(cost_aud=cost_aud, tokens=tokens, experiment=True)
            result = experiment_fn(contract)
            why = budget.exceeded()
            if why:
                _journal(state_dir, run_id, "experiment", "error", reason=f"budget:{why}")
                return {"verdict": "terminated", "reason": f"budget-exceeded:{why}"}
            artifact = _persist_experiment_artifact(state_dir, exp_key, result)
            if artifact is None:
                _journal(state_dir, run_id, "experiment", "error",
                         reason="artifact-persist-failed")
                return {"verdict": "terminated",
                        "reason": "experiment result was not durably checkpointed"}
            _journal(state_dir, run_id, "experiment", "ok", state="EXPERIMENT_DONE",
                     artifact_sha256=artifact["sha256"], experiment_index=int(rewrite_count),
                     contract_id=contract.get("contract_id"), budget_spent=dict(budget.spent))
        else:
            result = artifact["result"]
            _journal(state_dir, run_id, "experiment-resume", "ok",
                     state="EXPERIMENT_DONE", artifact_sha256=artifact.get("sha256"),
                     experiment_index=int(rewrite_count), contract_id=contract.get("contract_id"))

        # (2) verifier + held-out. On restart this consumes the durable artifact and
        # never calls experiment_fn again.
        _journal(state_dir, run_id, "verify", "start", state="VERIFYING",
                 artifact_sha256=artifact.get("sha256"))
        v = verifier_fn(contract, result)     # {supported: bool, evidence, benchmark_gain, risk}
        supported = bool(v.get("supported"))
        ho = {"overall_verdict": "pass"}
        if held_out_eval is not None:
            try:
                ho = held_out_eval(internal_metric_pass=supported)
            except Exception:  # noqa: BLE001
                ho = {"overall_verdict": "fail"}
        held_ok = ho.get("overall_verdict") == "pass" and not ho.get("anti_hacking_flag")

        # (3) رسیدِ durable برای آزمایش (هر آزمایش رسید دارد — step 6)
        rid = None
        if receipt_store is not None:
            try:
                rid = receipt_store.record({
                    "receipt_id": "dr_" + __import__("hashlib").sha256(
                        (str(contract.get("contract_id")) + str(rewrite_count)).encode()).hexdigest()[:16],
                    "trace_id": str(contract.get("contract_id") or ""),
                    "mission_id": "research", "objective": str(contract.get("question"))[:290],
                    "alternatives": ["support", "falsify"],
                    "selected_alternative": "support" if supported else "falsify",
                    "reason_codes": [f"VERIFY_{'PASS' if supported else 'FAIL'}",
                                     f"HELDOUT_{ho.get('overall_verdict', 'na').upper()}"],
                    "assumptions": list(contract.get("falsification_criteria", []))[:5],
                    "memories_used": [], "predicted_outcome": {"benchmark_gain": v.get("benchmark_gain", 0.0)},
                    "effect_class": "E0"})
            except Exception:  # noqa: BLE001
                rid = None

        # (4) falsification: hypothesis رد شد → terminate (نه بازنویسیِ بی‌نهایت)
        if not supported:
            _journal(state_dir, run_id, "verify", "ok", supported=False)
            e = {"contract_id": contract.get("contract_id"), "experiment_key": exp_key,
                 "hypothesis": contract.get("hypothesis"),
                 "verdict": "rejected", "reason": "hypothesis falsified by verifier",
                 "receipt_id": rid, "evidence": str(v.get("evidence", ""))[:200]}
            ledger.append(e)
            return {"verdict": "rejected", "reason": e["reason"], "receipt_id": rid, "ledger_entry": e}

        # C6 cycle-3: in-loop pre-registration gate (opt-in, tightening-only). The LOOP
        # re-derives verification from the append-only journal — it never trusts a caller
        # dict. Unverified prediction -> quarantine; verified -> its calibration uncertainty
        # can only RAISE the caller's uncertainty (max), never lower it.
        if preregistration is not None:
            _pv = verify_preregistration(
                state_dir=state_dir, contract=contract,
                capability=(preregistration or {}).get("capability"),
                predicted=(preregistration or {}).get("predicted"),
                experiment_index=int(rewrite_count))
            _cal = record_calibration(
                capability=str((preregistration or {}).get("capability")),
                predicted=(preregistration or {}).get("predicted"),
                measured=float(v.get("benchmark_gain", 0.0)),
                preregistration=_pv)
            uncertainty = max(float(uncertainty), float(_cal.get("uncertainty", 1.0)))
            if not _pv.get("preregistered"):
                e = {"contract_id": contract.get("contract_id"), "experiment_key": exp_key,
                     "hypothesis": contract.get("hypothesis"), "verdict": "quarantined",
                     "reason": f"prediction not pre-registered: {_pv.get('reason')}",
                     "receipt_id": rid}
                ledger.append(e)
                _journal(state_dir, run_id, "accept", "ok", verdict="quarantined",
                         reason="preregistration-failed")
                return {"verdict": "quarantined", "reason": e["reason"],
                        "receipt_id": rid, "ledger_entry": e,
                        "preregistration": _pv}

        # (5) acceptance = utility با hard-constraints (benchmark gain جبرانِ نقضِ قید نمی‌کند)
        gov = _governance()
        U = gov.utility(benchmark_gain=float(v.get("benchmark_gain", 0.0)),
                        risk=float(v.get("risk", 0.0)), cost=float(cost_aud),
                        maintenance_debt=float(v.get("maintenance_debt", 0.0)),
                        uncertainty=float(uncertainty),
                        hard_constraints_ok=bool(held_ok and v.get("hard_constraints_ok", True)))
        # regression/uncertaintyِ بالا یا held-out قرمز → quarantine (نه commit)
        if not held_ok or U <= 0 or uncertainty >= 0.5:
            e = {"contract_id": contract.get("contract_id"), "experiment_key": exp_key,
                 "hypothesis": contract.get("hypothesis"),
                 "verdict": "quarantined", "reason": f"U={U} held_ok={held_ok} uncertainty={uncertainty}",
                 "receipt_id": rid}
            ledger.append(e)
            _journal(state_dir, run_id, "accept", "ok", verdict="quarantined")
            return {"verdict": "quarantined", "reason": e["reason"], "receipt_id": rid, "ledger_entry": e}

        # (6) admission: نتیجه فقط از learning_gate (verifier+outcome، C3) وارد memory می‌شود.
        # audit #4: **accepted ⟺ همهٔ artifactهای durable موجودند** (receipt+outcome+memory+ledger).
        # اگر memory/store/receipt admit نشد → verified-not-admitted، هرگز accepted.
        mid = None
        learning_rid = None
        admit_reason = "no memory_gate/outcome_store provided"
        if memory_gate is not None and outcome_store is not None:
            try:
                import learning_gate as _lg  # noqa: WPS433
                oref = f"research|{contract.get('contract_id')}|accepted-measurement"
                outcome_store.record({"correlation_id": str(contract.get("contract_id")),
                                      "proposal_id": str(contract.get("contract_id")), "leg_id": "research",
                                      "event_type": "accepted-measurement", "value_aud_claimed": 0.0,
                                      "idempotency_key": oref})
                lr = _lg.learn_from_outcome(
                    memory_gate=memory_gate, receipt_store=receipt_store, outcome_store=outcome_store,
                    signal={"content": f"research finding: {contract.get('hypothesis')}"[:200],
                            "mkey": f"research-{contract.get('contract_id')}", "namespace": "semantic",
                            "correlation_id": str(contract.get("contract_id")), "outcome_ref": oref,
                            "trust": "OWNER_CONFIRMED", "salience": 0.6,
                            "source": "owner", "producer": "research_loop"},
                    evaluator=(held_out_eval and (lambda **k: held_out_eval(**k))),
                    pending_admission=True)
                mid = lr.get("memory_id")
                learning_rid = lr.get("receipt_id")
                admit_reason = lr.get("reason", "")
            except Exception as _ae:  # noqa: BLE001
                mid = None
                admit_reason = f"admission-error:{type(_ae).__name__}"
        if not (mid and rid and learning_rid):
            # verified ولی artifactِ کامل نساخت → NOT accepted (verified-not-admitted)
            e = {"contract_id": contract.get("contract_id"), "experiment_key": exp_key,
                 "hypothesis": contract.get("hypothesis"),
                 "verdict": "verified-not-admitted",
                 "reason": (f"verified+held-out but not admitted: memory={mid} "
                            f"experiment_receipt={rid} learning_receipt={learning_rid} "
                            f"({admit_reason})"),
                 "receipt_id": rid, "memory_id": mid, "utility": U}
            ledger.append_strict(e)
            _journal(state_dir, run_id, "accept", "ok", verdict="verified-not-admitted")
            return {"verdict": "verified-not-admitted", "reason": e["reason"], "receipt_id": rid,
                    "memory_id": mid, "utility": U, "ledger_entry": e}
        e = {"contract_id": contract.get("contract_id"), "experiment_key": exp_key,
             "hypothesis": contract.get("hypothesis"), "verdict": "accepted",
             "reason": f"verified + held-out + U={U} + full durable artifact",
             "receipt_id": rid, "learning_receipt_id": learning_rid,
             "memory_id": mid, "utility": U, "admission_state": "PENDING",
             "artifact_sha256": artifact.get("sha256"),
             "resumed_after_experiment": resumed_after_experiment}
        # First make the complete acceptance record durable while memory remains invisible.
        if not ledger.append_strict(e):
            try:
                rr = _lg.finalize_pending_learning(
                    memory_gate=memory_gate, memory_id=mid, admit=False)
            except Exception:
                rr = {"ok": False, "state": "PENDING"}
            _journal(state_dir, run_id, "accept", "error",
                     reason="ledger-append-failed", memory_state=rr.get("state"))
            return {"verdict": "quarantined",
                    "reason": ("ledger append failed — memory remains invisible"
                               if not rr.get("ok") else
                               "ledger append failed — pending memory retracted"),
                    "receipt_id": rid, "memory_id": mid,
                    "memory_retracted": bool(rr.get("ok")),
                    "memory_visible": False}
        # Only a durable accepted ledger row can promote retrieval visibility.
        promoted = _lg.finalize_pending_learning(
            memory_gate=memory_gate, memory_id=mid, admit=True)
        if not promoted.get("ok"):
            _journal(state_dir, run_id, "accept", "error",
                     reason="memory-promotion-failed", memory_state=promoted.get("state"))
            return {"verdict": "verified-not-admitted",
                    "reason": "accepted artifacts durable but memory promotion failed",
                    "receipt_id": rid, "memory_id": mid, "ledger_entry": e}
        # Append a promotion receipt. If this append fails, the accepted PENDING row still
        # provides a durable recovery instruction and the memory itself is already backed
        # by all required artifacts; boot recovery can idempotently append this marker.
        promoted_row = {**e, "verdict": "admission-promoted", "admission_state": "ADMITTED"}
        ledger.append_strict(promoted_row)
        e["admission_state"] = "ADMITTED"
        _journal(state_dir, run_id, "accept", "ok", verdict="accepted", memory_id=mid,
                 memory_state="ADMITTED", contract_id=contract.get("contract_id"),
                 experiment_index=int(rewrite_count), budget_spent=dict(budget.spent))
        return {"verdict": "accepted", "reason": e["reason"], "receipt_id": rid,
                "memory_id": mid, "utility": U, "ledger_entry": e,
                "resumed_after_experiment": resumed_after_experiment}
    except Exception as ex:  # noqa: BLE001 — حلقه هرگز caller را نمی‌کشد
        return {"verdict": "terminated", "reason": f"failsoft:{type(ex).__name__}"}


def _prediction_sha(contract_id, capability, predicted) -> str:
    canon = json.dumps({"contract_id": str(contract_id), "capability": str(capability),
                        "predicted": round(float(predicted), 6)},
                       sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canon.encode("utf-8")).hexdigest()


def preregister_prediction(*, state_dir, contract, capability, predicted,
                           experiment_index=0) -> dict:
    """C6 cycle-3: journal the prediction hash BEFORE the experiment runs. The append-only
    journal's line order (written by the journal itself) is the only precedence evidence —
    no caller-supplied clock strings. Bound to experiment_index so each experiment gets
    exactly one prediction (anti-spray). Returns the receipt for the caller's records."""
    sha = _prediction_sha(contract.get("contract_id"), capability, predicted)
    run_id = f"research-{contract.get('contract_id', 'rc')}"
    _journal(state_dir, run_id, "preregister", "ok",
             capability=str(capability)[:64], prediction_sha=sha,
             experiment_index=int(experiment_index))
    return {"run_id": run_id, "capability": str(capability)[:64],
            "predicted": round(float(predicted), 6), "prediction_sha": sha,
            "experiment_index": int(experiment_index)}


def verify_preregistration(*, state_dir, contract, capability, predicted,
                           experiment_index=0) -> dict:
    """Re-derive (never trust): recompute the sha from the CLAIMED prediction and demand,
    among the preregister rows OF THIS experiment_index, EXACTLY ONE distinct sha — which
    must equal the claimed one and PRECEDE the first experiment/start row of the same index
    (journal line order). Missing row = peeking; sha mismatch = tampering; multiple distinct
    shas for one index = spray — all -> not preregistered. Legit recalibration registers a
    new prediction under a HIGHER experiment_index (cycle-2 style) and stays valid.
    Fail-closed on any error."""
    try:
        sha = _prediction_sha(contract.get("contract_id"), capability, predicted)
        run_id = f"research-{contract.get('contract_id', 'rc')}"
        ei = int(experiment_index)
        p = Path(state_dir) / "journal" / "research-journal.jsonl"
        if not p.exists():
            return {"preregistered": False, "reason": "no research-journal"}
        shas_this_index = []
        pre_i = exp_i = None
        for i, ln in enumerate(p.read_text("utf-8").splitlines()):
            try:
                row = json.loads(ln)
            except ValueError:
                continue
            if row.get("run_id") != run_id:
                continue
            meta = row.get("meta") or {}
            if row.get("step") == "preregister" and int(meta.get("experiment_index", 0)) == ei:
                s = meta.get("prediction_sha")
                if s not in [x[1] for x in shas_this_index]:
                    shas_this_index.append((i, s))
                if pre_i is None and s == sha:
                    pre_i = i
            if exp_i is None and row.get("step") == "experiment"                     and row.get("status") == "start"                     and int(meta.get("experiment_index", 0)) == ei:
                exp_i = i
        if len(shas_this_index) > 1:
            return {"preregistered": False,
                    "reason": f"spray: {len(shas_this_index)} distinct preregistered "
                              f"predictions for experiment_index={ei}",
                    "distinct_preregistrations": len(shas_this_index)}
        ok = pre_i is not None and (exp_i is None or pre_i < exp_i)
        reason = ("ok" if ok else
                  ("no matching preregister row (peeking or tampered prediction)"
                   if pre_i is None else "preregister row AFTER experiment start"))
        return {"preregistered": bool(ok), "reason": reason,
                "preregister_line": pre_i, "experiment_start_line": exp_i}
    except Exception as ex:  # noqa: BLE001 — fail-closed
        return {"preregistered": False, "reason": f"verify-error:{type(ex).__name__}"}


def record_calibration(*, capability: str, predicted: float, measured: float,
                       ledger_path=None, preregistration=None) -> dict:
    """self-model calibration (C6 step 8): predicted vs measured capability. خطای calibration
    و overconfidence را می‌سنجد و به‌عنوان uncertaintyِ تصمیمِ بعدی برمی‌گرداند — ادعای توانایی
    که با اندازه‌گیری نمی‌خواند = overconfident → uncertaintyِ بالا → quarantine.
    خروجی: {calibration_error, overconfident, uncertainty}. append-only durable."""
    # C6 cycle-3: an unverified pre-registration is worse than a bad prediction — it is
    # an unauditable one. Force maximal uncertainty (-> quarantine downstream).
    if preregistration is not None and not (isinstance(preregistration, dict)
                                            and preregistration.get("preregistered")):
        rec = {"capability": str(capability)[:64], "predicted": None, "measured": None,
               "calibration_error": 1.0, "overconfident": True, "preregistered": False,
               "reason": (preregistration or {}).get("reason", "not preregistered")
               if isinstance(preregistration, dict) else "not preregistered"}
        if ledger_path is not None:
            try:
                p = Path(ledger_path)
                p.parent.mkdir(parents=True, exist_ok=True)
                with open(p, "a", encoding="utf-8") as f:
                    f.write(json.dumps(rec, ensure_ascii=False, sort_keys=True) + "\n")
            except Exception:  # noqa: BLE001
                pass
        rec["uncertainty"] = 1.0
        return rec
    try:
        pred = max(0.0, min(1.0, float(predicted)))
        meas = max(0.0, min(1.0, float(measured)))
    except (TypeError, ValueError):
        return {"calibration_error": 1.0, "overconfident": True, "uncertainty": 1.0}
    err = abs(pred - meas)
    overconfident = pred - meas > 0.15   # ادعا خیلی بالاتر از اندازه‌گیری
    rec = {"capability": str(capability)[:64], "predicted": pred, "measured": meas,
           "calibration_error": round(err, 3), "overconfident": overconfident}
    if preregistration is not None:
        rec["preregistered"] = True
    if ledger_path is not None:
        try:
            p = Path(ledger_path)
            p.parent.mkdir(parents=True, exist_ok=True)
            with open(p, "a", encoding="utf-8") as f:
                f.write(json.dumps(rec, ensure_ascii=False, sort_keys=True) + "\n")
        except Exception:  # noqa: BLE001
            pass
    # uncertainty = خطای calibration، با جریمهٔ overconfidence (به سمتِ quarantine)
    rec["uncertainty"] = min(1.0, err + (0.4 if overconfident else 0.0))
    return rec


def propose_only_apply_guard(action: str = "merge_or_deploy") -> dict:
    """گاردِ صریح: خودِ حلقه هرگز apply/merge/deploy نمی‌کند. تأییدِ constitutional."""
    return {"permitted": _permit(action), "note": "self-improvement loop never auto-applies; owner-gated"}


def plan_recovery(*, state_dir=None, within_h: float = 720.0) -> list:
    """C7.1 (Mission B / B8): نقشهٔ بازیابیِ **advisory** برای runهای پژوهشیِ ناتمام — از
    **research-journal** (نه run-journal). برای هر run: contract_id، last_completed_step،
    experiment_index، rewrite_count، budget_spent، mode=DETECTED. این تابع فقط **تشخیص** می‌دهد
    و نقطهٔ resume را از journalِ درست می‌خواند؛ اجرای واقعیِ resume idempotent است (run_experiment
    با ledger.find_completed آزمایشِ کامل را دوباره اجرا نمی‌کند). هرگز آزمایش را کورکورانه rerun نمی‌کند."""
    try:
        import durable_journal as _dj  # noqa: WPS433
    except Exception:  # noqa: BLE001
        return []
    rjp = (Path(state_dir) / "journal" / "research-journal.jsonl") if state_dir is not None else None
    if rjp is not None and not rjp.exists():
        return []
    try:
        inc = _dj.incomplete_runs(within_h=within_h, path=rjp) if rjp is not None \
            else _dj.incomplete_runs(within_h=within_h)
        rows = _dj._read_all(rjp) if rjp is not None else _dj._read_all()  # noqa: SLF001
    except Exception:  # noqa: BLE001
        return []
    latest_meta: dict = {}
    last_ok_step: dict = {}
    for r in rows:
        rid = r.get("run_id")
        m = r.get("meta") or {}
        if m:
            latest_meta.setdefault(rid, {}).update({k: v for k, v in m.items() if v is not None})
        if r.get("status") == "ok":
            last_ok_step[rid] = r.get("step")
    plans = []
    for row in inc:
        rid = row.get("run_id")
        m = latest_meta.get(rid, {})
        cid = m.get("contract_id") or (
            rid[len("research-"):] if str(rid).startswith("research-") else rid)
        plans.append({"run_id": rid, "contract_id": cid,
                      "died_at_step": row.get("step"),
                      "last_completed_step": last_ok_step.get(rid),
                      "experiment_index": m.get("experiment_index"),
                      "rewrite_count": m.get("rewrite_count"),
                      "budget_spent": m.get("budget_spent"),
                      "mode": "DETECTED",
                      "note": "advisory; resume is idempotent via run_experiment ledger guard"})
    return plans
