"""Contract tests for the signed, durable three-board event adapter."""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import sqlite3
import tempfile
import unittest

from ofn.adapters.board_events import (
    ACKED,
    BOARD_EVENT_VERSION,
    BOARDS,
    EVENT_TYPES,
    HELD,
    MAX_ATTEMPTS,
    MAX_EVENT_ID_LENGTH,
    MAX_PAYLOAD_BYTES,
    MAX_PAYLOAD_DEPTH,
    PROCESSED,
    RECEIVED,
    REJECTED,
    BoardEvent,
    BoardEventSignatureError,
    BoardEventStore,
    BoardEventValidationError,
    ENVELOPE_FIELDS,
)


SECRET = "three-board-test-secret"
NOW = "2026-08-26T12:00:00Z"
LATER = "2099-01-01T01:00:00Z"
MUCH_LATER = "2099-01-02T00:00:00Z"


def envelope(**changes):
    base = {
        "event_id": "evt-001",
        "run_id": "run-001",
        "source": "board-182",
        "target": "board-138",
        "type": "LEAD_DISCOVERED",
        "lead_id": "lead-001",
        "payload": {"score": 0.9, "name": "سارا"},
        "created_at": "2099-01-01T00:00:00Z",
        "expires_at": LATER,
        "attempt": 1,
    }
    base.update(changes)
    return base


def event(**changes):
    return BoardEvent.from_mapping(envelope(**changes))


class BoardEventContractTests(unittest.TestCase):
    def test_version_and_exact_envelope_surface(self):
        item = event()
        self.assertEqual(BOARD_EVENT_VERSION, 1)
        self.assertEqual(item.VERSION, 1)
        self.assertEqual(tuple(item.as_dict()), ENVELOPE_FIELDS)
        self.assertNotIn("signature", item.as_dict())
        self.assertNotIn("version", item.as_dict())

    def test_roundtrip_makes_defensive_payload_copies(self):
        raw = envelope(payload={"nested": [1, {"ok": True}]})
        item = BoardEvent.from_mapping(raw)
        raw["payload"]["nested"][1]["ok"] = False
        self.assertTrue(item.payload["nested"][1]["ok"])
        projected = item.as_dict()
        projected["payload"]["nested"][1]["ok"] = False
        self.assertTrue(item.payload["nested"][1]["ok"])

    def test_missing_and_extra_fields_are_rejected(self):
        for name in ENVELOPE_FIELDS:
            raw = envelope()
            del raw[name]
            with self.subTest(missing=name), self.assertRaises(
                BoardEventValidationError
            ):
                BoardEvent.from_mapping(raw)
        with self.assertRaises(BoardEventValidationError):
            BoardEvent.from_mapping({**envelope(), "signature": "not-in-envelope"})
        with self.assertRaises(BoardEventValidationError):
            BoardEvent.from_mapping({**envelope(), "version": 1})

    def test_ids_must_be_nonempty_bounded_clean_strings(self):
        invalid = ("", "   ", " leading", "trailing ", "bad\nvalue", 1, None)
        for field in ("event_id", "run_id"):
            for value in invalid:
                with self.subTest(field=field, value=value), self.assertRaises(
                    BoardEventValidationError
                ):
                    event(**{field: value})
        with self.assertRaises(BoardEventValidationError):
            event(event_id="x" * (MAX_EVENT_ID_LENGTH + 1))

    def test_only_three_distinct_boards_are_allowed(self):
        self.assertEqual(BOARDS, {"board-138", "board-180", "board-182"})
        for source in BOARDS:
            for target in BOARDS - {source}:
                with self.subTest(source=source, target=target):
                    self.assertEqual(event(source=source, target=target).target, target)
        for field in ("source", "target"):
            with self.subTest(field=field), self.assertRaises(
                BoardEventValidationError
            ):
                event(**{field: "board-999"})
        with self.assertRaises(BoardEventValidationError):
            event(source="board-138", target="board-138")

    def test_type_allowlist_and_business_lead_requirement(self):
        self.assertEqual(
            EVENT_TYPES,
            {
                "LEAD_DISCOVERED",
                "MESSAGE_DRAFT_REQUESTED",
                "MESSAGE_DRAFT_READY",
                "ACK",
                "ERROR",
            },
        )
        for kind in EVENT_TYPES:
            lead_id = None if kind in {"ACK", "ERROR"} else "lead-1"
            with self.subTest(kind=kind):
                self.assertEqual(event(type=kind, lead_id=lead_id).type, kind)
        with self.assertRaises(BoardEventValidationError):
            event(type="UNKNOWN")
        for kind in (
            "LEAD_DISCOVERED",
            "MESSAGE_DRAFT_REQUESTED",
            "MESSAGE_DRAFT_READY",
        ):
            for lead_id in (None, "", "  "):
                with self.subTest(kind=kind, lead_id=lead_id), self.assertRaises(
                    BoardEventValidationError
                ):
                    event(type=kind, lead_id=lead_id)

    def test_payload_must_be_bounded_json_object(self):
        for invalid in ([], "text", 2, None):
            with self.subTest(invalid=invalid), self.assertRaises(
                BoardEventValidationError
            ):
                event(payload=invalid)
        for invalid in (
            {1: "non-string-key"},
            {"tuple": (1, 2)},
            {"set": {1}},
            {"nan": float("nan")},
            {"infinity": float("inf")},
        ):
            with self.subTest(invalid=repr(invalid)), self.assertRaises(
                BoardEventValidationError
            ):
                event(payload=invalid)

        exact_text = "x" * (MAX_PAYLOAD_BYTES - len('{"v":""}'.encode("utf-8")))
        self.assertEqual(
            len(json.dumps({"v": exact_text}, separators=(",", ":")).encode()),
            MAX_PAYLOAD_BYTES,
        )
        self.assertEqual(event(payload={"v": exact_text}).payload["v"], exact_text)
        with self.assertRaises(BoardEventValidationError):
            event(payload={"v": exact_text + "x"})

    def test_payload_nesting_is_bounded(self):
        value = "leaf"
        for _ in range(MAX_PAYLOAD_DEPTH + 1):
            value = [value]
        with self.assertRaises(BoardEventValidationError):
            event(payload={"value": value})

    def test_timestamps_are_strict_rfc3339_utc(self):
        valid = (
            "2026-08-26T12:00:00Z",
            "2026-08-26T12:00:00.1Z",
            "2026-08-26T12:00:00.123456789Z",
            "2026-08-26T12:00:00+00:00",
        )
        for created in valid:
            with self.subTest(created=created):
                self.assertEqual(
                    event(created_at=created, expires_at="2099-01-01T00:00:00Z").created_at,
                    created,
                )
        invalid = (
            "",
            "2026-08-26 12:00:00Z",
            "2026-08-26T12:00:00",
            "2026-08-26T12:00:00+01:00",
            "2026-02-30T12:00:00Z",
            "2026-08-26T24:00:00Z",
            "2026-08-26T12:00:60Z",
            "2026-08-26t12:00:00z",
        )
        for value in invalid:
            with self.subTest(value=value), self.assertRaises(
                BoardEventValidationError
            ):
                event(created_at=value)

    def test_expiry_must_follow_creation_and_boundary_is_expired(self):
        with self.assertRaises(BoardEventValidationError):
            event(
                created_at="2026-08-26T12:00:00Z",
                expires_at="2026-08-26T12:00:00.000000000Z",
            )
        with self.assertRaises(BoardEventValidationError):
            event(
                created_at="2026-08-26T12:00:01Z",
                expires_at="2026-08-26T12:00:00Z",
            )
        BoardEvent.from_mapping(envelope(), now="2099-01-01T00:59:59.999999999Z")
        with self.assertRaises(BoardEventValidationError):
            BoardEvent.from_mapping(envelope(), now=LATER)
        with self.assertRaises(BoardEventValidationError):
            BoardEvent.from_mapping(envelope(), now="2099-01-01T01:00:01Z")

    def test_attempt_is_real_int_in_bounded_range(self):
        for value in (0, -1, MAX_ATTEMPTS + 1, True, 1.0, "1"):
            with self.subTest(value=value), self.assertRaises(
                BoardEventValidationError
            ):
                event(attempt=value)
        self.assertEqual(event(attempt=MAX_ATTEMPTS).attempt, MAX_ATTEMPTS)
        with self.assertRaises(BoardEventValidationError):
            BoardEvent.from_mapping(envelope(attempt=2), max_attempts=1)

    def test_canonical_json_and_hmac_sha256(self):
        left = event(payload={"z": 1, "a": "سلام"})
        right = event(payload={"a": "سلام", "z": 1})
        self.assertEqual(left.canonical_bytes(), right.canonical_bytes())
        self.assertNotIn(b" ", left.canonical_bytes())
        self.assertIn("سلام".encode(), left.canonical_bytes())
        expected = hmac.new(
            SECRET.encode(), left.canonical_bytes(), hashlib.sha256
        ).hexdigest()
        self.assertEqual(left.sign(SECRET), expected)
        self.assertTrue(left.verify(SECRET, expected))
        self.assertFalse(left.verify(SECRET, "0" * 64))
        self.assertFalse(left.verify(SECRET, expected.upper()))
        for empty in ("", b""):
            with self.assertRaises(BoardEventValidationError):
                left.sign(empty)
            with self.assertRaises(BoardEventValidationError):
                left.verify(empty, expected)

    def test_verify_uses_compare_digest(self):
        import ofn.adapters.board_events as module

        original = module.hmac.compare_digest
        calls = []

        def recording(left, right):
            calls.append((left, right))
            return original(left, right)

        module.hmac.compare_digest = recording
        try:
            item = event()
            signature = item.sign(SECRET)
            self.assertTrue(item.verify(SECRET, signature))
            self.assertFalse(item.verify(SECRET, "wrong"))
        finally:
            module.hmac.compare_digest = original
        self.assertEqual(len(calls), 2)


class BoardEventStoreTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = os.path.join(self.temp.name, "existing.sqlite")
        # Prove the adapter uses the supplied database instead of inventing one.
        conn = sqlite3.connect(self.path)
        conn.execute("CREATE TABLE existing_data (value TEXT)")
        conn.execute("INSERT INTO existing_data VALUES ('keep')")
        conn.commit()
        conn.close()
        self.store = BoardEventStore(self.path, SECRET, now=lambda: NOW)

    def tearDown(self):
        self.store.close()
        self.temp.cleanup()

    def ingest(self, item=None, *, signature=None, now=NOW, **changes):
        item = item or event(**changes)
        signature = item.sign(SECRET) if signature is None else signature
        return self.store.ingest(item, signature, now=now)

    def test_existing_db_preserved_table_created_and_durable_pragmas_applied(self):
        conn = sqlite3.connect(self.path)
        tables = {
            row[0]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
        }
        self.assertIn("existing_data", tables)
        self.assertIn("board_events", tables)
        self.assertEqual(
            conn.execute("SELECT value FROM existing_data").fetchone()[0], "keep"
        )
        self.assertEqual(conn.execute("PRAGMA journal_mode").fetchone()[0], "wal")
        self.assertEqual(self.store._conn.execute("PRAGMA synchronous").fetchone()[0], 2)
        conn.close()
        siblings = set(os.listdir(self.temp.name))
        self.assertFalse(any(name.endswith("board_events.sqlite") for name in siblings))

    def test_ingest_get_and_signature_transport_separation(self):
        item = event(payload={"message": "safe"})
        signature = item.sign(SECRET)
        self.assertTrue(self.store.ingest(item.as_dict(), signature, now=NOW))
        got = self.store.get(item.event_id)
        self.assertIsNotNone(got)
        self.assertEqual(got.as_dict(), item.as_dict())
        self.assertEqual(got.signature, signature)
        self.assertEqual(got.status, RECEIVED)
        self.assertNotIn("signature", got.as_dict())

    def test_wrong_or_missing_hmac_fails_without_writing(self):
        item = event()
        for bad in (None, "", "0" * 64, item.sign("other-secret")):
            with self.subTest(bad=bad), self.assertRaises(BoardEventSignatureError):
                self.store.ingest(item, bad, now=NOW)
            self.assertIsNone(self.store.get(item.event_id))

    def test_store_requires_nonempty_secret_at_init_or_ingest(self):
        for invalid in ("", b""):
            with self.subTest(invalid=invalid), self.assertRaises(
                BoardEventValidationError
            ):
                BoardEventStore(self.path, invalid)
        unsigned = BoardEventStore(self.path, now=lambda: NOW)
        self.addCleanup(unsigned.close)
        item = event(event_id="evt-secret")
        with self.assertRaises(BoardEventValidationError):
            unsigned.ingest(item, item.sign(SECRET))
        self.assertTrue(
            unsigned.ingest(item, item.sign(SECRET), secret=SECRET, now=NOW)
        )
        unsigned.close()   # before tearDown's tmpdir cleanup — Windows cannot
                           # delete the directory while the sqlite handle is open

    def test_replay_same_and_different_valid_envelope_is_idempotent(self):
        first = event(payload={"value": 1})
        self.assertTrue(self.ingest(first))
        self.assertFalse(self.ingest(first))
        different = event(
            event_id=first.event_id,
            run_id="other-run",
            payload={"value": 2},
        )
        self.assertFalse(self.ingest(different))
        stored = self.store.get(first.event_id)
        self.assertEqual(stored.run_id, "run-001")
        self.assertEqual(stored.payload, {"value": 1})
        self.assertEqual(self.store.counts(now=NOW), {RECEIVED: 1})

    def test_bad_signature_replay_still_fails_closed(self):
        item = event()
        self.assertTrue(self.ingest(item))
        with self.assertRaises(BoardEventSignatureError):
            self.store.ingest(item, "0" * 64, now=NOW)
        self.assertEqual(self.store.counts(now=NOW), {RECEIVED: 1})

    def test_expired_ingest_rejected_at_exact_boundary(self):
        item = event()
        with self.assertRaises(BoardEventValidationError):
            self.store.ingest(item, item.sign(SECRET), now=LATER)
        self.assertIsNone(self.store.get(item.event_id))

    def test_ordering_is_created_at_then_event_id(self):
        specs = (
            ("evt-z", "2026-08-26T12:00:01Z"),
            ("evt-b", "2026-08-26T12:00:00.000000000Z"),
            ("evt-a", "2026-08-26T12:00:00+00:00"),
        )
        for event_id, created_at in specs:
            self.ingest(
                event(
                    event_id=event_id,
                    created_at=created_at,
                    expires_at=MUCH_LATER,
                )
            )
        self.assertEqual(
            [item.event_id for item in self.store.pending("board-138", now=NOW)],
            ["evt-a", "evt-b", "evt-z"],
        )
        first = self.store.claim("board-138", now=NOW)
        second = self.store.claim("board-138", now=NOW)
        self.assertEqual((first.event_id, second.event_id), ("evt-a", "evt-b"))

    def test_pending_and_counts_can_be_target_scoped(self):
        self.ingest(event(event_id="to-138", target="board-138"))
        self.ingest(
            event(
                event_id="to-180",
                target="board-180",
                expires_at=LATER,
            )
        )
        self.assertEqual(
            [x.event_id for x in self.store.pending("board-138", now=NOW)],
            ["to-138"],
        )
        self.assertEqual(self.store.counts("board-180", now=NOW), {RECEIVED: 1})
        with self.assertRaises(BoardEventValidationError):
            self.store.pending("board-999", now=NOW)

    def test_claim_is_exclusive_and_mark_processed_requires_claim(self):
        self.ingest()
        self.assertFalse(self.store.mark_processed("evt-001", now=NOW))
        claimed = self.store.claim("board-138", now=NOW)
        self.assertIsNotNone(claimed)
        self.assertEqual(claimed.status, RECEIVED)
        self.assertEqual(claimed.claim_attempts, 1)
        self.assertTrue(claimed.claim_token)
        self.assertIsNone(self.store.claim("board-138", now=NOW))
        self.assertFalse(
            self.store.mark_processed(
                "evt-001", claim_token="wrong-token", now=NOW
            )
        )
        self.assertTrue(
            self.store.mark_processed(
                "evt-001", claim_token=claimed.claim_token, now=NOW
            )
        )
        self.assertEqual(self.store.get("evt-001").status, PROCESSED)
        self.assertFalse(self.store.mark_processed("evt-001", now=NOW))

    def test_limited_status_transitions(self):
        self.ingest()
        self.assertFalse(self.store.ack("evt-001", now=NOW))
        self.assertTrue(self.store.hold("evt-001", "manual check", now=NOW))
        self.assertEqual(self.store.get("evt-001").status, HELD)
        self.assertFalse(self.store.mark_processed("evt-001", now=NOW))
        self.assertFalse(self.store.hold("evt-001", now=NOW))
        self.assertTrue(self.store.reject("evt-001", "declined", now=NOW))
        self.assertEqual(self.store.get("evt-001").status, REJECTED)
        self.assertFalse(self.store.retry("evt-001", now=NOW))
        self.assertFalse(self.store.ack("evt-001", now=NOW))
        self.assertFalse(self.store.reject("evt-001", now=NOW))

    def test_hold_then_retry_within_budget(self):
        self.ingest()
        claimed = self.store.claim(now=NOW)
        self.assertTrue(claimed.claim_token)
        self.assertTrue(self.store.hold("evt-001", "temporary", now=NOW))
        self.assertTrue(self.store.retry("evt-001", now=NOW))
        self.assertEqual(self.store.get("evt-001").status, RECEIVED)
        again = self.store.claim(now=NOW)
        self.assertEqual(again.claim_attempts, 2)

    def test_bounded_retry_respects_signed_attempt(self):
        at_cap = event(event_id="evt-cap", attempt=MAX_ATTEMPTS)
        self.ingest(at_cap)
        claimed = self.store.claim(now=NOW)
        self.assertEqual(claimed.event_id, "evt-cap")
        self.assertTrue(self.store.hold("evt-cap", "failed", now=NOW))
        self.assertFalse(self.store.retry("evt-cap", now=NOW))
        self.assertEqual(self.store.get("evt-cap").status, HELD)

    def test_ack_event_is_persisted_and_can_ack_processed_event(self):
        work = event(event_id="work", type="MESSAGE_DRAFT_READY")
        ack_event = event(
            event_id="ack-1",
            source="board-138",
            target="board-182",
            type="ACK",
            lead_id=None,
            payload={"event_id": "work"},
        )
        self.ingest(work)
        self.ingest(ack_event)
        claim = self.store.claim("board-138", now=NOW)
        self.assertEqual(claim.event_id, "work")
        self.assertTrue(
            self.store.mark_processed(
                "work", claim_token=claim.claim_token, now=NOW
            )
        )
        self.assertFalse(self.store.ack("work", "missing-ack", now=NOW))
        self.assertTrue(self.store.ack("work", "ack-1", now=NOW))
        got = self.store.get("work")
        self.assertEqual(got.status, ACKED)
        self.assertEqual(got.ack_event_id, "ack-1")
        self.assertEqual(self.store.get("ack-1").type, "ACK")
        self.assertFalse(self.store.ack("work", "ack-1", now=NOW))

    def test_ack_without_linked_record_still_terminalises(self):
        work = event(event_id="solo", type="MESSAGE_DRAFT_READY")
        self.ingest(work)
        claim = self.store.claim("board-138", now=NOW)
        self.assertTrue(
            self.store.mark_processed(
                "solo", claim_token=claim.claim_token, now=NOW
            )
        )
        self.assertTrue(self.store.ack("solo", now=NOW))
        got = self.store.get("solo")
        self.assertEqual(got.status, ACKED)
        self.assertIsNone(got.ack_event_id)
        # A non-ACK event id supplied as the link is refused.
        other = event(event_id="not-ack", type="MESSAGE_DRAFT_READY")
        self.ingest(other)
        oclaim = self.store.claim("board-138", now=NOW)
        self.store.mark_processed(
            "not-ack", claim_token=oclaim.claim_token, now=NOW
        )
        self.assertFalse(self.store.ack("not-ack", "solo", now=NOW))
        self.assertEqual(self.store.get("not-ack").status, PROCESSED)

    def test_stale_claim_requeues_below_cap_then_holds_at_cap(self):
        self.ingest(event(expires_at=MUCH_LATER))
        first = self.store.claim(now="2026-08-26T12:00:00Z")
        self.assertEqual(first.claim_attempts, 1)
        self.assertEqual(
            self.store.recover_stale(
                timeout_seconds=300, now="2026-08-26T12:04:59Z"
            ),
            0,
        )
        self.assertEqual(
            self.store.recover_stale(
                timeout_seconds=300, now="2026-08-26T12:05:00Z"
            ),
            1,
        )
        second = self.store.claim(now="2026-08-26T12:05:01Z")
        self.assertEqual(second.claim_attempts, 2)
        self.assertEqual(
            self.store.recover_stale(
                timeout_seconds=300, now="2026-08-26T12:10:01Z"
            ),
            1,
        )
        third = self.store.claim(now="2026-08-26T12:10:02Z")
        self.assertEqual(third.claim_attempts, 3)
        self.assertEqual(
            self.store.recover_stale(
                timeout_seconds=300, now="2026-08-26T12:15:02Z"
            ),
            1,
        )
        exhausted = self.store.get("evt-001")
        self.assertEqual(exhausted.status, HELD)
        self.assertIn("retry limit", exhausted.note)
        self.assertIsNone(self.store.claim(now="2026-08-26T12:15:03Z"))

    def test_crash_recovery_and_persistence_across_reopen(self):
        self.ingest(event(expires_at=MUCH_LATER))
        claim = self.store.claim(now="2026-08-26T12:00:00Z")
        token = claim.claim_token
        self.store.close()  # crash after claim, before final status

        self.store = BoardEventStore(self.path, SECRET, now=lambda: NOW)
        persisted = self.store.get("evt-001")
        self.assertEqual(persisted.claim_token, token)
        self.assertEqual(persisted.claim_attempts, 1)
        self.assertEqual(
            self.store.recover(
                timeout_seconds=300, now="2026-08-26T12:05:00Z"
            ),
            1,
        )
        reclaimed = self.store.claim(now="2026-08-26T12:05:01Z")
        self.assertEqual(reclaimed.event_id, "evt-001")
        self.assertNotEqual(reclaimed.claim_token, token)
        self.assertEqual(reclaimed.claim_attempts, 2)

    def test_claimed_event_can_finish_after_delivery_ttl(self):
        item = event(
            event_id="slow-work",
            created_at="2026-08-26T11:59:00Z",
            expires_at="2026-08-26T12:00:01Z",
        )
        self.ingest(item, now="2026-08-26T12:00:00Z")
        claimed = self.store.claim(now="2026-08-26T12:00:00Z")
        self.assertTrue(
            self.store.mark_processed(
                "slow-work",
                claim_token=claimed.claim_token,
                now="2026-08-26T12:00:02Z",
            )
        )
        self.assertEqual(self.store.get("slow-work").status, PROCESSED)

    def test_pending_rejects_events_that_expire_while_stored(self):
        self.ingest()
        self.assertEqual(len(self.store.pending(now=NOW)), 1)
        self.assertEqual(self.store.pending(now=LATER), [])
        got = self.store.get("evt-001")
        self.assertEqual(got.status, REJECTED)
        self.assertEqual(got.note, "expired")

    def test_limit_is_bounded_and_validated(self):
        self.ingest()
        self.assertEqual(self.store.pending(limit=0, now=NOW), [])
        for invalid in (-1, 1.5, True):
            with self.subTest(invalid=invalid), self.assertRaises(
                BoardEventValidationError
            ):
                self.store.pending(limit=invalid, now=NOW)

    def test_schema_and_rows_persist_after_clean_reopen(self):
        self.ingest()
        self.store.close()
        self.store = BoardEventStore(self.path, SECRET, now=lambda: NOW)
        got = self.store.get("evt-001")
        self.assertEqual(got.as_dict(), envelope())
        self.assertEqual(self.store.counts(now=NOW), {RECEIVED: 1})


class NoOutboundAndNoSecretLoggingTests(unittest.TestCase):
    def test_module_has_no_network_import_or_logging_calls(self):
        path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "ofn",
            "adapters",
            "board_events.py",
        )
        with open(path, encoding="utf-8") as module_file:
            source = module_file.read()
        for forbidden in (
            "import requests",
            "import urllib",
            "import socket",
            "http.client",
            "logging.",
            "print(",
        ):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, source)


if __name__ == "__main__":
    unittest.main()
