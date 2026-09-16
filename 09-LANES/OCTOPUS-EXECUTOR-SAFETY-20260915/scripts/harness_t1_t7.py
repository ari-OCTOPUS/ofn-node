#!/usr/bin/env python3
"""Isolated acceptance harness T1-T7 for the executor-safety artifact.

Runs the STAGED ops_agent.py with HOME redirected to a throwaway fixture root so
no live state is touched (module constants bind under $FX at import). T1-T6
re-assert the F-001/OW-8 behaviour on the new base; T7 covers this lane's
hardening: witness-unavailable stays queued (never executed/), the dedupe vector
it created is gone, verified receipts carry request+proposal_id provenance, and
_verified_by_receipt refuses a receipt whose request name does not match.
"""
import json
import os
import shutil
import sys
import tempfile
import time
from pathlib import Path

STAGE = Path(
    "/home/ari/ofn/state/coding-worker/stage/EXECUTOR-SAFETY-20260915/ops_agent.py"
)
RESULTS = []


def check(tid, name, cond, detail=""):
    RESULTS.append((tid, name, bool(cond), str(detail)[:160]))
    print(("PASS" if cond else "FAIL"), tid, name, detail if not cond else "")


def seed_fixture(fx: Path, receipts=None, signatures=None) -> None:
    ag = fx / "ofn/state/ops-agent"
    (ag / "state/canary-requests").mkdir(parents=True, exist_ok=True)
    for d in ("executed", "closed", "failed", "owner-tasks", "pending",
              "proposals", "awaiting-outcome"):
        (ag / "state" / d).mkdir(parents=True, exist_ok=True)
    shutil.copyfile(STAGE, ag / "ops_agent.py")
    shutil.copyfile("/home/ari/ofn/state/ops-agent/ops_budgets.json",
                    ag / "ops_budgets.json")
    (ag / "state/ops-receipts.jsonl").write_text(
        "".join(json.dumps(r) + "\n" for r in (receipts or [])), encoding="utf-8")
    (ag / "state/failure-signatures.json").write_text(json.dumps(
        {"schema": "x", "signatures": signatures or []}), encoding="utf-8")
    (fx / "ofn/state/autonomy").mkdir(parents=True, exist_ok=True)
    (fx / "ofn/state/autonomy/witness-pins.json").write_text(json.dumps({
        "ssh_identity": "/nonexistent/key", "witness_host": "127.0.0.1",
        "witness_inbox": "/tmp/nowhere", "witness_receipts_path": "/tmp/nowhere/r.jsonl"
    }), encoding="utf-8")


def load_agent(fx: Path):
    os.environ["HOME"] = str(fx)
    sys.path.insert(0, str(fx / "ofn/state/ops-agent"))
    import ops_agent as O
    return O


def req_file(name, target, sha, component, deps=None, fx=None):
    patched = "/nonexistent/artifact"
    if fx is not None:
        art = fx / f"art-{sha[:8]}.txt"
        art.write_text("artifact-bytes-" + sha[:16] + "\n", encoding="utf-8")
        patched = str(art)
    return {"target": target, "target_sha256": sha, "artifact_sha256": sha,
            "base_sha256": "0" * 64, "patched": patched,
            "component": component, "dependencies": deps or [],
            "task_id": name, "category": "B8_NON_TCB_PATCH_CANARY"}


def receipts_of(O):
    return [json.loads(l) for l in open(O.STATE / "ops-receipts.jsonl", encoding="utf-8") if l.strip()]


def main() -> int:
    now = time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime())
    fx = Path(tempfile.mkdtemp(prefix="exec-safety-fx-"))
    seed_fixture(fx)
    O = load_agent(fx)
    S = O.STATE
    pins = {"ssh_identity": "/nonexistent/key", "witness_host": "127.0.0.1",
            "witness_inbox": "/tmp/nowhere", "witness_receipts_path": "/tmp/x"}
    cat = {"timeout_s": 30}
    CAT = "B8_NON_TCB_PATCH_CANARY"

    # ---------------- T5: canonical breaker key + legacy fallback (regression)
    sig = [{"category": "B8", "fixed_at": "2026-09-15T09:00:00Z", "signature": "t5"}]
    seed = [
        {"kind": "OPS_B_OUTCOME_REJECTED", "category": CAT, "at": "2026-09-15T08:00:00+00:00"},
        {"kind": "OPS_B_OUTCOME_REJECTED", "category": CAT, "at": "2026-09-15T08:10:00+00:00"},
    ]
    (S / "failure-signatures.json").write_text(json.dumps({"signatures": sig}), encoding="utf-8")
    (S / "ops-receipts.jsonl").write_text("".join(json.dumps(r) + "\n" for r in seed), encoding="utf-8")
    ok, why = O.budget_allows("B8", "test-comp")
    check("T5a", "canonical B8 signature honoured (breaker closed)", ok and why == "OK", why)
    sig_legacy = [{"category": "RY", "fixed_at": "2026-09-15T09:00:00Z", "signature": "t5"}]
    (S / "failure-signatures.json").write_text(json.dumps({"signatures": sig_legacy}), encoding="utf-8")
    ok2, why2 = O.budget_allows("B8", "test-comp")
    check("T5b", "legacy RY signature still honoured read-only", ok2 and why2 == "OK", why2)
    (S / "failure-signatures.json").write_text(json.dumps({"signatures": []}), encoding="utf-8")
    ok3, why3 = O.budget_allows("B8", "test-comp")
    check("T5c", "no signature + 2 fresh rejections => breaker OPEN",
          (not ok3) and why3 == "CIRCUIT_BREAKER_OPEN", why3)

    # ---------------- T4: layer-2 self-heal retire (G8-021 simulation, regression)
    (S / "ops-receipts.jsonl").write_text("", encoding="utf-8")
    xsha = "f" * 64
    # legacy receipt: no request field -> sha-only fallback must still self-heal
    (S / "ops-receipts.jsonl").write_text(json.dumps({
        "kind": "OPS_B_EXECUTED", "category": CAT, "at": now + "+00:00",
        "verified": True, "outcome": "VERIFIED",
        "verify_kind": "sha256:/home/ari/ofn/ofn/agents/glass_runner.py:" + xsha}) + "\n",
        encoding="utf-8")
    (S / "canary-requests" / "sim-g8-021.json").write_text(json.dumps(
        req_file("sim-g8-021.json", "/home/ari/ofn/ofn/agents/glass_runner.py",
                 xsha, "ofn-agents")), encoding="utf-8")
    out = O.handle_spool_category(CAT, cat, pins, "canary-requests")
    ret = (S / "executed" / "sim-g8-021.json").exists()
    kinds = [r["kind"] for r in receipts_of(O)]
    check("T4a", "verified-by-receipt request auto-retired to executed/", ret)
    check("T4b", "F001_SELF_RETIRE receipt emitted", "F001_SELF_RETIRE" in kinds)
    check("T4c", "ZERO budget spend (no OPS_B_BLOCKED)", "OPS_B_BLOCKED" not in kinds)
    check("T4d", "loop drained => no-action-needed", out == "no-action-needed", out)

    # ---------------- T1: fairness — blocked req cannot starve ready req (regression)
    (S / "executed" / "sim-g8-021.json").unlink()
    (S / "ops-receipts.jsonl").write_text(json.dumps({
        "kind": "OPS_B_EXECUTED", "category": CAT, "at": now + "+00:00",
        "verified": True, "component": "ofn-agents", "outcome": "X"}) + "\n",
        encoding="utf-8")
    (S / "canary-requests" / "a-blocked.json").write_text(json.dumps(
        req_file("a-blocked.json", "/tmp/t1a", "a" * 64, "ofn-agents", fx=fx)), encoding="utf-8")
    (S / "canary-requests" / "b-ready.json").write_text(json.dumps(
        req_file("b-ready.json", "/tmp/t1b", "b" * 64, "fresh-comp", fx=fx)), encoding="utf-8")
    out = O.handle_spool_category(CAT, cat, pins, "canary-requests")
    rs = receipts_of(O)
    blocked = [r for r in rs if r.get("kind") == "OPS_B_BLOCKED"]
    evaluated = [r for r in rs if r.get("kind") in
                 ("EXECUTE_DEFERRED_NOT_RETIRED", "OPS_B_PAUSED_WITNESS_UNAVAILABLE")]
    somewhere = any((S / d / "b-ready.json").exists()
                    for d in ("canary-requests", "executed", "awaiting-outcome", "failed"))
    check("T1a", "first request dispositioned budget-blocked", len(blocked) == 1, blocked)
    check("T1b", "second request EVALUATED despite first blocked", len(evaluated) >= 1, evaluated)
    check("T1c", "second request not lost (parked somewhere known)", somewhere)
    check("T1d", "cycle summary reflects work (not no-action)", out != "no-action-needed", out)

    # ---------------- T6: dependency-unmet + independent (regression)
    for f in ("a-blocked.json", "b-ready.json"):
        (S / "canary-requests" / f).unlink(missing_ok=True)
    for d in ("canary-requests", "executed", "awaiting-outcome", "failed"):
        for g in os.listdir(S / d):
            (S / d / g).unlink()
    (S / "ops-receipts.jsonl").write_text("", encoding="utf-8")
    (S / "canary-requests" / "dep-unmet.json").write_text(json.dumps(
        req_file("dep-unmet.json", "/tmp/t6a", "c" * 64, "comp1",
                 deps=["native-NEVER-EXISTS.json"], fx=fx)), encoding="utf-8")
    (S / "canary-requests" / "indep.json").write_text(json.dumps(
        req_file("indep.json", "/tmp/t6b", "d" * 64, "comp2", fx=fx)), encoding="utf-8")
    O.handle_spool_category(CAT, cat, pins, "canary-requests")
    rs = receipts_of(O)
    unmet = [r for r in rs if r.get("kind") == "OPS_B_DEPENDENCY_UNMET"]
    indep_evaluated = [r for r in rs if r.get("kind") in
                       ("EXECUTE_DEFERRED_NOT_RETIRED", "OPS_B_PAUSED_WITNESS_UNAVAILABLE")]
    check("T6a", "dependency-unmet dispositioned + retained",
          len(unmet) == 1 and (S / "canary-requests" / "dep-unmet.json").exists())
    check("T6b", "independent request still evaluated", len(indep_evaluated) >= 1)

    # ---------------- T3: idempotent retire (regression)
    (S / "canary-requests" / "dup.json").write_text("{}", encoding="utf-8")
    O._retire_executed(S / "canary-requests" / "dup.json", "dup.json", CAT)
    O._retire_executed(S / "canary-requests" / "dup.json", "dup.json", CAT)
    rs = receipts_of(O)
    check("T3", "double retire => ALREADY_EXECUTED, no error",
          sum(1 for r in rs if r.get("kind") == "OPS_B_REQUEST_ALREADY_EXECUTED") == 1)

    # ---------------- T2: layer-1 retire at cycle-close (move BEFORE receipt, regression)
    (S / "canary-requests" / "req-x.json").write_text("{}", encoding="utf-8")
    (S / "awaiting-outcome" / "ao.json").write_text(json.dumps({
        "request": "req-x.json", "category": CAT, "component": "comp9",
        "outcome_proposal": "op-t2"}), encoding="utf-8")
    O.witness_pull = lambda p: [{"proposal_id": "op-t2",
                                 "verdict": "OUTCOME_CONFIRMED",
                                 "witness_hash": "deadbeefdeadbeef"}]
    out = O.progress_outcomes(pins)
    rs = receipts_of(O)
    ci = next((i for i, r in enumerate(rs) if r.get("kind") == "OPS_B_CYCLE_CLOSED"), None)
    check("T2a", "request file moved to executed/ at close",
          (S / "executed" / "req-x.json").exists())
    check("T2b", "cycle closed after move", out == "cycle-closed" and ci is not None)

    # ============================================================= T7 (this lane)
    # Clean slate for the witness-unavailable path.
    for d in ("canary-requests", "executed", "awaiting-outcome", "failed", "pending"):
        for g in os.listdir(S / d):
            (S / d / g).unlink()
    (S / "ops-receipts.jsonl").write_text("", encoding="utf-8")

    # A real, unblocked, dependency-free request. witness_push will fail (pins
    # point nowhere) so _witnessed_action returns "witness-unavailable".
    wsha = "e" * 64
    (S / "canary-requests" / "wu-req.json").write_text(json.dumps(
        req_file("wu-req.json", "/tmp/t7-target", wsha, "wu-comp", fx=fx)),
        encoding="utf-8")
    out7 = O.handle_spool_category(CAT, cat, pins, "canary-requests")
    rs = receipts_of(O)
    kinds = [r.get("kind") for r in rs]
    parked_paused = "OPS_B_PAUSED_WITNESS_UNAVAILABLE" in kinds
    stayed_in_queue = (S / "canary-requests" / "wu-req.json").exists()
    not_in_executed = not (S / "executed" / "wu-req.json").exists()
    check("T7a", "witness-unavailable emits PAUSED receipt", parked_paused, kinds)
    check("T7b", "witness-unavailable request STAYS in canary-requests (retry-safe)",
          stayed_in_queue)
    check("T7c", "witness-unavailable request NOT parked in executed/",
          not_in_executed)

    # T7d: the false-dedupe vector is gone. A later identical request must NOT be
    # marked ALREADY_EXECUTED just because a prior attempt was witness-unavailable.
    out7b = O.handle_spool_category(CAT, cat, pins, "canary-requests")
    rs = receipts_of(O)
    false_dedupe = [r for r in rs if r.get("kind") == "OPS_B_REQUEST_ALREADY_EXECUTED"]
    check("T7d", "no false ALREADY_EXECUTED after witness-unavailable retry",
          len(false_dedupe) == 0, false_dedupe)

    # T7e: verified OPS_B_EXECUTED receipts now carry request + proposal_id.
    # Drive a full pending->execute cycle with a stubbed witness that approves.
    for d in ("canary-requests", "executed", "awaiting-outcome", "failed", "pending"):
        for g in os.listdir(S / d):
            (S / d / g).unlink()
    (S / "ops-receipts.jsonl").write_text("", encoding="utf-8")
    tgt = fx / "t7-deploy-target.txt"
    tgt.write_text("OLD\n", encoding="utf-8")
    src = fx / "t7-deploy-source.txt"
    src.write_text("NEW-CONTENT\n", encoding="utf-8")
    import hashlib as _h
    src_sha = _h.sha256(src.read_bytes()).hexdigest()
    pid = "op-t7prov"
    (S / "proposals").mkdir(parents=True, exist_ok=True)
    (S / "proposals" / "action-map").mkdir(parents=True, exist_ok=True)
    (S / "proposals" / "action-map" / (pid + ".json")).write_text(json.dumps({
        "component": "prov-comp", "request": "prov-req.json",
        "proposal_id": pid,
        "argv": [["cp", str(src), str(tgt)]],
        "verify_kind": "sha256:" + str(tgt) + ":" + src_sha,
        "timeout_s": 30,
        "source_path": str(src), "source_sha256": src_sha,
        "target_path": str(tgt),
        "pre_target_sha256": _h.sha256(b"OLD\n").hexdigest(),
        "deps_verified": []}), encoding="utf-8")
    exp = {"proposal_id": pid, "target_component": "prov-comp"}
    r = O._execute_pending(CAT, exp)
    check("T7e", "verified OPS_B_EXECUTED carries request + proposal_id",
          r.get("kind") == "OPS_B_EXECUTED" and r.get("verified") is True
          and r.get("request") == "prov-req.json" and r.get("proposal_id") == pid, r)

    # T7f: _verified_by_receipt refuses a receipt whose request name mismatches.
    (S / "ops-receipts.jsonl").write_text(json.dumps({
        "kind": "OPS_B_EXECUTED", "category": CAT, "at": now + "+00:00",
        "verified": True, "outcome": "VERIFIED", "request": "SOMEONE-ELSE.json",
        "verify_kind": "sha256:/tmp/whatever:" + ("a" * 64)}) + "\n", encoding="utf-8")
    mismatched = {"target_sha256": "a" * 64}
    refused = O._verified_by_receipt(mismatched, "MY-REQ.json")
    accepted = O._verified_by_receipt(mismatched, "SOMEONE-ELSE.json")
    check("T7g", "named receipt does NOT retire a different request", not refused)
    check("T7h", "named receipt DOES match its own request", accepted)

    shutil.rmtree(fx, ignore_errors=True)
    n_fail = sum(1 for r in RESULTS if not r[2])
    print(f"-- {len(RESULTS)} checks, {n_fail} failed")
    return 1 if n_fail else 0


if __name__ == "__main__":
    sys.exit(main())
