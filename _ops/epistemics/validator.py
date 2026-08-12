"""validator.py — اعتبارسنجیِ pure برای claim/plan/receipt/decision (ADR-039 C1).

هیچ I/O، هیچ network، هیچ side-effect. تمامِ checkها با reason_codes برمی‌گردند تا گیت
بتواند fail-closed و قابل‌ممیزی تصمیم بگیرد. ساختارِ first-line توسط schemas.py
(strict/forbid/frozen) enforcing می‌شود؛ این لایه، checkهای وابسته به policy-context
(caps، authorized_producers، binding، staleness، payload-hash) را انجام می‌دهد و
checkهای ساختاری را به‌عنوان defense-in-depth تکرار می‌کند.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Mapping, Set

from .canonical import payload_hash
from .policy import PolicyConfig
from .schemas import (
    Authority,
    EpistemicClaim,
    EvidenceReceipt,
    GateDecision,
    GateOutcome,
    SandboxProfile,
    TestPlan,
)


@dataclass(frozen=True)
class ValidationResult:
    """خروجیِ یک check: ok=true یا blocked=true همراه با reason_codes."""
    ok: bool
    blocked: bool
    reason_codes: List[str] = field(default_factory=list)


def _ok() -> ValidationResult:
    return ValidationResult(ok=True, blocked=False, reason_codes=[])


def _block(*codes: str) -> ValidationResult:
    clean = [c for c in codes if c]
    return ValidationResult(ok=False, blocked=True, reason_codes=clean)


def validate_claim(claim: EpistemicClaim, policy: PolicyConfig) -> ValidationResult:
    """defense-in-depth ساختاری + سازگاری با policy.

    برای یک claimِ ساخته‌شده (که schemas ساختار را تضمین کرده)، تقریباً همیشه ok
    برمی‌گردد؛ تمامِ مسیرهای block در زمانِ ساخت رخ می‌دهند. این check صرفاً برای
    a) checkِ policy-context (authority)، b) defense-in-depth اگر کسی model_construct
    زد، وجود دارد.
    """
    codes: List[str] = []
    if not claim.operational_definition.strip():
        codes.append("missing_operational_definition")
    if claim.falsifier is None:
        codes.append("missing_falsifier")
    if claim.testability <= 0.0:
        codes.append("zero_testability")
    if len(claim.competing_claim_ids) < 1:
        codes.append("no_competing_hypothesis")
    if len(claim.predictions) < 1:
        codes.append("no_discriminating_prediction")
    if claim.requested_authority is not Authority.PROPOSE:
        codes.append("forbidden_authority")
    if not (0.0 < claim.prior < 1.0):
        codes.append("dogmatic_prior")
    if policy.max_authority != "propose":
        codes.append("policy_authority_mismatch")
    return _block(*codes) if codes else _ok()


def validate_plan(plan: TestPlan, policy: PolicyConfig) -> ValidationResult:
    """sandbox_force + سقفِ منابع در برابرِ policy.caps."""
    codes: List[str] = []
    if plan.sandbox_profile is not SandboxProfile.NO_NETWORK:
        codes.append("forbidden_sandbox")
    if plan.max_runs > policy.caps.max_runs:
        codes.append("cap_exceeded_runs")
    if plan.max_wall_seconds > policy.caps.max_wall_seconds:
        codes.append("cap_exceeded_wall")
    if plan.max_cost_aud > policy.caps.max_cost_aud:
        codes.append("cap_exceeded_cost")
    return _block(*codes) if codes else _ok()


def validate_receipt(
    receipt: EvidenceReceipt,
    *,
    expected_binds: Mapping[str, str],
    authorized_producers: Set[str],
    expected_parent_hash: str,
) -> ValidationResult:
    """producer مجاز + زنجیره + binding + staleness + payload-hash.

    expected_binds: نگاشتِ {bind_key: expected_value} برای کلیدهای
        git_sha / config_hash / environment_hash / seed_set_hash / command_hash.
        اختلاف در git_sha ⇒ stale_hash (ADR §11 #3)؛ سایر ⇒ bind_mismatch (§11 #4).
    authorized_producers: مجموعهٔ producerهای مجاز (policy.authorized_producers).
    expected_parent_hash: parent_receipt_hash موردِ انتظار (زنجیرهٔ append-only، §11 #9).
    """
    codes: List[str] = []

    # #7: producer باید مجاز باشد.
    if receipt.produced_by not in authorized_producers:
        codes.append("unauthorized_producer")

    # #9: زنجیرهٔ receipt.
    if receipt.parent_receipt_hash != expected_parent_hash:
        codes.append("chain_break")

    # #3/#4: binding — receipt باید دقیقاً به همان hashها باند شده باشد.
    rb = receipt.binds
    bind_map = {
        "git_sha": rb.git_sha,
        "config_hash": rb.config_hash,
        "environment_hash": rb.environment_hash,
        "seed_set_hash": rb.seed_set_hash,
        "command_hash": rb.command_hash,
    }
    for key, expected in expected_binds.items():
        actual = bind_map.get(key)
        if actual is None:
            continue
        if actual != expected:
            # git_sha متفاوت ⇒ احتمالاً receipt از HEAD قدیمی است (stale).
            codes.append("stale_hash" if key == "git_sha" else f"bind_mismatch:{key}")

    # canonical_payload_hash باید از بدنهٔ receipt (منهایِ فیلدهای خودارجاع) باز-محاسبه شود.
    recomputed = payload_hash(receipt.model_dump(mode="json"))
    if recomputed != receipt.canonical_payload_hash:
        codes.append("payload_hash_mismatch")

    return _block(*codes) if codes else _ok()


def validate_gate_decision(decision: GateDecision) -> ValidationResult:
    """may_execute=False + fail-closed INCONCLUSIVE (defense-indepth بعد از schemas)."""
    codes: List[str] = []
    if decision.may_execute is not False:
        codes.append("may_execute_not_false")
    if decision.outcome is GateOutcome.INCONCLUSIVE and decision.belief_delta_log_odds != 0.0:
        codes.append("inconclusive_nonzero_delta")
    return _block(*codes) if codes else _ok()
