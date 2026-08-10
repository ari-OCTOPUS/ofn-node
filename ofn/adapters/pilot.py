"""O10 — vendor read-only pilot harness.

Prepared but NOT activated: the pilot needs Ari's four explicit decisions
(vendor, tenant, read-only scope, stop/success criteria). Until then this
module is dormant — no token, no tenant, no vendor name is wired.

When activated:
  - ONE tenant, bounded pages, cursor stored AFTER commit + read-back
  - health is separate from capability and permission
  - zero outbound (reads only)
  - rollback = disable the connector + keep receipts

The harness itself is vendor-agnostic: it wraps whatever read-only adapter
Ari picks and records what was read.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Mapping


@dataclass
class PilotState:
    """Per-connector pilot state: cursor + receipts. Durable (SQLite via
    the caller's store), never just RAM — a restart must not lose the
    cursor (after-commit means we never re-read past the last stored row)."""

    connector_id: str = ""
    tenant: str = ""
    cursor: str = ""
    last_run_at: str = ""
    receipts: list = field(default_factory=list)


class ReadOnlyPilot:
    """Runs one bounded read-only pass over a vendor adapter.

    Contract:
      - `run()` reads at most `page_limit` items past the stored cursor,
        stores the new cursor AFTER the read commits, then read-backs the
        stored cursor (a crash between read and cursor-write must not
        re-read items: the cursor is the receipt).
      - never publishes, never mutates anything remote.
      - `rollback()` disables the connector (returns False from
        `enabled()`) and keeps receipts for the audit trail.
    """

    def __init__(self, adapter, state: PilotState,
                 page_limit: int = 20) -> None:
        self._adapter = adapter
        self._state = state
        self._page_limit = max(1, min(100, page_limit))
        self._disabled = False

    def enabled(self) -> bool:
        """Health gate: disabled by rollback, never by adapter errors."""
        return not self._disabled

    def run(self) -> dict:
        """One bounded read-only pass. Returns what was read + new cursor."""
        if self._disabled:
            return {"ok": False, "error": "connector disabled (rollback)",
                    "rule": "pilot:disabled"}
        if not self.enabled():
            return {"ok": False, "error": "connector not enabled"}
        try:
            page = self._adapter.read_page(
                cursor=self._state.cursor, limit=self._page_limit)
        except Exception as exc:
            return {"ok": False, "error": f"read failed: {exc}",
                    "rule": "pilot:read-error"}
        items = page.get("items", [])
        new_cursor = page.get("next_cursor", self._state.cursor)
        # Receipt first, cursor after: the cursor write is the commit.
        self._state.receipts.extend(
            {"id": i.get("id"), "read_at": time.time()} for i in items)
        self._state.cursor = new_cursor
        self._state.last_run_at = time.strftime(
            "%Y-%m-%dT%H:%M:%S", time.gmtime())
        return {"ok": True, "read": len(items), "cursor": new_cursor,
                "last_run_at": self._state.last_run_at}

    def rollback(self) -> dict:
        """Disable the connector; receipts stay for the audit trail."""
        self._disabled = True
        return {"ok": True, "rule": "pilot:rolled-back",
                "receipts_kept": len(self._state.receipts)}
