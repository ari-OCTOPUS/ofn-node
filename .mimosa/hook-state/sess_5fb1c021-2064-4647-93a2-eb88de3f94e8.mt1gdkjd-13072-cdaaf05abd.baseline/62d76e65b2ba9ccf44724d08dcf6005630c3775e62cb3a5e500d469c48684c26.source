#!/usr/bin/env python3
"""Awareness Ask bridge — _self_context + intro intents (2026-08-12)."""
from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path

OPS = Path(__file__).resolve().parents[1]
ROOT = OPS.parent
sys.path.insert(0, str(OPS))
sys.path.insert(0, str(OPS / "owner_console"))


class TestSelfContext(unittest.TestCase):
    def test_self_context_mentions_two_brains_and_no_4d(self):
        from owner_console.collab_model_adapter import _self_context
        ctx = _self_context(limit=2000, query="از چی تشکیل شدی؟")
        self.assertIn("cortex", ctx)
        self.assertIn("business_brain", ctx)
        self.assertTrue(
            "وصل نیست" in ctx or "DEPRECATED" in ctx or "4d" in ctx.lower(),
            ctx[:400],
        )

    def test_self_context_failsoft_no_raise(self):
        from owner_console.collab_model_adapter import _self_context
        # Even with weird env, must not raise
        ctx = _self_context(limit=100, query="")
        self.assertIsInstance(ctx, str)
        self.assertLessEqual(len(ctx), 100)

    def test_self_context_includes_memory_block(self):
        from owner_console.collab_model_adapter import _self_context
        ctx = _self_context(limit=2500, query="improve خودبهبودی")
        self.assertIn("حافظه", ctx)


class TestConversationIntents(unittest.TestCase):
    def test_intro_from_chi_tashkil(self):
        from owner_console import conversation
        r = conversation.handle("از چی تشکیل شدی؟")
        self.assertEqual(r.get("schema"), "owner-console.reply.v1")
        self.assertEqual(r.get("kind"), "intro")
        self.assertFalse(r.get("external_effect"))
        self.assertIn("cortex", r.get("text") or "")
        self.assertIn("business_brain", (r.get("text") or ""))

    def test_blockers_intent(self):
        from owner_console import conversation
        r = conversation.handle("موانع چیست؟")
        self.assertEqual(r.get("kind"), "blockers")
        self.assertFalse(r.get("send_attempted"))

    def test_selfmap_intent(self):
        from owner_console import conversation
        r = conversation.handle("نقشه خودت چیست؟")
        self.assertEqual(r.get("kind"), "selfmap")
        self.assertIn("شاهد", (r.get("text") or "") + "selfmap")


if __name__ == "__main__":
    unittest.main()
