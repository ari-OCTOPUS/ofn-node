#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""beat_scheduler.py — C5: یک ضربان، یک زمان‌بند (shadow-first، پشتِ OCTOPUS_ONE_HEARTBEAT=0).

مأموریت: همهٔ ارگان‌های Brain Core زیرِ **یک** beat و یک beat_counterِ durable — بدونِ big-bang.
این ماژول scheduler را می‌سازد؛ loopهای قدیمی موازی می‌مانند تا parity سبز شود (مهاجرت تدریجی).

قرارداد organ: name, phase, every_n_beats, budget_ms, read_set, write_set, failure_policy, halt_behavior.
فازها (ترتیبِ قطعی): SENSE→RECORD→THINK→DECIDE→PROPOSE→ACT→LEARN→HEAL.

قواعدِ سخت (معیارهای موفقیتِ مأموریت):
  - **یک scheduler**، ترتیبِ فازِ قطعی، اجرای bounded (budget per handler).
  - **صفر double-actuation:** فازِ ACT پیش‌فرض **dry-run** است (پشتِ ACT_ARMED جدا، پیش‌فرض OFF)
    تا با loopهای قدیمیِ زنده هم‌زمان effect ندهد.
  - **organ failure isolation:** fail یک organ = fail-soft همان organ؛ **ضربان هرگز نمی‌ایستد**.
  - **circuit breaker:** organ که مکرر fail/overrun کند برای K beat quarantine می‌شود.
  - **restart continuity:** beat_counter durable؛ بیداری از beatِ **بعدی** ادامه می‌دهد،
    هرگز beatِ قبلی را دوباره اجرا نمی‌کند.
  - **HALT:** پیش از هر beat و پیش از ACT، اگر HALT → beat در حالتِ halted (فقط SENSE/RECORD/HEAL
    ایمن؛ ACT/effect هرگز). fail-closed.
  - **system.beat → spine** (پشتِ WIRE_SPINE) با beat_counter + HLC + provenance.
  - stdlib فقط؛ fail-soft؛ صفر شبکه/پول در خودِ scheduler.
"""
from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

_HERE = Path(__file__).resolve().parent
for _p in (str(_HERE), str(_HERE / "budget"), str(_HERE / "spine")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

FLAG = "OCTOPUS_ONE_HEARTBEAT"
ACT_ARMED_FLAG = "OCTOPUS_ONE_HEARTBEAT_ACT_ARMED"   # retained only for compatibility/status
# stage-3.2 (2026-07-24): organs مستقلِ یک فاز می‌توانند موازی اجرا شوند (conflict-detected).
_PARALLEL_FLAG = "OCTOPUS_BEAT_PARALLEL"   # پیش‌فرض خاموش = serial (رفتارِ امروز)
PHASES = ("SENSE", "RECORD", "THINK", "DECIDE", "PROPOSE", "ACT", "LEARN", "HEAL")
# C7.2: generic scheduler has no transactional outbox yet. Production composition must
# never register phases whose retry could duplicate an effect or durable learning write.
FORBIDDEN_PRODUCTION_PHASES = frozenset({"ACT", "LEARN"})
_PHASE_IX = {p: i for i, p in enumerate(PHASES)}
_SAFE_UNDER_HALT = ("SENSE", "RECORD", "HEAL")       # فقط این فازها زیرِ HALT اجرا می‌شوند
_CB_FAIL_THRESHOLD = 3        # این تعداد fail/overrunِ پیاپی → quarantine
_CB_QUARANTINE_BEATS = 5


def flag_on() -> bool:
    return str(os.environ.get(FLAG, "")).strip().lower() in ("1", "true", "yes", "on")


def _act_armed() -> bool:
    return str(os.environ.get(ACT_ARMED_FLAG, "")).strip().lower() in ("1", "true", "yes", "on")


class Organ:
    __slots__ = ("name", "phase", "every_n_beats", "budget_ms", "handler",
                 "failure_policy", "halt_behavior", "read_set", "write_set",
                 "fail_streak", "quarantined_until", "runs", "fails")

    def __init__(self, name, phase, handler, *, every_n_beats=1, budget_ms=1000,
                 failure_policy="fail-soft", halt_behavior="run",
                 read_set=(), write_set=()):
        # halt_behavior: "run" (پیش‌فرض) = در فازهای مجازِ زیرِ HALT اجرا شو (SENSE/RECORD/HEAL
        #   امن‌اند؛ ACT/effect را گیتِ فاز جدا می‌بندد). "skip-on-halt" = حتی در فازِ امن هم skip.
        if phase not in _PHASE_IX:
            raise ValueError(f"unknown phase {phase!r}")
        self.name = name
        self.phase = phase
        self.handler = handler
        self.every_n_beats = max(1, int(every_n_beats))
        self.budget_ms = float(budget_ms)
        self.failure_policy = failure_policy
        self.halt_behavior = halt_behavior
        self.read_set = tuple(read_set)
        self.write_set = tuple(write_set)
        self.fail_streak = 0
        self.quarantined_until = 0
        self.runs = 0
        self.fails = 0

    def contract(self) -> dict:
        return {"name": self.name, "phase": self.phase, "every_n_beats": self.every_n_beats,
                "budget_ms": self.budget_ms, "failure_policy": self.failure_policy,
                "halt_behavior": self.halt_behavior, "read_set": list(self.read_set),
                "write_set": list(self.write_set)}


class BeatScheduler:
    """یک ضربان. tick() یک beatِ کامل را اجرا می‌کند. beat_counter durable است."""

    def __init__(self, *, state_path=None, clock=None, spine=None, halted_fn=None,
                 production_safe=False):
        self._organs: list[Organ] = []
        self._clock = clock or (lambda: time.time())     # تزریق‌پذیر (virtual-time tests)
        self._spine = spine                              # EventSpine یا None
        self._halted_fn = halted_fn                      # () -> reason|None
        self.production_safe = bool(production_safe)
        self._state_path = Path(state_path) if state_path else (_HERE / "state" / "pulse" / "beat-state.json")
        self.committed_counter = 0     # C7.1 (B14): monotonic — فقط با COMMIT جلو می‌رود
        self.beat_counter = 0          # alias عمومیِ committed (سازگاریِ عقب‌رو + watchdog)
        self.boot_id = None
        self.recovery = None           # اگر بوت یک beatِ RESERVED-اما-COMMIT-نشده ببیند → reconcile
        self._load()

    # ── durability ──────────────────────────────────────────────────────────
    def _load(self):
        self.committed_counter = 0
        self.recovery = None
        try:
            if self._state_path.exists():
                d = json.loads(self._state_path.read_text("utf-8"))
                # committed_counter منبعِ حقیقت است؛ beat_counterِ قدیمی = fallback (مهاجرت)
                self.committed_counter = int(d.get("committed_counter",
                                                    d.get("beat_counter", 0)))
                self.boot_id = d.get("boot_id")
                cur = d.get("current") or {}
                # B14: beatِ RESERVED/DEGRADEDِ بزرگ‌تر از committed = «شروع شد، commit نشد» →
                # reconcile، **نه** تلقیِ خاموشِ «کامل». هویتِ committed هرگز از این جلو نمی‌رود.
                if (cur.get("status") in ("RESERVED", "RUNNING", "DEGRADED")
                        and int(cur.get("beat", 0)) > self.committed_counter):
                    self.recovery = {"reconcile": True, "reserved_beat": int(cur.get("beat", 0)),
                                     "status": cur.get("status"),
                                     "note": "beat reserved but never committed — reconcile, "
                                             "not treated as complete; no re-run of ACT/LEARN "
                                             "for it until a fresh committed identity exists"}
        except Exception:  # noqa: BLE001 — بوتِ تازه
            self.committed_counter = 0
        self.beat_counter = self.committed_counter

    def _persist(self, beat: int, halted, report, status: str = "COMMITTED") -> bool:
        """هویتِ beat را atomically durable کن با lifecycleِ صریح (B14).
        status ∈ RESERVED | RUNNING | COMMITTED | DEGRADED. committed_counter فقط وقتی که
        status='COMMITTED' برابرِ beat می‌شود؛ در بقیهٔ حالات committed دست‌نخورده می‌ماند
        (پس بوتِ بعدی می‌تواند beatِ ناتمام را reconcile کند). خروجی bool — شکست بلعیده نمی‌شود؛
        caller شکستِ reserve را با block کردنِ ACT/LEARN و شکستِ commit را با degraded پاسخ می‌دهد."""
        committed = beat if status == "COMMITTED" else self.committed_counter
        try:
            self._state_path.parent.mkdir(parents=True, exist_ok=True)
            tmp = self._state_path.with_suffix(".tmp")
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump({"committed_counter": committed,
                           "beat_counter": committed,          # سازگاریِ عقب‌رو (watchdog)
                           "current": {"beat": beat, "status": status, "at": self._clock()},
                           "last_beat_at": self._clock(),
                           "halted": bool(halted), "boot_id": self.boot_id,
                           "organs": len(self._organs)}, f, ensure_ascii=False)
                f.flush()
                os.fsync(f.fileno())
            os.replace(tmp, self._state_path)   # atomic
            return True
        except Exception:  # noqa: BLE001
            return False

    def recovery_state(self) -> "dict | None":
        """اگر بوت یک beatِ RESERVED-اما-COMMIT-نشده دید، وضعیتِ reconcile را برمی‌گرداند (وگرنه None)."""
        return self.recovery

    # ── registration ────────────────────────────────────────────────────────
    def register_organ(self, name, phase, handler, **kw) -> Organ:
        """یک organ را ثبت کن. loopِ مستقلِ جدید ممنوع — همه از این‌جا (قاعدهٔ بقا)."""
        if any(o.name == name for o in self._organs):
            raise ValueError(f"organ {name!r} already registered")
        if self.production_safe and phase in FORBIDDEN_PRODUCTION_PHASES:
            raise ValueError(
                f"production-safe scheduler forbids {phase}; transactional outbox required")
        org = Organ(name, phase, handler, **kw)
        self._organs.append(org)
        # ترتیبِ قطعی: بر اساسِ فاز، سپس ترتیبِ ثبت
        self._organs.sort(key=lambda o: _PHASE_IX[o.phase])
        return org

    def contracts(self) -> list:
        return [o.contract() for o in self._organs]

    def _halted(self):
        if self._halted_fn is not None:
            try:
                return self._halted_fn()
            except Exception:  # noqa: BLE001
                return None
        try:
            import opslib  # noqa: WPS433
            return opslib.halted()
        except Exception:  # noqa: BLE001
            return None

    # ── the beat ─────────────────────────────────────────────────────────────
    def tick(self) -> dict:
        """یک beatِ کامل. خروجی: گزارشِ ترتیب/بودجه/خطا/halt. هرگز raise نمی‌کند."""
        beat = self.committed_counter + 1
        halt_reason = self._halted()
        # C7.1 (B14): هویتِ beat را **پیش از** فازها با status=RESERVED durable کن (committed
        # جلو نمی‌رود). اگر persist نشد → degraded: فازهای commit-دار (DECIDE/PROPOSE/ACT/LEARN)
        # اجرا نمی‌شوند و committed_counter جلو نمی‌رود. «no durable identity → no ACT → no LEARN».
        reserved = self._persist(beat, halt_reason, {"phase": "reserve"}, status="RESERVED")
        degraded = not reserved
        _COMMIT_PHASES = ("DECIDE", "PROPOSE", "ACT", "LEARN")
        # C7.2: an incomplete prior beat may already have crossed ACT/LEARN before
        # its final commit failed.  Retrying those phases would duplicate effects.
        # Recovery beats are therefore safe-phase/advisory only until reconciliation.
        recovery_block = bool(self.recovery and self.recovery.get("reconcile"))
        # ACT_ARMED is deliberately ignored in production-safe mode until an operation-level
        # outbox/idempotency receipt exists. Shadow composition is structurally ACT/LEARN-free.
        act_armed = (not self.production_safe and _act_armed()
                     and not degraded and not recovery_block)
        order, results = [], {}
        for phase in PHASES:
            # زیرِ HALT فقط فازهای امن اجرا می‌شوند (ACT/effect هرگز — fail-closed)
            if halt_reason and phase not in _SAFE_UNDER_HALT:
                continue
            # بدونِ هویتِ durable، فازهای commit-دار اجرا نمی‌شوند (fail-closed).
            # On an incomplete-beat recovery, ACT/LEARN never rerun: their prior
            # external/durable outcome is unknown and must be reconciled first.
            if degraded and phase in _COMMIT_PHASES:
                continue
            if recovery_block and phase in ("ACT", "LEARN"):
                continue
            # organs این فاز که باید این beat اجرا شوند (cadence + quarantine)
            due = [o for o in self._organs if o.phase == phase
                   if beat % o.every_n_beats == 0 and o.quarantined_until < beat]
            for org in due:
                order.append(org.name)
            # PARALLEL (stage-3.2، پشتِ flag): organs مستقلِ یک فاز موازی اجرا می‌شوند
            # اگر write-set ناهمپوشان داشته باشند؛ وگرنه serial (امروز). flag خاموش = امروز.
            if (str(os.environ.get(_PARALLEL_FLAG, "")).strip().lower()
                    in ("1", "true", "yes", "on") and len(due) > 1
                    and self._independent(due)):
                results.update(self._run_phase_parallel(due, beat, halt_reason, act_armed, phase))
            else:
                for org in due:
                    dry = (phase == "ACT") and not act_armed
                    results[org.name] = self._run_organ(org, beat, halt_reason, dry)
            # organs قرنطینه‌شده را هم ثبت کن (نه فقط skip خاموش)
            for org in [o for o in self._organs if o.phase == phase
                        if beat % o.every_n_beats == 0 and o.quarantined_until >= beat]:
                results[org.name] = {"skipped": "quarantined", "until": org.quarantined_until}
        # system.beat → spine (فاز RECORD‌گونه: خودِ ضربان ثبت می‌شود)
        self._emit_beat(beat, halt_reason, order)
        # B14: commitِ نهایی **چک می‌شود** — اگر persist نشد، beat committed نیست → degraded،
        # committed_counter جلو نمی‌رود (بوتِ بعدی reconcile/بازتلاش، نه تلقیِ خاموشِ «کامل»).
        committed = False
        if reserved:
            if self._persist(beat, halt_reason, results, status="COMMITTED"):
                self.committed_counter = beat
                self.beat_counter = beat
                committed = True
            else:
                degraded = True
                self.recovery = {"reconcile": True, "reserved_beat": beat,
                                 "status": "DEGRADED",
                                 "note": "final commit failed; ACT/LEARN retry blocked"}
        if committed:
            # A safe recovery beat closes the scheduler-level ambiguity. Operation-level
            # effect reconciliation remains the authority for any earlier ACT receipt.
            self.recovery = None
        status = "COMMITTED" if committed else ("DEGRADED" if degraded else "RESERVED")
        return {"beat": beat, "halted": halt_reason, "act_armed": act_armed,
                "recovery_block": recovery_block,
                "degraded": degraded, "committed": committed, "status": status,
                "phase_order": order, "results": results}

    def _run_organ(self, org: Organ, beat, halt_reason, dry_run) -> dict:
        """اجرای یک handler با budget + failure isolation + circuit breaker."""
        if halt_reason and org.halt_behavior == "skip-on-halt":
            return {"skipped": "halt"}
        t0 = self._clock()
        try:
            org.runs += 1
            out = org.handler(beat=beat, dry_run=dry_run, halt=halt_reason)
            dt_ms = (self._clock() - t0) * 1000.0
            over = dt_ms > org.budget_ms
            if over:                                  # overrun = soft-fail (به سمتِ circuit breaker)
                org.fail_streak += 1
            else:
                org.fail_streak = 0
            if org.fail_streak >= _CB_FAIL_THRESHOLD:
                org.quarantined_until = beat + _CB_QUARANTINE_BEATS
                org.fail_streak = 0
            return {"ok": True, "dry_run": dry_run, "ms": round(dt_ms, 1),
                    "over_budget": over,
                    "quarantined": org.quarantined_until >= beat + 1,
                    "result": out if isinstance(out, (dict, str, int, float, bool, type(None))) else "opaque"}
        except Exception as e:  # noqa: BLE001 — organ failure isolation: ضربان ادامه دارد
            org.fails += 1
            org.fail_streak += 1
            if org.fail_streak >= _CB_FAIL_THRESHOLD:
                org.quarantined_until = beat + _CB_QUARANTINE_BEATS
                org.fail_streak = 0
            return {"ok": False, "error": type(e).__name__,
                    "quarantined": org.quarantined_until >= beat + 1}

    # ── stage-3.2: parallel execution inside a phase (conflict-detected) ──────
    @staticmethod
    def _independent(organs: list) -> bool:
        """آیا organsِ یک فاز مستقل‌اند؟ یعنی هیچ write-set مشترکی ندارند.
        اگر هر write-set با write-setِ دیگری اشتراک دارد → serial لازم (safe).
        organs بدونِ write_set همیشه مستقل فرض می‌شوند (read-only)."""
        for i, a in enumerate(organs):
            wa = set(a.write_set or ())
            for b in organs[i + 1:]:
                wb = set(b.write_set or ())
                if wa and wb and (wa & wb):
                    return False   # همپوشانیِ write → رقابت → serial
        return True

    def _run_phase_parallel(self, organs: list, beat, halt_reason, act_armed, phase) -> dict:
        """اجرای موازیِ organs مستقلِ یک فاز با ThreadPoolExecutor.
        thread-safety: هر organ فقط به selfِ خودش می‌نویسد (runs/fails/quarantined_until)،
        ticks خود سریال‌اند (organism loop یکی‌یکی tick می‌زند) پس هم‌پوشانیِ بین-beat نیست.
        실패ِ یک organ بقیه را نمی‌کشد (failure isolation حفظ می‌شود)."""
        import concurrent.futures
        results = {}
        dry_default = (phase == "ACT") and not act_armed
        # محدودِ modest: بیشینهٔ workers = تعدادِ organs (معمولاً کم) ولی کف ۲.
        max_w = max(2, len(organs))
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_w) as ex:
            future_map = {ex.submit(self._run_organ, org, beat, halt_reason, dry_default): org
                          for org in organs}
            for fut in concurrent.futures.as_completed(future_map):
                org = future_map[fut]
                try:
                    results[org.name] = fut.result()
                except Exception as e:  # noqa: BLE001 — defense-in-depth: نباید اتفاق بیفتد
                    results[org.name] = {"ok": False, "error": f"parallel:{type(e).__name__}"}
        return results

    @staticmethod
    def heartbeat_health(state_path=None, *, stall_after_s: float = 900.0, now=None) -> dict:
        """watchdog (C5 step 15): غیاب/توقفِ ضربان را تشخیص بده — از beat-state.jsonِ durable.
        {alive, beat, age_s, stall, reason}. stall = آخرین beat بیش از stall_after_s پیش بوده."""
        p = Path(state_path) if state_path else (_HERE / "state" / "pulse" / "beat-state.json")
        now = now if now is not None else time.time()
        if not p.exists():
            return {"alive": False, "stall": True, "reason": "no beat-state (never beat)"}
        try:
            d = json.loads(p.read_text("utf-8"))
        except Exception:  # noqa: BLE001
            return {"alive": False, "stall": True, "reason": "beat-state unreadable"}
        age = now - float(d.get("last_beat_at") or 0)
        stall = age > stall_after_s
        return {"alive": not stall, "beat": d.get("beat_counter"), "age_s": round(age, 1),
                "stall": stall, "halted": d.get("halted"),
                "reason": ("stalled" if stall else "beating")}

    def _emit_beat(self, beat, halt_reason, order):
        try:
            import spine_adapters as _sa  # noqa: WPS433
            _sa.emit_event(spine=self._spine, event_type="system.beat", domain="system",
                           correlation_id=f"beat_{beat}", subject=str(beat),
                           producer="beat_scheduler", trust="DETERMINISTIC",
                           payload={"beat": beat, "halted": bool(halt_reason),
                                    "organs_run": len(order)})
        except Exception:  # noqa: BLE001 — emit نباید ضربان را بکشد
            pass
