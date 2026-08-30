import json
from pathlib import Path
from jsonschema import Draft202012Validator

root = Path(r"F:\backup\06-EVIDENCE\OCTOPUS-LAPTOP-CONCEPTS-TO-CODE-2026-08-23")
brief = Path(r"F:\backup\06-EVIDENCE\OCTOPUS-LAPTOP-AGENT-OWNER-BRIEF-2026-08-22")
packs = {
  "BUSINESS": ("NODE-PACK-BUSINESS.json", "NODE-PACK-BUSINESS.schema.json"),
  "SENSORIUM": ("NODE-PACK-SENSORIUM.json", "NODE-PACK-SENSORIUM.schema.json"),
  "LAPTOP": ("NODE-PACK-LAPTOP.json", "NODE-PACK-LAPTOP.schema.json"),
}
results = {}
for role, (pj, sj) in packs.items():
    pack = json.loads((root / "node-packs" / pj).read_text(encoding="utf-8"))
    schema = json.loads((brief / sj).read_text(encoding="utf-8"))
    local = json.loads((root / "schemas" / sj).read_text(encoding="utf-8"))
    v = Draft202012Validator(schema)
    errs = sorted(v.iter_errors(pack), key=lambda e: list(e.path))
    results[role] = {
        "ok": len(errs) == 0,
        "error_count": len(errs),
        "errors": [f"{'/'.join(map(str,e.path))}: {e.message}" for e in errs[:30]],
        "schema_matches_local_copy": schema == local,
        "node_role": pack.get("node_role"),
        "can_synthesize": pack.get("synthesis_lock", {}).get("can_synthesize"),
        "claims": len(pack.get("claims", [])),
        "contradictions": len(pack.get("contradictions", [])),
    }
print(json.dumps(results, indent=2))
