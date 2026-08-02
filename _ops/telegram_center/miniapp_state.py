#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""miniapp_state.py — read-only state helpers for the MiniApp cockpit.

قرارداد (PHASE 4 megaprompt):
  · read-only — هیچ mutate، هیچ side-effect.
  · secret-scrubbed — هرگز token/chat_id/PII در خروجی.
  · fail-closed — اگه فایل غایب/خراب است، status=unknown نه صفرِ جعلی.
  · JSON-safe — خروجی همیشه JSON-serializable.
"""
from __future__ import annotations

import json
import os
import re
import sqlite3
import sys
from pathlib import Path
from typing import Any

_HERE = Path(__file__).resolve().parent
_OPS = _HERE.parent
for _p in (str(_OPS), str(_OPS / "budget")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

try:
    import opslib  # noqa: E402
    STATE_DIR = opslib.STATE_DIR
    ORGAN_STATE = opslib.ORGAN_STATE
    BUDGET_STATE = opslib.BUDGET_STATE
    ORGAN_LOG = opslib.ORGAN_LOG
except Exception:  # noqa: BLE001
    opslib = None  # type: ignore
    STATE_DIR = _OPS / "state"
    ORGAN_STATE = _OPS / "budget" / "organ-state.json"
    BUDGET_STATE = _OPS / "budget" / "budget-state.json"
    ORGAN_LOG = _OPS / "budget" / "organ-gate-log.jsonl"

_ROOT = _OPS.parent
_RUNTIME = _OPS / "agi2027_runtime"
_TRUTH = _ROOT / "OCTOPUS-CURRENT-TRUTH-2026-08-02.md"

# الگوی scrub — عبارت‌های حساس را پاک می‌کند
_SECRET_RE = re.compile(
    r"(?i)(bot_token|api[_-]?key|secret|password|passwd|chat_id|bearer|sk-|fish_|xoxb-)"
    r"\s*[:=]\s*[^\s,;\"']+")
_TOKEN_RE = re.compile(r"\b\d{6,12}:[A-Za-z0-9_-]{20,}\b")
_EMAIL_RE = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b")


def _scrub(text: str) -> str:
    if not isinstance(text, str):
        text = str(text)
    text = _TOKEN_RE.sub("<TOKEN_REDACTED>", text)
    text = _SECRET_RE.sub(r"\1=<REDACTED>", text)
    text = _EMAIL_RE.sub("<EMAIL_REDACTED>", text)
    return text


def _scrub_dict(d: Any) -> Any:
    """بازگشتی secretها را از dict/list/str پاک می‌کند."""
    if isinstance(d, dict):
        out = {}
        for k, v in d.items():
            if isinstance(k, str) and re.search(
                    r"(?i)token|secret|password|passwd|api[_-]?key|chat_id|cookie|session",
                    k):
                out[k] = "<REDACTED>"
            else:
                out[k] = _scrub_dict(v)
        return out
    if isinstance(d, list):
        return [_scrub_dict(x) for x in d]
    if isinstance(d, str):
        return _scrub(_scrub(d))
    return d


def _read_json_safe(path: Path) -> "dict | None":
    try:
        if not path.exists():
            return None
        d = json.loads(path.read_text("utf-8"))
        return d if isinstance(d, dict) else None
    except (OSError, ValueError, TypeError):
        return None
def _miniapp_url_configured() -> bool:
    """Best-effort config check without exposing the URL.
    The gateway may be started before the User env is inherited by the process,
    while run-miniapp-tunnel.ps1 always writes state/telegram/miniapp-url.json.
    Treat either source as configured so the cockpit does not show a false
    CONFIG_NEEDED warning.
    """
    if str(os.environ.get("OCTOPUS_MINIAPP_URL", "") or "").strip():
        return True
    try:
        import subprocess
        code = "[Environment]::GetEnvironmentVariable('OCTOPUS_MINIAPP_URL','User')"
        r = subprocess.run(["powershell", "-NoProfile", "-Command", code],
                           capture_output=True, text=True, timeout=2)
        if (r.stdout or "").strip():
            return True
    except Exception:
        pass
    try:
        d = _read_json_safe(STATE_DIR / "telegram" / "miniapp-url.json")
        return bool(isinstance(d, dict) and str(d.get("url") or "").strip())
    except Exception:
        return False


def get_miniapp_state(root: "Path | None" = None) -> dict:
    """Home/Cockpit: system status، flags، pending، risk، Project-F، auth."""
    st = _read_json_safe(STATE_DIR / "ORGANISM-STATE.json")
    if st is None:
        return {"status": "unknown", "reason": "ORGANISM-STATE missing/unreadable"}
    flags = {
        "OCTOPUS_WIRE_TG_CONTROL": os.environ.get("OCTOPUS_WIRE_TG_CONTROL", "0") == "1",
        "OCTOPUS_WIRE_LEAD_OUTBOUND_WAL": os.environ.get("OCTOPUS_WIRE_LEAD_OUTBOUND_WAL", "0") == "1",
        "OCTOPUS_WIRE_VALUE_LEDGER": os.environ.get("OCTOPUS_WIRE_VALUE_LEDGER", "0") == "1",
    }
    # managed_flags.json را هم بخوان
    mf = _read_json_safe(_RUNTIME / "managed_flags.json")
    if isinstance(mf, dict):
        for k, v in mf.items():
            flags[k] = (str(v) == "1")
    # auth status: آیا bot_token + owner_id موجود است؟
    auth_configured = bool(os.environ.get("TG_CENTER_BOT_TOKEN")) and bool(os.environ.get("TELEGRAM_OWNER_CHAT_ID"))
    out = {
        "status": "ok",
        "halted": bool(st.get("halted") or st.get("stop_organism")),
        "frozen": bool(st.get("frozen")),
        "beat": st.get("beat"),
        "epoch_mode": st.get("epoch_mode"),
        "ts": st.get("ts"),
        "month": st.get("month"),
        "today": st.get("today"),
        "conflicts": st.get("conflicts"),
        "suspect_zero_total": st.get("suspect_zero_total"),
        "active_flags": flags,
        "auth_status": "configured" if auth_configured else "CONFIG_NEEDED",
        "projectf_status": "BLOCKED_NEEDS_CREDENTIALS",
        "miniapp_url_configured": _miniapp_url_configured(),
        "commit": _git_head_short(root),
    }
    return _scrub_dict(out)


def get_outbound_state(root: "Path | None" = None) -> dict:
    """Outbound/G-03: sent/failed/sending/needs_owner/cancelled counts."""
    db = _RUNTIME / "outbound-effects.sqlite3"
    if not db.exists():
        return {"status": "no_wal_db", "counts": {}, "note": "no outbound effects yet"}
    try:
        conn = sqlite3.connect(str(db))
        rows = conn.execute(
            "SELECT state, COUNT(*) FROM outbound_effects GROUP BY state").fetchall()
        conn.close()
        counts = {r[0]: r[1] for r in rows}
        return {"status": "ok", "counts": counts, "total": sum(counts.values())}
    except Exception as exc:  # noqa: BLE001
        return {"status": "error", "reason": f"{type(exc).__name__}"}


def get_approvals_state(root: "Path | None" = None) -> dict:
    """Approvals: pending proposal cards از outcomes."""
    db = STATE_DIR / "outcomes" / "outcomes.db"
    if not db.exists():
        return {"status": "no_outcomes_db", "pending": []}
    try:
        conn = sqlite3.connect(str(db))
        # best-effort: count deliveries not resolved
        try:
            rows = conn.execute(
                "SELECT proposal_id, kind, amount_aud FROM deliveries WHERE resolved=0 LIMIT 50"
            ).fetchall()
            pending = [{"proposal_id": r[0], "kind": r[1], "amount_aud": r[2]} for r in rows]
        except Exception:  # noqa: BLE001 — schema ممکن است متفاوت باشد
            pending = []
            conn.close()
            return {"status": "unknown_schema", "pending": []}
        conn.close()
        return {"status": "ok", "pending": _scrub_dict(pending), "count": len(pending)}
    except Exception as exc:  # noqa: BLE001
        return {"status": "error", "reason": f"{type(exc).__name__}"}


def get_legs_state(root: "Path | None" = None) -> dict:
    """Legs/Agents: از business_legs در ORGANISM-STATE."""
    st = _read_json_safe(STATE_DIR / "ORGANISM-STATE.json")
    biz = st.get("business_legs") if isinstance(st, dict) else None
    # unwrap double-layer
    if isinstance(biz, dict) and "business_legs" in biz:
        biz = biz.get("business_legs")
    if not isinstance(biz, dict):
        return {"status": "unknown", "reason": "business_legs missing", "legs": {}}
    return {"status": "ok", "legs": _scrub_dict(biz)}


def get_value_state(root: "Path | None" = None) -> dict:
    """Value Ledger: خلاصه از value-ledger.jsonl (اگر هست)."""
    ledger = _RUNTIME / "value-ledger.jsonl"
    if not ledger.exists():
        return {"status": "no_value_ledger", "note": "value ledger not yet populated"}
    try:
        counts = {}
        for raw in ledger.read_text("utf-8", errors="replace").splitlines():
            raw = raw.strip()
            if not raw:
                continue
            try:
                r = json.loads(raw)
            except ValueError:
                continue
            leg = r.get("leg", "?")
            counts[leg] = counts.get(leg, 0) + 1
        return {"status": "ok", "events_per_leg": counts, "total": sum(counts.values()),
                "auto_delete": False}
    except Exception as exc:  # noqa: BLE001
        return {"status": "error", "reason": f"{type(exc).__name__}"}


def get_ui_registry(root: "Path | None" = None) -> dict:
    """UI Registry: از ui-registry.json."""
    reg = _read_json_safe(_RUNTIME / "ui-registry.json")
    if reg is None:
        return {"status": "missing", "reason": "ui-registry.json not found"}
    return reg



def get_ops_state(root: "Path | None" = None) -> dict:
    """Ops Studio local summary: leads/tasks/value from local SQLite."""
    try:
        import sys as _sys
        ops_path = str(_OPS)
        if ops_path not in _sys.path:
            _sys.path.insert(0, ops_path)
        from agi2027_control.ops_actions import OpsActionEngine  # noqa: WPS433
        eng = OpsActionEngine(_ROOT)
        try:
            out = eng.summary()
            out["actions"] = {
                "enabled_when": "owner-auth configured + Telegram initData valid",
                "safe_local_actions": [
                    "lead.create", "lead.add_note", "lead.update_stage",
                    "task.create", "task.done", "value.record_event",
                ],
                "blocked_external_automation": ["onlyfans.*", "fansly.*", "mass_message", "cookie_import"],
            }
            return _scrub_dict(out)
        finally:
            eng.close()
    except Exception as exc:  # noqa: BLE001
        return {"status": "error", "reason": f"{type(exc).__name__}"}

def get_current_truth(root: "Path | None" = None) -> dict:
    """Current Truth: خلاصهٔ OCTOPUS-CURRENT-TRUTH markdown."""
    if not _TRUTH.exists():
        return {"status": "missing", "reason": "OCTOPUS-CURRENT-TRUTH file not found"}
    try:
        text = _TRUTH.read_text("utf-8", errors="replace")
        # اولین ~۲۰ خطِ غیر-frontmatter را بگیر
        lines = [ln for ln in text.splitlines() if ln.strip() and not ln.startswith("---")][:25]
        return {"status": "ok", "preview": _scrub("\n".join(lines)), "path": str(_TRUTH.name)}
    except Exception as exc:  # noqa: BLE001
        return {"status": "error", "reason": f"{type(exc).__name__}"}


def _git_head_short(root: "Path | None" = None) -> str:
    """short commit hash، fail-soft."""
    import subprocess
    r = root if root is not None else _ROOT
    try:
        out = subprocess.run(["git", "-C", str(r), "rev-parse", "--short", "HEAD"],
                             capture_output=True, text=True, timeout=5)
        return out.stdout.strip() if out.returncode == 0 else "unknown"
    except Exception:  # noqa: BLE001
        return "unknown"


# dispatcher برای gateway
def dispatch_api(path: str, root: "Path | None" = None) -> "tuple[int, bytes, str]":
    """GET /api/* dispatcher. خروجی: (status, body_bytes, content_type)."""
    p = str(path or "").split("?", 1)[0]
    handlers = {
        "/api/state": get_miniapp_state,
        "/api/outbound": get_outbound_state,
        "/api/approvals": get_approvals_state,
        "/api/legs": get_legs_state,
        "/api/value": get_value_state,
        "/api/ui-registry": get_ui_registry,
        "/api/current-truth": get_current_truth,
        "/api/ops": get_ops_state,
    }
    fn = handlers.get(p)
    if fn is None:
        return 404, b'{"status":"not_found"}', "application/json; charset=utf-8"
    try:
        data = fn(root)
        return 200, json.dumps(data, ensure_ascii=False, default=str).encode("utf-8"), \
            "application/json; charset=utf-8"
    except Exception as exc:  # noqa: BLE001 — fail-closed، هرگز crash
        return 500, json.dumps({"status": "error", "reason": f"{type(exc).__name__}"}).encode("utf-8"), \
            "application/json; charset=utf-8"


if __name__ == "__main__":
    # self-test: همه‌ی helpers را فراخوانی کن و خروجی JSON چاپ کن
    for name, fn in [("miniapp", get_miniapp_state), ("outbound", get_outbound_state),
                     ("approvals", get_approvals_state), ("legs", get_legs_state),
                     ("value", get_value_state), ("ops", get_ops_state), ("ui-registry", get_ui_registry),
                     ("current-truth", get_current_truth)]:
        print(f"=== {name} ===")
        print(json.dumps(fn(), ensure_ascii=False, indent=2)[:600])
        print()
