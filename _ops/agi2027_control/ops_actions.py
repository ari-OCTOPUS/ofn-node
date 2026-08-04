#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ops_actions.py — owner-gated local action engine for Octopus Ops Studio.

Wave 1 scope:
- local-only, no external platform calls
- SQLite CRM/task/value primitives
- owner-gated + idempotent + audited
- blocks OnlyFans/Fansly automation actions explicitly
"""
from __future__ import annotations

import json
import os
import re
import sqlite3
import time
from pathlib import Path
from typing import Any, Dict, Optional

from .runtime import AuditLog, IdempotencyStore, stable_hash

ROOT = Path(__file__).resolve().parents[2]
RUNTIME = ROOT / "_ops" / "agi2027_runtime"
DB_PATH = Path(os.environ.get("OCTOPUS_OPS_DB_PATH", str(RUNTIME / "octopus_ops.sqlite3")))
ALLOWED_ACTIONS = {
    "lead.create",
    "lead.add_note",
    "lead.update_stage",
    "task.create",
    "task.done",
    "value.record_event",
}
BLOCKED_PREFIXES = (
    "onlyfans.",
    "fansly.",
    "platform.scrape",
    "platform.login",
    "mass_message",
    "cookie_import",
    "reverse_api",
)
STAGES = {"new", "warm", "hot", "subscribed", "vip", "churn_risk", "lost", "blocked"}
TASK_KINDS = {"followup", "manual_send", "content_prepare", "content_post", "check_payment", "review_campaign", "general"}
_SAFE = re.compile(r"[^a-zA-Z0-9_.:@-]+")
_TOKEN = re.compile(r"\b\d{6,12}:[A-Za-z0-9_-]{20,}\b")
_EMAIL = re.compile(r"(?i)\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b")


def now_ts() -> float:
    return time.time()


def clean(v: Any, limit: int = 1000) -> str:
    s = str(v or "").strip()
    s = _TOKEN.sub("<TOKEN_REDACTED>", s)
    s = _EMAIL.sub("<EMAIL_REDACTED>", s)
    return s[:limit]


def make_id(prefix: str, payload: Dict[str, Any]) -> str:
    raw = payload.get("id") or payload.get("handle") or payload.get("title") or stable_hash(payload)[:12]
    base = _SAFE.sub("-", str(raw).strip()).strip("-_.") or stable_hash(payload)[:12]
    return f"{prefix}_{base[:80]}"


class OctopusOpsDB:
    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(str(self.db_path))
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.execute("PRAGMA synchronous=NORMAL")
        self.init_schema()

    def init_schema(self) -> None:
        self.conn.execute(
            "CREATE TABLE IF NOT EXISTS leads("
            "id TEXT PRIMARY KEY,handle TEXT NOT NULL,display_name TEXT,source TEXT,platform TEXT,"
            "stage TEXT NOT NULL,tags_json TEXT NOT NULL,value_estimate REAL DEFAULT 0,notes TEXT,"
            "created_at REAL NOT NULL,updated_at REAL NOT NULL)"
        )
        self.conn.execute(
            "CREATE TABLE IF NOT EXISTS lead_notes("
            "id TEXT PRIMARY KEY,lead_id TEXT NOT NULL,note TEXT NOT NULL,created_at REAL NOT NULL)"
        )
        self.conn.execute(
            "CREATE TABLE IF NOT EXISTS tasks("
            "id TEXT PRIMARY KEY,title TEXT NOT NULL,kind TEXT NOT NULL,target_type TEXT,target_id TEXT,"
            "due_at TEXT,status TEXT NOT NULL,priority INTEGER DEFAULT 3,notes TEXT,"
            "created_at REAL NOT NULL,updated_at REAL NOT NULL)"
        )
        self.conn.execute(
            "CREATE TABLE IF NOT EXISTS value_events("
            "id TEXT PRIMARY KEY,leg TEXT NOT NULL,event TEXT NOT NULL,value_type TEXT NOT NULL,"
            "output_score REAL DEFAULT 0,cost_score REAL DEFAULT 0,risk_score REAL DEFAULT 0,"
            "metadata_json TEXT NOT NULL,created_at REAL NOT NULL)"
        )
        self.conn.commit()

    def close(self) -> None:
        try:
            self.conn.close()
        except Exception:
            pass

    def create_lead(self, p: Dict[str, Any]) -> Dict[str, Any]:
        handle = clean(p.get("handle"), 120)
        if not handle:
            return {"ok": False, "status": "BLOCKED", "reason": "missing_handle"}
        stage = clean(p.get("stage") or "new", 40)
        if stage not in STAGES:
            return {"ok": False, "status": "BLOCKED", "reason": "invalid_stage", "allowed": sorted(STAGES)}
        tags = p.get("tags") or []
        if isinstance(tags, str):
            tags = [x.strip() for x in tags.split(",") if x.strip()]
        tags = [clean(x, 40) for x in list(tags)[:20]]
        lead_id = make_id("lead", {"id": p.get("id"), "handle": handle})
        ts = now_ts()
        self.conn.execute(
            "INSERT INTO leads(id,handle,display_name,source,platform,stage,tags_json,value_estimate,notes,created_at,updated_at) "
            "VALUES(?,?,?,?,?,?,?,?,?,?,?) "
            "ON CONFLICT(id) DO UPDATE SET "
            "handle=excluded.handle,display_name=excluded.display_name,source=excluded.source,"
            "platform=excluded.platform,stage=excluded.stage,tags_json=excluded.tags_json,"
            "value_estimate=excluded.value_estimate,notes=excluded.notes,updated_at=excluded.updated_at",
            (
                lead_id,
                handle,
                clean(p.get("display_name"), 120),
                clean(p.get("source") or "manual", 120),
                clean(p.get("platform") or "manual", 60).lower(),
                stage,
                json.dumps(tags, ensure_ascii=False),
                float(p.get("value_estimate") or 0),
                clean(p.get("notes"), 2000),
                ts,
                ts,
            ),
        )
        self.conn.commit()
        return {"ok": True, "status": "APPLIED", "lead_id": lead_id, "handle": handle, "stage": stage}

    def add_note(self, p: Dict[str, Any]) -> Dict[str, Any]:
        lead_id, note = clean(p.get("lead_id"), 120), clean(p.get("note"), 2000)
        if not lead_id or not note:
            return {"ok": False, "status": "BLOCKED", "reason": "missing_lead_id_or_note"}
        if not self.conn.execute("SELECT 1 FROM leads WHERE id=?", (lead_id,)).fetchone():
            return {"ok": False, "status": "BLOCKED", "reason": "lead_not_found", "lead_id": lead_id}
        note_id = make_id("note", {"lead_id": lead_id, "note": note, "ts": now_ts()})
        ts = now_ts()
        self.conn.execute("INSERT INTO lead_notes(id,lead_id,note,created_at) VALUES(?,?,?,?)", (note_id, lead_id, note, ts))
        self.conn.execute("UPDATE leads SET notes=COALESCE(notes,'') || ? || ?, updated_at=? WHERE id=?", ("\n", note, ts, lead_id))
        self.conn.commit()
        return {"ok": True, "status": "APPLIED", "note_id": note_id, "lead_id": lead_id}

    def update_stage(self, p: Dict[str, Any]) -> Dict[str, Any]:
        lead_id, stage = clean(p.get("lead_id"), 120), clean(p.get("stage"), 40)
        if stage not in STAGES:
            return {"ok": False, "status": "BLOCKED", "reason": "invalid_stage", "allowed": sorted(STAGES)}
        cur = self.conn.execute("SELECT stage FROM leads WHERE id=?", (lead_id,)).fetchone()
        if not cur:
            return {"ok": False, "status": "BLOCKED", "reason": "lead_not_found", "lead_id": lead_id}
        self.conn.execute("UPDATE leads SET stage=?, updated_at=? WHERE id=?", (stage, now_ts(), lead_id))
        self.conn.commit()
        return {"ok": True, "status": "APPLIED", "lead_id": lead_id, "previous_stage": cur[0], "stage": stage}

    def create_task(self, p: Dict[str, Any]) -> Dict[str, Any]:
        title = clean(p.get("title"), 240)
        if not title:
            return {"ok": False, "status": "BLOCKED", "reason": "missing_title"}
        kind = clean(p.get("kind") or "general", 60)
        if kind not in TASK_KINDS:
            return {"ok": False, "status": "BLOCKED", "reason": "invalid_task_kind", "allowed": sorted(TASK_KINDS)}
        task_id = make_id("task", {"id": p.get("id"), "title": title, "kind": kind})
        ts = now_ts()
        self.conn.execute(
            "INSERT INTO tasks(id,title,kind,target_type,target_id,due_at,status,priority,notes,created_at,updated_at) "
            "VALUES(?,?,?,?,?,?,?,?,?,?,?) "
            "ON CONFLICT(id) DO UPDATE SET "
            "title=excluded.title,kind=excluded.kind,target_type=excluded.target_type,target_id=excluded.target_id,"
            "due_at=excluded.due_at,priority=excluded.priority,notes=excluded.notes,updated_at=excluded.updated_at",
            (
                task_id,
                title,
                kind,
                clean(p.get("target_type"), 60),
                clean(p.get("target_id"), 120),
                clean(p.get("due_at"), 80),
                "open",
                int(p.get("priority") or 3),
                clean(p.get("notes"), 1000),
                ts,
                ts,
            ),
        )
        self.conn.commit()
        return {"ok": True, "status": "APPLIED", "task_id": task_id, "title": title, "kind": kind}

    def task_done(self, p: Dict[str, Any]) -> Dict[str, Any]:
        task_id = clean(p.get("task_id"), 120)
        row = self.conn.execute("SELECT status FROM tasks WHERE id=?", (task_id,)).fetchone()
        if not row:
            return {"ok": False, "status": "BLOCKED", "reason": "task_not_found", "task_id": task_id}
        self.conn.execute("UPDATE tasks SET status=?, updated_at=? WHERE id=?", ("done", now_ts(), task_id))
        self.conn.commit()
        return {"ok": True, "status": "APPLIED", "task_id": task_id, "previous_status": row[0], "new_status": "done"}

    def record_value(self, p: Dict[str, Any]) -> Dict[str, Any]:
        leg = clean(p.get("leg") or "ops_studio", 120)
        event = clean(p.get("event") or "manual_value_event", 120)
        value_type = clean(p.get("value_type") or "production", 80)
        event_id = make_id("value", {"id": p.get("id"), "leg": leg, "event": event, "payload": p})
        ts = now_ts()
        meta = p.get("metadata") if isinstance(p.get("metadata"), dict) else {}
        self.conn.execute(
            "INSERT OR REPLACE INTO value_events(id,leg,event,value_type,output_score,cost_score,risk_score,metadata_json,created_at) "
            "VALUES(?,?,?,?,?,?,?,?,?)",
            (
                event_id,
                leg,
                event,
                value_type,
                float(p.get("output_score") or 0),
                float(p.get("cost_score") or 0),
                float(p.get("risk_score") or 0),
                json.dumps(meta, ensure_ascii=False, sort_keys=True),
                ts,
            ),
        )
        self.conn.commit()
        return {"ok": True, "status": "APPLIED", "value_event_id": event_id, "leg": leg, "event": event}

    def summary(self) -> Dict[str, Any]:
        def one(sql: str) -> int:
            r = self.conn.execute(sql).fetchone()
            return int(r[0] if r else 0)
        stages = {r[0]: r[1] for r in self.conn.execute("SELECT stage, COUNT(*) FROM leads GROUP BY stage").fetchall()}
        tasks = {r[0]: r[1] for r in self.conn.execute("SELECT status, COUNT(*) FROM tasks GROUP BY status").fetchall()}
        values = {r[0]: r[1] for r in self.conn.execute("SELECT leg, COUNT(*) FROM value_events GROUP BY leg").fetchall()}
        return {
            "status": "ok",
            "leads_total": one("SELECT COUNT(*) FROM leads"),
            "lead_stages": stages,
            "tasks_total": one("SELECT COUNT(*) FROM tasks"),
            "task_status": tasks,
            "value_events_total": one("SELECT COUNT(*) FROM value_events"),
            "value_events_per_leg": values,
        }


class OpsActionEngine:
    def __init__(self, root: Path = ROOT, db_path: Optional[Path] = None):
        self.root = Path(root)
        runtime = Path(os.environ.get("OCTOPUS_OPS_RUNTIME_DIR", str(self.root / "_ops" / "agi2027_runtime")))
        runtime.mkdir(parents=True, exist_ok=True)
        self.db = OctopusOpsDB(db_path or Path(os.environ.get("OCTOPUS_OPS_DB_PATH", str(runtime / "octopus_ops.sqlite3"))))
        self.audit = AuditLog(Path(os.environ.get("OCTOPUS_OPS_AUDIT_PATH", str(runtime / "ops-action-audit.jsonl"))))
        self.idem = IdempotencyStore(Path(os.environ.get("OCTOPUS_OPS_IDEMPOTENCY_PATH", str(runtime / "ops-actions-idempotency.sqlite3"))))

    def close(self) -> None:
        self.db.close()
        self.idem.close()

    def execute(self, action: str, payload: Dict[str, Any], actor: Dict[str, Any], action_id: Optional[str] = None) -> Dict[str, Any]:
        action = clean(action, 120)
        payload = payload if isinstance(payload, dict) else {}
        if not actor.get("is_owner"):
            return {"ok": False, "status": "DENIED", "reason": "owner_gate_failed"}
        if any(action.lower().startswith(p) for p in BLOCKED_PREFIXES):
            return {"ok": False, "status": "BLOCKED", "reason": "external_platform_automation_forbidden", "action": action}
        if action not in ALLOWED_ACTIONS:
            return {"ok": False, "status": "BLOCKED", "reason": "action_not_allowlisted", "action": action, "allowed": sorted(ALLOWED_ACTIONS)}
        key = action_id or f"ops:{action}:{stable_hash(payload)}"
        begin = self.idem.begin(key, {"action": action, "payload": payload})
        if begin["state"] == "DUPLICATE":
            # ⚠️ `ok` دیگر کوبیده نیست. تلاشِ قبلی ممکن است BLOCKED یا DENIED
            # بوده باشد؛ اگر این‌جا همیشه True برگردانیم، یک شکستِ ثبت‌شده را
            # به موفقیت **پول‌شویی** کرده‌ایم و UI رویش اقدام می‌کند.
            prev = begin.get("result")
            prev_ok = bool(prev.get("ok")) if isinstance(prev, dict) else True
            return {"ok": prev_ok, "status": "DUPLICATE", "action": action,
                    "action_id": key, "result": prev}
        if begin["state"] in {"CONFLICT", "BLOCKED"}:
            return {"ok": False, "status": begin["state"], "action": action, "idempotency": begin}
        # RETRY = تلاشِ قبلی هرگز settle نشد ⇒ مثلِ NEW جلو می‌رویم (پایین).
        try:
            if action == "lead.create":
                res = self.db.create_lead(payload)
            elif action == "lead.add_note":
                res = self.db.add_note(payload)
            elif action == "lead.update_stage":
                res = self.db.update_stage(payload)
            elif action == "task.create":
                res = self.db.create_task(payload)
            elif action == "task.done":
                res = self.db.task_done(payload)
            elif action == "value.record_event":
                res = self.db.record_value(payload)
            else:
                res = {"ok": False, "status": "BLOCKED", "reason": "unreachable_action"}
        except Exception as exc:  # noqa: BLE001 — عمداً وسیع
            # ⚠️ بدونِ این، هر استثنا ردیفِ idempotency را برای همیشه RUNNING
            # می‌گذاشت. مسیرهای واقعیِ ترکیدن که سنجیده شدند:
            # `float(output_score)` و `int(priority)` روی ورودیِ متنیِ کاربر،
            # و قفلِ sqlite روی دیسکِ مکانیکیِ این دستگاه.
            # حالا شکست **ثبت** می‌شود: ردیف settle می‌شود، ممیزی خط می‌گیرد،
            # و تلاشِ بعدی واقعاً دوباره اجرا می‌شود.
            res = {"ok": False, "status": "ERROR", "reason": type(exc).__name__,
                   "detail": str(exc)[:200]}
            self.idem.settle(key, "ERROR", res)
            self.audit.append({"event": "ops_action", "action": action, "action_id": key,
                               "ok": False, "status": "ERROR", "result": res})
            res.setdefault("action", action)
            res.setdefault("action_id", key)
            return res
        res = dict(res)
        res.setdefault("action", action)
        res.setdefault("action_id", key)
        self.idem.settle(key, res.get("status", "DONE"), res)
        self.audit.append({"event": "ops_action", "action": action, "action_id": key, "ok": bool(res.get("ok")), "status": res.get("status"), "result": res})
        return res

    def summary(self) -> Dict[str, Any]:
        return self.db.summary()
