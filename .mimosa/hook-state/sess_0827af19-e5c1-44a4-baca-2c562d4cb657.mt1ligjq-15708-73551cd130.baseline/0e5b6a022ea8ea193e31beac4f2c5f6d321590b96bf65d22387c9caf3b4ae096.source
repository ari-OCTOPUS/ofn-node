#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""extract_ideas_backlog.py — CH-12: Company Ideas → Backlog

Sources: F:/backup/00 - Inbox/ (idea notes, build-proposals/, system-review/, etc.)
Sink:   ideas-data.js  (window.IDEAS_DATA = {...})

Extracts markdown frontmatter + H1 titles, computes a strategic-value score,
and ranks ideas for the OCTOPUS admin backlog panel.

$0 offline, stdlib-only.
"""
from __future__ import annotations

import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path

INBOX_DIR = "F:/backup/00 - Inbox"
NS_DIR = "F:/backup/nervous-system"
MAX_DEPTH = 3

# ---------------------------------------------------------------------------
# Scoring tables
# ---------------------------------------------------------------------------
TYPE_SCORE = {
    "proposal": 40,
    "spec": 38,
    "strategy": 36,
    "architecture": 35,
    "design": 30,
    "runbook": 25,
    "report": 20,
    "research": 18,
    "prompt": 12,
    "idea": 35,
    "plan": 30,
    "pitch": 32,
    "moc": 10,
    "knowledge": 8,
    "checklist": 8,
    "digest": 5,
    "log": 2,
}

STATUS_MULT = {
    "ready": 1.2,
    "active": 1.1,
    "draft": 1.0,
    "inbox": 0.9,
    "stalled": 0.7,
    "archived": 0.3,
    "done": 0.2,
    "rejected": 0.1,
}

TAG_BONUS = {
    "architecture": 4,
    "genome": 4,
    "agents": 4,
    "self-improvement": 4,
    "strategic": 4,
    "build-proposal": 4,
    "codegen": 3,
    "ops": 3,
    "dashboard": 3,
    "second-brain": 3,
    "autonomy": 3,
    "evolution": 3,
    "self-improving": 4,
    "reflexion": 3,
    "mycelial": 3,
    "research": 2,
    "marketing": 2,
    "mining": 2,
    "crypto": 2,
    "accounting": 2,
    "lead": 2,
    "ziman": 2,
    "fable5": 2,
}

TITLE_KEYWORD_BONUS = {
    "master": 5,
    "spec": 4,
    "architecture": 4,
    "genome": 4,
    "strategy": 4,
    "hybrid": 4,
    "coherence": 3,
    "master-plan": 5,
    "proposal": 3,
    "design": 3,
    "runbook": 3,
    "panel": 3,
    "roadmap": 3,
    "backlog": 3,
    "deep": 2,
    "gap": 2,
    "analysis": 2,
    "audit": 2,
}

PATH_BONUS = {
    "build-proposals": 15,
    "system-review": 10,
    "replication-kit": 8,
    "scout-digests": -15,
}

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _parse_frontmatter(text: str) -> tuple[dict, str]:
    """Extract simple key:value frontmatter between --- fences."""
    if not text.startswith("---"):
        return {}, text
    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}, text
    fm_text = parts[1].strip()
    body = parts[2].strip()
    fm: dict[str, str | list] = {}
    for line in fm_text.splitlines():
        line = line.rstrip()
        if ":" not in line or line.startswith("#"):
            continue
        key, val = line.split(":", 1)
        key = key.strip().lower()
        val = val.strip().strip('"').strip("'")
        # YAML list: [a, b] or inline dash list
        if val.startswith("[") and val.endswith("]"):
            items = [v.strip().strip('"').strip("'") for v in val[1:-1].split(",")]
            fm[key] = [i for i in items if i]
        elif val.startswith("-"):
            # part of a multiline list — skip for simplicity
            pass
        else:
            fm[key] = val
    return fm, body


def _extract_h1(body: str) -> str | None:
    m = re.search(r"^#\s+(.+)$", body, re.MULTILINE)
    if m:
        return m.group(1).strip()
    return None


def _extract_snippet(body: str, length: int = 160) -> str:
    # Remove code blocks, headers, tables for snippet
    cleaned = re.sub(r"```[\s\S]*?```", "", body)
    cleaned = re.sub(r"`[^`]+`", "", cleaned)
    cleaned = re.sub(r"^#+\s.*$", "", cleaned, flags=re.MULTILINE)
    cleaned = re.sub(r"^\|.*\|$", "", cleaned, flags=re.MULTILINE)
    cleaned = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", cleaned)
    cleaned = re.sub(r"\[\[([^\]]+)\]\]", r"\1", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned[:length] + "…" if len(cleaned) > length else cleaned


def _parse_date(val: str | None) -> datetime | None:
    if not val:
        return None
    for fmt in ("%Y-%m-%d", "%Y-%m-%d %H:%M", "%Y-%m-%dT%H:%M:%S"):
        try:
            return datetime.strptime(val, fmt)
        except ValueError:
            continue
    return None


def _score_idea(idea: dict) -> float:
    """Compute strategic-value score 0-100."""
    score = 0.0

    # Type base
    t = idea.get("type", "")
    score += TYPE_SCORE.get(t, 10)

    # Status multiplier applied to base
    s = idea.get("status", "")
    mult = STATUS_MULT.get(s, 0.85)
    score *= mult

    # Path bonus
    rel = idea.get("source_path", "")
    for seg, bonus in PATH_BONUS.items():
        if seg in rel.replace("\\", "/").lower():
            score += bonus
            break

    # Tag bonus
    tags = idea.get("tags", [])
    if isinstance(tags, str):
        tags = [tags]
    for tag in tags:
        score += TAG_BONUS.get(tag.lower(), 0.3)
    score = min(score, score + 3)  # cap misc-tag bonus roughly

    # Title keyword bonus
    title = idea.get("title", "")
    title_lo = title.lower()
    for kw, bonus in TITLE_KEYWORD_BONUS.items():
        if kw in title_lo:
            score += bonus
            title_lo = title_lo.replace(kw, "", 1)  # avoid double-count same word

    # Word count bonus (up to +5)
    wc = idea.get("word_count", 0)
    score += min(wc / 400, 5)

    # Freshness
    updated = _parse_date(idea.get("updated"))
    created = _parse_date(idea.get("created"))
    dt = updated or created
    if dt:
        age_days = (datetime.now() - dt).days
        if age_days <= 3:
            score += 4
        elif age_days <= 7:
            score += 3
        elif age_days <= 14:
            score += 1.5
        elif age_days <= 30:
            score += 0.5
        else:
            score -= min(age_days / 60, 3)  # mild decay

    # Clamp
    return max(0.0, min(100.0, round(score, 1)))


def _is_idea_candidate(fm: dict, rel_path: str) -> bool:
    """Filter out obvious non-ideas (logs, diaries, raw data)."""
    lo = rel_path.lower().replace("\\", "/")
    # Always include build-proposals and system-review
    if "build-proposals/" in lo or "system-review" in lo:
        return True
    # Exclude scout digests unless they look like proposals
    if "scout-digests/" in lo:
        return False
    # Exclude replication-kit readme/blueprint unless flagged
    if "replication-kit/" in lo:
        t = str(fm.get("type", "")).lower()
        return t in ("proposal", "spec", "plan", "design", "report")
    # Exclude obvious logs
    base = os.path.basename(lo)
    if base.startswith("overnight-log") or base.startswith("ui-build-log") or base.startswith("_"):
        return False
    t = str(fm.get("type", "")).lower()
    if t in ("log", "digest", "checklist", "moc") and "build-proposals/" not in lo:
        return False
    return True


def _make_id(rel_path: str) -> str:
    base = os.path.splitext(os.path.basename(rel_path))[0]
    base = re.sub(r"^\d{4}-\d{2}-\d{2}\s+", "", base)
    base = base.strip()
    return base


def main() -> None:
    os.makedirs(NS_DIR, exist_ok=True)
    generated = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    ideas: list[dict] = []
    errors: list[str] = []

    inbox_path = Path(INBOX_DIR)
    for root, _dirs, files in os.walk(INBOX_DIR):
        depth = len(Path(root).relative_to(inbox_path).parts)
        if depth > MAX_DEPTH:
            continue
        for fname in files:
            if not fname.lower().endswith(".md"):
                continue
            fpath = os.path.join(root, fname)
            rel = os.path.relpath(fpath, INBOX_DIR)
            try:
                with open(fpath, "r", encoding="utf-8") as f:
                    raw = f.read()
            except (OSError, UnicodeDecodeError) as exc:
                errors.append(f"{rel}: {exc}")
                continue

            fm, body = _parse_frontmatter(raw)
            if not _is_idea_candidate(fm, rel):
                continue

            title = _extract_h1(body) or fm.get("title", "")
            if not title:
                title = os.path.splitext(fname)[0]

            word_count = len(body.split())
            snippet = _extract_snippet(body, 180)

            idea = {
                "id": _make_id(rel),
                "title": title,
                "source_path": f"00 - Inbox/{rel.replace(chr(92), '/')}",
                "type": str(fm.get("type", "note")).lower(),
                "status": str(fm.get("status", "unknown")).lower(),
                "tags": fm.get("tags", []),
                "created": fm.get("created", ""),
                "updated": fm.get("updated", ""),
                "word_count": word_count,
                "snippet": snippet,
            }
            idea["strategic_score"] = _score_idea(idea)
            ideas.append(idea)

    # Sort by strategic score descending, then updated date
    ideas.sort(key=lambda x: (x["strategic_score"], x.get("updated", "")), reverse=True)
    for idx, idea in enumerate(ideas, start=1):
        idea["rank"] = idx
        sc = idea["strategic_score"]
        if sc >= 70:
            idea["tier"] = "gold"
        elif sc >= 45:
            idea["tier"] = "silver"
        elif sc >= 25:
            idea["tier"] = "bronze"
        else:
            idea["tier"] = "backlog"

    # Summaries
    by_status: dict[str, int] = {}
    by_type: dict[str, int] = {}
    for idea in ideas:
        by_status[idea["status"]] = by_status.get(idea["status"], 0) + 1
        by_type[idea["type"]] = by_type.get(idea["type"], 0) + 1

    top_tier = [i for i in ideas if i["tier"] == "gold"]
    ready_to_build = [i for i in ideas if i["status"] in ("ready", "active")]
    draft_proposals = [i for i in ideas if i["status"] == "draft"]
    research_pending = [i for i in ideas if i["type"] in ("research", "report")]

    ideas_data = {
        "generated": generated,
        "channel": "CH-12: Company Ideas → Backlog",
        "summary": {
            "total_ideas": len(ideas),
            "by_status": by_status,
            "by_type": by_type,
            "avg_strategic_score": round(sum(i["strategic_score"] for i in ideas) / len(ideas), 1) if ideas else 0.0,
            "top_tier_count": len(top_tier),
            "ready_to_build_count": len(ready_to_build),
            "draft_count": len(draft_proposals),
            "research_pending_count": len(research_pending),
        },
        "ideas": ideas,
        "backlog": {
            "ready_to_build": [{"id": i["id"], "title": i["title"], "score": i["strategic_score"]} for i in ready_to_build[:20]],
            "draft_proposals": [{"id": i["id"], "title": i["title"], "score": i["strategic_score"]} for i in draft_proposals[:20]],
            "research_pending": [{"id": i["id"], "title": i["title"], "score": i["strategic_score"]} for i in research_pending[:20]],
            "top_tier": [{"id": i["id"], "title": i["title"], "score": i["strategic_score"], "tier": i["tier"]} for i in top_tier[:15]],
        },
        "meta": {
            "errors": errors,
            "sources_scanned": INBOX_DIR,
            "max_depth": MAX_DEPTH,
        },
    }

    js = "window.IDEAS_DATA = " + json.dumps(ideas_data, ensure_ascii=False, default=str) + ";\n"
    out_path = os.path.join(NS_DIR, "ideas-data.js")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(js)

    print(
        f"[extract_ideas_backlog] ideas-data.js refreshed: {len(js)} chars, "
        f"{len(ideas)} ideas, {len(top_tier)} gold, {len(ready_to_build)} ready, "
        f"{len(errors)} errors"
    )


if __name__ == "__main__":
    main()
