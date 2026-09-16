import importlib.util
import json
import pathlib
import sys
import tempfile

sys.path.insert(0, "/home/ari/ofn/ofn/agents")
sys.path.insert(0, "/home/ari/ofn")
sys.path.insert(0, "/home/ari/ofn/ofn")
sys.path.insert(0, "/home/ari/ofn/ofn/budget")

spec = importlib.util.spec_from_file_location(
    "bo", "/home/ari/ofn/ofn/agents/go_b3_owner_bind.py")
b = importlib.util.module_from_spec(spec)
spec.loader.exec_module(b)

fx = pathlib.Path(tempfile.mkdtemp())
od = fx / "owner_dialogue"
od.mkdir(parents=True)
b.STATE = od
b.REGISTRY = od / "go_b3_pending_registry.json"
b.SPOOL = od / "go_b3_tg_spool.jsonl"
b.OFFSET = od / "go_b3_tg_offset.txt"
b.DECISIONS = od / "owner_decision.v1.jsonl"

REG_X = "a03b2ecc" + "9" * 56
REG_Y = "c" * 64
REG_Z = "d" * 64
b.REGISTRY.write_text(json.dumps({"requests": [
    {"id": "CARD-X", "card": "CARD-X", "payload_sha256": REG_X, "status": "consumed"},
    {"id": "CARD-Y", "card": "CARD-Y", "payload_sha256": REG_Y, "status": "pending"},
    {"id": "CARD-Z", "card": "CARD-Z", "payload_sha256": REG_Z, "status": "pending"},
]}), encoding="utf-8")

text = "Confirming " + REG_Y
print("hexes:", b.HEX_PAT.findall(text))
rows = b.pending_rows(b.load_registry())
print("pending:", [(r["id"], r["payload_sha256"][:8]) for r in rows])
print("resolve:", b.resolve_hash(REG_Y, rows))
d = b.parse_owner_text(text)
print("decision:", d.get("verdict"), d.get("reason"))
