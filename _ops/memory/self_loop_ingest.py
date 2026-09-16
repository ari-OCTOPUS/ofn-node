#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""self_loop_ingest.py — durable provenance for self-awareness / self-heal / auto-improve.

Why: upgrades-digest, synthesis-latest, self-knowledge-latest, part-loops-latest, and
self-model overwrite every cycle; selfheal-events append but were never MemoryGate'd.
Without ingest, automation work is produced then orphaned.

Additive only:
  · always append state/memory/self-loop-ingest.jsonl
  · when OCTOPUS_WIRE_MEMORY_GATE=1 → episodic MemoryGate (GRADED, not OWNER)
  · may_authorize=False always — never halt/APPLY/outbound
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

SCHEMA = "self-loop-ingest.v1"
CHANNELS = frozenset({
    "improve", "synthesis", "self_knowledge", "part_loops",
    "selfheal", "self_model",
})
_MAX_ITEMS = 16
_CONTENT_MAX = 420


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _state_root() -> Path:
    st = (os.environ.get("OCTOPUS_STATE_DIR") or "").strip()
    if st:
        return Path(st)
    ops = (os.environ.get("OPS_DIR") or "").strip()
    if ops:
        return Path(ops) / "state"
    return _OPS / "state"


def trail_path(root: Optional[Path] = None) -> Path:
    if root is None:
        return _state_root() / "memory" / "self-loop-ingest.jsonl"
    root = Path(root)
    if root.name == "state" or (root / "memory").exists() or (root / "pulse").exists():
        return root / "memory" / "self-loop-ingest.jsonl"
    return root / "state" / "memory" / "self-loop-ingest.jsonl"


def _sha(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def _append_trail(path: Path, rec: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")


def _gate_submit(candidate: dict, gate: Optional[Any] = None) -> dict:
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


def _norm_item(channel: str, item: dict) -> Optional[dict]:
    """Normalize to {title, body, mkey_seed} or None."""
    if not isinstance(item, dict):
        return None
    title = str(
        item.get("title") or item.get("action") or item.get("leg")
        or item.get("id") or ""
    ).strip()[:160]
    body = str(
        item.get("body") or item.get("suggested_action") or item.get("action")
        or item.get("why") or item.get("first_step") or item.get("reason")
        or item.get("detail") or item.get("content") or ""
    ).strip()[:280]
    if not title and not body:
        return None
    if not title:
        title = body[:80]
    seed = f"{channel}|{title}|{body}"
    return {"title": title, "body": body, "seed": seed,
            "source_tag": str(item.get("source") or item.get("part") or channel)[:60]}


def ingest_items(channel: str, items: list, *, root: Optional[Path] = None,
                 max_items: int = _MAX_ITEMS,
                 digest_ts: str = "") -> dict:
    """Core ingest: list of dict items → trail + optional MemoryGate episodic."""
    ch = str(channel or "").strip()
    if ch not in CHANNELS:
        return {"ok": False, "error": f"unknown channel {ch!r}", "schema": SCHEMA,
                "may_authorize": False}
    if not isinstance(items, list):
        items = []

    trail = trail_path(root)
    committed = proposed = skipped = rejected = 0
    n = 0
    ts = digest_ts or _utc_now_iso()

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
        for raw in items:
            if n >= max_items:
                break
            norm = _norm_item(ch, raw if isinstance(raw, dict) else {})
            if not norm:
                continue
            content = (
                f"channel={ch} | source={norm['source_tag']} | "
                f"title={norm['title']}"
                + (f" | body={norm['body']}" if norm["body"] else "")
            )[:_CONTENT_MAX]
            mkey = f"selfloop:{ch}:" + _sha(norm["seed"])[:20]
            candidate = {
                "namespace": "episodic",
                "mkey": mkey,
                "content": content,
                "source": f"self_loop:{ch}",
                "producer": "self_loop_ingest",
                "privacy": "scrubbed",
                "scope": "project",
                "classification": "internal",
                "tenant_id": "personal",
                "project_id": "octopus-core",
                "agent_id": f"self_loop_{ch}",
                "task_id": "self_loop_ingest",
                "confidence": 0.6,
                "salience": 0.55,
                "inputs_sha": _sha(norm["seed"]),
                "admission_state": "ADMITTED",
                "policy_version": SCHEMA,
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
            try:
                _append_trail(trail, {
                    "ts": _utc_now_iso(),
                    "schema": SCHEMA,
                    "channel": ch,
                    "digest_ts": ts,
                    "mkey": mkey,
                    "title": norm["title"],
                    "gate_verb": verb,
                    "memory_id": result.get("memory_id"),
                    "reason": result.get("reason"),
                })
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
        "channel": ch,
        "n_items": n,
        "committed": committed,
        "proposed": proposed,
        "skipped": skipped,
        "rejected": rejected,
        "trail": str(trail),
        "may_authorize": False,
    }


# ── channel adapters (extract durable bits from overwrite pulses) ─────────────

def ingest_improve(digest: dict, *, root: Optional[Path] = None) -> dict:
    if not isinstance(digest, dict):
        return {"ok": False, "error": "digest must be dict", "may_authorize": False}
    items: list[dict] = []
    for p in (digest.get("top") or [])[:10]:
        if isinstance(p, dict):
            items.append({
                "title": p.get("title"),
                "body": p.get("suggested_action") or p.get("rationale"),
                "source": p.get("source") or "improve",
                "id": p.get("id"),
            })
    deep = digest.get("deep_thought")
    if isinstance(deep, dict) and deep.get("text"):
        items.append({"title": "deep_thought", "body": str(deep.get("text"))[:280],
                      "source": "improve-deep"})
    elif isinstance(deep, str) and deep.strip():
        items.append({"title": "deep_thought", "body": deep[:280], "source": "improve-deep"})
    note = digest.get("brain_note")
    if isinstance(note, str) and note.strip():
        items.append({"title": "brain_note", "body": note[:280], "source": "improve-brain"})
    return ingest_items("improve", items, root=root, digest_ts=str(digest.get("ts") or ""))


def ingest_synthesis(digest: dict, *, root: Optional[Path] = None) -> dict:
    if not isinstance(digest, dict):
        return {"ok": False, "error": "digest must be dict", "may_authorize": False}
    items = []
    for p in (digest.get("proposals") or [])[:10]:
        if isinstance(p, dict):
            items.append({
                "title": p.get("title"),
                "body": p.get("why") or p.get("first_step"),
                "source": f"synth:{digest.get('tier') or '?'}",
            })
    return ingest_items("synthesis", items, root=root, digest_ts=str(digest.get("ts") or ""))


def ingest_self_knowledge(rec: dict, *, root: Optional[Path] = None) -> dict:
    if not isinstance(rec, dict):
        return {"ok": False, "error": "rec must be dict", "may_authorize": False}
    items: list[dict] = []
    dd = rec.get("deep_dive") if isinstance(rec.get("deep_dive"), dict) else {}
    sf = dd.get("smallest_fix")
    if isinstance(sf, dict):
        body = str(
            sf.get("description") or sf.get("action") or sf.get("fix")
            or sf.get("text") or json.dumps(sf, ensure_ascii=False)
        )[:280]
        items.append({"title": "smallest_fix", "body": body, "source": "doctor-deep"})
    elif isinstance(sf, str) and sf.strip():
        items.append({"title": "smallest_fix", "body": sf[:280], "source": "doctor-deep"})
    u = rec.get("understanding") if isinstance(rec.get("understanding"), dict) else {}
    anat = str(u.get("anatomy") or "").strip()
    if anat:
        items.append({"title": "anatomy", "body": anat[:280], "source": "self_knowledge"})
    for p in (u.get("pathology") or [])[:3]:
        if isinstance(p, dict):
            items.append({
                "title": str(p.get("root_cause") or p.get("symptom") or "pathology")[:120],
                "body": str(p.get("symptom") or p.get("why") or "")[:280],
                "source": "pathology",
            })
    for p in (u.get("prescription") or [])[:3]:
        if isinstance(p, dict):
            items.append({
                "title": str(p.get("action") or "prescription")[:120],
                "body": str(p.get("why") or "")[:280],
                "source": "prescription",
            })
    return ingest_items("self_knowledge", items, root=root,
                        digest_ts=str(rec.get("ts") or ""))


def ingest_part_loops(digest: dict, *, root: Optional[Path] = None) -> dict:
    if not isinstance(digest, dict):
        return {"ok": False, "error": "digest must be dict", "may_authorize": False}
    items = []
    for p in (digest.get("proposals") or [])[:12]:
        if isinstance(p, dict):
            items.append({
                "title": f"{p.get('part', '?')}: {p.get('title', '')}"[:160],
                "body": p.get("action") or p.get("detail"),
                "source": p.get("part") or "part_loops",
                "part": p.get("part"),
            })
    # also capture unhealthy parts as awareness signals
    for part in (digest.get("parts") or []):
        if not isinstance(part, dict):
            continue
        if part.get("status") in ("🔴", "🟡"):
            items.append({
                "title": f"part-health:{part.get('name') or part.get('id')}",
                "body": str(part.get("detail") or part.get("status"))[:280],
                "source": "part-health",
            })
    return ingest_items("part_loops", items, root=root, digest_ts=str(digest.get("ts") or ""))


def ingest_selfheal_event(event: dict, *, root: Optional[Path] = None) -> dict:
    if not isinstance(event, dict):
        return {"ok": False, "error": "event must be dict", "may_authorize": False}
    leg = str(event.get("leg") or "?")
    reason = str(event.get("reason") or "selfheal")
    items = [{
        "title": f"selfheal:{leg}",
        "body": f"reason={reason} phi={event.get('phi')} beat={event.get('beat')}",
        "source": "selfheal",
        "leg": leg,
        "reason": reason,
    }]
    return ingest_items("selfheal", items, root=root, max_items=1)


def ingest_self_model(model: dict, *, root: Optional[Path] = None) -> dict:
    """Short summary only — never dump full module map."""
    if not isinstance(model, dict):
        return {"ok": False, "error": "model must be dict", "may_authorize": False}
    items: list[dict] = []
    pct = model.get("self_awareness_pct")
    n_mod = model.get("n_modules")
    items.append({
        "title": "self_model_snapshot",
        "body": f"awareness={pct}% modules={n_mod}",
        "source": "self_model",
    })
    undoc = model.get("undocumented") or []
    if isinstance(undoc, list) and undoc:
        items.append({
            "title": f"undocumented:{len(undoc)}",
            "body": ", ".join(str(x) for x in undoc[:5]),
            "source": "self_model",
        })
    return ingest_items("self_model", items, root=root,
                        digest_ts=str(model.get("ts") or ""), max_items=4)


def recall_recent(query: str = "", *, k: int = 8,
                  channels: Optional[list[str]] = None,
                  root: Optional[Path] = None) -> list[dict[str, Any]]:
    """Read-only recall — citations only, never authority."""
    q = (query or "").strip().lower()
    want = set(channels) if channels else None
    out: list[dict[str, Any]] = []

    try:
        import gate as mg
        import memory_store as ms
        if mg.flag_on():
            store = ms.MemoryStore()
            try:
                rows = store.search(q or "selfloop", namespace="episodic",
                                    k=max(k * 4, k)) or []
                for r in rows:
                    content = str(r.get("content") or "")
                    mkey = str(r.get("mkey") or "")
                    if not mkey.startswith("selfloop:"):
                        continue
                    ch = mkey.split(":")[1] if mkey.count(":") >= 2 else ""
                    if want and ch not in want:
                        continue
                    if q and q not in content.lower() and q not in mkey.lower():
                        continue
                    out.append({
                        "memory_id": r.get("memory_id"),
                        "mkey": mkey,
                        "channel": ch,
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
        ch = str(rec.get("channel") or "")
        if want and ch not in want:
            continue
        blob = f"{ch} {rec.get('title', '')} {rec.get('mkey', '')}".lower()
        if q and q not in blob:
            continue
        out.append({
            "memory_id": rec.get("memory_id"),
            "mkey": rec.get("mkey"),
            "channel": ch,
            "content": f"channel={ch} | title={rec.get('title')}",
            "trust": "trail",
            "provenance": "self-loop-ingest.jsonl",
            "may_authorize": False,
        })
    return out


def safe_call(fn_name: str, payload: dict, *, root: Optional[Path] = None) -> dict:
    """Fail-soft dispatcher for producer hooks."""
    try:
        fn = {
            "improve": ingest_improve,
            "synthesis": ingest_synthesis,
            "self_knowledge": ingest_self_knowledge,
            "part_loops": ingest_part_loops,
            "selfheal": ingest_selfheal_event,
            "self_model": ingest_self_model,
        }.get(fn_name)
        if not fn:
            return {"ok": False, "skipped": "unknown-fn", "may_authorize": False}
        return fn(payload, root=root)
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "skipped": f"{type(e).__name__}", "may_authorize": False}
