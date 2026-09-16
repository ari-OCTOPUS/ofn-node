"""Lab memory store with mandatory read-back. Live 4d/vault is read-only if present."""
from __future__ import annotations

import hashlib
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_OPS = Path(__file__).resolve().parents[2]
_VAULT = _OPS.parent
_4D_DB = _VAULT / "4d_system" / "outputs" / "4d_experiments.db"


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def lab_path(store: Path) -> Path:
    p = Path(store) / "lab-memory.jsonl"
    p.parent.mkdir(parents=True, exist_ok=True)
    return p


def write_lab(store: Path, *, task_id: str, kind: str, payload: dict[str, Any]) -> dict[str, Any]:
    rec = {
        "schema": "full-loop-lab-memory.v1",
        "id": "",
        "task_id": task_id,
        "kind": kind,
        "ts": datetime.now(timezone.utc).isoformat(),
        "payload": payload,
        "executable": False,
    }
    rec["id"] = "lm-" + _sha(json.dumps(rec, sort_keys=True, default=str))[:16]
    rec["record_hash"] = _sha(json.dumps(rec, sort_keys=True, default=str))
    p = lab_path(store)
    with p.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
    return rec


def read_lab(store: Path, record_id: str) -> dict[str, Any] | None:
    p = lab_path(store)
    if not p.exists():
        return None
    for ln in p.read_text(encoding="utf-8").splitlines():
        if not ln.strip():
            continue
        rec = json.loads(ln)
        if rec.get("id") == record_id:
            return rec
    return None


def retrieve_for_task(task: dict[str, Any], store: Path) -> dict[str, Any]:
    """task → retrieve (live try + lab) → evidence IDs. Live writers are never called."""
    q = (task.get("summary") or task.get("task_id") or "frontmatter")[:200]
    live = {
        "query_experiments": _ro_query_experiments(),
        "get_pending_hypotheses": _ro_pending_hypotheses(),
        "search_vault": _try_search_vault(q),
        "memory_read_patch": "NOT_CALLED_AVOIDS_ENSURE_DB_WRITE",
    }
    evidence_ids: list[str] = []
    snippets: list[str] = []
    for key, block in live.items():
        if isinstance(block, dict) and block.get("status") == "PASS":
            for item in block.get("items") or []:
                eid = item.get("id") or item.get("evidence_id")
                if eid:
                    evidence_ids.append(f"{key}:{eid}")
                snippets.append(str(item.get("excerpt") or item.get("hypothesis") or item.get("text") or "")[:240])
        elif isinstance(block, dict) and block.get("status"):
            evidence_ids.append(f"{key}:{block['status']}")

    seed = write_lab(store, task_id=str(task.get("task_id")), kind="retrieve", payload={
        "query": q,
        "live": {k: (v.get("status") if isinstance(v, dict) else v) for k, v in live.items()},
        "snippets": snippets[:8],
    })
    back = read_lab(store, seed["id"])
    readback_ok = bool(back) and back.get("record_hash") == seed.get("record_hash")
    if readback_ok:
        evidence_ids.append(seed["id"])
    return {
        "schema": "full-loop-memory.v1",
        "query": q,
        "live": live,
        "lab_record_id": seed["id"],
        "readback": "PASS" if readback_ok else "FAIL",
        "evidence_ids": evidence_ids,
        "snippets": snippets[:8],
        "wrote_4d_db": False,
        "wrote_ops_state": False,
        "memory_gate": "PASS" if readback_ok else "FAIL",
        "live_memory_label": _live_label(live),
    }


def _live_label(live: dict[str, Any]) -> str:
    statuses = [v.get("status") for v in live.values() if isinstance(v, dict)]
    if any(s == "PASS" for s in statuses):
        return "PARTIAL_LIVE_PLUS_LAB"
    return "LAB_ONLY_LIVE_UNLOCATED"


def _ro_query_experiments(limit: int = 5) -> dict[str, Any]:
    if not _4D_DB.exists():
        return {"status": "UNLOCATED", "reason": "4d_experiments.db missing", "items": []}
    try:
        uri = _4D_DB.resolve().as_uri() + "?mode=ro"
        conn = sqlite3.connect(uri, uri=True, timeout=5)
        conn.row_factory = sqlite3.Row
        try:
            rows = conn.execute(
                "SELECT id, timestamp, source, verdict FROM experiments ORDER BY timestamp DESC LIMIT ?",
                (limit,),
            ).fetchall()
        finally:
            conn.close()
        items = [{"id": r["id"], "excerpt": f"{r['source']}:{r['verdict']}", "ts": r["timestamp"]} for r in rows]
        return {"status": "PASS", "items": items, "n": len(items), "mode": "sqlite_readonly"}
    except Exception as e:  # noqa: BLE001 — fail-soft, no secret
        return {"status": "UNLOCATED", "reason": type(e).__name__, "items": []}


def _ro_pending_hypotheses(limit: int = 5) -> dict[str, Any]:
    if not _4D_DB.exists():
        return {"status": "UNLOCATED", "reason": "4d_experiments.db missing", "items": []}
    try:
        uri = _4D_DB.resolve().as_uri() + "?mode=ro"
        conn = sqlite3.connect(uri, uri=True, timeout=5)
        conn.row_factory = sqlite3.Row
        try:
            rows = conn.execute(
                "SELECT id, timestamp, hypothesis, status FROM hypotheses "
                "WHERE IFNULL(status,'pending')='pending' ORDER BY timestamp DESC LIMIT ?",
                (limit,),
            ).fetchall()
        finally:
            conn.close()
        items = [{"id": r["id"], "hypothesis": str(r["hypothesis"])[:200], "ts": r["timestamp"]} for r in rows]
        return {"status": "PASS", "items": items, "n": len(items), "mode": "sqlite_readonly"}
    except Exception as e:  # noqa: BLE001
        return {"status": "UNLOCATED", "reason": type(e).__name__, "items": []}


def _try_search_vault(query: str) -> dict[str, Any]:
    try:
        import sys
        mem = str(_OPS / "memory")
        if mem not in sys.path:
            sys.path.insert(0, mem)
        import vault_bridge as vb  # type: ignore
        hits = vb.search_vault_evidence(query, k=3) or []
        items = []
        for h in hits[:3]:
            if isinstance(h, dict):
                items.append({
                    "id": h.get("id") or h.get("path") or h.get("source"),
                    "excerpt": str(h.get("text") or h.get("excerpt") or "")[:240],
                })
        return {"status": "PASS" if items else "EMPTY", "items": items, "n": len(items)}
    except Exception as e:  # noqa: BLE001
        return {"status": "UNLOCATED", "reason": type(e).__name__, "items": []}
