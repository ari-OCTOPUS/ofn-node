#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""funnel_store.py — Trust-Engine P0 · D3 (فاز D): ژورنالِ قیفِ لید + fold + متریک‌ها.

الگوی موجود: `outcome_store.py` (STD-lib فقط، SQLite/WAL، INSERT OR IGNORE روی
idempotency_key UNIQUE، single-writer، schema-versioned، replay-safe metrics).

قراردادِ حاکم: `03 - Projects/Lead-نقاشی/Trust-Engine-v1.1/PHASE-B-CONTRACTS/06_FUNNEL_STATE_MACHINE.md`
(بخشِ ۸: ذخیره‌سازی و replay-safety).

دو سیگنالِ جدا (06 §0):
  · نیمهٔ داخلی (internal quality): received → qualified → delivered_to_owner → owner_*
  · نیمهٔ بازار (market outcome): sent → replied → inspection_booked → quote_sent → won|lost → paid
رأیِ مالک هرگز state بازاری نمی‌سازد (جداییِ ساختاری).

D3 فقط storage + fold + metrics را می‌دهد (مثلِ outcome_store):
  · funnel_events (append-only، منبعِ حقیقت)
  · fold(lead_id) — state هرگز ذخیرهٔ mutable نیست؛ همیشه از رویدادها بازساخته می‌شود.
  · metrics() — از rows بازساخته (replay-safe).
دستوراتِ مالک (/sent /replied /meeting /won /lost /dead) در D3b. این store صرفاً داده‌خور/خواننده است،
صفر caller تا wiring بعداً. flag خاموش = no-op (اما store خودش flag ندارد؛ فقط emitterها پشتِ flag‌اند).

هرگز چیزی نمی‌فرستد، effect نمی‌سازد، ledger نمی‌زند. صرفاً ژورنالِ فقط-افزوده.
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

# ── واژگانِ رویداد (الگوی outcome_store.py:27 — allowlist در کد) ────────────────
# دقیقاً طبقِ SPEC §3 + 06_FUNNEL_STATE_MACHINE §2/§5. ناشناخته → ValueError.
EVENT_TYPES = (
    # نیمهٔ داخلی (INT)
    "lead.candidate.received", "lead.candidate.rejected", "lead.duplicate.detected",
    "lead.normalized", "lead.qualified", "lead.compliance_blocked",
    "response.draft.prepared", "quote.draft.prepared",
    "proposal.routed", "proposal.owner_approved", "proposal.owner_edited",
    "proposal.owner_rejected", "proposal.expired",
    # پلِ داخلی→بازار
    "effect.released", "communication.sent", "communication.failed", "communication.delivered",
    # نیمهٔ بازار (MKT)
    "customer.replied", "inspection.booked", "quote.sent", "quote.won", "quote.lost",
    "invoice.paid",
    # outcome genera (kind در payload)
    "outcome.recorded",
)
_ET_SET = set(EVENT_TYPES)

_LOCK = threading.RLock()   # single-writer روی read-modify-writeها


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _default_path() -> Path:
    """الگوی outcome_store._default_path: env-first، fallback به STATE_DIR."""
    base = os.environ.get("OCTOPUS_STATE_DIR", "").strip()
    if base:
        root = Path(base)
    else:
        try:
            budget = str(Path(__file__).resolve().parent.parent / "legs" / ".." / "budget")
            budget = str(Path(budget).resolve())
            if budget not in sys.path:
                sys.path.insert(0, budget)
            import opslib as _ops   # noqa: WPS433
            root = _ops.STATE_DIR
        except Exception:  # noqa: BLE001
            root = Path(__file__).resolve().parent.parent / "state"
    return root / "outcomes" / "funnel.db"


def _sha(obj) -> str:
    blob = json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


# ── رتبهٔ state برایِ fold (monotonic، 06 §8.3) ────────────────────────────────
# هر رویداد به یک state funnel نگاشت می‌شود. رتبهٔ بالاتر = پیشرویِ بیشتر.
# رویداد با رتبهٔ پایین‌تر از state فعلی regress نمی‌کند (ثبت می‌شود، state ثابت).
_STATE_RANK = {
    "received": 1, "quarantined": 2, "duplicate": 2, "normalized": 3,
    "qualified": 4, "compliance_blocked": 2,  # blocked = DEAD، رتبهٔ پایین (چسبنده)
    "delivered_to_owner": 5, "owner_approved": 6, "owner_edited": 6,
    "owner_rejected": 2, "expired": 2,        # DEAD
    "send_pending": 7, "sent": 8, "send_failed": 7,  # send_failed re-entrant
    "replied": 9, "inspection_booked": 10, "quote_sent": 11,
    "won": 12, "lost": 2, "dead": 2,           # lost/dead = DEAD
    "paid": 13, "gross_profit_recorded": 14, "repeat_or_referral": 15,
    "synthetic_done": 2,                       # DEAD
}

# نگاشتِ رویداد → state funnel (بخشِ 2 قرارداد)
_EVENT_TO_STATE = {
    "lead.candidate.received": "received",
    "lead.candidate.rejected": "quarantined",
    "lead.duplicate.detected": "duplicate",
    "lead.normalized": "normalized",
    "lead.qualified": "qualified",
    "lead.compliance_blocked": "compliance_blocked",
    "proposal.routed": "delivered_to_owner",
    "proposal.owner_approved": "owner_approved",
    "proposal.owner_edited": "owner_edited",
    "proposal.owner_rejected": "owner_rejected",
    "proposal.expired": "expired",
    "effect.released": "send_pending",
    "communication.sent": "sent",
    "communication.failed": "send_failed",
    "communication.delivered": "sent",   # رسید provider همچنان در sent نگه می‌دارد
    "customer.replied": "replied",
    "inspection.booked": "inspection_booked",
    "quote.sent": "quote_sent",
    "quote.won": "won",
    "quote.lost": "lost",
    "invoice.paid": "paid",
    # outcome.recorded: state از payload.kind برگردانده می‌شود (synthetic_complete, gross_profit, ...)
}

# stateهای DEAD (چسبنده، 06 §8.3)
_DEAD_STATES = frozenset({"quarantined", "duplicate", "compliance_blocked", "owner_rejected",
                          "expired", "lost", "dead", "synthetic_done"})


class FunnelStore:
    """store پایدارِ ژورنالِ قیفِ لید. path صریح در تست؛ پیش‌فرض state/outcomes/funnel.db."""

    def __init__(self, path=None):
        self.path = Path(path) if path else _default_path()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(self.path), check_same_thread=False)
        with _LOCK:
            self._conn.execute("PRAGMA journal_mode=WAL")
            self._conn.execute("PRAGMA synchronous=NORMAL")
            self._conn.execute(
                "CREATE TABLE IF NOT EXISTS funnel_events("
                "event_id TEXT PRIMARY KEY,"
                "idempotency_key TEXT UNIQUE NOT NULL,"
                "lead_id TEXT NOT NULL,"
                "proposal_id TEXT, effect_id TEXT, attribution_id TEXT,"
                "event_type TEXT NOT NULL,"
                "correlation_id TEXT NOT NULL,"    # = lead_id (envelope SPEC §3)
                "causation_id TEXT,"
                "source_component TEXT NOT NULL,"
                "channel_mode TEXT,"
                "occurred_at TEXT NOT NULL, recorded_at TEXT NOT NULL,"
                "schema_version INTEGER NOT NULL, payload_json TEXT)")
            self._conn.commit()

    # ── append-only event (idempotent) ─────────────────────────────────────────
    def record(self, ev: dict) -> bool:
        """درجِ idempotent. True = ردیفِ نو؛ False = idempotency_key از قبل بود.
        event_type نامعتبر → ValueError. همیشه dict با کلیدهایSPEC §3 می‌پذیرد."""
        et = str(ev.get("event_type", ""))
        if et not in _ET_SET:
            raise ValueError(f"unknown event_type: {et!r} (allowed: {EVENT_TYPES})")
        lead_id = str(ev.get("lead_id") or ev.get("correlation_id") or "")
        if not lead_id:
            raise ValueError("lead_id (or correlation_id) required")
        idem = str(ev.get("idempotency_key") or "").strip() or _sha({
            "l": lead_id, "p": ev.get("proposal_id"), "e": ev.get("effect_id"),
            "t": et, "ca": ev.get("causation_id")})
        event_id = str(ev.get("event_id") or ("fev_" + hashlib.sha256(idem.encode()).hexdigest()[:16]))
        row = (event_id, idem, lead_id,
               ev.get("proposal_id"), ev.get("effect_id"), ev.get("attribution_id"),
               et, str(ev.get("correlation_id") or lead_id), ev.get("causation_id"),
               str(ev.get("source_component") or "unknown"), ev.get("channel_mode"),
               str(ev.get("occurred_at") or _utc_now_iso()), _utc_now_iso(),
               SCHEMA_VERSION, json.dumps(ev.get("payload") or {}, ensure_ascii=False, sort_keys=True))
        with _LOCK:
            cur = self._conn.execute(
                "INSERT OR IGNORE INTO funnel_events("
                "event_id,idempotency_key,lead_id,proposal_id,effect_id,attribution_id,"
                "event_type,correlation_id,causation_id,source_component,channel_mode,"
                "occurred_at,recorded_at,schema_version,payload_json)"
                " VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", row)
            self._conn.commit()
            return cur.rowcount == 1

    def events_for_lead(self, lead_id: str) -> list:
        """همهٔ eventهای یک lead_id به ترتیبِ occurred_at, event_id (دترمینیستیک). فقط‌خواندنی."""
        with _LOCK:
            return self._conn.execute(
                "SELECT event_id, event_type, proposal_id, effect_id, attribution_id, "
                "correlation_id, causation_id, source_component, channel_mode, "
                "occurred_at, payload_json FROM funnel_events WHERE lead_id=? "
                "ORDER BY occurred_at, event_id",
                (str(lead_id),)).fetchall()

    # ── fold (state deriving، خالص، 06 §8.3) ───────────────────────────────────
    def fold(self, lead_id: str) -> dict:
        """state فعلیِ قیف را از replayِ رویدادها بازساز. هرگز mutable state ذخیره نمی‌کند.
        monotonic: رویداد با رتبهٔ پایین‌تر regress نمی‌کند. DEAD چسبنده.
        خروجی: {lead_id, state, rank, first_received_at, last_event_at, dead, anomaly}
        anomaly: لیستِ گذارهای غیرمجاز (append شد ولی state را عوض نکردند)."""
        rows = self.events_for_lead(lead_id)
        if not rows:
            return {"lead_id": str(lead_id), "state": None, "rank": 0,
                    "first_received_at": None, "last_event_at": None,
                    "dead": False, "anomaly": []}
        state, rank = None, 0
        first_received = None
        last_at = None
        dead = False
        anomalies = []
        for r in rows:
            et = r[1]
            payload = json.loads(r[10] or "{}") if r[10] else {}
            new_state = _EVENT_TO_STATE.get(et)
            # outcome.recorded: state از payload.kind
            if et == "outcome.recorded":
                kind = str(payload.get("kind") or "")
                if kind == "synthetic_complete":
                    new_state = "synthetic_done"
                elif kind == "gross_profit":
                    new_state = "gross_profit_recorded"
                elif kind in ("repeat", "referral"):
                    new_state = "repeat_or_referral"
                elif kind == "lead_dead":
                    new_state = "dead"
                elif kind == "proposal_expired":
                    new_state = "expired"
                # بقیهٔ kindها: state را عوض نمی‌کند (فقط ثبت می‌شود)
            occurred = r[9]
            if et == "lead.candidate.received" and first_received is None:
                first_received = occurred
            last_at = occurred
            if new_state is None:
                continue
            new_rank = _STATE_RANK.get(new_state, 0)
            # DEAD چسبنده: اگر state فعلی DEAD است، جدید را رد کن (مگر اینکه خودش DEADِ بالاتر باشد — نیست)
            if dead and new_state not in _DEAD_STATES:
                anomalies.append({"event_type": et, "reason": "dead_state_sticky",
                                  "current": state, "attempted": new_state})
                continue
            # monotonic: رتبهٔ پایین‌تر regress نمی‌کند
            if new_rank < rank and not (new_state in _DEAD_STATES):
                anomalies.append({"event_type": et, "reason": "regression_blocked",
                                  "current": state, "attempted": new_state})
                continue
            # گذار مجاز
            if new_state in _DEAD_STATES:
                dead = True
            state = new_state
            rank = max(rank, new_rank) if not dead else new_rank
        return {"lead_id": str(lead_id), "state": state, "rank": rank,
                "first_received_at": first_received, "last_event_at": last_at,
                "dead": dead, "anomaly": anomalies}

    # ── metrics (replay-safe، از rows، 06 §8.3) ────────────────────────────────
    def metrics(self) -> dict:
        """متریک‌های قیف از خودِ rows بازساخته (replay-safe). همیشه از data محاسبه،
        هرگز cached mutable. الگوی outcome_store.metrics."""
        with _LOCK:
            total = self._conn.execute("SELECT COUNT(*) FROM funnel_events").fetchone()[0]
            leads = self._conn.execute("SELECT COUNT(DISTINCT lead_id) FROM funnel_events").fetchone()[0]
            # شمارشِ رویدادهای کلیدی
            by_type = {}
            for et in EVENT_TYPES:
                n = self._conn.execute("SELECT COUNT(*) FROM funnel_events WHERE event_type=?",
                                       (et,)).fetchone()[0]
                if n:
                    by_type[et] = n
            # terminal-state شمارش (fold per lead — گران‌تر ولی دقیق)
            lead_ids = [r[0] for r in self._conn.execute(
                "SELECT DISTINCT lead_id FROM funnel_events").fetchall()]
            state_counts = {}
            won = paid = 0
            for lid in lead_ids:
                f = self.fold(lid)
                s = f.get("state") or "unknown"
                state_counts[s] = state_counts.get(s, 0) + 1
                if s == "won":
                    won += 1
                elif s == "paid":
                    paid += 1
        return {"total_events": total, "total_leads": leads, "events_by_type": by_type,
                "leads_by_state": state_counts, "won_count": won, "paid_count": paid}

    def close(self) -> None:
        with _LOCK:
            self._conn.close()
