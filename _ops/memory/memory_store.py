#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""memory_store.py — storeِ حافظهٔ graded (SQLite + FTS5)، append-only، trust-stamped.

منبعِ تولیدکنندهٔ `memories_used`ِ Decision Receipt (که تا امروز صفر تولیدکننده داشت).
رکوردها immutable‌اند؛ نسخهٔ جدید = ردیفِ نو با supersedes به قدیمی (هرگز overwrite/حذفِ
فیزیکی — قاعدهٔ vault §۱). واژگان از outcomes/taxonomy.py (منبعِ یگانه). retrieval:
get(key) + search(FTS5 bm25 + recency/salience) — بدونِ vector (فاز ۱). WAL + RLock.
هیچ side-effectِ بیرونی؛ stdlib فقط.
"""
from __future__ import annotations

import hashlib
import json
import os
import sqlite3
import threading
from datetime import datetime, timezone
from pathlib import Path

_HERE = Path(__file__).resolve().parent
import sys
if str(_HERE.parent / "outcomes") not in sys.path:
    sys.path.insert(0, str(_HERE.parent / "outcomes"))
import taxonomy as tax  # noqa: E402

SCHEMA_VERSION = 3
_LOCK = threading.RLock()
_ADMISSION_STATES = frozenset({"PENDING", "ADMITTED", "RETRACTED", "QUARANTINED"})
_COLS = ("memory_id", "namespace", "mkey", "content", "content_sha256", "trust",
         "provenance_json", "confidence", "salience", "valid_from", "valid_to",
         "supersedes", "privacy", "admission_state", "schema_version", "created_at",
         "tenant_id", "project_id", "scope", "agent_id", "task_id", "classification",
         "policy_version", "evidence_ref", "confidence_source", "confidence_method")


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _sha(s: str) -> str:
    return hashlib.sha256(str(s).encode("utf-8")).hexdigest()


def _default_path() -> Path:
    base = os.environ.get("OCTOPUS_STATE_DIR", "").strip()
    root = Path(base) if base else (_HERE.parent / "state")
    return root / "memory" / "memory.db"


class MemoryStore:
    def __init__(self, path=None):
        self.path = Path(path) if path else _default_path()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(self.path), check_same_thread=False)
        self._fts = False
        with _LOCK:
            self._conn.execute("PRAGMA journal_mode=WAL")
            self._conn.execute("PRAGMA synchronous=NORMAL")
            self._conn.execute(
                "CREATE TABLE IF NOT EXISTS memory("
                "memory_id TEXT PRIMARY KEY, namespace TEXT NOT NULL, mkey TEXT,"
                "content TEXT NOT NULL, content_sha256 TEXT NOT NULL, trust TEXT NOT NULL,"
                "provenance_json TEXT, confidence REAL, salience REAL,"
                "valid_from TEXT NOT NULL, valid_to TEXT, supersedes TEXT,"
                "privacy TEXT NOT NULL, admission_state TEXT NOT NULL DEFAULT 'ADMITTED',"
                "schema_version INTEGER NOT NULL, created_at TEXT NOT NULL)")
            # Additive v1→v3 migrations. Existing memories preserve their previous visibility.
            cols = {r[1] for r in self._conn.execute("PRAGMA table_info(memory)").fetchall()}
            if "admission_state" not in cols:
                self._conn.execute(
                    "ALTER TABLE memory ADD COLUMN admission_state TEXT NOT NULL DEFAULT 'ADMITTED'")
            for name, ddl in (
                ("tenant_id", "TEXT NOT NULL DEFAULT 'personal'"),
                ("project_id", "TEXT NOT NULL DEFAULT 'octopus-core'"),
                ("scope", "TEXT NOT NULL DEFAULT 'project'"),
                ("agent_id", "TEXT NOT NULL DEFAULT 'unknown'"),
                ("task_id", "TEXT NOT NULL DEFAULT ''"),
                ("classification", "TEXT NOT NULL DEFAULT 'internal'"),
                ("policy_version", "TEXT NOT NULL DEFAULT 'memory-policy.v1'"),
                # TEAM-A promotion (OWNER-CONSENTS-2026-08-19T0615Z §4): ستون‌های
                # افزایشی — provenance همچنان منبع کامل است؛ ستون‌ها برای پرس‌وجوی مستقیم.
                ("evidence_ref", "TEXT"),
                ("confidence_source", "TEXT"),
                ("confidence_method", "TEXT"),
            ):
                if name not in cols:
                    self._conn.execute(f"ALTER TABLE memory ADD COLUMN {name} {ddl}")
            # C6 evolution_v3: secondary indexes — get() and the insert() dedupe check were
            # full-table SCANs (O(n); ~6.7ms/7.5ms at 20k rows). Additive + idempotent,
            # access-path only: explicit ORDER BY already fixes result order, so outputs are
            # byte-identical. Existing DBs gain the indexes on next open (one-time build).
            try:
                self._conn.execute(
                    "CREATE INDEX IF NOT EXISTS idx_memory_ns_mkey "
                    "ON memory(namespace, mkey, created_at DESC)")
                self._conn.execute(
                    "CREATE INDEX IF NOT EXISTS idx_memory_scope_lookup "
                    "ON memory(tenant_id, project_id, scope, namespace, created_at DESC)")
                self._conn.execute(
                    "CREATE INDEX IF NOT EXISTS idx_memory_ns_sha "
                    "ON memory(namespace, content_sha256)")
            except sqlite3.OperationalError:
                pass   # fail-soft (busy writer / name collision): slow-but-correct;
                       # next open retries — same posture as the FTS DDL below.
            try:
                self._conn.execute(
                    "CREATE VIRTUAL TABLE IF NOT EXISTS memory_fts USING fts5("
                    "content, mkey, memory_id UNINDEXED, tokenize='unicode61')")
                self._fts = True
            except sqlite3.OperationalError:
                self._fts = False   # FTS5 در دسترس نیست → fallback به LIKE (search همچنان کار می‌کند)
            self._conn.commit()

    # ── نوشتن (فقط از طریقِ gate صدا زده می‌شود؛ اعتبارسنجیِ trust/namespace آن‌جاست) ──
    def insert(self, rec: dict) -> "str | None":
        """رکوردِ نرمال‌شده را immutably درج کن. خروجی memory_id یا None اگر dedupe/نامعتبر.
        dedupe: content_sha256 فعال در همان (namespace, mkey) → skip."""
        ns = str(rec.get("namespace") or "")
        if not tax.is_namespace(ns):
            raise ValueError(f"unknown namespace: {ns!r}")
        trust = str(rec.get("trust") or "UNKNOWN")
        if not tax.is_trust(trust):
            raise ValueError(f"unknown trust: {trust!r}")
        content = str(rec.get("content") or "")
        # F3 (OWNER-CONSENTS-2026-08-19T0615Z §4): متادیتای اجباری — fail-closed.
        # ردیفِ بدون confidence هرگز وارد حافظهٔ کانونی نمی‌شود (۴۲ ردیفِ تاریخیِ
        # فاقدِ confidence دست‌نخورده و EXCLUDED می‌مانند؛ این قانون فقط insert نو است).
        if rec.get("confidence") is None or rec.get("confidence") == "":
            raise ValueError("F3: confidence required for canonical insert (fail-closed)")
        csha = _sha(content)
        mkey = rec.get("mkey")
        mkey = str(mkey) if mkey is not None else None
        tenant_id = str(rec.get("tenant_id") or "personal")
        project_id = str(rec.get("project_id") or "octopus-core")
        scope = str(rec.get("scope") or "project")
        with _LOCK:
            dup = self._conn.execute(
                "SELECT memory_id FROM memory WHERE namespace=? AND content_sha256=? "
                "AND (mkey IS ? OR mkey=?) AND tenant_id=? AND project_id=? AND scope=? "
                "AND admission_state IN ('PENDING','ADMITTED') "
                "AND (valid_to IS NULL OR valid_to>?)",
                (ns, csha, mkey, mkey, tenant_id, project_id, scope, _utc_now_iso())).fetchone()
            if dup:
                return None   # dedupe: already an active identical memory
            mid = "mem_" + _sha(f"{ns}|{mkey}|{csha}|{rec.get('created_at') or _utc_now_iso()}")[:16]
            row = (mid, ns, mkey, content, csha, trust,
                   json.dumps(rec.get("provenance") or {}, ensure_ascii=False, sort_keys=True),
                   _numf(rec.get("confidence")), _numf(rec.get("salience")),
                   str(rec.get("valid_from") or _utc_now_iso()),
                   (str(rec["valid_to"]) if rec.get("valid_to") else None),
                   (str(rec["supersedes"]) if rec.get("supersedes") else None),
                   (str(rec.get("privacy")) if tax.is_privacy(rec.get("privacy")) else "scrubbed"),
                   (str(rec.get("admission_state") or "ADMITTED")
                    if str(rec.get("admission_state") or "ADMITTED") in _ADMISSION_STATES
                    else "PENDING"),
                   SCHEMA_VERSION, str(rec.get("created_at") or _utc_now_iso()),
                   tenant_id,
                   project_id,
                   scope,
                   str(rec.get("agent_id") or "unknown"),
                   str(rec.get("task_id") or ""),
                   str(rec.get("classification") or "internal"),
                   str(rec.get("policy_version") or "memory-policy.v1"),
                   (str(rec["evidence_ref"]) if rec.get("evidence_ref") else None),
                   (str(rec["confidence_source"]) if rec.get("confidence_source") else None),
                   (str(rec["confidence_method"]) if rec.get("confidence_method") else None))
            self._conn.execute(
                "INSERT OR IGNORE INTO memory(" + ",".join(_COLS) + ") VALUES(" +
                ",".join("?" * len(_COLS)) + ")", row)
            if self._fts:
                self._conn.execute("INSERT INTO memory_fts(content, mkey, memory_id) VALUES(?,?,?)",
                                   (content, mkey or "", mid))
            # supersede: کهنه را invalidate کن (valid_to=now) — نه حذفِ فیزیکی.
            # BUGFIX (C3 red-team P1): پیش‌تر فقط valid_to IS NULL را می‌بست، پس خاطراتِ
            # TTL‌دار (semantic 90d/episodic 30d) با supersede **invalidate نمی‌شدند** و
            # rollback بی‌اثر بود. حالا valid_toِ آینده را هم به now کوتاه می‌کنیم.
            sup = rec.get("supersedes")
            if sup:
                now = _utc_now_iso()
                self._conn.execute(
                    "UPDATE memory SET valid_to=?, admission_state='RETRACTED' WHERE memory_id=? "
                    "AND (valid_to IS NULL OR valid_to>?)", (now, str(sup), now))
            self._conn.commit()
            return mid

    # ── خواندن ────────────────────────────────────────────────────────────────
    def quarantine(self, memory_id: str) -> bool:
        """TEAM-A: تناقض ⇒ QUARANTINED — گذارِ وضعیت، بدون حذفِ رکورد."""
        with _LOCK:
            cur = self._conn.execute(
                "UPDATE memory SET admission_state='QUARANTINED' "
                "WHERE memory_id=? AND admission_state IN ('PENDING','ADMITTED')",
                (memory_id,))
            self._conn.commit()
            return cur.rowcount > 0

    def get(self, namespace: str, mkey: str, min_trust: str = None) -> "dict | None":
        """آخرین رکوردِ معتبرِ (namespace, mkey). min_trust → فقط اگر دستِ‌کم آن قوّت."""
        with _LOCK:
            rows = self._conn.execute(
                "SELECT " + ",".join(_COLS) + " FROM memory WHERE namespace=? AND mkey=? "
                "AND admission_state='ADMITTED' "
                "AND (valid_to IS NULL OR valid_to>?) ORDER BY created_at DESC, memory_id DESC",
                (namespace, str(mkey), _utc_now_iso())).fetchall()
        for r in rows:
            d = dict(zip(_COLS, r))
            if min_trust and not tax.trust_at_least(d["trust"], min_trust):
                continue
            return d
        return None

    def search(self, query: str, namespace: str = None, k: int = 5, min_trust: str = None,
               tenant_id: str = None, project_id: str = None, scopes: "tuple | list | None" = None) -> list:
        """FTS5/LIKE retrieval with mandatory post-hydration scope fencing when requested.
        Vector/FTS is a derived recall index; canonical metadata remains in SQLite."""
        q = str(query or "").strip()
        # A scoped query is answered from canonical SQLite, not from a global FTS candidate
        # window. This prevents a noisy tenant/project from crowding the requested scope out
        # before post-filtering. FTS remains a derived accelerator for unscoped recall.
        if tenant_id is not None or project_id is not None or scopes is not None:
            conds = ["admission_state='ADMITTED'", "(valid_to IS NULL OR valid_to>?)",
                     "(content LIKE ? OR mkey LIKE ?)"]
            args = [_utc_now_iso(), f"%{q}%", f"%{q}%"]
            if namespace:
                conds.append("namespace=?"); args.append(str(namespace))
            if tenant_id is not None:
                conds.append("tenant_id=?"); args.append(str(tenant_id))
            if project_id is not None:
                conds.append("project_id=?"); args.append(str(project_id))
            if scopes is not None:
                ss = [str(x) for x in scopes]
                if not ss:
                    return []
                conds.append("scope IN (" + ",".join("?" * len(ss)) + ")")
                args.extend(ss)
            with _LOCK:
                rows = self._conn.execute(
                    "SELECT " + ",".join(_COLS) + " FROM memory WHERE " +
                    " AND ".join(conds) + " ORDER BY salience DESC, created_at DESC LIMIT ?",
                    (*args, max(1, int(k)) * 4)).fetchall()
            out = []
            for r in rows:
                d = dict(zip(_COLS, r))
                if min_trust and not tax.trust_at_least(d["trust"], min_trust):
                    continue
                d["_rank"] = -(d.get("salience") or 0.0)
                out.append(d)
            return out[:max(1, int(k))]
        # FTS5 lenient: توکن‌های alnum (≥۳ کاراکتر) را OR کن — تا AND ضمنی/نویسه‌های خاص match را نکشند
        import re as _re
        terms = [t for t in _re.findall(r"[^\W_]{3,}", q, _re.UNICODE)][:12]
        fts_q = " OR ".join(terms) if terms else ""
        with _LOCK:
            ids = []
            if self._fts and fts_q:
                try:
                    frows = self._conn.execute(
                        "SELECT memory_id, bm25(memory_fts) AS score FROM memory_fts "
                        "WHERE memory_fts MATCH ? ORDER BY score LIMIT ?", (fts_q, max(k * 4, 20))).fetchall()
                    ids = [(r[0], r[1]) for r in frows]
                except sqlite3.OperationalError:
                    ids = []
            if not ids:   # fallback: LIKE
                like = f"%{q}%"
                lrows = self._conn.execute(
                    "SELECT memory_id, 0.0 FROM memory WHERE content LIKE ? OR mkey LIKE ? LIMIT ?",
                    (like, like, max(k * 4, 20))).fetchall()
                ids = [(r[0], 0.0) for r in lrows]
            # batched hydration (C6 evolution_v2): ONE IN(...) query for all candidates
            # instead of a per-candidate round-trip (N+1). Ranking/tie-break unchanged —
            # candidate order is preserved, and the admission_state / validity /
            # namespace / min_trust filters are byte-identical to the per-candidate form.
            # (k*4 candidates stays far below SQLite's bound-parameter limit.)
            now = _utc_now_iso()
            row_by_id = {}
            if ids:
                mids = [mid for mid, _ in ids]
                ph = ",".join("?" * len(mids))
                for hr in self._conn.execute(
                        "SELECT " + ",".join(_COLS) + " FROM memory WHERE memory_id IN (" + ph + ") "
                        "AND admission_state='ADMITTED' "
                        "AND (valid_to IS NULL OR valid_to>?)", (*mids, now)).fetchall():
                    row_by_id[hr[0]] = hr
            out = []
            for mid, score in ids:
                r = row_by_id.get(mid)
                if not r:
                    continue
                d = dict(zip(_COLS, r))
                if namespace and d["namespace"] != namespace:
                    continue
                if tenant_id is not None and d.get("tenant_id") != str(tenant_id):
                    continue
                if project_id is not None and d.get("project_id") != str(project_id):
                    continue
                if scopes is not None and d.get("scope") not in {str(x) for x in scopes}:
                    continue
                if min_trust and not tax.trust_at_least(d["trust"], min_trust):
                    continue
                # رتبهٔ ترکیبی: bm25 (کمتر=بهتر) با boostِ salience (مثبت)
                sal = d.get("salience") or 0.0
                d["_rank"] = float(score) - float(sal)
                out.append(d)
        out.sort(key=lambda x: x["_rank"])
        return out[:k]

    def set_admission_state(self, memory_id: str, state: str) -> bool:
        """CAS-like admission transition. PENDING is invisible to get/search.

        Allowed transitions are deliberately narrow: PENDING→ADMITTED/RETRACTED and
        ADMITTED→RETRACTED. A retracted memory can never be resurrected in place.
        """
        state = str(state or "").upper()
        if state not in _ADMISSION_STATES or state == "PENDING":
            return False
        with _LOCK:
            row = self._conn.execute(
                "SELECT admission_state FROM memory WHERE memory_id=?", (str(memory_id),)).fetchone()
            if not row or row[0] == "RETRACTED":
                return False
            if row[0] not in ("PENDING", "ADMITTED"):
                return False
            if state == "RETRACTED":
                cur = self._conn.execute(
                    "UPDATE memory SET admission_state='RETRACTED', valid_to=? "
                    "WHERE memory_id=? AND admission_state=?",
                    (_utc_now_iso(), str(memory_id), row[0]))
            else:
                cur = self._conn.execute(
                    "UPDATE memory SET admission_state='ADMITTED' "
                    "WHERE memory_id=? AND admission_state=?",
                    (str(memory_id), row[0]))
            self._conn.commit()
            return cur.rowcount == 1

    def admission_state(self, memory_id: str) -> "str | None":
        with _LOCK:
            row = self._conn.execute(
                "SELECT admission_state FROM memory WHERE memory_id=?", (str(memory_id),)).fetchone()
        return str(row[0]) if row else None

    def as_memories_used(self, recs: list) -> list:
        """نگاشت به شکلِ دقیقِ decision_receipt.memories_used (hash/ref فقط، بدونِ متنِ خام)."""
        now = _utc_now_iso()
        return [{"memory_id": d["memory_id"], "content_sha256": d["content_sha256"],
                 "trust_grade": d["trust"], "retrieved_at": now} for d in recs]

    def metrics(self) -> dict:
        with _LOCK:
            rows = self._conn.execute(
                "SELECT namespace, trust, valid_to, admission_state FROM memory").fetchall()
        m = {"total": len(rows), "active": 0, "pending": 0, "retracted": 0,
             "by_trust": {}, "by_namespace": {}, "fts": self._fts,
             "schema_version": SCHEMA_VERSION}
        now = _utc_now_iso()
        for ns, tr, vt, adm in rows:
            if adm == "ADMITTED" and (vt is None or vt > now):
                m["active"] += 1
            elif adm == "PENDING":
                m["pending"] += 1
            elif adm == "RETRACTED":
                m["retracted"] += 1
            m["by_trust"][tr] = m["by_trust"].get(tr, 0) + 1
            m["by_namespace"][ns] = m["by_namespace"].get(ns, 0) + 1
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


def _numf(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None
