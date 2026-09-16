import importlib.util
import json
import pathlib

OA = "/home/ari/ofn/state/ops-agent/ops_agent.py"
spec = importlib.util.spec_from_file_location("oa_b", OA)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

B = pathlib.Path("/home/ari/ofn/state/ops-agent/ops_budgets.json")
old = json.loads(B.read_text(encoding="utf-8"))
new = dict(old)
new["per_node_24h"] = 10
new["mesh_wide_24h"] = 15
new["_authority"] = ("owner decision 2026-09-14: ALL FOUR unlock options "
                     "selected (quota 10x, API key, bigger model, warm customer)")
B.write_text(json.dumps(new, indent=2) + "\n", encoding="utf-8")
m.append_jsonl(m.RECEIPTS,
    {"schema": "octopus.ops-receipt.v1", "kind": "OPS_BUDGET_UPDATED",
     "agent": "octopus-commander-editor/2026-09-14", "at": m.now_iso(),
     "old": {"per_node_24h": 2, "mesh_wide_24h": 3},
     "new": {"per_node_24h": 10, "mesh_wide_24h": 15},
     "authority": "owner selected ALL FOUR 10x options at 2026-09-14T22:15Z"},
    hash_field="ops_hash", prev_field="previous_ops_hash")
ok, n = m.verify_own_chain()
print("budget: 2->10 per_node, 3->15 mesh | chain:", ok, n)
