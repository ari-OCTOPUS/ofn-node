import hashlib
import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from ofn.adapters.cockpit_v2_read_model import CockpitV2ReadModel
from ofn.node import Node


EVIDENCE = Path(
    "/home/ari/ofn/06-EVIDENCE/runtime-provenance-20260828T230743Z"
)


class ShadowNode:
    def owner_queue(self):
        return [
            {
                "id": "lead:shadow-idem-1",
                "tenant": "lead",
                "kind": "lead:reply",
                "tier": "yellow",
                "payload": {
                    "text": "SHOULD_NOT_APPEAR",
                    "phone": "0400000000",
                },
                "created_at": "2026-08-28T23:10:00Z",
                "needs_double_confirm": False,
            }
        ]


with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)
    for name in (
        "config",
        "state",
        "state/incidents",
        "inbox",
        "outbox",
        "processing",
        "processed",
        "rejected",
        "receipts",
        "audit",
        "calibration",
    ):
        (root / name).mkdir(parents=True, exist_ok=True)
    (root / "inbox" / "mesh.json").write_text(
        json.dumps(
            {
                "message_id": "mesh-shadow-1",
                "run_id": "mesh-shadow-run",
                "message_type": "task",
                "sender_node": "180",
                "recipient_node": "138",
                "created_at": "2026-08-28T23:09:00Z",
            }
        ),
        encoding="utf-8",
    )

    owner_metadata = Node.owner_queue_metadata(ShadowNode())
    model = CockpitV2ReadModel(
        clock=lambda: datetime(2026, 8, 29, tzinfo=timezone.utc),
        mesh_root=root,
        ofn_callbacks={
            "owner_queue_metadata": lambda: owner_metadata,
        },
        version_metadata={"ofn": "shadow"},
    )
    envelope = model.read("queue", {})

rendered = json.dumps(
    envelope, ensure_ascii=False, sort_keys=True, indent=2
)
assert "SHOULD_NOT_APPEAR" not in rendered
assert "0400000000" not in rendered
assert envelope["data"]["items"][0]["id"] == "mesh-shadow-1"
assert envelope["data"]["owner_items"][0]["id"] == (
    "business:lead:shadow-idem-1"
)
assert envelope["data"]["owner_items"][0]["idempotency_key"] == (
    owner_metadata[0]["idempotency_key"]
)

response_path = EVIDENCE / "p1-shadow-v2-response.json"
response_path.write_text(rendered + "\n", encoding="utf-8")
response_sha = hashlib.sha256(response_path.read_bytes()).hexdigest()
report = {
    "mode": "shadow_fixture",
    "mesh_items_unchanged": True,
    "mesh_native_id": envelope["data"]["items"][0]["id"],
    "owner_items_visible": True,
    "business_id": envelope["data"]["owner_items"][0]["id"],
    "idempotency_parity": True,
    "pii_leaks": 0,
    "response_sha256": response_sha,
}
(EVIDENCE / "p1-parity-report.json").write_text(
    json.dumps(report, sort_keys=True, indent=2) + "\n",
    encoding="utf-8",
)

# region agent log
debug_path = os.environ.get("OCTOPUS_DEBUG_LOG")
if debug_path:
    payload = {
        "sessionId": "bbea48",
        "runId": "p1-shadow",
        "hypothesisId": "H5",
        "location": "p1-shadow-response.py",
        "message": "shadow V2 parity",
        "data": report,
        "timestamp": 1787961600000,
    }
    with open(debug_path, "a", encoding="utf-8") as stream:
        stream.write(json.dumps(payload, sort_keys=True) + "\n")
# endregion agent log

print(json.dumps(report, sort_keys=True))
