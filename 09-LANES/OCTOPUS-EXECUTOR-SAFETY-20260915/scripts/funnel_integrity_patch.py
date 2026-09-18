#!/usr/bin/env python3
"""Funnel data-integrity patch (owner ruling 2026-09-17, items 3+4).

FINDING (read-only audit, 2026-09-17):
  season-meter's `sent_today` counts MESSAGES from sent-log.jsonl (11 today,
  all with explicit outcome="sent"), while `sent_total` counts PACKETS whose
  lifecycle state == "SENT" (3). Different units under ambiguous names — that
  is why sent_today(11) > sent_total(3). NOT a counting bug; a naming bug.
  Producer of both: revenue_state.py. Also found: the sent_today counter used
  `.get("outcome", "sent")`, silently counting outcome-less rows as sent.

THIS PATCH (small, pre-imaged, additive; no receipts rewritten):
  1. meter fields renamed to state their units: messages_sent_today,
     packets_in_sent_state (old ambiguous names dropped from the regenerated
     meter file; MIGRATION note below).
  2. the outcome default bug fixed (only explicit outcome=="sent" counts).
  3. phone-only queue built: leads with no email anywhere -> channel=phone_only
     (separate file; no external effect).
  4. the daily demand report now emits the four owner-mandated values:
     leads_total, emails_known, contactable_phone_only, verified_cash
     (verified_cash stays 0.0 with no optimistic interpretation).
INVARIANT (registered): had both old fields been send counters,
  sent_total >= sent_today >= 0 must hold; it did NOT (11 > 3), which is what
  exposed the mixed units. With the new names the invariant applies per-unit:
  packets_in_sent_state <= messages_sent_today is NOT required (different
  units) — queries compare like with like now.
"""
import json
import pathlib
import re
import shutil
import subprocess
import time

ROOT = pathlib.Path("/home/ari/ofn/state/revenue-drive")
RS = ROOT / "revenue_state.py"
PRE = ROOT / "revenue_state.py.pre-meter-naming-20260917"
METER = ROOT / "season-meter.json"
RECEIPTS = ROOT / "receipts.jsonl"
LEADS = pathlib.Path("/home/ari/ofn/tools/leads_master.json")
FOUND = ROOT / "lead-emails.jsonl"
PHONE_Q = ROOT / "phone-only-queue.jsonl"

OLD_BLOCK = '''    _sent_today = 0
    for _l in (ROOT / "sent-log.jsonl").read_text(errors="replace").splitlines():
        try:
            _r = json.loads(_l)
        except ValueError:
            continue
        if _r.get("at", "").startswith(_today) and _r.get("outcome", "sent") == "sent":
            _sent_today += 1'''
NEW_BLOCK = '''    # 2026-09-17 data-integrity fix: explicit outcome only (the old default
    # `.get("outcome", "sent")` silently counted outcome-less rows as sent).
    _sent_today = 0
    for _l in (ROOT / "sent-log.jsonl").read_text(errors="replace").splitlines():
        try:
            _r = json.loads(_l)
        except ValueError:
            continue
        if _r.get("at", "").startswith(_today) and _r.get("outcome") == "sent":
            _sent_today += 1'''

OLD_WRITE = '''    (ROOT / "season-meter.json").write_text(json.dumps({
        "at": NOW,
        "verified_cash": st.get("verified_cash_aud", 0.0),
        "leads_total": len(leads),
        "emails_known": _emails,
        "authorized_with_contact": st["counts"].get("CHANNEL_AUTHORIZED", 0),
        "staged_packets": _staged,
        "sent_today": _sent_today,
        "sent_total": st["counts"].get("SENT", 0),
        "replies_detected": _repl,
    }, indent=1, sort_keys=True) + "\\n", encoding="utf-8")'''
NEW_WRITE = '''    # MIGRATION 2026-09-17 (owner ruling): sent_today/sent_total had mixed
    # units (messages vs packet-lifecycle-state) — renamed to make the unit
    # explicit; added contactable_phone_only; the four canonical daily values
    # are leads_total, emails_known, contactable_phone_only, verified_cash.
    _phone_only = 0
    if PHONE_Q.exists():
        _phone_only = sum(1 for _l in PHONE_Q.read_text(errors="replace")
                          .splitlines() if _l.strip())
    (ROOT / "season-meter.json").write_text(json.dumps({
        "at": NOW,
        "verified_cash": st.get("verified_cash_aud", 0.0),
        "leads_total": len(leads),
        "emails_known": _emails,
        "contactable_phone_only": _phone_only,
        "authorized_with_contact": st["counts"].get("CHANNEL_AUTHORIZED", 0),
        "staged_packets": _staged,
        "messages_sent_today": _sent_today,
        "packets_in_sent_state": st["counts"].get("SENT", 0),
        "replies_detected": _repl,
    }, indent=1, sort_keys=True) + "\\n", encoding="utf-8")'''


def receipt(kind, **kw):
    with RECEIPTS.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(dict(schema="octopus.funnel-integrity.v1",
                                 at=time.strftime("%Y-%m-%dT%H:%M:%SZ",
                                                  time.gmtime()),
                                 kind=kind, **kw), sort_keys=True,
                            ensure_ascii=False) + "\n")


def build_phone_queue():
    leads = json.loads(LEADS.read_text(errors="replace")).get("accounts", [])
    have = set()
    for line in FOUND.read_text(errors="replace").splitlines():
        try:
            have.add(json.loads(line)["business_name"])
        except (ValueError, KeyError):
            pass
    EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
    rows, kept = [], []
    if PHONE_Q.exists():
        kept = [l for l in PHONE_Q.read_text(errors="replace").splitlines()
                if l.strip()]
    kept_names = set()
    for l in kept:
        try:
            kept_names.add(json.loads(l)["business_name"])
        except (ValueError, KeyError):
            pass
    for a in leads:
        name = (a.get("business_name") or "").strip()
        if not name or name in have or name in kept_names:
            continue
        blob = " ".join(str(a.get(k) or "") for k in
                        ("contact_channel", "notes", "evidence_url", "website"))
        if EMAIL.search(blob):
            continue  # an address exists somewhere; not phone-only
        rows.append({"business_name": name, "channel": "phone_only",
                     "phone": (a.get("contact_channel") or "")[:60],
                     "website": a.get("website"),
                     "note": "no email found on site or in records as of "
                             "2026-09-17; NO outbound of any kind without "
                             "explicit card/consent/gate",
                     "at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())})
    with PHONE_Q.open("a", encoding="utf-8") as fh:
        for r in rows:
            fh.write(json.dumps(r, sort_keys=True, ensure_ascii=False) + "\n")
    return len(kept) + len(rows), len(rows)


def main():
    pre_meter = METER.read_text(errors="replace") if METER.exists() else ""
    src = RS.read_text(encoding="utf-8")
    if "MIGRATION 2026-09-17" in src:
        print("already patched")
    else:
        for tag, old in (("outcome-default", OLD_BLOCK),
                         ("meter-write", OLD_WRITE)):
            if src.count(old) != 1:
                print(f"ABORT: anchor {tag} count={src.count(old)}")
                return 2
        if not PRE.exists():
            shutil.copyfile(RS, PRE)
            print("preimage_written")
        src = src.replace(OLD_BLOCK, NEW_BLOCK).replace(OLD_WRITE, NEW_WRITE)
        RS.write_text(src, encoding="utf-8", newline="\n")
        import py_compile
        py_compile.compile(str(RS), doraise=True)
        print("patched+compiled")
    total_q, added_q = build_phone_queue()
    print(f"phone_only queue: +{added_q} new, {total_q} total")
    # regenerate the meter with new names
    out = subprocess.run(["python3", str(RS)], capture_output=True, text=True,
                         cwd=str(ROOT))
    print("revenue_state run:", out.stdout.strip()[-200:] or out.stderr.strip()[-200:])
    post_meter = METER.read_text(errors="replace") if METER.exists() else ""
    receipt("METER_NAMING_MIGRATION", pre_meter=pre_meter.strip()[-300:],
            post_meter=post_meter.strip()[-400:], phone_only_total=total_q,
            note="sent_today/sent_total were mixed units (messages vs packet "
                 "state SENT); renamed messages_sent_today/packets_in_sent_"
                 "state + outcome-default bug fixed; phone-only queue built; "
                 "verified_cash stays 0.0 uninterpreted; no conversion-rate "
                 "claims until semantics stable")
    print("receipt appended; new meter:")
    print(post_meter)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
