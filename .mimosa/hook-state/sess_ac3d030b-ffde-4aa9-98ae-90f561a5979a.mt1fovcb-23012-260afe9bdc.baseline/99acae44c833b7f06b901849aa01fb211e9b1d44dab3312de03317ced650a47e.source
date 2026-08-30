"""O10 — read-only pilot harness tests.

The harness must: read bounded pages, store cursor after commit, keep
receipts on rollback, never publish, and be dormant until Ari's four
decisions are made (no vendor/tenant/token wired here).
"""

from __future__ import annotations

import unittest

from ofn.adapters.pilot import PilotState, ReadOnlyPilot


class _FakeAdapter:
    """A read-only adapter that yields pages and never mutates."""

    def __init__(self, total: int = 45):
        self._total = total
        self._reads = 0

    def read_page(self, *, cursor: str, limit: int) -> dict:
        self._reads += 1
        start = int(cursor) if cursor else 0
        end = min(start + limit, self._total)
        items = [{"id": str(i)} for i in range(start, end)]
        next_cursor = str(end) if end < self._total else ""
        return {"items": items, "next_cursor": next_cursor}

    @property
    def reads(self) -> int:
        return self._reads


class TestReadOnlyPilot(unittest.TestCase):
    def test_bounded_pages_no_overlap(self):
        adapter = _FakeAdapter(total=45)
        state = PilotState(connector_id="c1", tenant="ziman")
        pilot = ReadOnlyPilot(adapter, state, page_limit=20)
        r1 = pilot.run()
        self.assertEqual(r1["read"], 20)
        self.assertEqual(r1["cursor"], "20")
        r2 = pilot.run()
        self.assertEqual(r2["read"], 20)
        self.assertEqual(r2["cursor"], "40")
        r3 = pilot.run()
        self.assertEqual(r3["read"], 5)
        self.assertEqual(r3["cursor"], "")
        # 45 items read exactly once across three pages.
        ids = [rc["id"] for rc in state.receipts]
        self.assertEqual(len(ids), 45)
        self.assertEqual(len(set(ids)), 45)

    def test_cursor_is_stored_after_read(self):
        adapter = _FakeAdapter(total=30)
        state = PilotState(connector_id="c1", tenant="ziman")
        pilot = ReadOnlyPilot(adapter, state, page_limit=10)
        pilot.run()
        # The receipt count equals the items read — the cursor write is the
        # commit, and both happened in run().
        self.assertEqual(len(state.receipts), 10)
        self.assertEqual(state.cursor, "10")

    def test_rollback_disables_and_keeps_receipts(self):
        adapter = _FakeAdapter(total=10)
        state = PilotState(connector_id="c1", tenant="ziman")
        pilot = ReadOnlyPilot(adapter, state, page_limit=10)
        pilot.run()
        rb = pilot.rollback()
        self.assertTrue(rb["ok"])
        self.assertEqual(rb["rule"], "pilot:rolled-back")
        self.assertFalse(pilot.enabled())
        # A disabled pilot refuses further reads but keeps the receipts.
        r = pilot.run()
        self.assertFalse(r["ok"])
        self.assertEqual(r["rule"], "pilot:disabled")
        self.assertEqual(len(state.receipts), 10)

    def test_dormant_until_decisions(self):
        """No vendor, no tenant, no token is hard-wired here."""
        state = PilotState()   # empty: nothing wired
        self.assertEqual(state.connector_id, "")
        self.assertEqual(state.tenant, "")


if __name__ == "__main__":
    unittest.main()
