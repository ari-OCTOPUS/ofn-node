"""Add the TRIO->W24 deploy-ordering edge (ROUND31 section 5): resolves the
ROUND30 contradiction ('independent' vs 'runs last by name') by making the
ordering EXPLICIT and consumed: TRIO waits until the binder holds W24's
expected_post. With this edge the cascade G8->W24->TRIO->G30 is fully
edge-driven; no name dependence, no manual repin after TRIO (G8/W24 are done
before TRIO can pass). Chain receipt appended."""
import hashlib
import importlib.util
import json
import pathlib

SP = pathlib.Path("/home/ari/ofn/state/ops-agent/state/canary-requests")
OA = "/home/ari/ofn/state/ops-agent/ops_agent.py"
TRIO_ART = pathlib.Path("/home/ari/ofn/state/coding-worker/stage/"
                        "SUCCESSOR-TRIO-20260914/ops_agent.py")
art = hashlib.sha256(TRIO_ART.read_bytes()).hexdigest()
assert art.startswith("db03333d"), art

spec = importlib.util.spec_from_file_location("oa_e", OA)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

p = SP / "native-Z-SUCCESSOR-TRIO-001.json"
req = json.loads(p.read_text(encoding="utf-8"))
req["artifact_sha256"] = art
req["target_sha256"] = art
req["expected_post_sha256"] = art
req["patched"] = str(TRIO_ART)
req["dependencies"] = [d for d in req.get("dependencies", [])
                       if "dep-evidence" in str(d)]
req["dependencies"].append("native-A3-W24-BINDER-006.json")
req["edge_note"] = {
    "at": m.now_iso(),
    "why": ("ROUND30 contradiction resolved: TRIO was 'independent' yet "
            "expected to run last only by filename. The explicit ordering "
            "edge is consumed by G29: TRIO passes only when the binder holds "
            "W24's expected_post (b9c504f8), making G8->W24->TRIO->G30 fully "
            "edge-driven with no manual repin (G8/W24 finish before TRIO can "
            "pass, so the executor pin never goes stale under them)"),
    "protection_binding": ("G8/W24 deploys run under the LIVE executor "
                           "109e68c0: pre-effect drift-block+verify YES; the "
                           "S4a in-memory copy and S4b precondition-freeze "
                           "are staged in TRIO and protect deploys AFTER it")}
req["stage_tests"] = {
    "battery": "round31-battery (this round): ledger tick gate, B5 "
               "completeness, decision consumer, DAG shuffle",
    "matrix": "g28-accept-v2 32/32 PASS on db03333d",
    "at": m.now_iso()}
p.write_text(json.dumps(req, indent=1, sort_keys=True) + "\n", encoding="utf-8")
m.append_jsonl(m.RECEIPTS,
               {"schema": "octopus.ops-receipt.v1",
                "kind": "OPS_B_REQUEST_EDGE_UPDATED",
                "agent": "octopus-commander-editor/2026-09-14",
                "at": m.now_iso(), "request": p.name,
                "new_edge": "deploy-ordering native-A3-W24-BINDER-006.json",
                "artifact": art,
                "why": "explicit consumed ordering; resolves ROUND30 "
                       "independent-vs-last contradiction"},
               hash_field="ops_hash", prev_field="previous_ops_hash")
ok, n = m.verify_own_chain()
print("chain_verify:", ok, n, "| TRIO deps:", req["dependencies"])
