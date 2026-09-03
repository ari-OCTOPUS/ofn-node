"""Read-model contract for Cockpit V2 M1.

Covers the seams the business-truth suite does not: query validation,
bounded pagination/cursors, tolerant handling of missing/corrupt/stale
sources, freshness truth states, and deterministic semantic ETags.
"""

from __future__ import annotations

import json
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from tests.tmpdir import temp_dir

from ofn.adapters.cockpit_v2_read_model import (
    UNKNOWN,
    BadQuery,
    CockpitV2ReadModel,
    semantic_etag,
)

NOW = datetime(2026, 8, 27, 12, 0, tzinfo=timezone.utc)
RESOURCES = ("status", "nodes", "legs", "queue", "audit", "version")


def make_root(case: unittest.TestCase) -> Path:
    # Owned by the requesting case; a leaked root under the repo's /tmp
    # tmpfs is exactly the failure mode tests.tmpdir exists for.
    root = Path(temp_dir(case))
    for name in (
        "config", "state", "state/incidents", "inbox", "outbox", "processing",
        "processed", "rejected", "receipts", "audit", "calibration",
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


def envelope_ok(envelope: dict) -> None:
    assert set(envelope) == {
        "schema_version", "generated_at", "status", "data",
        "sources", "warnings", "stale_after",
    }
    assert envelope["schema_version"] == "2.0"
    assert envelope["status"] in {"ok", "degraded", "unavailable"}
    assert isinstance(envelope["sources"], list)
    assert isinstance(envelope["warnings"], list)


class TestEnvelopeAndQueries(unittest.TestCase):
    def test_all_resources_share_the_common_envelope(self):
        model = make_model(make_root(self))
        for resource in RESOURCES:
            with self.subTest(resource=resource):
                envelope = model.read(resource, {})
                envelope_ok(envelope)

    def test_unknown_resource_is_rejected(self):
        model = make_model(make_root(self))
        with self.assertRaises(BadQuery):
            model.read("commands", {})

    def test_query_validation_matrix(self):
        model = make_model(make_root(self))
        bad_queries = (
            {"limit": "0"},
            {"limit": "-1"},
            {"limit": "101"},
            {"limit": "abc"},
            {"limit": ""},
            {"limit": True},
            {"unknown_field": "1"},
            {"cursor": "not-a-cursor"},
            {"cursor": "x" * 512},
            {"search": "y" * 300},
        )
        for resource in ("queue", "audit"):
            for query in bad_queries:
                with self.subTest(resource=resource, query=query):
                    with self.assertRaises(BadQuery):
                        model.read(resource, query)

    def test_list_valued_and_aliased_queries_are_accepted(self):
        root = make_root(self)
        model = make_model(root)
        envelope = model.read("audit", {"kind": ["settle"], "q": ["x"], "limit": ["10"]})
        envelope_ok(envelope)
        envelope = model.read("queue", {"status": ["expired"], "type": ["task"]})
        envelope_ok(envelope)


class TestQueueAndAuditProjections(unittest.TestCase):
    def _seed(self, root: Path) -> None:
        meta = {
            "message_id": "m-1",
            "run_id": "r-1",
            "sender_node": "180",
            "recipient_node": "138",
            "sender_role": "quality-brain",
            "message_type": "task",
            "created_at": "2026-08-27T11:00:00Z",
            "expires_at": "2026-08-27T15:00:00Z",
            "correlation_id": "c-1",
            "idempotency_key": "i-1",
        }
        (root / "inbox" / "a.json").write_text(json.dumps(meta))
        (root / "inbox" / "b.tmp").write_text("partial")
        (root / "inbox" / "c.json").write_text("{not json")
        (root / "audit" / "audit.jsonl").write_text("\n".join([
            json.dumps({"seq": 1, "event": "sent", "ts": "2026-08-27T10:00:00Z"}),
            "{corrupt line",
            json.dumps({"seq": 2, "event": "settled", "ts": "2026-08-27T11:00:00Z"}),
        ]))

    def test_queue_is_metadata_only_and_ignores_temp_files(self):
        root = self._seed_root()
        envelope = make_model(root).read("queue", {})
        rows = envelope["data"]["items"]
        self.assertEqual(len(rows), 1)
        row = rows[0]
        self.assertEqual(row["id"], "m-1")
        self.assertNotIn("payload", row)
        self.assertNotIn("evidence", row)
        self.assertNotIn("error", row)
        # The corrupt sibling degraded the endpoint without hiding the row.
        self.assertEqual(envelope["status"], "degraded")

    def _seed_root(self) -> Path:
        root = make_root(self)
        self._seed(root)
        return root

    def test_audit_tolerates_one_corrupt_line(self):
        root = self._seed_root()
        envelope = make_model(root).read("audit", {})
        events = [row["kind"] for row in envelope["data"]["items"]]
        self.assertIn("sent", events)
        self.assertIn("settled", events)
        self.assertEqual(envelope["status"], "degraded")

    def test_pagination_is_bounded_and_cursor_stable(self):
        root = make_root(self)
        lines = []
        for i in range(120):
            lines.append(json.dumps({
                "seq": i + 1, "event": f"e{i}",
                "ts": "2026-08-27T11:00:00Z",
            }))
        (root / "audit" / "audit.jsonl").write_text("\n".join(lines))
        model = make_model(root)
        first = model.read("audit", {"limit": "50"})
        self.assertEqual(len(first["data"]["items"]), 50)
        cursor = first["data"].get("next_cursor")
        self.assertIsNotNone(cursor)
        second = model.read("audit", {"limit": "50", "cursor": cursor})
        ids1 = {row["sequence"] for row in first["data"]["items"]}
        ids2 = {row["sequence"] for row in second["data"]["items"]}
        self.assertFalse(ids1 & ids2)
        # A cursor bound to another filter shape must not be replayable.
        with self.assertRaises(BadQuery):
            model.read("audit", {"limit": "50", "cursor": cursor, "q": "x"})


class TestFreshnessAndTruth(unittest.TestCase):
    def test_missing_mesh_root_degrades_every_resource(self):
        model = make_model(Path(temp_dir(self)) / "absent")
        for resource in RESOURCES:
            with self.subTest(resource=resource):
                envelope = model.read(resource, {})
                envelope_ok(envelope)
                self.assertIn(envelope["status"], {"degraded", "unavailable"})

    def test_stale_observation_is_labelled_stale_not_live(self):
        old = (NOW - timedelta(seconds=400)).strftime("%Y-%m-%dT%H:%M:%SZ")
        model = make_model(make_root(self), callbacks={
            "money": lambda: {
                "verified_cash": {
                    "amount_minor": 100_00,
                    "currency": "AUD",
                    "receipt_verified": True,
                    "observed_at": old,
                },
            },
        })
        envelope = model.read("legs", {})
        cash = {row["id"]: row for row in envelope["data"]["legs"]}["CASH"]
        self.assertEqual(
            cash["metrics"]["verified_cash_minor"]["truth"], "STALE")

    def test_symlink_escape_is_blocked(self):
        root = make_root(self)
        outside = Path(temp_dir(self))
        (outside / "leak.json").write_text("{}")
        try:
            (root / "state" / "leak.json").symlink_to(outside / "leak.json")
        except OSError:
            self.skipTest("symlinks unavailable")
        envelope = make_model(root).read("status", {})
        envelope_ok(envelope)


class TestSemanticEtag(unittest.TestCase):
    def test_etag_is_deterministic_and_ignores_generation_time(self):
        model = make_model(make_root(self))
        one = model.read("queue", {})
        two = dict(one)
        two["generated_at"] = "2030-01-01T00:00:00Z"
        self.assertEqual(
            semantic_etag(one, "queue", {}),
            semantic_etag(two, "queue", {}),
        )

    def test_etag_changes_with_semantic_content_or_query(self):
        model = make_model(make_root(self))
        one = model.read("queue", {})
        two = dict(one)
        two["warnings"] = ["different"]
        self.assertNotEqual(
            semantic_etag(one, "queue", {}),
            semantic_etag(two, "queue", {}),
        )
        self.assertNotEqual(
            semantic_etag(one, "queue", {}),
            semantic_etag(one, "queue", {"limit": 10}),
        )

    def test_reads_do_not_mutate_the_mesh_tree(self):
        root = make_root(self)
        self._seed(root)
        before = {
            p: p.stat().st_mtime_ns
            for p in sorted(root.rglob("*")) if p.is_file()
        }
        model = make_model(root)
        for _ in range(3):
            for resource in RESOURCES:
                model.read(resource, {})
        after = {
            p: p.stat().st_mtime_ns
            for p in sorted(root.rglob("*")) if p.is_file()
        }
        self.assertEqual(before, after)
        self.assertEqual(
            sorted(p.name for p in root.rglob("*") if p.is_file()),
            sorted(before and [p.name for p in before] or []),
        )

    def _seed(self, root: Path) -> None:
        (root / "inbox" / "a.json").write_text(json.dumps({
            "message_id": "m-1", "message_type": "task",
            "created_at": "2026-08-27T11:00:00Z",
        }))
        (root / "audit" / "audit.jsonl").write_text(json.dumps({
            "seq": 1, "event": "sent", "ts": "2026-08-27T10:00:00Z",
        }) + "\n")


class TestSurfaceResource(unittest.TestCase):
    """The seven-card surface: fail-closed numbers, loud disagreement."""

    SHA_A = "a" * 40
    SHA_B = "b" * 40

    def make_model(self, root: Path, *, repo_root=None, commit=None,
                   owner_queue=None) -> CockpitV2ReadModel:
        callbacks = {}
        if owner_queue is not None:
            callbacks["owner_queue_metadata"] = lambda: owner_queue
        return CockpitV2ReadModel(
            clock=lambda: NOW,
            mesh_root=root,
            ofn_callbacks=callbacks,
            version_metadata={"ofn": "test", "ofn_commit": commit},
            repo_root=repo_root,
        )

    def seed_repo(self, root: Path, *, code_sha: str, self_model: object,
                  receipt_line: str = "") -> None:
        artifact = root / "state" / "self-model"
        artifact.mkdir(parents=True, exist_ok=True)
        (artifact / "SYSTEM-SELF-MODEL.json").write_text(
            json.dumps(self_model), encoding="utf-8")
        doctor = root / "09-LANES" / "LB" / "runs" / "2026-09-02-final"
        doctor.mkdir(parents=True, exist_ok=True)
        (doctor / "receipt.jsonl").write_text(receipt_line, encoding="utf-8")
        econ = root / "09-LANES" / "ECONOMIC-LEARNING" / "runs" / "2026-09-02"
        econ.mkdir(parents=True, exist_ok=True)
        (econ / "run-summary.json").write_text(json.dumps({
            "generated_at": "2026-09-02T10:42:12Z",
            "code_sha": code_sha,
            "campaign_id": "PAINT-L5-001",
            "verified_payments": 0,
            "unverified_payment_claims": 1,
            "chains_total": 5,
            "chains_complete": 0,
        }), encoding="utf-8")

    @staticmethod
    def ok_self_model(sha: str) -> dict:
        return {
            "schema": "octopus.self-model.v2",
            "status": "ok",
            "data": {"code_identity": {"commit_sha": sha}},
        }

    def test_surface_shares_the_common_envelope_and_takes_no_query(self):
        model = self.make_model(make_root(self))
        envelope = model.read("surface", {})
        envelope_ok(envelope)
        with self.assertRaises(BadQuery):
            model.read("surface", {"limit": "5"})

    def test_present_agreeing_sources_are_consistent(self):
        repo = Path(temp_dir(self))
        self.seed_repo(
            repo, code_sha=self.SHA_A, self_model=self.ok_self_model(self.SHA_A),
            receipt_line=json.dumps({
                "kind": "round_start", "ts": "2026-09-02T09:17:00Z",
                "mode": "read-only-dry-run-only"}) + "\n")
        root = make_root(self)
        (root / "config" / "telegram_policy.json").write_text(
            json.dumps({"mode": "owner_reads"}), encoding="utf-8")
        model = self.make_model(
            root, repo_root=repo, commit=self.SHA_A,
            owner_queue=[{
                "native_id": "t1:k1", "tenant": "t1", "idempotency_key": "k1",
                "state": "pending", "risk": "low",
                "created_at": "2026-09-01T00:00:00Z"}])
        envelope = model.read("surface", {})
        self.assertEqual(envelope["status"], "ok")
        self.assertEqual(envelope["warnings"], [])
        coherence = envelope["data"]["coherence"]
        self.assertEqual(coherence["verdict"], "consistent")
        self.assertEqual(coherence["disagreements"], [])
        self.assertEqual(
            [number["id"] for number in coherence["numbers"]],
            ["main_sha", "self_model_sha", "doctor_run_id",
             "verified_payments", "owner_queue_count"],
        )
        self.assertTrue(all(
            number["truth"] != UNKNOWN for number in coherence["numbers"]))
        cards = envelope["data"]["cards"]
        self.assertEqual(sorted(cards), sorted([
            "command_center", "self_model", "doctor", "economic_learning",
            "owner_queue", "telegram_bridge", "receipts_sync"]))
        self.assertEqual(cards["owner_queue"]["count"], 1)
        self.assertEqual(cards["doctor"]["run_id"], "2026-09-02-final")
        # verified_payments is 0 — a known zero, not an unknown.
        self.assertEqual(cards["economic_learning"]["verified_payments"], 0)

    def test_absent_sources_stay_unknown_and_never_green(self):
        model = self.make_model(make_root(self))
        envelope = model.read("surface", {})
        self.assertNotEqual(envelope["status"], "ok")
        coherence = envelope["data"]["coherence"]
        self.assertNotEqual(coherence["verdict"], "consistent")
        self.assertNotEqual(coherence["verdict"], "inconsistent")
        for number in coherence["numbers"]:
            self.assertIsNone(number["value"])
            self.assertEqual(number["truth"], UNKNOWN)
        statuses = envelope["data"]["card_status"]
        self.assertEqual(statuses["self_model"], "unavailable")
        self.assertEqual(statuses["doctor"], "unavailable")
        self.assertEqual(statuses["economic_learning"], "unavailable")

    def test_disagreeing_identities_are_loud_inconsistent(self):
        repo = Path(temp_dir(self))
        self.seed_repo(
            repo, code_sha=self.SHA_B, self_model=self.ok_self_model(self.SHA_A))
        model = self.make_model(
            make_root(self), repo_root=repo, commit=self.SHA_A)
        envelope = model.read("surface", {})
        self.assertEqual(envelope["status"], "degraded")
        coherence = envelope["data"]["coherence"]
        self.assertEqual(coherence["verdict"], "inconsistent")
        self.assertIn("coherence_inconsistent", envelope["warnings"])
        pairs = {
            (item["left"], item["right"])
            for item in coherence["disagreements"]
        }
        self.assertIn(("main_sha", "economic_code_sha"), pairs)
        self.assertIn(("self_model_sha", "economic_code_sha"), pairs)

    def test_malformed_repo_files_fail_closed_not_green(self):
        repo = Path(temp_dir(self))
        self.seed_repo(
            repo, code_sha=self.SHA_A,
            self_model="{not json",
            receipt_line=": not json\n")
        econ_summary = (
            repo / "09-LANES" / "ECONOMIC-LEARNING" / "runs"
            / "2026-09-02" / "run-summary.json")
        econ_summary.write_text("{not json", encoding="utf-8")
        model = self.make_model(
            make_root(self), repo_root=repo, commit=self.SHA_A)
        envelope = model.read("surface", {})
        self.assertNotEqual(envelope["status"], "ok")
        coherence = envelope["data"]["coherence"]
        self.assertEqual(coherence["verdict"], "incomplete")
        cards = envelope["data"]["cards"]
        self.assertIsNone(cards["self_model"]["commit_sha"])
        self.assertIsNone(cards["doctor"]["run_id"])
        self.assertIsNone(cards["economic_learning"]["code_sha"])
        self.assertIsNone(cards["economic_learning"]["verified_payments"])


if __name__ == "__main__":
    unittest.main()
