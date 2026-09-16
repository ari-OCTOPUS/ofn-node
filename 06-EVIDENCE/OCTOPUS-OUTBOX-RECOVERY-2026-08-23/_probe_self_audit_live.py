import sys, json, os
from pathlib import Path
ops = Path(r"F:\backup\_ops")
sys.path.insert(0, str(ops))
sys.path.insert(0, str(ops / "cortex"))
# Do NOT use harness.setup temp isolation — probe live paths
os.environ.pop("OCTOPUS_ROOT", None)
import self_audit as sa

items = []
for name in ("_probe_dry_run", "_probe_regression_suite", "_probe_replay", "_probe_rollback", "_probe_secrets_isolation"):
    fn = getattr(sa, name)
    it = fn()
    items.append({
        "probe": name,
        "status": it.get("status"),
        "evidence_bound": bool(it.get("evidence_bound")),
        "evidence_json": it.get("evidence_json"),
        "gap_type": it.get("gap_type"),
        "priority": it.get("priority"),
        "evidence_snippet": str(it.get("evidence") or "")[:280],
    })

fake = sa._item("probe-fake", "Done", "none", "P1", None, "test",
                evidence_bound=True, evidence_json=r"F:\backup\06-EVIDENCE\__missing_no_such__.json")

# Does run_audit exist and accept a limited path?
run_sig = "callable" if callable(getattr(sa, "run_audit", None)) else "missing"

out = {
  "mode": "live_ops_paths",
  "self_audit_file": str(Path(sa.__file__)),
  "run_audit": run_sig,
  "gate_fail_closed_on_missing_json": fake.get("status") != "Done",
  "gate_status_when_missing": fake.get("status"),
  "sample_probes": items,
}
print(json.dumps(out, indent=2))
Path(r"F:\backup\06-EVIDENCE\OCTOPUS-OUTBOX-RECOVERY-2026-08-23\self_audit_live.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
