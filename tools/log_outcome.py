#!/usr/bin/env python3
<<<<<<< HEAD
"""Log call outcome for a B2B account.

Records what happened when Ari called a company: updates stage,
appends timestamped outcome to notes, sets next_action.

Commercial purpose: every call result is captured so we know
conversion rates, which segments respond, and what to do next.

Usage:
    # Single outcome
    python tools/log_outcome.py "Strata Choice" no_answer
    python tools/log_outcome.py "IB Property" interested "Nick said send proposal"

    # Batch from file
    python tools/log_outcome.py --batch outcomes.txt

    # List valid outcome codes
    python tools/log_outcome.py --codes

    # Show all logged outcomes
    python tools/log_outcome.py --history
"""
import argparse
import re
=======
"""Log a call outcome as one canonical event in painting_call_log.

This tool used to keep its own record of what happened on a call: it set
`stage` on the account, appended a line of prose to `notes`, and wrote a
`next_action`. `painting_call_log` then arrived as the canonical, structured,
one-row-per-call history. Two independent writers of the same fact is how a
lead ends up with a follow-up that contradicts its own history, so this is now
a thin writer of the canonical table and nothing else.

What it does NOT do, deliberately:

  * It does not touch `painting_b2b_accounts`. Not `stage`, not `notes`, not
    `next_action`. Derived state — where a lead stands now — is read from the
    `v_account_last_call` view, which already exists for that purpose.
    Deriving state and recording an event are different jobs, and mixing them
    is the thing that went wrong.

  * It never modifies or removes a logged call. The table is append-only: a
    call that happened is a fact, and a fact does not get edited because a
    later call went differently.

Two vocabularies meet here, which is the part worth reading twice. This tool
speaks the descriptive codes Ari types (`no_answer`, `interested`); the table
speaks the short codes the analysis uses (`N`, `J`). `OUTCOME_MAP` translates
between them. Three words that used to be accepted — `meeting_set`,
`quote_sent`, `won` — are refused outright, because they are not outcomes of a
phone call at all: they are positions in the funnel. Mapping `won` onto the
nearest available outcome code would file a signed job as a conversation.

Idempotency is semantic rather than textual. The first ten calls carry
hand-written ids (`lead:call:sarastrata-20260914-1`) that cannot be derived
from `lead:acct:sara-strata`, so a generated-id check would look at those ten,
see no match, and write an eleventh row for a call already recorded. The check
is on `(account_id, date(called_at))` instead. The attempt number is derived
from history exactly once — when the day's first row is written — which is
what makes a repeat run a no-op instead of a new attempt.

Usage:
    python tools/log_outcome.py "Sara Strata" interested "Nick said send proposal"
    python tools/log_outcome.py "IB Property" no_answer --new-attempt
    python tools/log_outcome.py "Sara Strata" email_requested --follow-up 2026-09-18
    python tools/log_outcome.py --batch outcomes.txt
    python tools/log_outcome.py --codes
    python tools/log_outcome.py --history
"""
import argparse
>>>>>>> origin/main
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ofn.adapters.lead_store import LeadStore

<<<<<<< HEAD

# ---------------------------------------------------------------------------
# Outcome definitions
# ---------------------------------------------------------------------------

OUTCOMES = {
    "no_answer":        {"stage": "researched",  "next": "Retry in 2 days",          "label": "No answer"},
    "voicemail":        {"stage": "researched",  "next": "Retry in 2 days",          "label": "Voicemail left"},
    "gatekeeper":       {"stage": "researched",  "next": "Send email or retry",      "label": "Gatekeeper/receptionist"},
    "email_requested":  {"stage": "researched",  "next": "Send email within 24h",    "label": "Asked for email"},
    "net_dropped":      {"stage": None,         "next": "Retry ASAP (net issue)",    "label": "Call dropped (net)"},
    "rejected":         {"stage": "lost",   "next": "Review in 30 days",        "label": "Not interested"},
    "interested":       {"stage": "qualified",    "next": "Send proposal within 24h", "label": "Interested"},
    "callback":         {"stage": "researched",  "next": "Call back at agreed time",  "label": "Callback requested"},
    "meeting_set":      {"stage": "meeting",    "next": "Prepare for meeting",       "label": "Meeting set"},
    "quote_sent":       {"stage": "opportunity",     "next": "Follow up in 3 days",       "label": "Quote sent"},
    "won":              {"stage": "won",        "next": "Schedule job",              "label": "Won"},
    "lost":             {"stage": "lost",       "next": "Log reason, review later",  "label": "Lost"},
=======
TENANT = "lead"
TABLE = "painting_call_log"

# ---------------------------------------------------------------------------
# The two vocabularies
# ---------------------------------------------------------------------------

# Descriptive code (what Ari types) -> canonical code (what the table stores).
# Approved by Ari via Elaheh, 2026-09-17. `callback` maps to J because the call
# WAS answered and went well; the fact that a time was agreed belongs in the
# note, not in a code that would claim something the vocabulary cannot say.
OUTCOME_MAP = {
    "no_answer": "N",
    "voicemail": "M",
    "gatekeeper": "M",
    "email_requested": "E",
    "rejected": "JN",
    "interested": "J",
    "net_dropped": "Q",
    "callback": "J",
    "lost": "JN",
}

# Not call outcomes. These describe where the lead sits in the funnel, and the
# canonical vocabulary — designed for first contact — has no code for them. The
# honest answer is to refuse and say why, rather than to record a meeting as a
# phone call because `J` was the closest thing available.
STAGE_NOT_OUTCOME = {
    "meeting_set": "a meeting was agreed",
    "quote_sent": "a quote went out",
    "won": "the job was won",
}

# Default next action per descriptive code. A caller may override it, because
# the real entries are specific ("RE-CALL with pen/screen ready") and a generic
# default would be worse than the truth.
NEXT_ACTION = {
    "no_answer": "Retry in a different time window",
    "voicemail": "Retry in 2 days",
    "gatekeeper": "Send email or retry",
    "email_requested": "Send email within 24h",
    "rejected": "Review in 30 days",
    "interested": "Send proposal within 24h",
    "net_dropped": "Retry ASAP (net issue)",
    "callback": "Call back at agreed time",
    "lost": "Log reason, review later",
}

LABEL = {
    "no_answer": "No answer",
    "voicemail": "Voicemail left",
    "gatekeeper": "Gatekeeper/receptionist",
    "email_requested": "Asked for email",
    "rejected": "Not interested",
    "interested": "Interested",
    "net_dropped": "Call dropped (net)",
    "callback": "Callback requested",
    "lost": "Lost",
>>>>>>> origin/main
}


# ---------------------------------------------------------------------------
<<<<<<< HEAD
# Account lookup — fuzzy match by name
# ---------------------------------------------------------------------------

def find_account(store, name):
    """Find account by name. Case-insensitive, partial match."""
    accts = store.accounts("lead", limit=300)

    # Exact match (case-insensitive)
    exact = [a for a in accts
             if a["business_name"].lower() == name.lower()]
    if len(exact) == 1:
        return exact[0]

    # Partial match
    partial = [a for a in accts
               if name.lower() in a["business_name"].lower()]
=======
# Connection
# ---------------------------------------------------------------------------

def _connect(db_path):
    """Open the database with this board's durability policy.

    `synchronous = FULL` rather than NORMAL: under WAL, NORMAL lets a
    committed transaction roll back after a power cut, and a call outcome that
    silently un-happens is exactly the kind of loss this table exists to
    prevent.
    """
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA synchronous = FULL")
    return conn


# ---------------------------------------------------------------------------
# Identity and time
# ---------------------------------------------------------------------------

def call_id_for(account_id, occurred_date, attempt_no):
    """Stable id for one attempt on one account on one day.

    Derived entirely from the account, so it needs no nickname table. It will
    NOT match the hand-written ids on the first ten calls, which is why the
    duplicate check does not go through this function.
    """
    slug = str(account_id).split(":")[-1]
    compact = str(occurred_date).replace("-", "")
    return f"{TENANT}:call:{slug}:{compact}:{int(attempt_no)}"


def call_window_for(called_at):
    """morning / midday / afternoon, from the hour the call was made.

    A function of the timestamp, not a guess about it: if the hour is
    unreadable the window is left empty rather than invented.
    """
    try:
        hour = int(str(called_at)[11:13])
    except (ValueError, IndexError):
        return ""
    if hour < 12:
        return "morning"
    if hour < 14:
        return "midday"
    return "afternoon"


# ---------------------------------------------------------------------------
# Account lookup — fuzzy match by name, unchanged behaviour
# ---------------------------------------------------------------------------

def find_account(store, name):
    """Find one account by name. Case-insensitive, partial match.

    Returns the row, or None when the answer is ambiguous or absent — an
    ambiguous name must not resolve to whichever account happened to sort
    first, because the call would be filed against the wrong company.
    """
    accts = store.accounts(TENANT, limit=300)

    exact = [a for a in accts if a["business_name"].lower() == name.lower()]
    if len(exact) == 1:
        return exact[0]

    partial = [a for a in accts if name.lower() in a["business_name"].lower()]
>>>>>>> origin/main
    if len(partial) == 1:
        return partial[0]
    if len(partial) > 1:
        print(f"Multiple matches for '{name}':")
        for a in partial:
            print(f"  - {a['business_name']}")
        print("Be more specific.")
        return None

    print(f"No account found matching '{name}'")
    return None


# ---------------------------------------------------------------------------
<<<<<<< HEAD
# Log outcome
# ---------------------------------------------------------------------------

def log_outcome(db_path, business_name, outcome_code, note_text=""):
    """Record a call outcome for one account."""
    if outcome_code not in OUTCOMES:
        print(f"Unknown outcome: '{outcome_code}'")
        print(f"Valid codes: {', '.join(OUTCOMES.keys())}")
        return False

    outcome = OUTCOMES[outcome_code]
    store = LeadStore(db_path)
    acct = find_account(store, business_name)
    if not acct:
        return False

    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    old_notes = acct.get("notes", "") or ""

    # Build outcome line
    extra = f" — {note_text}" if note_text else ""
    outcome_line = f"OUTCOME [{now}]: {outcome['label']}{extra}."

    # Append to notes
    new_notes = f"{old_notes}\n{outcome_line}".strip()

    # Stage transition (None = don't change, e.g. net_dropped)
    new_stage = outcome["stage"] or acct.get("stage", "discovered")
    next_action = outcome["next"]

    # Direct SQL update
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute(
        """UPDATE painting_b2b_accounts
           SET stage = ?, notes = ?, next_action = ?
           WHERE business_name = ? AND tenant_id = 'lead'""",
        (new_stage, new_notes, next_action, acct["business_name"]),
    )
    if cur.rowcount == 0:
        print(f"  WARNING: no rows updated for '{acct['business_name']}'")
        conn.close()
        return False

    conn.commit()
    conn.close()

    print(f"  ✅ {acct['business_name']}: {outcome['label']} → stage={new_stage}, next={next_action}")
    return True
=======
# Validation
# ---------------------------------------------------------------------------

def canonical_code(descriptive):
    """Translate a descriptive code, or explain why it cannot be translated.

    Returns (canonical, error). Exactly one of the two is set.
    """
    if descriptive in STAGE_NOT_OUTCOME:
        meaning = STAGE_NOT_OUTCOME[descriptive]
        return None, (
            f"'{descriptive}' is a stage, not a call outcome — it says {meaning}, "
            f"which is where the lead now sits rather than what happened on the "
            f"phone. Log the call itself (e.g. 'interested'), and set the stage "
            f"through whatever owns stage; this tool only writes {TABLE}."
        )
    if descriptive not in OUTCOME_MAP:
        valid = ", ".join(sorted(OUTCOME_MAP))
        return None, f"Unknown outcome '{descriptive}'. Valid codes: {valid}"
    return OUTCOME_MAP[descriptive], None


# ---------------------------------------------------------------------------
# The writer
# ---------------------------------------------------------------------------

def log_outcome(db_path, business_name, outcome_code, note_text="", *,
                now=None, new_attempt=False, next_action=None,
                follow_up_at="", caller="ari", loss_reason="",
                person_called="", number_called="", channel="mobile"):
    """Record one call as one row. Returns a result dict, never raises on
    ordinary failure.

    Keys: ok (the request was valid and the log is in the state the caller
    asked for), written (a row was actually added), call_id, error.

    A repeat is `ok=True, written=False` rather than an error: running the
    same command twice is a normal thing for a person to do, and answering it
    with a failure would teach the operator to distrust the tool.
    """
    canonical, error = canonical_code(outcome_code)
    if error:
        print(f"  ❌ {error}")
        return {"ok": False, "written": False, "call_id": "", "error": error}

    called_at = now or datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    occurred_date = called_at[:10]

    store = LeadStore(db_path)
    try:
        acct = find_account(store, business_name)
    finally:
        store.close()
    if not acct:
        error = f"no single account matches '{business_name}'"
        return {"ok": False, "written": False, "call_id": "", "error": error}

    account_id = acct["account_id"]
    conn = _connect(db_path)
    try:
        # The semantic duplicate check: has this account already got a call
        # logged on this date, whatever id that row carries?
        same_day = conn.execute(
            f"SELECT call_id, attempt_no FROM {TABLE}"
            f" WHERE tenant_id = ? AND account_id = ?"
            f" AND substr(called_at, 1, 10) = ?"
            f" ORDER BY attempt_no DESC LIMIT 1",
            (TENANT, account_id, occurred_date)).fetchone()

        if same_day and not new_attempt:
            print(f"  = {acct['business_name']}: already logged for "
                  f"{occurred_date} (attempt {same_day['attempt_no']}) — "
                  f"no change. Use --new-attempt for a second call today.")
            return {"ok": True, "written": False,
                    "call_id": same_day["call_id"], "error": ""}

        # Derived once, here, and never again for this day.
        attempt_no = int(conn.execute(
            f"SELECT COALESCE(MAX(attempt_no), 0) + 1 AS n FROM {TABLE}"
            f" WHERE tenant_id = ? AND account_id = ?",
            (TENANT, account_id)).fetchone()["n"])

        call_id = call_id_for(account_id, occurred_date, attempt_no)
        action = NEXT_ACTION.get(outcome_code, "") if next_action is None \
            else next_action

        cur = conn.execute(
            f"INSERT INTO {TABLE} ("
            " call_id, tenant_id, account_id, called_at, call_window, caller,"
            " channel, number_called, person_called, outcome_code,"
            " outcome_note, loss_reason, next_action, next_action_at,"
            " recall_after, attempt_no, created_at)"
            " VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)"
            " ON CONFLICT(call_id) DO NOTHING",
            (call_id, TENANT, account_id, called_at,
             call_window_for(called_at), caller, channel, number_called,
             person_called, canonical, note_text, loss_reason, action,
             follow_up_at, "", attempt_no, called_at))
        conn.commit()
    finally:
        conn.close()

    if cur.rowcount == 0:
        # Lost a race, or an id collision from a differently-shaped past run.
        print(f"  = {acct['business_name']}: {call_id} already present — no change.")
        return {"ok": True, "written": False, "call_id": call_id, "error": ""}

    label = LABEL.get(outcome_code, outcome_code)
    print(f"  ✅ {acct['business_name']}: {label} → {canonical} "
          f"(attempt {attempt_no}), next: {action or '—'}")
    return {"ok": True, "written": True, "call_id": call_id, "error": "",
            "attempt_no": attempt_no, "outcome_code": canonical}
>>>>>>> origin/main


# ---------------------------------------------------------------------------
# Batch mode
# ---------------------------------------------------------------------------

<<<<<<< HEAD
def run_batch(db_path, batch_file):
    """Process a batch file of outcomes.

    Format per line:
        Company Name | outcome_code | optional note
    Lines starting with # are skipped.
    """
    lines = Path(batch_file).read_text(encoding="utf-8").strip().splitlines()
    ok = fail = 0
=======
def run_batch(db_path, batch_file, *, now=None, new_attempt=False):
    """Process a batch file. Format per line:

        Company Name | outcome_code | optional note

    Lines starting with # are skipped. One bad line does not stop the rest —
    a stack trace halfway through a call list would leave the operator
    guessing which calls made it in.
    """
    lines = Path(batch_file).read_text(encoding="utf-8").strip().splitlines()
    written = skipped = failed = 0
>>>>>>> origin/main
    for line in lines:
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = [p.strip() for p in line.split("|")]
        if len(parts) < 2:
            print(f"  ❌ Bad line (need at least name|outcome): {line}")
<<<<<<< HEAD
            fail += 1
            continue
        name = parts[0]
        code = parts[1]
        note = parts[2] if len(parts) > 2 else ""
        if log_outcome(db_path, name, code, note):
            ok += 1
        else:
            fail += 1

    print(f"\nDone: {ok} logged, {fail} failed")


# ---------------------------------------------------------------------------
# History
# ---------------------------------------------------------------------------

def show_history(db_path):
    """Show all accounts that have OUTCOME entries in notes."""
    store = LeadStore(db_path)
    accts = store.accounts("lead", limit=300)
    found = 0
    for a in accts:
        notes = a.get("notes", "") or ""
        outcomes = re.findall(r"OUTCOME \[([^\]]+)\]: (.+?)(?:\.|$)", notes)
        if outcomes:
            found += 1
            print(f"\n{a['business_name']} (stage: {a.get('stage','?')})")
            for dt, result in outcomes:
                print(f"  [{dt}] {result}")
            if a.get("next_action"):
                print(f"  → Next: {a['next_action']}")
    if found == 0:
        print("No outcomes logged yet.")
=======
            failed += 1
            continue
        name, code = parts[0], parts[1]
        note = parts[2] if len(parts) > 2 else ""
        res = log_outcome(db_path, name, code, note, now=now,
                          new_attempt=new_attempt)
        if res["written"]:
            written += 1
        elif res["ok"]:
            skipped += 1
        else:
            failed += 1

    print(f"\nDone: {written} logged, {skipped} already present, {failed} failed")
    return {"written": written, "skipped": skipped, "failed": failed}


# ---------------------------------------------------------------------------
# Reads
# ---------------------------------------------------------------------------

def codes_listing():
    """The valid codes, both vocabularies, plus the three that are refused."""
    lines = ["Valid outcome codes (what you type → what is stored):", ""]
    for code in sorted(OUTCOME_MAP):
        lines.append(f"  {code:<18} → {OUTCOME_MAP[code]:<14} "
                     f"{LABEL.get(code, '')}")
    lines += ["", "Refused — these are stages, not call outcomes:", ""]
    for code, meaning in STAGE_NOT_OUTCOME.items():
        lines.append(f"  {code:<18}   {meaning}")
    return "\n".join(lines)


def history(db_path, account_id=None, limit=500):
    """Logged calls, newest first, read from the canonical table.

    The old version scraped `OUTCOME [...]` lines out of the `notes` prose,
    which only ever worked because this tool had written them. Reading the
    table instead means a call logged by anything else also shows up.
    """
    conn = _connect(db_path)
    try:
        sql = (f"SELECT call_id, account_id, called_at, call_window,"
               f" outcome_code, outcome_note, loss_reason, next_action,"
               f" next_action_at, attempt_no, caller FROM {TABLE}"
               f" WHERE tenant_id = ?")
        args = [TENANT]
        if account_id:
            sql += " AND account_id = ?"
            args.append(account_id)
        sql += " ORDER BY called_at DESC, attempt_no DESC LIMIT ?"
        args.append(limit)
        return [dict(r) for r in conn.execute(sql, tuple(args))]
    finally:
        conn.close()


def print_history(db_path):
    rows = history(db_path)
    if not rows:
        print("No calls logged yet.")
        return
    current = None
    for row in rows:
        if row["account_id"] != current:
            current = row["account_id"]
            print(f"\n{current}")
        note = f" — {row['outcome_note']}" if row["outcome_note"] else ""
        print(f"  [{row['called_at']}] attempt {row['attempt_no']}: "
              f"{row['outcome_code']}{note}")
        if row["next_action"]:
            at = f" (by {row['next_action_at']})" if row["next_action_at"] else ""
            print(f"    → {row['next_action']}{at}")
>>>>>>> origin/main


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
<<<<<<< HEAD
    ap = argparse.ArgumentParser(description="Log call outcomes")
    ap.add_argument("name", nargs="?", help="Company name (partial match OK)")
    ap.add_argument("outcome", nargs="?", help="Outcome code")
    ap.add_argument("note", nargs="?", default="", help="Optional note")
    ap.add_argument("--batch", type=str, help="Batch file path")
    ap.add_argument("--codes", action="store_true", help="List valid codes")
    ap.add_argument("--history", action="store_true", help="Show logged outcomes")
=======
    ap = argparse.ArgumentParser(
        description="Log call outcomes into painting_call_log (append-only)")
    ap.add_argument("name", nargs="?", help="Company name (partial match OK)")
    ap.add_argument("outcome", nargs="?", help="Outcome code")
    ap.add_argument("note", nargs="?", default="", help="What they said")
    ap.add_argument("--batch", type=str, help="Batch file path")
    ap.add_argument("--codes", action="store_true", help="List valid codes")
    ap.add_argument("--history", action="store_true", help="Show logged calls")
    ap.add_argument("--new-attempt", action="store_true",
                    help="Record a further call on a day already logged")
    ap.add_argument("--next-action", type=str, default=None,
                    help="Override the default next action text")
    ap.add_argument("--follow-up", type=str, default="",
                    help="Follow-up date, ISO (YYYY-MM-DD)")
    ap.add_argument("--caller", type=str, default="ari", help="Who called")
    ap.add_argument("--person", type=str, default="", help="Who was called")
    ap.add_argument("--number", type=str, default="", help="Number dialled")
    ap.add_argument("--channel", type=str, default="mobile",
                    choices=("mobile", "office", "email", "other"))
    ap.add_argument("--loss-reason", type=str, default="",
                    help="Only for JN / Q / WRONG_SEGMENT outcomes")
>>>>>>> origin/main
    ap.add_argument("--db", type=str, default="painting.sqlite", help="DB path")
    args = ap.parse_args()

    if args.codes:
<<<<<<< HEAD
        print("Valid outcome codes:\n")
        for code, info in OUTCOMES.items():
            print(f"  {code:<20} → {info['label']:<25} (stage → {info['stage'] or 'no change'})")
        return

    if args.history:
        show_history(args.db)
        return

    if args.batch:
        run_batch(args.db, args.batch)
=======
        print(codes_listing())
        return

    if args.history:
        print_history(args.db)
        return

    if args.batch:
        run_batch(args.db, args.batch, new_attempt=args.new_attempt)
>>>>>>> origin/main
        return

    if not args.name or not args.outcome:
        ap.print_help()
        return

<<<<<<< HEAD
    log_outcome(args.db, args.name, args.outcome, args.note)
=======
    log_outcome(args.db, args.name, args.outcome, args.note,
                new_attempt=args.new_attempt, next_action=args.next_action,
                follow_up_at=args.follow_up, caller=args.caller,
                person_called=args.person, number_called=args.number,
                channel=args.channel, loss_reason=args.loss_reason)
>>>>>>> origin/main


if __name__ == "__main__":
    main()
