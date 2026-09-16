import hashlib
import importlib.util
import json
import pathlib
import sys
import tempfile

V2 = ("/home/ari/ofn/state/coding-worker/stage/SUCCESSOR-TRIO-20260914/"
      "ops_agent.py")
fx = pathlib.Path(tempfile.mkdtemp(prefix="dbgb5-"))
import os
for i in range(3):
    d = fx / ("stable/pkg%d/__pycache__" % i)
    d.mkdir(parents=True)
    (d / "x.pyc").write_bytes(b"Z" * 1024)
os.chmod(fx / "stable/pkg1/__pycache__", 0o000)
_real_home = pathlib.Path.home
pathlib.Path.home = classmethod(lambda cls, _fx=fx: _fx)

spec = importlib.util.spec_from_file_location("dbg_oa", V2)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
m.ROOT = fx
m.STATE = fx / "state"
m.RECEIPTS = m.STATE / "ops-receipts.jsonl"
m.GOALS = m.STATE / "goals.jsonl"
m.OBS = m.STATE / "observations.jsonl"
m.CONSUMPTION = m.STATE / "witness-consumption.jsonl"
m.ARMED = m.STATE / "armed.json"
m.PENDING = m.STATE / "pending"
m.CONTRACTS = fx / "ops_contracts.json"
m.BUDGETS = fx / "ops_budgets.json"
m.STABLE_ROOT = fx / "stable"
m.PINS_FILE = fx / "witness-pins.json"
m.STATE.mkdir(parents=True, exist_ok=True)
m.BUDGETS.write_text(json.dumps({"mesh_wide_24h": 99, "per_node_24h": 99,
                                 "per_component_30min": 99,
                                 "circuit_breaker_after_same_class_failures": 99}),
                     encoding="utf-8")
m.PINS_FILE.write_text("{}", encoding="utf-8")
m.witness_push = lambda pins, name, data: (True, "fx")
m.witness_pull = lambda pins: []

r1 = m.handle_b5_storage({"timeout_s": 30}, {})
print("r1:", r1)
# approve via a minimal verdict row set
row = {"schema": "octopus.remote-witness-receipt.v1",
       "verdict": "APPROVE_ELIGIBLE_CLASS_B", "executable": False,
       "action_authority": "NONE",
       "node_182_identity_evidence": {"machine_id_sha256": "f" * 64},
       "witness_code_hash": "c" * 64, "witness_contract_hash": "d" * 64,
       "previous_witness_hash": None}
# build the verdict from the pending file
pend = list((m.STATE / "pending").glob("*.json"))
print("r1:", r1, "pending:", pend)
if pend:
    exp = json.loads(pend[0].read_text(encoding="utf-8"))["exp"]
    row.update({k: exp[k] for k in ("proposal_id", "proposal_hash",
                                    "action_contract_hash",
                                    "precondition_hash", "input_hash",
                                    "rollback_contract_hash", "target_node",
                                    "target_component", "timeout_s",
                                    "producer_authority")})
    row["action_class"] = "B"
    row["timestamp"] = m.now_iso()
    row["witness_hash"] = m.sha_obj(row)
    m.witness_pull = lambda pins: [row]
    r2 = m.progress_pending({"node182_identity": "f" * 64,
                             "witness_code_sha256": "c" * 64,
                             "witness_contract_sha256": "d" * 64})
    print("r2:", r2)
for x in m.read_receipts():
    if x.get("kind") == "OPS_B_EXECUTED":
        print("EXEC keys:", sorted(x.keys()))
        print("verified:", x.get("verified"), "| vk:",
              str(x.get("verify_kind"))[:44], "| freed:", x.get("bytes_freed"))
        print("exit_codes:", x.get("exit_codes"))
        print("argv:", json.dumps(x.get("argv"))[:300])
