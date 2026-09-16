#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""capability_journal.py — append-only discovery journal (Talk Discovery Phase C).

Propose-only. Never arms flags. Never sends outbound.
Stores redacted candidate rows as JSONL; Markdown is a render view.
"""
from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
OPS = HERE.parent
DEFAULT_JSONL = OPS / "state" / "capability-journal.jsonl"
DEFAULT_MD = OPS / "CAPABILITY-JOURNAL.md"

LEVELS = frozenset({"STRUCTURAL", "TESTED", "SHADOW", "ARMED"})
SCHEMA = "CapabilityJournal.entry.v1"

# Never auto-arm these families from discovery pulse.
_NO_AUTO_ARM_PREFIXES = (
    "OCTOPUS_LEAD_",
    "OCTOPUS_WIRE_OUTBOUND",
    "OCTOPUS_MONEY_",
    "OCTOPUS_HARVEST",
    "OCTOPUS_PAY",
)


def _utc_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def journal_path() -> Path:
    raw = os.environ.get("OCTOPUS_CAPABILITY_JOURNAL_JSONL", "").strip()
    return Path(raw) if raw else DEFAULT_JSONL


def md_path() -> Path:
    raw = os.environ.get("OCTOPUS_CAPABILITY_JOURNAL_MD", "").strip()
    return Path(raw) if raw else DEFAULT_MD


def is_arm_forbidden(flag_or_id: str) -> bool:
    s = str(flag_or_id or "")
    return any(s.startswith(p) for p in _NO_AUTO_ARM_PREFIXES)


def append_entry(
    *,
    candidate: str,
    level: str,
    evidence: str,
    owner_vote: str = "pending",
    next_step: str = "propose-only",
    source: str = "talk-discovery",
    path: Path | None = None,
    ts: str | None = None,
) -> dict[str, Any]:
    """Append one journal row. level must be STRUCTURAL/TESTED/SHADOW/ARMED.

    ts اختیاری: برای seed از pulse تا idempotency روی (candidate, day) درست بماند.
    """
    lvl = str(level or "").upper()
    if lvl not in LEVELS:
        raise ValueError(f"invalid level: {level}")
    if is_arm_forbidden(candidate) and lvl == "ARMED":
        raise ValueError("money/lead/outbound candidates cannot be recorded as ARMED here")
    entry = {
        "schema": SCHEMA,
        "ts": str(ts).strip() if ts else _utc_iso(),
        "candidate": str(candidate)[:200],
        "level": lvl,
        "evidence": str(evidence)[:500],
        "owner_vote": str(owner_vote)[:80],
        "next_step": str(next_step)[:200],
        "source": str(source)[:80],
        "auto_arm": False,
    }
    dest = path or journal_path()
    dest.parent.mkdir(parents=True, exist_ok=True)
    with dest.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    return entry


def read_entries(*, path: Path | None = None, limit: int = 200) -> list[dict]:
    dest = path or journal_path()
    if not dest.is_file():
        return []
    rows: list[dict] = []
    with dest.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return rows[-max(1, int(limit)):]


def render_markdown(entries: list[dict] | None = None) -> str:
    rows = entries if entries is not None else read_entries()
    lines = [
        "# CAPABILITY-JOURNAL — Talk Discovery",
        "",
        "Rule: Novel ∧ Repeatable ∧ Useful ∧ Policy-Compliant. **No auto-arm.**",
        "",
        "| candidate | level | evidence | owner_vote | next |",
        "|---|---|---|---|---|",
    ]
    for e in rows:
        lines.append(
            f"| {e.get('candidate','')} | {e.get('level','')} | "
            f"{e.get('evidence','')[:80]} | {e.get('owner_vote','')} | "
            f"{e.get('next_step','')} |"
        )
    if not rows:
        lines.append("| _(empty)_ | — | — | — | — |")
    lines.extend([
        "",
        "```text",
        "discovery-journal + propose-only",
        "!= auto-arm != money-live != outbound-send",
        "```",
        "",
    ])
    return "\n".join(lines)


def write_markdown(*, path: Path | None = None) -> Path:
    dest = path or md_path()
    dest.write_text(render_markdown(), encoding="utf-8")
    return dest
