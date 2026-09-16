from pathlib import Path
from datetime import datetime, timezone, timedelta
import json
AEST = timezone(timedelta(hours=10))
stamp = datetime.now(AEST).strftime("%Y-%m-%dT%H:%M:%S+10:00")
root = Path(r"F:/backup/06-EVIDENCE/BOARD2-ZIMAN-ETSY-PERSONA-GO-2026-08-24")
root.mkdir(parents=True, exist_ok=True)
rec = {
  "schema": "octopus.etsy-persona-go/1",
  "stamp_local": stamp,
  "owner_go": True,
  "decision": "GO: Maliheh Persona identity verify for Etsy Ziman",
  "legal_name": "Maliheh Khalajijou",
  "executor": "marketing/Board2",
  "constraints": ["no invent listings", "no ID images in chat", "owner/Maliheh completes camera+gov ID"],
}
(root / "GO.json").write_text(json.dumps(rec, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
(root / "SUMMARY.md").write_text(
  f"# Etsy Ziman Persona GO\n\nstamp: {stamp}\nowner GO to marketing for Maliheh Khalajijou Persona verify.\n",
  encoding="utf-8",
)
print(str(root))
