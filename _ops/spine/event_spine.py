#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""event_spine.py — لاگِ رویدادِ واحدِ append-only و replayable با envelopeِ canonical.

SoTِ cross-domain برای تصمیم/outcome/mission. **trace_id (correlation_id) اجباری** —
رویدادِ بی‌trace رد می‌شود (ناوردیِ ردیابیِ end-to-end). idempotent، replayable، schema-versioned،
UTC-aware. domain ledgerها (genome/money/chrono) را جایگزین نمی‌کند — کنارشان می‌نشیند و از
طریقِ dual-write (helper، v1 بی‌producerِ زنده) پر می‌شود. پشتِ OCTOPUS_WIRE_SPINE (خاموش).
stdlib فقط؛ صفر side-effectِ بیرونی؛ WAL + RLock.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import sqlite3
import sys
import threading
from datetime import datetime, timezone
from pathlib import Path

_HERE = Path(__file__).resolve().parent
if str(_HERE.parent / "outcomes") not in sys.path:
    sys.path.insert(0, str(_HERE.parent / "outcomes"))
import taxonomy as tax  # noqa: E402

SCHEMA_VERSION = 1
FLAG = "OCTOPUS_WIRE_SPINE"
_LOCK = threading.RLock()
_COLS = ("event_id", "idempotency_key", "event_type", "domain", "occurred_at", "recorded_at",
         "producer", "producer_sequence", "correlation_id", "mission_id", "subject",
         "trust", "schema_version", "payload_json")


def flag_on() -> bool:
    return str(os.environ.get(FLAG, "")).strip().lower() in ("1", "true", "yes", "on")


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _sha(obj) -> str:
    return hashlib.sha256(json.dumps(obj, sort_keys=True, ensure_ascii=False,
                                     separators=(",", ":")).encode("utf-8")).hexdigest()


# ── بهداشتِ ساختاریِ payload (defense-in-depth، آینهٔ spine_adapters.sanitize_payload) ──
# عمداً همتا/تکرارشده: spine_adapters این ماژول را import می‌کند، پس importِ برعکس =
# circular. قواعد یکسان‌اند تا double-sanitize (آداپتور سپس این‌جا) قطعاً idempotent باشد.
# فقط کلیدِ snake_case امن با مقدارِ bool/int/float یا strِ تک‌خطیِ ≤۸۰ عبور می‌کند؛
# کلیدِ متن‌خام (body/text/desc/prompt/…/email/…) یا nested/متنِ بلند بی‌صدا حذف می‌شود.
_SAN_KEY_OK_RE = re.compile(r"^[a-z0-9_]{1,32}$")
_SAN_KEY_BLOCK_RE = re.compile(
    r"(body|text|desc|prompt|content|message|caption|address|email|phone|"
    r"name|applicant|raw|note|comment)", re.I)
_SAN_MAX_STR = 80


def _sanitize_payload(payload) -> dict:
    out = {}
    if not isinstance(payload, dict):
        return out
    for k, v in payload.items():
        ks = str(k)
        if not _SAN_KEY_OK_RE.match(ks) or _SAN_KEY_BLOCK_RE.search(ks):
            continue
        if isinstance(v, bool) or isinstance(v, (int, float)):
            out[ks] = v
        elif isinstance(v, str) and len(v) <= _SAN_MAX_STR and "\n" not in v and "\r" not in v:
            out[ks] = v
        # هر نوعِ دیگر (list/dict/None/متنِ بلند/چندخطی) → حذف
    return out


def _default_path() -> Path:
    base = os.environ.get("OCTOPUS_STATE_DIR", "").strip()
    root = Path(base) if base else (_HERE.parent / "state")
    return root / "spine" / "spine.db"


class EventSpine:
    def __init__(self, path=None):
        self.path = Path(path) if path else _default_path()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(self.path), check_same_thread=False)
        with _LOCK:
            self._conn.execute("PRAGMA journal_mode=WAL")
            self._conn.execute("PRAGMA synchronous=NORMAL")
            self._conn.execute(
                "CREATE TABLE IF NOT EXISTS events("
                "event_id TEXT PRIMARY KEY, idempotency_key TEXT UNIQUE NOT NULL,"
                "event_type TEXT NOT NULL, domain TEXT NOT NULL,"
                "occurred_at TEXT NOT NULL, recorded_at TEXT NOT NULL,"
                "producer TEXT, producer_sequence INTEGER, correlation_id TEXT NOT NULL,"
                "mission_id TEXT, subject TEXT, trust TEXT, schema_version INTEGER NOT NULL,"
                "payload_json TEXT)")
            self._conn.commit()

    def publish(self, ev: dict) -> "str | None":
        """رویداد را با envelopeِ canonical درج کن (idempotent). خروجی event_id یا None(dup).
        قیود: correlation_id/trace_id اجباری؛ event_type از taxonomy؛ domain غیرخالی."""
        corr = str(ev.get("correlation_id") or ev.get("trace_id") or "").strip()
        if not corr:
            raise ValueError("correlation_id/trace_id is MANDATORY (no untraced events)")
        et = str(ev.get("event_type") or "")
        if not tax.is_event_type(et):
            raise ValueError(f"unknown event_type {et!r}")
        domain = str(ev.get("domain") or "").strip()
        if not domain:
            raise ValueError("domain required")
        idem = str(ev.get("idempotency_key") or "").strip() or _sha(
            {"c": corr, "t": et, "d": domain, "s": ev.get("subject"), "m": ev.get("mission_id")})
        eid = str(ev.get("event_id") or ("evt_" + hashlib.sha256(idem.encode()).hexdigest()[:16]))
        trust = ev.get("trust")
        trust = trust if tax.is_trust(trust) else "UNKNOWN"
        row = (eid, idem, et, domain, str(ev.get("occurred_at") or _utc_now_iso()), _utc_now_iso(),
               ev.get("producer"), _inti(ev.get("producer_sequence")), corr, ev.get("mission_id"),
               ev.get("subject"), trust, SCHEMA_VERSION,
               json.dumps(ev.get("payload") or {}, ensure_ascii=False, sort_keys=True))
        with _LOCK:
            cur = self._conn.execute(
                "INSERT OR IGNORE INTO events(" + ",".join(_COLS) + ") VALUES(" +
                ",".join("?" * len(_COLS)) + ")", row)
            self._conn.commit()
            return eid if cur.rowcount == 1 else None

    def events(self, *, correlation_id=None, mission_id=None, domain=None) -> list:
        conds, args = [], []
        for col, v in (("correlation_id", correlation_id), ("mission_id", mission_id), ("domain", domain)):
            if v is not None:
                conds.append(f"{col}=?")
                args.append(v)
        q = "SELECT " + ",".join(_COLS) + " FROM events"
        if conds:
            q += " WHERE " + " AND ".join(conds)
        q += " ORDER BY recorded_at, event_id"
        with _LOCK:
            rows = self._conn.execute(q, args).fetchall()
        return [dict(zip(_COLS, r)) for r in rows]

    def replay_mission(self, mission_id: str) -> dict:
        """read-modelِ قطعیِ یک mission را از رویدادها fold کن (deterministic، side-effect-free)."""
        evs = self.events(mission_id=mission_id)
        state = {"mission_id": mission_id, "correlation_ids": [], "timeline": [],
                 "last_status": None, "n_events": len(evs)}
        seen = set()
        for e in evs:
            if e["correlation_id"] not in seen:
                seen.add(e["correlation_id"])
                state["correlation_ids"].append(e["correlation_id"])
            state["timeline"].append({"type": e["event_type"], "domain": e["domain"],
                                      "at": e["occurred_at"], "subject": e["subject"]})
            state["last_status"] = e["event_type"]
        return state

    def metrics(self) -> dict:
        with _LOCK:
            rows = self._conn.execute("SELECT event_type, domain FROM events").fetchall()
        m = {"total": len(rows), "by_type": {}, "by_domain": {}, "schema_version": SCHEMA_VERSION}
        for et, dom in rows:
            m["by_type"][et] = m["by_type"].get(et, 0) + 1
            m["by_domain"][dom] = m["by_domain"].get(dom, 0) + 1
        return m

    def close(self):
        with _LOCK:
            try:
                self._conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
            except Exception:  # noqa: BLE001
                pass
            try:
                self._conn.close()
            except Exception:  # noqa: BLE001
                pass


def dual_write(spine: "EventSpine", ev: dict) -> dict:
    """helperِ مهاجرتِ تدریجی: producer domain-ledgerِ خودش را می‌نویسد، سپس این را برای spine
    صدا می‌زند. flag خاموش → no-op (بایت‌به‌بایتِ رفتارِ فعلی). خروجی: {published, event_id?, reason}."""
    if not flag_on():
        return {"published": False, "reason": "flag-off"}
    try:
        # defense-in-depth: بهداشتِ ساختاریِ payload حتی برای callerِ مستقیم (غیرآداپتور) تا
        # متنِ خام/PII (body/text/prompt/email/…) هرگز persist نشود. فقط payload لمس می‌شود؛
        # فیلدهای هویت/idempotency (correlation_id/subject/mission_id/event_type/domain و کلیدِ
        # idempotency که در publish از همان‌ها ساخته می‌شود) دست‌نخورده → identity ثابت.
        # idempotent با صافیِ آداپتور (double-sanitize = همان نتیجه).
        if isinstance(ev, dict) and "payload" in ev:
            ev = dict(ev)
            ev["payload"] = _sanitize_payload(ev.get("payload"))
        eid = spine.publish(ev)
        return {"published": eid is not None, "event_id": eid,
                "reason": "ok" if eid else "duplicate"}
    except ValueError as e:
        return {"published": False, "reason": str(e)}


def _inti(v):
    try:
        return int(v)
    except (TypeError, ValueError):
        return None
