#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""research_ingest.py — bridge: web_research digest → MemoryGate episodic + provenance trail.

چرا: research-latest.json هر بار overwrite می‌شود؛ بدون ingest، یادگیری API «هدر» می‌رود.
این ماژول additive است: هیچ halt/APPLY/outbound نمی‌سازد؛ فقط شواهد episodic + jsonl.

قواعد:
  · Memory هرگز مجوز نیست (هم‌تراز retrieval_router / Metaphor Decode).
  · flag-off MemoryGate → فقط jsonl trail (fail-soft، بدون DB).
  · content بدون secret خام؛ URL/title/snippet کوتاه.
  · stdlib · صفر شبکه.
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

_HERE = Path(__file__).resolve().parent
_OPS = _HERE.parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))
if str(_OPS) not in sys.path:
    sys.path.insert(0, str(_OPS))

SCHEMA = "research-ingest.v1"
_MAX_HITS = 24
_SNIPPET_MAX = 280


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _state_root() -> Path:
    """Same root family as MemoryStore: OCTOPUS_STATE_DIR, else OPS_DIR/state, else _ops/state."""
    st = (os.environ.get("OCTOPUS_STATE_DIR") or "").strip()
    if st:
        return Path(st)
    ops = (os.environ.get("OPS_DIR") or "").strip()
    if ops:
        return Path(ops) / "state"
    return _OPS / "state"


def trail_path(root: Optional[Path] = None) -> Path:
    """root may be state-root OR ops-root; normalize to …/state/memory/research-ingest.jsonl."""
    if root is None:
        return _state_root() / "memory" / "research-ingest.jsonl"
    root = Path(root)
    if root.name == "state" or (root / "memory").exists() or (root / "pulse").exists():
        return root / "memory" / "research-ingest.jsonl"
    return root / "state" / "memory" / "research-ingest.jsonl"


def _sha(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def _hit_content(topic: str, hit: dict) -> str:
    title = str(hit.get("title") or "").strip()[:160]
    url = str(hit.get("url") or "").strip()[:300]
    snippet = str(hit.get("snippet") or "").strip()[:_SNIPPET_MAX]
    src = str(hit.get("source") or "").strip()[:40]
    parts = [f"topic={topic}", f"source={src}", f"title={title}"]
    if url:
        parts.append(f"url={url}")
    if snippet:
        parts.append(f"snippet={snippet}")
    return " | ".join(parts)


def _append_trail(path: Path, rec: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")


def _gate_submit(candidate: dict, gate: Optional[Any] = None) -> dict:
    """Submit via MemoryGate when flag on; never raises to caller."""
    owns = False
    store = None
    try:
        import gate as mg
        import memory_store as ms
        if gate is None:
            if not mg.flag_on():
                return {"verb": "skip", "reason": "flag-off"}
            store = ms.MemoryStore()
            gate = mg.MemoryGate(store)
            owns = True
        return gate.submit(candidate)
    except Exception as e:  # noqa: BLE001
        return {"verb": "skip", "reason": f"gate-error:{type(e).__name__}"}
    finally:
        if owns and store is not None:
            try:
                store.close()
            except Exception:  # noqa: BLE001
                pass


def ingest_digest(digest: dict, *, root: Optional[Path] = None,
                  max_hits: int = _MAX_HITS) -> dict:
    """Persist research findings into episodic memory + append-only trail.

    Returns summary: {ok, schema, n_hits, committed, proposed, skipped, rejected, trail}.
    """
    if not isinstance(digest, dict):
        return {"ok": False, "error": "digest must be dict", "schema": SCHEMA}
    findings = digest.get("findings") or []
    if not isinstance(findings, list):
        findings = []

    trail = trail_path(root)
    committed = proposed = skipped = rejected = 0
    n = 0
    digest_ts = str(digest.get("ts") or _utc_now_iso())
    digest_sha = _sha(json.dumps(digest, sort_keys=True, ensure_ascii=False)[:8000])

    gate = None
    store = None
    try:
        import gate as mg
        import memory_store as ms
        if mg.flag_on():
            store = ms.MemoryStore()
            gate = mg.MemoryGate(store)
    except Exception:  # noqa: BLE001
        gate = None
        store = None

    try:
        for block in findings:
            if n >= max_hits:
                break
            if not isinstance(block, dict):
                continue
            topic = str(block.get("topic") or "").strip()[:120]
            hits = block.get("hits") or []
            if not isinstance(hits, list):
                continue
            for hit in hits:
                if n >= max_hits:
                    break
                if not isinstance(hit, dict):
                    continue
                title = str(hit.get("title") or "").strip()
                if not title:
                    continue
                content = _hit_content(topic, hit)
                url = str(hit.get("url") or "").strip()
                mkey = "research:" + _sha(url or f"{topic}|{title}")[:24]
                candidate = {
                    "namespace": "episodic",
                    "mkey": mkey,
                    "content": content,
                    "source": "web_research",
                    "producer": "research_ingest",
                    "privacy": "scrubbed",
                    "scope": "project",
                    "classification": "internal",
                    "tenant_id": "personal",
                    "project_id": "octopus-core",
                    "agent_id": "web_research",
                    "task_id": "research_ingest",
                    "confidence": 0.55,
                    "salience": 0.5,
                    "inputs_sha": digest_sha,
                    "admission_state": "ADMITTED",
                    "policy_version": "research-ingest.v1",
                }
                if gate is not None:
                    result = _gate_submit(candidate, gate=gate)
                else:
                    result = {"verb": "skip", "reason": "flag-off"}
                verb = str(result.get("verb") or "skip")
                if verb == "commit":
                    committed += 1
                elif verb == "propose":
                    proposed += 1
                elif verb == "reject":
                    rejected += 1
                else:
                    skipped += 1

                trail_rec = {
                    "ts": _utc_now_iso(),
                    "schema": SCHEMA,
                    "digest_ts": digest_ts,
                    "digest_sha": digest_sha[:16],
                    "topic": topic,
                    "mkey": mkey,
                    "title": title[:160],
                    "url": url[:300],
                    "source": str(hit.get("source") or ""),
                    "gate_verb": verb,
                    "memory_id": result.get("memory_id"),
                    "reason": result.get("reason"),
                }
                try:
                    _append_trail(trail, trail_rec)
                except OSError:
                    pass
                n += 1
    finally:
        if store is not None:
            try:
                store.close()
            except Exception:  # noqa: BLE001
                pass

    return {
        "ok": True,
        "schema": SCHEMA,
        "n_hits": n,
        "committed": committed,
        "proposed": proposed,
        "skipped": skipped,
        "rejected": rejected,
        "trail": str(trail),
        "may_authorize": False,
    }


def recall_recent(query: str = "", *, k: int = 5,
                  root: Optional[Path] = None) -> list[dict[str, Any]]:
    """Read-only recall of research episodic rows (and/or trail fallback).

    Never grants authority — citations only.
    """
    q = (query or "").strip().lower()
    out: list[dict[str, Any]] = []

    # Prefer MemoryStore when gate path is available
    try:
        import gate as mg
        import memory_store as ms
        if mg.flag_on():
            store = ms.MemoryStore()
            try:
                rows = store.search(q or "research", namespace="episodic", k=max(k * 3, k)) or []
                for r in rows:
                    content = str(r.get("content") or "")
                    mkey = str(r.get("mkey") or "")
                    if not (mkey.startswith("research:") or "topic=" in content):
                        continue
                    if q and q not in content.lower() and q not in mkey.lower():
                        continue
                    out.append({
                        "memory_id": r.get("memory_id"),
                        "mkey": mkey,
                        "content": content[:400],
                        "trust": r.get("trust"),
                        "provenance": "memory_store",
                        "may_authorize": False,
                    })
                    if len(out) >= k:
                        return out
            finally:
                try:
                    store.close()
                except Exception:  # noqa: BLE001
                    pass
    except Exception:  # noqa: BLE001
        pass

    # Trail fallback (always available if ingest ran)
    path = trail_path(root)
    if not path.exists():
        return out
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return out
    for line in reversed(lines):
        if len(out) >= k:
            break
        line = line.strip()
        if not line:
            continue
        try:
            rec = json.loads(line)
        except json.JSONDecodeError:
            continue
        blob = f"{rec.get('topic','')} {rec.get('title','')} {rec.get('url','')}".lower()
        if q and q not in blob:
            continue
        out.append({
            "memory_id": rec.get("memory_id"),
            "mkey": rec.get("mkey"),
            "content": f"topic={rec.get('topic')} | title={rec.get('title')} | url={rec.get('url')}",
            "trust": "trail",
            "provenance": "research-ingest.jsonl",
            "may_authorize": False,
        })
    return out
