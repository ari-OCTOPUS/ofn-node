#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""consent_store.py — Trust-Engine P0 · D2a (فاز D): ذخیرهٔ پایدارِ رضایت + suppression.

الگوی موجود: `outcome_store.py` (SQLite/WAL + RLock single-writer + idempotency_key UNIQUE +
schema-versioned + close() صریح). این ماژول **خارج از مسیرِ اثر** است: stdlib فقط، صفر
import از chrono / named-effect-path-gate / ledger / telegram. صفر شبکه. صفر side-effectِ بیرونی.

قراردادِ حاکم: `03 - Projects/Lead-نقاشی/Trust-Engine-v1.1/PHASE-B-CONTRACTS/05_CONSENT_STATE_MACHINE.md`
(بخشِ ۳: Storage). D2a هستهٔ ایمنی را پیاده می‌کند:
  · جدول‌های consent_events (append-only، منبعِ حقیقت) + consent_current (materialized،
    چکِ سریعِ predicate) + suppression (هرگز purge نمی‌شود).
  · CHECKهای structural firewall (لایهٔ ۱): market_signal/outreach_allowed=1 غیرممکن است؛
    basis none/unknown + outreach=1 غیرممکن؛ حالت‌های non-outreach + outreach=1 غیرممکن.
  · هرگز چیزی نمی‌فرستد، هیچ transitionی را امضای نهایی نمی‌کند، named-effect-path-gate نمی‌سازد.

بقیهٔ ماشینِ consent (escalation، compliance-overlay، retention-beat، purge-tombstone)
در فازِ آیندهٔ D2b اضافه می‌شوند. D2a فقط store + CHECK + دسترسیِ پایه را می‌دهد تا
consent_gate.py روی آن predicate بسازد.
"""
from __future__ import annotations

import hashlib
import json
import os
import sqlite3
import sys
import threading
from datetime import datetime, timezone
from pathlib import Path

SCHEMA_VERSION = 1

# ── allowlistِ event_type (الگوی outcome_store.py:27) ───────────────────────────
EVENT_TYPES = (
    "consent.classified",        # inbox یک رکورد را کلاس‌بندی کرد (T3/T4/T5)
    "consent.quarantined",       # payload نامعتبر (T2)
    "consent.suppressed",        # STOP/unsubscribe/DNC (T9)
    "consent.unsuppressed",      # lift فقط-مالک (§6.3)
    "consent.retention.purged",  # retention منقضی (T10/T11/T12)
    "consent.escalation.proposed",  # (D2b — зарезیک Shar)
    "consent.escalation.approved",
    "consent.escalation.rejected",
    "compliance.cleared_scan",
    "compliance.flagged",
    "compliance.cleared",
)
_ET_SET = set(EVENT_TYPES)

_ACTORS = ("inbox", "owner", "retention-job")

_LOCK = threading.RLock()   # single-writer روی read-modify-writeها (intra-process)


def _utc_now_iso() -> str:
    """UTC-aware ISO-8601 (هرگز naive)."""
    return datetime.now(timezone.utc).isoformat()


def _default_path() -> Path:
    """مسیرِ db. الگوی outcome_store._default_path: env-first، fallback به STATE_DIR."""
    base = os.environ.get("OCTOPUS_STATE_DIR", "").strip()
    if base:
        root = Path(base)
    else:
        # STATE_DIRِ opslib را از طریقِ import بگیر (ایمن در برابرِ نقل‌مکان)
        try:
            if str(Path(__file__).resolve().parent.parent / "budget") not in sys.path:
                sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "budget"))
            import opslib as _ops   # noqa: WPS433
            root = _ops.STATE_DIR
        except Exception:  # noqa: BLE001
            root = Path(__file__).resolve().parent.parent / "state"
    return root / "legs" / "consent.db"


def _sha(obj) -> str:
    blob = json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


class ConsentStore:
    """store پایدارِ consent + suppression. path صریح در تست؛ پیش‌فرض state/legs/consent.db."""

    def __init__(self, path=None):
        self.path = Path(path) if path else _default_path()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(self.path), check_same_thread=False)
        with _LOCK:
            self._conn.execute("PRAGMA journal_mode=WAL")
            self._conn.execute("PRAGMA synchronous=NORMAL")
            self._conn.executescript(self._ddl())
            self._conn.commit()

    @staticmethod
    def _ddl() -> str:
        return """
        -- append-only: تنها منبعِ حقیقت؛ consent_current از این بازساختنی است (replay)
        CREATE TABLE IF NOT EXISTS consent_events(
          event_id        TEXT PRIMARY KEY,
          idempotency_key TEXT UNIQUE NOT NULL,
          lead_id         TEXT NOT NULL,
          event_type      TEXT NOT NULL,
          from_state      TEXT,
          to_state        TEXT,
          actor           TEXT NOT NULL CHECK(actor IN ('inbox','owner','retention-job')),
          occurred_at     TEXT NOT NULL,
          recorded_at     TEXT NOT NULL,
          causation_id    TEXT,
          correlation_id  TEXT,
          schema_version  INTEGER NOT NULL,
          payload_json    TEXT);

        -- materialized current-state: چکِ سریعِ predicateها؛ هر ردیف با replay قابلِ بازسازی
        CREATE TABLE IF NOT EXISTS consent_current(
          lead_id            TEXT PRIMARY KEY,
          candidate_type     TEXT NOT NULL CHECK(candidate_type IN
              ('consented_inbound','public_b2b','market_signal')),
          consent_basis      TEXT NOT NULL CHECK(consent_basis IN
              ('explicit','inferred_business','none','unknown')),
          consent_evidence   TEXT,
          compliance_reason  TEXT,
          consent_state      TEXT NOT NULL CHECK(consent_state IN
              ('RECEIVED','QUARANTINED','CONSENTED_INBOUND','B2B_PROSPECT','SIGNAL_ONLY',
               'ESCALATION_PROPOSED','ESCALATED','SUPPRESSED','PURGED')),
          compliance_state   TEXT NOT NULL DEFAULT 'UNREVIEWED' CHECK(compliance_state IN
              ('UNREVIEWED','CLEAR','RISK_FLAGGED','OWNER_CLEARED')),
          risk_flags_json    TEXT NOT NULL DEFAULT '[]',
          flags_hash         TEXT,
          outreach_allowed   INTEGER NOT NULL DEFAULT 0 CHECK(outreach_allowed IN (0,1)),
          retention_class    TEXT NOT NULL CHECK(retention_class IN
              ('consented_customer','b2b_prospect_12m','signal_30d')),
          retention_anchor_at TEXT NOT NULL,
          source_channel     TEXT NOT NULL,
          contact_value_norm TEXT,                    -- phone/email نرمال‌شده برایِ تطبیقِ suppression
          purged             INTEGER NOT NULL DEFAULT 0,
          updated_at         TEXT NOT NULL,
          -- ═══ THE STRUCTURAL FIREWALL (لایهٔ ۱ از ۳) ═══
          CHECK (NOT (candidate_type='market_signal'          AND outreach_allowed=1)),
          CHECK (NOT (consent_basis IN ('none','unknown')     AND outreach_allowed=1)),
          CHECK (NOT (consent_state IN ('SUPPRESSED','PURGED','QUARANTINED','RECEIVED',
                      'SIGNAL_ONLY','ESCALATION_PROPOSED','ESCALATED') AND outreach_allowed=1)),
          CHECK (NOT (candidate_type='public_b2b' AND consent_basis<>'inferred_business'
                      AND outreach_allowed=1)));

        -- suppression: هرگز purge نمی‌شود؛ lift فقط ستونِ nullable + eventِ append-only
        CREATE TABLE IF NOT EXISTS suppression(
          channel_value_norm TEXT PRIMARY KEY,
          channel_kind       TEXT NOT NULL CHECK(channel_kind IN ('phone','email')),
          reason             TEXT NOT NULL CHECK(reason IN
              ('stop_reply','unsubscribe','bounce','manual_dnc','complaint')),
          source_event_id    TEXT,
          created_at         TEXT NOT NULL,
          lifted_at          TEXT,
          lifted_event_id    TEXT);
        """

    # ── append-only events (idempotent) ────────────────────────────────────────
    def record_event(self, ev: dict) -> bool:
        """درجِ idempotentِ پایدار. True = ردیفِ نو؛ False = idempotency_key از قبل بود.
        event_type/actor نامعتبر → ValueError (fail-fastِ برنامه‌نویسی)."""
        et = str(ev.get("event_type", ""))
        if et not in _ET_SET:
            raise ValueError(f"unknown event_type: {et!r} (allowed: {EVENT_TYPES})")
        actor = str(ev.get("actor", ""))
        if actor not in _ACTORS:
            raise ValueError(f"unknown actor: {actor!r} (allowed: {_ACTORS})")
        idem = str(ev.get("idempotency_key") or "").strip() or _sha({
            "l": ev.get("lead_id"), "t": et, "to": ev.get("to_state"),
            "fh": (ev.get("payload") or {}).get("flags_hash")})
        event_id = str(ev.get("event_id") or ("cev_" + hashlib.sha256(idem.encode()).hexdigest()[:16]))
        row = (event_id, idem, str(ev.get("lead_id", "")), et,
               ev.get("from_state"), ev.get("to_state"), actor,
               str(ev.get("occurred_at") or _utc_now_iso()), _utc_now_iso(),
               ev.get("causation_id"), ev.get("correlation_id"), SCHEMA_VERSION,
               json.dumps(ev.get("payload") or {}, ensure_ascii=False, sort_keys=True))
        with _LOCK:
            cur = self._conn.execute(
                "INSERT OR IGNORE INTO consent_events("
                "event_id,idempotency_key,lead_id,event_type,from_state,to_state,actor,"
                "occurred_at,recorded_at,causation_id,correlation_id,schema_version,payload_json)"
                " VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)", row)
            self._conn.commit()
            return cur.rowcount == 1

    # ── current-state upsert (همیشه با CHECK firewall) ─────────────────────────
    def upsert_current(self, rec: dict) -> None:
        """upsert ردیفِ consent_current. CHECK firewall اعمال می‌شود: اگر داده‌ای
        با outreach_allowed=1 برای market_signal بیاید → sqlite3.IntegrityError (fail-closed).
        این لایهٔ ۱ firewall است؛ consent_gate لایهٔ ۲، تست‌ها لایهٔ ۳.
        contact_value_norm (اگر داده شود) برایِ تطبیقِ suppression ذخیره می‌شود (نرمال‌شده
        از سویِ caller — consent_gate.normalize_phone/email)."""
        cols = ("lead_id", "candidate_type", "consent_basis", "consent_evidence",
                "compliance_reason", "consent_state", "compliance_state",
                "risk_flags_json", "flags_hash", "outreach_allowed", "retention_class",
                "retention_anchor_at", "source_channel", "contact_value_norm", "purged")
        vals = (
            str(rec.get("lead_id", "")),
            str(rec.get("candidate_type", "market_signal")),
            str(rec.get("consent_basis", "none")),
            rec.get("consent_evidence"),
            rec.get("compliance_reason"),
            str(rec.get("consent_state", "RECEIVED")),
            str(rec.get("compliance_state", "UNREVIEWED")),
            json.dumps(rec.get("risk_flags") or [], ensure_ascii=False, sort_keys=True),
            rec.get("flags_hash"),
            int(bool(rec.get("outreach_allowed", 0))),
            str(rec.get("retention_class", "signal_30d")),
            str(rec.get("retention_anchor_at") or _utc_now_iso()),
            str(rec.get("source_channel", "")),
            rec.get("contact_value_norm"),
            int(bool(rec.get("purged", 0))),
        )
        updates = ", ".join(f"{c}=excluded.{c}" for c in cols[1:])
        with _LOCK:
            self._conn.execute(
                f"INSERT INTO consent_current({', '.join(cols)}, updated_at) "
                f"VALUES({', '.join('?' for _ in cols)}, ?) "
                f"ON CONFLICT(lead_id) DO UPDATE SET {updates}, updated_at=excluded.updated_at",
                (*vals, _utc_now_iso()))
            self._conn.commit()

    def load_current(self, lead_id: str) -> dict | None:
        """خواندنِ ردیفِ consent_current. None اگر نبود. فقط‌خواندنی."""
        with _LOCK:
            row = self._conn.execute(
                "SELECT lead_id, candidate_type, consent_basis, consent_evidence, "
                "compliance_reason, consent_state, compliance_state, risk_flags_json, "
                "flags_hash, outreach_allowed, retention_class, retention_anchor_at, "
                "source_channel, contact_value_norm, purged, updated_at FROM consent_current "
                "WHERE lead_id=?",
                (str(lead_id),)).fetchone()
        if not row:
            return None
        return {"lead_id": row[0], "candidate_type": row[1], "consent_basis": row[2],
                "consent_evidence": row[3], "compliance_reason": row[4],
                "consent_state": row[5], "compliance_state": row[6],
                "risk_flags": json.loads(row[7] or "[]"), "flags_hash": row[8],
                "outreach_allowed": bool(row[9]), "retention_class": row[10],
                "retention_anchor_at": row[11], "source_channel": row[12],
                "contact_value_norm": row[13], "purged": bool(row[14]),
                "updated_at": row[15]}

    # ── suppression ────────────────────────────────────────────────────────────
    def insert_suppression(self, channel_value_norm: str, channel_kind: str, reason: str,
                           *, source_event_id: str | None = None) -> bool:
        """درجِ ردیفِ suppression. True = ردیفِ نو؛ False = از قبل بود (idempotent).
        lift فقط ستونِ nullable است (§6.3)؛ ردیف هرگز حذف نمی‌شود. هرگز رکوردِ لید را mutate
        نمی‌کند — فقط جدولِ suppression را تغذیه می‌کند تا consent_gate در predicate چک کند."""
        with _LOCK:
            cur = self._conn.execute(
                "INSERT OR IGNORE INTO suppression(channel_value_norm, channel_kind, reason, "
                "source_event_id, created_at) VALUES(?,?,?,?,?)",
                (str(channel_value_norm), str(channel_kind), str(reason),
                 source_event_id, _utc_now_iso()))
            self._conn.commit()
            return cur.rowcount == 1

    def suppression_active(self, channel_value_norm: str) -> str | None:
        """دلیلِ suppression اگر فعال است، یا None. خطا/ابهام = active (fail-closed)."""
        try:
            with _LOCK:
                row = self._conn.execute(
                    "SELECT reason FROM suppression WHERE channel_value_norm=? AND lifted_at IS NULL",
                    (str(channel_value_norm),)).fetchone()
            return row[0] if row else None
        except Exception:  # noqa: BLE001 — ابهام در چکِ suppression = hit
            return "suppression-check-error"

    def events_for_lead(self, lead_id: str) -> list:
        """همهٔ eventهای یک lead_id (برایِ replay/audit). فقط‌خواندنی."""
        with _LOCK:
            return self._conn.execute(
                "SELECT event_id, event_type, from_state, to_state, actor, occurred_at, "
                "payload_json FROM consent_events WHERE lead_id=? ORDER BY recorded_at",
                (str(lead_id),)).fetchall()

    def close(self) -> None:
        """بستنِ صریح (ضدِ نشتِ WAL ویندوز، الگوی outcome_store)."""
        with _LOCK:
            self._conn.close()
