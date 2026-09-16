#!/usr/bin/env python3
"""owner_recall — cite-only, fail-soft, never authorize (2026-08-12)."""
from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path
from unittest import mock

OPS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(OPS / "memory"))
sys.path.insert(0, str(OPS))


class TestOwnerRecall(unittest.TestCase):
    def test_gate_off_still_failsoft(self):
        import owner_recall as or_
        with mock.patch.dict(os.environ, {"OCTOPUS_WIRE_MEMORY_GATE": "0"}, clear=False):
            facts = or_.recall_for_owner_ask("improve self-loop", limit=3)
        self.assertIsInstance(facts, list)
        for f in facts:
            self.assertIs(f.get("may_authorize"), False)

    def test_cite_only_shape(self):
        import owner_recall as or_
        facts = or_.recall_for_owner_ask("خودآگاهی", limit=2)
        self.assertIsInstance(facts, list)
        for f in facts:
            self.assertIn("content_preview", f)
            self.assertIn("mkey", f)
            self.assertIn("source_path", f)
            self.assertIs(f.get("may_authorize"), False)

    def test_topic_filter(self):
        import owner_recall as or_
        self.assertTrue(or_.topic_wants_recall("آخرین improve چی بود؟"))
        self.assertFalse(or_.topic_wants_recall("asdf qwerty zz"))

    def test_facts_block_empty_honest(self):
        import owner_recall as or_
        text = or_.facts_block_for_context([])
        self.assertIn("خالی", text)

    def test_no_authorize_creep(self):
        import owner_recall as or_
        facts = or_.recall_for_owner_ask("research حافظه", limit=5)
        self.assertTrue(all(f.get("may_authorize") is False for f in facts))


class TestCollaboratorFacts(unittest.TestCase):
    def test_collaborator_attaches_facts_field(self):
        os.environ.setdefault("OCTOPUS_WIRE_COLLAB", "1")
        os.environ["OCTOPUS_COLLAB_USE_MODEL"] = "0"  # stub fast
        from owner_console import collaborator
        r = collaborator.handle("از چی تشکیل شدی؟")
        self.assertEqual(r.get("schema"), "owner-console.reply.v1")
        self.assertFalse(r.get("external_effect"))
        self.assertFalse(r.get("send_attempted"))
        data = r.get("data") or {}
        self.assertIn("facts", data)
        self.assertIs(data.get("may_authorize"), False)


if __name__ == "__main__":
    unittest.main()
