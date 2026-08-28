"""Behavioral contract for the metadata-only owner approval projection."""

from __future__ import annotations

import json
import os
import urllib.request
import unittest
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace

from tests.tmpdir import temp_dir

from ofn.adapters.cockpit_v2_read_model import CockpitV2ReadModel
from ofn.node import Node
from ofn.run import _cockpit_v2_reader


NOW = datetime(2026, 8, 29, 0, 0, tzinfo=timezone.utc)


# region agent log
def _agent_log(hypothesis_id: str, message: str, data: dict) -> None:
    payload = {
        "sessionId": "bbea48",
        "runId": os.environ.get("OCTOPUS_DEBUG_RUN_ID", "p1-owner-queue"),
        "hypothesisId": hypothesis_id,
        "location": "tests/test_cockpit_v2_owner_queue.py",
        "message": message,
        "data": data,
        "timestamp": int(NOW.timestamp() * 1000),
    }
    log_path = os.environ.get("OCTOPUS_DEBUG_LOG")
    if log_path:
        with open(log_path, "a", encoding="utf-8") as stream:
            stream.write(json.dumps(payload, sort_keys=True) + "\n")
    endpoint = os.environ.get("OCTOPUS_DEBUG_ENDPOINT")
    if not endpoint:
        return
    request = urllib.request.Request(
        endpoint,
        data=json.dumps(payload, sort_keys=True).encode("utf-8"),
        method="POST",
        headers={
            "Content-Type": "application/json",
            "X-Debug-Session-Id": "bbea48",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=2):
            pass
    except Exception:
        pass
# endregion agent log


def make_root(case: unittest.TestCase) -> Path:
    root = Path(temp_dir(case))
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
    return root


def make_model(root: Path, callbacks=None) -> CockpitV2ReadModel:
    return CockpitV2ReadModel(
        clock=lambda: NOW,
        mesh_root=root,
        ofn_callbacks=callbacks or {},
        version_metadata={"ofn": "test"},
    )


def seed_mesh(root: Path) -> None:
    (root / "inbox" / "mesh.json").write_text(
        json.dumps(
            {
                "message_id": "mesh-message-1",
                "run_id": "mesh-run-1",
                "message_type": "task",
                "sender_node": "180",
                "recipient_node": "138",
                "created_at": "2026-08-28T23:00:00Z",
            }
        ),
        encoding="utf-8",
    )


def owner_source_rows() -> list[dict]:
    return [
        {
            "id": "lead:idem-1",
            "tenant": "lead",
            "kind": "lead:reply",
            "tier": "yellow",
            "payload": {
                "text": "PRIVATE CUSTOMER MESSAGE",
                "phone": "0400000000",
                "email": "private@example.invalid",
            },
            "customer_name": "PRIVATE CUSTOMER",
            "source_ref": "PRIVATE SOURCE",
            "token": "PRIVATE TOKEN",
            "created_at": "2026-08-28T23:01:00Z",
            "needs_double_confirm": False,
        }
    ]


class _OwnerQueueFixture:
    def __init__(self, rows=None):
        self.rows = list(rows if rows is not None else owner_source_rows())

    def owner_queue(self):
        return list(self.rows)


class TestNodeOwnerQueueMetadata(unittest.TestCase):
    def test_metadata_is_derived_from_real_owner_queue_contract(self):
        rows = Node.owner_queue_metadata(_OwnerQueueFixture())
        self.assertEqual(
            rows,
            [
                {
                    "native_id": "lead:idem-1",
                    "idempotency_key": "idem-1",
                    "tenant": "lead",
                    "state": "pending_owner",
                    "risk": "yellow",
                    "created_at": "2026-08-28T23:01:00Z",
                }
            ],
        )
        # region agent log
        _agent_log(
            "H3",
            "node metadata allowlist",
            {"count": len(rows), "keys": sorted(rows[0])},
        )
        # endregion agent log

    def test_held_state_uses_existing_held_marker(self):
        source = owner_source_rows()[0]
        source["held"] = True
        rows = Node.owner_queue_metadata(_OwnerQueueFixture([source]))
        self.assertEqual(rows[0]["state"], "held")


class TestCockpitV2OwnerQueue(unittest.TestCase):
    def metadata(self):
        return Node.owner_queue_metadata(_OwnerQueueFixture())

    def test_owner_queue_callback_is_exposed_additively(self):
        root = make_root(self)
        envelope = make_model(
            root,
            {"owner_queue_metadata": self.metadata},
        ).read("queue", {})
        # region agent log
        _agent_log(
            "H1",
            "owner group projection",
            {
                "data_keys": sorted(envelope["data"]),
                "status": envelope["status"],
            },
        )
        # endregion agent log
        business = envelope["data"]["owner_items"]
        self.assertEqual(len(business), 1)
        self.assertEqual(business[0]["id"], "business:lead:idem-1")
        self.assertEqual(business[0]["native_id"], "lead:idem-1")
        self.assertEqual(business[0]["idempotency_key"], "idem-1")
        self.assertEqual(business[0]["source_kind"], "business_outbox")

    def test_mesh_items_are_unchanged_when_owner_callback_is_added(self):
        root = make_root(self)
        seed_mesh(root)
        before = make_model(root).read("queue", {})["data"]["items"]
        after = make_model(
            root,
            {"owner_queue_metadata": self.metadata},
        ).read("queue", {})["data"]["items"]
        # region agent log
        _agent_log(
            "H2",
            "mesh projection compatibility",
            {"unchanged": before == after, "mesh_count": len(after)},
        )
        # endregion agent log
        self.assertEqual(after, before)
        self.assertEqual(after[0]["id"], "mesh-message-1")

    def test_missing_callback_is_unknown_and_degraded_not_empty(self):
        envelope = make_model(make_root(self)).read("queue", {})
        self.assertIsNone(envelope["data"]["owner_items"])
        self.assertEqual(envelope["status"], "degraded")
        self.assertIn("ofn_owner_queue_metadata_missing", envelope["warnings"])

    def test_callback_exception_does_not_crash(self):
        def broken():
            raise RuntimeError("sensitive internal detail")

        envelope = make_model(
            make_root(self),
            {"owner_queue_metadata": broken},
        ).read("queue", {})
        self.assertIsNone(envelope["data"]["owner_items"])
        self.assertEqual(envelope["status"], "degraded")
        self.assertIn("ofn_owner_queue_metadata_failed", envelope["warnings"])
        self.assertNotIn("sensitive internal detail", json.dumps(envelope))

    def test_payload_and_pii_are_not_serialized(self):
        envelope = make_model(
            make_root(self),
            {"owner_queue_metadata": self.metadata},
        ).read("queue", {})
        rendered = json.dumps(envelope, sort_keys=True)
        for forbidden in (
            "payload",
            "PRIVATE CUSTOMER MESSAGE",
            "0400000000",
            "private@example.invalid",
            "customer_name",
            "source_ref",
            "PRIVATE TOKEN",
        ):
            self.assertNotIn(forbidden, rendered)

    def test_duplicate_native_id_is_one_row_and_degraded(self):
        rows = self.metadata()
        conflicting = dict(rows[0], state="held")
        envelope = make_model(
            make_root(self),
            {"owner_queue_metadata": lambda: [rows[0], conflicting]},
        ).read("queue", {})
        self.assertEqual(len(envelope["data"]["owner_items"]), 1)
        self.assertEqual(envelope["status"], "degraded")
        self.assertIn("ofn_owner_queue_metadata_malformed", envelope["warnings"])

    def test_read_does_not_mutate_mesh_tree(self):
        root = make_root(self)
        seed_mesh(root)

        def snapshot():
            return {
                path.relative_to(root).as_posix(): (
                    path.stat().st_mtime_ns,
                    path.read_bytes(),
                )
                for path in root.rglob("*")
                if path.is_file()
            }

        before = snapshot()
        make_model(
            root,
            {"owner_queue_metadata": self.metadata},
        ).read("queue", {})
        self.assertEqual(snapshot(), before)

    def test_idempotency_key_parity_survives_projection(self):
        metadata = self.metadata()
        envelope = make_model(
            make_root(self),
            {"owner_queue_metadata": lambda: metadata},
        ).read("queue", {})
        self.assertEqual(
            envelope["data"]["owner_items"][0]["idempotency_key"],
            metadata[0]["idempotency_key"],
        )


class TestProductionReaderOwnerQueueWiring(unittest.TestCase):
    def test_run_reader_injects_metadata_callback(self):
        root = make_root(self)
        previous = os.environ.get("OCTOPUS_MESH_ROOT")
        os.environ["OCTOPUS_MESH_ROOT"] = str(root)
        node = SimpleNamespace(
            owner_status=lambda: {},
            owner_observability=lambda: {},
            owner_metrics=lambda: {},
            owner_businesses=lambda: {},
            owner_risks=lambda: {},
            owner_ledger_summary=lambda: {},
            owner_queue_metadata=lambda: [
                {
                    "native_id": "lead:idem-1",
                    "idempotency_key": "idem-1",
                    "tenant": "lead",
                    "state": "pending_owner",
                    "risk": "yellow",
                    "created_at": "2026-08-28T23:01:00Z",
                }
            ],
        )
        try:
            reader = _cockpit_v2_reader(node)
        finally:
            if previous is None:
                os.environ.pop("OCTOPUS_MESH_ROOT", None)
            else:
                os.environ["OCTOPUS_MESH_ROOT"] = previous
        envelope, metadata = reader("queue", {})
        self.assertEqual(
            envelope["data"]["owner_items"][0]["idempotency_key"],
            "idem-1",
        )
        self.assertTrue(metadata["validator"].startswith('W/"'))


if __name__ == "__main__":
    unittest.main()
