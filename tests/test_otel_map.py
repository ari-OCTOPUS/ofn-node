"""Contract tests for the telemetry span map.

The map is the P5 contract: every typed event has a span name, send
states do not, and looking up an unknown kind fails closed.
"""

from __future__ import annotations

import unittest

from ofn.kernel.errors import FailClosedError
from ofn.kernel.otel_map import (
    ATTRIBUTE_KEYS, EVENT_KINDS, NON_EXPORTABLE_STATES, SPAN_BY_KIND,
    attribute_key, is_exportable_state, span_name,
)


class Completeness(unittest.TestCase):
    def test_nine_kinds_each_have_a_span(self):
        self.assertEqual(set(SPAN_BY_KIND), EVENT_KINDS)
        self.assertEqual(len(SPAN_BY_KIND), 9)

    def test_span_names_are_dotted_and_nonempty(self):
        for kind, name in SPAN_BY_KIND.items():
            with self.subTest(kind=kind):
                self.assertIn(".", name)
                self.assertFalse(name.startswith("."))
                self.assertNotIn("send", name)


class FailClosedLookup(unittest.TestCase):
    def test_unknown_kind_refused(self):
        with self.assertRaises(FailClosedError):
            span_name("SOMETHING_ELSE")

    def test_known_kind_round_trips(self):
        self.assertEqual(span_name("RUN_CREATED"), "run.created")
        self.assertEqual(span_name("BUDGET_DEBIT"), "budget.debit")


class ReadyIsNotASendSpan(unittest.TestCase):
    def test_send_and_ready_states_are_not_in_the_map(self):
        for state in NON_EXPORTABLE_STATES:
            self.assertNotIn(state, SPAN_BY_KIND)
            self.assertNotIn(state, SPAN_BY_KIND.values())
            self.assertFalse(is_exportable_state(state))

    def test_empty_state_refused(self):
        with self.assertRaises(FailClosedError):
            is_exportable_state("")

    def test_attribute_allowlist_omits_unknown_fields(self):
        self.assertEqual(attribute_key("run_id"), "run.id")
        self.assertIsNone(attribute_key("customer_email"))
        self.assertNotIn("body", ATTRIBUTE_KEYS)
        self.assertNotIn("payload", ATTRIBUTE_KEYS)


if __name__ == "__main__":
    unittest.main()
