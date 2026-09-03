"""Contract tests for typed_event (P1 complementary).

A record is TYPED only with kind + run_id + ts. Missing is UNKNOWN,
not FALSE. Sealed ready/send names refuse. Proposal ≠ execution.
BUDGET_DEBIT without ref fails closed. Not wired into the run store.
Distinct from kind_graph succession.
"""

from __future__ import annotations

import inspect
import unittest

from ofn.kernel.errors import FailClosedError
from ofn.kernel.events import (
    BUDGET_DEBIT,
    EXECUTION_RECEIPT,
    PROPOSAL_CREATED,
    RUN_CREATED,
)
from ofn.kernel.typed_event import (
    TYPED,
    TypedEvent,
    UNKNOWN,
    claims_immutable,
    classify_record,
    execution_kind,
    grants_send,
    halt_blocks_typed,
    is_execution,
    proposal_is_execution,
    proposal_kind,
    ready_is_authorized,
    require_typed,
    timeout_proves_concurrent_write,
    try_typed,
    unknown_is_false,
)


_TS = 1788405009
_RUN = "run-1788405009-typedevt01"


def _record(kind=RUN_CREATED, run_id=_RUN, ts=_TS, ref=None):
    rec = {"kind": kind, "run_id": run_id, "ts": ts}
    if ref is not None:
        rec["ref"] = ref
    return rec


class ClassifyRecord(unittest.TestCase):
    def test_none_is_unknown_not_false(self):
        self.assertEqual(classify_record(None), UNKNOWN)
        self.assertNotEqual(classify_record(None), "FALSE")

    def test_missing_kind_is_unknown(self):
        self.assertEqual(classify_record({"run_id": _RUN, "ts": _TS}), UNKNOWN)

    def test_none_kind_is_unknown(self):
        self.assertEqual(classify_record(_record(kind=None)), UNKNOWN)

    def test_none_run_id_is_unknown(self):
        self.assertEqual(classify_record(_record(run_id=None)), UNKNOWN)

    def test_none_ts_is_unknown(self):
        self.assertEqual(classify_record(_record(ts=None)), UNKNOWN)

    def test_run_created_is_typed(self):
        self.assertEqual(classify_record(_record()), TYPED)

    def test_proposal_is_typed_not_execution(self):
        self.assertEqual(classify_record(_record(kind=PROPOSAL_CREATED)), TYPED)
        self.assertFalse(is_execution(PROPOSAL_CREATED))
        self.assertFalse(proposal_is_execution())
        self.assertNotEqual(proposal_kind(), execution_kind())

    def test_execution_receipt_is_typed_and_execution(self):
        self.assertEqual(
            classify_record(_record(kind=EXECUTION_RECEIPT)), TYPED)
        self.assertTrue(is_execution(EXECUTION_RECEIPT))

    def test_budget_debit_requires_ref(self):
        with self.assertRaises(FailClosedError):
            classify_record(_record(kind=BUDGET_DEBIT))

    def test_budget_debit_with_ref_is_typed(self):
        self.assertEqual(
            classify_record(_record(kind=BUDGET_DEBIT, ref="evt-1")),
            TYPED)

    def test_unknown_kind_fails_closed(self):
        with self.assertRaises(FailClosedError):
            classify_record(_record(kind="GUESS"))

    def test_empty_kind_fails_closed(self):
        with self.assertRaises(FailClosedError):
            classify_record(_record(kind="  "))

    def test_bool_int_kind_fail_closed(self):
        with self.assertRaises(FailClosedError):
            classify_record(_record(kind=True))
        with self.assertRaises(FailClosedError):
            classify_record(_record(kind=1))

    def test_bool_ts_fails_closed(self):
        with self.assertRaises(FailClosedError):
            classify_record(_record(ts=True))

    def test_float_str_ts_fail_closed(self):
        with self.assertRaises(FailClosedError):
            classify_record(_record(ts=1788405009.0))
        with self.assertRaises(FailClosedError):
            classify_record(_record(ts="1788405009"))

    def test_string_record_fails_closed(self):
        with self.assertRaises(FailClosedError):
            classify_record("RUN_CREATED")

    def test_list_record_fails_closed(self):
        with self.assertRaises(FailClosedError):
            classify_record([RUN_CREATED, _RUN, _TS])

    def test_sealed_names_refused(self):
        for name in (
            "send_authorized",
            "quote_sent",
            "campaign_envelope_ready",
            "Send_Authorized",
            "send-authorized",
        ):
            with self.subTest(name=name):
                with self.assertRaises(FailClosedError):
                    classify_record(_record(kind=name))
                with self.assertRaises(FailClosedError):
                    classify_record(_record(run_id=name))
                with self.assertRaises(FailClosedError):
                    classify_record(_record(kind=BUDGET_DEBIT, ref=name))


class RequireAndTry(unittest.TestCase):
    def test_require_typed_records_frozen(self):
        typed = require_typed(_record(kind=EXECUTION_RECEIPT, ref="prior"))
        self.assertIsInstance(typed, TypedEvent)
        self.assertEqual(typed.kind, EXECUTION_RECEIPT)
        self.assertEqual(typed.run_id, _RUN)
        self.assertEqual(typed.ts, _TS)
        self.assertEqual(typed.ref, "prior")
        with self.assertRaises(Exception):
            typed.kind = RUN_CREATED  # type: ignore[misc]

    def test_require_typed_missing_fails_closed(self):
        with self.assertRaises(FailClosedError):
            require_typed(None)
        with self.assertRaises(FailClosedError):
            require_typed({"run_id": _RUN, "ts": _TS})

    def test_try_typed_missing_is_none(self):
        self.assertIsNone(try_typed(None))
        self.assertIsNone(try_typed({"kind": RUN_CREATED, "run_id": _RUN}))
        self.assertIsNone(try_typed(_record(kind=None)))

    def test_try_typed_success(self):
        typed = try_typed(_record())
        self.assertIsNotNone(typed)
        assert typed is not None
        self.assertEqual(typed.kind, RUN_CREATED)

    def test_try_typed_present_bad_still_fails(self):
        with self.assertRaises(FailClosedError):
            try_typed(_record(kind="GUESS"))
        with self.assertRaises(FailClosedError):
            try_typed(_record(ts=True))

    def test_is_execution_missing_fails_closed(self):
        with self.assertRaises(FailClosedError):
            is_execution(None)


class StructuralRefusals(unittest.TestCase):
    def test_grants_send_is_structurally_false(self):
        self.assertFalse(grants_send())

    def test_halt_does_not_block_classify(self):
        self.assertFalse(halt_blocks_typed())

    def test_unknown_is_not_false(self):
        self.assertFalse(unknown_is_false())

    def test_does_not_claim_immutable(self):
        self.assertFalse(claims_immutable())

    def test_ready_is_not_authorized(self):
        self.assertFalse(ready_is_authorized())
        self.assertNotEqual("campaign_envelope_ready", "send_authorized")

    def test_timeout_does_not_prove_writer(self):
        self.assertFalse(timeout_proves_concurrent_write())

    def test_classify_has_no_halt_or_now_parameter(self):
        params = inspect.signature(classify_record).parameters
        self.assertNotIn("halted", params)
        self.assertNotIn("now", params)
        self.assertEqual(list(params), ["record"])


class NotWiredIntoStore(unittest.TestCase):
    def test_run_store_does_not_import_this_module(self):
        import ofn.adapters.run_store as run_store
        source = inspect.getsource(run_store)
        self.assertNotIn("typed_event", source)
        self.assertNotIn("receipt_bind", source)

    def test_kind_graph_does_not_import_this_module(self):
        import ofn.kernel.kind_graph as kind_graph
        source = inspect.getsource(kind_graph)
        self.assertNotIn("typed_event", source)
        self.assertNotIn("receipt_bind", source)


if __name__ == "__main__":
    unittest.main()
