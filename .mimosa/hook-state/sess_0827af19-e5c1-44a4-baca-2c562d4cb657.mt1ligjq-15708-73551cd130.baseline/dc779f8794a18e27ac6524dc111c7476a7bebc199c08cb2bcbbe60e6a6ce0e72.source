#!/usr/bin/env python3
"""Fail-closed manifest catalog for the owner's single conversation surface.

Invalid manifests remain visible as NOT_LIVE diagnostics; they never disappear and never grant
execution. Metadata is parsed only — capability modules are not imported by discovery.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

OPS = Path(__file__).resolve().parents[1]
SCHEMA = "octopus.capability-manifest.v1"
SKIP = {"tests", "__pycache__", "_Archive", "_Duplicates", ".git", "artifacts"}

_STATUS_ORDER = {
    "LIVE": 0, "WIRED_NOT_LOADED": 1, "INTEGRATED_IN_SANDBOX": 2,
    "IMPLEMENTED_NOT_INTEGRATED": 3, "IMPLEMENTED_NOT_WIRED": 4,
    "DOC_ONLY": 5, "NOT_LIVE": 6, "MANIFEST_MISSING": 7,
    "MANIFEST_INVALID": 8, "UNKNOWN": 9,
}


def _paths(root: Path = OPS) -> list[Path]:
    out = []
    try:
        for p in root.rglob("capability-manifest.json"):
            rel = p.relative_to(root)
            if any(part in SKIP for part in rel.parts):
                continue
            if len(rel.parts) <= 5:
                out.append(p)
    except OSError:
        pass
    return sorted(set(out), key=lambda p: p.as_posix().lower())


def _parse_status(probe) -> str:
    text = str(probe or "").upper()
    if "IMPLEMENTED_NOT_INTEGRATED" in text:
        return "IMPLEMENTED_NOT_INTEGRATED"
    if "IMPLEMENTED_NOT_WIRED" in text or "ZERO CALLER" in text or "صفر صداکننده" in text:
        return "IMPLEMENTED_NOT_WIRED"
    if "NOT_LIVE" in text or "NOT LIVE" in text:
        return "NOT_LIVE"
    if "INTEGRATED_IN_SANDBOX" in text:
        return "INTEGRATED_IN_SANDBOX"
    if re.search(r"\bLIVE\b", text):
        return "LIVE"
    if "WIRED_NOT_LOADED" in text:
        return "WIRED_NOT_LOADED"
    return "UNKNOWN"


def validate(d) -> list[str]:
    e = []
    if not isinstance(d, dict):
        return ["not-an-object"]
    required = ("schema", "capability_id", "title", "version", "owner_phrases",
                "read_handler", "action_contract", "risk_class", "owner_gate",
                "surface", "runtime_status_probe", "tests")
    for k in required:
        if k not in d:
            e.append(f"missing:{k}")
    if d.get("schema") != SCHEMA:
        e.append("bad-schema")
    if not re.fullmatch(r"[a-z0-9][a-z0-9_.-]{2,79}", str(d.get("capability_id") or "")):
        e.append("bad-capability-id")
    if not isinstance(d.get("owner_phrases"), list) or not d.get("owner_phrases"):
        e.append("bad-owner-phrases")
    ac = d.get("action_contract")
    if not (isinstance(ac, dict) and ac.get("default_decision") in
            ("READ_ONLY", "OWNER_GATE", "BLOCK", "REJECT")):
        e.append("bad-action-contract")
    if not isinstance(d.get("owner_gate"), bool):
        e.append("bad-owner-gate")
    if d.get("surface") not in ("owner_outer_dm", "owner_inner_dm", "legs_forum_group"):
        e.append("bad-surface")
    if d.get("registration_is_authorization") is not False:
        e.append("registration-must-not-authorize")
    return e


def _legacy_cards() -> list[dict]:
    """Canonical AST registry; it discovers metadata without importing capability modules."""
    try:
        import sys
        if str(OPS) not in sys.path:
            sys.path.insert(0, str(OPS))
        import capability_registry
        return list(capability_registry.discover(refresh=True))
    except Exception:
        return []


_EXPECTED = {
    "world_discovery": ("🌍 کشف دنیای واقعی", "world_discovery"),
    "telegram_access": ("📡 قرارداد دسترسی تلگرام", "telegram_contract"),
}


def discover(root: Path = OPS) -> list[dict]:
    rows = []
    seen = set()
    for p in _paths(root):
        try:
            d = json.loads(p.read_text("utf-8"))
        except (OSError, ValueError):
            d = {}
        errors = validate(d)
        cid = str(d.get("capability_id") or f"invalid:{p.parent.name}")
        if cid in seen:
            errors.append("duplicate-capability-id")
        seen.add(cid)
        status = "MANIFEST_INVALID" if errors else _parse_status(d.get("runtime_status_probe"))
        rows.append({
            "capability_id": cid,
            "title": str(d.get("title") or p.parent.name),
            "version": str(d.get("version") or "?"),
            "phrases": [str(x) for x in (d.get("owner_phrases") or [])],
            "read_handler": d.get("read_handler"),
            "action_contract": d.get("action_contract"),
            "risk_class": str(d.get("risk_class") or "unknown"),
            "owner_gate": d.get("owner_gate") if isinstance(d.get("owner_gate"), bool) else True,
            "surface": str(d.get("surface") or "owner_outer_dm"),
            "probe": str(d.get("runtime_status_probe") or ""),
            "status": status,
            "errors": errors,
            "manifest": p.relative_to(root).as_posix(),
            "registration_is_authorization": False,
        })
    # Important implemented namespaces without a manifest remain visible as a defect.
    if root == OPS:
        for cid, (title, dirname) in _EXPECTED.items():
            if cid in seen or not (root / dirname).is_dir():
                continue
            seen.add(cid)
            rows.append({
                "capability_id": cid, "title": title, "version": "?",
                "phrases": [cid, title], "read_handler": None,
                "action_contract": None, "risk_class": "unknown", "owner_gate": True,
                "surface": "owner_outer_dm", "probe": "manifest missing",
                "status": "MANIFEST_MISSING", "errors": ["missing-capability-manifest"],
                "manifest": None, "registration_is_authorization": False,
            })
    # Legacy zero-arg cards remain visible. Explicit manifest wins on duplicate id.
    for old in _legacy_cards() if root == OPS else []:
        cid = str(old.get("key") or "")
        if not cid or cid in seen:
            continue
        seen.add(cid)
        live = bool(old.get("flag_on"))
        rows.append({
            "capability_id": cid, "title": str(old.get("title") or cid),
            "version": "legacy-card", "phrases": [cid, str(old.get("title") or cid)],
            "read_handler": f"capability_registry:render:{cid}",
            "action_contract": {"schema": None, "default_decision": "READ_ONLY"},
            "risk_class": "read", "owner_gate": False,
            "surface": "owner_outer_dm",
            "probe": ("LIVE — legacy card flag on" if live else
                      "IMPLEMENTED_NOT_LIVE — legacy card flag off"),
            "status": "LIVE" if live else "IMPLEMENTED_NOT_WIRED",
            "errors": [], "manifest": None,
            "registration_is_authorization": False,
        })
    rows.sort(key=lambda r: (_STATUS_ORDER.get(r["status"], 99), r["title"]))
    return rows


def find(text: str, rows: list[dict] | None = None) -> dict | None:
    q = str(text or "").strip().lower()
    if not q:
        return None
    best = None
    for row in (rows if rows is not None else discover()):
        terms = [row["capability_id"], row["title"], *row["phrases"]]
        score = sum(1 for t in terms if str(t).lower() in q or q in str(t).lower())
        if score and (best is None or score > best[0]):
            best = (score, row)
    return best[1] if best else None
