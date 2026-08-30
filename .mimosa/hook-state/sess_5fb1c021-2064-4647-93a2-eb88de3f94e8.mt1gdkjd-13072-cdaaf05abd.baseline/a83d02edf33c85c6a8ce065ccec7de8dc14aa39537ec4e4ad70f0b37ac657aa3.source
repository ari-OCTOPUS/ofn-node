"""sandbox_runner.py — اجرای boundedِ یک BoundedRunSpec (ADR-039 C3، Plane-3).

این لایهٔ اجرای واقعیِ زنجیرهٔ epistemic است. **نه** یک sandboxِ کاملِ process/
network-iso (آن C3-future با subprocess است) — بلکه یک **bounded-exec wrapper** که
این‌ها را enforce می‌کند:

  - HALT/STOP check قبل از هر چیز (fail-closed؛ §11 #11)
  - max_wall_seconds: deadline با time.time()
  - max_runs: شمارشِ تکرار
  - output-path: receipt فقط در _ALLOWED_ROOTS نوشته می‌شود (§11 #10)
  - crash/timeout → INCONCLUSIVE/BLOCKED، نه pass (§11 #8)
  - خروجی: tamper-evident EvidenceReceipt در ReceiptStore

قراردادِ صادقانه: caller مسئولِ پاس‌دادنِ experiment_fnای است که خودش no_network
است (replay روی fixture، نه دسترسیِ زنده). runner آن را در کرانِ زمان/تعداد/مسیر
می‌پیچد. اجرای خودکارِ شبکه/فایل خارج از حیطهٔ این ماژول است و عمداً موجود نیست.
"""
from __future__ import annotations

import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Optional

from .canonical import canonical_hash
from .receipt_store import ReceiptStore, _ALLOWED_ROOTS
from .schemas import BindHashes, EvidenceReceipt, WorldMode
from .test_planner import BoundedRunSpec


# فلگ‌های kill-switch (همان مسیرِ opslib، اما lazy تا import-cycle نسازد).
def _is_halted(state_dir: Optional[Path] = None) -> bool:
    base = Path(state_dir) if state_dir else Path(os.environ.get(
        "OCTOPUS_STATE_DIR", "_ops/state"))
    # همان سه فلگِ organisms — fail-closed روی هر کدام.
    return any((base.parent / n).exists() for n in
               ("STOP-ORGANISM", "STOP-CORTEX", "HALT-ALL")) or any(
                   Path(os.getcwd()).parent.joinpath(n).exists()
                   for n in ("STOP-ORGANISM", "HALT-ALL"))


@dataclass(frozen=True)
class RunResult:
    """خروجیِ یک run."""
    ok: bool
    receipt: Optional[EvidenceReceipt]
    falsified: bool
    raw_result: dict
    reason: str          # "completed" | "halted" | "timeout" | "crash" | "budget"


def _binds_for(spec: BoundedRunSpec, *, git_sha: str, config_hash: str,
               command_hash: str) -> BindHashes:
    return BindHashes(
        git_sha=git_sha,
        material_hash=canonical_hash({"claim_id": spec.claim_id,
                                      "plan_id": spec.plan_id}),
        config_hash=config_hash,
        environment_hash=canonical_hash({"experiment_type": spec.experiment_type}),
        seed_set_hash=canonical_hash(list(spec.seeds)),
        command_hash=command_hash,
        artifact_hashes={},
    )


def run(
    spec: BoundedRunSpec,
    experiment_fn: Callable[[BoundedRunSpec], dict],
    *,
    world_mode: str = "hypothesis",
    store_path: Optional[Path] = None,
    git_sha: str = "unknown",
    config_hash: str = "unknown",
    command_hash: str = "unknown",
    produced_by: str = "epistemic_sandbox_runner",
    state_dir: Optional[Path] = None,
    now: Optional[float] = None,
    monotonic=None,
) -> RunResult:
    """یک BoundedRunSpec را در کران اجرا کن و receipt بساز.

    experiment_fn(spec) -> dict: تابعِ آزمونِ no_network (replay/fixture). خروجی‌اش
    به falsifier_check(spec) داده می‌شود. crash/timeout → INCONCLUSIVE.
    """
    _clock = monotonic or time.monotonic
    t0 = _clock()

    # ۱. HALT check — fail-closed پیش از هر کاری (§11 #11)
    if _is_halted(state_dir=state_dir):
        return RunResult(False, None, False, {}, "halted")

    deadline = t0 + max(1, spec.max_wall_seconds)
    runs_done = 0
    raw: dict = {}
    falsified = False
    crash_exc: Optional[BaseException] = None

    # ۲. اجرای bounded: max_runs تکرار، هر بار deadline check
    try:
        for _i in range(max(1, spec.max_runs)):
            if _clock() > deadline:
                break
            runs_done += 1
            raw = experiment_fn(spec) or {}
            # falsifier_check روی آخرین raw — اگر falsified شد، کافی است.
            if spec.falsifier_check(raw):
                falsified = True
                break
    except Exception as exc:  # noqa: BLE001 — crash → INCONCLUSIVE، نه pass
        crash_exc = exc
        raw = {"crash": type(exc).__name__, "runs_done": runs_done}

    elapsed = _clock() - t0
    reason = "completed"
    if crash_exc is not None:
        reason = "crash"
    elif runs_done == 0:
        reason = "halted"
    elif _clock() > deadline and not falsified and not raw:
        reason = "timeout"

    # verdict پیش‌ثبت (نهایی در GateDecision): crash/timeout → inconclusive
    verdict = "falsified" if falsified else (
        "inconclusive" if reason in ("crash", "timeout") else "not_falsified")

    # ۳. receipt با binds + parent_hash از store
    binds = _binds_for(spec, git_sha=git_sha, config_hash=config_hash,
                       command_hash=command_hash)
    payload = {
        "run_id": spec.run_id, "claim_id": spec.claim_id,
        "plan_id": spec.plan_id, "experiment_type": spec.experiment_type,
        "seeds": list(spec.seeds), "runs_done": runs_done,
        "elapsed_s": round(elapsed, 4), "verdict": verdict,
        "falsified": falsified, "reason": reason,
    }
    canonical_payload_hash = canonical_hash(payload)

    # world_mode membership در schema چک می‌شود؛ فقط مقادیرِ WorldMode مجاز.
    valid_wm = {m.value for m in WorldMode}
    if world_mode not in valid_wm:
        world_mode = "hypothesis"

    store = ReceiptStore(store_path) if store_path else ReceiptStore()
    parent = store.tip()

    receipt = EvidenceReceipt(
        receipt_id="rcpt-" + canonical_hash({"run_id": spec.run_id})[:12],
        plan_id=spec.plan_id,
        claim_id=spec.claim_id,
        binds=binds,
        parent_receipt_hash=parent,
        canonical_payload_hash=canonical_payload_hash,
        produced_by=produced_by,
        produced_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(now)),
        verdict=verdict,
        world_mode=world_mode,
    )
    # ۴. append به زنجیرهٔ tamper-evident (output-path confinement در ReceiptStore)
    store.append(receipt)

    ok = reason == "completed"
    return RunResult(ok=ok, receipt=receipt, falsified=falsified,
                     raw_result=payload, reason=reason)
