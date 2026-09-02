"""D-27 W2-EDGE: boards propose. They do not send or write the ledger.

A new event type that means 'sent' or 'booked' or 'paid' must turn this
red. The adapter already refuses unknown types; this file makes that
refusal an explicit claim, not an accident of the allowlist test.
"""

from __future__ import annotations

import ast
import os
import tempfile
import unittest

from ofn.adapters.board_events import (
    EVENT_TYPES,
    BoardEventStore,
    BoardEventValidationError,
)
from ofn.config import D27_PER_BOARD_BUDGET_DEFAULT
from tests.test_board_events import NOW, SECRET, event


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BOARD_EVENTS = os.path.join(ROOT, "ofn", "adapters", "board_events.py")

LEDGER_EVENT_TYPES = frozenset(
    {
        "MESSAGE_SENT",
        "REVENUE_RECORDED",
        "BOOKING_CONFIRMED",
        "PAYMENT_RECEIVED",
        "INVOICE_ISSUED",
    }
)
FORBIDDEN_IMPORT_ROOTS = (
    "ofn.adapters.outbox",
    "ofn.commerce",
    "ofn.adapters.commerce",
    "ofn.agents.outbox",
    "smtplib",
    "http.client",
    "urllib.request",
    "requests",
)


def _import_names(tree: ast.AST) -> set[str]:
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                names.add(alias.name)
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.add(node.module)
    return names


class TestBoardIsProposalOnly(unittest.TestCase):
    def test_event_allowlist_has_no_send_or_money_types(self):
        self.assertTrue(LEDGER_EVENT_TYPES.isdisjoint(EVENT_TYPES))
        self.assertIn("MESSAGE_DRAFT_READY", EVENT_TYPES)
        self.assertNotIn("MESSAGE_SENT", EVENT_TYPES)

    def test_ledger_shaped_types_are_rejected(self):
        for kind in sorted(LEDGER_EVENT_TYPES):
            with self.subTest(kind=kind):
                with self.assertRaises(BoardEventValidationError):
                    event(type=kind)

    def test_adapter_source_does_not_import_send_or_commerce(self):
        with open(BOARD_EVENTS, encoding="utf-8") as fh:
            src = fh.read()
        tree = ast.parse(src, filename=BOARD_EVENTS)
        imported = _import_names(tree)
        offenders = [name for name in imported if name in FORBIDDEN_IMPORT_ROOTS
                     or name.split(".")[0] in {"requests", "httpx", "smtplib"}]
        self.assertEqual(offenders, [])
        self.assertNotIn("def send", src)
        names = [n.name for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]
        self.assertNotIn("send", names)
        self.assertNotIn("send_message", names)
        self.assertNotIn("record_revenue", names)
        self.assertNotIn("write_ledger", names)

    def test_ingest_does_not_create_a_commerce_or_outbox_file(self):
        with tempfile.TemporaryDirectory(prefix="d27-edge-") as tmp:
            path = os.path.join(tmp, "events.sqlite")
            store = BoardEventStore(path, SECRET, now=lambda: NOW)
            item = event()
            store.ingest(item, item.sign(SECRET), now=NOW)
            store.close()
            names = set(os.listdir(tmp))
            self.assertTrue(any(name.startswith("events.sqlite") for name in names))
            for banned in ("ledger.sqlite", "outbox.sqlite", "commerce.sqlite"):
                self.assertNotIn(banned, names)

    def test_per_board_budget_default_is_zero(self):
        self.assertEqual(D27_PER_BOARD_BUDGET_DEFAULT, 0)
