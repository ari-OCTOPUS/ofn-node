#!/usr/bin/env python3
"""
adr_feed.py — Scan kernel ADR files and emit structured JSON feed.

این ماژول فایل‌های ADR را می‌خواند و یک feed ساختاریافته JSON تولید می‌کند
که بدن می‌تواند آن را بخواند.
"""
from __future__ import annotations

import csv
import hashlib
import json
import logging
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# Kernel root path (absolute, stable for this project)
KERNEL_ROOT = Path("F:/backup/03 - Projects/research-spec-compiler")
ADR_DIR = KERNEL_ROOT / "adr"
OUTPUT_DIR = KERNEL_ROOT / "body_bridge" / "output"
OUTPUT_PATH = OUTPUT_DIR / "adr_feed.json"

# Regex patterns for inline metadata parsing (ADRs use markdown headers, not YAML frontmatter)
_RE_ADR_HEADER = re.compile(r"^#\s+ADR-(\d+)\s+[—-]\s+(.*)$", re.MULTILINE)
_RE_STATUS = re.compile(r"\*\*Status:\*\*\s*(.*?)(?:\n|$)", re.IGNORECASE)
_RE_DATE = re.compile(r"\*\*Date:\*\*\s*(\d{4}-\d{2}-\d{2})", re.IGNORECASE)
_RE_SPEC = re.compile(r"\*\*Spec(?:s)?:\*\*\s*(.*?)(?:\n|$)", re.IGNORECASE)
_RE_DECISION_RULE = re.compile(r"\*\*Decision rule.*?\*\*\s*(.*?)(?:\n|$)", re.IGNORECASE)
_RE_VERDICT_BOLD = re.compile(r"\*\*([A-Z/\-]+)\*\*")

# Verdict table extraction: find the markdown table under ## Verdict
_RE_VERDICT_SECTION = re.compile(r"##\s+Verdict\s*(.*?)(?=\n## |\Z)", re.DOTALL | re.IGNORECASE)


def _extract_verdict_table(text: str) -> list[dict[str, Any]]:
    """Extract the first markdown table inside the Verdict section as structured rows."""
    match = _RE_VERDICT_SECTION.search(text)
    if not match:
        return []
    section = match.group(1)
    # Find the first markdown table in this section
    lines = [ln.strip() for ln in section.splitlines() if ln.strip()]
    table_lines = []
    in_table = False
    for line in lines:
        if line.startswith("|"):
            in_table = True
            table_lines.append(line)
        elif in_table:
            break
    if len(table_lines) < 2:
        return []
    # Header = first line, skip separator line (second line with dashes)
    header = [c.strip() for c in table_lines[0].split("|") if c.strip()]
    rows = []
    start = 2 if table_lines[1].replace("-", "").replace("|", "").replace(":", "").replace(" ", "") == "" else 1
    for line in table_lines[start:]:
        cells = [c.strip() for c in line.split("|")]
        # Drop leading/trailing empty strings caused by | delimiters
        while cells and cells[0] == "":
            cells.pop(0)
        while cells and cells[-1] == "":
            cells.pop()
        # Pad or trim to header length
        if len(cells) < len(header):
            cells += [""] * (len(header) - len(cells))
        cells = cells[:len(header)]
        rows.append(dict(zip(header, cells)))
    return rows


def _parse_adr_file(path: Path) -> dict[str, Any]:
    """Parse a single ADR markdown file into a structured dict."""
    text = path.read_text(encoding="utf-8")
    filename = path.name

    # Number and title from first header or filename
    header_match = _RE_ADR_HEADER.search(text)
    if header_match:
        number = int(header_match.group(1))
        title = header_match.group(2).strip()
    else:
        # Fallback to filename pattern ADR-NNN-...
        fn_match = re.search(r"ADR-(\d+)", filename)
        number = int(fn_match.group(1)) if fn_match else 0
        title = filename

    status_match = _RE_STATUS.search(text)
    status = status_match.group(1).strip() if status_match else "unknown"

    date_match = _RE_DATE.search(text)
    date = date_match.group(1) if date_match else ""

    spec_match = _RE_SPEC.search(text)
    spec = spec_match.group(1).strip() if spec_match else ""

    decision_rule_match = _RE_DECISION_RULE.search(text)
    decision_rule = decision_rule_match.group(1).strip() if decision_rule_match else ""

    # Verdict extraction: look for bolded verdict keywords near the Verdict section
    verdict = "UNKNOWN"
    verdict_keywords = ["INTEGRATE", "OPTIMIZE", "REJECTED", "DISCARD", "FAIL", "accepted"]
    
    # Search within the Verdict section for a bold verdict
    v_section = _RE_VERDICT_SECTION.search(text)
    if v_section:
        v_text = v_section.group(1)
        for kw in verdict_keywords:
            if kw.upper() in v_text.upper():
                # Prefer the first bold mention
                bold = _RE_VERDICT_BOLD.search(v_text)
                if bold:
                    verdict = bold.group(1).strip()
                    break
                else:
                    verdict = kw.upper()
                    break
    else:
        # Fallback: search whole text for machine verdict line
        machine_line = re.search(r"machine verdict\s+([A-Z]+)", text, re.IGNORECASE)
        if machine_line:
            verdict = machine_line.group(1).upper()

    # Normalize accepted → ACCEPTED
    if verdict.lower() == "accepted":
        verdict = "ACCEPTED"

    table = _extract_verdict_table(text)

    return {
        "adr_number": number,
        "title": title,
        "status": status,
        "date": date,
        "spec": spec,
        "decision_rule": decision_rule,
        "verdict": verdict,
        "filename": filename,
        "verdict_table": table,
    }


def _compute_checksum(adr_dicts: list[dict]) -> str:
    """Compute SHA256 of concatenated ADR contents (sorted by filename)."""
    h = hashlib.sha256()
    for d in sorted(adr_dicts, key=lambda x: x.get("filename", "")):
        h.update(json.dumps(d, sort_keys=True, ensure_ascii=False).encode("utf-8"))
    return h.hexdigest()


def refresh_adr_feed() -> dict:
    """Rebuild the ADR feed JSON and write it to disk. Returns the feed dict."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    adrs: list[dict] = []

    if not ADR_DIR.exists():
        logger.warning("ADR directory not found: %s", ADR_DIR)
    else:
        for path in sorted(ADR_DIR.glob("ADR-*.md")):
            try:
                adr = _parse_adr_file(path)
                adrs.append(adr)
            except Exception as e:
                logger.warning("Failed to parse %s: %s", path.name, e)

    feed = {
        "kernel_name": "Cognitive Kernel 0.1",
        "ring": 2,
        "feed_type": "adr",
        "last_updated": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "checksum": _compute_checksum(adrs),
        "total": len(adrs),
        "adrs": adrs,
    }

    OUTPUT_PATH.write_text(
        json.dumps(feed, indent=2, ensure_ascii=False, sort_keys=True),
        encoding="utf-8",
    )
    logger.info("ADR feed refreshed: %d ADRs, checksum %s...", len(adrs), feed["checksum"][:12])
    return feed


def get_adr_by_verdict(verdict: str) -> list[dict]:
    """Return ADRs filtered by verdict (case-insensitive)."""
    feed = refresh_adr_feed()
    target = verdict.upper().strip()
    return [adr for adr in feed.get("adrs", []) if adr.get("verdict", "").upper() == target]


def summary() -> dict:
    """Return counts by verdict plus total."""
    feed = refresh_adr_feed()
    counts: dict[str, int] = {}
    for adr in feed.get("adrs", []):
        v = adr.get("verdict", "UNKNOWN")
        counts[v] = counts.get(v, 0) + 1
    return {
        "total": feed.get("total", 0),
        "by_verdict": counts,
        "last_updated": feed.get("last_updated", ""),
        "checksum": feed.get("checksum", ""),
    }


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(name)s %(levelname)s %(message)s")
    feed = refresh_adr_feed()
    print(f"ADR feed refreshed: {feed['total']} ADRs")
    print("Summary:", summary())


if __name__ == "__main__":
    main()
