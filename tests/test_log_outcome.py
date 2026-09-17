"""log_outcome as a thin writer of painting_call_log. Tests first, per §5.

The handoff decision this file encodes: `painting_call_log` is canonical, one
row per call, append-only, and `log_outcome` is the only thing that writes it.
Everything else about the old tool — the fuzzy name lookup, the batch file,
the CLI — survives; only the destination changes.

Four decisions were settled before these tests were written, and each one is
asserted here rather than left to a docstring:

  1. Two vocabularies, not one. The tool speaks twelve descriptive codes
     (`no_answer`, `interested`); the table speaks eight short ones
     (`N`, `J`). `OUTCOME_MAP` translates. Three of the twelve —
     `meeting_set`, `quote_sent`, `won` — are NOT call outcomes at all: they
     are funnel stages that happen to have been typed into an outcome field.
     They are refused with an explanation, not silently mapped to something
     close, because "close" here means recording a meeting as a phone call.

  2. Idempotency beats auto-increment. `attempt_no` is derived from history
     exactly once — when the first row for that account on that date is
     written. A second run finds the date already taken and does nothing, so
     there is no second derivation and no second row. Deriving `MAX+1` on
     every run, which is the obvious implementation, makes every run unique
     and idempotency unreachable. A genuinely new call on a day already
     recorded is an explicit `--new-attempt`.

  3. Idempotency is semantic, not textual. The ten calls already in the table
     carry hand-written ids (`lead:call:sarastrata-20260914-1`) that no
     function can derive from `lead:acct:sara-strata`. The duplicate check is
     therefore on `(account_id, date(called_at))`, which covers those ten;
     checking a generated `call_id` string would quietly write an eleventh row
     for a call that is already recorded.

  4. One writer, one table. `log_outcome` does not touch
     `painting_b2b_accounts` at all — not `stage`, not `notes`, not
     `next_action`. Derived state is what `v_account_last_call` is for.
     `TestSingleWriter` asserts the accounts row is unchanged byte for byte.

Fixture note: the canonical table's DDL lives in `001_call_log.sql`, which is
untracked — it exists in Elaheh's working tree and in no commit. The DDL is
therefore embedded here so the suite runs anywhere, and
`test_embedded_ddl_matches_the_migration` compares the two whenever the real
file is present, so the copy cannot drift unnoticed.
"""

from __future__ import annotations

import importlib.util
import os
import sqlite3
import unittest
from pathlib import Path

from ofn.adapters.lead_store import LeadStore
from tests.tmpdir import temp_dir

ROOT = Path(__file__).resolve().parent.parent
NOW = "2026-09-17T10:30:00"
TODAY = "2026-09-17"


def _table_columns(sql: str) -> list[str]:
    """Column names of the painting_call_log CREATE TABLE in `sql`.

    Deliberately literal rather than clever: take the table block only (the
    file also holds indexes and a view), then the first word of each line that
    starts a column definition. A constraint or comment line is skipped, and
    nesting depth keeps the CHECK(...) lists from being mistaken for columns.
    """
    body = sql.split("painting_call_log", 1)[1].split("(", 1)[1]
    columns: list[str] = []
    depth = 1
    for line in body.splitlines():
        stripped = line.strip()
        if depth == 1 and stripped and not stripped.startswith(("--", ")")):
            word = stripped.split()[0]
            if word.isidentifier() and word.upper() not in {
                    "CHECK", "FOREIGN", "PRIMARY", "UNIQUE", "CONSTRAINT"}:
                columns.append(word.lower())
        depth += line.count("(") - line.count(")")
        if depth <= 0:
            break
    return sorted(columns)


def _load_tool():
    """Import tools/log_outcome.py by path — it is a script, not a package."""
    spec = importlib.util.spec_from_file_location(
        "log_outcome_under_test", ROOT / "tools" / "log_outcome.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


log_outcome = _load_tool()


# The canonical table, copied from 001_call_log.sql. Kept in sync by
# test_embedded_ddl_matches_the_migration.
CALL_LOG_DDL = """
CREATE TABLE IF NOT EXISTS painting_call_log (
    call_id        TEXT PRIMARY KEY,
    tenant_id      TEXT NOT NULL DEFAULT 'lead',
    account_id     TEXT NOT NULL,

    called_at      TEXT NOT NULL,
    call_window    TEXT NOT NULL DEFAULT '',
    caller         TEXT NOT NULL DEFAULT 'ari',

    channel        TEXT NOT NULL DEFAULT 'mobile'
                   CHECK (channel IN ('mobile','office','email','other')),
    number_called  TEXT NOT NULL DEFAULT '',
    person_called  TEXT NOT NULL DEFAULT '',

    outcome_code   TEXT NOT NULL
                   CHECK (outcome_code IN
                     ('J','JN','M','N','E','Q','WRONG_SEGMENT','OPS_FAIL')),
    outcome_note   TEXT NOT NULL DEFAULT '',
    loss_reason    TEXT NOT NULL DEFAULT '',

    next_action    TEXT NOT NULL DEFAULT '',
    next_action_at TEXT NOT NULL DEFAULT '',
    recall_after   TEXT NOT NULL DEFAULT '',

    attempt_no     INTEGER NOT NULL DEFAULT 1,
    created_at     TEXT NOT NULL,

    FOREIGN KEY (account_id) REFERENCES painting_b2b_accounts(account_id)
);

CREATE VIEW IF NOT EXISTS v_account_last_call AS
SELECT
    c.account_id,
    c.tenant_id,
    c.called_at        AS last_called_at,
    c.outcome_code     AS last_outcome,
    c.outcome_note     AS last_note,
    c.next_action,
    c.next_action_at,
    c.recall_after,
    (SELECT COUNT(*) FROM painting_call_log x
      WHERE x.account_id = c.account_id
        AND x.tenant_id  = c.tenant_id) AS attempts
FROM painting_call_log c
WHERE c.called_at = (
    SELECT MAX(x.called_at) FROM painting_call_log x
     WHERE x.account_id = c.account_id
       AND x.tenant_id  = c.tenant_id
);
"""

# Ari's real first ten, as (call_id, account_id, outcome_code). The ids are
# the hand-written ones — that is the point of keeping them here.
SEEDED_TEN = (
    ("lead:call:dynamic-20260914-1", "lead:acct:dynamic-property-services-pica-group", "N"),
    ("lead:call:jamesons-20260914-1", "lead:acct:jamesons-strata-management", "N"),
    ("lead:call:ibproperty-20260914-1", "lead:acct:ib-property", "N"),
    ("lead:call:bcs-20260914-1", "lead:acct:bcs-strata-sydney-pica-group", "N"),
    ("lead:call:alldis-20260914-1", "lead:acct:alldis-and-cox", "N"),
    ("lead:call:esr-20260914-1", "lead:acct:esr-group", "N"),
    ("lead:call:sarastrata-20260914-1", "lead:acct:sara-strata", "E"),
    ("lead:call:onestrata-20260914-1", "lead:acct:one-strata-managers", "OPS_FAIL"),
    ("lead:call:talentweb-20260914-1", "lead:acct:talentweb-property-donny-mudiasa", "WRONG_SEGMENT"),
    ("lead:call:sopa-20260914-1", "lead:acct:sydney-olympic-park-authority", "N"),
)

ACCOUNTS = (
    ("Sara Strata", "lead:acct:sara-strata"),
    ("IB Property", "lead:acct:ib-property"),
    ("ESR Group", "lead:acct:esr-group"),
    # Never called. The attempt-number and idempotency tests need an account
    # with no history, or they end up asserting facts about the seed.
    ("Bright and Duggan Group", "lead:acct:bright-and-duggan-group"),
)

CLEAN = "Bright and Duggan Group"
CLEAN_ID = "lead:acct:bright-and-duggan-group"


class _Base(unittest.TestCase):
    def setUp(self):
        d = temp_dir(self)
        self.db = os.path.join(d, "painting.sqlite")

        # LeadStore builds painting_b2b_accounts and everything else it owns.
        store = LeadStore(self.db)
        for name, _aid in ACCOUNTS:
            store.create_account("lead", {"business_name": name,
                                          "segment": "strata"}, now_iso=NOW)
        store.close()

        conn = sqlite3.connect(self.db)
        conn.executescript(CALL_LOG_DDL)
        for call_id, account_id, code in SEEDED_TEN:
            conn.execute(
                "INSERT INTO painting_call_log (call_id, tenant_id, account_id,"
                " called_at, caller, outcome_code, attempt_no, created_at)"
                " VALUES (?,'lead',?,?,'ari',?,1,?)",
                (call_id, account_id, "2026-09-14T15:00:00", code,
                 "2026-09-14T15:00:00"))
        conn.commit()
        conn.close()

    # ── helpers ────────────────────────────────────────────────────────────
    def rows(self, account_id=None):
        conn = sqlite3.connect(self.db)
        conn.row_factory = sqlite3.Row
        sql = "SELECT * FROM painting_call_log"
        args = ()
        if account_id:
            sql += " WHERE account_id = ?"
            args = (account_id,)
        sql += " ORDER BY called_at, attempt_no"
        out = [dict(r) for r in conn.execute(sql, args)]
        conn.close()
        return out

    def accounts_snapshot(self):
        conn = sqlite3.connect(self.db)
        conn.row_factory = sqlite3.Row
        out = [dict(r) for r in
               conn.execute("SELECT * FROM painting_b2b_accounts ORDER BY account_id")]
        conn.close()
        return out

    def run_tool(self, name=CLEAN, code="interested", note="", **kw):
        kw.setdefault("now", NOW)
        return log_outcome.log_outcome(self.db, name, code, note, **kw)


# ── §5.1 — one run, one canonical event ─────────────────────────────────────

class TestSingleCanonicalEvent(_Base):
    def test_one_run_writes_exactly_one_row(self):
        before = len(self.rows())
        res = self.run_tool()
        self.assertTrue(res["ok"], res)
        self.assertTrue(res["written"])
        self.assertEqual(len(self.rows()), before + 1)

    def test_all_eight_contract_fields_are_mapped(self):
        """The §4 contract named eight fields. Each one lands in its column —
        `next_action_at` is optional by nature (five of the real ten leave it
        empty), so it is asserted as settable rather than as always present."""
        self.run_tool(code="email_requested", note="Asked for details by email",
                      next_action="Send the intro email",
                      follow_up_at="2026-09-18", caller="ari")
        row = self.rows(CLEAN_ID)[-1]
        self.assertEqual(row["account_id"], CLEAN_ID)                  # lead_id
        self.assertEqual(row["called_at"], NOW)                        # occurred_at
        self.assertEqual(row["outcome_code"], "E")                     # outcome_code
        self.assertEqual(row["outcome_note"],
                         "Asked for details by email")                 # notes
        self.assertEqual(row["next_action"], "Send the intro email")   # next_action
        self.assertEqual(row["next_action_at"], "2026-09-18")          # follow_up_at
        self.assertEqual(row["attempt_no"], 1)                         # attempt_number
        self.assertEqual(row["caller"], "ari")                         # recorded_by

    def test_required_columns_are_never_left_blank(self):
        self.run_tool()
        row = self.rows(CLEAN_ID)[-1]
        for column in ("call_id", "account_id", "called_at", "outcome_code",
                       "caller", "created_at"):
            self.assertTrue(str(row[column]).strip(),
                            f"{column} was written blank")

    def test_unknown_business_name_writes_nothing(self):
        before = self.rows()
        res = self.run_tool(name="No Such Company Pty Ltd")
        self.assertFalse(res["ok"])
        self.assertEqual(self.rows(), before)


# ── §5.7 — tenant ───────────────────────────────────────────────────────────

class TestTenantCarried(_Base):
    def test_every_written_row_is_tenant_lead(self):
        self.run_tool()
        for row in self.rows():
            self.assertEqual(row["tenant_id"], "lead")


# ── §5.6 — the two vocabularies ─────────────────────────────────────────────

class TestOutcomeVocabulary(_Base):
    CANONICAL = ("J", "JN", "M", "N", "E", "Q", "WRONG_SEGMENT", "OPS_FAIL")

    def test_the_agreed_mapping(self):
        self.assertEqual(log_outcome.OUTCOME_MAP, {
            "no_answer": "N",
            "voicemail": "M",
            "gatekeeper": "M",
            "email_requested": "E",
            "rejected": "JN",
            "interested": "J",
            "net_dropped": "Q",
            "callback": "J",
            "lost": "JN",
        })

    def test_every_mapped_value_survives_the_check_constraint(self):
        for descriptive, canonical in log_outcome.OUTCOME_MAP.items():
            with self.subTest(code=descriptive):
                self.assertIn(canonical, self.CANONICAL)

    def test_each_descriptive_code_writes_its_canonical_form(self):
        for descriptive, canonical in log_outcome.OUTCOME_MAP.items():
            with self.subTest(code=descriptive):
                res = self.run_tool(code=descriptive, new_attempt=True)
                self.assertTrue(res["ok"], res)
                self.assertEqual(self.rows(CLEAN_ID)[-1]["outcome_code"],
                                 canonical)

    def test_an_invalid_code_is_refused_and_writes_nothing(self):
        before = self.rows()
        res = self.run_tool(code="had_a_nice_chat")
        self.assertFalse(res["ok"])
        self.assertEqual(self.rows(), before)

    def test_stage_words_are_refused_with_an_explanation(self):
        """`meeting_set`, `quote_sent` and `won` describe where the lead is in
        the funnel, not what happened on a phone call. Mapping them to the
        nearest outcome would record a meeting as a call."""
        for word in ("meeting_set", "quote_sent", "won"):
            with self.subTest(code=word):
                before = self.rows()
                res = self.run_tool(code=word)
                self.assertFalse(res["ok"])
                self.assertIn("stage", (res.get("error") or "").lower())
                self.assertEqual(self.rows(), before)

    def test_stage_words_are_not_in_the_outcome_map(self):
        for word in ("meeting_set", "quote_sent", "won"):
            self.assertNotIn(word, log_outcome.OUTCOME_MAP)
            self.assertIn(word, log_outcome.STAGE_NOT_OUTCOME)


# ── §5.2 / §4.4 — idempotency ───────────────────────────────────────────────

class TestIdempotent(_Base):
    def test_the_same_call_logged_twice_is_one_row(self):
        first = self.run_tool()
        second = self.run_tool()
        self.assertTrue(first["written"])
        self.assertFalse(second["written"],
                         "a repeat run wrote a second row")
        self.assertTrue(second["ok"], "a repeat should be a no-op, not an error")
        self.assertEqual(len(self.rows(CLEAN_ID)), 1)

    def test_a_repeat_does_not_rewrite_the_first_row(self):
        self.run_tool(note="what he actually said")
        before = self.rows(CLEAN_ID)
        self.run_tool(note="a different note, same call")
        self.assertEqual(self.rows(CLEAN_ID), before)

    def test_idempotency_is_semantic_not_textual(self):
        """The seeded ten carry hand-written ids. Re-logging one of those calls
        must be recognised as already recorded even though the tool would
        generate a different call_id string for it."""
        generated = log_outcome.call_id_for("lead:acct:sara-strata",
                                            "2026-09-14", 1)
        self.assertNotEqual(generated, "lead:call:sarastrata-20260914-1",
                            "fixture no longer exercises the id mismatch")
        before = self.rows()
        res = self.run_tool(name="Sara Strata", code="email_requested",
                            now="2026-09-14T16:20:00")
        self.assertFalse(res["written"],
                         "wrote an eleventh row for a call already in the log")
        self.assertEqual(self.rows(), before)


# ── §5.5 / §4.1 — append-only ───────────────────────────────────────────────

class TestAppendOnly(_Base):
    def test_new_attempt_adds_a_row_and_leaves_the_old_one_alone(self):
        self.run_tool(code="no_answer")
        first = self.rows(CLEAN_ID)
        res = self.run_tool(code="interested", new_attempt=True)
        self.assertTrue(res["written"])
        after = self.rows(CLEAN_ID)
        self.assertEqual(len(after), len(first) + 1)
        self.assertEqual(after[:len(first)], first,
                         "an earlier attempt was modified")

    def test_new_attempt_increments_the_attempt_number(self):
        self.run_tool(code="no_answer")
        self.run_tool(code="no_answer", new_attempt=True)
        attempts = [r["attempt_no"] for r in self.rows(CLEAN_ID)]
        self.assertEqual(attempts, [1, 2])

    def test_the_attempt_number_advances_once_and_then_stops(self):
        """Sara already has attempt 1 from the 14th. A call today is attempt 2
        — and stays attempt 2 however many times it is logged.

        This is the resolution of the §4.4-vs-§5.5 conflict. The attempt
        number is derived from history exactly once, when the day's first row
        is written; afterwards the day is taken, so a repeat has nothing to
        derive and nothing to add. Deriving it on every run is what would make
        idempotency impossible.
        """
        self.run_tool(name="Sara Strata")
        self.run_tool(name="Sara Strata")
        self.run_tool(name="Sara Strata")
        self.assertEqual([r["attempt_no"] for r in
                          self.rows("lead:acct:sara-strata")], [1, 2])

    def test_nothing_is_ever_updated_or_deleted(self):
        """Structural: the tool contains no UPDATE or DELETE against the log."""
        source = (ROOT / "tools" / "log_outcome.py").read_text(encoding="utf-8")
        upper = source.upper()
        self.assertNotIn("UPDATE PAINTING_CALL_LOG", upper)
        self.assertNotIn("DELETE FROM PAINTING_CALL_LOG", upper)


# ── §5.3 — the existing ten ─────────────────────────────────────────────────

class TestPreservesTheExistingTen(_Base):
    def test_the_ten_are_untouched_by_a_new_write(self):
        before = {r["call_id"]: r for r in self.rows()}
        self.run_tool(code="interested", note="new call, new row")
        after = {r["call_id"]: r for r in self.rows()}
        for call_id, _account, _code in SEEDED_TEN:
            self.assertIn(call_id, after, f"{call_id} disappeared")
            self.assertEqual(after[call_id], before[call_id],
                             f"{call_id} was modified")

    def test_a_failed_run_leaves_the_table_exactly_as_it_was(self):
        before = self.rows()
        self.run_tool(code="not_a_real_code")
        self.run_tool(name="Nobody Ltd")
        self.run_tool(code="won")
        self.assertEqual(self.rows(), before)


# ── §5.4 / handoff §4.3 — one writer ────────────────────────────────────────

class TestSingleWriter(_Base):
    def test_the_accounts_table_is_not_touched(self):
        """Not stage, not notes, not next_action. If derived state is wanted,
        it is read from v_account_last_call — deriving and writing are
        different jobs and only one of them belongs in this tool."""
        before = self.accounts_snapshot()
        self.run_tool(code="interested", note="Very keen")
        self.assertEqual(self.accounts_snapshot(), before)

    def test_the_tool_never_names_the_accounts_table_in_a_write(self):
        source = (ROOT / "tools" / "log_outcome.py").read_text(encoding="utf-8")
        upper = source.upper()
        self.assertNotIn("UPDATE PAINTING_B2B_ACCOUNTS", upper)
        self.assertNotIn("INSERT INTO PAINTING_B2B_ACCOUNTS", upper)

    def test_derived_state_comes_from_the_view(self):
        self.run_tool(name="Sara Strata", code="interested", note="Very keen",
                      next_action="Send proposal")
        conn = sqlite3.connect(self.db)
        conn.row_factory = sqlite3.Row
        row = dict(conn.execute(
            "SELECT * FROM v_account_last_call WHERE account_id = ?",
            ("lead:acct:sara-strata",)).fetchone())
        conn.close()
        self.assertEqual(row["last_outcome"], "J")
        self.assertEqual(row["last_note"], "Very keen")
        self.assertEqual(row["next_action"], "Send proposal")
        self.assertEqual(row["attempts"], 2)


# ── the CLI survives (§6.3) ─────────────────────────────────────────────────

class TestCliPreserved(_Base):
    def test_codes_listing_covers_both_vocabularies(self):
        listing = log_outcome.codes_listing()
        for descriptive, canonical in log_outcome.OUTCOME_MAP.items():
            self.assertIn(descriptive, listing)
            self.assertIn(canonical, listing)

    def test_history_reads_the_call_log_not_free_text_notes(self):
        history = log_outcome.history(self.db)
        self.assertEqual(len(history), len(SEEDED_TEN))
        self.assertIn("outcome_code", history[0])

    def test_batch_file_still_works(self):
        path = os.path.join(os.path.dirname(self.db), "outcomes.txt")
        Path(path).write_text(
            "# a comment line\n"
            "Sara Strata | interested | Very keen\n"
            "IB Property | no_answer\n"
            "Nobody Ltd | no_answer\n",
            encoding="utf-8")
        stats = log_outcome.run_batch(self.db, path, now=NOW)
        self.assertEqual(stats["written"], 2)
        self.assertEqual(stats["failed"], 1)


# ── fixture integrity ───────────────────────────────────────────────────────

class TestFixtureMatchesReality(unittest.TestCase):
    def test_embedded_ddl_matches_the_migration(self):
        """001_call_log.sql is untracked, so the DDL is embedded above. When
        the real file IS present, the two must agree — otherwise the suite
        would go on passing against a table shape that no longer exists."""
        migration = ROOT / "001_call_log.sql"
        if not migration.exists():
            self.skipTest("001_call_log.sql is untracked and not present here")
        real = migration.read_text(encoding="utf-8")
        self.assertEqual(_table_columns(CALL_LOG_DDL), _table_columns(real),
                         "embedded DDL has drifted from 001_call_log.sql")


if __name__ == "__main__":
    unittest.main()
