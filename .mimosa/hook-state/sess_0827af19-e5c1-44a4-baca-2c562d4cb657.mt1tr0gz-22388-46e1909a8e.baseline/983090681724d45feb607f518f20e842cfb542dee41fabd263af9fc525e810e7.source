#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""extract_research_data.py — اسکاوت دیجست‌ها → research-data.js

Sources: F:/backup/00 - Inbox/scout-digests/*.md
Sink:    F:/backup/nervous-system/research-data.js

std-lib only.  خواندن فرانت‌متر YAML + شماری یافته‌ها/اسپور/کراس‌دومین.
"""
from __future__ import annotations

import json
import os
import re
from datetime import datetime, timezone, timedelta

SCOUT_DIR = "F:/backup/00 - Inbox/scout-digests"
NS_DIR = "F:/backup/nervous-system"

# canonical scout slugs from Research Scout Fleet definition
CANONICAL_SCOUTS = {
    "mycelium", "crypto", "mining", "lead", "ziman",
    "accounting", "hypnosis", "projectf", "ai-watch",
    "security", "markets", "jobs", "health", "tools",
    "philosophy", "world", "science", "learning", "local",
    "selfimprove", "selfimprove-safety", "selfimprove-memory",
}

# ── helpers ──

def _parse_frontmatter(text: str) -> tuple[dict, str]:
    """Extract simple YAML frontmatter + body."""
    if not text.startswith("---"):
        return {}, text
    m = re.search(r"^---\s*\n(.*?)\n---\s*\n", text, re.DOTALL)
    if not m:
        return {}, text
    raw = m.group(1)
    body = text[m.end():]
    meta: dict = {}
    key = None
    for line in raw.splitlines():
        line = line.rstrip()
        if not line:
            continue
        # simple key: value
        kv = re.match(r"^(\w+):\s*(.*)$", line)
        if kv:
            key = kv.group(1)
            val = kv.group(2).strip()
            # remove quotes
            if val.startswith('"') and val.endswith('"'):
                val = val[1:-1]
            elif val.startswith("'") and val.endswith("'"):
                val = val[1:-1]
            # list inline
            if val.startswith("[") and val.endswith("]"):
                val = [v.strip().strip('"').strip("'") for v in val[1:-1].split(",") if v.strip()]
            meta[key] = val
            continue
        # list item
        lm = re.match(r"^  -\s+(.*)$", line)
        if lm and key:
            item = lm.group(1).strip().strip('"').strip("'")
            if isinstance(meta.get(key), list):
                meta[key].append(item)
            else:
                meta[key] = [meta[key], item] if key in meta else [item]
    return meta, body


def _extract_slug(fname: str) -> str:
    """YYYY-MM-DD <slug>.md  → slug."""
    base = os.path.basename(fname)
    # strip date prefix
    m = re.match(r"^\d{4}-\d{2}-\d{2}(?:\s+\d{4})?\s+(.*?)\.md$", base)
    if m:
        return m.group(1)
    # special files
    if base.startswith("_"):
        return base[1:].replace(".md", "").replace(" ", "-")
    return base.replace(".md", "").replace(" ", "-")


def _count_findings(body: str) -> int:
    """Count numbered findings (Persian or Arabic numerals with dot)."""
    # pattern: 1. or ۱. at start of line
    return len(re.findall(r"^\s*(?:\d+|[\u06f0-\u06f9])+[.．]\s+", body, re.MULTILINE))


def _count_spores(body: str) -> int:
    """Count spore items after ## اسپور."""
    # find section
    sec = re.search(r"##\s+اسپور.*?(?=##|\Z)", body, re.DOTALL)
    if not sec:
        return 0
    return len(re.findall(r"^\s*[۰-۹\d]+[.．]\s+", sec.group(0), re.MULTILINE))


def _count_cross_domain_refs(body: str) -> int:
    """Count wiki-style links in Cross-domain section."""
    sec = re.search(r"##\s+Cross-domain.*?(?=##|\Z)", body, re.DOTALL)
    if not sec:
        return 0
    return len(re.findall(r"\[\[.*?\]\]", sec.group(0)))


def _count_body_links(body: str) -> int:
    """Count all markdown links."""
    return len(re.findall(r"\[.*?\]\(.*?\)", body))


def _safe_date(s: str) -> datetime | None:
    for fmt in ("%Y-%m-%d", "%Y-%m-%d %H:%M", "%Y-%m-%dT%H:%M:%S"):
        try:
            return datetime.strptime(s.strip(), fmt)
        except ValueError:
            pass
    return None


def main() -> None:
    os.makedirs(NS_DIR, exist_ok=True)
    generated = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    files = [f for f in os.listdir(SCOUT_DIR) if f.endswith(".md")]

    digests: list[dict] = []
    by_status: dict[str, int] = {}
    by_type: dict[str, int] = {}
    by_scout: dict[str, int] = {}
    by_date: dict[str, int] = {}
    total_sources = 0
    total_findings = 0
    total_spores = 0
    total_cross_links = 0
    synthesis_dates: list[str] = []
    latest_synthesis: str | None = None
    last_seen: dict[str, str] = {}
    scout_slugs: set[str] = set()

    now = datetime.now(timezone.utc)

    for fname in sorted(files):
        path = os.path.join(SCOUT_DIR, fname)
        try:
            with open(path, "r", encoding="utf-8") as f:
                text = f.read()
        except (OSError, UnicodeDecodeError) as exc:
            print(f"[skip] {fname}: {exc}")
            continue

        meta, body = _parse_frontmatter(text)
        slug = _extract_slug(fname)
        status = meta.get("status", "unknown")
        dtype = meta.get("type", "unknown")
        created = meta.get("created", "")
        updated = meta.get("updated", "")
        sources = meta.get("sources", [])
        if isinstance(sources, str):
            sources = [sources] if sources else []
        tags = meta.get("tags", [])
        if isinstance(tags, str):
            tags = [tags] if tags else []

        # date from filename or meta
        date_str = ""
        dm = re.match(r"^(\d{4}-\d{2}-\d{2})", fname)
        if dm:
            date_str = dm.group(1)
        elif created:
            cd = _safe_date(created)
            if cd:
                date_str = cd.strftime("%Y-%m-%d")

        findings = _count_findings(body)
        spores = _count_spores(body)
        cross_links = _count_cross_domain_refs(body)
        body_links = _count_body_links(body)

        # aggregates
        by_status[status] = by_status.get(status, 0) + 1
        by_type[dtype] = by_type.get(dtype, 0) + 1
        by_scout[slug] = by_scout.get(slug, 0) + 1
        if date_str:
            by_date[date_str] = by_date.get(date_str, 0) + 1
        total_sources += len(sources)
        total_findings += findings
        total_spores += spores
        total_cross_links += cross_links

        # synthesis tracking
        if dtype == "synthesis" or slug == "synthesis":
            synthesis_dates.append(date_str)
            if date_str and (latest_synthesis is None or date_str > latest_synthesis):
                latest_synthesis = date_str

        # fleet last-seen (only canonical scouts)
        if date_str and slug in CANONICAL_SCOUTS:
            scout_slugs.add(slug)
            if slug not in last_seen or date_str > last_seen[slug]:
                last_seen[slug] = date_str

        digests.append({
            "file": fname,
            "slug": slug,
            "type": dtype,
            "status": status,
            "date": date_str,
            "sources_count": len(sources),
            "findings": findings,
            "spores": spores,
            "cross_links": cross_links,
            "body_links": body_links,
            "tags": tags[:8],
            "title": meta.get("project", "")[:120],
        })

    # ── fleet health (canonical scouts only) ──
    canonical_seen = {k: v for k, v in last_seen.items() if k in CANONICAL_SCOUTS}
    active_scouts = len(canonical_seen)
    stale_scouts: list[str] = []
    coverage_24h = 0.0
    coverage_7d = 0.0
    if canonical_seen:
        day_ago = (now - timedelta(days=1)).strftime("%Y-%m-%d")
        week_ago = (now - timedelta(days=7)).strftime("%Y-%m-%d")
        seen_24h = sum(1 for d in canonical_seen.values() if d >= day_ago)
        seen_7d = sum(1 for d in canonical_seen.values() if d >= week_ago)
        coverage_24h = round(seen_24h / active_scouts, 2) if active_scouts else 0.0
        coverage_7d = round(seen_7d / active_scouts, 2) if active_scouts else 0.0
        for slug, d in canonical_seen.items():
            if d < day_ago:
                stale_scouts.append(slug)

    # ── triage board rough scan ──
    triage_path = os.path.join(SCOUT_DIR, "_TRIAGE-BOARD.md")
    triage_open = 0
    triage_top_salience = 0.0
    if os.path.exists(triage_path):
        try:
            with open(triage_path, "r", encoding="utf-8") as f:
                triage_text = f.read()
            # count rows with | # | salience |
            triage_rows = re.findall(r"\|\s*\d+\s*\|\s*(\d?\.?\d+)\s*\|", triage_text)
            triage_open = len(triage_rows)
            if triage_rows:
                triage_top_salience = max(float(v) for v in triage_rows)
        except Exception:
            pass

    # ── health score ──
    health_score = 1.0
    if stale_scouts:
        health_score -= min(len(stale_scouts) * 0.05, 0.4)
    if not latest_synthesis:
        health_score -= 0.3
    else:
        syn_age = (now - datetime.strptime(latest_synthesis, "%Y-%m-%d").replace(tzinfo=timezone.utc)).total_seconds() / 3600
        if syn_age > 48:
            health_score -= 0.2
        elif syn_age > 24:
            health_score -= 0.1
    health_score = max(round(health_score, 2), 0.0)

    # ── recent digests (last 12, dated first) ──
    recent = sorted(
        [d for d in digests if d["date"]],
        key=lambda x: (x["date"], x["file"]),
        reverse=True,
    )[:12]

    research_data = {
        "generated": generated,
        "pipeline": {
            "total_digests": len(digests),
            "by_status": by_status,
            "by_type": by_type,
            "by_scout": by_scout,
            "by_date": by_date,
            "total_sources": total_sources,
            "total_findings": total_findings,
            "total_spores": total_spores,
            "cross_domain_links": total_cross_links,
        },
        "fleet": {
            "active_scouts": active_scouts,
            "last_seen": last_seen,
            "stale_scouts": stale_scouts,
            "coverage_24h": coverage_24h,
            "coverage_7d": coverage_7d,
        },
        "synthesis": {
            "latest_date": latest_synthesis,
            "count": len(synthesis_dates),
        },
        "triage": {
            "open_proposals": triage_open,
            "top_salience": triage_top_salience,
        },
        "recent_digests": [
            {
                "slug": r["slug"],
                "date": r["date"],
                "type": r["type"],
                "status": r["status"],
                "findings": r["findings"],
                "sources": r["sources_count"],
                "spores": r["spores"],
                "file": r["file"],
            }
            for r in recent
        ],
        "health": {
            "score": health_score,
            "stale_count": len(stale_scouts),
            "last_synthesis": latest_synthesis,
        },
    }

    js = (
        "window.RESEARCH_DATA = "
        + json.dumps(research_data, ensure_ascii=False, default=str)
        + ";\n"
    )
    out_path = os.path.join(NS_DIR, "research-data.js")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(js)

    print(
        f"[extract_research_data] research-data.js refreshed: {len(js)} chars, "
        f"{len(digests)} digests, {total_findings} findings, "
        f"{active_scouts} scouts, health={health_score}"
    )


if __name__ == "__main__":
    main()
