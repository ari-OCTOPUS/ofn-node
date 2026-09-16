from pathlib import Path
from datetime import datetime, timezone, timedelta
import json
AEST = timezone(timedelta(hours=10))
stamp = datetime.now(AEST).strftime("%Y-%m-%dT%H:%M:%S+10:00")
root = Path(r"F:/backup/06-EVIDENCE/OCTOPUS-CG001-GA4-OAUTH-START-2026-08-23")
root.mkdir(parents=True, exist_ok=True)
mp = {
  "schema": "octopus.cg001.property-map/1",
  "status": "OWNER_SIGNED_OFF",
  "stamp_local": stamp,
  "signed_off_by": "owner",
  "rule": "each business has its own pages",
  "oauth_account": "arminooal4@gmail.com",
  "vault": {
    "oauth_client": r"F:\backup\_ops\secrets\google-ga4\oauth-client.json",
    "token": r"F:\backup\_ops\secrets\google-ga4\token.json",
    "scope": "analytics.readonly",
  },
  "businesses": {
    "master-painting": {
      "ga4_property_id": "358651346",
      "ga4_property_resource": "properties/358651346",
      "ga4_measurement_id": "G-53PXCTFQ8M",
      "property_name": "www.masterpainting.sydney",
      "signed_off": True,
    },
    "ziman": {
      "ga4_property_id": "551101646",
      "ga4_property_resource": "properties/551101646",
      "property_name": "Ziman Gift",
      "signed_off": True,
    },
    "studio": {
      "ga4_property_id": None,
      "signed_off": False,
      "status": "HOLD_NO_PROPERTY",
    },
  },
  "metrics_allowed": False,
  "cg001": "CLOSED_WITH_STUDIO_HOLD",
}
(root / "PROPERTY-MAP.json").write_text(json.dumps(mp, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
(root / "OWNER-SIGNOFF.json").write_text(json.dumps({
  "stamp_local": stamp,
  "decision": "Sign off GA4 property map and close CG-001",
  "studio": "HOLD",
}, indent=2) + "\n", encoding="utf-8")
(root / "STATUS.json").write_text(json.dumps({
  "stamp_local": stamp,
  "status": "CLOSED_WITH_HOLDS",
  "cg001": "CLOSED",
  "studio_hold": True,
  "metrics_allowed": False,
  "token_vaulted": True,
}, indent=2) + "\n", encoding="utf-8")
regp = Path(r"F:/backup/06-EVIDENCE/OCTOPUS-LAPTOP-CONCEPTS-TO-CODE-2026-08-23/CONNECTOR-GAP-REGISTRY.json")
reg = json.loads(regp.read_text(encoding="utf-8"))
for g in reg.get("gaps", []):
  if g.get("gap_id") == "CG-001":
    g["status"] = "CLOSED"
    g["closed_at_local"] = stamp
    g["oauth_consent"] = "DONE_READONLY"
    g["metrics_allowed"] = False
    g["property_map_signed_off"] = True
    g["holds"] = ["studio GA4 property absent"]
    g["evidence"] = r"F:\backup\06-EVIDENCE\OCTOPUS-CG001-GA4-OAUTH-START-2026-08-23\\"
reg["as_of"] = stamp
regp.write_text(json.dumps(reg, indent=2) + "\n", encoding="utf-8")
rec = Path(r"F:/backup/06-EVIDENCE/OCTOPUS-UNDISCOVERED-2026-08-23/RECONCILE.md")
extra = (
  "\n\n## CG-001 GA4 (" + stamp + ")\n"
  "- Status: **CLOSED** (studio property HOLD)\n"
  "- OAuth readonly + vault token OK\n"
  "- Map: painting 358651346 / Ziman 551101646 / studio absent\n"
  "- metrics_allowed=false\n"
)
if rec.exists():
  t = rec.read_text(encoding="utf-8")
  if "CG-001 GA4" not in t:
    rec.write_text(t.rstrip() + extra, encoding="utf-8")
print("CG001_CLOSED")
