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

-- OCT-DB-06 / C1 (2026-07-22): نسخهٔ اسکیمای chrono.db توسطِ ChronoDB._migrate اداره
-- می‌شود، نه با یک `PRAGMA user_version = N` داخلِ این DDL. گذاشتنِ PRAGMA اینجا هر
-- ساختِ ChronoDB نسخه را reset می‌کرد و guardِ مهاجرت را می‌شکست (C-A، critical).
"""


CHRONO_SCHEMA_TARGET = 4   # C1: framework · C2: binding columns · C3: unique idempotency index · C5: execution CAS
# canonical v1 column set of gated_effect — used to disambiguate a user_version=0
# database into {empty | legacy-unversioned-v1 | malformed}.
_GATED_EFFECT_V1_COLS = frozenset({
    "effect_id", "kind", "payload_ref", "created_beat",
    "created_ts", "release_ref", "status"})


class ChronoSchemaError(RuntimeError):
    """chrono.db schema is inconsistent — fail-closed. Never auto-downgrade,
    never silently proceed on a malformed or unknown-version DB."""


class IdempotencyConflict(RuntimeError):
    """Same idempotency_key requested with a different canonical effect
    (kind/action/target/content) — fail-closed, never a second row."""


class ChronoDB:
    def __init__(self, path: pathlib.Path | str | None = None):
        self.path = pathlib.Path(path) if path else (opslib.STATE_DIR / "chrono.db")
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self._con = sqlite3.connect(str(self.path), check_same_thread=False)
        self._con.execute("PRAGMA journal_mode=WAL")
        self._con.executescript(_DDL)     # CREATE TABLE IF NOT EXISTS ... (idempotent)
        self._con.commit()
        try:
            self._migrate()                # explicit, transactional, fail-closed
        except Exception:
            self._con.close()              # never leave a locked connection on a bad schema
            raise

    # ── C1: schema migration framework ──────────────────────────────────────
    def _gated_effect_cols(self) -> frozenset | None:
        rows = self._con.execute("PRAGMA table_info(gated_effect)").fetchall()
        return frozenset(r[1] for r in rows) if rows else None

    def _migrate(self) -> None:
        """Bring chrono.db to CHRONO_SCHEMA_TARGET. Fail-closed on downgrade or a
        malformed DB; a user_version=0 DB is disambiguated (not assumed) into
        empty / legacy-unversioned-v1 (both -> v1) or malformed (-> error)."""
        con = self._con
        ver = con.execute("PRAGMA user_version").fetchone()[0]
        if ver > CHRONO_SCHEMA_TARGET:
            raise ChronoSchemaError(
                f"chrono.db user_version={ver} > target {CHRONO_SCHEMA_TARGET}: "
                "refusing to auto-downgrade (fail-closed)")
        if ver == 0:
            cols = self._gated_effect_cols()
            if cols is None:
                # _DDL ran before this (CREATE IF NOT EXISTS); a missing table => malformed.
                raise ChronoSchemaError("gated_effect missing after DDL — malformed chrono.db")
            if cols != _GATED_EFFECT_V1_COLS:
                raise ChronoSchemaError(
                    f"gated_effect columns {sorted(cols)} != v1 schema "
                    f"{sorted(_GATED_EFFECT_V1_COLS)} — malformed chrono.db")
            # fresh OR legacy-unversioned v1 (both are valid v1); stamp the version.
            ver = self._stamp_version(1)
        while ver < CHRONO_SCHEMA_TARGET:      # forward steps (C2 adds 1->2)
            ver = self._apply_step(ver, ver + 1)
        final = con.execute("PRAGMA user_version").fetchone()[0]
        if final != CHRONO_SCHEMA_TARGET:
            raise ChronoSchemaError(f"migration incomplete: {final} != {CHRONO_SCHEMA_TARGET}")

    def _stamp_version(self, v: int) -> int:
        self._con.execute(f"PRAGMA user_version = {int(v)}")   # int we control; not parameterizable
        self._con.commit()
        return int(v)

    def _apply_step(self, frm: int, to: int) -> int:
        """Apply exactly one version step ATOMICALLY: on any error the whole step
        rolls back and user_version is unchanged (no half-migrated schema)."""
        con = self._con
        con.execute("BEGIN IMMEDIATE")
        try:
            self._migrate_step(frm, to)
            con.execute(f"PRAGMA user_version = {int(to)}")
            con.commit()
        except Exception:
            con.rollback()
            raise
        return to

    def _migrate_step(self, frm: int, to: int) -> None:
        if (frm, to) == (1, 2):
            self._migrate_1_to_2()
            return
        if (frm, to) == (2, 3):
            self._migrate_2_to_3()
            return
        if (frm, to) == (3, 4):
            self._migrate_3_to_4()
            return
        # C1 baseline; C2 adds (1,2); C3 adds (2,3); C5 adds (3,4). Later slices add further steps.
        raise ChronoSchemaError(f"chrono: no migration path v{frm} -> v{to}")

    def _migrate_3_to_4(self) -> None:
        """C5: execution-CAS columns + statusهای EXECUTING/FAILED_SAFE/EXPIRED/
        RECONCILE_REQUIRED در CHECK. چون SQLite نمی‌تواند CHECK را ALTER کند، جدول
        rebuild می‌شود (الگوی C2). additive: هیچ ردیفِ موجودی status عوض نمی‌کند.
        هشدار: DROP TABLE ایندکسِ UNIQUEِ C3 را هم می‌بَرد — باید بازساخته شود
        وگرنه idempotencyِ DB-enforced بی‌صدا از بین می‌رود."""
        con = self._con
        con.execute("""CREATE TABLE gated_effect_v4 (
          effect_id    TEXT PRIMARY KEY,
          kind         TEXT NOT NULL,
          payload_ref  TEXT NOT NULL,
          created_beat INTEGER,
          created_ts   INTEGER NOT NULL,
          release_ref  TEXT,
          status       TEXT NOT NULL DEFAULT 'pending'
                       CHECK (status IN ('pending','releasable','settled','refused',
                                         'NEEDS_OWNER_REVIEW','LEGACY_UNBOUND',
                                         'EXECUTING','EXPIRED','FAILED_SAFE',
                                         'RECONCILE_REQUIRED')),
          content_hash    TEXT,
          action_kind     TEXT,
          target_ref      TEXT,
          idempotency_key TEXT,
          proposal_id     TEXT,
          mission_id      TEXT,
          approval_id     TEXT,
          approved_by     TEXT,
          approved_at     INTEGER,
          expires_at      INTEGER,
          execution_id          TEXT,
          execution_started_at  INTEGER,
          execution_finished_at INTEGER,
          execution_worker_ref  TEXT,
          external_receipt_ref  TEXT,
          failure_reason        TEXT
        )""")
        con.execute(
            "INSERT INTO gated_effect_v4 "
            "(effect_id,kind,payload_ref,created_beat,created_ts,release_ref,status,"
            "content_hash,action_kind,target_ref,idempotency_key,proposal_id,mission_id,"
            "approval_id,approved_by,approved_at,expires_at) "
            "SELECT effect_id,kind,payload_ref,created_beat,created_ts,release_ref,status,"
            "content_hash,action_kind,target_ref,idempotency_key,proposal_id,mission_id,"
            "approval_id,approved_by,approved_at,expires_at FROM gated_effect")
        con.execute("DROP TABLE gated_effect")
        con.execute("ALTER TABLE gated_effect_v4 RENAME TO gated_effect")
        con.execute("CREATE UNIQUE INDEX ux_gated_effect_idem "
                    "ON gated_effect(idempotency_key)")

    def _migrate_2_to_3(self) -> None:
        """C3: enforce idempotency at the DB layer — replace the non-unique index
        with a UNIQUE one so a race between two identical requests yields exactly
        one row (SQLite allows multiple NULL idempotency_key, so legacy rows are
        unaffected)."""
        con = self._con
        con.execute("DROP INDEX IF EXISTS ix_gated_effect_idem")
        con.execute("CREATE UNIQUE INDEX ux_gated_effect_idem "
                    "ON gated_effect(idempotency_key)")

    def _migrate_1_to_2(self) -> None:
        """C2: add per-effect authorization-binding columns + widen the status
        CHECK. Uses individual execute() (NOT executescript, which would COMMIT
        and break the enclosing BEGIN IMMEDIATE). Legacy pending rows carry no
        binding, so they become NEEDS_OWNER_REVIEW (never auto-authorizable)."""
        con = self._con
        con.execute("""CREATE TABLE gated_effect_v2 (
          effect_id    TEXT PRIMARY KEY,
          kind         TEXT NOT NULL,
          payload_ref  TEXT NOT NULL,
          created_beat INTEGER,
          created_ts   INTEGER NOT NULL,
          release_ref  TEXT,
          status       TEXT NOT NULL DEFAULT 'pending'
                       CHECK (status IN ('pending','releasable','settled','refused',
                                         'NEEDS_OWNER_REVIEW','LEGACY_UNBOUND')),
          content_hash    TEXT,
          action_kind     TEXT,
          target_ref      TEXT,
          idempotency_key TEXT,
          proposal_id     TEXT,
          mission_id      TEXT,
          approval_id     TEXT,
          approved_by     TEXT,
          approved_at     INTEGER,
          expires_at      INTEGER
        )""")
        con.execute(
            "INSERT INTO gated_effect_v2 "
            "(effect_id,kind,payload_ref,created_beat,created_ts,release_ref,status) "
            "SELECT effect_id,kind,payload_ref,created_beat,created_ts,release_ref,status "
            "FROM gated_effect")
        con.execute("DROP TABLE gated_effect")
        con.execute("ALTER TABLE gated_effect_v2 RENAME TO gated_effect")
        # any row still 'pending' at migration time has no per-effect binding →
        # it cannot be exactly-authorized later; quarantine for owner review.
        con.execute("UPDATE gated_effect SET status='NEEDS_OWNER_REVIEW' "
                    "WHERE status='pending' AND (content_hash IS NULL OR content_hash='')")
        con.execute("CREATE INDEX IF NOT EXISTS ix_gated_effect_idem "
                    "ON gated_effect(idempotency_key)")

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
# batch-release (release_gated_effects، یک human-append همهٔ pendingها را releasable می‌کند)
# فقط برای kindهای پول/داخلیِ شناخته‌شده مجاز است — **allowlist، نه denylist** (LEAD-SAFETY-C1،
# رأی مالک 2026-07-21؛ سخت‌شده پس از راستی‌آزماییِ متخاصم که نشان داد denylist با casing/whitespace/
# سینونیم دور می‌خورد). هر kindِ خارج از این مجموعه (ارسالِ به مشتری، ناشناخته، هجیِ نو) → fail-safe
# = فقط با release_one صریح. تطبیق case/whitespace-insensitive است (lower(trim(kind))).
# money kindِ نو؟ این‌جا اضافه کن (وگرنه batch-release نمی‌شود — که سمتِ امنِ خطاست).
# C4 (2026-07-23): "pay" (money/E4) از این allowlist حذف شد — پول هرگز batch نمی‌شود؛
# فقط از مسیرِ release_effect (per-effect: id + content_hash + action_kind + target_ref +
# approval_id تک‌مصرفه + expiry). یک approvalِ عمومی (بدونِ effect_id) صفر پول آزاد می‌کند.
_BATCH_RELEASE_KINDS = frozenset({"send", "publish", "sync"})
# money/E4 kinds — هرگز batch؛ فقط release_effect. تطبیق lower(trim(kind)).
_E4_MONEY_KINDS = frozenset({"pay"})
# مستندِ kindهای اثرگذار-بر-مشتری که باید per-effect (release_one) بروند (زیرمجموعهٔ «خارج از allowlist»).
_PER_EFFECT_KINDS = frozenset({"lead_outbound", "customer_send"})


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

    def request(self, kind: str, payload_ref: str, beat: int | None = None, *,
                idempotency_key: str | None = None, action_kind: str | None = None,
                target_ref: str | None = None, proposal_id: str | None = None,
                mission_id: str | None = None) -> str:
        """ثبتِ نیتِ اثرِ برگشت‌ناپذیر → pending. **idempotent** بر اساس idempotency_key
        (اگر داده نشود، از محتوای canonical مشتق می‌شود) — پس retry/crash یک کالر دقیقاً یک
        اثرِ منطقی می‌سازد، نه دو ردیف. content_hash/action_kind/target_ref برای binding
        دقیقِ authorization (C4) ثبت می‌شوند. race دو کالر با UNIQUE(idempotency_key)
        (C3، DB-enforced) به یک ردیف می‌رسد."""
        import hashlib
        import uuid
        ch = hashlib.sha256(str(payload_ref).encode("utf-8")).hexdigest()
        akind = action_kind if action_kind is not None else kind
        tref = target_ref or ""
        # key stays NULL when the caller gives none → preserves today's behavior
        # (two keyless requests = two distinct effects; SQLite lets many NULLs coexist
        # under the UNIQUE index). Dedup applies ONLY to an explicit idempotency_key.
        key = idempotency_key
        eid = uuid.uuid4().hex[:16]
        cur = self.db.ex(
            "INSERT OR IGNORE INTO gated_effect(effect_id,kind,payload_ref,created_beat,"
            "created_ts,status,content_hash,action_kind,target_ref,idempotency_key,"
            "proposal_id,mission_id) VALUES (?,?,?,?,?, 'pending', ?,?,?,?,?,?)",
            (eid, kind, payload_ref, beat, _utc_ms(), ch, akind, tref, key,
             proposal_id, mission_id))
        if cur.rowcount == 1:                       # fresh insert
            self._note("EFFECT_REQUEST", {"effect_id": eid, "kind": kind})
            return eid
        # idempotency_key already present → return the existing effect iff the
        # canonical request matches, else fail-closed (never a divergent second row).
        row = self.db.q("SELECT effect_id, content_hash, action_kind, target_ref, kind "
                        "FROM gated_effect WHERE idempotency_key=?", (key,))
        if not row:
            raise ChronoSchemaError("idempotent insert ignored but no row found")
        eid0, ch0, ak0, tr0, k0 = row[0]
        if (ch0, ak0 or "", tr0 or "", k0) == (ch, akind, tref, kind):
            return eid0
        raise IdempotencyConflict(
            f"idempotency_key already bound to a different effect (kind/target/content differ)")

    def release_gated_effects(self, entry: dict) -> int:
        """پس از human-append (DOC-B §9 `on_human_judgment`): هر pendingِ موجود
        مجازِ settle می‌شود؛ release_ref = hash همان append (ردِ audit).

        **قاعدهٔ allowlist (LEAD-SAFETY-C1):** فقط kindهای پول/داخلیِ شناخته‌شده
        (`_BATCH_RELEASE_KINDS`) با یک human-append batch-release می‌شوند. هر kindِ دیگر —
        ارسالِ به مشتری، ناشناخته، یا هجیِ غیرمتعارف — fail-safe فقط با `release_one` (صریح،
        یکی-یکی) آزاد می‌شود. تطبیق case/whitespace-insensitive: `lower(trim(kind))`.

        **C4:** money/E4 (`_E4_MONEY_KINDS`) هرگز از این مسیر آزاد نمی‌شود — یک approvalِ عمومی
        صفر پول release می‌کند؛ پول فقط از `release_effect`. هر پولِ pendingِ skip‌شده audit می‌شود.
        **D3:** زیرِ halt سراسری هیچ authorizationای — صفر release (دفاعِ عمقی؛ کالرِ بالادست
        هم halt-gated است ولی گیت خودش هم باید رد کند)."""
        kill = self.force_closed()
        if kill:
            self._note("EFFECT_REFUSED", {"reason": f"batch release under halt: {kill}"})
            return 0
        ref = entry.get("hash", "")
        # C4: پولِ pendingی که این approvalِ عمومی عمداً release نمی‌کند را auditable کن (نه سکوت).
        _mk = sorted(_E4_MONEY_KINDS)
        if _mk:
            _mph = ",".join("?" for _ in _mk)
            _sk = self.db.q("SELECT COUNT(*) FROM gated_effect WHERE status='pending' "
                            f"AND lower(trim(kind)) IN ({_mph})", tuple(_mk))
            _n_money = _sk[0][0] if _sk else 0
            if _n_money:
                self._note("EFFECT_BATCH_MONEY_SKIPPED",
                           {"skipped": _n_money,
                            "reason": "money/E4 requires exact release_effect (C4) — generic approval releases zero"})
        _ak = sorted(_BATCH_RELEASE_KINDS)
        _ph = ",".join("?" for _ in _ak)
        cur = self.db.ex("UPDATE gated_effect SET status='releasable', release_ref=? "
                         f"WHERE status='pending' AND lower(trim(kind)) IN ({_ph})",
                         (ref, *_ak))
        return cur.rowcount

    def release_one(self, effect_id: str, entry: dict) -> bool:
        """آزادسازیِ **دقیقاً یک** effect با id (نه batch) — مسیرِ اجباریِ kindهای per-effect
        (ارسالِ به مشتری). release_ref = hash همان appendِ انسانیِ مختصِ همین effect (ردِ audit).
        fail-closed: بدونِ ref، یا اگر effect دقیقاً یک ردیفِ pending نباشد → False (چیزی آزاد نمی‌شود).
        این تنها راهِ releasable شدنِ یک kindِ per-effect است؛ authorizationِ صریح بالادست
        (lead_effect_gate) تضمین می‌کند این متد فقط برای effectِ رأی‌خوردهٔ همان لید صدا شود.
        **D3:** زیرِ halt سراسری هیچ authorizationای (دفاعِ عمقی، هم‌ارزِ release_effect)."""
        kill = self.force_closed()
        if kill:
            self._note("EFFECT_REFUSED", {"effect_id": effect_id,
                                          "reason": f"release_one under halt: {kill}"})
            return False
        ref = str(entry.get("hash") or "").strip()
        if not ref:
            self._note("EFFECT_REFUSED", {"effect_id": effect_id,
                                          "reason": "release_one without append ref"})
            return False
        # C4.1 (2026-07-23): E4/money هرگز id-only آزاد نمی‌شود — یک approvalِ فقط-id روی یک
        # effectِ پول یک bypass است (batch بسته شد ولی این تک‌اثری باز بود). پول فقط از
        # release_effect (binding دقیق). money-rowِ بدونِ binding (legacy) → NEEDS_OWNER_REVIEW؛
        # money-rowِ bound → refuse و pending می‌ماند تا release_effectِ دقیق. release_one فقط
        # برای kindهای صریحاً غیر-E4 (ارسالِ مشتری: lead_outbound/customer_send) مجاز است.
        _r = self.db.q("SELECT lower(trim(kind)), content_hash FROM gated_effect "
                       "WHERE effect_id=? AND status='pending'", (effect_id,))
        if _r and _r[0][0] in _E4_MONEY_KINDS:
            if not str(_r[0][1] or "").strip():
                self.db.ex("UPDATE gated_effect SET status='NEEDS_OWNER_REVIEW' "
                           "WHERE effect_id=? AND status='pending'", (effect_id,))
                _reason = "E4 id-only on legacy-unbound money → NEEDS_OWNER_REVIEW"
            else:
                _reason = "E4 money forbids id-only release — requires exact release_effect"
            self._note("EFFECT_REFUSED", {"effect_id": effect_id, "reason": _reason})
            return False
        cur = self.db.ex("UPDATE gated_effect SET status='releasable', release_ref=? "
                         "WHERE effect_id=? AND status='pending'", (ref, effect_id))
        ok = cur.rowcount == 1
        self._note("EFFECT_RELEASE_ONE" if ok else "EFFECT_REFUSED",
                   {"effect_id": effect_id, "release_ref": ref,
                    "ok": ok, "reason": None if ok else "no single pending row"})
        return ok

    def release_effect(self, effect_id: str, approval: dict) -> bool:
        """C4 — authorizationِ دقیق، per-effect، fail-closed: **تنها مسیرِ مجازِ پول/E4**.
        یک approval دقیقاً همین effect را آزاد می‌کند، bind به content_hash + action_kind +
        target_ref، با approval_idِ تک‌مصرفه (anti-replay) و expiry. هر mismatch/replay/expiry/
        غیر-pending/kill-switch → False و صفر release. تمام چک‌های binding در WHEREِ یک UPDATEِ
        اتمیک‌اند (بی‌TOCTOU برای مرحلهٔ release). settle بعداً فقط 'releasable'+release_ref را می‌برد."""
        kill = self.force_closed()
        if kill:
            self.db.ex("UPDATE gated_effect SET status='refused' WHERE effect_id=? "
                       "AND status IN ('pending','releasable')", (effect_id,))
            self._note("EFFECT_REFUSED", {"effect_id": effect_id, "reason": kill})
            return False
        a = approval if isinstance(approval, dict) else {}
        aid = str(a.get("approval_id") or "").strip()
        if not aid:
            self._note("EFFECT_REFUSED", {"effect_id": effect_id, "reason": "empty approval_id"})
            return False
        if str(a.get("effect_id") or "") != str(effect_id):
            self._note("EFFECT_REFUSED",
                       {"effect_id": effect_id, "reason": "approval effect_id mismatch"})
            return False
        now = _utc_ms()
        exp = a.get("expires_at")
        if exp is not None:
            try:
                if now > int(exp):
                    self._note("EFFECT_REFUSED", {"effect_id": effect_id, "reason": "approval expired"})
                    return False
            except (TypeError, ValueError):
                self._note("EFFECT_REFUSED", {"effect_id": effect_id, "reason": "bad expires_at"})
                return False
        # C4.1: مرجعِ لجرِ انسانی اجباری است — approval_id به‌تنهایی authority نیست.
        # این ref باید از appendِ human-appendِ اعتبارسنجی‌شده بیاید (on_human_judgment: entry.hash).
        ref = str(a.get("release_ref") or a.get("ref") or "").strip()
        if not ref:
            self._note("EFFECT_REFUSED",
                       {"effect_id": effect_id, "reason": "missing human ledger reference (release_ref)"})
            return False
        ch, ak, tr = a.get("content_hash"), a.get("action_kind"), a.get("target_ref")
        # تک‌UPDATEِ اتمیک: id + status=pending + bindingِ کامل + anti-replay (approval_id تک‌مصرفه)
        cur = self.db.ex(
            "UPDATE gated_effect SET status='releasable', release_ref=?, approval_id=?, "
            "approved_by=?, approved_at=? "
            "WHERE effect_id=? AND status='pending' AND content_hash=? AND action_kind=? "
            "AND target_ref=? AND NOT EXISTS (SELECT 1 FROM gated_effect WHERE approval_id=?)",
            (ref, aid, a.get("approved_by") or "human", now, effect_id, ch, ak, tr, aid))
        if cur.rowcount == 1:
            self._note("EFFECT_RELEASE_EXACT",
                       {"effect_id": effect_id, "approval_id": aid, "release_ref": ref})
            return True
        # fail-closed: تشخیصِ دلیل فقط برای audit (خواندنِ read-only، صفر تغییرِ حالت)
        row = self.db.q("SELECT status, content_hash, action_kind, target_ref FROM gated_effect "
                        "WHERE effect_id=?", (effect_id,))
        if not row:
            reason = "no such effect"
        elif row[0][0] != "pending":
            reason = f"not pending (status={row[0][0]})"
        elif (row[0][1], row[0][2], row[0][3]) != (ch, ak, tr):
            reason = "binding mismatch (content_hash/action_kind/target_ref)"
        else:
            reason = "approval_id already used (replay) or race"
        self._note("EFFECT_REFUSED",
                   {"effect_id": effect_id, "approval_id": aid, "reason": reason})
        return False

    def status_of(self, effect_id: str) -> str | None:
        """وضعیتِ authoritative یک effect را فقط‌خواندنی برمی‌گرداند.
        pending | releasable | settled | refused | None (ناموجود).
        خواندن، نه نوشتن — کاربرد: نمایِ فقط‌خواندنیِ صفِ تأیید (مانند cockpit)
        تا هرگز با gate واگرا نشود. هیچ اثرِ جانبی."""
        row = self.db.q("SELECT status FROM gated_effect WHERE effect_id=?",
                        (effect_id,))
        return row[0][0] if row else None

    def binding_of(self, effect_id: str) -> dict | None:
        """C-caller-migration — bindingِ فقط‌خواندنیِ یک effect برای ساختِ approvalِ دقیق.
        producerِ کارتِ تأیید (تلگرام) در لحظهٔ ساختِ کارت این snapshot را برمی‌دارد و
        approve همان را ارائه می‌دهد؛ اگر ردیف بعد از کارت عوض شود → mismatch → refuse
        (بستنِ کاملِ card-swap). خواندن، نه نوشتن؛ chrono مالکِ انحصاریِ SQL می‌ماند."""
        row = self.db.q("SELECT content_hash, action_kind, target_ref, kind, status "
                        "FROM gated_effect WHERE effect_id=?", (effect_id,))
        if not row:
            return None
        ch, ak, tr, kind, st = row[0]
        return {"content_hash": ch, "action_kind": ak, "target_ref": tr,
                "kind": kind, "status": st}

    def settle(self, effect_id: str) -> bool:
        """تنها نقطهٔ عبورِ اثر به جهان. False = مجاز نیست (fail-closed).
        C5: دیگر SELECT→blind-UPDATE نیست — کلِ گارد (releasable + release_refِ ناخالی)
        داخلِ WHEREِ یک UPDATEِ اتمیک است؛ دو settleِ همزمان فقط یک برنده دارد و
        pending هرگز مستقیم settled نمی‌شود. مسیرِ receiptدارِ اجرا (executorها) از
        begin_execution/complete_execution می‌گذرد؛ این wrapperِ سازگاریِ تک‌مرحله‌ای است."""
        kill = self.force_closed()
        if kill:
            self.db.ex("UPDATE gated_effect SET status='refused' WHERE effect_id=? "
                       "AND status IN ('pending','releasable')", (effect_id,))
            self._note("EFFECT_REFUSED", {"effect_id": effect_id, "reason": kill})
            return False
        cur = self.db.ex(
            "UPDATE gated_effect SET status='settled' "
            "WHERE effect_id=? AND status='releasable' "
            "AND release_ref IS NOT NULL AND release_ref != ''",
            (effect_id,))
        if cur.rowcount == 1:
            row = self.db.q("SELECT release_ref FROM gated_effect WHERE effect_id=?",
                            (effect_id,))
            self._note("EFFECT_SETTLED", {"effect_id": effect_id,
                                          "release_ref": row[0][0] if row else None})
            return True
        self._note("EFFECT_REFUSED", {"effect_id": effect_id,
                                      "reason": "no matching LANGAR append (TINV-7)"})
        return False

    # ── C5: CAS execution — pending → releasable → EXECUTING → settled ──────────
    def begin_execution(self, effect_id: str, worker_ref: str = "") -> str | None:
        """C5 — claimِ اتمیکِ اجرا: releasable→EXECUTING با execution_idِ تازه.
        برنده execution_id می‌گیرد؛ بازنده None (fail-closed). دو executor روی یک
        effect: دقیقاً یک برنده (CAS در WHERE، بی‌TOCTOU). kill-switch ارشد است."""
        kill = self.force_closed()
        if kill:
            self.db.ex("UPDATE gated_effect SET status='refused' WHERE effect_id=? "
                       "AND status IN ('pending','releasable')", (effect_id,))
            self._note("EFFECT_REFUSED", {"effect_id": effect_id, "reason": kill})
            return None
        import uuid
        xid = uuid.uuid4().hex
        cur = self.db.ex(
            "UPDATE gated_effect SET status='EXECUTING', execution_id=?, "
            "execution_started_at=?, execution_worker_ref=? "
            "WHERE effect_id=? AND status='releasable' "
            "AND release_ref IS NOT NULL AND release_ref != ''",
            (xid, _utc_ms(), str(worker_ref or ""), effect_id))
        if cur.rowcount == 1:
            self._note("EFFECT_EXECUTION_CLAIMED",
                       {"effect_id": effect_id, "execution_id": xid,
                        "worker_ref": str(worker_ref or "")})
            return xid
        self._note("EFFECT_REFUSED",
                   {"effect_id": effect_id,
                    "reason": "claim failed (not releasable, no LANGAR ref, or lost race)"})
        return None

    def complete_execution(self, effect_id: str, execution_id: str,
                           external_receipt_ref: str) -> bool:
        """C5 — commitِ اتمیک: EXECUTING→settled فقط با همان execution_id (workerِ
        stale/عوضی finalize نمی‌کند) و فقط با receiptِ بیرونیِ ناخالی. تکرارِ همان
        completion (همان xid+receipt روی ردیفِ settled) idempotent → True بدونِ تغییر.
        halt وسطِ اجرا: اثرِ بیرونی شاید رخ داده — refuseِ دروغین نمی‌زنیم؛
        EXECUTING→RECONCILE_REQUIRED با ثبتِ receipt/دلیل (آشتیِ انسانی لازم)."""
        xid = str(execution_id or "").strip()
        receipt = str(external_receipt_ref or "").strip()
        if not xid or not receipt:
            self._note("EFFECT_REFUSED",
                       {"effect_id": effect_id,
                        "reason": "complete_execution requires execution_id + external receipt"})
            return False
        kill = self.force_closed()
        if kill:
            cur = self.db.ex(
                "UPDATE gated_effect SET status='RECONCILE_REQUIRED', failure_reason=?, "
                "execution_finished_at=?, external_receipt_ref=? "
                "WHERE effect_id=? AND status='EXECUTING' AND execution_id=?",
                (f"halt during execution: {kill}", _utc_ms(), receipt, effect_id, xid))
            self._note("EFFECT_RECONCILE_REQUIRED",
                       {"effect_id": effect_id, "execution_id": xid,
                        "reason": kill, "updated": cur.rowcount})
            return False
        cur = self.db.ex(
            "UPDATE gated_effect SET status='settled', external_receipt_ref=?, "
            "execution_finished_at=? "
            "WHERE effect_id=? AND status='EXECUTING' AND execution_id=?",
            (receipt, _utc_ms(), effect_id, xid))
        if cur.rowcount == 1:
            self._note("EFFECT_SETTLED",
                       {"effect_id": effect_id, "execution_id": xid,
                        "external_receipt_ref": receipt})
            return True
        row = self.db.q("SELECT status, execution_id, external_receipt_ref "
                        "FROM gated_effect WHERE effect_id=?", (effect_id,))
        if (row and row[0][0] == "settled" and row[0][1] == xid
                and (row[0][2] or "") == receipt):
            return True    # duplicate completion — idempotent، صفر تغییرِ حالت
        self._note("EFFECT_REFUSED",
                   {"effect_id": effect_id, "execution_id": xid,
                    "reason": "complete mismatch (stale worker, wrong execution_id, or not EXECUTING)"})
        return False

    def fail_execution(self, effect_id: str, execution_id: str, reason: str = "") -> bool:
        """C5 — شکستِ امن: اثرِ بیرونی رخ نداده → EXECUTING→FAILED_SAFE (terminal).
        فقط با همان execution_id؛ workerِ stale نمی‌تواند ردیفِ دیگری را بکُشد."""
        xid = str(execution_id or "").strip()
        if not xid:
            return False
        # D3 (red-team MIG-P2، 2026-07-23): زیرِ halt سراسری، fail_execution یک ردیفِ
        # in-flight را به FAILED_SAFEِ ترمینال («اثرِ بیرونی رخ نداد») نمی‌بندد — چون
        # ممکن است رخ داده باشد. هم‌ارزِ complete_execution → RECONCILE_REQUIRED (آشتیِ
        # انسانی)، نه یک ترمینالِ دروغینِ «پول حرکت نکرد» توسطِ workerِ stale زیرِ STOP.
        kill = self.force_closed()
        if kill:
            cur = self.db.ex(
                "UPDATE gated_effect SET status='RECONCILE_REQUIRED', failure_reason=?, "
                "execution_finished_at=? "
                "WHERE effect_id=? AND status='EXECUTING' AND execution_id=?",
                (f"halt during fail_execution ({kill}); "
                 f"claimed-fail reason: {str(reason or 'unspecified')}",
                 _utc_ms(), effect_id, xid))
            self._note("EFFECT_RECONCILE_REQUIRED",
                       {"effect_id": effect_id, "execution_id": xid,
                        "reason": kill, "updated": cur.rowcount})
            return False
        cur = self.db.ex(
            "UPDATE gated_effect SET status='FAILED_SAFE', failure_reason=?, "
            "execution_finished_at=? "
            "WHERE effect_id=? AND status='EXECUTING' AND execution_id=?",
            (str(reason or "unspecified"), _utc_ms(), effect_id, xid))
        ok = cur.rowcount == 1
        self._note("EFFECT_FAILED_SAFE" if ok else "EFFECT_REFUSED",
                   {"effect_id": effect_id, "execution_id": xid,
                    "reason": str(reason or "unspecified") if ok else "fail mismatch"})
        return ok

    def sweep_stale_effects(self, max_age_hours: int = 72) -> dict:
        """gated_effectهایی که بیش از max_age_hours pending هستند → auto-refuse.
        max_age_hours=0 → sweep خاموش (rollback knob).
        هر epoch از governor_epoch.run_epoch() صدا زده می‌شود.
        عمداً فقط pending (قراردادِ test_gate_sweep): releasable در لایهٔ bridge
        freshness-guard دارد و لاینِ C6 جاروی صریحِ خودش را دارد."""
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

    # ── C6: receipt/reconciliation lane ────────────────────────────────────────
    def sweep_stale_releasables(self, max_age_hours: int = 72) -> dict:
        """C6 (crash window b) — intentِ گیرافتاده: releasableای که هرگز claim نشد.
        چون در C5 اجرا فقط با claim شروع می‌شود، releasableِ کهنه یعنی هیچ اثرِ
        بیرونی‌ای رخ نداده → refuseِ امن (fail-closed). عمر از approved_at (لحظهٔ
        releasable شدن) و درنبودش created_ts. max_age_hours=0 → خاموش. جدا از
        sweep_stale_effects تا قراردادِ موجودِ آن (فقط pending) نشکند."""
        if max_age_hours <= 0:
            return {"refused": 0, "ids": []}
        cutoff_ms = _utc_ms() - (max_age_hours * 3600_000)
        rows = self.db.q(
            "SELECT effect_id FROM gated_effect WHERE status='releasable' "
            "AND COALESCE(approved_at, created_ts) < ?", (cutoff_ms,))
        ids = [r[0] for r in rows]
        for eid in ids:
            self.db.ex("UPDATE gated_effect SET status='refused', "
                       "failure_reason=COALESCE(failure_reason, "
                       "'stale releasable — authorized but never claimed (C6 sweep)') "
                       "WHERE effect_id=? AND status='releasable'", (eid,))
        if ids:
            self._note("EFFECT_STALE_RELEASABLE_SWEEP",
                       {"refused_count": len(ids), "ids": ids})
        return {"refused": len(ids), "ids": ids}

    def sweep_stale_executions(self, max_exec_hours: float = 6) -> dict:
        """C6 — workerِ گم‌شده وسطِ اجرا: EXECUTINGِ کهنه → RECONCILE_REQUIRED.
        هرگز refuse نمی‌شود چون اثرِ بیرونی شاید واقعاً رخ داده باشد (crash window c
        صادقانه: بدونِ receipt، exactly-once ادعا نمی‌کنیم — فقط آشتیِ انسانی).
        max_exec_hours=0 → خاموش."""
        if max_exec_hours <= 0:
            return {"reconcile_required": 0, "ids": []}
        cutoff_ms = _utc_ms() - int(max_exec_hours * 3600_000)
        rows = self.db.q(
            "SELECT effect_id FROM gated_effect WHERE status='EXECUTING' "
            "AND execution_started_at IS NOT NULL AND execution_started_at < ?",
            (cutoff_ms,))
        ids = [r[0] for r in rows]
        for eid in ids:
            self.db.ex(
                "UPDATE gated_effect SET status='RECONCILE_REQUIRED', "
                "failure_reason=COALESCE(failure_reason, "
                "'stale execution — worker lost mid-flight (C6 sweep)') "
                "WHERE effect_id=? AND status='EXECUTING'", (eid,))
        if ids:
            self._note("EFFECT_STALE_EXECUTION_SWEEP",
                       {"reconcile_count": len(ids), "ids": ids})
        return {"reconcile_required": len(ids), "ids": ids}

    def reconcile_effect(self, effect_id: str, resolution: str, evidence_ref: str,
                         operator: str = "") -> bool:
        """C6 — حلِ انسانیِ یک ردیفِ RECONCILE_REQUIRED پس از تحقیقِ بیرونی.
        resolution='settled' (اثباتِ وقوعِ بیرونی؛ evidence_ref = مرجعِ receipt) یا
        resolution='failed_safe' (اثباتِ عدمِ وقوع). evidence و operator اجباری‌اند.
        CAS اتمیک فقط از RECONCILE_REQUIRED؛ receiptِ ثبت‌شدهٔ قبلی هرگز بازنویسی
        نمی‌شود؛ زیرِ halt هیچ reconciliationای مجاز نیست (D-block)."""
        res = str(resolution or "").strip().lower()
        ev = str(evidence_ref or "").strip()
        op = str(operator or "").strip()
        if res not in ("settled", "failed_safe") or not ev or not op:
            self._note("EFFECT_REFUSED",
                       {"effect_id": effect_id,
                        "reason": "reconcile needs resolution in {settled,failed_safe} + evidence + operator"})
            return False
        kill = self.force_closed()
        if kill:
            self._note("EFFECT_REFUSED",
                       {"effect_id": effect_id,
                        "reason": f"no reconciliation under halt: {kill}"})
            return False
        target = "settled" if res == "settled" else "FAILED_SAFE"
        receipt_fill = ev if res == "settled" else None
        cur = self.db.ex(
            "UPDATE gated_effect SET status=?, "
            "external_receipt_ref=COALESCE(NULLIF(external_receipt_ref,''), ?), "
            "failure_reason=COALESCE(failure_reason,'') || ' | reconciled('||?||') by '||?||': '||?, "
            "execution_finished_at=COALESCE(execution_finished_at, ?) "
            "WHERE effect_id=? AND status='RECONCILE_REQUIRED'",
            (target, receipt_fill, res, op, ev, _utc_ms(), effect_id))
        ok = cur.rowcount == 1
        self._note("EFFECT_RECONCILED" if ok else "EFFECT_REFUSED",
                   {"effect_id": effect_id, "resolution": res, "operator": op,
                    "evidence_ref": ev,
                    "reason": None if ok else "not RECONCILE_REQUIRED"})
        return ok

    def reconciliation_report(self, max_exec_hours: float = 6,
                              max_age_hours: int = 72) -> dict:
        """C6 — نمای فقط‌خواندنیِ لاینِ آشتی: چه چیزی توجهِ انسانی/جارو می‌خواهد.
        هیچ اثرِ جانبی — گزارش برای cockpit/governor/owner packet."""
        now = _utc_ms()
        exec_cutoff = now - int(max_exec_hours * 3600_000) if max_exec_hours > 0 else None
        rel_cutoff = now - (max_age_hours * 3600_000) if max_age_hours > 0 else None
        need = [r[0] for r in self.db.q(
            "SELECT effect_id FROM gated_effect WHERE status='RECONCILE_REQUIRED'")]
        stale_exec = [] if exec_cutoff is None else [r[0] for r in self.db.q(
            "SELECT effect_id FROM gated_effect WHERE status='EXECUTING' "
            "AND execution_started_at IS NOT NULL AND execution_started_at < ?",
            (exec_cutoff,))]
        stale_rel = [] if rel_cutoff is None else [r[0] for r in self.db.q(
            "SELECT effect_id FROM gated_effect WHERE status='releasable' "
            "AND COALESCE(approved_at, created_ts) < ?", (rel_cutoff,))]
        return {"reconcile_required": need, "stale_executing": stale_exec,
                "stale_releasable": stale_rel,
                "attention_total": len(need) + len(stale_exec) + len(stale_rel)}


# ─── LANGAR — فلشِ میرا (P-Chrono-4؛ ledger ژنوم v0.4.5 گسترش‌یافته) ─────────────
def _route_authorized_judgment(gate: "EffectorGate", judgment, entry: dict) -> None:
    """مسیریابیِ یک قضاوتِ انسانیِ authorized به releaseِ درست — C6 این را از
    on_human_judgment استخراج کرد تا redrive_approval هم عینِ همان معناشناسی را
    بدونِ appendِ دوباره به ledger استفاده کند (semantics C4/C4.1 بایت‌به‌بایت):
    BLOCKER-2 (§3.7b): approval که effectِ مشخص را نام می‌برد فقط همان را آزاد
    می‌کند؛ approvalِ بدونِ effect_id هنوز batch (allowlistِ پول، E4 مستثنا)."""
    _eid = ""
    _has_binding = False
    if isinstance(judgment, dict):
        _eid = str(judgment.get("effect_id") or "").strip()
        _has_binding = any(judgment.get(k) for k in
                           ("content_hash", "action_kind", "target_ref", "approval_id"))
    if _eid and _has_binding:
        # C4: authorizationِ دقیقِ per-effect (مسیرِ پول/E4). approval به
        # content_hash/action_kind/target_ref bind می‌شود با approval_idِ تک‌مصرفه.
        gate.release_effect(_eid, {
            "effect_id": _eid,
            "approval_id": str(judgment.get("approval_id") or entry.get("hash") or "").strip(),
            "content_hash": judgment.get("content_hash"),
            "action_kind": judgment.get("action_kind"),
            "target_ref": judgment.get("target_ref"),
            "approved_by": judgment.get("approved_by") or "human",
            "expires_at": judgment.get("expires_at"),
            "release_ref": entry.get("hash")})
    elif _eid:
        gate.release_one(_eid, entry)         # id-bound، مسیرِ غیرپولِ ارسالِ مشتری
    else:
        gate.release_gated_effects(entry)     # batch — پول/E4 مستثنا (C4)


def redrive_approval(judgment: dict, entry_ref: str,
                     gate: "EffectorGate") -> bool:
    """C6 (crash window a) — بازراندنِ APPROVALی که در ledger ثبت شد ولی crash مانعِ
    releaseاش شد. **هیچ appendِ تازه‌ای به ledger نمی‌زند** (age_tickِ میرا جلو نمی‌رود).
    فقط قضاوت‌های تک‌اثری (effect_idدار) بازرانده می‌شوند — batchِ عمومی عمداً نه
    (fail-closed؛ batchِ گم‌شده مسیرِ ارزان‌تر و امن‌ترش تکرارِ رأیِ انسانی است).
    idempotent: anti-replayِ approval_id و گاردهای status باعث می‌شوند بازراندنِ
    تکراری/دیرهنگام صفر اثرِ اضافه بگذارد. ورودی باید از یک entryِ APPROVALِ humanِ
    اعتبارسنجی‌شده در ledger بیاید (مسئولیتِ لاینِ reconciliation)؛
    entry_ref = hash همان append. خروجی: آیا همین بازراندن effect را releasable کرد."""
    ref = str(entry_ref or "").strip()
    if gate is None or not ref or not isinstance(judgment, dict):
        return False
    if gate.force_closed():
        return False                          # D-block: زیرِ halt هیچ redriveای
    eid = str(judgment.get("effect_id") or "").strip()
    if not eid:
        return False                          # batch redrive ممنوع — فقط تک‌اثری
    before = gate.status_of(eid)
    _route_authorized_judgment(gate, judgment, {"hash": ref})
    after = gate.status_of(eid)
    return before == "pending" and after == "releasable"


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
        except Exception as _guard_err:  # noqa: BLE001 — fail-CLOSED (§3.8)
            # BLOCKER-1: خطای گارد دیگر «رفتارِ قبلی (is_human=True)» نیست — چون
            # گاردِ armed است، خطای غیرمنتظره نباید یک append را انسانی جا بزند.
            # «گاردِ پیکربندی‌نشده/خاموش» جداگانه از طریقِ reasonِ
            # guard-disabled-passthrough بالا مدیریت می‌شود (به except نمی‌رسد)،
            # پس این مسیر فقط خطاهای واقعی است → عدمِ اعتماد (age_tick جلو نمی‌رود).
            is_human = False
            opslib.alert([f"human-append guard: is_human downgraded "
                          f"(guard-exception: {_guard_err!r}) — fail-closed (ضدِ جعلِ E16)"])
    # BLOCKER-1 (fail-closed در کلِ مسیر، نه فقط برچسبِ ledger):
    # یک append که قضاوتِ انسانیِ authorized نیست (گارد armed رد/خطا داد) به‌عنوانِ
    # مشاهدهٔ سیستمی ثبت می‌شود ولی **نباید هیچ effectی را release یا settle کند**.
    # invariantِ اجباری:  authorized == False  ⇒  released == 0  ⇒  settled == 0
    authorized = is_human
    entry = lg.append(event_type, judgment,
                      actor="human" if is_human else "system", is_human=is_human)
    if gate is not None and authorized:
        _route_authorized_judgment(gate, judgment, entry)
    elif gate is not None:
        # append غیرمجاز به gate رسید → صفر release، ردِ صریح.
        opslib.alert(["human-append guard: unauthorized append — 0 effects released "
                      "(fail-closed release gate, §3.8 invariant)"])
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

    def _tick_decision(self) -> str:
        """تصمیمِ هر تیکِ run_forever (تست‌پذیر، بدونِ sleep):
          · 'stop'  = kill supreme — STOP-ORGANISM یا master_halted() (HALT-ALL / STOP معمار).
                      تسلیمِ بی‌قیدوشرط؛ خروجِ دائم (رفتارِ قبلی، دست‌نخورده).
          · 'pause' = STOP-METABOLIC — محافظتِ خودکارِ متابولیک (می‌تواند کاذب باشد).
                      توقفِ **برگشت‌پذیر**، نه مرگِ نخ.
          · 'beat'  = ضربانِ عادی.
        ترتیب = شدت: kill supreme همیشه بر STOP-METABOLIC مقدم است."""
        if opslib.STOP_ORGANISM.exists() or opslib.master_halted():
            return "stop"
        if opslib.STOP_METABOLIC.exists():
            return "pause"
        return "beat"

    def run_forever(self) -> None:
        """حلقهٔ پس‌زمینه برای organism.py.
          · kill supreme (STOP-ORGANISM / HALT-ALL / STOP معمار) → تسلیمِ بی‌قیدوشرط (return).
          · STOP-METABOLIC → **pause-not-die**: نبض را نگه می‌دارد ولی نخ زنده می‌ماند و با
            رفعِ شرط، ضربان خودکار از سر گرفته می‌شود.
        رفعِ frozen-beat ۲۰۲۶-۰۷-۲۳: قبلاً `opslib.halted()` (که STOP-METABOLIC را هم برمی‌گرداند)
        باعثِ return دائم می‌شد و در یک STOP-METABOLICِ کاذب نبض روی همان beat یخ می‌زد."""
        paused = False
        while True:
            decision = self._tick_decision()
            if decision == "stop":
                if paused:  # از pause مستقیم به kill — لاگِ صادق
                    opslib.heartbeat(f"chrono=STOP-after-pause beat={self.beat}")
                return
            if decision == "pause":
                if not paused:
                    paused = True
                    opslib.heartbeat(f"chrono=PAUSED (STOP-METABOLIC) beat={self.beat} "
                                     f"— pause-not-die")
                time.sleep(self.period_s)
                continue
            if paused:
                paused = False
                opslib.heartbeat(f"chrono=RESUMED (STOP-METABOLIC cleared) beat={self.beat}")
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
