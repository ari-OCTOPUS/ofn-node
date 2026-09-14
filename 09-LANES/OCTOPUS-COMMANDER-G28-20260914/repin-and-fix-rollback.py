"""Post-pre-effect repin + rollback-field correction (2026-09-14).

1. The dep-evidence pin moves to executor bytes 109e68c0 (the pin's PURPOSE is
   'executor carries the B8+G22+G28+TCB+G29+pre-effect capability set'; the
   bytes evolved by a verified fix, so the pin follows with provenance).
2. The G8 request's rollback field is corrected: the safe pre-image is the
   CURRENT live glass bytes ddee3da4 (rolling to ad34b138 would ALSO remove the
   G13 spool-write fix - never a safe destination). A staged copy of ddee3da4
   is preserved as the rollback source.
3. The rollback recipe now names the ENFORCED mechanism: any rollback request
   must carry preconditions=[{path: owner_reply.py, sha256: f8187600...}] which
   the executor checks (J4f) - the condition is no longer prose.
Chain receipts appended."""
import hashlib
import importlib.util
import json
import pathlib
import shutil

OA = "/home/ari/ofn/state/ops-agent/ops_agent.py"
GLASS_LIVE = pathlib.Path("/home/ari/ofn/ofn/agents/glass_runner.py")
MONEY_GATE = pathlib.Path("/home/ari/ofn/state/revenue-drive/owner_reply.py")
PIN = pathlib.Path("/home/ari/ofn/state/ops-agent/state/dep-evidence/B8-CAPABILITY-20260914.json")
PREIMAGE = pathlib.Path("/home/ari/ofn/state/owner_dialogue/preimage/glass_runner.py.ddee3da4-20260914.pre")
REQ = pathlib.Path("/home/ari/ofn/state/ops-agent/state/canary-requests/native-A2-G8-PRODUCER-010.json")

exec_sha = hashlib.sha256(pathlib.Path(OA).read_bytes()).hexdigest()
glass_sha = hashlib.sha256(GLASS_LIVE.read_bytes()).hexdigest()
gate_sha = hashlib.sha256(MONEY_GATE.read_bytes()).hexdigest()
assert exec_sha.startswith("109e68c0"), exec_sha
assert glass_sha.startswith("ddee3da4"), glass_sha
assert gate_sha.startswith("f8187600"), gate_sha

spec = importlib.util.spec_from_file_location("oa_rep3", OA)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


def chain(kind, **kw):
    m.append_jsonl(m.RECEIPTS,
                   {"schema": "octopus.ops-receipt.v1", "kind": kind,
                    "agent": "octopus-commander-editor/2026-09-14",
                    "at": m.now_iso(), **kw},
                   hash_field="ops_hash", prev_field="previous_ops_hash")


# 1) repin with provenance
old_pin = json.loads(PIN.read_text(encoding="utf-8"))
pin = dict(old_pin)
pin["expected_post_sha256"] = exec_sha
pin["pinned_at"] = m.now_iso()
pin["capability"] = ("executor holds B8 prefer-patched + base-verify + G22 "
                     "evidence-enforced deps + retire/dedupe G28 + TCB gate "
                     "G28-E + G29 dep resolution + PRE-EFFECT integrity "
                     "(source/target/deps freeze, enforced preconditions)")
pin["repin_history"] = pin.get("repin_history", []) + [{
    "from": old_pin["expected_post_sha256"][:16],
    "to": exec_sha[:16],
    "why": "pre-effect integrity patch 8e1c43e8 -> 109e68c0 (matrix 31/31 PASS)",
    "at": m.now_iso()}]
PIN.write_text(json.dumps(pin, indent=1, sort_keys=True) + "\n", encoding="utf-8")
chain("OPS_B_DEP_EVIDENCE_PINNED", pin=str(PIN), target=OA,
      pinned_sha256=exec_sha, repinned_from=old_pin["expected_post_sha256"][:16])

# 2) preserve the correct pre-image (current live bytes)
if not PREIMAGE.exists():
    shutil.copy2(GLASS_LIVE, PREIMAGE)
assert hashlib.sha256(PREIMAGE.read_bytes()).hexdigest() == glass_sha

# 3) correct the request's rollback field
req = json.loads(REQ.read_text(encoding="utf-8"))
req["rollback"] = {
    "mechanism": "B4 rollback-requests entry (executor-enforced)",
    "pre_image": str(PREIMAGE),
    "pre_image_sha256": glass_sha,
    "preconditions": [{"path": str(MONEY_GATE), "sha256": gate_sha}],
    "precondition_note": ("the executor checks preconditions at admission "
                          "(OPS_B_PRECONDITION_UNMET, request waits) - if the "
                          "money gates are not live, the restore NEVER runs"),
    "forbidden_pre_image": ("ad34b1388cb9ac9d... would ALSO remove the G13 "
                            "spool-write fix - never a rollback destination"),
    "manual_step": ("restore the G13+leak fixes separately if ever needed; a "
                    "bare restore to ad34b138 is not an authorized rollback")}
REQ.write_text(json.dumps(req, indent=1, sort_keys=True) + "\n", encoding="utf-8")
chain("OPS_B_REQUEST_ROLLBACK_REPINNED", request=REQ.name,
      pre_image=glass_sha[:16], precondition=gate_sha[:16])

ok, n = m.verify_own_chain()
print("chain_verify:", ok, n)
print("pin ->", exec_sha[:16], "| preimage staged:", glass_sha[:16],
      "| precondition gate:", gate_sha[:16])
