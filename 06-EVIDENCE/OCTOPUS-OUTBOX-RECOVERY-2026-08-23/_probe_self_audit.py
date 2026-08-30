import sys, json, ast
from pathlib import Path
sys.path.insert(0, r"F:\backup\_ops")
sys.path.insert(0, r"F:\backup\_ops\cortex")
sys.path.insert(0, r"F:\backup\_ops\tests")
import harness
ENV = harness.setup("self-audit-outbox-probe")
import self_audit as sa

src = Path(sa.__file__).read_text("utf-8")
tree = ast.parse(src)
probe_names = [n.name for n in tree.body if isinstance(n, ast.FunctionDef) and n.name.startswith("_probe_")]
has_gate = hasattr(sa, "_gate_evidence_bound_done")
has_resolve = hasattr(sa, "_resolve_evidence_json_path")
has_run = hasattr(sa, "run_audit")

items = []
for name in ("_probe_dry_run", "_probe_regression_suite", "_probe_replay", "_probe_rollback"):
    fn = getattr(sa, name, None)
    if fn is None:
        items.append({"probe": name, "status": "MISSING_FN"})
        continue
    try:
        it = fn()
        items.append({
            "probe": name,
            "status": it.get("status"),
            "evidence_bound": bool(it.get("evidence_bound")),
            "evidence_json": it.get("evidence_json"),
            "gap_type": it.get("gap_type"),
            "evidence_snippet": str(it.get("evidence") or "")[:240],
        })
    except Exception as e:
        items.append({"probe": name, "status": "ERROR", "error": type(e).__name__ + ": " + str(e)[:200]})

fake = sa._item("probe-fake", "Done", "none", "P1", None, "test",
                evidence_bound=True, evidence_json=r"F:\backup\06-EVIDENCE\__missing_no_such__.json")
gate_ok = fake.get("status") != "Done"

out = {
  "probe_count": len(probe_names),
  "has_gate_evidence_bound_done": has_gate,
  "has_resolve_evidence_json_path": has_resolve,
  "has_run_audit": has_run,
  "gate_fail_closed_on_missing_json": gate_ok,
  "gate_status_when_missing": fake.get("status"),
  "sample_probes": items,
}
Path(r"F:\backup\06-EVIDENCE\OCTOPUS-OUTBOX-RECOVERY-2026-08-23").mkdir(parents=True, exist_ok=True)
Path(r"F:\backup\06-EVIDENCE\OCTOPUS-OUTBOX-RECOVERY-2026-08-23\self_audit_probe.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
print(json.dumps(out, indent=2))
