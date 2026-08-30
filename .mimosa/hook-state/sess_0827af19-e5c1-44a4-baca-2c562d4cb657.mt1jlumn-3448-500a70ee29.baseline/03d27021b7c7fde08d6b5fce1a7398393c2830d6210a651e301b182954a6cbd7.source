# -*- coding: utf-8 -*-
"""Memory Layer — یک sqlite مشترک (core.db) برای بریف/بازخورد/صف/دانش/بودجه.

طبق ARCHITECTURE §۳. migration ها idempotent اند؛ thread-safe با یک lock.
هیچ secret ای اینجا ذخیره نمی‌شود (to_ref = ارجاع کاربر، نه شماره/توکن).
"""
from __future__ import annotations

import hashlib
import sqlite3
import threading
from datetime import date, datetime
from pathlib import Path
from typing import List, Optional

from core.contracts import Brief, Feedback, OutboxMessage

_SCHEMA = """
CREATE TABLE IF NOT EXISTS briefs(
  id INTEGER PRIMARY KEY, business TEXT NOT NULL, title TEXT, opportunity TEXT,
  why TEXT, action TEXT, source TEXT, created TEXT, notified INTEGER DEFAULT 0);
CREATE TABLE IF NOT EXISTS feedback(
  id INTEGER PRIMARY KEY, brief_id INTEGER NOT NULL, useful INTEGER NOT NULL,
  note TEXT DEFAULT '', ts TEXT);
CREATE TABLE IF NOT EXISTS outbox(
  id INTEGER PRIMARY KEY, business TEXT NOT NULL, channel TEXT, to_ref TEXT,
  text TEXT, brief_id INTEGER, status TEXT DEFAULT 'pending',
  notified INTEGER DEFAULT 0, ts TEXT, resolved_ts TEXT, detail TEXT DEFAULT '');
CREATE TABLE IF NOT EXISTS knowledge(
  id INTEGER PRIMARY KEY, business TEXT, tag TEXT, text TEXT, source TEXT, ts TEXT);
CREATE INDEX IF NOT EXISTS idx_know_tag ON knowledge(tag);
CREATE TABLE IF NOT EXISTS usage(
  id INTEGER PRIMARY KEY, day TEXT, provider TEXT, business TEXT,
  tokens_in INTEGER DEFAULT 0, tokens_out INTEGER DEFAULT 0, cost_usd REAL DEFAULT 0);
CREATE TABLE IF NOT EXISTS proposals(
  id INTEGER PRIMARY KEY, title TEXT, problem TEXT, solution TEXT, risk TEXT,
  impact TEXT, rollback TEXT, status TEXT DEFAULT 'pending',
  notified INTEGER DEFAULT 0, ts TEXT, resolved_ts TEXT);
"""


def _now() -> str:
    return datetime.now().isoformat(timespec="seconds")


class Memory:
    def __init__(self, db_path):
        self._path = str(db_path)
        Path(self._path).parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._c = sqlite3.connect(self._path, check_same_thread=False)
        with self._lock:
            self._c.executescript(_SCHEMA)
            self._c.commit()

    # ---------- briefs ----------
    def add_brief(self, b: Brief) -> int:
        with self._lock:
            cur = self._c.execute(
                "INSERT INTO briefs(business,title,opportunity,why,action,source,created)"
                " VALUES(?,?,?,?,?,?,?)",
                (b.business, b.title, b.opportunity, b.why, b.action, b.source, b.created))
            self._c.commit()
            b.id = cur.lastrowid
            return b.id

    def _row_brief(self, r) -> Brief:
        return Brief(business=r[1], title=r[2], opportunity=r[3], why=r[4],
                     action=r[5], source=r[6], created=r[7], id=r[0])

    def unnotified_briefs(self) -> List[Brief]:
        with self._lock:
            rows = self._c.execute("SELECT * FROM briefs WHERE notified=0 ORDER BY id").fetchall()
        return [self._row_brief(r) for r in rows]

    def recent_briefs(self, n: int = 5, business: Optional[str] = None) -> List[Brief]:
        q = "SELECT * FROM briefs" + (" WHERE business=?" if business else "") + " ORDER BY id DESC LIMIT ?"
        args = (business, n) if business else (n,)
        with self._lock:
            rows = self._c.execute(q, args).fetchall()
        return [self._row_brief(r) for r in rows]

    def mark_brief_notified(self, brief_id: int) -> None:
        with self._lock:
            self._c.execute("UPDATE briefs SET notified=1 WHERE id=?", (brief_id,))
            self._c.commit()

    # ---------- feedback (حلقه یادگیری) ----------
    def add_feedback(self, f: Feedback) -> None:
        with self._lock:
            self._c.execute("INSERT INTO feedback(brief_id,useful,note,ts) VALUES(?,?,?,?)",
                            (f.brief_id, 1 if f.useful else 0, f.note, f.ts))
            self._c.commit()

    def feedback_for(self, business: str, n: int = 20) -> List[Feedback]:
        with self._lock:
            rows = self._c.execute(
                "SELECT f.brief_id, f.useful, f.note, f.ts FROM feedback f"
                " JOIN briefs b ON b.id=f.brief_id WHERE b.business=?"
                " ORDER BY f.id DESC LIMIT ?", (business, n)).fetchall()
        return [Feedback(brief_id=r[0], useful=bool(r[1]), note=r[2], ts=r[3]) for r in rows]

    # ---------- outbox (صف رکن B) ----------
    def add_outbox(self, m: OutboxMessage) -> int:
        with self._lock:
            cur = self._c.execute(
                "INSERT INTO outbox(business,channel,to_ref,text,brief_id,status,ts)"
                " VALUES(?,?,?,?,?,?,?)",
                (m.business, m.channel, m.to_ref, m.text, m.brief_id, m.status, m.ts))
            self._c.commit()
            m.id = cur.lastrowid
            return m.id

    def _row_out(self, r) -> OutboxMessage:
        return OutboxMessage(business=r[1], channel=r[2], to_ref=r[3], text=r[4],
                             brief_id=r[5], status=r[6], id=r[0], ts=r[8])

    def get_outbox(self, msg_id: int) -> Optional[OutboxMessage]:
        with self._lock:
            r = self._c.execute("SELECT * FROM outbox WHERE id=?", (msg_id,)).fetchone()
        return self._row_out(r) if r else None

    def pending_outbox(self) -> List[OutboxMessage]:
        with self._lock:
            rows = self._c.execute(
                "SELECT * FROM outbox WHERE status='pending' ORDER BY id").fetchall()
        return [self._row_out(r) for r in rows]

    def unnotified_outbox(self) -> List[OutboxMessage]:
        with self._lock:
            rows = self._c.execute(
                "SELECT * FROM outbox WHERE status='pending' AND notified=0 ORDER BY id").fetchall()
        return [self._row_out(r) for r in rows]

    def mark_outbox_notified(self, msg_id: int) -> None:
        with self._lock:
            self._c.execute("UPDATE outbox SET notified=1 WHERE id=?", (msg_id,))
            self._c.commit()

    def set_outbox(self, msg_id: int, status: str, text: Optional[str] = None, detail: str = "") -> None:
        with self._lock:
            if text is not None:
                self._c.execute("UPDATE outbox SET status=?, text=?, resolved_ts=?, detail=? WHERE id=?",
                                (status, text, _now(), detail, msg_id))
            else:
                self._c.execute("UPDATE outbox SET status=?, resolved_ts=?, detail=? WHERE id=?",
                                (status, _now(), detail, msg_id))
            self._c.commit()

    # ---------- knowledge + cache ----------
    def knowledge_add(self, text: str, tag: str = "", business: Optional[str] = None,
                      source: str = "") -> None:
        with self._lock:
            self._c.execute("INSERT INTO knowledge(business,tag,text,source,ts) VALUES(?,?,?,?,?)",
                            (business, tag, text, source, _now()))
            self._c.commit()

    def knowledge_search(self, term: str, business: Optional[str] = None, n: int = 8) -> List[str]:
        q = "SELECT text FROM knowledge WHERE text LIKE ?"
        args: list = [f"%{term}%"]
        if business:
            q += " AND (business=? OR business IS NULL)"
            args.append(business)
        q += " ORDER BY id DESC LIMIT ?"
        args.append(n)
        with self._lock:
            rows = self._c.execute(q, args).fetchall()
        return [r[0] for r in rows]

    @staticmethod
    def cache_key(payload: str) -> str:
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:32]

    def cache_get(self, key: str, max_age_hours: int = 24) -> Optional[str]:
        with self._lock:
            r = self._c.execute(
                "SELECT text, ts FROM knowledge WHERE tag=? ORDER BY id DESC LIMIT 1",
                (f"cache:{key}",)).fetchone()
        if not r:
            return None
        age_h = (datetime.now() - datetime.fromisoformat(r[1])).total_seconds() / 3600
        return r[0] if age_h <= max_age_hours else None

    def cache_put(self, key: str, text: str) -> None:
        self.knowledge_add(text, tag=f"cache:{key}")

    # ---------- usage (بودجه) ----------
    def usage_add(self, provider: str, tokens_in: int, tokens_out: int,
                  cost_usd: float, business: str = "") -> None:
        with self._lock:
            self._c.execute(
                "INSERT INTO usage(day,provider,business,tokens_in,tokens_out,cost_usd)"
                " VALUES(?,?,?,?,?,?)",
                (date.today().isoformat(), provider, business, tokens_in, tokens_out, cost_usd))
            self._c.commit()

    def month_cost(self, provider: str) -> float:
        month = date.today().isoformat()[:7]
        with self._lock:
            r = self._c.execute(
                "SELECT COALESCE(SUM(cost_usd),0) FROM usage WHERE provider=? AND day LIKE ?",
                (provider, month + "%")).fetchone()
        return float(r[0] or 0)

    def day_cost(self, provider: str) -> float:
        with self._lock:
            r = self._c.execute(
                "SELECT COALESCE(SUM(cost_usd),0) FROM usage WHERE provider=? AND day=?",
                (provider, date.today().isoformat())).fetchone()
        return float(r[0] or 0)

    # ---------- proposals (مغز تکاملی — فاز ۴) ----------
    def add_proposal(self, title: str, problem: str, solution: str, risk: str,
                     impact: str, rollback: str) -> int:
        with self._lock:
            cur = self._c.execute(
                "INSERT INTO proposals(title,problem,solution,risk,impact,rollback,ts)"
                " VALUES(?,?,?,?,?,?,?)",
                (title, problem, solution, risk, impact, rollback, _now()))
            self._c.commit()
            return cur.lastrowid

    def get_proposal(self, pid: int):
        with self._lock:
            return self._c.execute("SELECT * FROM proposals WHERE id=?", (pid,)).fetchone()

    def pending_proposals(self) -> list:
        with self._lock:
            return self._c.execute(
                "SELECT id,title,problem,solution,risk,impact,rollback,ts FROM proposals"
                " WHERE status='pending' ORDER BY id").fetchall()

    def unnotified_proposals(self) -> list:
        with self._lock:
            return self._c.execute(
                "SELECT id,title,problem,solution,risk,impact,rollback FROM proposals"
                " WHERE status='pending' AND notified=0 ORDER BY id").fetchall()

    def mark_proposal_notified(self, pid: int) -> None:
        with self._lock:
            self._c.execute("UPDATE proposals SET notified=1 WHERE id=?", (pid,))
            self._c.commit()

    def set_proposal(self, pid: int, status: str) -> None:
        with self._lock:
            self._c.execute("UPDATE proposals SET status=?, resolved_ts=? WHERE id=?",
                            (status, _now(), pid))
            self._c.commit()

    def expire_proposals(self, max_age_days: int = 30) -> int:
        """الگوی TTL (توصیه pass-1): پیشنهاد بی‌verdict > سقف → expired (fail-closed)."""
        cutoff = datetime.now().timestamp() - max_age_days * 86400
        n = 0
        with self._lock:
            rows = self._c.execute("SELECT id, ts FROM proposals WHERE status='pending'").fetchall()
            for pid, ts in rows:
                try:
                    if datetime.fromisoformat(ts).timestamp() < cutoff:
                        self._c.execute(
                            "UPDATE proposals SET status='expired', resolved_ts=? WHERE id=?",
                            (_now(), pid))
                        n += 1
                except Exception:  # noqa: BLE001
                    continue
            self._c.commit()
        return n

    def stats(self) -> dict:
        with self._lock:
            b = self._c.execute("SELECT COUNT(*) FROM briefs").fetchone()[0]
            p = self._c.execute("SELECT COUNT(*) FROM outbox WHERE status='pending'").fetchone()[0]
            s = self._c.execute("SELECT COUNT(*) FROM outbox WHERE status='sent'").fetchone()[0]
            k = self._c.execute("SELECT COUNT(*) FROM knowledge WHERE tag NOT LIKE 'cache:%'").fetchone()[0]
        return {"briefs": b, "pending": p, "sent": s, "knowledge": k,
                "deepseek_month": round(self.month_cost("deepseek"), 3),
                "fugu_month": round(self.month_cost("fugu"), 2)}
