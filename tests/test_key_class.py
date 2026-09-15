"""Contract tests for key_class (P1 complementary).

A caller-chosen idempotency key binds as KEY_BOUND. Missing is
UNKNOWN, not FALSE. send_authorized / quote_sent /
campaign_envelope_ready refuse. Binding does not burn and
does not grant a send. Ready ≠ authorized. Not wired into
the run store. Distinct from idempotency.py.
"""

from __future__ import annotations

import inspect
import unittest

from ofn.kernel.errors import FailClosedError
from ofn.kernel.key_class import (
    KEY_BOUND,
    KeyBind,
    UNKNOWN,
    bind_key,
    burns_key,
    claims_immutable,
    classify_key,
    grants_send,
    halt_blocks_bind,
    is_sealed_key,
    promotes_ready_to_send,
    proposal_is_execution,
    ready_is_authorized,
    timeout_proves_concurrent_write,
    try_bind,
    unknown_is_false,
)


class ClassifyKey(unittest.TestCase):
    def test_none_is_unknown_not_false(self):
        self.assertEqual(classify_key(None), UNKNOWN)
        self.assertNotEqual(classify_key(None), "FALSE")
        self.assertIsNot(classify_key(None), False)

    def test_plain_key_is_bound(self):
        self.assertEqual(classify_key("run-paint-l5-001"), KEY_BOUND)
        self.assertEqual(classify_key("abc123"), KEY_BOUND)

    def test_whitespace_stripped_still_binds(self):
        self.assertEqual(classify_key("  keep-me  "), KEY_BOUND)

    def test_send_authorized_fails_closed(self):
        with self.assertRaises(FailClosedError):
            classify_key("send_authorized")
        with self.assertRaises(FailClosedError):
            classify_key("Send_Authorized")
        with self.assertRaises(FailClosedError):
            classify_key("send-authorized")

    def test_quote_sent_fails_closed(self):
        with self.assertRaises(FailClosedError):
            classify_key("quote_sent")
        with self.assertRaises(FailClosedError):
            classify_key("quote-sent")

    def test_ready_name_fails_closed(self):
        with self.assertRaises(FailClosedError):
            classify_key("campaign_envelope_ready")
        with self.assertRaises(FailClosedError):
            classify_key("campaign-envelope-ready")

    def test_empty_fails_closed(self):
        with self.assertRaises(FailClosedError):
            classify_key("  ")
        with self.assertRaises(FailClosedError):
            classify_key("")

    def test_bool_int_fail_closed(self):
        with self.assertRaises(FailClosedError):
            classify_key(True)
        with self.assertRaises(FailClosedError):
            classify_key(1)
        with self.assertRaises(FailClosedError):
            classify_key(0)


class BindKey(unittest.TestCase):
    def test_bind_records_stripped_key(self):
        bound = bind_key("  keep-me  ")
        self.assertIsInstance(bound, KeyBind)
        self.assertEqual(bound.key, "keep-me")
        self.assertEqual(bound.key_class, KEY_BOUND)

    def test_bind_preserves_case(self):
        bound = bind_key("KeepMe")
        self.assertEqual(bound.key, "KeepMe")

    def test_frozen_cannot_retcon_to_send(self):
        bound = bind_key("keep-me")
        with self.assertRaises(Exception):
            bound.key = "send_authorized"  # type: ignore[misc]
        with self.assertRaises(Exception):
            bound.key_class = "send_authorized"  # type: ignore[misc]

    def test_constructor_refuses_sealed_name(self):
        with self.assertRaises(FailClosedError):
            KeyBind(key="send_authorized", key_class=KEY_BOUND)

    def test_constructor_refuses_non_bound_class(self):
        with self.assertRaises(FailClosedError):
            KeyBind(key="keep-me", key_class=UNKNOWN)

    def test_missing_on_explicit_bind_fails_closed(self):
        with self.assertRaises(FailClosedError):
            bind_key(None)

    def test_try_bind_missing_is_none(self):
        self.assertIsNone(try_bind(None))
        self.assertIsNot(try_bind(None), False)

    def test_try_bind_success(self):
        bound = try_bind("keep-me")
        self.assertIsNotNone(bound)
        assert bound is not None
        self.assertEqual(bound.key_class, KEY_BOUND)
        self.assertEqual(bound.key, "keep-me")

    def test_try_bind_present_bad_still_fails(self):
        with self.assertRaises(FailClosedError):
            try_bind("send_authorized")
        with self.assertRaises(FailClosedError):
            try_bind("quote_sent")
        with self.assertRaises(FailClosedError):
            try_bind("campaign_envelope_ready")


class SealedWitness(unittest.TestCase):
    def test_sealed_aliases(self):
        self.assertTrue(is_sealed_key("send_authorized"))
        self.assertTrue(is_sealed_key("Send_Authorized"))
        self.assertTrue(is_sealed_key("send-authorized"))
        self.assertTrue(is_sealed_key("quote_sent"))
        self.assertTrue(is_sealed_key("campaign_envelope_ready"))
        self.assertFalse(is_sealed_key("keep-me"))
        self.assertFalse(is_sealed_key(None))
        self.assertFalse(is_sealed_key(True))


class StructuralRefusals(unittest.TestCase):
    def test_grants_send_is_structurally_false(self):
        self.assertFalse(grants_send())

    def test_halt_does_not_block_bind(self):
        self.assertFalse(halt_blocks_bind())

    def test_unknown_is_not_false(self):
        self.assertFalse(unknown_is_false())

    def test_ready_is_not_authorized(self):
        self.assertFalse(ready_is_authorized())
        self.assertFalse(promotes_ready_to_send())
        self.assertNotEqual("campaign_envelope_ready", "send_authorized")
        self.assertNotEqual("send_authorized", "quote_sent")

    def test_does_not_burn(self):
        self.assertFalse(burns_key())

    def test_does_not_claim_immutable(self):
        self.assertFalse(claims_immutable())

    def test_timeout_does_not_prove_writer(self):
        self.assertFalse(timeout_proves_concurrent_write())

    def test_proposal_is_not_execution(self):
        self.assertFalse(proposal_is_execution())

    def test_classify_has_no_halt_or_now_parameter(self):
        params = inspect.signature(classify_key).parameters
        self.assertNotIn("halted", params)
        self.assertNotIn("now", params)
        self.assertEqual(list(params), ["value"])


class NotWiredIntoStore(unittest.TestCase):
    def test_run_store_does_not_import_these_modules(self):
        import ofn.adapters.run_store as run_store
        source = inspect.getsource(run_store)
        self.assertNotIn("key_class", source)
        self.assertNotIn("burn_pin", source)

    def test_idempotency_module_is_a_different_file(self):
        import ofn.kernel.idempotency as idem
        source = inspect.getsource(idem)
        self.assertNotIn("key_class", source)
        self.assertNotIn("burn_pin", source)
        self.assertNotIn("KEY_BOUND", source)


if __name__ == "__main__":
    unittest.main()
