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

import datetime as _dt
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
    # ── تصمیم روی پیشنهادها — ۲۰۲۶-۰۸-۰۵، GO ِ صریحِ مالک ────────────────
    # تا امروز کاکپیت شش پیشنهادِ منتظر را **نشان می‌داد** ولی در کلِ سیستم
    # هیچ اقدامِ تأیید/ردی وجود نداشت؛ فقط از بات. پس صفحه ساختاراً تماشا
    # بود، و مالک درست می‌گفت «عملگرا نیست».
    #
    # ⚠️ این‌ها به `outcomes.db` می‌نویسند نه به پایگاهِ ops — چون همان‌جا
    # صفِ تصمیم زندگی می‌کند و دو نسخهٔ حقیقت نمی‌سازیم.
    "proposal.approve",
    "proposal.reject",
    "lead.create",
    "lead.add_note",
    "lead.update_stage",
    "task.create",
    "task.done",
    "value.record_event",
    # ── بیرون‌آوردنِ کارت از رکود — ۲۰۲۶-۰۸-۰۵، رأیِ صریحِ مالک ────────────
    # ۲۹ کارتِ RFC در `pending-cards.json` راکد بودند (قدیمی‌ترین ~۱۰ روز):
    # `delivery=SENT` ولی `decision != DECIDED`. تنها سطحِ تصمیم، دکمهٔ
    # اینلاینِ تلگرام بود که با توکنِ امضاشده کار می‌کند — و تحویلِ کارت
    # خاموش است (`card_delivery_ready = (False, 'no-secret')`). یعنی مالک
    # عدد «۲۹ راکد» را می‌دید و **هیچ‌جا** نمی‌توانست تصمیم بگیرد.
    #
    # ⚠️ چرا توکن این‌جا لازم نیست: توکن احرازِ **حاملِ** callback ِ تلگرام
    # است. مینی‌اپ احرازِ خودش را دارد (HMAC ِ init-data، سنجیده: بی‌امضا/
    # دستکاری‌شده/غیرمالک/کهنه هر چهار ۴۰۳). دو حامل، یک مالک.
    #
    # پایین‌دست واقعاً وجود دارد: `persist_rfc_verdict` هم دفتر را DECIDED
    # می‌کند هم پروجکشنِ کارت را، و تسکِ روزانهٔ `OCTOPUS-doctor-day` با
    # `claim_rfc_verdicts` برشان می‌دارد و اعمال می‌کند. همان مسیری که ۲۱
    # کارتِ APPLIED از آن آمدند.
    "rfc.approve",
    "rfc.deny",
    # ۲۰۲۶-۰۸-۰۷ — تبِ هفتم (اعلان‌ها). صندوق JSON است نه ops.db، پس شاخهٔ
    # execute() برایش مستقیم notif_inbox را صدا می‌زند، نه self.db.
    "notif.mark_read",
    # ۲۰۲۶-۰۸-۰۹ (رأیِ مالک، مگاپرامپتِ تناقضات، آیتمِ الف-۳): تنها اکشنِ این
    # لیست که هیچ جدولِ بیزینسی را لمس نمی‌کند — فقط `soak_test_noop` (جدولِ
    # اختصاصیِ تشخیصی، هیچ صداکنندهٔ دیگری ندارد). هدف: مسیرِ نوشتنِ واقعی
    # (همان اتصال/قفل/idempotency که proposal.approve و بقیه استفاده می‌کنند)
    # زیرِ soak-testِ طولانی هم تمرین شود، بدونِ ریسکِ آلودگیِ دادهٔ بیزینسی.
    "diagnostics.noop",
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


def _notif_inbox_mod():
    """ماژولِ notif_inbox، از هر پروسه‌ای — این فایل در _ops/agi2027_control
    است، پس مسیرِ _ops/telegram_center باید صریح اضافه شود. fail-soft: خطا →
    None (شاخهٔ notif.mark_read باید دستِ خالی را تحمل کند)."""
    import sys as _s
    _tgc = str(ROOT / "_ops" / "telegram_center")
    if _tgc not in _s.path:
        _s.path.insert(0, _tgc)
    try:
        import notif_inbox as _ni
        return _ni
    except Exception:  # noqa: BLE001
        return None
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
        # ۲۰۲۶-۰۸-۰۸: check_same_thread=False چون miniapp_gateway این کلاس را از
        # داخلِ _run_with_timeout (thread جدا) صدا می‌زند. بدونِ این، SQLite
        # ProgrammingError پرتاب می‌کرد و هیچ action‌ای از gateway کار نمی‌کرد.
        # WAL mode + این lock میکروسکوپی، همزمانیِ امن را تضمین می‌کنند.
        import threading as _th
        self._lock = _th.Lock()
        self.conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
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
        # ۲۰۲۶-۰۸-۰۹: جدولِ اختصاصیِ diagnostics.noop — عمداً جدا از هر جدولِ
        # بیزینسی (leads/tasks/value_events) تا هیچ probe ای دادهٔ واقعی را
        # لمس نکند. هیچ کدِ دیگری این جدول را نمی‌خواند؛ فقط اثباتِ نوشتن است.
        self.conn.execute(
            "CREATE TABLE IF NOT EXISTS soak_test_noop("
            "id TEXT PRIMARY KEY,note TEXT,created_at REAL NOT NULL)"
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

    def record_noop(self, p: Dict[str, Any]) -> Dict[str, Any]:
        """۲۰۲۶-۰۸-۰۹: تنها اکشنِ صرفاً تشخیصی — فقط `soak_test_noop` را لمس می‌کند،
        هیچ جدولِ بیزینسی را نه می‌خواند نه می‌نویسد. هدف: مسیرِ نوشتنِ واقعیِ
        SQLite (همان conn/lock/idempotency) زیرِ soak-testِ طولانی امتحان شود."""
        note = clean(p.get("note") or "soak-test", 200)
        noop_id = make_id("noop", {"note": note, "ts": now_ts()})
        self.conn.execute(
            "INSERT INTO soak_test_noop(id,note,created_at) VALUES(?,?,?)",
            (noop_id, note, now_ts()))
        self.conn.commit()
        return {"ok": True, "status": "APPLIED", "noop_id": noop_id}

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

    # ── تصمیمِ مالک روی یک پیشنهاد ────────────────────────────────────────
    #: پایگاهِ صفِ تصمیم. **جدا** از پایگاهِ ops است و عمداً همان‌جایی که
    #: `miniapp_state.get_approvals_state` می‌خواند — یک منبع، یک حقیقت.
    def _outcomes_conn(self):
        import sqlite3 as _sq
        # ⚠️ `self.root` این‌جا وجود ندارد — آن صفتِ `OpsActionEngine` است نه
        # `OctopusOpsDB`. اولین نسخه همان را صدا زد و هر شش تست AttributeError
        # داد. `ROOT` ثابتِ ماژول است و env همیشه برنده (برای تست/ایزوله).
        p = Path(os.environ.get("OCTOPUS_OUTCOMES_DB",
                                str(ROOT / "_ops" / "state" / "outcomes" / "outcomes.db")))
        if not p.exists():
            return None
        return _sq.connect(str(p))

    def decide_proposal(self, p: Dict[str, Any], verdict: str) -> Dict[str, Any]:
        """حکمِ مالک روی یک پیشنهاد را **اضافه** می‌کند، نه اینکه ردیفی را عوض کند.

        چرا append و نه UPDATE: منشور §۰.۱ — «هرگز حذف نکن». تاریخچهٔ یک
        تصمیم خودش داده است؛ اگر ردیفِ delivered را بازنویسی کنیم، دیگر
        نمی‌شود گفت چقدر طول کشید تا مالک تصمیم بگیرد.

        `get_approvals_state` آخرین رویدادِ هر پیشنهاد را می‌گیرد، پس یک
        ردیفِ تازه با حکم، خودبه‌خود آن را از صف بیرون می‌برد.
        """
        pid = clean(p.get("proposal_id"), 120)
        if not pid:
            return {"ok": False, "status": "BLOCKED", "reason": "missing_proposal_id"}
        conn = self._outcomes_conn()
        if conn is None:
            return {"ok": False, "status": "BLOCKED", "reason": "outcomes_db_missing"}
        try:
            row = conn.execute(
                "SELECT leg_id, lead_id, correlation_id, mission_id, event_type, verdict "
                "FROM outcomes WHERE proposal_id=? ORDER BY occurred_at DESC LIMIT 1",
                (pid,)).fetchone()
            if not row:
                return {"ok": False, "status": "BLOCKED",
                        "reason": "proposal_not_found", "proposal_id": pid}
            leg, lead, corr, mission, last_type, last_verdict = row
            # ⚠️ تصمیمِ دوباره روی چیزی که قبلاً تصمیم گرفته شده = BLOCKED،
            # نه یک ردیفِ دومِ متناقض. صف باید یک حکم داشته باشد.
            if last_verdict:
                return {"ok": False, "status": "BLOCKED", "reason": "already_decided",
                        "proposal_id": pid, "existing_verdict": last_verdict}
            ts = _dt.datetime.now(_dt.timezone.utc).isoformat()
            eid = make_id("evt", {"p": pid, "v": verdict, "ts": ts})
            conn.execute(
                "INSERT INTO outcomes(event_id,idempotency_key,correlation_id,mission_id,"
                "proposal_id,leg_id,lead_id,event_type,verdict,value_aud_claimed,"
                "occurred_at,recorded_at,schema_version,payload_json) "
                "VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (eid, f"{pid}|owner-{verdict}", corr, mission, pid, leg, lead,
                 "owner-decision", verdict, 0.0, ts, ts, "1",
                 json.dumps({"by": "owner", "surface": "cockpit"}, ensure_ascii=False)))
            conn.commit()
            return {"ok": True, "status": "APPLIED", "proposal_id": pid,
                    "verdict": verdict, "event_id": eid, "previous_event": last_type}
        finally:
            try:
                conn.close()
            except Exception:  # noqa: BLE001
                pass

    def decide_rfc(self, p: Dict[str, Any], verdict: str) -> Dict[str, Any]:
        """حکمِ مالک روی یک کارتِ RFC ِ راکد، از سطحِ وب‌اپ.

        سیمِ واقعی به `pending_card_recovery.persist_rfc_verdict` — که هم
        ردیفِ `rfc_decision` را DECIDED می‌کند و هم `decision` ِ خودِ کارت
        را، پس کارت **درجا** از STALLED بیرون می‌آید و نمای چرخهٔ عمر همان
        تیک تغییر را نشان می‌دهد.

        ⚠️ `persist_rfc_verdict` روی خطا `False` برمی‌گرداند و استثنا را
        می‌بلعد. یک `False` را نباید APPLIED گزارش کرد — همان «✅ ِ تو هیچ
        نکرد» که کلِ این چند روز دنبالش بودیم. پس False ⇒ ERROR.
        """
        rid = clean(p.get("rfc_id"), 64)
        if not rid:
            return {"ok": False, "status": "BLOCKED", "reason": "missing_rfc_id"}
        try:
            import outcomes.pending_card_recovery as _pcr  # noqa: WPS433
        except Exception as exc:  # noqa: BLE001
            return {"ok": False, "status": "BLOCKED",
                    "reason": "pcr_unavailable", "detail": type(exc).__name__}
        # ⚠️ `self.root` این‌جا وجود ندارد — آن صفتِ `OpsActionEngine` است، نه
        # `OctopusOpsDB` (که فقط conn/db_path/init_schema دارد). همین اشتباه
        # را یک‌بار کردم و شش تست AttributeError دادند.
        # قابلِ override با env تا تست هرگز به ذخیرهٔ زنده نخورد.
        state_dir = Path(os.environ.get("OCTOPUS_STATE_DIR",
                                        str(ROOT / "_ops" / "state")))
        if not state_dir.is_dir():
            return {"ok": False, "status": "BLOCKED", "reason": "state_dir_missing"}
        # کارت باید واقعاً وجود داشته باشد و واقعاً راکد باشد. بدونِ این چک،
        # یک `rfc_id` ِ تایپی یک ردیفِ حکم برای کارتی می‌سازد که نیست.
        try:
            store = _pcr._load_store(str(state_dir)) or {}
        except Exception:  # noqa: BLE001
            store = {}
        rec = store.get(f"rfc:{rid}")
        if not isinstance(rec, dict):
            return {"ok": False, "status": "BLOCKED",
                    "reason": "rfc_card_not_found", "rfc_id": rid}
        if str(rec.get("decision") or "").upper() == "DECIDED":
            return {"ok": False, "status": "BLOCKED",
                    "reason": "already_decided", "rfc_id": rid}
        ok = False
        try:
            ok = bool(_pcr.persist_rfc_verdict(state_dir=str(state_dir),
                                               rfc_id=rid, verdict=verdict))
        except Exception as exc:  # noqa: BLE001
            return {"ok": False, "status": "ERROR",
                    "reason": type(exc).__name__, "rfc_id": rid}
        if not ok:
            return {"ok": False, "status": "ERROR",
                    "reason": "persist_returned_false", "rfc_id": rid}
        return {"ok": True, "status": "APPLIED", "rfc_id": rid, "verdict": verdict,
                # مالک باید بداند اثر **کِی** می‌رسد، نه فقط اینکه ثبت شد.
                "next_effect": "OCTOPUS-doctor-day"}

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
            if action == "proposal.approve":
                res = self.db.decide_proposal(payload, "approved")
            elif action == "proposal.reject":
                res = self.db.decide_proposal(payload, "rejected")
            elif action == "lead.create":
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
            elif action == "rfc.approve":
                res = self.db.decide_rfc(payload, "merge-approved")
            elif action == "rfc.deny":
                res = self.db.decide_rfc(payload, "denied")
            elif action == "diagnostics.noop":
                res = self.db.record_noop(payload)
            elif action == "notif.mark_read":
                _ni = _notif_inbox_mod()
                if _ni is None:
                    res = {"ok": False, "status": "ERROR", "reason": "notif_inbox_unavailable"}
                else:
                    ids = payload.get("ids")
                    all_flag = bool(payload.get("all"))
                    if not all_flag and not (isinstance(ids, list) and ids):
                        res = {"ok": False, "status": "BLOCKED", "reason": "missing_ids_or_all"}
                    else:
                        n = _ni.mark_read(
                            ids=None if all_flag else [str(i)[:80] for i in ids])
                        res = {"ok": True, "status": "APPLIED", "marked": n}
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
