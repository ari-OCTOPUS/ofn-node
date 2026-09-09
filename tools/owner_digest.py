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
from ofn.agents.b2b_discovery import AUTO_DISCOVERY_TAG


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


def _is_direct(approach: str) -> bool:
    """Match 'Direct' and variants like 'Direct but self-managed...'"""
    return approach.startswith("Direct")


def _direct_caveat(approach: str) -> str:
    """Return caveat text for non-standard Direct variants, or ''."""
    if approach == "Direct":
        return ""
    if approach.startswith("Direct"):
        return approach[len("Direct"):].strip(" —-–")
    return ""


# ---------------------------------------------------------------------------
# Phone classifier — mobile vs office/1300
# ---------------------------------------------------------------------------

_MOBILE_RE = re.compile(r"(?:0[45]\d{2}|\+?614\d{2})[\s\-]?\d{3}[\s\-]?\d{3}")


def _has_mobile(contact_str: str) -> bool:
    """True if contact_channel contains any AU mobile (04xx/05xx/+614)."""
    return bool(_MOBILE_RE.search(contact_str or ""))


def _extract_mobiles(contact_str: str) -> list:
    """Return all mobile numbers found in contact_channel."""
    return _MOBILE_RE.findall(contact_str or "")


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
    ap.add_argument("--include-unverified", action="store_true",
                    help="Also include auto-discovered accounts the "
                         "b2b_discovery agent has not had a human "
                         "verification pass yet (tagged "
                         f"{AUTO_DISCOVERY_TAG!r} in notes). Off by "
                         "default: this digest is a call list, and an "
                         "unverified discovery-agent row is not the same "
                         "confidence level as a researched one.")
    args = ap.parse_args()

    store = LeadStore(args.db)
    accts = store.accounts("lead", limit=300)

    # ---- Parse all accounts ------------------------------------------------
    unverified_excluded = 0
    rows = []
    for a in accts:
        if not args.include_unverified and AUTO_DISCOVERY_TAG in (a.get("notes") or ""):
            unverified_excluded += 1
            continue
        relevance, approach, body = parse_notes(a.get("notes", ""))
        phone = (a.get("contact_channel") or "").strip()
        rows.append({
            "business_name": a.get("business_name", ""),
            "segment":       a.get("segment", ""),
            "suburb":        a.get("suburb", ""),
            "phone":         phone,
            "has_phone":     bool(phone),
            "has_mobile":    _has_mobile(phone),
            "mobiles":       _extract_mobiles(phone),
            "relevance":     relevance,
            "approach":      approach,
            "body":          body,
            "stage":         a.get("stage", "discovered"),
            "website":       a.get("website", ""),
        })

    # ---- Counts ------------------------------------------------------------
    direct_with_phone = [r for r in rows
                         if _is_direct(r["approach"]) and r["has_phone"]]
    direct_no_phone   = [r for r in rows
                         if _is_direct(r["approach"]) and not r["has_phone"]]
    panel_tender      = [r for r in rows
                         if r["approach"] in ("Panel-Tender",
                                              "Panel/Tender",
                                              "Subcontractor Pathway")]
    other             = [r for r in rows
                         if not _is_direct(r["approach"])
                         and r["approach"] not in ("Panel-Tender",
                                                   "Panel/Tender",
                                                   "Subcontractor Pathway")]

    # ---- Sort: mobile first, then by relevance DESC -------------------------
    callable_rows = sorted(direct_with_phone,
                           key=lambda r: (-r["has_mobile"], -r["relevance"]))
    top = callable_rows[:args.top]

    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    # ---- Mobile stats ------------------------------------------------------
    with_mobile = [r for r in direct_with_phone if r["has_mobile"]]
    office_only = [r for r in direct_with_phone if not r["has_mobile"]]

    # ---- Build output ------------------------------------------------------
    lines = []
    lines.append(f"# Owner Digest — {now}")
    lines.append("")
    lines.append(
        f"Total: {len(rows)} | "
        f"Direct+phone: {len(direct_with_phone)} "
        f"(🟢 mobile: {len(with_mobile)} · 🟡 office only: {len(office_only)}) | "
        f"No phone: {len(direct_no_phone)} | "
        f"Panel/Sub: {len(panel_tender)} | "
        f"Other: {len(other)}"
        + (f" | Unverified (hidden): {unverified_excluded}" if unverified_excluded else "")
    )
    lines.append("")

    if args.summary:
        # ---- Compact one-liner format --------------------------------------
        lines.append(f"## Top {len(top)} — Call Today")
        lines.append("")
        for i, r in enumerate(top, 1):
            caveat = _direct_caveat(r["approach"])
            tag = f"  ⚠️ {caveat}" if caveat else ""
            mob = "🟢" if r["has_mobile"] else "🟡"
            # Show mobile number prominently if available
            if r["mobiles"]:
                display_phone = r["mobiles"][0] + "  ← MOBILE"
            else:
                display_phone = r["phone"][:60]
            lines.append(
                f"{i:>2}. {mob} [{r['relevance']:.0f}/10] "
                f"{r['business_name']}  —  {display_phone}{tag}"
            )
        lines.append("")
    else:
        # ---- Detailed card format ------------------------------------------
        lines.append(f"## Top {len(top)} — Call Today")
        lines.append("")
        for i, r in enumerate(top, 1):
            caveat = _direct_caveat(r["approach"])
            caveat_label = f"  ⚠️ {caveat}" if caveat else ""
            mob = "🟢" if r["has_mobile"] else "🟡"
            lines.append(
                f"### {i}. {mob} {r['business_name']}  "
                f"[{r['relevance']:.0f}/10]{caveat_label}"
            )
            if r["mobiles"]:
                lines.append(f"- **📱 Mobile:** {' | '.join(r['mobiles'])}")
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
