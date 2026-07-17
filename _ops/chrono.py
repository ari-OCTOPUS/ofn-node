#!/usr/bin/env python3
"""
chrono.py — بسترِ زمان و ضربانِ قلبِ Octopus (Phase 1: THE HEART).

پیاده‌سازیِ verbatim از:
  · CHRONOS-FABLE-OS/10_Implementation/DataSchemas.sql (DDL دقیق)
  · CHRONOS-FABLE-OS/01_SourceMap/_primaries/OCTOPUS_CHRONO_ARCHITECTURE.md §8/§9/§11
  · CHRONOS-FABLE-OS/08_Safety/HeartDesign_PulseCore.md (EffectorGate + kill supreme)

سه منبعِ ضربان (DOC-B §4):
  Pacemaker (تیکِ ~60s؛ فقط liveness + scheduler=F19) · HLC (ساعتِ ذهنیِ هر پا)
  · human-append به LANGAR (تنها چیزی که فلشِ میرا `age_tick` را می‌برد — TINV-3).

قوانینِ سخت (TINV):
  TINV-1 HLC یکنواختِ اکید · TINV-2 ترتیبِ کلی فقط از LANGAR (= ledger ژنوم،
  گسترش‌یافته — جدولِ رقیب ممنوع) · TINV-3 (v0.4.6 re-ratify) `age_tick` با human **یا** heartbeat
  · TINV-4 phi-accrual: alive→suspected→failed · TINV-5 پاها هرگز ساعتِ دیواری
  نمی‌خوانند (فقط HLC محلی + آخرین beat_seq؛ مهرزنی کارِ بستر است)
  · TINV-6 experience_rate کران‌دار [0, cap] · TINV-7 هیچ اثرِ برگشت‌ناپذیری بدونِ
  append قبلی settle نمی‌شود (EffectorGate — تک‌گلوگاه؛ kill آن را force-close می‌کند).

دو ساعت (two-clock):
  `experience_rate`/`metabolic_age` = پیریِ متابولیک (سریع‌تر تجربه = سریع‌تر فرسایش،
  در chrono.db). `age_tick` = فلشِ میرا روی ledger ژنوم. ✅ verdict آری 2026-07-08
  **re-ratify شد (v0.4.6): age_tick هم heart-driven است** — هر `CHRONO_AGE_PER_N_BEATS`
  ضربان یک appendِ HEARTBEAT با `beat=True` فلش را +۱ می‌برد (ماشین خودش پیر می‌شود)؛
  human-append هم جدا فلش را می‌برد. رکوردهای legacy با قانونِ TINV-3ِ قدیم verify
  می‌شوند (نسخه‌بندی با `age_rule` در ledger.py). TINV-3ِ سرِ فایل بازنویسی شد.

SQLite تک-writer: همهٔ نوشتن‌های پا در سدِ ضربان serialize می‌شوند (DOC-B §12) —
پاها فقط در حافظه بافر می‌کنند؛ تنها pacemaker به دیسک می‌نویسد.

پیش‌فرض‌های PENDING-VERDICT (verdict «بساز با پیش‌فرض‌ها» 2026-07-08؛ env-tunable):
  CHRONO_PERIOD_S=60 · CHRONO_PHI_SUSPECT=8 · CHRONO_PHI_DEAD=16
  · CHRONO_XP_RATE_CAP=50 ev/s (سقفِ پلانک‌آنالوگ) · CHRONO_WEAR_BASE=1.0
status: additive؛ منطقِ کسب‌وکار دست‌نخورده (DOC-B §0). $0، آفلاین، stdlib-only.
"""
from __future__ import annotations

import json
import math
import os
import pathlib
import sqlite3
import sys
import threading
import time
from collections import deque
from typing import Any, Callable, Iterable, Optional

_HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE / "budget"))
import opslib  # noqa: E402

# ─── پیکربندی (PENDING-VERDICT — هر عدد env-tunable، هیچ‌کدام hardcode-قفل نیست) ──
def _envf(name: str, default: float) -> float:
    try:
        return float(os.environ.get(name, default))
    except ValueError:
        return default

PERIOD_S     = _envf("CHRONO_PERIOD_S", 60.0)      # DOC-B §9 پیش‌فرض
PHI_SUSPECT  = _envf("CHRONO_PHI_SUSPECT", 8.0)    # TINV-4
PHI_DEAD     = _envf("CHRONO_PHI_DEAD", 16.0)
XP_RATE_CAP  = _envf("CHRONO_XP_RATE_CAP", 50.0)   # TINV-6 سقفِ سخت‌افزاری
WEAR_BASE    = _envf("CHRONO_WEAR_BASE", 1.0)      # قیدِ متابولیک §10
# verdict آری 2026-07-08 «age_tick ضربان‌محور»: هر این‌قدر beat، یک بار فلشِ میرا را
# روی ledger ژنوم +۱ می‌بریم (heart-driven). پیش‌فرض ۱۴۴۰ (با beatِ ~۶۰s ≈ روزانه؛
# verdict آری جلسه ۳۲) تا زنجیرهٔ گران‌بها متورم نشود؛ N=۱ = هر ضربان، N بزرگ‌تر = کندتر.
AGE_PER_N_BEATS = int(_envf("CHRONO_AGE_PER_N_BEATS", 1440.0))
# OCT-DB-05: نگه‌داریِ چرخشیِ جدول‌های per-beat. 0 = خاموش (پیش‌فرض، رفتارِ قبلی).
# >0 = فقط N ضربانِ اخیر می‌ماند. خواننده‌ها امن: heartbeat فقط MAX(beat_seq) + پنجرهٔ
# ۲۴h؛ experience_meter/checkpoint خوانندهٔ prod ندارند. اخطار: N باید >۲۴h (beat~۶۰s → N>1440).
RETAIN_BEATS = int(_envf("CHRONO_RETAIN_BEATS", 0.0))

GENESIS_HLC = (0, 0)


def _utc_ms() -> int:
    return int(time.time() * 1000)


# ─── HLC — الگوریتمِ CockroachDB pkg/util/hlc (~۲۰ خط، DOC-B §9) ────────────────
def hlc_tick(hlc: tuple[int, int], pt_ms: int) -> tuple[int, int]:
    """رویدادِ محلی/ارسال: l=max(l,pt)؛ اگر l ثابت ماند c+=1 وگرنه c=0 (TINV-1)."""
    l, c = hlc
    l2 = max(l, pt_ms)
    return (l2, c + 1) if l2 == l else (l2, 0)


def hlc_merge(local: tuple[int, int], remote: tuple[int, int],
              pt_ms: int) -> tuple[int, int]:
    """قاعدهٔ receive: همگرایی به بزرگ‌ترین ساعت، بدون شکستِ علیّت."""
    l, c = local
    ml, mc = remote
    l2 = max(l, ml, pt_ms)
    if l2 == l and l2 == ml:
        return (l2, max(c, mc) + 1)
    if l2 == l:
        return (l2, c + 1)
    if l2 == ml:
        return (l2, mc + 1)
    return (l2, 0)


def hlc_max(hlcs: Iterable[tuple[int, int]]) -> tuple[int, int]:
    """«اکنونِ مشترک» = max (barrier همگام‌سازی، DOC-B §9 قدم ۲)."""
    out = GENESIS_HLC
    for h in hlcs:
        if tuple(h) > out:
            out = tuple(h)
    return out


# ─── phi-accrual (Hayashibara، تقریبِ نرمال) — TINV-4 / SWIM suspected ───────────
class PhiAccrual:
    """تاریخچهٔ فاصلهٔ رسیدنِ ackها → phi = -log10(P_later). بالاتر = مشکوک‌تر.
    پنجرهٔ گرمِ bootstrap: تا وقتی ۲ فاصله ثبت نشده phi=0 (پای نوزاد را نکش)."""

    def __init__(self, window: int = 20):
        self.arrivals: deque[float] = deque(maxlen=window)

    def heard(self, t_ms: int) -> None:
        self.arrivals.append(float(t_ms))

    def phi(self, now_ms: int) -> float:
        if len(self.arrivals) < 2:
            return 0.0
        xs = list(self.arrivals)
        gaps = [b - a for a, b in zip(xs, xs[1:])]
        mean = sum(gaps) / len(gaps)
        var = sum((g - mean) ** 2 for g in gaps) / len(gaps)
        std = max(math.sqrt(var), 0.1 * mean, 1.0)
        t = now_ms - xs[-1]
        p_later = 0.5 * math.erfc((t - mean) / (std * math.sqrt(2.0)))
        p_later = max(p_later, 1e-300)  # کف: phi محدود، نه inf
        return -math.log10(p_later)


# ─── ChronoDB — جدول‌های DataSchemas.sql (SQLite/WAL؛ تک-writer در سدِ ضربان) ────
_DDL = """
CREATE TABLE IF NOT EXISTS heartbeat (
  beat_seq      INTEGER PRIMARY KEY,
  wall_ts       INTEGER NOT NULL,
  hlc_phys      INTEGER NOT NULL,
  hlc_logical   INTEGER NOT NULL,
  present_legs  TEXT NOT NULL,
  absent_legs   TEXT NOT NULL,
  workspace_ref TEXT,
  ts            INTEGER NOT NULL
);
DROP INDEX IF EXISTS idx_heartbeat_ts;  -- OCT-DB-03: dead index (readers use beat_seq PK / full-scan wall_ts), drop to skip ~1440 index writes/day

CREATE TABLE IF NOT EXISTS leg_clock (
  leg_id          TEXT PRIMARY KEY,
  hlc_phys        INTEGER NOT NULL,
  hlc_logical     INTEGER NOT NULL,
  last_ack_beat   INTEGER NOT NULL,
  vitality_phi    REAL NOT NULL DEFAULT 0.0,
  experience_rate REAL NOT NULL DEFAULT 0.0,
  state           TEXT NOT NULL DEFAULT 'alive'
                  CHECK (state IN ('alive','suspected','failed')),
  updated_at      INTEGER NOT NULL
);

-- LANGAR: جدولِ رقیب عمداً ساخته نمی‌شود (قانونِ «extend, don't rival» —
-- DataSchemas.sql سرصفحه). LANGAR = ledger ژنومِ گسترش‌یافته (ledger.py v0.4.5).

CREATE TABLE IF NOT EXISTS experience_meter (
  leg_id        TEXT NOT NULL,
  beat_seq      INTEGER NOT NULL,
  events_count  INTEGER NOT NULL,
  dt_wall_ms    INTEGER NOT NULL,
  rate          REAL NOT NULL,
  PRIMARY KEY (leg_id, beat_seq)
);

CREATE TABLE IF NOT EXISTS duration_marker (
  event_id    TEXT PRIMARY KEY,
  hlc_phys    INTEGER NOT NULL,
  hlc_logical INTEGER NOT NULL,
  wall_ts     INTEGER NOT NULL,
  label       TEXT
);

CREATE TABLE IF NOT EXISTS anticipation_queue (
  id           INTEGER PRIMARY KEY,
  leg_id       TEXT,
  due_beat     INTEGER,
  kind         TEXT NOT NULL,
  task_ref     TEXT NOT NULL,
  created_beat INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_anticipation_due ON anticipation_queue(due_beat);

CREATE TABLE IF NOT EXISTS checkpoint (
  beat_id       INTEGER PRIMARY KEY,
  logical_clock TEXT NOT NULL,
  ledger_hash   TEXT NOT NULL,
  snapshot_ref  TEXT NOT NULL,
  metrics       TEXT
);

-- additive (خارج از DDL مرجع): تک‌گلوگاهِ TINV-7 نیاز به state ماندگار دارد.
CREATE TABLE IF NOT EXISTS gated_effect (
  effect_id   TEXT PRIMARY KEY,
  kind        TEXT NOT NULL,
  payload_ref TEXT NOT NULL,
  created_beat INTEGER,
  created_ts  INTEGER NOT NULL,
  release_ref TEXT,
  status      TEXT NOT NULL DEFAULT 'pending'
              CHECK (status IN ('pending','releasable','settled','refused'))
);

-- additive (verdict آری 2026-07-08 «پیری heart-driven هم»): فرسایشِ متابولیکِ
-- ضربان‌محور — جدا از age_tick (دو-ساعت). ردیفِ '_organism' = سطحِ کلِ بدن.
CREATE TABLE IF NOT EXISTS metabolic_age (
  leg_id       TEXT PRIMARY KEY,
  wear         REAL NOT NULL DEFAULT 0.0,
  updated_beat INTEGER NOT NULL
);

-- OCT-DB-06: baselineِ نسخهٔ اسکیمای chrono.db (فعلاً ۱). idempotent؛ هر ساختِ ChronoDB
-- این را ست می‌کند. مهاجرت‌های بعدی این عدد را بالا می‌برند و کد با `PRAGMA user_version`
-- می‌تواند تصمیم بگیرد.
PRAGMA user_version = 1;
"""


class ChronoDB:
    def __init__(self, path: pathlib.Path | str | None = None):
        self.path = pathlib.Path(path) if path else (opslib.STATE_DIR / "chrono.db")
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self._con = sqlite3.connect(str(self.path), check_same_thread=False)
        self._con.execute("PRAGMA journal_mode=WAL")
        self._con.executescript(_DDL)
        self._con.commit()

    def ex(self, sql: str, args: tuple = ()) -> sqlite3.Cursor:
        with self._lock:
            cur = self._con.execute(sql, args)
            self._con.commit()
            return cur

    def q(self, sql: str, args: tuple = ()) -> list[tuple]:
        with self._lock:
            return self._con.execute(sql, args).fetchall()

    def last_beat_seq(self) -> int:
        row = self.q("SELECT MAX(beat_seq) FROM heartbeat")
        return int(row[0][0] or 0)

    def close(self) -> None:
        with self._lock:
            self._con.close()


# ─── پا (Leg) — فقط HLC محلی + آخرین beat؛ هیچ ساعتِ دیواری (TINV-5) ────────────
class LegHandle:
    """آنچه یک پا می‌بیند. مهرِ HLC را بستر می‌زند (پا زمانِ فیزیکی نمی‌خواند)؛
    رویدادها فقط در حافظه بافر می‌شوند و در سدِ ضربان به دیسک می‌روند."""

    def __init__(self, leg_id: str, bus: "ChronoBus"):
        self.id = leg_id
        self._bus = bus
        self.hlc: tuple[int, int] = GENESIS_HLC
        self.last_beat_seen: int = 0
        self.events_this_beat: int = 0
        self.state: str = "alive"
        self.inbox: deque[dict] = deque(maxlen=int(os.environ.get("CHRONO_INBOX_MAXLEN", "1024")))

    def event(self, payload_ref: str | None = None) -> tuple[int, int]:
        """کارِ تخصصیِ پا یک رویداد تولید کرد → HLC محلی +1 و ack حیات."""
        return self._bus._leg_event(self, payload_ref)

    def _on_broadcast(self, msg: dict) -> None:
        self.hlc = self._bus._merge_for(self, msg["hlc"])
        self.last_beat_seen = msg["beat"]
        self.inbox.append(msg)


class ChronoBus:
    """عصب‌کشی: ثبتِ پاها، ackها، broadcastِ «اکنونِ مشترک» (GWT). تنها جایی که
    ساعتِ دیواری برای مهرزنی خوانده می‌شود — پاها نه (TINV-5). clock تزریق‌پذیر
    است تا تست بدونِ sleep زمان را جلو ببرد."""

    def __init__(self, clock: Callable[[], int] = _utc_ms):
        self._clock = clock
        self._lk = threading.Lock()
        self.legs: dict[str, LegHandle] = {}
        self.phi: dict[str, PhiAccrual] = {}
        self._acks: dict[str, tuple[int, int]] = {}
        self.subscribers: list[Callable[[dict], None]] = []

    def register_leg(self, leg_id: str) -> LegHandle:
        with self._lk:
            if leg_id not in self.legs:
                self.legs[leg_id] = LegHandle(leg_id, self)
                self.phi[leg_id] = PhiAccrual()
                self.phi[leg_id].heard(self._clock())  # تولد = اولین نشانِ حیات
            return self.legs[leg_id]

    def _leg_event(self, leg: LegHandle, payload_ref: str | None) -> tuple[int, int]:
        with self._lk:
            leg.hlc = hlc_tick(leg.hlc, self._clock())   # TINV-1
            leg.events_this_beat += 1
            self._acks[leg.id] = leg.hlc                 # نشانِ حیات
            self.phi[leg.id].heard(self._clock())
            return leg.hlc

    def _merge_for(self, leg: LegHandle, remote: tuple[int, int]) -> tuple[int, int]:
        with self._lk:
            return hlc_merge(leg.hlc, tuple(remote), self._clock())

    def ack(self, leg_id: str) -> None:
        """ack صریح (پاسخِ broadcast) — پای بیکار ولی زنده."""
        with self._lk:
            leg = self.legs[leg_id]
            self._acks[leg_id] = leg.hlc
            self.phi[leg_id].heard(self._clock())

    def collect_acks(self) -> dict[str, tuple[int, int]]:
        with self._lk:
            out, self._acks = self._acks, {}
            return out

    def broadcast(self, msg: dict) -> None:
        for leg in list(self.legs.values()):
            leg._on_broadcast(msg)
        for fn in list(self.subscribers):
            try:
                fn(msg)
            except Exception as e:  # noqa: BLE001 — مشترکِ خراب ضربان را نمی‌کشد
                opslib.alert([f"chrono subscriber error: {type(e).__name__}: {e}"])


# ─── EffectorGate — تک‌گلوگاهِ TINV-7 (HeartDesign invariant 5؛ kill supreme 7) ──
class GateClosed(Exception):
    pass


class EffectorGate:
    """هیچ send/publish/sync/pay بدونِ appendِ قبلی به LANGAR settle نمی‌شود.
    kill-switch (STOP/FREEZE) گیت را بدونِ قیدوشرط force-close می‌کند."""

    def __init__(self, db: ChronoDB, ledger=None):
        self.db = db
        self._ledger = ledger

    def _note(self, subtype: str, payload: dict) -> None:
        try:
            opslib.ledger_note(subtype, payload, actor="effector-gate")
        except Exception:  # noqa: BLE001 — ثبتِ ناظر fail-soft است
            pass

    def force_closed(self) -> str | None:
        """دلیلِ بسته‌بودنِ بی‌قیدوشرط، یا None. kill از همه‌چیز ارشدتر است."""
        reason = opslib.halted()
        if reason:
            return reason
        if opslib.STOP_ORGANISM.exists():
            return "STOP-ORGANISM"
        if opslib.frozen():
            return "FREEZE (I3 fail-closed)"
        return None

    def request(self, kind: str, payload_ref: str, beat: int | None = None) -> str:
        """ثبتِ نیتِ اثرِ برگشت‌ناپذیر → pending (هنوز هیچ اثری در جهان نیست)."""
        import uuid
        eid = uuid.uuid4().hex[:16]
        self.db.ex("INSERT INTO gated_effect(effect_id,kind,payload_ref,created_beat,"
                   "created_ts,status) VALUES (?,?,?,?,?, 'pending')",
                   (eid, kind, payload_ref, beat, _utc_ms()))
        self._note("EFFECT_REQUEST", {"effect_id": eid, "kind": kind,
                                      "payload_ref": payload_ref})
        return eid

    def release_gated_effects(self, entry: dict) -> int:
        """پس از human-append (DOC-B §9 `on_human_judgment`): هر pendingِ موجود
        مجازِ settle می‌شود؛ release_ref = hash همان append (ردِ audit)."""
        ref = entry.get("hash", "")
        cur = self.db.ex("UPDATE gated_effect SET status='releasable', release_ref=? "
                         "WHERE status='pending'", (ref,))
        return cur.rowcount

    def status_of(self, effect_id: str) -> str | None:
        """وضعیتِ authoritative یک effect را فقط‌خواندنی برمی‌گرداند.
        pending | releasable | settled | refused | None (ناموجود).
        خواندن، نه نوشتن — کاربرد: نمایِ فقط‌خواندنیِ صفِ تأیید (مانند cockpit)
        تا هرگز با gate واگرا نشود. هیچ اثرِ جانبی."""
        row = self.db.q("SELECT status FROM gated_effect WHERE effect_id=?",
                        (effect_id,))
        return row[0][0] if row else None

    def settle(self, effect_id: str) -> bool:
        """تنها نقطهٔ عبورِ اثر به جهان. False = مجاز نیست (fail-closed)."""
        kill = self.force_closed()
        if kill:
            self.db.ex("UPDATE gated_effect SET status='refused' WHERE effect_id=? "
                       "AND status IN ('pending','releasable')", (effect_id,))
            self._note("EFFECT_REFUSED", {"effect_id": effect_id, "reason": kill})
            return False
        row = self.db.q("SELECT status, release_ref FROM gated_effect "
                        "WHERE effect_id=?", (effect_id,))
        if not row or row[0][0] != "releasable" or not row[0][1]:
            self._note("EFFECT_REFUSED", {"effect_id": effect_id,
                                          "reason": "no matching LANGAR append (TINV-7)"})
            return False
        self.db.ex("UPDATE gated_effect SET status='settled' WHERE effect_id=?",
                   (effect_id,))
        self._note("EFFECT_SETTLED", {"effect_id": effect_id, "release_ref": row[0][1]})
        return True

    def sweep_stale_effects(self, max_age_hours: int = 72) -> dict:
        """gated_effectهایی که بیش از max_age_hours pending هستند → auto-refuse.
        max_age_hours=0 → sweep خاموش (rollback knob).
        هر epoch از governor_epoch.run_epoch() صدا زده می‌شود."""
        if max_age_hours <= 0:
            return {"refused": 0, "ids": []}
        cutoff_ms = _utc_ms() - (max_age_hours * 3600_000)
        rows = self.db.q(
            "SELECT effect_id FROM gated_effect WHERE status='pending' AND created_ts < ?",
            (cutoff_ms,))
        refused = []
        for (eid,) in rows:
            self.db.ex("UPDATE gated_effect SET status='refused' WHERE effect_id=?", (eid,))
            refused.append(eid)
        if refused:
            self._note("EFFECT_SWEEP", {"refused_count": len(refused), "ids": refused})
        return {"refused": len(refused), "ids": refused}


# ─── LANGAR — فلشِ میرا (P-Chrono-4؛ ledger ژنوم v0.4.5 گسترش‌یافته) ─────────────
def on_human_judgment(judgment: dict, gate: EffectorGate | None = None,
                      event_type: str = "APPROVAL", ledger=None,
                      ha_token: str | None = None) -> dict:
    """DOC-B §9: تنها قضاوتِ انسانی فلش را می‌برد (age_tick=last+1 داخلِ ledger،
    اتمیک زیرِ قفلِ append) → سپس اثرهای منتظرِ گیت آزاد می‌شوند (TINV-7).

    جلسه ۴۶ (رفعِ P0/E16): گاردِ human-append. فقط تلگرام (که رازِ mint را دارد) می‌تواند
    توکنِ معتبر بسازد؛ بی‌توکن یا توکنِ جعلی → `is_human` به 0 downgrade می‌شود تا age_tickِ
    میرا با یک append جعلی جلو نرود. مسیرِ settle/release دست‌نخورده (گیتِ پول جداست).
    flag-gated + fail-safe: پرچمِ خاموش یا گاردِ پیکربندی‌نشده → رفتارِ قبلی."""
    lg = ledger or opslib.genome_ledger()
    is_human = True
    if os.environ.get("OCTOPUS_WIRE_HUMAN_APPEND_GUARD") == "1":
        try:
            _bp = str(_HERE / "budget")
            if _bp not in sys.path:
                sys.path.insert(0, _bp)
            from human_append_guard import default_guard
            _raw = judgment.get("effect_id") if isinstance(judgment, dict) else None
            _aid = str(_raw).replace(".", "-") if _raw is not None else None  # هم‌راستا با mint
            allow, reason = default_guard().authorize(event_type, True,
                                                      token=ha_token, approval_id=_aid)
            if not allow and reason != "guard-disabled-passthrough":
                is_human = False
                opslib.alert([f"human-append guard: is_human downgraded ({reason}) "
                              f"— append بدونِ توکنِ معتبر (ضدِ جعلِ E16)"])
        except Exception:  # noqa: BLE001 — fail-safe: خطای گارد → رفتارِ قبلی
            pass
    entry = lg.append(event_type, judgment,
                      actor="human" if is_human else "system", is_human=is_human)
    if gate is not None:
        gate.release_gated_effects(entry)
    return entry


def last_age_tick(ledger=None) -> int:
    lg = ledger or opslib.genome_ledger()
    return lg.last_age_tick()


# ─── Pacemaker — حلقهٔ ضربان (DOC-B §9؛ scheduler=F19 همین‌جاست) ────────────────
class Pacemaker:
    """مغزِ مرکزی + Chrono Bus. `beat_once()` یک ضربانِ کامل و تست‌پذیر است
    (بدونِ sleep)؛ `run_forever()` همان را با PERIOD تکرار می‌کند."""

    def __init__(self, db: ChronoDB | None = None, bus: ChronoBus | None = None,
                 period_s: float = PERIOD_S,
                 clock: Callable[[], int] = _utc_ms,
                 dispatcher: Optional[Callable[[dict], None]] = None,
                 doctor: Any = None, ledger=None,
                 age_per_n_beats: int | None = None):
        self.db = db or ChronoDB()
        self.bus = bus or ChronoBus(clock)
        self.period_s = period_s
        self._clock = clock
        self.dispatcher = dispatcher          # F19: followup/escalate بعداً وصل می‌شود
        self.doctor = doctor                  # Phase 2: restart_from_known_good
        self._ledger = ledger
        self.age_per_n_beats = int(age_per_n_beats if age_per_n_beats is not None
                                   else AGE_PER_N_BEATS)   # v0.4.6 heart-driven age
        self.beat = self.db.last_beat_seq()   # ادامه از آخرین نبض (پیوستگی)
        self.hlc: tuple[int, int] = GENESIS_HLC
        row = self.db.q("SELECT wall_ts FROM heartbeat WHERE beat_seq=?", (self.beat,))
        self._last_beat_wall: int | None = int(row[0][0]) if row else None
        self.dispatched: list[dict] = []      # مشاهده‌پذیریِ تست/دیباگ

    # -- P-Chrono-6: زمان‌بندی بر حسبِ نبض، نه ساعتِ دیواری --------------------
    def schedule(self, kind: str, task_ref: str, due_beat: int | None = None,
                 in_beats: int | None = None, leg_id: str | None = None) -> int:
        if due_beat is None:
            due_beat = self.beat + int(in_beats or 1)
        cur = self.db.ex("INSERT INTO anticipation_queue(leg_id,due_beat,kind,task_ref,"
                         "created_beat) VALUES (?,?,?,?,?)",
                         (leg_id, due_beat, kind, task_ref, self.beat))
        return int(cur.lastrowid)

    def mark_duration(self, event_id: str, label: str = "") -> None:
        self.db.ex("INSERT OR REPLACE INTO duration_marker(event_id,hlc_phys,"
                   "hlc_logical,wall_ts,label) VALUES (?,?,?,?,?)",
                   (event_id, self.hlc[0], self.hlc[1], self._clock(), label))

    def duration_since(self, event_id: str) -> tuple[int, int] | None:
        """حسِ مدت (ویژگی ۱): duration = now_hlc − event_hlc (+Δwall برای انسان)."""
        row = self.db.q("SELECT hlc_phys, wall_ts FROM duration_marker "
                        "WHERE event_id=?", (event_id,))
        if not row:
            return None
        return (self.hlc[0] - row[0][0], self._clock() - row[0][1])

    # -- سدِ ضربان — تنها writer دیسک (DOC-B §12) --------------------------------
    def beat_once(self) -> dict:
        t0 = self._clock()
        self.beat += 1
        dt_ms = (t0 - self._last_beat_wall) if self._last_beat_wall else int(self.period_s * 1000)
        dt_ms = max(int(dt_ms), 1)
        self._last_beat_wall = t0

        # 1) جمعِ ackها + phi-accrual → alive/suspected/failed (TINV-4)
        acks = self.bus.collect_acks()
        present, absent = [], []
        for leg in self.bus.legs.values():
            phi = self.bus.phi[leg.id].phi(t0)
            new_state = ("alive" if phi < PHI_SUSPECT else
                         "suspected" if phi < PHI_DEAD else "failed")
            was = leg.state
            leg.state = new_state
            (present if new_state == "alive" else absent).append(leg.id)
            if new_state == "failed" and was != "failed" and self.doctor is not None:
                # B5: self-heal پشتِ flag + circuit-breaker (ضدِ restart-storm)
                import os as _os
                if _os.environ.get("OCTOPUS_WIRE_SELFHEAL") == "1":
                    import time as _time
                    now_s = _time.time()
                    window = 300   # ۵ دقیقه
                    max_restarts = 3   # حداکثر ۳ restart در ۵ دقیقه
                    recent = [t for t in getattr(self, "_restart_log", []) if now_s - t < window]
                    if len(recent) < max_restarts:
                        recent.append(now_s)
                        self._restart_log = recent
                        try:  # Phase 2 قلاب: OTP-style restart از حالتِ known-good لجر
                            self.doctor.restart_from_known_good(leg, self.db)
                            # جلسه ۴۶: لاگِ بی‌محتوا برای خانهٔ ساده («خودم درستش کردم»)
                            try:
                                import time as _t2
                                with open(opslib.STATE_DIR / "selfheal-events.jsonl",
                                          "a", encoding="utf-8") as _hf:
                                    _hf.write(json.dumps({"leg": getattr(leg, "id", "?"),
                                                          "ts": _t2.time()}) + "\n")
                            except OSError:
                                pass
                            # جلسه ۴۶: رویدادِ ساختاریافته برای داشبورد (blocked→completed)
                            try:
                                _sp = str(_HERE)
                                if _sp not in sys.path:
                                    sys.path.insert(0, _sp)
                                import events as _ev
                                _lg = getattr(leg, "id", "?")
                                _ev.emit("task.blocked", f"leg/{_lg}",
                                         summary=f"عضو «{_lg}» از کار افتاد", status="failed")
                                _ev.emit("task.completed", "self-heal",
                                         summary=f"عضو «{_lg}» را خودم دوباره راه انداختم")
                            except Exception:  # noqa: BLE001
                                pass
                        except Exception as e:  # noqa: BLE001
                            opslib.alert([f"doctor restart hook failed ({leg.id}): {e}"])
                    else:
                        opslib.alert([f"self-heal circuit-breaker: {len(recent)} restarts "
                                      f"in {window}s — throttled ({leg.id})"])

        # 2) «اکنونِ مشترک» = max HLCهای پاهای غیرمرده + تیکِ خودِ pacemaker
        self.hlc = hlc_tick(hlc_max([leg.hlc for leg in self.bus.legs.values()
                                     if leg.state != "failed"] + [self.hlc]), t0)

        # 3) BROADCAST (GWT): پاها فقط beat + hlc می‌بینند (TINV-5)
        msg = {"beat": self.beat, "hlc": self.hlc, "present": present}
        counts = {leg.id: leg.events_this_beat for leg in self.bus.legs.values()}
        for leg in self.bus.legs.values():
            leg.events_this_beat = 0
        self.bus.broadcast(msg)

        # 4) experience_meter + قیدِ متابولیک (TINV-6؛ نوشتن فقط این‌جا = سدِ writer)
        for leg_id, n in counts.items():
            rate = max(0.0, min(XP_RATE_CAP, n / (dt_ms / 1000.0)))
            self.db.ex("INSERT OR REPLACE INTO experience_meter(leg_id,beat_seq,"
                       "events_count,dt_wall_ms,rate) VALUES (?,?,?,?,?)",
                       (leg_id, self.beat, n, dt_ms, rate))
            leg = self.bus.legs[leg_id]
            self.db.ex("INSERT OR REPLACE INTO leg_clock(leg_id,hlc_phys,hlc_logical,"
                       "last_ack_beat,vitality_phi,experience_rate,state,updated_at) "
                       "VALUES (?,?,?,?,?,?,?,?)",
                       (leg_id, leg.hlc[0], leg.hlc[1],
                        self.beat if leg_id in acks else leg.last_beat_seen,
                        self.bus.phi[leg_id].phi(t0), rate, leg.state, t0))
            # پیریِ متابولیک (verdict heart-driven): پرمشغله‌تر = فرسوده‌تر؛ هرگز age_tick
            wear_inc = WEAR_BASE * (1.0 + rate / XP_RATE_CAP)
            self.db.ex("INSERT INTO metabolic_age(leg_id,wear,updated_beat) "
                       "VALUES (?,?,?) ON CONFLICT(leg_id) DO UPDATE SET "
                       "wear=wear+excluded.wear, updated_beat=excluded.updated_beat",
                       (leg_id, wear_inc, self.beat))
        self.db.ex("INSERT INTO metabolic_age(leg_id,wear,updated_beat) VALUES "
                   "('_organism',?,?) ON CONFLICT(leg_id) DO UPDATE SET "
                   "wear=wear+excluded.wear, updated_beat=excluded.updated_beat",
                   (WEAR_BASE, self.beat))

        # 5) scheduler (F19): سررسید بر حسبِ نبض — هرگز ساعتِ دیواری
        due = self.db.q("SELECT id,leg_id,due_beat,kind,task_ref FROM anticipation_queue "
                        "WHERE due_beat<=? ORDER BY due_beat,id", (self.beat,))
        for (aid, leg_id, due_beat, kind, task_ref) in due:
            task = {"id": aid, "leg_id": leg_id, "due_beat": due_beat,
                    "kind": kind, "task_ref": task_ref, "fired_beat": self.beat}
            self.dispatched.append(task)
            if self.dispatcher:
                try:
                    self.dispatcher(task)
                except Exception as e:  # noqa: BLE001
                    opslib.alert([f"chrono dispatcher error ({task_ref}): {e}"])
            self.db.ex("DELETE FROM anticipation_queue WHERE id=?", (aid,))

        # 6) ردیفِ heartbeat + checkpoint سبک (L13؛ نه verifyِ کامل — F14)
        self.db.ex("INSERT INTO heartbeat(beat_seq,wall_ts,hlc_phys,hlc_logical,"
                   "present_legs,absent_legs,workspace_ref,ts) VALUES (?,?,?,?,?,?,?,?)",
                   (self.beat, t0, self.hlc[0], self.hlc[1],
                    json.dumps(present), json.dumps(absent), None, t0))
        try:
            lhash = (self._ledger or opslib.genome_ledger()).last_hash()
        except Exception:  # noqa: BLE001 — checkpoint سبک نباید ضربان را بکشد
            lhash = ""
        snapshot = {leg.id: {"hlc": list(leg.hlc), "state": leg.state}
                    for leg in self.bus.legs.values()}
        self.db.ex("INSERT OR REPLACE INTO checkpoint(beat_id,logical_clock,"
                   "ledger_hash,snapshot_ref,metrics) VALUES (?,?,?,?,?)",
                   (self.beat, json.dumps(list(self.hlc)), lhash,
                    json.dumps(snapshot, ensure_ascii=False),
                    json.dumps({"dt_ms": dt_ms, "due_fired": len(due)})))

        # 7) فلشِ میرا، ضربان‌محور (verdict آری 2026-07-08): هر AGE_PER_N_BEATS ضربان
        # یک appendِ HEARTBEAT با beat=True روی ledger ژنوم می‌زند → age_tick +۱ (تنها
        # جای حرکتِ ماشینیِ فلش؛ human هم جدا فلش را می‌برد). fail-soft: خطا ضربان را نمی‌کشد.
        if self.age_per_n_beats > 0 and self.beat % self.age_per_n_beats == 0:
            try:
                (self._ledger or opslib.genome_ledger()).append(
                    "HEARTBEAT", {"beat": self.beat, "hlc": list(self.hlc)},
                    actor="pacemaker", beat=True)
            except Exception as e:  # noqa: BLE001 — فلشِ میرا نباید سدِ ضربان را بکشد
                opslib.alert([f"chrono age-tick append failed (beat {self.beat}): {e}"])

        # 8) OCT-DB-05: prune چرخشیِ جدول‌های per-beat (flag-gated، پیش‌فرض خاموش). فقط
        # beatهای قدیمی‌تر از پنجرهٔ نگه‌داری؛ newest (=self.beat) هرگز حذف نمی‌شود چون
        # self.beat > RETAIN_BEATS تضمین می‌کند cutoff < self.beat. metabolic_age/leg_clock
        # و gated_effect عمداً دست‌نخورده‌اند. fail-soft: خطا سدِ ضربان را نمی‌کشد.
        if RETAIN_BEATS > 0 and self.beat > RETAIN_BEATS:
            cutoff = self.beat - RETAIN_BEATS
            try:
                self.db.ex("DELETE FROM heartbeat WHERE beat_seq < ?", (cutoff,))
                self.db.ex("DELETE FROM experience_meter WHERE beat_seq < ?", (cutoff,))
                self.db.ex("DELETE FROM checkpoint WHERE beat_id < ?", (cutoff,))
            except Exception as e:  # noqa: BLE001 — prune نباید سدِ ضربان را بکشد
                opslib.alert([f"chrono retention prune failed (beat {self.beat}): {e}"])
        return msg

    def status(self) -> dict:
        """snapshot ماشین‌خوان برای ORGANISM-STATE/UI (فقط‌خواندنی، fail-soft)."""
        wear = {r[0]: r[1] for r in self.db.q("SELECT leg_id,wear FROM metabolic_age")}
        try:
            age = last_age_tick(self._ledger)
        except Exception:  # noqa: BLE001
            age = None
        return {"beat": self.beat, "hlc": list(self.hlc),
                "legs": {l.id: l.state for l in self.bus.legs.values()},
                "metabolic_age": wear.get("_organism", 0.0),
                "age_tick": age,
                "effects_pending": self.db.q(
                    "SELECT COUNT(*) FROM gated_effect WHERE status='pending'")[0][0]}

    def run_forever(self) -> None:
        """حلقهٔ پس‌زمینه برای organism.py — تسلیمِ بی‌قیدوشرط به STOP (kill supreme)."""
        while True:
            if opslib.STOP_ORGANISM.exists() or opslib.halted():
                return
            try:
                self.beat_once()
            except Exception as e:  # noqa: BLE001 — خطای خاموش ممنوع (منشور §۴)
                opslib.alert([f"chrono beat error: {type(e).__name__}: {e}"])
            time.sleep(self.period_s)


# ─── سوارشدن روی organism.py (P-Chrono-1، additive) ─────────────────────────────
_default: Pacemaker | None = None


def start_pacemaker_thread(period_s: float | None = None,
                           doctor=None, dispatcher=None) -> Pacemaker:
    """pacemaker پیش‌فرض به‌عنوان background task (daemon).
    B5: doctor برای restart_from_known_good (self-heal پشتِ flag).
    B6: dispatcher برای F19 scheduler (پشتِ flag).
    fail-soft: شکستِ chrono نباید متابولیسمِ موجود را بکشد — تماس‌گیرنده try می‌کند."""
    global _default
    if _default is None:
        _default = Pacemaker(period_s=period_s or PERIOD_S,
                             doctor=doctor, dispatcher=dispatcher)
        threading.Thread(target=_default.run_forever, daemon=True,
                         name="chrono-pacemaker").start()
        opslib.heartbeat(f"chrono=START period={_default.period_s:.0f}s "
                         f"beat={_default.beat}")
    return _default


def status() -> dict | None:
    return _default.status() if _default else None
