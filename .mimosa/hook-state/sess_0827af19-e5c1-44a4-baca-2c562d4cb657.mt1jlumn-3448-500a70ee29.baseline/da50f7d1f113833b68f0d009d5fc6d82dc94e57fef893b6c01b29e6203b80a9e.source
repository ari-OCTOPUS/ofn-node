#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""sources.py — concrete DiscoverySource adapters (read-only)."""
from __future__ import annotations

import time
from datetime import UTC, datetime
from pathlib import Path

from discovery.discover_facade import DiscoveryFact, Provenance, _digest

OPS = Path(__file__).resolve().parents[1]

# World Discovery report is historical (2026-07-30) — mark stale after 7 days from capture.
_WD_REPORT = OPS / "world_discovery" / "reports" / "WORLD-DISCOVERY-EXECUTION-REPORT-2026-07-30.md"
_WD_CAPTURED = "2026-07-30T00:00:00+00:00"
_WD_STALE_HOURS = 168  # 7 days — already stale relative to Aug 2026


class CatalogSource:
    def search(self, query: str) -> list[DiscoveryFact]:
        try:
            from owner_console import catalog
            rows = catalog.discover() or []
        except Exception:
            return []
        q = (query or "").strip().lower()
        out: list[DiscoveryFact] = []
        for r in rows:
            if not isinstance(r, dict):
                continue
            title = str(r.get("title") or r.get("capability_id") or "")
            cid = str(r.get("capability_id") or "")
            status = str(r.get("status") or "UNKNOWN")
            blob = f"{title} {cid} {status}".lower()
            if q and q not in blob and not any(tok in blob for tok in q.split() if len(tok) > 2):
                # still include top LIVE rows when query is discovery-generic
                if status != "LIVE":
                    continue
            text = f"status={status}"
            path = str(r.get("manifest_path") or r.get("path") or f"catalog:{cid}")
            captured = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            out.append(DiscoveryFact(
                title=title or cid or "catalog-item",
                text=text,
                confidence=0.7 if status == "LIVE" else 0.45,
                provenance=Provenance(
                    source_id=cid or title,
                    source_kind="catalog",
                    path=path,
                    captured_at=captured,
                    trust="verified" if status == "LIVE" else "derived",
                    content_digest=_digest(f"{cid}|{status}|{title}"),
                    stale_after_hours=24,
                ),
            ))
            if len(out) >= 8:
                break
        return out


class HiddenCapabilitiesSource:
    """Journal + dark pulse + held-out (AI-core hidden)."""

    def search(self, query: str) -> list[DiscoveryFact]:
        out: list[DiscoveryFact] = []
        try:
            from owner_console import capability_journal as cj
            from owner_console import discovery_pulse as dp
        except Exception:
            return out

        seen: set[str] = set()
        for e in reversed(cj.read_entries(limit=40)):
            cand = str(e.get("candidate") or "")
            if not cand or cand in seen:
                continue
            seen.add(cand)
            level = str(e.get("level") or "STRUCTURAL")
            conf = {"ARMED": 0.85, "SHADOW": 0.7, "TESTED": 0.65, "STRUCTURAL": 0.4}.get(level, 0.4)
            out.append(DiscoveryFact(
                title=cand,
                text=f"level={level} vote={e.get('owner_vote')}",
                confidence=conf,
                provenance=Provenance(
                    source_id=cand,
                    source_kind="journal",
                    path="CAPABILITY-JOURNAL / state/capability-journal.jsonl",
                    captured_at=str(e.get("ts") or time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())),
                    trust="derived",
                    content_digest=_digest(f"{cand}|{level}|{e.get('evidence')}"),
                    stale_after_hours=72,
                ),
            ))
            if len(out) >= 6:
                break

        pulse = dp.build_dark_pulse()
        for r in (pulse.get("proposals") or [])[:6]:
            cand = str(r.get("candidate") or "")
            if not cand or cand in seen:
                continue
            seen.add(cand)
            out.append(DiscoveryFact(
                title=cand,
                text="dark AI-core flag (STRUCTURAL, no auto-arm)",
                confidence=0.35,
                provenance=Provenance(
                    source_id=cand,
                    source_kind="journal",
                    path="dark_capabilities.scan → discovery_pulse",
                    captured_at=str(pulse.get("ts") or time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())),
                    trust="derived",
                    content_digest=_digest(cand + "|dark"),
                    stale_after_hours=24,
                ),
            ))
        return out


class WorldDiscoverySource:
    def search(self, query: str) -> list[DiscoveryFact]:
        status = "UNKNOWN"
        try:
            text = _WD_REPORT.read_text("utf-8")
            if "NO_VALID_DISCOVERY" in text:
                status = "NO_VALID_DISCOVERY"
            elif "DISCOVERY_VALIDATED" in text:
                status = "DISCOVERY_VALIDATED"
            ok = True
        except OSError:
            text = ""
            ok = False
        path = str(_WD_REPORT.relative_to(OPS)).replace("\\", "/") if _WD_REPORT.exists() else "missing"
        body = (
            f"گزارش تاریخی World Discovery: status={status}. "
            "۱۵ منبع / ۸ کاندیدا / صفر کشف دو-منبعی معتبر. این حقیقت فعلی نیست."
            if ok else "گزارش World Discovery خوانده نشد."
        )
        return [DiscoveryFact(
            title="World Discovery (historical)",
            text=body,
            confidence=0.3 if ok else 0.1,
            provenance=Provenance(
                source_id="world-discovery-2026-07-30",
                source_kind="world_discovery",
                path=path,
                captured_at=_WD_CAPTURED,
                trust="stale",  # will stay/force stale via TTL
                content_digest=_digest(body),
                stale_after_hours=_WD_STALE_HOURS,
            ),
        )]


def default_sources() -> tuple[CatalogSource, HiddenCapabilitiesSource, WorldDiscoverySource]:
    return CatalogSource(), HiddenCapabilitiesSource(), WorldDiscoverySource()


def default_reply(query: str = "") -> "object":
    from discovery.discover_facade import discover_reply_text
    cat, hid, wd = default_sources()
    return discover_reply_text(
        query or "کشف پنهان",
        catalog=cat,
        hidden_capabilities=hid,
        world_discovery=wd,
    )
