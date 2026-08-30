#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""memory_store_opt.py — C6 evolution_v1 CANDIDATE: batched-hydration search().

Subclasses the REAL MemoryStore and overrides ONLY search(): the per-candidate
N+1 hydration loop is replaced by a single batched `WHERE memory_id IN (...)` query,
then rows are re-ordered by the original FTS candidate order so ranking/tie-breaks
are byte-identical to the baseline. Everything else (insert, get, FTS, ranking math,
validity/namespace/min_trust filters) is inherited unchanged.

This override mirrors EXACTLY the minimal patch proposed for _ops/memory/memory_store.py.
"""
from __future__ import annotations

import re
import sqlite3

import memory_store as ms


class OptMemoryStore(ms.MemoryStore):
    def search(self, query: str, namespace: str = None, k: int = 5, min_trust: str = None) -> list:
        q = str(query or "").strip()
        terms = [t for t in re.findall(r"[^\W_]{3,}", q, re.UNICODE)][:12]
        fts_q = " OR ".join(terms) if terms else ""
        with ms._LOCK:
            ids = []
            if self._fts and fts_q:
                try:
                    frows = self._conn.execute(
                        "SELECT memory_id, bm25(memory_fts) AS score FROM memory_fts "
                        "WHERE memory_fts MATCH ? ORDER BY score LIMIT ?",
                        (fts_q, max(k * 4, 20))).fetchall()
                    ids = [(r[0], r[1]) for r in frows]
                except sqlite3.OperationalError:
                    ids = []
            if not ids:   # fallback: LIKE
                like = f"%{q}%"
                lrows = self._conn.execute(
                    "SELECT memory_id, 0.0 FROM memory WHERE content LIKE ? OR mkey LIKE ? LIMIT ?",
                    (like, like, max(k * 4, 20))).fetchall()
                ids = [(r[0], 0.0) for r in lrows]

            # ── batched hydration (the fix): one query for all candidates ──
            now = ms._utc_now_iso()
            score_by_id = {}
            for mid, score in ids:
                # first occurrence wins (mirrors baseline loop order; ids are unique anyway)
                if mid not in score_by_id:
                    score_by_id[mid] = score
            row_by_id = {}
            if score_by_id:
                mids = list(score_by_id.keys())
                ph = ",".join("?" * len(mids))
                hydrated = self._conn.execute(
                    "SELECT " + ",".join(ms._COLS) + " FROM memory WHERE memory_id IN (" + ph + ") "
                    "AND (valid_to IS NULL OR valid_to>?)", (*mids, now)).fetchall()
                for r in hydrated:
                    d = dict(zip(ms._COLS, r))
                    row_by_id[d["memory_id"]] = d

            out = []
            for mid, score in ids:                     # preserve original candidate order
                d = row_by_id.get(mid)
                if not d:                               # dropped by validity filter
                    continue
                if namespace and d["namespace"] != namespace:
                    continue
                if min_trust and not ms.tax.trust_at_least(d["trust"], min_trust):
                    continue
                sal = d.get("salience") or 0.0
                d = dict(d)                             # avoid mutating the cached dict
                d["_rank"] = float(score) - float(sal)
                out.append(d)
        out.sort(key=lambda x: x["_rank"])              # stable sort — same tie-break as baseline
        return out[:k]
