#!/usr/bin/env python3
"""test_epistemic_schemas.py — ADR-039 Commit 1: strict schemas + canonical + policy + validator.

پوششِ تست‌های اجباریِ ADR §11 که در محدودهٔ C1 (pure validation، بدونِ runner/gate)
می‌گنجند:
  #1  claim بدونِ falsifier یا operational_definition   → block (ساخت شکست)
  #2  testability=0                                       → هیچ plan/packet (ساخت شکست)
  #3  receipt با git_sha/config_hash قدیمی               → block (stale_hash)
  #4  receipt با command/seed/environment متفاوت          → block (bind_mismatch)
  #7  evidence بدونِ producer مجاز                        → block (unauthorized_producer)
  #9  زنجیرهٔ receipt با parent_receipt_hash غلط          → block (chain_break)
  #12 نتیجه با seed/hash یکسان                            → replayable (canonical determinism)
به‌علاوهٔ checkهای ساختاریِ strict/forbid/frozen و سخت‌مرزهای may_execute/sandbox/authority.

سبکِ harness: هم‌الگو با test_env_factory.py (module-level FAILED + check()).
"""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

_OPS = Path(__file__).resolve().parent.parent
if str(_OPS) not in sys.path:
    sys.path.insert(0, str(_OPS))

from epistemics.schemas import (  # noqa: E402
    Authority,
    BindHashes,
    ClaimType,
    EpistemicClaim,
    EvidenceReceipt,
    Falsifier,
    GateDecision,
    GateOutcome,
    Prediction,
    PredictionDirection,
    SandboxProfile,
    TestDesign,
    TestPlan,
)
from epistemics.canonical import (  # noqa: E402
    SELF_REFERENTIAL_FIELDS,
    GENESIS,
    canonical_hash,
    canonical_json,
    chain_hash,
    material_hash_of,
    payload_hash,
)
from epistemics.policy import PolicyConfig, load_policy  # noqa: E402
from epistemics.validator import (  # noqa: E402
    validate_claim,
    validate_gate_decision,
    validate_plan,
    validate_receipt,
)

from pydantic import ValidationError  # noqa: E402

FAILED = 0


def check(name: str, cond: bool, detail: str = ""):
    global FAILED
    if cond:
        print(f"  OK {name}")
    else:
        FAILED += 1
        print(f"  FAIL {name}: {detail}")


def _raises(fn) -> bool:
    """آیا فراخوانیِ fn یک ValidationError انداخت؟"""
    try:
        fn()
    except ValidationError:
        return True
    except Exception:  # ساخت باید ValidationError بدهد، نه چیزِ دیگر
        return False
    return False


# ============================================================================
# builders
# ============================================================================
def _prediction(**over) -> Prediction:
    base = dict(
        variable="discovery_rate_B_minus_A",
        direction=PredictionDirection.INCREASE,
        operational_ref="holdout S1 mean discovery rate",
    )
    base.update(over)
    return Prediction(**base)


def _falsifier(**over) -> Falsifier:
    base = dict(
        description="B fails to exceed A on held-out deceptive grids",
        operational_ref="holdout mean over S1 family",
        metric="discovery_rate",
        threshold="discovery_B - discovery_A <= 0",
    )
    base.update(over)
    return Falsifier(**base)


def _claim(**over) -> EpistemicClaim:
    base = dict(
        claim_id="CLM-1",
        claim_type=ClaimType.CAUSAL,
        operational_definition="Agent B discovers the deceptive optimum more often than A on held-out grids.",
        competing_claim_ids=["CLM-null", "CLM-novelty"],
        predictions=[_prediction()],
        falsifier=_falsifier(),
        testability=0.8,
        prior=0.5,
        source_git_sha="abc1234",
        source_config_hash="deadbeefdeadbeef",
        requested_authority=Authority.PROPOSE,
    )
    base.update(over)
    return EpistemicClaim(**base)


def _binds(**over) -> BindHashes:
    base = dict(
        git_sha="abc1234",
        material_hash="m" * 16,
        config_hash="c" * 16,
        environment_hash="e" * 16,
        seed_set_hash="s" * 16,
        command_hash="cmd" * 6,
        artifact_hashes={"outputs/out.jsonl": "a" * 16},
    )
    base.update(over)
    return BindHashes(**base)


def _receipt(**over) -> EvidenceReceipt:
    """receipt با canonical_payload_hashِ درستِ باز-محاسبه‌شده."""
    base = dict(
        receipt_id="R-1",
        plan_id="P-1",
        claim_id="CLM-1",
        binds=_binds(),
        parent_receipt_hash=GENESIS,
        produced_by="epistemic_sandbox_runner",
        produced_at="2026-08-12T00:00:00Z",
        verdict="pending",
        canonical_payload_hash="placeholder",  # درست می‌شود
    )
    base.update(over)
    # اگر binds عوض شده، payload_hash را از نو بساز.
    tmp = EvidenceReceipt(**base)
    base["canonical_payload_hash"] = payload_hash(tmp.model_dump(mode="json"))
    return EvidenceReceipt(**base)


def _plan(**over) -> TestPlan:
    base = dict(
        plan_id="P-1",
        claim_id="CLM-1",
        design=TestDesign.HOLDOUT,
        interventions=["holdout_seed_split"],
        discriminating_prediction=_prediction(),
        falsifier=_falsifier(),
        max_runs=10,
        max_wall_seconds=60,
        max_cost_aud=0.1,
        seed_set=[1, 2, 3],
        holdout=True,
    )
    base.update(over)
    return TestPlan(**base)


# ============================================================================
# §11 #1 + #2: claim block در زمانِ ساخت
# ============================================================================
def t_claim_minimal_ok():
    c = _claim()
    check("claim minimal constructs", c.claim_id == "CLM-1")


def t_claim_missing_falsifier_blocked():            # §11 #1
    d = _claim().model_dump(mode="json")
    d.pop("falsifier")
    check("claim without falsifier blocked (§11 #1)", _raises(lambda: EpistemicClaim(**d)))


def t_claim_missing_operational_definition_blocked():   # §11 #1
    d = _claim().model_dump(mode="json")
    d.pop("operational_definition")
    check("claim without operational_definition blocked (§11 #1)",
          _raises(lambda: EpistemicClaim(**d)))


def t_claim_empty_operational_definition_blocked():
    check("empty operational_definition blocked",
          _raises(lambda: _claim(operational_definition="")))


def t_claim_testability_zero_blocked():             # §11 #2
    check("testability=0 blocked (§11 #2)", _raises(lambda: _claim(testability=0.0)))


def t_claim_no_competing_hypothesis_blocked():
    check("no competing hypothesis blocked",
          _raises(lambda: _claim(competing_claim_ids=[])))


def t_claim_no_prediction_blocked():
    check("no discriminating prediction blocked",
          _raises(lambda: _claim(predictions=[])))


def t_claim_dogmatic_prior_zero_blocked():
    check("dogmatic prior=0 blocked", _raises(lambda: _claim(prior=0.0)))


def t_claim_dogmatic_prior_one_blocked():
    check("dogmatic prior=1 blocked", _raises(lambda: _claim(prior=1.0)))


# ============================================================================
# سخت‌مرزها در سطحِ type/enum
# ============================================================================
def t_authority_propose_only():
    check("Authority has only PROPOSE (execute forbidden)",
          list(Authority.__members__) == ["PROPOSE"])


def t_sandbox_no_network_only():
    check("SandboxProfile has only NO_NETWORK",
          list(SandboxProfile.__members__) == ["NO_NETWORK"])


def t_claim_forbidden_authority_unreachable():
    # execute اصلاً در enum نیست — نمی‌توان ساخت.
    d = _claim().model_dump(mode="json")
    d["requested_authority"] = "execute"
    check("authority=execute rejected", _raises(lambda: EpistemicClaim(**d)))


# ============================================================================
# strict / forbid / frozen (structural)
# ============================================================================
def t_claim_extra_field_forbidden():
    d = _claim().model_dump(mode="json")
    d["surprise_field"] = "evil"
    check("extra field forbidden (extra=forbid)", _raises(lambda: EpistemicClaim(**d)))


def t_claim_frozen_immutable():
    c = _claim()
    check("frozen claim immutable",
          _raises_strict_setattr(lambda: setattr(c, "prior", 0.9)))


def _raises_strict_setattr(fn) -> bool:
    try:
        fn()
    except (ValidationError, TypeError):
        return True
    except Exception:
        return False
    return False


# ============================================================================
# TestPlan: sandbox_force + caps
# ============================================================================
def t_plan_forced_no_network():
    p = _plan()
    check("plan sandbox forced no_network",
          p.sandbox_profile == SandboxProfile.NO_NETWORK)


def t_plan_cap_exceeded_runs_blocked():
    pol = load_policy()
    p = _plan(max_runs=pol.caps.max_runs + 1)
    r = validate_plan(p, pol)
    check("plan over cap.max_runs blocked", r.blocked and "cap_exceeded_runs" in r.reason_codes)


def t_plan_cap_exceeded_cost_blocked():
    pol = load_policy()
    p = _plan(max_cost_aud=pol.caps.max_cost_aud + 1.0)
    r = validate_plan(p, pol)
    check("plan over cap.max_cost blocked", r.blocked and "cap_exceeded_cost" in r.reason_codes)


def t_plan_valid_ok():
    pol = load_policy()
    r = validate_plan(_plan(), pol)
    check("valid plan ok", r.ok and not r.blocked)


# ============================================================================
# EvidenceReceipt: §11 #3 #4 #7 #9 + payload-hash
# ============================================================================
def _expected_binds() -> dict:
    return {
        "git_sha": "abc1234",
        "config_hash": "c" * 16,
        "environment_hash": "e" * 16,
        "seed_set_hash": "s" * 16,
        "command_hash": "cmd" * 6,
    }


def t_receipt_valid_ok():
    pol = load_policy()
    r = validate_receipt(
        _receipt(),
        expected_binds=_expected_binds(),
        authorized_producers=set(pol.authorized_producers),
        expected_parent_hash=GENESIS,
    )
    check("valid receipt ok", r.ok and not r.blocked)


def t_receipt_unauthorized_producer_blocked():      # §11 #7
    r = validate_receipt(
        _receipt(produced_by="rogue_llm"),
        expected_binds=_expected_binds(),
        authorized_producers={"epistemic_sandbox_runner"},
        expected_parent_hash=GENESIS,
    )
    check("unauthorized producer blocked (§11 #7)",
          r.blocked and "unauthorized_producer" in r.reason_codes)


def t_receipt_stale_git_sha_blocked():              # §11 #3
    exp = _expected_binds()
    exp["git_sha"] = "newercommit9999"   # receipt همچنان abc1234 دارد ⇒ stale
    r = validate_receipt(
        _receipt(),
        expected_binds=exp,
        authorized_producers={"epistemic_sandbox_runner"},
        expected_parent_hash=GENESIS,
    )
    check("stale git_sha blocked (§11 #3)",
          r.blocked and "stale_hash" in r.reason_codes)


def t_receipt_bind_mismatch_seed_blocked():         # §11 #4
    exp = _expected_binds()
    exp["seed_set_hash"] = "different_seed_hash!!"
    r = validate_receipt(
        _receipt(),
        expected_binds=exp,
        authorized_producers={"epistemic_sandbox_runner"},
        expected_parent_hash=GENESIS,
    )
    check("seed bind mismatch blocked (§11 #4)",
          r.blocked and any(c.startswith("bind_mismatch:seed_set_hash") for c in r.reason_codes))


def t_receipt_bind_mismatch_command_blocked():      # §11 #4
    exp = _expected_binds()
    exp["command_hash"] = "differentcommandhash"
    r = validate_receipt(
        _receipt(),
        expected_binds=exp,
        authorized_producers={"epistemic_sandbox_runner"},
        expected_parent_hash=GENESIS,
    )
    check("command bind mismatch blocked (§11 #4)",
          r.blocked and any("command_hash" in c for c in r.reason_codes))


def t_receipt_chain_break_blocked():                # §11 #9
    r = validate_receipt(
        _receipt(),
        expected_binds=_expected_binds(),
        authorized_producers={"epistemic_sandbox_runner"},
        expected_parent_hash="WRONG-PARENT-HASH",
    )
    check("wrong parent_receipt_hash blocked (§11 #9)",
          r.blocked and "chain_break" in r.reason_codes)


def t_receipt_payload_hash_mismatch_blocked():
    # payload_hash را دستکاری کن — باز-محاسبه با مقدارِ ذخیره‌شده فرق می‌کند.
    rcpt = _receipt()
    tampered = rcpt.model_dump(mode="json")
    tampered["canonical_payload_hash"] = "tampereddeadbeef"
    forged = EvidenceReceipt(**tampered)
    r = validate_receipt(
        forged,
        expected_binds=_expected_binds(),
        authorized_producers={"epistemic_sandbox_runner"},
        expected_parent_hash=GENESIS,
    )
    check("tampered canonical_payload_hash blocked",
          r.blocked and "payload_hash_mismatch" in r.reason_codes)


# ============================================================================
# GateDecision: may_execute + INCONCLUSIVE fail-closed (§5, §7.2)
# ============================================================================
def t_decision_may_execute_true_blocked():
    check("may_execute=True rejected",
          _raises(lambda: GateDecision(
              decision_id="D-1", receipt_id="R-1", claim_id="CLM-1",
              outcome=GateOutcome.SUPPORTED, belief_delta_log_odds=1.0,
              may_execute=True,
          )))


def t_decision_default_may_execute_false():
    d = GateDecision(
        decision_id="D-1", receipt_id="R-1", claim_id="CLM-1",
        outcome=GateOutcome.SUPPORTED, belief_delta_log_odds=1.0,
    )
    check("GateDecision default may_execute False", d.may_execute is False)


def t_decision_inconclusive_nonzero_delta_blocked():    # §5
    check("INCONCLUSIVE with nonzero delta rejected",
          _raises(lambda: GateDecision(
              decision_id="D-1", receipt_id="R-1", claim_id="CLM-1",
              outcome=GateOutcome.INCONCLUSIVE, belief_delta_log_odds=0.5,
          )))


def t_decision_inconclusive_zero_delta_ok():
    d = GateDecision(
        decision_id="D-1", receipt_id="R-1", claim_id="CLM-1",
        outcome=GateOutcome.INCONCLUSIVE, belief_delta_log_odds=0.0,
    )
    check("INCONCLUSIVE with zero delta ok", validate_gate_decision(d).ok)


# ============================================================================
# canonical.py — §11 #12 (replayable) + self-ref stripping + chain
# ============================================================================
def t_canonical_deterministic_replayable():         # §11 #12
    a = {"seed": 1, "agent": "B", "config": "x", "git_sha": "abc"}
    b = {"git_sha": "abc", "agent": "B", "seed": 1, "config": "x"}  # ترتیبِ متفاوت
    check("canonical_hash replayable (order-independent) (§11 #12)",
          canonical_hash(a) == canonical_hash(b))


def t_canonical_distinct_inputs_distinct():
    check("distinct inputs → distinct hashes",
          canonical_hash({"a": 1}) != canonical_hash({"a": 2}))


def t_payload_hash_strips_self_ref():
    body = {
        "receipt_id": "R-1",
        "binds": {"git_sha": "abc"},
        "canonical_payload_hash": "WHATEVER",
        "parent_receipt_hash": GENESIS,
        "produced_at": "2026-08-12T00:00:00Z",
    }
    body2 = dict(body, canonical_payload_hash="DIFFERENT", parent_receipt_hash="other")
    check("payload_hash ignores self-referential fields",
          payload_hash(body) == payload_hash(body2))


def t_payload_hash_keeps_binds():
    body = {"binds": {"git_sha": "abc"}, "receipt_id": "R-1"}
    body2 = {"binds": {"git_sha": "XYZ"}, "receipt_id": "R-1"}
    check("payload_hash reflects content (binds)",
          payload_hash(body) != payload_hash(body2))


def t_self_ref_set_includes_key_fields():
    for f in ("canonical_payload_hash", "parent_receipt_hash", "signature_b64",
              "hash", "prev_hash"):
        check(f"SELF_REFERENTIAL_FIELDS has {f}", f in SELF_REFERENTIAL_FIELDS)


def t_chain_hash_deterministic():
    body = {"x": 1, "y": 2}
    check("chain_hash deterministic", chain_hash(GENESIS, body) == chain_hash(GENESIS, body))


def t_chain_hash_parent_sensitive():
    body = {"x": 1}
    check("chain_hash parent-sensitive",
          chain_hash(GENESIS, body) != chain_hash("aaaa", body))


def t_material_hash_order_independent():
    a = {"runner.py": "print(1)", "env.py": "x=2"}
    b = {"env.py": "x=2", "runner.py": "print(1)"}
    check("material_hash order-independent",
          material_hash_of(a) == material_hash_of(b))


def t_material_hash_content_sensitive():
    check("material_hash content-sensitive",
          material_hash_of({"a.py": "1"}) != material_hash_of({"a.py": "2"}))


# ============================================================================
# policy.py — fail-closed loader
# ============================================================================
def t_policy_load_ok():
    pol = load_policy()
    check("policy loads", isinstance(pol, PolicyConfig))
    check("policy sandbox no_network", pol.sandbox_profile == "no_network")
    check("policy authority propose", pol.max_authority == "propose")
    check("policy default_off", pol.default_off is True)
    check("policy has authorized producers", len(pol.authorized_producers) >= 1)


def t_policy_missing_file_freeze():
    ok = False
    try:
        load_policy(Path("__definitely_not_here__.yaml"))
    except RuntimeError:
        ok = True
    except Exception:
        ok = False
    check("missing policy file → RuntimeError (FREEZE)", ok)


def _write_bad_policy(override: dict) -> Path:
    import yaml as _yaml
    base = {
        "schema_version": 1,
        "default_off": True,
        "env_flag": "EPISTEMIC_TESTS",
        "caps": {"max_runs": 1, "max_wall_seconds": 1, "max_cost_aud": 0.1},
        "belief_update": {"clip_log_odds": 6.0, "lambda_disagreement": 0.5},
        "independence": {"min_clusters": 3, "clustering_keys": ["provider"]},
        "producers": {"authorized": ["epistemic_sandbox_runner"]},
        "maturity_ladder": {},
    }
    base.update(override)
    fd, path = tempfile.mkstemp(suffix=".yaml")
    import os as _os
    _os.close(fd)
    with open(path, "w", encoding="utf-8") as fh:
        _yaml.dump(base, fh)
    return Path(path)


def t_policy_bad_sandbox_freeze():
    path = _write_bad_policy({"sandbox_profile": "network", "max_authority": "propose"})
    ok = False
    try:
        load_policy(path)
    except RuntimeError:
        ok = True
    except Exception:
        ok = False
    finally:
        path.unlink(missing_ok=True)
    check("policy sandbox != no_network → RuntimeError (FREEZE)", ok)


def t_policy_bad_authority_freeze():
    path = _write_bad_policy({"sandbox_profile": "no_network", "max_authority": "execute"})
    ok = False
    try:
        load_policy(path)
    except RuntimeError:
        ok = True
    except Exception:
        ok = False
    finally:
        path.unlink(missing_ok=True)
    check("policy authority != propose → RuntimeError (FREEZE)", ok)


def t_policy_missing_key_freeze():
    path = _write_bad_policy({"sandbox_profile": "no_network", "max_authority": "propose"})
    # یک فایلِ معتبر بساز ولی یک کلیدِ الزامی را حذف کن.
    import yaml as _yaml
    txt = path.read_text("utf-8")
    txt = txt.replace("schema_version: 1\n", "")
    path.write_text(txt, encoding="utf-8")
    ok = False
    try:
        load_policy(path)
    except RuntimeError:
        ok = True
    except Exception:
        ok = False
    finally:
        path.unlink(missing_ok=True)
    check("policy missing required key → RuntimeError (FREEZE)", ok)


# ============================================================================
# round-trip replayability (§11 #12) — بازتولید از model_dump
# ============================================================================
def t_claim_roundtrip_hash_stable():
    c = _claim()
    h1 = canonical_hash(c.model_dump(mode="json"))
    h2 = canonical_hash(c.model_dump(mode="json"))
    check("claim dump hash stable across calls", h1 == h2)


def t_receipt_roundtrip_rebuild_same_hash():
    rcpt = _receipt()
    dump = rcpt.model_dump(mode="json")
    rebuilt = EvidenceReceipt(**dump)
    check("receipt rebuild → same canonical_payload_hash",
          rebuilt.canonical_payload_hash == rcpt.canonical_payload_hash)


# ============================================================================
def main():
    tests = sorted((n, f) for n, f in globals().items() if n.startswith("t_"))
    for name, fn in tests:
        try:
            fn()
        except Exception as exc:  # noqa: BLE001
            global FAILED
            FAILED += 1
            print(f"  CRASH {name}: {type(exc).__name__}: {exc}")
    total = len(tests)
    print(f"\n{'OK' if not FAILED else 'FAIL'} test_epistemic_schemas: "
          f"{total - FAILED}/{total} (failed={FAILED})")
    return 1 if FAILED else 0


if __name__ == "__main__":
    sys.exit(main())
