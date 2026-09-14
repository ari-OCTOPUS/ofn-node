"""Queue DAG: extract the REAL dependency edges from the on-disk requests,
classify each edge, upgrade the queue to the round's artifacts, and receipt.

Edge classification:
 - capability-pin (version condition): dep-evidence absolute pin on executor
   bytes - gates on a RUNTIME VERSION, not on another package
 - deploy-ordering: name-dep on another REQUEST - met when that request's
   target currently holds its expected_post (G29 resolves spool->executed;
   retire/rollback keep the edge live)
DAG after this script:  G8 --ordering--> W24 ; TRIO (independent, base=live
executor) ; G30 --ordering--> TRIO (avoids pin invalidation: after TRIO
deploys, executor bytes move, so G30's old byte-pin would go stale forever).
"""
import hashlib
import importlib.util
import json
import pathlib

SP = pathlib.Path("/home/ari/ofn/state/ops-agent/state/canary-requests")
OA = "/home/ari/ofn/state/ops-agent/ops_agent.py"
LIVE_EXEC = hashlib.sha256(pathlib.Path(OA).read_bytes()).hexdigest()
ART = pathlib.Path("/home/ari/ofn/state/coding-worker/stage/"
                   "SUCCESSOR-TRIO-20260914/ops_agent.py")
TRIO_SHA = hashlib.sha256(ART.read_bytes()).hexdigest()
assert LIVE_EXEC.startswith("109e68c0") and TRIO_SHA.startswith("a85db3b0")

spec = importlib.util.spec_from_file_location("oa_dag", OA)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

# 1) extract + classify the CURRENT on-disk DAG
print("=== DAG extracted from request identities ===")
for f in sorted(SP.glob("*.json")):
    req = json.loads(f.read_text(encoding="utf-8"))
    deps = req.get("dependencies") or []
    for d in deps:
        kind = ("deploy-ordering (request name-dep)" if not str(d).startswith("/")
                else "capability-pin (executor version condition)")
        print("  %s --%s--> %s" % (f.name, kind, str(d)[-60:]))
    print("  %s [base=%s artifact=%s]" % (f.name,
                                          str(req.get("base_sha256"))[:16],
                                          str(req.get("artifact_sha256"))[:16]))

# 2) TRIO request -> v2d artifact (lineage + this round's acceptances)
trio = json.loads((SP / "native-Z-SUCCESSOR-TRIO-001.json").read_text(encoding="utf-8"))
prev_sup = trio.get("supersedes", {})
trio["artifact_sha256"] = TRIO_SHA
trio["target_sha256"] = TRIO_SHA
trio["expected_post_sha256"] = TRIO_SHA
trio["patched"] = str(ART)
trio["supersedes"] = {
    "artifact": "d0b86a359917e04d...", "at": m.now_iso(),
    "by": "octopus-commander-editor/2026-09-14",
    "reason": ("owner-mission ROUND30: B5 same-scope measurement (frozen set, "
               "one rule, measurement-first verdict, quarantine-mv with unique "
               "names, no rm -rf), G3 no-starvation + safe priority parse, "
               "CATSCOPE verdicts, malformed-ledger tolerance, S4a internal "
               "byte-copy, S4b precondition freeze+re-check"),
    "lineage": "d0b86a35 -> 9126c388 -> aa867bfb -> ae293073 -> a85db3b0",
    "previous_supersede": prev_sup}
trio["stage_tests"] = {
    "battery": "trio-v2-battery 24/24 PASS on a85db3b0 (B5 real-path with "
               "counterexamples on v1/live, CATSCOPE isolated ledger, G3 "
               "robustness, S4a barrier, S4b both polarities)",
    "matrix": "g28-accept-v2 32/32 PASS on a85db3b0",
    "at": m.now_iso()}
(SP / "native-Z-SUCCESSOR-TRIO-001.json").write_text(
    json.dumps(trio, indent=1, sort_keys=True) + "\n", encoding="utf-8")

# 3) G30 request: byte-pin -> name-dep on TRIO (ordering edge, consumed by G29)
g30p = SP / "native-G30-STAGE-GUARD-WIRING-001.json"
g30 = json.loads(g30p.read_text(encoding="utf-8"))
old_pin = g30.get("dependencies", [])[0]
g30["dependencies_original"] = g30.get("dependencies")
g30["dependencies"] = ["native-Z-SUCCESSOR-TRIO-001.json"]
g30["dependency_note"] = {
    "at": m.now_iso(),
    "why": ("deploy-ordering: after TRIO deploys the executor bytes move, so a "
            "byte-pin on 109e68c0 would stale-block G30 forever; the name-dep "
            "is met exactly when the executor holds TRIO's expected_post "
            "(a85db3b0), survives TRIO's retire into executed/, and fails "
            "closed if TRIO is rolled back"),
    "old_edge": old_pin}
g30p.write_text(json.dumps(g30, indent=1, sort_keys=True) + "\n", encoding="utf-8")

# 4) receipts
m.append_jsonl(m.RECEIPTS,
               {"schema": "octopus.ops-receipt.v1",
                "kind": "OPS_B_REQUEST_ARTIFACT_UPDATED",
                "agent": "octopus-commander-editor/2026-09-14",
                "at": m.now_iso(),
                "request": "native-Z-SUCCESSOR-TRIO-001.json",
                "old_artifact": "d0b86a359917e04d", "new_artifact": TRIO_SHA,
                "why": "ROUND30 fixes; battery 24/24 + matrix 32/32"},
               hash_field="ops_hash", prev_field="previous_ops_hash")
m.append_jsonl(m.RECEIPTS,
               {"schema": "octopus.ops-receipt.v1",
                "kind": "OPS_B_REQUEST_EDGE_UPDATED",
                "agent": "octopus-commander-editor/2026-09-14",
                "at": m.now_iso(),
                "request": "native-G30-STAGE-GUARD-WIRING-001.json",
                "old_edge": "capability-pin " + str(old_pin)[-40:],
                "new_edge": "deploy-ordering native-Z-SUCCESSOR-TRIO-001.json",
                "why": "pin-version coupling turned into a consumed ordering edge"},
               hash_field="ops_hash", prev_field="previous_ops_hash")
ok, n = m.verify_own_chain()
print("chain_verify:", ok, n)
print("=== final queue ===")
for f in sorted(SP.glob("*.json")):
    req = json.loads(f.read_text(encoding="utf-8"))
    print(" ", f.name, "artifact", str(req.get("artifact_sha256"))[:16],
          "deps", [str(d)[-42:] for d in req.get("dependencies") or []])
