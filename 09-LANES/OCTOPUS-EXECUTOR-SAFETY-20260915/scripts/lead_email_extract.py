#!/usr/bin/env python3
"""lead_email_extract.py — pull emails already present in free-text fields into
the machine-readable send ledger (`lead-emails.jsonl`).

Root cause this fixes (2026-09-17 funnel day): 32 of 97 leads carry a real
address inside `contact_channel` (e.g. "1300 ... | info@x.com.au"), but the
enricher skips any account whose blob contains "@" ("already emailable") and
never writes those addresses to the ledger the send path reads. Net effect:
the funnel looks email-starved while the addresses sit in plain sight.

Bounded and additive: reads leads_master.json, appends only NEW business_names,
writes one receipt row per cycle. No network, no paid API.
"""
import json
import pathlib
import re
import time

ROOT = pathlib.Path("/home/ari/ofn/state/revenue-drive")
LEADS = pathlib.Path("/home/ari/ofn/tools/leads_master.json")
FOUND = ROOT / "lead-emails.jsonl"
RECEIPTS = ROOT / "receipts.jsonl"
EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
BAD = ("example.", "sentry", "wixpress", "@2x", ".png", ".jpg", "domain.com",
       "noreply", "no-reply")


def receipt(kind, **kw):
    with RECEIPTS.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(dict(schema="octopus.lead-email-extract.v1",
                                 at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                                 kind=kind, **kw), sort_keys=True,
                            ensure_ascii=False) + "\n")


def main() -> int:
    leads = json.loads(LEADS.read_text(errors="replace")).get("accounts", [])
    have = set()
    if FOUND.exists():
        for line in FOUND.read_text(errors="replace").splitlines():
            try:
                have.add(json.loads(line)["business_name"])
            except (ValueError, KeyError):
                pass
    added = []
    for a in leads:
        name = (a.get("business_name") or "").strip()
        if not name or name in have:
            continue
        blob = " ".join(str(a.get(k) or "") for k in
                        ("contact_channel", "notes", "evidence_url", "website"))
        cands = [e for e in EMAIL.findall(blob)
                 if not any(b in e.lower() for b in BAD)]
        if not cands:
            continue
        pick = cands[0]
        row = {"business_name": name, "email": pick,
               "suburb": a.get("suburb"),
               "source": str(a.get("contact_channel") or "")[:120],
               "strategy": "contact_channel_extract",
               "at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
        with FOUND.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(row, sort_keys=True, ensure_ascii=False) + "\n")
        added.append(name)
        have.add(name)
    receipt("EXTRACT_CYCLE", added=len(added), ledger_total=len(have))
    print(json.dumps({"added": len(added), "ledger_total": len(have),
                      "added_names": added[:8]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
