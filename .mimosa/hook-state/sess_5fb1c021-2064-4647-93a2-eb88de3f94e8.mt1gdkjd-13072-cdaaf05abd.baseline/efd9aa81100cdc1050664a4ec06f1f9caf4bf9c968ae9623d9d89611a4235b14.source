#!/usr/bin/env python3
"""tg_site_fire_log.py — ADR-042 Phase 0: which send *call sites* actually run.

Does not send, does not change return values. Append-only JSONL of
{ts, sender, caller_file, caller_line, caller_func, on_watchlist, topic}.
Fail-soft: any error is swallowed. Flag-off = zero I/O.

Why not 84 inline patches: telegram_center/center.py is a worklock file
(HANDOFF). Both live senders already funnel through TgClient.send and
TelegramApprovalChannel.send_text — stack frames attribute the call site.
"""
from __future__ import annotations

import inspect
import json
import os
import time
from pathlib import Path

FLAG = "OCTOPUS_TG_SITE_FIRE_LOG"
_HERE = Path(__file__).resolve().parent
CATALOG_PATH = _HERE / "tg_site_fire_catalog.json"
_SKIP_FILES = frozenset({
    "tg_site_fire_log.py",
    "tg_api.py",
})
_SKIP_FUNCS = frozenset({"send", "send_text", "record_call", "_record"})


def enabled() -> bool:
    return str(os.environ.get(FLAG, "") or "").strip().lower() in (
        "1", "true", "yes", "on")


def _state_dir() -> Path:
    try:
        import sys
        budget = _HERE / "budget"
        if str(budget) not in sys.path:
            sys.path.insert(0, str(budget))
        import opslib  # noqa: WPS433
        return Path(opslib.STATE_DIR)
    except Exception:  # noqa: BLE001
        return _HERE / "state"


def _load_catalog() -> dict[tuple[str, int], dict]:
    out: dict[tuple[str, int], dict] = {}
    try:
        rows = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return out
    if not isinstance(rows, list):
        return out
    for row in rows:
        if not isinstance(row, dict):
            continue
        rel = str(row.get("rel") or "").replace("\\", "/")
        try:
            line = int(row.get("line"))
        except (TypeError, ValueError):
            continue
        if rel and line > 0:
            out[(rel, line)] = row
    return out


_CATALOG = None


def _catalog() -> dict[tuple[str, int], dict]:
    global _CATALOG
    if _CATALOG is None:
        _CATALOG = _load_catalog()
    return _CATALOG


def _rel_ops(path: str) -> str:
    p = str(path or "").replace("\\", "/")
    marker = "/_ops/"
    if marker in p:
        return p.split(marker, 1)[1]
    return Path(p).name


def record_call(*, sender: str) -> None:
    """Log the first non-sender stack frame. Never raises. Never changes send."""
    if not enabled():
        return
    try:
        _record(sender=sender)
    except Exception:  # noqa: BLE001
        return


def _record(*, sender: str) -> None:
    caller_file = ""
    caller_line = 0
    caller_func = ""
    for fr in inspect.stack()[2:]:
        name = Path(fr.filename).name
        func = str(fr.function or "")
        if name in _SKIP_FILES:
            continue
        if name == "approval_channel.py" and func == "send_text":
            continue
        if func in _SKIP_FUNCS and name in ("tg_api.py", "approval_channel.py"):
            continue
        caller_file = _rel_ops(fr.filename)
        caller_line = int(fr.lineno or 0)
        caller_func = func
        break
    cat = _catalog().get((caller_file.replace("\\", "/"), caller_line))
    row = {
        "ts": time.time(),
        "sender": str(sender or ""),
        "caller_file": caller_file,
        "caller_line": caller_line,
        "caller_func": caller_func,
        "on_watchlist": bool(cat),
        "watch_topic": (cat or {}).get("topic"),
        "watch_method": (cat or {}).get("method"),
    }
    path = _state_dir() / "tg-site-fire.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(row, ensure_ascii=False) + "\n")
