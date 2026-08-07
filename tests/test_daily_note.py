"""Daily notes: add, list, delete, and RAG sync idempotency."""

import os
import tempfile
import unittest

from hypno.adapters.store import Store

NOW_DAY = "2026-08-07"


class TestDailyNotesStore(unittest.TestCase):
    def setUp(self):
        self._d = tempfile.mkdtemp()
        self.s = Store(os.path.join(self._d, "x.sqlite"))

    def _add(self, user="u", content="یک یادداشت"):
        return self.s.add_daily_note(user, content)

    def test_add_and_list(self):
        self._add()
        notes = self.s.daily_notes("u")
        self.assertEqual(len(notes), 1)
        self.assertIn("یادداشت", notes[0]["content"])

    def test_multiple_notes_per_day(self):
        self._add(content="صبح")
        self._add(content="عصر")
        notes = self.s.daily_notes("u")
        self.assertEqual(len(notes), 2)

    def test_delete_removes_note(self):
        n = self._add()
        ok = self.s.delete_daily_note("u", n["id"])
        self.assertTrue(ok)
        self.assertEqual(len(self.s.daily_notes("u")), 0)

    def test_delete_only_own_note(self):
        n = self._add(user="alice")
        # bob cannot delete alice's note
        ok = self.s.delete_daily_note("bob", n["id"])
        self.assertFalse(ok)
        self.assertEqual(len(self.s.daily_notes("alice")), 1)

    def test_empty_note_rejected(self):
        with self.assertRaises(ValueError):
            self.s.add_daily_note("u", "   ")

    def test_isolation_between_users(self):
        self._add(user="alice", content="alice note")
        self._add(user="bob", content="bob note")
        self.assertEqual(len(self.s.daily_notes("alice")), 1)
        self.assertEqual(len(self.s.daily_notes("bob")), 1)


class TestNoteToRagSync(unittest.TestCase):
    def setUp(self):
        self._d = tempfile.mkdtemp()
        self.s = Store(os.path.join(self._d, "x.sqlite"))

    def test_sync_adds_chunk(self):
        from hypno.daily_sync import sync_notes_to_rag
        self.s.add_daily_note("u", "امروز تمرین تنفس پنج دقیقه انجام دادم و خیلی آرام شدم.")
        notes = self.s.recent_daily_notes(1.5)
        added = sync_notes_to_rag(self.s, notes)
        self.assertEqual(added, 1)
        self.assertTrue(self.s.has_research_source("local://daily-note/1"))

    def test_sync_is_idempotent(self):
        from hypno.daily_sync import sync_notes_to_rag
        self.s.add_daily_note("u", "تمرین تنفس امروز خوب بود.")
        notes = self.s.recent_daily_notes(1.5)
        first = sync_notes_to_rag(self.s, notes)
        second = sync_notes_to_rag(self.s, notes)
        self.assertEqual(first, 1)
        self.assertEqual(second, 0)  # already synced

    def test_short_note_is_padded(self):
        from hypno.daily_sync import sync_notes_to_rag
        # Short notes (< 40 chars) are padded with their day so they still
        # meet add_research's minimum and become findable chunks.
        self.s.add_daily_note("u", "کوتاه")
        notes = self.s.recent_daily_notes(1.5)
        added = sync_notes_to_rag(self.s, notes)
        self.assertEqual(added, 1)  # padded, not skipped

    def test_delete_removes_chunk_too(self):
        from hypno.daily_sync import sync_notes_to_rag
        n = self.s.add_daily_note("u", "یادداشت طولانی برای تست حذف از RAG.")
        notes = self.s.recent_daily_notes(1.5)
        sync_notes_to_rag(self.s, notes)
        self.assertTrue(self.s.has_research_source(f"local://daily-note/{n['id']}"))
        # delete the note + its chunk
        self.s.delete_daily_note("u", n["id"])
        self.s.delete_research_by_source(f"local://daily-note/{n['id']}")
        self.assertFalse(self.s.has_research_source(f"local://daily-note/{n['id']}"))


if __name__ == "__main__":
    unittest.main()
