"""ذخیره‌سازِ ساده با پایگاه‌دادهٔ سبک (SQLite): شناسهٔ فرایندها، پرچم‌ها، دفتر رویدادها.

افزون بر دفترِ سادهٔ events (سازگاریِ عقب‌رو)، یک «دفترِ رویدادِ evt.v1» تغییرناپذیر
دارد: هر رکورد ULIDِ مرتب‌شونده، هشِ محتوا، و زنجیرهٔ prev_hash→self_hash دارد تا
دستکاری یا حذفِ میانی قابلِ تشخیص باشد. صدورِ شناسهٔ تصمیم ZIM-DEC-YYYYMMDD-NNNN.
همه افزایشی است؛ log()/recent_events() و طرحِ قبلی دست‌نخورده می‌مانند.
"""
import hashlib
import json
import os
import sqlite3
import time
from pathlib import Path
from typing import List, Optional, Tuple

# ── evt.v1 primitives ───────────────────────────────────────────────────────
_GENESIS = "0" * 64  # prev_hash نخستین رکورد
_CROCKFORD = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"  # ULID base32 (Crockford)


def _b32(value: int, length: int) -> str:
    out = []
    for _ in range(length):
        out.append(_CROCKFORD[value & 0x1F])
        value >>= 5
    return "".join(reversed(out))


def new_ulid(ts_ms: Optional[int] = None, rand: Optional[bytes] = None) -> str:
    """ULID ۲۶ نویسه‌ای: ۱۰ نویسه زمان (میلی‌ثانیه) + ۱۶ نویسه تصادفی. مرتب‌شونده."""
    ts_ms = int(ts_ms if ts_ms is not None else time.time() * 1000)
    rb = rand if rand is not None else os.urandom(10)
    return _b32(ts_ms, 10) + _b32(int.from_bytes(rb, "big"), 16)


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def format_decision_id(day: str, n: int) -> str:
    """قالبِ شناسهٔ تصمیم — خالص و قطعی."""
    return f"ZIM-DEC-{day}-{int(n):04d}"


class Store:
    def __init__(self, path):
        self.path = str(path)
        Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        self._init()

    def _conn(self):
        c = sqlite3.connect(self.path)
        c.row_factory = sqlite3.Row
        return c

    def _init(self) -> None:
        with self._conn() as c:
            c.execute("CREATE TABLE IF NOT EXISTS proc (id TEXT PRIMARY KEY, pid INTEGER)")
            c.execute("CREATE TABLE IF NOT EXISTS flags (k TEXT PRIMARY KEY, v TEXT)")
            c.execute("CREATE TABLE IF NOT EXISTS events (ts REAL, kind TEXT, project TEXT, detail TEXT, actor TEXT)")
            cols = [r[1] for r in c.execute("PRAGMA table_info(events)").fetchall()]
            if "actor" not in cols:
                c.execute("ALTER TABLE events ADD COLUMN actor TEXT")
            # دفترِ رویدادِ تغییرناپذیر evt.v1 — زنجیرهٔ هش + ULID + شناسهٔ تصمیم
            c.execute(
                "CREATE TABLE IF NOT EXISTS ledger ("
                "seq INTEGER PRIMARY KEY AUTOINCREMENT, "
                "event_id TEXT UNIQUE, ts REAL, kind TEXT, project TEXT, "
                "actor TEXT, detail TEXT, decision_id TEXT, "
                "content_hash TEXT, prev_hash TEXT, self_hash TEXT)"
            )
            # چرخهٔ Proposal→Decision (propose-only governance)
            c.execute(
                "CREATE TABLE IF NOT EXISTS proposals ("
                "proposal_id TEXT PRIMARY KEY, kind TEXT, project TEXT, "
                "detail TEXT, risk TEXT, proposed_by TEXT, status TEXT, "
                "created_at REAL, decision_id TEXT, decided_by TEXT, "
                "decided_at REAL, ref TEXT)"
            )
            pcols = [r[1] for r in c.execute("PRAGMA table_info(proposals)").fetchall()]
            if "ref" not in pcols:   # مهاجرتِ افزایشی برای دیتابیسِ قدیمی
                c.execute("ALTER TABLE proposals ADD COLUMN ref TEXT")

    def set_pid(self, pid_id: str, pid: int) -> None:
        with self._conn() as c:
            c.execute("REPLACE INTO proc (id, pid) VALUES (?, ?)", (pid_id, pid))

    def get_pid(self, pid_id: str) -> Optional[int]:
        with self._conn() as c:
            row = c.execute("SELECT pid FROM proc WHERE id = ?", (pid_id,)).fetchone()
            return int(row["pid"]) if row else None

    def clear_pid(self, pid_id: str) -> None:
        with self._conn() as c:
            c.execute("DELETE FROM proc WHERE id = ?", (pid_id,))

    def set_flag(self, k: str, v: str) -> None:
        with self._conn() as c:
            c.execute("REPLACE INTO flags (k, v) VALUES (?, ?)", (k, v))

    def get_flag(self, k: str, default: Optional[str] = None) -> Optional[str]:
        with self._conn() as c:
            row = c.execute("SELECT v FROM flags WHERE k = ?", (k,)).fetchone()
            return row["v"] if row else default

    def log(self, kind: str, project: str, detail: str = "", actor: str = "-") -> None:
        with self._conn() as c:
            c.execute("INSERT INTO events (ts, kind, project, detail, actor) VALUES (?, ?, ?, ?, ?)",
                      (time.time(), kind, project, detail, actor))

    def recent_events(self, n: int = 20) -> List[Tuple]:
        with self._conn() as c:
            rows = c.execute("SELECT ts, kind, project, detail, actor FROM events ORDER BY ts DESC LIMIT ?", (n,)).fetchall()
            return [(r["ts"], r["kind"], r["project"], r["detail"], r["actor"]) for r in rows]

    # ── evt.v1 دفترِ رویدادِ تغییرناپذیر ────────────────────────────────────
    def _hashes(self, seq, event_id, ts, kind, project, actor, detail,
                decision_id, prev_hash):
        """(content_hash, self_hash) را قطعی محاسبه می‌کند — مستقل از ترتیبِ کلید."""
        content = json.dumps(
            {"kind": kind, "project": project, "actor": actor,
             "detail": detail, "decision_id": decision_id},
            ensure_ascii=False, sort_keys=True)
        content_hash = _sha256(content)
        payload = "|".join([str(seq), event_id, f"{ts:.6f}",
                            content_hash, prev_hash or ""])
        return content_hash, _sha256(payload)

    def append_event(self, kind: str, project: str, detail: str = "",
                     actor: str = "-", decision_id: Optional[str] = None) -> dict:
        """یک رویدادِ evt.v1 به دفتر می‌افزاید و رکوردِ ساخته‌شده را برمی‌گرداند.

        فقط-افزودنی: seq و prev_hash از آخرین رکورد گرفته می‌شوند؛ زنجیره را می‌بندد.
        """
        with self._conn() as c:
            last = c.execute(
                "SELECT seq, self_hash FROM ledger ORDER BY seq DESC LIMIT 1"
            ).fetchone()
            seq = (last["seq"] + 1) if last else 1
            prev_hash = last["self_hash"] if last else _GENESIS
            ts = time.time()
            event_id = new_ulid(int(ts * 1000))
            content_hash, self_hash = self._hashes(
                seq, event_id, ts, kind, project, actor, detail, decision_id, prev_hash)
            c.execute(
                "INSERT INTO ledger (seq, event_id, ts, kind, project, actor, "
                "detail, decision_id, content_hash, prev_hash, self_hash) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (seq, event_id, ts, kind, project, actor, detail,
                 decision_id, content_hash, prev_hash, self_hash))
        return {"seq": seq, "event_id": event_id, "ts": ts, "kind": kind,
                "project": project, "actor": actor, "detail": detail,
                "decision_id": decision_id, "content_hash": content_hash,
                "prev_hash": prev_hash, "self_hash": self_hash}

    def ledger_tail(self, n: int = 20) -> List[dict]:
        with self._conn() as c:
            rows = c.execute(
                "SELECT * FROM ledger ORDER BY seq DESC LIMIT ?", (n,)).fetchall()
        return [dict(r) for r in rows]

    def verify_ledger(self) -> dict:
        """کلِ زنجیره را دوباره می‌سازد و صحتِ hash-chain را می‌سنجد."""
        with self._conn() as c:
            rows = c.execute("SELECT * FROM ledger ORDER BY seq ASC").fetchall()
        prev = _GENESIS
        for r in rows:
            ch, sh = self._hashes(
                r["seq"], r["event_id"], r["ts"], r["kind"], r["project"],
                r["actor"], r["detail"], r["decision_id"], prev)
            if r["prev_hash"] != prev or r["content_hash"] != ch or r["self_hash"] != sh:
                return {"ok": False, "count": len(rows), "broken_at": r["seq"]}
            prev = r["self_hash"]
        return {"ok": True, "count": len(rows), "broken_at": None}

    def next_decision_id(self, day: Optional[str] = None) -> str:
        """شناسهٔ بعدیِ تصمیم ZIM-DEC-YYYYMMDD-NNNN (بر پایهٔ دفتر)."""
        day = day or time.strftime("%Y%m%d")
        prefix = f"ZIM-DEC-{day}-"
        with self._conn() as c:
            rows = c.execute(
                "SELECT decision_id FROM ledger WHERE decision_id LIKE ?",
                (prefix + "%",)).fetchall()
        nums = []
        for r in rows:
            did = r["decision_id"] or ""
            if did.startswith(prefix):
                try:
                    nums.append(int(did.rsplit("-", 1)[1]))
                except (ValueError, IndexError):
                    continue
        return format_decision_id(day, max(nums, default=0) + 1)

    # ── proposals (چرخهٔ propose→decide) ────────────────────────────────────
    def put_proposal(self, p: dict) -> None:
        with self._conn() as c:
            c.execute(
                "INSERT OR REPLACE INTO proposals (proposal_id, kind, project, "
                "detail, risk, proposed_by, status, created_at, decision_id, "
                "decided_by, decided_at, ref) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (p["proposal_id"], p.get("kind"), p.get("project"), p.get("detail"),
                 p.get("risk"), p.get("proposed_by"), p.get("status"),
                 p.get("created_at"), p.get("decision_id"), p.get("decided_by"),
                 p.get("decided_at"), p.get("ref")))

    def get_proposal(self, proposal_id: str) -> Optional[dict]:
        with self._conn() as c:
            r = c.execute("SELECT * FROM proposals WHERE proposal_id = ?",
                          (proposal_id,)).fetchone()
        return dict(r) if r else None

    def get_proposal_by_ref(self, ref: str) -> Optional[dict]:
        """جست‌وجوی proposal با شناسهٔ انسان‌خوانِ ZIM-DEC (برای /approve)."""
        with self._conn() as c:
            r = c.execute("SELECT * FROM proposals WHERE ref = ? "
                          "ORDER BY created_at DESC LIMIT 1", (ref,)).fetchone()
        return dict(r) if r else None

    def list_proposals(self, status: Optional[str] = None) -> List[dict]:
        with self._conn() as c:
            if status:
                rows = c.execute(
                    "SELECT * FROM proposals WHERE status = ? ORDER BY created_at DESC",
                    (status,)).fetchall()
            else:
                rows = c.execute(
                    "SELECT * FROM proposals ORDER BY created_at DESC").fetchall()
        return [dict(r) for r in rows]
