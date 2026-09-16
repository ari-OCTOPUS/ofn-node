from pathlib import Path
from datetime import datetime, timezone, timedelta
import json

AEST = timezone(timedelta(hours=10))
stamp = datetime.now(AEST).strftime("%Y-%m-%dT%H:%M:%S+10:00")
root = Path(r"F:/backup/06-EVIDENCE/OCTOPUS-TECH-ADMISSION-REFRESH-2026-08-23")
root.mkdir(parents=True, exist_ok=True)

# The report body will be written by a companion file if present; write summary decision table now
decisions = {
  "schema": "octopus-tech-admission-refresh/1",
  "stamp_local": stamp,
  "scope": "octopus-unified-chat / owner-chat — Ziman OUT OF SCOPE",
  "source": "owner-pasted research report 2026-08-23",
  "proposed_status": {
    "MCP": "ADOPT as adapter; review Tool Registry for stateless 2026-07-28 headers Mcp-Method/Mcp-Name; no new authority",
    "SSE": "ADOPT (confirm O-E4 GET /api/runs/{run_id}/events)",
    "WebSocket": "DEFER until voice/HITL realtime proven",
    "Qdrant": "DEFER; keep Chroma until real corpus Recall@K/p95 fail",
    "DBOS": "TRIAL for Run Store on existing Postgres vs Temporal",
    "Temporal": "REJECT for now; only if multi-service fan-out proven",
    "OpenTelemetry_GenAI": "TRIAL mapping only onto existing typed events",
    "NATS_JetStream": "DEFER until >1 independent consumers",
    "Kafka": "DEFER",
  },
  "immediate_week": [
    "MCP adapter header compatibility review (no session authority)",
    "SSE O-E4 endpoint + heartbeat/resume tests",
    "Minimal gen_ai.* mapping layer over MODEL_STARTED/FINISHED",
  ],
  "this_month": [
    "DBOS-style Run Store TRIAL with O-T0 criteria",
    "Chroma baseline on real Vault corpus",
    "Equation/Architecture explainers parallel (Q/R)",
  ],
  "later": [
    "NATS only if multi-consumer proven",
    "Align Pi command-trust with sessionless MCP model (already VERIFIED on Pi)",
    "Physical e-stop before any PWM",
  ],
  "hard_rule": "No install without Technology Decision Record (measured problem + existing insufficient + trial threshold + tested rollback)",
}
(root / "DECISIONS.json").write_text(json.dumps(decisions, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
(root / "README.md").write_text(
    f"""# OCTOPUS Tech Admission Refresh — {stamp}

Owner pasted research brief (MCP 2026-07-28 stateless, SSE vs WS, Qdrant/Chroma, Temporal/DBOS, OTel GenAI, NATS/Kafka).
Ziman explicitly out of scope.

See DECISIONS.json for proposed ADOPT/TRIAL/DEFER/REJECT table.
Full prose report: OWNER-REPORT.md (if present).
""",
    encoding="utf-8",
)
print(root)
