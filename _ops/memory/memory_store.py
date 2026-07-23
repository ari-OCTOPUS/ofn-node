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
import time
from datetime import datetime, timezone
from pathlib import Path

_HERE = Path(__file__).resolve().parent
import sys
if str(_HERE.parent / "outcomes") not in sys.path:
    sys.path.insert(0, str(_HERE.parent / "outcomes"))
import taxonomy as tax  # noqa: E402

SCHEMA_VERSION = 1
_LOCK = threading.RLock()
_COLS = ("memory_id", "namespace", "mkey", "content", "content_sha256", "trust",
         "provenance_json", "confidence", "salience", "valid_from", "valid_to",
         "supersedes", "privacy", "schema_version", "created_at")


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
                "privacy TEXT NOT NULL, schema_version INTEGER NOT NULL, created_at TEXT NOT NULL)")
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
        csha = _sha(content)
        mkey = rec.get("mkey")
        mkey = str(mkey) if mkey is not None else None
        with _LOCK:
            dup = self._conn.execute(
                "SELECT memory_id FROM memory WHERE namespace=? AND content_sha256=? "
                "AND (mkey IS ? OR mkey=?) AND (valid_to IS NULL OR valid_to>?)",
                (ns, csha, mkey, mkey, _utc_now_iso())).fetchone()
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
                   SCHEMA_VERSION, str(rec.get("created_at") or _utc_now_iso()))
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
                    "UPDATE memory SET valid_to=? WHERE memory_id=? "
                    "AND (valid_to IS NULL OR valid_to>?)", (now, str(sup), now))
            self._conn.commit()
            return mid

    # ── خواندن ────────────────────────────────────────────────────────────────
    def get(self, namespace: str, mkey: str, min_trust: str = None) -> "dict | None":
        """آخرین رکوردِ معتبرِ (namespace, mkey). min_trust → فقط اگر دستِ‌کم آن قوّت."""
        with _LOCK:
            rows = self._conn.execute(
                "SELECT " + ",".join(_COLS) + " FROM memory WHERE namespace=? AND mkey=? "
                "AND (valid_to IS NULL OR valid_to>?) ORDER BY created_at DESC, memory_id DESC",
                (namespace, str(mkey), _utc_now_iso())).fetchall()
        for r in rows:
            d = dict(zip(_COLS, r))
            if min_trust and not tax.trust_at_least(d["trust"], min_trust):
                continue
            return d
        return None

    def search(self, query: str, namespace: str = None, k: int = 5, min_trust: str = None) -> list:
        """FTS5 bm25 + رتبه‌بندیِ ترکیبی با salience/recency؛ fallback به LIKE اگر FTS نبود.
        فقط رکوردهای معتبر؛ اختیاری min_trust."""
        q = str(query or "").strip()
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
            out = []
            for mid, score in ids:
                r = self._conn.execute("SELECT " + ",".join(_COLS) + " FROM memory WHERE memory_id=? "
                                       "AND (valid_to IS NULL OR valid_to>?)",
                                       (mid, _utc_now_iso())).fetchone()
                if not r:
                    continue
                d = dict(zip(_COLS, r))
                if namespace and d["namespace"] != namespace:
                    continue
                if min_trust and not tax.trust_at_least(d["trust"], min_trust):
                    continue
                # رتبهٔ ترکیبی: bm25 (کمتر=بهتر) با boostِ salience (مثبت)
                sal = d.get("salience") or 0.0
                d["_rank"] = float(score) - float(sal)
                out.append(d)
        out.sort(key=lambda x: x["_rank"])
        return out[:k]

    def as_memories_used(self, recs: list) -> list:
        """نگاشت به شکلِ دقیقِ decision_receipt.memories_used (hash/ref فقط، بدونِ متنِ خام)."""
        now = _utc_now_iso()
        return [{"memory_id": d["memory_id"], "content_sha256": d["content_sha256"],
                 "trust_grade": d["trust"], "retrieved_at": now} for d in recs]

    def metrics(self) -> dict:
        with _LOCK:
            rows = self._conn.execute("SELECT namespace, trust, valid_to FROM memory").fetchall()
        m = {"total": len(rows), "active": 0, "by_trust": {}, "by_namespace": {},
             "fts": self._fts, "schema_version": SCHEMA_VERSION}
        now = _utc_now_iso()
        for ns, tr, vt in rows:
            if vt is None or vt > now:
                m["active"] += 1
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
