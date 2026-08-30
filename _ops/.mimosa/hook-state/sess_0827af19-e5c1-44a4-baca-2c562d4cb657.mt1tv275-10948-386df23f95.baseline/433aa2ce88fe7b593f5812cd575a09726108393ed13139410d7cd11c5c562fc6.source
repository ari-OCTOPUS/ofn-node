#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""discovery_pulse.py — safe weekly AI-core dark pulse (Talk Discovery Phase C).

Read-only / propose-only. Never sets env flags. Never schedules outbound.
"""
from __future__ import annotations

import re
import time
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
OPS = HERE.parent

SCHEMA = "DiscoveryPulse.v1"

# AI-core focus — money/lead harvest explicitly excluded from propose list.
_AI_CORE = re.compile(
    r"(CORTEX_|COLLAB|FUGU|SEMANTIC|KERNEL_BRIDGE|ASK_BRAIN|MODEL|"
    r"CHAT_ROOM_BRAIN|COCKPIT_BRAIN|CODE_BRAIN|BRAIN_DIGEST|"
    r"CONTEXT_BUNDLE|ROUTE_|LOCAL_FIRST)",
    re.I,
)
_EXCLUDE = re.compile(
    r"(LEAD_|OUTBOUND|MONEY_|HARVEST|PAY_|CSV|CRM|WIRE_SEND)",
    re.I,
)


def _utc_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _ai_core_rows(scan_result: dict) -> list[dict]:
    dark = list(scan_result.get("dark") or [])
    out = []
    for r in dark:
        flag = str(r.get("flag") or "")
        if _EXCLUDE.search(flag):
            continue
        if _AI_CORE.search(flag):
            out.append(r)
    return out


def build_dark_pulse(*, ops_root: Path | None = None, scan_result: dict | None = None) -> dict:
    """Build a weekly dark inventory pulse focused on AI-core flags."""
    if scan_result is None:
        import dark_capabilities as dc  # noqa: WPS433
        scan_result = dc.scan(ops_root or OPS)
    rows = _ai_core_rows(scan_result)
    # Prefer higher reader-count (more structurally wired)
    rows = sorted(rows, key=lambda r: (-int(r.get("n_readers") or 0), r.get("flag") or ""))
    proposals = []
    for r in rows[:12]:
        proposals.append({
            "candidate": r["flag"],
            "level": "STRUCTURAL",
            "evidence": f"dark scan; {r.get('n_readers', 0)} readers; no auto-arm",
            "owner_vote": "pending",
            "next_step": "owner vote: experiment | ignore | arm-later",
            "auto_arm": False,
        })
    return {
        "schema": SCHEMA,
        "ts": _utc_iso(),
        "n_dark_total": int(scan_result.get("n_dark") or 0),
        "n_ai_core_dark": len(rows),
        "live_source": scan_result.get("live_source"),
        "proposals": proposals,
        "note": "Propose-only pulse. Scheduler arm requires separate owner vote.",
    }


def living_card(*, pulse: dict | None = None, digest: dict | None = None) -> str:
    """Short cockpit / MiniApp status card text (edit-in-place friendly)."""
    p = pulse or build_dark_pulse()
    d = digest
    if d is None:
        try:
            from owner_console import collab_digest as cd
            d = cd.build_digest(snapshot={
                "health": {}, "organism": {"beat": 0}, "flags": {},
            })
        except Exception:  # noqa: BLE001
            d = {"status": "UNKNOWN"}
    lines = [
        "🧠 Living card — مغز / کشف",
        f"dark AI-core: {p.get('n_ai_core_dark', '?')} · total dark: {p.get('n_dark_total', '?')}",
        f"digest: {d.get('status', '?')} · source: {p.get('live_source', '?')}",
        "قانون: پیشنهاد فقط — بدون arm خودکار",
    ]
    top = (p.get("proposals") or [])[:3]
    if top:
        lines.append("پیشنهادها:")
        for row in top:
            lines.append(f"· {row['candidate']} [{row['level']}]")
    return "\n".join(lines)


def seed_journal_from_pulse(*, pulse: dict | None = None, write_md: bool = True) -> list[dict]:
    """Append pulse proposals into capability journal (idempotent by candidate+day)."""
    from owner_console import capability_journal as cj

    p = pulse or build_dark_pulse()
    stamp = str(p.get("ts") or _utc_iso())
    day = stamp[:10]
    existing = {(e.get("candidate"), (e.get("ts") or "")[:10]) for e in cj.read_entries()}
    written = []
    for row in p.get("proposals") or []:
        key = (row["candidate"], day)
        if key in existing:
            continue
        written.append(cj.append_entry(
            candidate=row["candidate"],
            level=row["level"],
            evidence=row["evidence"],
            owner_vote=row.get("owner_vote", "pending"),
            next_step=row.get("next_step", "propose-only"),
            source="dark-pulse",
            ts=stamp,  # همان روزِ pulse — وگرنه idempotency می‌شکند
        ))
        existing.add(key)
    if write_md:
        cj.write_markdown()
    return written


def heldout_candidates(*, fixture_path: Path | None = None) -> list[dict]:
    """Load advisory held-out discovery candidates (side-effect-free)."""
    import json
    path = fixture_path or (OPS / "test_intelligence" / "fixtures" / "discovery-held-out.json")
    if not path.is_file():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    return list(data.get("candidates") or [])


def discover_reply_text(*, max_items: int = 5) -> str:
    """Backward-compatible wrapper → unified discovery_facade (provenance)."""
    from owner_console.discovery_facade import discover_reply_text as _facade
    return _facade(max_items=max_items)


if __name__ == "__main__":
    import argparse
    import json
    import sys

    ap = argparse.ArgumentParser(description="AI-core dark discovery pulse (propose-only)")
    ap.add_argument("--seed", action="store_true",
                    help="append proposals to capability journal + refresh MD")
    ap.add_argument("--json", action="store_true", help="print pulse JSON only")
    args = ap.parse_args()
    pulse = build_dark_pulse()
    if args.seed:
        written = seed_journal_from_pulse(pulse=pulse, write_md=True)
        print(f"seeded {len(written)} journal row(s); auto_arm=false", file=sys.stderr)
    if args.json or not args.seed:
        print(json.dumps(pulse, ensure_ascii=False, indent=2))
    if not args.json:
        print("---", file=sys.stderr)
        print(living_card(pulse=pulse), file=sys.stderr)
