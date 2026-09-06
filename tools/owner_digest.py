#!/usr/bin/env python3
"""Owner Daily Digest — top callable B2B accounts sorted by relevance.

Reads painting_b2b_accounts, parses RELEVANCE and APPROACH from the
free-text `notes` field (these are NOT database columns), filters for
Direct approach with a phone number, and outputs a sorted list.

Commercial purpose: Ari sees exactly who to call today, in priority
order, with full phone numbers and context — no guessing.

Usage:
    python tools/owner_digest.py                # top 10 to stdout
    python tools/owner_digest.py --top 20       # top 20
    python tools/owner_digest.py --md digest.md # save as markdown
    python tools/owner_digest.py --summary      # one-line-per-account
"""
import argparse
import re
import sys
from datetime import datetime
from pathlib import Path

# Allow running from repo root: python tools/owner_digest.py
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ofn.adapters.lead_store import LeadStore


# ---------------------------------------------------------------------------
# Notes parser — RELEVANCE and APPROACH live in free text, not columns
# ---------------------------------------------------------------------------

def parse_notes(notes: str):
    """Extract structured data from free-text notes field.

    Expected format inside notes:
        "RELEVANCE: 9/10. APPROACH: Direct. Body Corporate & FM..."

    Returns (relevance: float, approach: str, body: str)
    """
    notes = notes or ""
    rel_match = re.search(r"RELEVANCE:\s*([\d.]+)", notes)
    app_match = re.search(r"APPROACH:\s*([^.]+)", notes)

    relevance = float(rel_match.group(1)) if rel_match else 0.0
    approach = app_match.group(1).strip() if app_match else "Unknown"

    # Body = everything after "APPROACH: Xyz." prefix
    body_match = re.search(r"APPROACH:\s*[^.]+\.\s*(.*)", notes, re.DOTALL)
    body = body_match.group(1).strip() if body_match else notes.strip()

    return relevance, approach, body


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser(description="Owner daily digest")
    ap.add_argument("--top", type=int, default=10,
                    help="How many accounts to show (default 10)")
    ap.add_argument("--md", type=str, default=None,
                    help="Save output as markdown file")
    ap.add_argument("--summary", action="store_true",
                    help="One-line-per-account compact output")
    ap.add_argument("--db", type=str, default="painting.sqlite",
                    help="DB filename (default: painting.sqlite)")
    ap.add_argument("--include-no-phone", action="store_true",
                    help="Also list Direct accounts missing a phone")
    args = ap.parse_args()

    store = LeadStore(args.db)
    accts = store.accounts("lead", limit=300)

    # ---- Parse all accounts ------------------------------------------------
    rows = []
    for a in accts:
        relevance, approach, body = parse_notes(a.get("notes", ""))
        phone = (a.get("contact_channel") or "").strip()
        rows.append({
            "business_name": a.get("business_name", ""),
            "segment":       a.get("segment", ""),
            "suburb":        a.get("suburb", ""),
            "phone":         phone,
            "has_phone":     bool(phone),
            "relevance":     relevance,
            "approach":      approach,
            "body":          body,
            "stage":         a.get("stage", "discovered"),
            "website":       a.get("website", ""),
        })

    # ---- Counts ------------------------------------------------------------
    # "Direct or Vendor Panel" whales are callable too — any approach starting
    # with Direct belongs in Call Today (PR #201 feedback: exact match dropped
    # 11 top-relevance group accounts out of the call list).
    direct_with_phone = [r for r in rows
                         if r["approach"].startswith("Direct") and r["has_phone"]]
    direct_no_phone   = [r for r in rows
                         if r["approach"].startswith("Direct") and not r["has_phone"]]
    panel_tender      = [r for r in rows
                         if r["approach"] in ("Panel-Tender",
                                              "Panel/Tender",
                                              "Subcontractor Pathway")]
    other             = [r for r in rows
                         if r["approach"] not in ("Direct",
                                                  "Panel-Tender",
                                                  "Panel/Tender",
                                                  "Subcontractor Pathway")]

    # ---- Sort callable list by relevance DESC ------------------------------
    callable_rows = sorted(direct_with_phone, key=lambda r: -r["relevance"])
    top = callable_rows[:args.top]

    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    # ---- Build output ------------------------------------------------------
    lines = []
    lines.append(f"# Owner Digest — {now}")
    lines.append("")
    lines.append(
        f"Total: {len(rows)} | "
        f"Direct+phone: {len(direct_with_phone)} | "
        f"Direct (no phone): {len(direct_no_phone)} | "
        f"Panel/Sub: {len(panel_tender)} | "
        f"Other: {len(other)}"
    )
    lines.append("")

    if args.summary:
        # ---- Compact one-liner format --------------------------------------
        lines.append(f"## Top {len(top)} — Call Today")
        lines.append("")
        for i, r in enumerate(top, 1):
            lines.append(
                f"{i:>2}. [{r['relevance']:.0f}/10] "
                f"{r['business_name']}  —  {r['phone']}"
            )
        lines.append("")
    else:
        # ---- Detailed card format ------------------------------------------
        lines.append(f"## Top {len(top)} — Call Today")
        lines.append("")
        for i, r in enumerate(top, 1):
            lines.append(
                f"### {i}. {r['business_name']}  "
                f"[{r['relevance']:.0f}/10]"
            )
            lines.append(f"- **Phone:** {r['phone']}")
            lines.append(f"- **Segment:** {r['segment']}")
            if r["suburb"]:
                lines.append(f"- **Suburb:** {r['suburb']}")
            if r["website"]:
                lines.append(f"- **Website:** {r['website']}")
            lines.append(f"- **Stage:** {r['stage']}")
            if r["body"]:
                # Show full notes body, no truncation
                lines.append(f"- **Why:** {r['body']}")
            lines.append("")

    # ---- Direct accounts missing phone (enrichment candidates) -------------
    if args.include_no_phone and direct_no_phone:
        no_phone_sorted = sorted(direct_no_phone,
                                 key=lambda r: -r["relevance"])
        lines.append(f"## Needs Phone ({len(no_phone_sorted)} accounts)")
        lines.append("")
        for i, r in enumerate(no_phone_sorted, 1):
            web = f" | {r['website']}" if r["website"] else ""
            lines.append(
                f"{i:>2}. [{r['relevance']:.0f}/10] "
                f"{r['business_name']}{web}"
            )
        lines.append("")

    output = "\n".join(lines)

    # ---- Write or print ----------------------------------------------------
    if args.md:
        Path(args.md).write_text(output, encoding="utf-8")
        print(f"Saved to {args.md}")
    else:
        print(output)


if __name__ == "__main__":
    main()
