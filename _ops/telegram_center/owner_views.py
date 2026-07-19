#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
owner_views — read-only "read model" behind menu options ① وضعیت, ③ کارهای من, ④ پاها.

WHY: the 6-option menu (owner_menu.py) needs consistent, cheap, crash-proof data. This module
reads the REAL state files (approval queue + per-leg ORGANISM-STATE snapshots) and returns compact
structured data + short Persian renders. It does NOT duplicate render.py's rich cards — it is the
tiny shared read-model that ①/③/④ and the Boss dashboard all source from (single source of truth).

Read-only. Never mutates. Graceful: missing/garbled files -> empty/unknown, never raises.
Shapes verified by live probe 2026-07-18: _octopus/state/approvals.json buckets carry
{id,title,risk,action,target,content_sha256}; per-leg files are _ops/state/ORGANISM-STATE.<leg>.
"""
from __future__ import annotations

import json
import os
import time
from typing import Any, Dict, List, Optional

# default roots (overridable for tests / alternate deployments)
DEFAULT_OCTOPUS_STATE = os.environ.get("OCTOPUS_STATE_ROOT", r"F:\backup\_octopus\state")
DEFAULT_OPS_STATE = os.environ.get("OPS_STATE_ROOT", r"F:\backup\_ops\state")
FRESH_SECS = int(os.environ.get("OCTOPUS_LEG_FRESH_SECS", "3600"))  # green if touched within 1h

# known legs and their on-disk signal file (per-leg ORGANISM-STATE snapshot)
LEGS = [
    {"key": "lead", "label": "🎨 نقاشی/لید", "state": "ORGANISM-STATE.lead_discovery"},
    {"key": "ziman", "label": "🖼 زیمان", "state": "ORGANISM-STATE.ziman"},
    {"key": "accounting", "label": "🧾 حسابداری", "state": "ORGANISM-STATE.accounting"},
    {"key": "code", "label": "🛠 کدنویس", "state": "ORGANISM-STATE.code"},
    {"key": "mining", "label": "⛏ ماینینگ", "state": None},
    {"key": "crypto", "label": "📈 کریپتو", "state": None},
]


def _read_json(path: str) -> Optional[Any]:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


# ── ③ کارهای من — pending owner decisions ────────────────────────────
def _load_aps():
    """Load approval_store (the canonical mission-approval queue) by file path. None on failure."""
    import importlib.util
    ap = os.path.join(os.path.dirname(os.path.abspath(__file__)), "approval_store.py")
    spec = importlib.util.spec_from_file_location("approval_store", ap)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def pending_decisions(octopus_state_root: str = DEFAULT_OCTOPUS_STATE) -> List[Dict[str, Any]]:
    """Items awaiting the owner's ✅/❌. Uses approval_store.load_pending() (the exact list the
    mission approve/reject buttons act on) for the live store; raw read for injected/test roots."""
    if octopus_state_root == DEFAULT_OCTOPUS_STATE:
        try:
            items = _load_aps().load_pending()
            if isinstance(items, list):
                return [{"id": it.get("id"),
                         "title": it.get("title") or it.get("action") or "—",
                         "risk": it.get("risk", "unknown"), "action": it.get("action")}
                        for it in items if isinstance(it, dict)]
        except Exception:
            pass  # fall back to raw read below
    data = _read_json(os.path.join(octopus_state_root, "approvals.json")) or {}
    out: List[Dict[str, Any]] = []
    for it in (data.get("pending") or []):
        if not isinstance(it, dict):
            continue
        out.append({
            "id": it.get("id"),
            "title": it.get("title") or it.get("action") or "—",
            "risk": it.get("risk", "unknown"),
            "action": it.get("action"),
        })
    return out


def render_tasks(items: List[Dict[str, Any]]) -> str:
    if not items:
        return "③ کارهای من: چیزی منتظرِ تأییدِ تو نیست ✅"
    lines = [f"③ کارهای من — {len(items)} تصمیم منتظرِ توست:"]
    for it in items[:8]:
        lines.append(f"• {it['title']} (ریسک: {it['risk']})")
    return "\n".join(lines)


def proposals(ops_state_root: str = DEFAULT_OPS_STATE) -> List[Dict[str, Any]]:
    """Upgrade proposals awaiting owner review — the «پیشنهاد در صف» the Organism bot shows.
    Source: cortex/upgrades-digest.json 'top'. Read-only, graceful."""
    d = _read_json(os.path.join(ops_state_root, "cortex", "upgrades-digest.json")) or {}
    out: List[Dict[str, Any]] = []
    for it in (d.get("top") or []):
        if isinstance(it, dict):
            out.append({"id": it.get("id"), "title": it.get("title") or "—",
                        "priority": it.get("priority", ""), "source": it.get("source", "")})
    return out


def render_backlog(approvals: List[Dict[str, Any]], props: List[Dict[str, Any]]) -> str:
    """③ کارهای من — the REAL backlog: yes/no approvals + queued proposals (what the owner sees)."""
    if not approvals and not props:
        return "③ کارهای من: چیزی منتظرِ تو نیست ✅"
    lines = ["③ کارهای من:"]
    if approvals:
        lines.append(f"— تصمیم‌های منتظرِ ✅/❌ ({len(approvals)}):")
        for it in approvals[:6]:
            lines.append(f"  • {it['title']} (ریسک: {it.get('risk', '?')})")
    if props:
        lines.append(f"— پیشنهادهای در صف ({len(props)}):")
        for it in props[:6]:
            pr = f"[{it['priority']}] " if it.get("priority") else ""
            src = f"  ({it['source']})" if it.get("source") else ""
            lines.append(f"  • {pr}{it['title']}{src}")
    return "\n".join(lines)


# ── ④ پاها — RAG status per leg ──────────────────────────────────────
def _leg_detail(key: str, blob: Any) -> str:
    """Actionable one-liner per leg from its state snapshot (VALUE-PLAN فاز B6:
    بردِ نامرئی دیده شود). Read-only; "" when nothing actionable. Never raises."""
    try:
        if key == "accounting" and isinstance(blob, dict):
            parts: List[str] = []
            if blob.get("synced") is True:
                parts.append("سینک ✅")
            pr = blob.get("pending_review")
            if isinstance(pr, int) and pr > 0:
                parts.append(f"{pr} منتظرِ /review")
            pb = blob.get("pending_books")
            if isinstance(pb, int) and pb > 0:
                parts.append(f"{pb} منتظرِ /books")
            return " · ".join(parts)
    except Exception:
        pass
    return ""

def _leg_rag(ops_state_root: str, leg: Dict[str, Any], now: float) -> Dict[str, Any]:
    sf = leg.get("state")
    if not sf:
        return {"key": leg["key"], "label": leg["label"], "rag": "grey", "reason": "غیرفعال/بی‌سیگنال", "detail": ""}
    path = os.path.join(ops_state_root, sf)
    if not os.path.exists(path):
        return {"key": leg["key"], "label": leg["label"], "rag": "red", "reason": "state غایب", "detail": ""}
    age = now - os.path.getmtime(path)
    blob = _read_json(path) or {}
    err = bool(blob.get("error")) if isinstance(blob, dict) else False
    if err:
        return {"key": leg["key"], "label": leg["label"], "rag": "red", "reason": "خطا در state", "detail": ""}
    det = _leg_detail(leg["key"], blob)
    if age <= FRESH_SECS:
        return {"key": leg["key"], "label": leg["label"], "rag": "green", "reason": "تازه", "detail": det}
    hrs = int(age // 3600)
    return {"key": leg["key"], "label": leg["label"], "rag": "yellow", "reason": f"کهنه (~{hrs}h)", "detail": det}


def legs_status(ops_state_root: str = DEFAULT_OPS_STATE) -> List[Dict[str, Any]]:
    now = time.time()
    return [_leg_rag(ops_state_root, leg, now) for leg in LEGS]


_DOT = {"green": "🟢", "yellow": "🟡", "red": "🔴", "grey": "⚪"}


def render_legs(rows: List[Dict[str, Any]]) -> str:
    lines = ["④ پاها:"]
    for r in rows:
        extra = f" · {r['detail']}" if r.get("detail") else ""
        lines.append(f"{_DOT.get(r['rag'], '⚪')} {r['label']} — {r['reason']}{extra}")
    return "\n".join(lines)


# ── ① وضعیت الان / Boss dashboard summary ────────────────────────────
def dashboard(octopus_state_root: str = DEFAULT_OCTOPUS_STATE,
              ops_state_root: str = DEFAULT_OPS_STATE) -> Dict[str, Any]:
    pend = pending_decisions(octopus_state_root)
    props = proposals(ops_state_root)
    legs = legs_status(ops_state_root)
    reds = [l for l in legs if l["rag"] == "red"]
    acct_note = next((l.get("detail") or "" for l in legs if l.get("key") == "accounting"), "")
    return {
        "needs_approval": len(pend),
        "proposals": len(props),
        "legs_total": len(legs),
        "legs_red": len(reds),
        "legs_green": len([l for l in legs if l["rag"] == "green"]),
        "red_legs": [l["label"] for l in reds],
        "accounting_note": acct_note,
        "ts": time.time(),
    }


def render_dashboard(d: Dict[str, Any]) -> str:
    return (
        "🐙 وضعیت الان\n"
        f"نیازمندِ تأییدِ تو: {d['needs_approval']} · پیشنهاد در صف: {d.get('proposals', 0)}\n"
        f"پاها: {d['legs_green']}🟢 از {d['legs_total']} · قرمز: {d['legs_red']}"
        + (f" ({'، '.join(d['red_legs'])})" if d.get("red_legs") else "")
        + (f"\n🧾 حسابداری: {d['accounting_note']}" if d.get("accounting_note") else "")
    )


if __name__ == "__main__":
    print(render_dashboard(dashboard()))
    print(render_legs(legs_status()))
    print(render_tasks(pending_decisions()))
