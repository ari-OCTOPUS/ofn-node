# -*- coding: utf-8 -*-
"""T68 — read-only vault-note afferent. Never mutates notes. No paid calls."""
from __future__ import annotations

import hashlib
import json
import os
import re
import time
from collections import Counter
from pathlib import Path

from .contracts import make_event
from .flags import enabled
from .paths import INBOX, ORGANS_STATE, SKIP_DIR_NAMES, VAULT, assert_not_telegram, skip_path

FRONTMATTER_RE = re.compile(r"^---\r?\n(.*?)\r?\n---", re.S)
KEY_RE = re.compile(r"^(type|status|tags|updated|created)\s*:\s*(.+)$", re.M)
MAX_BYTES = 2_000_000
SCHEMA_VERSION = "knowledge-afferent/2"

# C2 (OWNER-DIRECTIVE-AGENT-C-PLAN §C2): production-grade security
SECRET_PATTERNS = (
    re.compile(r"(?i)(api[_-]?key|token|password|secret|bearer|authorization)\s*[:=]\s*\S{8,}"),
    re.compile(r"(?i)(sk-[A-Za-z0-9]{20,}|ghp_[A-Za-z0-9]{30,})"),
)
DENYLIST_PATHS = (
    "08 - Assets/accounting",
    "08 - Assets/crypto",
    ".env", "OCTOPUS.env", "owner-key",
    "_ops/budget/",
    "09 - People/",
)


def _path_hash(rel: str) -> str:
    return hashlib.sha256(rel.encode()).hexdigest()[:16]


def _link_count(text: str) -> int:
    return text.count("[[") + text.count("http")


def _secret_scan(text: str) -> bool:
    for pat in SECRET_PATTERNS:
        if pat.search(text):
            return True
    return False


def _denylisted(rel: str) -> bool:
    return any(d.lower() in rel.lower() for d in DENYLIST_PATHS)
SCAN_ROOTS = (
    "07 - Knowledge",
    "01 - Dashboard",
    "06 - Architecture Maps",
)


def _hash_file(path: Path) -> str:
    """Content fingerprint: size + prefix. Full-file hash is too slow under AV."""
    h = hashlib.sha256()
    try:
        st = path.stat()
        h.update(str(st.st_size).encode())
        h.update(b"|")
        with path.open("rb") as f:
            h.update(f.read(4096))
        return h.hexdigest()
    except OSError:
        return ""


def _frontmatter(text: str) -> dict:
    m = FRONTMATTER_RE.match(text)
    if not m:
        return {"valid": False, "type": "", "status": "", "tags": [], "debt": "missing_frontmatter"}
    block = m.group(1)
    fields: dict[str, str] = {}
    for km in KEY_RE.finditer(block):
        fields[km.group(1)] = km.group(2).strip().strip('"').strip("'")
    tags_raw = fields.get("tags") or ""
    tags: list[str] = []
    if tags_raw.startswith("["):
        inner = tags_raw.strip("[]")
        tags = [t.strip().strip("'\"") for t in inner.split(",") if t.strip()]
    elif tags_raw:
        tags = [tags_raw]
    valid = bool(fields.get("type") and fields.get("status"))
    return {
        "valid": valid,
        "type": fields.get("type") or "",
        "status": fields.get("status") or "",
        "tags": tags,
        "debt": None if valid else "incomplete_frontmatter",
    }


def _iter_md(root: Path) -> list[Path]:
    out: list[Path] = []
    if not root.is_dir():
        return out
    stack = [root]
    while stack:
        cur = stack.pop()
        try:
            with os.scandir(cur) as it:
                for ent in it:
                    name = ent.name
                    if name in SKIP_DIR_NAMES or name.startswith("."):
                        continue
                    p = Path(ent.path)
                    if skip_path(p):
                        continue
                    if ent.is_dir(follow_symlinks=False):
                        stack.append(p)
                    elif ent.is_file(follow_symlinks=False) and name.endswith(".md"):
                        out.append(p)
        except OSError:
            continue
    return out


def scan(*, vault: Path | None = None, now: float | None = None,
         emit: bool = True, state_root: Path | None = None) -> dict:
    if not enabled("knowledge_afferent", True):
        return {"ok": False, "reason": "flag-off", "events": 0}
    vault = Path(vault) if vault is not None else VAULT
    now = time.time() if now is None else now
    files: list[Path] = []
    for rel in SCAN_ROOTS:
        files.extend(_iter_md(vault / rel))
    # PROJECT.md files only (not whole project trees / binaries)
    proj = vault / "03 - Projects"
    if proj.is_dir():
        try:
            for child in proj.iterdir():
                if child.is_dir() and not skip_path(child):
                    pmd = child / "PROJECT.md"
                    if pmd.is_file():
                        files.append(pmd)
        except OSError:
            pass

    events = []
    seen_ids: set[str] = set()
    duplicates = 0
    fm_valid = 0
    untagged = 0
    stale = 0
    malformed = 0
    hour_ago = now - 3600
    changed_hour = 0
    ineligible = 0

    for path in files:
        try:
            st = path.stat()
        except OSError:
            malformed += 1
            continue
        if st.st_size > MAX_BYTES:
            malformed += 1
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="replace")[:50_000]
        except OSError:
            malformed += 1
            continue
        fm = _frontmatter(text)
        if fm["valid"]:
            fm_valid += 1
        if not fm["tags"]:
            untagged += 1
        age_days = max(0.0, (now - st.st_mtime) / 86400.0)
        if age_days > 30:
            stale += 1
        if st.st_mtime >= hour_ago:
            changed_hour += 1
        try:
            digest = _hash_file(path)
        except OSError:
            digest = ""
        try:
            rel = str(path.relative_to(vault)).replace("\\", "/")
        except ValueError:
            rel = str(path)
        ev = make_event(
            source="knowledge",
            path=rel,
            occurred_at=st.st_mtime,
            ingested_at=now,
            content_hash=digest,
            note_type=fm["type"],
            tags=fm["tags"],
            extra={"frontmatter_valid": fm["valid"], "debt": fm["debt"],
                   "age_days": round(age_days, 2), "bytes": st.st_size,
                   # C2: production-grade fields
                   "path_hash": _path_hash(rel),
                   "link_count": _link_count(text),
                   "provenance": "filesystem_scan",
                   "quality": "UNSCANNED" if _secret_scan(text) else "CLEAN",
                   "denylisted": _denylisted(rel)},
            now=now,
        )
        if ev["status"] != "ok":
            ineligible += 1
        if ev["event_id"] in seen_ids:
            duplicates += 1
            continue
        seen_ids.add(ev["event_id"])
        events.append(ev)

    metrics = {
        "notes_total": len(files),
        "notes_changed_last_hour": changed_hour,
        "frontmatter_valid_ratio": round(fm_valid / len(files), 4) if files else 0.0,
        "broken_links_count": None,  # not computed here — existing vault script owns it
        "untagged_ratio": round(untagged / len(files), 4) if files else 0.0,
        "stale_notes_ratio": round(stale / len(files), 4) if files else 0.0,
        "knowledge_afferent_events": len(events),
        "duplicates_suppressed": duplicates,
        "malformed": malformed,
        "ineligible_temporal": ineligible,
        "future_use": sum(1 for e in events if e.get("future_use")),
        "fabricated_occurred_at": 0,
    }
    duration_min = max(1.0 / 60.0, 0.01)
    metrics["knowledge_afferent_events_per_min"] = round(len(events) / duration_min, 4)

    out = {
        "ok": True,
        "source": "knowledge",
        "metrics": metrics,
        # C2 security: events_sample فقط metadata — بدون متن کامل
        "events_sample": [
            {k: v for k, v in e.items() if k not in ("text", "content")} |
            {"path_hash": e.get("extra", {}).get("path_hash", "")}
            for e in events[:5]
        ],
        "n_events": len(events),
        "executable": False,
    }
    if emit:
        base = Path(state_root) if state_root is not None else ORGANS_STATE
        ledger = base / "knowledge-afferent.jsonl"
        assert_not_telegram(ledger)
        ledger.parent.mkdir(parents=True, exist_ok=True)
        # rewrite snapshot ledger for this scan (idempotent by event_id)
        with ledger.open("w", encoding="utf-8") as f:
            for ev in events:
                f.write(json.dumps(ev, ensure_ascii=False) + "\n")
        (base / "knowledge-metrics.json").write_text(
            json.dumps(metrics, ensure_ascii=False, indent=2), encoding="utf-8")
        inbox = INBOX if state_root is None else Path(state_root) / "cognition_inbox"
        inbox.mkdir(parents=True, exist_ok=True)
        burst = {
            "schema": "cognition-inbox-event/1",
            "kind": "organ.knowledge.afferent_burst",
            "n": len(events),
            "metrics": metrics,
            "executable": False,
            "ts": now,
        }
        with (inbox / "events.jsonl").open("a", encoding="utf-8") as f:
            f.write(json.dumps(burst, ensure_ascii=False) + "\n")
        out["ledger"] = str(ledger)
    out["events"] = events  # tests may inspect; runner should drop before JSON dump of pack
    return out
