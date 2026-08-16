"""owner_recall.py — cite-only recall for owner Ask/Collaborator.

ADR / megaprompt Awareness-Memory-Ask 2026-08-12.
Read-only · fail-soft · may_authorize always False · never grants effects.
"""
from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any

_HERE = Path(__file__).resolve().parent
_OPS = _HERE.parent

_AWARE_HINT = re.compile(
    r"(خودآگاه|تشکیل|improve|خودبهبود|self.?loop|حافظه|یاد|مانع|موانع|"
    r"runtime|هدف|selfmap|نقشه|synthesis|research|کشف)",
    re.I,
)


def topic_wants_recall(query: str) -> bool:
    q = str(query or "").strip()
    if not q:
        return False
    return bool(_AWARE_HINT.search(q))


def recall_for_owner_ask(query: str, limit: int = 3) -> list[dict[str, Any]]:
    """Return cite-only facts for owner surfaces.

    Shape: [{content_preview, mkey, trust, namespace, source_path, may_authorize}]
    Gate off / DB missing / errors → [] (never raise).
    """
    out: list[dict[str, Any]] = []
    lim = max(1, min(int(limit or 3), 8))
    q = str(query or "").strip()
    # Soft query: long owner questions rarely substring-match trail content.
    # Prefer short tokens; fall back to recent selfloop/improve cite.
    tokens = re.findall(r"[A-Za-z_]{3,}|[\u0600-\u06FF]{3,}", q)
    soft_q = ""
    for pref in ("improve", "selfloop", "self_loop", "synthesis", "research",
                 "خودبهبود", "حافظه", "خودآگاه"):
        if pref.lower() in q.lower() or any(pref in t for t in tokens):
            soft_q = "improve" if "improve" in pref or "خودبهبود" in pref else pref
            break
    if not soft_q and tokens:
        soft_q = tokens[0]

    # 1) MemoryGate episodic (when ON)
    try:
        import gate as mg  # noqa: WPS433 — same package dir
        import memory_store as ms  # noqa: WPS433
        if mg.flag_on():
            store = ms.MemoryStore()
            try:
                for probe in (soft_q, "selfloop", "improve", q):
                    if not probe:
                        continue
                    rows = store.search(probe, namespace="episodic", k=lim * 3) or []
                    for r in rows:
                        if not isinstance(r, dict):
                            continue
                        mkey = str(r.get("mkey") or "")
                        content = str(r.get("content") or "")[:280]
                        if not content and not mkey:
                            continue
                        if any(f.get("mkey") == mkey for f in out):
                            continue
                        out.append({
                            "content_preview": content,
                            "mkey": mkey,
                            "trust": r.get("trust") or "GRADED",
                            "namespace": r.get("namespace") or "episodic",
                            "source_path": "memory.db",
                            "may_authorize": False,
                            "provenance": "memory_store",
                        })
                        if len(out) >= lim:
                            break
                    if len(out) >= lim:
                        break
            finally:
                try:
                    store.close()
                except Exception:  # noqa: BLE001
                    pass
    except Exception:  # noqa: BLE001
        pass

    # 2) self-loop trail fallback (works even if gate/DB cold)
    if len(out) < lim:
        try:
            import self_loop_ingest as sli  # noqa: WPS433
            for row in (sli.recall_recent(soft_q or "", k=lim)
                        or sli.recall_recent("", k=lim)
                        or []):
                if not isinstance(row, dict):
                    continue
                mkey = str(row.get("mkey") or "")
                if any(f.get("mkey") == mkey for f in out):
                    continue
                out.append({
                    "content_preview": str(row.get("content") or "")[:280],
                    "mkey": mkey,
                    "trust": row.get("trust") or "GRADED",
                    "namespace": "episodic",
                    "source_path": "state/memory/self-loop-ingest.jsonl",
                    "may_authorize": False,
                    "provenance": row.get("provenance") or "self_loop_ingest",
                    "channel": row.get("channel"),
                })
                if len(out) >= lim:
                    break
        except Exception:  # noqa: BLE001
            pass

    # 2b) ۲۰۲۶-۰۸-۱۶ — consolidation similar_keys (distant recall) cite-only
    # مسیرِ گمشدهٔ تزریق: similar_keys نوشته می‌شد ولی به تصمیم/پرسش نمی‌رسید.
    if len(out) < lim:
        try:
            import json as _json
            cons = _OPS / "neural" / "consolidation.json"
            hist = _json.loads(cons.read_text(encoding="utf-8"))
            if isinstance(hist, list):
                for row in reversed(hist):
                    if not isinstance(row, dict):
                        continue
                    keys = row.get("similar_keys") or []
                    if not keys:
                        continue
                    insights = row.get("insights") or []
                    preview = " · ".join(str(x) for x in insights[:2])[:200]
                    own = row.get("cycle")
                    out.append({
                        "content_preview": preview or f"consolidation cycle-{own}",
                        "mkey": f"consolidation:cycle-{own}",
                        "trust": "GRADED",
                        "namespace": "consolidation",
                        "source_path": "neural/consolidation.json",
                        "may_authorize": False,
                        "provenance": "consolidation.similar_keys",
                        "similar_keys": list(keys)[:8],
                    })
                    break
        except Exception:  # noqa: BLE001
            pass

    # 3) collab episodic digests (content-free markers — cite path only)
    if len(out) < lim:
        try:
            import sys
            oc = str(_OPS / "owner_console")
            if oc not in sys.path:
                sys.path.insert(0, str(_OPS))
            from owner_console import collab_memory  # noqa: WPS433
            for row in collab_memory.recent(limit=8) or []:
                if not isinstance(row, dict):
                    continue
                summary = str(row.get("summary") or row.get("intent") or "")[:200]
                tid = str(row.get("turn_id") or "")
                out.append({
                    "content_preview": summary or f"collab turn {tid}",
                    "mkey": f"collab:{tid}" if tid else "collab:recent",
                    "trust": "EPISODIC_DIGEST",
                    "namespace": "collab",
                    "source_path": "state/collab-memory.jsonl",
                    "may_authorize": False,
                    "provenance": "collab_memory",
                })
                if len(out) >= lim:
                    break
        except Exception:  # noqa: BLE001
            pass

    # Hard invariant: never claim authorize
    for f in out:
        f["may_authorize"] = False
    return out[:lim]


def facts_block_for_context(facts: list[dict[str, Any]], *, limit_chars: int = 400) -> str:
    """Format facts for LLM/self_context — paths only, no secrets."""
    if not facts:
        return "حافظهٔ اخیر: recall خالی (شاهد مسیر یافت نشد)."
    lines = ["حافظهٔ اخیر (cite-only، may_authorize=false):"]
    for f in facts[:5]:
        mkey = f.get("mkey") or "?"
        path = f.get("source_path") or "?"
        prev = str(f.get("content_preview") or "")[:120].replace("\n", " ")
        lines.append(f"- [{path}] {mkey}: {prev}")
    text = "\n".join(lines)
    return text[:limit_chars]
