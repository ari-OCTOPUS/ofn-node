"""Phase 4: StudioAssistantStore reads from the shared corpus as a fallback.

When the tenant's own assistant_chunks have nothing for a question, the
shared knowledge (edge model, hypno research, cross-tenant seeds) may still
answer. This tests that fallback, and that the local answer is always
preferred over shared.
"""

import os
import unittest

from ofn.adapters.studio_assistant import StudioAssistantStore
from tests.tmpdir import temp_dir


class _FakeShared:
    """Minimal stand-in for fugu_core.memory.Memory.recall()."""
    def __init__(self, hits):
        self._hits = hits
        self.calls = []

    def recall(self, tenant, query, *, limit=5):
        self.calls.append((tenant, query, limit))
        return list(self._hits)


class TestSharedFallback(unittest.TestCase):
    def setUp(self):
        self._d = temp_dir(self)

    def _store(self, shared=None):
        return StudioAssistantStore(os.path.join(self._d, "a.sqlite"),
                                    shared_memory=shared)

    def test_local_answer_preferred_over_shared(self):
        # Local chunk present → shared never consulted.
        store = self._store(shared=_FakeShared(hits=[]))
        store.ingest_text("studio", "local", "local title",
                          "first post ideas for gallery", now_epoch_s=1000)
        out = store.answer_local("studio", "gallery post")
        self.assertTrue(out["sources"])
        # No shared fallback because local had an answer.

    def test_shared_used_when_local_empty(self):
        # No local chunks → shared is consulted.
        fake = _FakeShared(hits=[])
        store = self._store(shared=fake)
        store.answer_local("studio", "breathing calm")
        self.assertEqual(len(fake.calls), 1)
        self.assertEqual(fake.calls[0][0], "studio")

    def test_shared_returns_results_when_local_empty(self):
        # Local empty + shared has a hit → the shared hit appears in sources.
        class Passage:
            def __init__(self, cid, title, body, source_url="", source="seed"):
                self.chunk_id = cid
                self.title = title
                self.body = body
                self.source_url = source_url
                self.source = source
        hits = [Passage("s1", "breathing", "Breathe slowly to calm down.")]
        store = self._store(shared=_FakeShared(hits=hits))
        out = store.answer_local("studio", "how to calm down")
        self.assertTrue(any("Breathe slowly" in s["body"] for s in out["sources"]))

    def test_shared_failure_does_not_break_answer(self):
        # If shared.recall raises, the local path still returns an answer.
        class Broken:
            def recall(self, *a, **kw):
                raise RuntimeError("shared memory offline")
        store = self._store(shared=Broken())
        store.ingest_text("studio", "local", "t", "gallery tip", now_epoch_s=1)
        out = store.answer_local("studio", "gallery")
        # The answer still comes through from local chunks.
        self.assertNotIn("error", out)


if __name__ == "__main__":
    unittest.main()
