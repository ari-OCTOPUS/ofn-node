#!/usr/bin/env python3
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
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ofn.adapters.lead_store import LeadStore


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
}


# ---------------------------------------------------------------------------
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


# ---------------------------------------------------------------------------
# Batch mode
# ---------------------------------------------------------------------------

def run_batch(db_path, batch_file):
    """Process a batch file of outcomes.

    Format per line:
        Company Name | outcome_code | optional note
    Lines starting with # are skipped.
    """
    lines = Path(batch_file).read_text(encoding="utf-8").strip().splitlines()
    ok = fail = 0
    for line in lines:
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = [p.strip() for p in line.split("|")]
        if len(parts) < 2:
            print(f"  ❌ Bad line (need at least name|outcome): {line}")
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


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser(description="Log call outcomes")
    ap.add_argument("name", nargs="?", help="Company name (partial match OK)")
    ap.add_argument("outcome", nargs="?", help="Outcome code")
    ap.add_argument("note", nargs="?", default="", help="Optional note")
    ap.add_argument("--batch", type=str, help="Batch file path")
    ap.add_argument("--codes", action="store_true", help="List valid codes")
    ap.add_argument("--history", action="store_true", help="Show logged outcomes")
    ap.add_argument("--db", type=str, default="painting.sqlite", help="DB path")
    args = ap.parse_args()

    if args.codes:
        print("Valid outcome codes:\n")
        for code, info in OUTCOMES.items():
            print(f"  {code:<20} → {info['label']:<25} (stage → {info['stage'] or 'no change'})")
        return

    if args.history:
        show_history(args.db)
        return

    if args.batch:
        run_batch(args.db, args.batch)
        return

    if not args.name or not args.outcome:
        ap.print_help()
        return

    log_outcome(args.db, args.name, args.outcome, args.note)


if __name__ == "__main__":
    main()
