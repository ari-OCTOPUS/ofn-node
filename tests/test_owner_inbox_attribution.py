#!/usr/bin/env python3
"""Regression tests: a customer email must never be consumed as an owner vote.

Context (board 138, 2026-09-18). Two channels write into one spool file,
`state/revenue-drive/tg-inbox.jsonl`:

  * Telegram owner updates  -> carry `chat` (the owner's id)
  * customer email replies  -> `kind=REPLY_DETECTED`, no `chat` field at all

`owner_reply.tg_get()` turns rows from that file into owner decisions. Two
defects made that unsafe:

  1. the allowlist was used raw: `chat_allow.split(",")`. A trailing comma in
     secrets.env produces an empty entry, and `str(d.get("chat","")) in [""]`
     is True for every chat-less row — so all twelve customer emails would have
     been read as owner votes;
  2. the cursor was documented as a set of consumed row HASHES, but the writer
     still emitted an integer line index (`str(kept)`), so every run fell back
     to the index path — the exact mechanism that had already swallowed a real
     owner vote.

Both are covered below. The tests run against the patched module itself, not a
re-implementation.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

MODULE = Path(__file__).resolve().parent.parent / "state" / "revenue-drive" / "owner_reply.py"
OWNER = "5551610"


def load_module(tmp: Path):
    """Import owner_reply with its state paths redirected into a temp dir."""
    spec = importlib.util.spec_from_file_location("owner_reply_under_test", MODULE)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    mod.ROOT = tmp
    mod.INBOX = tmp / "tg-inbox.jsonl"
    mod.CURSOR = tmp / "tg-inbox-cursor.txt"
    return mod


def owner_row(text: str, at: str = "2026-09-18T00:00:00Z") -> dict:
    return {"chat": OWNER, "text": text, "at": at, "kind": "callback", "lane": "MONEY"}


def email_row(uid: str = "42") -> dict:
    """A customer email reply: no chat field, exactly as the live spool carries."""
    return {"kind": "REPLY_DETECTED", "uid": uid, "subject": "which building?",
            "snippet": "redacted", "route_reason": "imap", "at": "2026-09-18T00:00:01Z"}


def write_spool(path: Path, rows: list[dict]) -> None:
    path.write_text("".join(json.dumps(r, sort_keys=True) + "\n" for r in rows), encoding="utf-8")


class TestAttribution(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)
        self.mod = load_module(self.dir)

    def tearDown(self):
        self.tmp.cleanup()

    def test_customer_email_is_never_an_owner_message(self):
        write_spool(self.mod.INBOX, [email_row(), owner_row("go")])
        _, msgs = self.mod.tg_get("tok", OWNER)
        self.assertEqual(len(msgs), 1)
        self.assertEqual(msgs[0]["text"], "go")
        self.assertEqual(msgs[0]["chat"], OWNER)

    def test_email_only_spool_yields_nothing(self):
        write_spool(self.mod.INBOX, [email_row("1"), email_row("2"), email_row("3")])
        _, msgs = self.mod.tg_get("tok", OWNER)
        self.assertEqual(msgs, [])

    def test_empty_allowlist_entry_cannot_admit_email(self):
        """The hazard: chat_allow='<owner>,' used to admit every chat-less row."""
        write_spool(self.mod.INBOX, [email_row(), owner_row("go")])
        _, msgs = self.mod.tg_get("tok", f"{OWNER},")
        self.assertEqual(len(msgs), 1)
        self.assertEqual(msgs[0]["text"], "go")

    def test_allowlist_of_only_empties_yields_nothing(self):
        write_spool(self.mod.INBOX, [email_row(), owner_row("go")])
        for allow in ("", ",", " , "):
            _, msgs = self.mod.tg_get("tok", allow)
            self.assertEqual(msgs, [], f"allow={allow!r} admitted {msgs}")

    def test_foreign_chat_is_ignored(self):
        write_spool(self.mod.INBOX, [{"chat": "999999", "text": "hi", "at": "x", "kind": "message"}])
        _, msgs = self.mod.tg_get("tok", OWNER)
        self.assertEqual(msgs, [])


class TestCursorPersistence(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)
        self.mod = load_module(self.dir)

    def tearDown(self):
        self.tmp.cleanup()

    def test_cursor_is_persisted_as_hashes_not_an_index(self):
        write_spool(self.mod.INBOX, [owner_row("go", at="2026-09-18T00:00:00Z")])
        self.mod.tg_get("tok", OWNER)
        raw = self.mod.CURSOR.read_text(encoding="utf-8").strip()
        self.assertTrue(raw.startswith("{"), f"cursor is not the v4 hash form: {raw!r}")
        payload = json.loads(raw)
        self.assertEqual(payload.get("v"), 4)
        expected = hashlib.sha256(
            (json.dumps(owner_row("go", at="2026-09-18T00:00:00Z"), sort_keys=True)).encode("utf-8")
        ).hexdigest()[:16]
        self.assertIn(expected, payload["hashes"])

    def test_message_is_not_returned_twice(self):
        write_spool(self.mod.INBOX, [owner_row("go")])
        _, first = self.mod.tg_get("tok", OWNER)
        _, second = self.mod.tg_get("tok", OWNER)
        self.assertEqual(len(first), 1)
        self.assertEqual(second, [])

    def test_rewritten_spool_does_not_swallow_a_new_owner_vote(self):
        """The original failure: a shorter/rewritten spool hid a genuinely new vote."""
        write_spool(self.mod.INBOX, [owner_row("old-1"), owner_row("old-2"), owner_row("old-3")])
        self.mod.tg_get("tok", OWNER)
        # The spool is rewritten: old rows gone, a brand new owner vote present.
        write_spool(self.mod.INBOX, [owner_row("brand-new-vote")])
        _, msgs = self.mod.tg_get("tok", OWNER)
        self.assertEqual([m["text"] for m in msgs], ["brand-new-vote"])

    def test_legacy_integer_cursor_still_upgrades(self):
        write_spool(self.mod.INBOX, [owner_row("a"), owner_row("b")])
        self.mod.CURSOR.write_text("2", encoding="utf-8")  # legacy index form
        _, msgs = self.mod.tg_get("tok", OWNER)
        self.assertEqual(msgs, [])
        raw = self.mod.CURSOR.read_text(encoding="utf-8").strip()
        self.assertTrue(raw.startswith("{"))
        self.assertEqual(json.loads(raw)["v"], 4)

    def test_malformed_line_does_not_break_the_round(self):
        self.mod.INBOX.write_text(
            json.dumps(owner_row("go")) + "\n" + "{not json at all}\n", encoding="utf-8"
        )
        _, msgs = self.mod.tg_get("tok", OWNER)
        self.assertEqual([m["text"] for m in msgs], ["go"])


if __name__ == "__main__":
    unittest.main()
