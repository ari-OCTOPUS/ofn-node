"""J4 — the follow-up reader over `painting_call_log`. Tests first, per §5.

WHY THIS EXISTS: Ari called ten accounts. Seven answered nothing (`N`) and not
one of them carries a `next_action_at`, so no queue holds them and nothing ever
reminds him to dial again. The data to fix that is already in the call log —
`called_at`, `outcome_code`, `attempt_no`. Only the reader was missing.

WHAT IT MUST NOT DO: write. `next_action_at` currently means "a human decided
this". The moment a machine writes a guessed `+3 days` into that column, Ari's
commitment and the system's inference become indistinguishable, and
`v_account_last_call` starts serving the guess to the digest as fact. So the
derived date is computed at read time and carried beside the stored one:
`due_at` + `source` ("recorded" | "implied"), with the raw `next_action_at`
passed through verbatim so the two can never be confused.

`today` is a parameter, never a clock, so "overdue" is a fixed fact in a test
and two reads in one request cannot straddle midnight.
"""

from __future__ import annotations

import hashlib
import os
import re
import sqlite3
import unittest
from pathlib import Path

from ofn.adapters.lead_store import LeadStore, followup_due_for_outcome

from tests.tmpdir import temp_dir

ROOT = Path(__file__).resolve().parent.parent
MIGRATION = ROOT / "migrations" / "20260914_call_log.sql"

TENANT = "lead"
TODAY = "2026-09-19"

# The real board's numbers: every one of Ari's first ten calls was logged at
# this timestamp, five days before TODAY. An `N` here implies 2026-09-17.
CALLED = "2026-09-14T15:00:00"
YESTERDAY_CALL = "2026-09-18T10:00:00"


def _apply_call_log(db_path: str) -> None:
    """Apply the tracked migration, rather than embedding a copy of its DDL.

    `painting_call_log` is not in `lead_store.SCHEMA`; it arrives only by this
    file, which no Python code path applies. A fourth hand-written copy of the
    DDL would be a fourth thing to drift.
    """
    conn = sqlite3.connect(db_path)
    try:
        conn.executescript(MIGRATION.read_text())
        conn.commit()
    finally:
        conn.close()


def _seed(db_path: str, rows: list[dict]) -> None:
    conn = sqlite3.connect(db_path)
    try:
        for i, r in enumerate(rows):
            tenant = r.get("tenant_id", TENANT)
            account_id = r["account_id"]
            conn.execute(
                "INSERT OR IGNORE INTO painting_b2b_accounts "
                "(account_id, tenant_id, segment, business_name, created_at, updated_at) "
                "VALUES (?, ?, 'strata', ?, ?, ?)",
                (account_id, tenant, r.get("business_name", account_id),
                 CALLED, CALLED))
            conn.execute(
                "INSERT INTO painting_call_log "
                "(call_id, tenant_id, account_id, called_at, outcome_code, "
                " outcome_note, next_action, next_action_at, recall_after, "
                " number_called, person_called, attempt_no, created_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (f"{tenant}:call:{i}", tenant, account_id,
                 r.get("called_at", CALLED), r["outcome_code"],
                 r.get("outcome_note", ""), r.get("next_action", ""),
                 r.get("next_action_at", ""), r.get("recall_after", ""),
                 r.get("number_called", ""), r.get("person_called", ""),
                 int(r.get("attempt_no", 1)), CALLED))
        conn.commit()
    finally:
        conn.close()


def _dump_hash(db_path: str) -> str:
    """A fingerprint of the whole logical database, for the read-only proof."""
    conn = sqlite3.connect(db_path)
    try:
        return hashlib.sha256(
            "\n".join(conn.iterdump()).encode()).hexdigest()
    finally:
        conn.close()


def _by_account(payload: dict) -> dict:
    return {r["account_id"]: r for r in payload["due"]}


class _Base(unittest.TestCase):
    """A store whose file carries the call log."""

    rows: list[dict] = []

    def setUp(self):
        self.dir = temp_dir(self)
        self.path = os.path.join(self.dir, "lead.sqlite")
        self.store = LeadStore(self.path)
        self.addCleanup(self.store.close)
        _apply_call_log(self.path)
        if self.rows:
            _seed(self.path, self.rows)


# ---------------------------------------------------------------------------
# §5.1 / §5.2 — the two accounts that already carry a human-set date
# ---------------------------------------------------------------------------

class TestRecordedDates(_Base):
    rows = [
        {"account_id": "lead:acct:sara-strata", "business_name": "Sara Strata",
         "outcome_code": "E", "next_action_at": "2026-09-15",
         "next_action": "SEND EMAIL — fact-only intro + capability."},
        {"account_id": "lead:acct:one-strata-managers",
         "business_name": "One Strata Managers", "outcome_code": "OPS_FAIL",
         "next_action_at": "2026-09-21",
         "next_action": "RE-CALL with pen/screen ready."},
    ]

    def test_overdue_recorded_date_is_found(self):
        """§5.1 — Sara: 2026-09-15 against TODAY is four days overdue."""
        rows = _by_account(self.store.call_followups_due(TENANT, TODAY))
        sara = rows["lead:acct:sara-strata"]
        self.assertEqual(sara["due_at"], "2026-09-15")
        self.assertEqual(sara["days_overdue"], 4)
        self.assertEqual(sara["source"], "recorded")
        self.assertEqual(sara["kind"], "followup")
        self.assertEqual(sara["last_outcome"], "E")
        self.assertEqual(sara["business_name"], "Sara Strata")
        self.assertEqual(sara["attempt_no"], 1)
        self.assertEqual(sara["next_action"],
                         "SEND EMAIL — fact-only intro + capability.")

    def test_future_date_stays_out(self):
        """§5.2 — One Strata is due 2026-09-21. It has not arrived."""
        rows = _by_account(self.store.call_followups_due(TENANT, TODAY))
        self.assertNotIn("lead:acct:one-strata-managers", rows)

    def test_the_boundary_day_is_due(self):
        """Due *today* is due — `<=`, not `<`. Ari acts on it this morning."""
        rows = _by_account(
            self.store.call_followups_due(TENANT, "2026-09-21"))
        self.assertEqual(rows["lead:acct:one-strata-managers"]["days_overdue"], 0)

    def test_today_is_a_parameter_not_a_clock(self):
        """§4.3 — the same store, two days, two answers. No hidden now()."""
        early = self.store.call_followups_due(TENANT, "2026-09-14")
        late = self.store.call_followups_due(TENANT, "2026-09-21")
        self.assertEqual(early["due"], [])
        self.assertEqual(len(late["due"]), 2)
        self.assertEqual(early["today"], "2026-09-14")


# ---------------------------------------------------------------------------
# §5.3 / §5.4 — the seven silent leads, which is the whole point
# ---------------------------------------------------------------------------

class TestImpliedFollowUps(_Base):
    rows = [
        {"account_id": "lead:acct:esr-group", "business_name": "ESR Group",
         "outcome_code": "N", "next_action": "retry in a different time window"},
        {"account_id": "lead:acct:fresh-call", "business_name": "Fresh Call",
         "outcome_code": "N", "called_at": YESTERDAY_CALL},
    ]

    def test_no_reply_without_a_date_becomes_due(self):
        """§5.3 — an `N` five days old implies called_at + 3 = 2026-09-17."""
        rows = _by_account(self.store.call_followups_due(TENANT, TODAY))
        esr = rows["lead:acct:esr-group"]
        self.assertEqual(esr["due_at"], "2026-09-17")
        self.assertEqual(esr["days_overdue"], 2)
        self.assertEqual(esr["source"], "implied")

    def test_the_stored_column_is_still_empty_in_the_payload(self):
        """The derived date never masquerades as the recorded one.

        `due_at` is what to act on; `next_action_at` stays exactly what the
        database holds — empty. This is the whole reason J4 does not write.
        """
        rows = _by_account(self.store.call_followups_due(TENANT, TODAY))
        self.assertEqual(rows["lead:acct:esr-group"]["next_action_at"], "")

    def test_a_fresh_no_reply_is_not_chased_yet(self):
        """§5.4 — called yesterday: +3 lands in the future, so not due."""
        rows = _by_account(self.store.call_followups_due(TENANT, TODAY))
        self.assertNotIn("lead:acct:fresh-call", rows)


class TestRecordedBeatsDerived(_Base):
    """A human date on an `N` wins over the rule. Ari outranks the default."""

    rows = [
        {"account_id": "lead:acct:decided", "business_name": "Decided",
         "outcome_code": "N", "next_action_at": "2026-09-19"},
    ]

    def test_human_date_wins_and_is_marked_recorded(self):
        rows = _by_account(self.store.call_followups_due(TENANT, TODAY))
        row = rows["lead:acct:decided"]
        self.assertEqual(row["due_at"], "2026-09-19")
        self.assertEqual(row["source"], "recorded")


class TestRecall(_Base):
    """`recall_after` is the long-horizon re-contact date, a separate bucket."""

    rows = [
        {"account_id": "lead:acct:later", "business_name": "Later",
         "outcome_code": "Q", "recall_after": "2026-09-18"},
    ]

    def test_recall_due_is_reported_as_its_own_kind(self):
        rows = _by_account(self.store.call_followups_due(TENANT, TODAY))
        row = rows["lead:acct:later"]
        self.assertEqual(row["kind"], "recall")
        self.assertEqual(row["due_at"], "2026-09-18")
        self.assertEqual(row["source"], "recorded")


class TestClosedOutcomeWithHumanDate(_Base):
    """D3 end-to-end: a decision Ari typed survives its own outcome code."""

    rows = [
        {"account_id": "lead:acct:talentweb", "business_name": "TalentWeb",
         "outcome_code": "WRONG_SEGMENT", "next_action_at": "2026-09-16",
         "next_action": "Possible referral channel later."},
    ]

    def test_a_wrong_segment_with_a_date_is_still_surfaced(self):
        rows = _by_account(self.store.call_followups_due(TENANT, TODAY))
        row = rows["lead:acct:talentweb"]
        self.assertEqual(row["due_at"], "2026-09-16")
        self.assertEqual(row["source"], "recorded")
        self.assertEqual(row["days_overdue"], 3)


class TestClosedOutcomeWithoutDate(_Base):
    """The other half: no date on a closed outcome means no queue entry."""

    rows = [
        {"account_id": "lead:acct:talentweb", "business_name": "TalentWeb",
         "outcome_code": "WRONG_SEGMENT"},
        {"account_id": "lead:acct:interested", "business_name": "Interested",
         "outcome_code": "J"},
    ]

    def test_closed_and_won_outcomes_stay_out_of_the_queue(self):
        payload = self.store.call_followups_due(TENANT, TODAY)
        self.assertEqual(payload["due"], [])


# ---------------------------------------------------------------------------
# §5.5 — the date rule as a pure function (D2: module-level, so `leadboard`
# can call this exact rule later instead of growing a second definition)
# ---------------------------------------------------------------------------

class TestDateRule(unittest.TestCase):

    def test_no_reply_is_three_days(self):
        self.assertEqual(
            followup_due_for_outcome("N", CALLED, ""),
            ("2026-09-17", "implied"))

    def test_voicemail_is_two_days(self):
        self.assertEqual(
            followup_due_for_outcome("M", CALLED, ""),
            ("2026-09-16", "implied"))

    def test_a_recorded_date_is_honoured_for_every_outcome(self):
        """The rule that resolves the §2.3 / D3 conflict.

        §2.3 said `JN`/`WRONG_SEGMENT`/`Q` never produce a follow-up. Read
        literally that also discards a date a human typed onto such a row —
        the exact thing D3 says is sacred. A written date is a decision, and
        an outcome code is not allowed to overrule a decision. So: a stored
        `next_action_at` wins for every outcome, without exception.
        """
        for code in ("N", "M", "E", "OPS_FAIL", "J", "JN", "WRONG_SEGMENT", "Q"):
            with self.subTest(code=code):
                self.assertEqual(
                    followup_due_for_outcome(code, CALLED, "2026-09-15"),
                    ("2026-09-15", "recorded"))

    def test_a_human_date_overrides_the_derived_one(self):
        """Even where a rule exists, the human's date is the one used."""
        self.assertEqual(
            followup_due_for_outcome("N", CALLED, "2026-09-30"),
            ("2026-09-30", "recorded"))

    def test_only_unanswered_calls_imply_a_follow_up_on_their_own(self):
        """With no stored date, only `N` and `M` mean "we did not get through,
        try again". For every other outcome an empty date is a decision too —
        Ari did not schedule one — so nothing is invented. `J` belongs here:
        an interested account has moved on to a meeting or a quote, and a
        cold-call queue is the wrong place to show it.
        """
        for code in ("E", "OPS_FAIL", "J", "JN", "WRONG_SEGMENT", "Q"):
            with self.subTest(code=code):
                self.assertIsNone(followup_due_for_outcome(code, CALLED, ""))

    def test_it_is_pure(self):
        """Same inputs, same answer, and it touches no database."""
        for _ in range(3):
            self.assertEqual(
                followup_due_for_outcome("N", CALLED, ""),
                ("2026-09-17", "implied"))

    def test_an_unreadable_timestamp_yields_nothing_rather_than_a_guess(self):
        self.assertIsNone(followup_due_for_outcome("N", "", ""))
        self.assertIsNone(followup_due_for_outcome("N", "not-a-date", ""))

    def test_an_unknown_code_yields_nothing(self):
        self.assertIsNone(followup_due_for_outcome("ZZZ", CALLED, ""))


# ---------------------------------------------------------------------------
# §5.6 / §5.7 — read-only, and tenant-scoped
# ---------------------------------------------------------------------------

class TestReadOnly(_Base):
    rows = [
        {"account_id": "lead:acct:esr-group", "outcome_code": "N"},
        {"account_id": "lead:acct:sara-strata", "outcome_code": "E",
         "next_action_at": "2026-09-15"},
    ]

    def test_reading_changes_nothing(self):
        """§5.6 — the database is byte-identical before and after the read."""
        before = _dump_hash(self.path)
        payload = self.store.call_followups_due(TENANT, TODAY)
        self.assertTrue(payload["due"])
        self.assertEqual(_dump_hash(self.path), before)


class TestTenantIsolation(_Base):
    rows = [
        {"account_id": "lead:acct:ours", "business_name": "Ours",
         "outcome_code": "N"},
        {"account_id": "other:acct:theirs", "business_name": "Theirs",
         "outcome_code": "N", "tenant_id": "other"},
    ]

    def test_another_tenants_call_never_appears(self):
        """§5.7 — every query is scoped; no cross-tenant leak."""
        rows = _by_account(self.store.call_followups_due(TENANT, TODAY))
        self.assertIn("lead:acct:ours", rows)
        self.assertNotIn("other:acct:theirs", rows)

    def test_the_other_tenant_sees_only_its_own(self):
        rows = _by_account(self.store.call_followups_due("other", TODAY))
        self.assertEqual(list(rows), ["other:acct:theirs"])


# ---------------------------------------------------------------------------
# §5.8 — a file the migration never reached
# ---------------------------------------------------------------------------

class TestGracefulDegrade(unittest.TestCase):

    def setUp(self):
        self.dir = temp_dir(self)
        self.path = os.path.join(self.dir, "lead.sqlite")
        self.store = LeadStore(self.path)
        self.addCleanup(self.store.close)

    def test_a_file_without_the_call_log_reports_unavailable(self):
        """§5.8 — `painting_call_log` is not in SCHEMA, so a fresh file lacks
        it. Say so; do not die. A panel draws other sections from this call."""
        payload = self.store.call_followups_due(TENANT, TODAY)
        self.assertEqual(payload["available"], False)
        self.assertEqual(payload["due"], [])

    def test_the_available_file_says_so(self):
        _apply_call_log(self.path)
        payload = self.store.call_followups_due(TENANT, TODAY)
        self.assertEqual(payload["available"], True)


# ---------------------------------------------------------------------------
# §5.9 / D3 — no raw contact detail in the structure
# ---------------------------------------------------------------------------

_EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+")
_PHONE = re.compile(r"(?:\+?61|0)[\d\s-]{8,}")
_ISO = re.compile(r"^\d{4}-\d{2}-\d{2}([T ]\d{2}:\d{2}(:\d{2})?)?$")


def _is_a_date(value: str) -> bool:
    """An ISO date is not a phone number, though `_PHONE` cannot tell.

    `2026-09-15` reads as a leading 0 followed by digits and hyphens, which is
    exactly the shape of an Australian mobile. Dates are recognised and
    excused here rather than by loosening the phone pattern, which would be
    the one change that could let a real number through unnoticed.
    """
    return bool(_ISO.match(value))

# `next_action` is Ari's own instruction to himself ("Confirm his email
# address") and is useless if stripped, so it is passed through verbatim and
# exempted here. Every other field is structure, and structure carries no PII.
_FREE_TEXT = {"next_action", "last_note"}


class TestTheDetectorItselfWorks(unittest.TestCase):
    """A PII assertion that cannot fail is worse than none — it reassures.

    The date exemption above is a hole cut in the phone pattern, so these pin
    that the hole is exactly date-shaped and nothing else fits through it.
    """

    def test_a_real_number_is_still_caught(self):
        for number in ("0412345678", "+61412345678", "0412 345 678"):
            with self.subTest(number=number):
                self.assertFalse(_is_a_date(number))
                self.assertIsNotNone(_PHONE.search(number))

    def test_a_real_address_is_still_caught(self):
        self.assertIsNotNone(_EMAIL.search("sara@example.test"))

    def test_only_dates_are_excused(self):
        for value in ("2026-09-15", "2026-09-14T15:00:00"):
            with self.subTest(value=value):
                self.assertTrue(_is_a_date(value))
        for value in ("implied", "recorded", "followup", ""):
            with self.subTest(value=value):
                self.assertFalse(_is_a_date(value))


class TestNoRawContact(_Base):
    rows = [
        {"account_id": "lead:acct:sara-strata", "business_name": "Sara Strata",
         "outcome_code": "E", "next_action_at": "2026-09-15",
         "next_action": "SEND EMAIL — confirm his email address.",
         "number_called": "0412345678",
         "person_called": "sara@example.test"},
    ]

    def test_the_dialled_number_is_not_in_the_payload(self):
        """§5.9 — the call log stores what was dialled. This reader is a
        queue, not a contact card, so it never carries the number out."""
        payload = self.store.call_followups_due(TENANT, TODAY)
        row = payload["due"][0]
        self.assertNotIn("number_called", row)
        self.assertNotIn("person_called", row)
        self.assertNotIn("0412345678", repr(payload))
        self.assertNotIn("sara@example.test", repr(payload))

    def test_structural_fields_hold_no_contact_pattern(self):
        """D3 — assert the shape, not just today's fixture. `leadboard`'s row
        (which carries a raw `mobile`) must never be copied into this one."""
        payload = self.store.call_followups_due(TENANT, TODAY)
        for row in payload["due"]:
            for key, value in row.items():
                if key in _FREE_TEXT or not isinstance(value, str):
                    continue
                with self.subTest(field=key):
                    self.assertIsNone(_EMAIL.search(value))
                    if not _is_a_date(value):
                        self.assertIsNone(_PHONE.search(value))


if __name__ == "__main__":
    unittest.main()
