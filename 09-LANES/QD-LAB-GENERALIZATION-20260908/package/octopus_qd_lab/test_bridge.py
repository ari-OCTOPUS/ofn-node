"""Isolated stdlib unittest coverage for the offline OCTOPUS evidence layer.

Run from this directory:
    PYTHONDONTWRITEBYTECODE=1 python -m unittest -v test_bridge
"""

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

import octopus_bridge
from octopus_bridge import (
    ReceiptLedger,
    make_proposal,
    observe_vitality,
    verify_ledger,
)


def canonical(value):
    """Independent test implementation of the documented canonical encoding."""
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
        allow_nan=False,
    )


def rehash(receipt):
    unsigned = {key: value for key, value in receipt.items() if key != "hash"}
    receipt["hash"] = hashlib.sha256(canonical(unsigned).encode("utf-8")).hexdigest()
    return receipt


class LedgerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / "receipts.jsonl"

    def create(self, count=3):
        receipts = []
        with ReceiptLedger(self.path) as ledger:
            for generation in range(count):
                receipts.append(
                    ledger.append(
                        "GENERATION_EVALUATED",
                        {"generation": generation, "fitness": generation / 10},
                        generation,
                    )
                )
        return receipts

    def rewrite(self, receipts):
        self.path.write_text(
            "".join(canonical(receipt) + "\n" for receipt in receipts),
            encoding="utf-8",
        )

    def assert_invalid(self, **anchors):
        result = verify_ledger(self.path, **anchors)
        self.assertIs(result["valid"], False)
        self.assertTrue(result["errors"])
        self.assertEqual(set(result), {"valid", "count", "head", "errors"})
        return result

    def test_exports(self):
        self.assertEqual(
            set(octopus_bridge.__all__),
            {"ReceiptLedger", "verify_ledger", "make_proposal", "observe_vitality"},
        )

    def test_exclusive_creation_preserves_existing_bytes(self):
        self.path.write_bytes(b"do not overwrite\n")
        with self.assertRaises(FileExistsError):
            ReceiptLedger(self.path)
        self.assertEqual(self.path.read_bytes(), b"do not overwrite\n")

    def test_exclusive_creation_rejects_even_existing_empty_file(self):
        self.path.touch()
        with self.assertRaises(FileExistsError):
            ReceiptLedger(self.path)
        self.assertEqual(self.path.read_bytes(), b"")

    def test_receipt_schema_canonical_hash_and_chain(self):
        receipts = self.create()
        self.assertEqual(
            set(receipts[0]),
            {
                "schema_version", "index", "event_time", "record_time",
                "previous_hash", "payload", "event_type", "hash",
            },
        )
        previous = "0" * 64
        for index, receipt in enumerate(receipts):
            self.assertEqual(receipt["schema_version"], 1)
            self.assertEqual(receipt["index"], index)
            self.assertEqual(receipt["event_time"], index)
            self.assertEqual(receipt["previous_hash"], previous)
            self.assertEqual(receipt["hash"], rehash(dict(receipt))["hash"])
            previous = receipt["hash"]
        result = verify_ledger(self.path, receipts[-1]["hash"], len(receipts))
        self.assertEqual(
            result, {"valid": True, "count": 3, "head": previous, "errors": []}
        )

    def test_record_time_is_actual_utc_not_logical_event_time(self):
        before = datetime.now(timezone.utc)
        with ReceiptLedger(self.path) as ledger:
            receipt = ledger.append("EVALUATION", {}, 37)
        after = datetime.now(timezone.utc)
        stamp = datetime.fromisoformat(receipt["record_time"])
        self.assertEqual(stamp.utcoffset(), timedelta(0))
        self.assertLessEqual(before, stamp)
        self.assertLessEqual(stamp, after)
        self.assertEqual(
            receipt["record_time"], stamp.isoformat(timespec="microseconds")
        )
        self.assertEqual(receipt["event_time"], 37)

    def test_context_manager_and_read_only_anchors(self):
        with ReceiptLedger(self.path) as ledger:
            self.assertIsNone(ledger.head)
            self.assertEqual(ledger.count, 0)
            first = ledger.append("TEST", {}, 0)
            self.assertEqual(ledger.count, 1)
            self.assertEqual(ledger.head, first["hash"])
            with self.assertRaises(AttributeError):
                ledger.head = "f" * 64
            with self.assertRaises(AttributeError):
                ledger.count = 8
        self.assertTrue(ledger.closed)
        ledger.close()
        with self.assertRaises(ValueError):
            ledger.append("AFTER_CLOSE", {}, 1)
        with self.assertRaises(ValueError):
            with ledger:
                self.fail("closed ledger must not reenter")

    def test_context_manager_closes_and_propagates_exception(self):
        ledger = ReceiptLedger(self.path)
        with self.assertRaisesRegex(RuntimeError, "intentional"):
            with ledger:
                ledger.append("TEST", {}, 0)
                raise RuntimeError("intentional")
        self.assertTrue(ledger.closed)
        self.assertTrue(verify_ledger(self.path)["valid"])

    def test_append_flushes_and_does_not_rewrite_prefix(self):
        with ReceiptLedger(self.path) as ledger:
            first = ledger.append("FIRST", {}, 0)
            prefix = self.path.read_bytes()
            self.assertTrue(verify_ledger(self.path, first["hash"], 1)["valid"])
            ledger.append("SECOND", {}, 1)
            self.assertTrue(self.path.read_bytes().startswith(prefix))
            self.assertTrue(self.path.read_bytes().endswith(b"\n"))

    def test_payload_and_returned_receipt_are_detached(self):
        payload = {"nested": [{"score": 1}], "name": "octopus"}
        with ReceiptLedger(self.path) as ledger:
            first = ledger.append("FIRST", payload, 0)
            original_head = first["hash"]
            payload["nested"][0]["score"] = 90
            first["payload"]["nested"][0]["score"] = 100
            first["hash"] = "f" * 64
            second = ledger.append("SECOND", {}, 0)
        disk = [json.loads(line) for line in self.path.read_text().splitlines()]
        self.assertEqual(disk[0]["payload"]["nested"][0]["score"], 1)
        self.assertEqual(second["previous_hash"], original_head)
        self.assertTrue(verify_ledger(self.path)["valid"])

    def test_unicode_and_all_supported_json_payload_types(self):
        payload = {
            "label": "octopus \u03bb \U0001f419",
            "items": [None, True, False, -2, 0, 0.25, "two\nlines", {}],
        }
        with ReceiptLedger(self.path) as ledger:
            receipt = ledger.append("UNICODE", payload, 0)
        self.assertEqual(receipt["payload"], payload)
        self.assertIn("\u03bb".encode("utf-8"), self.path.read_bytes())
        self.assertTrue(verify_ledger(self.path)["valid"])

    def test_logical_times_can_repeat_or_go_back(self):
        with ReceiptLedger(self.path) as ledger:
            for event_time in (3, 3, 0):
                ledger.append("ISLAND_EVENT", {}, event_time)
        self.assertTrue(verify_ledger(self.path)["valid"])

    def test_invalid_logical_times_rejected_without_consuming_index(self):
        bad = [True, False, -1, 1.0, float("nan"), float("inf"), "1", None,
               datetime.now(timezone.utc)]
        with ReceiptLedger(self.path) as ledger:
            for event_time in bad:
                with self.subTest(event_time=event_time):
                    with self.assertRaises(ValueError):
                        ledger.append("TEST", {}, event_time)
            self.assertEqual(ledger.count, 0)
            self.assertEqual(self.path.read_bytes(), b"")
            self.assertEqual(ledger.append("VALID", {}, 1)["index"], 0)

    def test_invalid_event_types_fail_without_write(self):
        with ReceiptLedger(self.path) as ledger:
            for event_type in ("", " \t\n", 1, True, None, [], {}):
                with self.subTest(event_type=event_type):
                    with self.assertRaises(ValueError):
                        ledger.append(event_type, {}, 0)
            self.assertEqual(self.path.read_bytes(), b"")

    def test_invalid_payloads_rejected_without_write(self):
        bad = [
            None, [], "text", 1, {1: "coerced key"}, {"tuple": (1, 2)},
            {"set": {1}}, {"bad": object()}, {"nan": float("nan")},
            {"infinite": float("inf")}, {"infinite": -float("inf")},
            {"surrogate": "\ud800"},
        ]
        cycle = {}
        cycle["self"] = cycle
        bad.append(cycle)
        with ReceiptLedger(self.path) as ledger:
            for index, payload in enumerate(bad):
                with self.subTest(case=index):
                    with self.assertRaises(ValueError):
                        ledger.append("TEST", payload, 0)
            self.assertEqual(self.path.read_bytes(), b"")
            self.assertEqual(ledger.append("RECOVERED", {}, 0)["index"], 0)

    def test_single_instance_concurrent_appends_are_serialized(self):
        with ReceiptLedger(self.path) as ledger:
            with ThreadPoolExecutor(max_workers=4) as pool:
                receipts = list(
                    pool.map(lambda i: ledger.append("TEST", {"i": i}, i), range(24))
                )
            self.assertEqual({record["index"] for record in receipts}, set(range(24)))
            head = ledger.head
        self.assertTrue(verify_ledger(self.path, head, 24)["valid"])

    def test_write_failure_closes_and_poisons_instance(self):
        class BrokenWriter:
            def __init__(self):
                self.closed = False

            def write(self, line):
                raise OSError("simulated disk failure")

            def close(self):
                self.closed = True

        ledger = ReceiptLedger(self.path)
        self.addCleanup(ledger.close)
        ledger._file.close()
        broken = BrokenWriter()
        ledger._file = broken
        with self.assertRaisesRegex(OSError, "simulated"):
            ledger.append("TEST", {}, 0)
        self.assertTrue(ledger.closed)
        self.assertTrue(broken.closed)
        self.assertEqual(ledger.count, 0)
        self.assertIsNone(ledger.head)
        with self.assertRaises(ValueError):
            ledger.append("RETRY", {}, 0)

    def test_payload_tampering_detected(self):
        receipts = self.create()
        receipts[1]["payload"]["fitness"] = 999
        self.rewrite(receipts)
        result = self.assert_invalid()
        self.assertEqual(result["count"], 1)
        self.assertEqual(result["head"], receipts[0]["hash"])
        self.assertTrue(any("hash mismatch" in error for error in result["errors"]))

    def test_record_timestamp_tampering_detected(self):
        receipts = self.create()
        receipts[0]["record_time"] = "2000-01-01T00:00:00.000000+00:00"
        self.rewrite(receipts)
        self.assert_invalid()

    def test_reordering_detected(self):
        receipts = self.create()
        self.rewrite([receipts[1], receipts[0], receipts[2]])
        self.assert_invalid()

    def test_removing_middle_record_detected(self):
        receipts = self.create()
        self.rewrite([receipts[0], receipts[2]])
        self.assert_invalid()

    def test_duplicate_record_detected(self):
        receipts = self.create()
        self.rewrite([receipts[0], receipts[1], receipts[1], receipts[2]])
        self.assert_invalid()

    def test_truncation_detected_with_either_anchor(self):
        receipts = self.create()
        self.rewrite(receipts[:-1])
        # An unanchored valid prefix alone cannot reveal suffix truncation.
        self.assertTrue(verify_ledger(self.path)["valid"])
        self.assert_invalid(expected_head=receipts[-1]["hash"])
        self.assert_invalid(expected_count=3)
        self.assert_invalid(expected_head=receipts[-1]["hash"], expected_count=3)

    def test_entire_rewrite_needs_trusted_head_not_just_count(self):
        receipts = self.create()
        trusted_head = receipts[-1]["hash"]
        previous = "0" * 64
        for receipt in receipts:
            receipt["payload"]["fitness"] = 999
            receipt["previous_hash"] = previous
            previous = rehash(receipt)["hash"]
        self.rewrite(receipts)
        self.assertTrue(verify_ledger(self.path)["valid"])
        self.assertTrue(verify_ledger(self.path, expected_count=3)["valid"])
        self.assert_invalid(expected_head=trusted_head)
        # Replacing the anchor as well defeats local-only verification.
        self.assertTrue(verify_ledger(self.path, receipts[-1]["hash"], 3)["valid"])

    def test_empty_file_fails_even_with_zero_count_anchor(self):
        with ReceiptLedger(self.path):
            pass
        result = self.assert_invalid(expected_count=0)
        self.assertEqual(result["count"], 0)
        self.assertIsNone(result["head"])

    def test_missing_unreadable_and_bad_path_fail_closed(self):
        self.assert_invalid()
        for path in (Path(self.temp.name), None, 99, "\x00"):
            with self.subTest(path=path):
                self.assertFalse(verify_ledger(path)["valid"])

    def test_malformed_jsonl_fails_closed(self):
        for contents in (b"\n", b"   \n", b"{broken}\n", b"null\n", b"[]\n",
                         b'{"schema_version":1}\n', b"\xff\n"):
            with self.subTest(contents=contents):
                self.path.write_bytes(contents)
                self.assert_invalid()

    def test_unterminated_final_record_fails_closed(self):
        self.create()
        self.path.write_bytes(self.path.read_bytes().rstrip(b"\n"))
        self.assert_invalid()

    def test_trailing_blank_or_garbage_record_fails_closed(self):
        self.create()
        original = self.path.read_bytes()
        for suffix in (b"\n", b"not json\n", b'{"truncated":'):
            with self.subTest(suffix=suffix):
                self.path.write_bytes(original + suffix)
                self.assert_invalid()

    def test_duplicate_json_keys_rejected_even_when_hash_would_match(self):
        receipts = self.create(1)
        line = canonical(receipts[0])
        self.path.write_text(
            '{"schema_version":1,' + line[1:] + "\n", encoding="utf-8"
        )
        self.assert_invalid()
        duplicate_payload = dict(receipts[0], payload={"x": 1})
        line = canonical(rehash(duplicate_payload)).replace(
            '"payload":{"x":1}', '"payload":{"x":1,"x":1}'
        )
        self.path.write_text(line + "\n", encoding="utf-8")
        self.assert_invalid()

    def test_nonfinite_json_constants_and_overflow_rejected(self):
        receipts = self.create(1)
        line = canonical(receipts[0])
        for constant in ("NaN", "Infinity", "-Infinity", "1e9999"):
            with self.subTest(constant=constant):
                modified = line.replace('"fitness":0.0', '"fitness":' + constant)
                self.path.write_text(modified + "\n", encoding="utf-8")
                self.assert_invalid()

    def test_missing_and_unknown_receipt_fields_rejected(self):
        receipt = self.create(1)[0]
        for key in receipt:
            with self.subTest(missing=key):
                broken = dict(receipt)
                del broken[key]
                self.rewrite([broken])
                self.assert_invalid()
        broken = dict(receipt, approved=True)
        self.rewrite([rehash(broken)])
        self.assert_invalid()

    def test_rehashed_malformed_receipt_fields_still_rejected(self):
        receipt = self.create(1)[0]
        bad_fields = [
            ("schema_version", True), ("schema_version", 2),
            ("schema_version", 1.0), ("index", True), ("index", -1),
            ("index", 1), ("event_time", True), ("event_time", 1.0),
            ("event_time", -1), ("event_type", ""), ("payload", []),
            ("record_time", 0), ("record_time", "unknown"),
            ("record_time", "2026-01-01T00:00:00.000000"),
            ("record_time", "2026-01-01T01:00:00.000000+01:00"),
            ("previous_hash", "f" * 64), ("previous_hash", None),
        ]
        for field, value in bad_fields:
            with self.subTest(field=field, value=value):
                self.rewrite([rehash(dict(receipt, **{field: value}))])
                self.assert_invalid()

    def test_malformed_or_wrong_hash_rejected(self):
        receipt = self.create(1)[0]
        for value in (None, True, "", "f" * 63, "G" * 64, "F" * 64, "f" * 64):
            with self.subTest(value=value):
                self.rewrite([dict(receipt, hash=value)])
                self.assert_invalid()

    def test_semantic_whitespace_and_key_order_not_byte_integrity(self):
        receipts = self.create()
        self.path.write_text(
            "".join(json.dumps(record, sort_keys=False) + "\n" for record in receipts),
            encoding="utf-8",
        )
        self.assertTrue(verify_ledger(self.path, receipts[-1]["hash"], 3)["valid"])

    def test_invalid_anchors_fail_closed(self):
        receipts = self.create()
        for count in (True, False, -1, 1.0, "3", float("nan"), float("inf"), []):
            with self.subTest(count=count):
                self.assert_invalid(expected_count=count)
        for head in (True, 3, "", "f" * 63, "X" * 64, [], {}):
            with self.subTest(head=head):
                self.assert_invalid(expected_head=head)
        self.assert_invalid(expected_count=4)
        self.assert_invalid(expected_head="f" * 64)
        self.assertTrue(verify_ledger(self.path, receipts[-1]["hash"], 3)["valid"])


class ProposalTests(unittest.TestCase):
    def evidence(self, **updates):
        result = {"integrity_ok": True, "tests_ok": True, "evidence_count": 3}
        result.update(updates)
        return result

    def assert_no_authority(self, proposal):
        self.assertIs(proposal["production_authorized"], False)
        self.assertEqual(proposal["action"], "NONE")
        self.assertEqual(proposal["authority"], "A0_PROPOSE_ONLY")
        self.assertNotIn("execute", proposal)
        self.assertNotIn("execute_flag", proposal)
        self.assertEqual(
            set(proposal),
            {
                "production_authorized", "action", "authority",
                "technical_lab_status", "evidence_count", "reasons",
            },
        )
        json.dumps(proposal, allow_nan=False)

    def test_technical_pass_is_only_propose(self):
        for count in (1, 3, 0.5, 1e300, 10 ** 400):
            with self.subTest(count=count):
                result = make_proposal(self.evidence(evidence_count=count))
                self.assertEqual(result["technical_lab_status"], "PASS")
                self.assertEqual(result["evidence_count"], count)
                self.assertEqual(result["reasons"], [])
                self.assert_no_authority(result)

    def test_zero_is_valid_but_insufficient_for_pass(self):
        for count in (0, 0.0, -0.0):
            with self.subTest(count=count):
                result = make_proposal(self.evidence(evidence_count=count))
                self.assertEqual(result["technical_lab_status"], "INSUFFICIENT_EVIDENCE")
                self.assertEqual(result["evidence_count"], 0)
                self.assert_no_authority(result)

    def test_explicit_check_failure(self):
        for integrity, tests in ((False, True), (True, False), (False, False)):
            with self.subTest(integrity=integrity, tests=tests):
                result = make_proposal(
                    self.evidence(integrity_ok=integrity, tests_ok=tests)
                )
                self.assertEqual(result["technical_lab_status"], "FAIL")
                self.assert_no_authority(result)

    def test_missing_evidence_fields_fail_closed(self):
        for missing in self.evidence():
            evidence = self.evidence()
            del evidence[missing]
            with self.subTest(missing=missing):
                result = make_proposal(evidence)
                self.assertEqual(result["technical_lab_status"], "UNKNOWN")
                self.assert_no_authority(result)
        self.assertEqual(make_proposal({})["technical_lab_status"], "UNKNOWN")

    def test_malformed_evidence_containers_fail_closed(self):
        for evidence in (None, [], (), "approved", True, 1, float("nan")):
            with self.subTest(evidence=evidence):
                result = make_proposal(evidence)
                self.assertEqual(result["technical_lab_status"], "UNKNOWN")
                self.assert_no_authority(result)

    def test_flags_must_be_strict_bools_not_truthy_or_falsey(self):
        class Truthy:
            def __bool__(self):
                raise AssertionError("must not ask a custom value for truthiness")

        for flag in ("integrity_ok", "tests_ok"):
            for value in (1, 0, 1.0, "true", "False", "PASS", "unknown",
                          None, [], {}, float("nan"), float("inf"), Truthy()):
                with self.subTest(flag=flag, value_type=type(value).__name__):
                    result = make_proposal(self.evidence(**{flag: value}))
                    self.assertEqual(result["technical_lab_status"], "UNKNOWN")
                    self.assert_no_authority(result)

    def test_count_nan_bool_and_numeric_coercion_tricks_fail_closed(self):
        class NumberSubclass(int):
            pass

        for count in (True, False, -1, -0.5, float("nan"), float("inf"),
                      -float("inf"), "3", None, [], {}, 1 + 0j, NumberSubclass(1)):
            with self.subTest(count_type=type(count).__name__, count=count):
                result = make_proposal(self.evidence(evidence_count=count))
                self.assertEqual(result["technical_lab_status"], "UNKNOWN")
                self.assertIsNone(result["evidence_count"])
                self.assert_no_authority(result)

    def test_unknown_fields_and_owner_approval_never_authorize(self):
        extras = [
            {"owner_approval": "APPROVED by owner"},
            {"signature": "signed by admin"},
            {"production_authorized": True},
            {"action": "EXECUTE"},
            {"authority": "A9_ADMIN"},
            {"execute": True},
            {"technical_lab_status": "PASS"},
            {"independent": True},
            {"future_schema": 2},
            {1: True},
        ]
        for extra in extras:
            with self.subTest(extra=extra):
                evidence = self.evidence()
                evidence.update(extra)
                result = make_proposal(evidence)
                self.assertEqual(result["technical_lab_status"], "UNKNOWN")
                self.assertIn("unknown_evidence_fields", result["reasons"])
                self.assert_no_authority(result)

    def test_malformed_takes_precedence_over_failed_check(self):
        result = make_proposal(self.evidence(integrity_ok=False, evidence_count=float("nan")))
        self.assertEqual(result["technical_lab_status"], "UNKNOWN")
        self.assert_no_authority(result)

    def test_input_and_later_proposals_are_not_mutated(self):
        evidence = self.evidence()
        before = dict(evidence)
        result = make_proposal(evidence)
        self.assertEqual(evidence, before)
        result["production_authorized"] = True
        result["reasons"].append("external edit")
        fresh = make_proposal(evidence)
        self.assertEqual(fresh["reasons"], [])
        self.assert_no_authority(fresh)


class VitalityTests(unittest.TestCase):
    def assert_observe_only(self, result):
        self.assertIs(result["observe_only"], True)
        self.assertIs(result["controls_motion"], False)
        self.assertIs(result["production_authorized"], False)
        self.assertEqual(result["action"], "NONE")
        self.assertEqual(result["authority"], "A0_PROPOSE_ONLY")
        self.assertEqual(result["value_kind"], "TOY_RESOURCE_PROXY")
        self.assertNotIn("execute", result)
        self.assertGreaterEqual(result["energy_reserve"], 0.0)
        self.assertLessEqual(result["energy_reserve"], 1.0)
        json.dumps(result, allow_nan=False)

    def test_formula_matches_direct_toy_equation(self):
        for path, collision, turn in ((0, 0, 0), (1, 0.25, 0.5),
                                      (4, 0.1, 0.2), (100, 1, 5)):
            with self.subTest(path=path, collision=collision, turn=turn):
                result = observe_vitality(path, collision, turn)
                expected = max(0, min(1, 1 - 0.12 * path - 0.35 * turn - 0.4 * collision))
                self.assertAlmostEqual(result["energy_reserve"], expected)
                self.assertIs(result["input_valid"], True)
                self.assert_observe_only(result)

    def test_statuses_and_inclusive_thresholds(self):
        cases = [
            ((0, 0, 0), 1.0, "GREEN"),
            ((0, 0, 1), 0.65, "GREEN"),
            ((4, 0, 0), 0.52, "YELLOW"),
            ((5, 0, 0), 0.4, "YELLOW"),
            ((6, 0, 0), 0.28, "RED"),
            ((0, 1, 8 / 7), 0.2, "RED"),
            ((7, 0, 0), 0.16, "BLACK"),
        ]
        for inputs, energy, status in cases:
            with self.subTest(inputs=inputs):
                result = observe_vitality(*inputs)
                self.assertAlmostEqual(result["energy_reserve"], energy)
                self.assertEqual(result["status"], status)
                self.assert_observe_only(result)

    def test_just_below_thresholds(self):
        for turn, status in ((1.000001, "YELLOW"), ((0.6 / 0.35) + 0.000001, "RED"),
                             ((0.8 / 0.35) + 0.000001, "BLACK")):
            with self.subTest(turn=turn):
                self.assertEqual(observe_vitality(0, 0, turn)["status"], status)

    def test_clamps_and_handles_very_large_finite_values(self):
        for path, turn in ((1e308, 0), (10 ** 400, 0), (0, 1e308),
                           (0, 10 ** 400), (100, 100)):
            with self.subTest(path=path, turn=turn):
                result = observe_vitality(path, 0, turn)
                self.assertEqual(result["energy_reserve"], 0.0)
                self.assertEqual(result["status"], "BLACK")
                self.assertIs(result["input_valid"], True)
                self.assert_observe_only(result)

    def test_invalid_scalar_inputs_always_black(self):
        class FloatSubclass(float):
            pass

        bad = (True, False, None, "0", [], {}, -1, float("nan"),
               float("inf"), -float("inf"), 1 + 0j, FloatSubclass(0))
        for position in range(3):
            for value in bad:
                with self.subTest(position=position, value_type=type(value).__name__):
                    inputs = [0, 0, 0]
                    inputs[position] = value
                    result = observe_vitality(*inputs)
                    self.assertEqual(result["status"], "BLACK")
                    self.assertEqual(result["energy_reserve"], 0.0)
                    self.assertIs(result["input_valid"], False)
                    self.assert_observe_only(result)

    def test_collision_rate_domain_and_unbounded_turn_effort(self):
        for collision in (-0.01, 1.00001, 10 ** 400):
            with self.subTest(collision=collision):
                result = observe_vitality(0, collision, 0)
                self.assertEqual(result["status"], "BLACK")
                self.assertIs(result["input_valid"], False)
                self.assert_observe_only(result)
        result = observe_vitality(0, 0, 2)
        self.assertIs(result["input_valid"], True)
        self.assertEqual(result["status"], "RED")
        self.assert_observe_only(result)

    def test_observations_are_fresh_and_do_not_affect_proposals(self):
        first = observe_vitality(0, 0, 0)
        first["controls_motion"] = True
        self.assert_observe_only(observe_vitality(0, 0, 0))
        self.assertEqual(
            make_proposal({})["technical_lab_status"], "UNKNOWN"
        )


if __name__ == "__main__":
    unittest.main()
