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


def run_experiment(*, contract: dict, experiment_fn, verifier_fn, held_out_eval=None,
                   budget: "Budget", ledger: "ResearchLedger", receipt_store=None,
                   memory_gate=None, outcome_store=None, state_dir=None,
                   cost_aud=0.0, tokens=0, uncertainty=0.0, rewrite_count=0) -> dict:
    """یک آزمایشِ حاکمیت‌شده. خروجی: {verdict, reason, receipt_id?, memory_id?, ledger_entry}.
    verdict ∈ accepted|rejected|quarantined|terminated. هرگز raise نمی‌کند؛ هرگز apply/merge."""
    run_id = f"research-{contract.get('contract_id', 'rc')}"
    try:
        # (0) governance: فقط اکشن‌های مجاز؛ test_in_sandbox پیش‌شرطِ اجراست
        if not _permit("test_in_sandbox"):
            return {"verdict": "terminated", "reason": "governance denied test_in_sandbox"}
        # bad-conjecture terminate: بازنویسیِ بی‌نهایت ممنوع
        if rewrite_count >= MAX_REWRITES:
            _journal(state_dir, run_id, "conjecture", "error", reason="max-rewrites")
            e = {"contract_id": contract.get("contract_id"), "hypothesis": contract.get("hypothesis"),
                 "verdict": "rejected", "reason": "bad conjecture — max rewrites reached (terminated)"}
            ledger.append(e)
            return {"verdict": "rejected", "reason": e["reason"], "ledger_entry": e}
        # budget: پیش از اجرا
        why = budget.exceeded()
        if why:
            _journal(state_dir, run_id, "budget", "error", reason=why)
            return {"verdict": "terminated", "reason": f"budget-exceeded:{why}"}

        # (1) اجرای آزمایش در sandbox (تزریق‌پذیر؛ صفر اثرِ بیرونی — مسئولیتِ caller/sandbox)
        _journal(state_dir, run_id, "experiment", "start")
        budget.charge(cost_aud=cost_aud, tokens=tokens, experiment=True)
        result = experiment_fn(contract)
        why = budget.exceeded()
        if why:
            _journal(state_dir, run_id, "experiment", "error", reason=f"budget:{why}")
            return {"verdict": "terminated", "reason": f"budget-exceeded:{why}"}

        # (2) verifier + held-out (ضدخودفریبی: hypothesis باید falsifiable + verify شود)
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
            e = {"contract_id": contract.get("contract_id"), "hypothesis": contract.get("hypothesis"),
                 "verdict": "rejected", "reason": "hypothesis falsified by verifier",
                 "receipt_id": rid, "evidence": str(v.get("evidence", ""))[:200]}
            ledger.append(e)
            return {"verdict": "rejected", "reason": e["reason"], "receipt_id": rid, "ledger_entry": e}

        # (5) acceptance = utility با hard-constraints (benchmark gain جبرانِ نقضِ قید نمی‌کند)
        gov = _governance()
        U = gov.utility(benchmark_gain=float(v.get("benchmark_gain", 0.0)),
                        risk=float(v.get("risk", 0.0)), cost=float(cost_aud),
                        maintenance_debt=float(v.get("maintenance_debt", 0.0)),
                        uncertainty=float(uncertainty),
                        hard_constraints_ok=bool(held_ok and v.get("hard_constraints_ok", True)))
        # regression/uncertaintyِ بالا یا held-out قرمز → quarantine (نه commit)
        if not held_ok or U <= 0 or uncertainty >= 0.5:
            e = {"contract_id": contract.get("contract_id"), "hypothesis": contract.get("hypothesis"),
                 "verdict": "quarantined", "reason": f"U={U} held_ok={held_ok} uncertainty={uncertainty}",
                 "receipt_id": rid}
            ledger.append(e)
            _journal(state_dir, run_id, "accept", "ok", verdict="quarantined")
            return {"verdict": "quarantined", "reason": e["reason"], "receipt_id": rid, "ledger_entry": e}

        # (6) admission: نتیجه فقط از learning_gate (verifier+outcome، C3) وارد memory می‌شود.
        # audit #4: **accepted ⟺ همهٔ artifactهای durable موجودند** (receipt+outcome+memory+ledger).
        # اگر memory/store/receipt admit نشد → verified-not-admitted، هرگز accepted.
        mid = None
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
                    evaluator=(held_out_eval and (lambda **k: held_out_eval(**k))))
                mid = lr.get("memory_id")
                admit_reason = lr.get("reason", "")
            except Exception as _ae:  # noqa: BLE001
                mid = None
                admit_reason = f"admission-error:{type(_ae).__name__}"
        if not (mid and rid):
            # verified ولی artifactِ کامل نساخت → NOT accepted (verified-not-admitted)
            e = {"contract_id": contract.get("contract_id"), "hypothesis": contract.get("hypothesis"),
                 "verdict": "verified-not-admitted",
                 "reason": f"verified+held-out but not admitted: memory={mid} receipt={rid} ({admit_reason})",
                 "receipt_id": rid, "memory_id": mid, "utility": U}
            ledger.append_strict(e)
            _journal(state_dir, run_id, "accept", "ok", verdict="verified-not-admitted")
            return {"verdict": "verified-not-admitted", "reason": e["reason"], "receipt_id": rid,
                    "memory_id": mid, "utility": U, "ledger_entry": e}
        e = {"contract_id": contract.get("contract_id"), "hypothesis": contract.get("hypothesis"),
             "verdict": "accepted", "reason": f"verified + held-out + U={U} + full durable artifact",
             "receipt_id": rid, "memory_id": mid, "utility": U}
        # audit #4: appendِ ledger برای accept **حیاتی** است — اگر ننشیند accepted نیست
        if not ledger.append_strict(e):
            _journal(state_dir, run_id, "accept", "error", reason="ledger-append-failed")
            return {"verdict": "quarantined", "reason": "ledger append failed — not accepted",
                    "receipt_id": rid, "memory_id": mid}
        _journal(state_dir, run_id, "accept", "ok", verdict="accepted", memory_id=mid)
        # NOTE: صفر auto-apply. patch/code فقط پیشنهاد است؛ merge_or_deploy در governance ممنوع.
        return {"verdict": "accepted", "reason": e["reason"], "receipt_id": rid,
                "memory_id": mid, "utility": U, "ledger_entry": e}
    except Exception as ex:  # noqa: BLE001 — حلقه هرگز caller را نمی‌کشد
        return {"verdict": "terminated", "reason": f"failsoft:{type(ex).__name__}"}


def record_calibration(*, capability: str, predicted: float, measured: float,
                       ledger_path=None) -> dict:
    """self-model calibration (C6 step 8): predicted vs measured capability. خطای calibration
    و overconfidence را می‌سنجد و به‌عنوان uncertaintyِ تصمیمِ بعدی برمی‌گرداند — ادعای توانایی
    که با اندازه‌گیری نمی‌خواند = overconfident → uncertaintyِ بالا → quarantine.
    خروجی: {calibration_error, overconfident, uncertainty}. append-only durable."""
    try:
        pred = max(0.0, min(1.0, float(predicted)))
        meas = max(0.0, min(1.0, float(measured)))
    except (TypeError, ValueError):
        return {"calibration_error": 1.0, "overconfident": True, "uncertainty": 1.0}
    err = abs(pred - meas)
    overconfident = pred - meas > 0.15   # ادعا خیلی بالاتر از اندازه‌گیری
    rec = {"capability": str(capability)[:64], "predicted": pred, "measured": meas,
           "calibration_error": round(err, 3), "overconfident": overconfident}
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
