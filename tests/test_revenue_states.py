"""campaign_envelope_ready is not send_authorized — structural pin."""

from __future__ import annotations

import ast
import os
import unittest

from ofn.kernel.errors import FailClosedError
from ofn.kernel.revenue_states import (
    CAMPAIGN_ENVELOPE_READY, QUOTE_SENT, READY_STATES, SEND_AUTHORIZED,
    SEND_STATES, authorizes_external_effect, next_state_after_ready,
)

SRC = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "ofn", "kernel", "revenue_states.py",
)


class Separation(unittest.TestCase):
    def test_ready_is_not_authorized(self):
        self.assertNotEqual(CAMPAIGN_ENVELOPE_READY, SEND_AUTHORIZED)
        self.assertNotEqual(CAMPAIGN_ENVELOPE_READY, QUOTE_SENT)
        self.assertTrue(READY_STATES.isdisjoint(SEND_STATES))

    def test_ready_does_not_authorize_external_effect(self):
        self.assertFalse(authorizes_external_effect(CAMPAIGN_ENVELOPE_READY))
        self.assertFalse(authorizes_external_effect("policy_checked"))
        self.assertFalse(authorizes_external_effect("quote_drafted"))

    def test_send_states_are_refused_not_granted(self):
        with self.assertRaises(FailClosedError):
            authorizes_external_effect(SEND_AUTHORIZED)
        with self.assertRaises(FailClosedError):
            authorizes_external_effect(QUOTE_SENT)

    def test_unknown_state_is_not_authorized(self):
        with self.assertRaises(FailClosedError):
            authorizes_external_effect("looks-fine-to-me")

    def test_no_next_state_after_ready(self):
        with self.assertRaises(FailClosedError):
            next_state_after_ready()


class NoHiddenTransition(unittest.TestCase):
    def test_source_never_returns_a_send_state(self):
        tree = ast.parse(open(SRC, encoding="utf-8").read(), filename=SRC)
        returned = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Return) and node.value is not None:
                if isinstance(node.value, ast.Constant):
                    returned.append(node.value.value)
                elif isinstance(node.value, ast.Name):
                    returned.append(node.value.id)
        for item in returned:
            self.assertNotIn(item, SEND_STATES)
            self.assertNotEqual(item, SEND_AUTHORIZED)
            self.assertNotEqual(item, QUOTE_SENT)
            self.assertNotEqual(item, "SEND_AUTHORIZED")
            self.assertNotEqual(item, "QUOTE_SENT")


if __name__ == "__main__":
    unittest.main()
