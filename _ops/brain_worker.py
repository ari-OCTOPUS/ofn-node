#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""brain_worker.py — M2.2 tick decoupling: event-driven brain workers.

PROPOSE-ONLY DRAFT. Not wired into the live organism. Behind OCTOPUS_WIRE_TICK_WORKERS
(default off). When off, organism.py runs the inline pipeline exactly as today (no
regression). When on, organism.py's metabolic core stays thin (kill-check + telemetry +
state write + heartbeat) and enqueues one `tick` event per period; this module's worker
pool runs the ordered organ pipeline off the metabolic thread.

Design invariants (see DESIGN-tick-decoupling.md):
  · The metabolic core is the queue PRODUCER and never blocks: submit_* uses put_nowait
    and coalesces/drops when full (a missed cadence tick is harmless; beats are
    cadence-gated + idempotent; durability lives in chrono.db / genome ledger / journals,
    never in this queue).
  · Three isolation layers so a worker crash can NEVER kill the metabolic core:
      1. per-organ try/except (transplanted verbatim from organism.py — charter §4)
      2. per-task try/except in the worker loop
      3. per-thread supervisor with a restart circuit-breaker (mirrors chrono self-heal)
  · One correlation id per cycle via events.begin_run()/end_run() (moved from the per-tick
    site organism.py:402,849-853).
  · State stays single-writer-to-disk: workers only write in-memory blocks into StateLatch;
    the metabolic core reads latch.snapshot() and does the one LockedJson write.
  · Kill stays supreme: the pipeline self-gates on STOP/halt, and EffectorGate re-checks
    force_closed() on every settle/release/execute independently.

stdlib-only, $0, offline.
"""
from __future__ import annotations

import json
import os
import queue
import threading
import time
from pathlib import Path
from typing import Any, Callable, Optional

_HERE = Path(__file__).resolve().parent
import sys
sys.path.insert(0, str(_HERE / "budget"))
sys.path.insert(0, str(_HERE))
import opslib          # noqa: E402

try:
    import events as _events   # correlation_id (run-scoped) — same module organism uses
except Exception:              # noqa: BLE001 — additive; absence must not break workers
    _events = None

FLAG = "OCTOPUS_WIRE_TICK_WORKERS"


def flag_on() -> bool:
    return str(os.environ.get(FLAG, "")).strip().lower() in ("1", "true", "yes", "on")


def _envi(name: str, default: int) -> int:
    try:
        return int(os.environ.get(name, default))
    except (TypeError, ValueError):
        return default


# ─────────────────────────── shared, thread-safe state ──────────────────────────
class StateLatch:
    """In-memory bag of organ 'blocks'. Workers set(); the metabolic core snapshot()s
    and merges into the single ORGANISM-STATE.json write. Preserves the existing
    'freeze last-known block while ts advances' semantics (organism.py:174-187)."""

    def __init__(self) -> None:
        self._lk = threading.Lock()
        self._d: dict[str, Any] = {}

    def set(self, key: str, value: Any) -> None:
        with self._lk:
            self._d[key] = value

    def update(self, mapping: dict) -> None:
        with self._lk:
            self._d.update(mapping)

    def snapshot(self) -> dict:
        with self._lk:
            return dict(self._d)


class Wired:
    """The objects wiring builds once at boot (organism.py:216-296). Passed to the pool
    so the pipeline can reach them without the metabolic core holding brain references."""

    def __init__(self, *, w, chrono=None, doctor=None, neural_stack=None,
                 school_bridge=None, sensory_bus=None, live_loop=None, leg=None,
                 ziman_leg=None, cartographer_leg=None, idea_graph=None,
                 pacemaker=None, rhythm=None, circadian=None, chan=None) -> None:
        self.w = w                          # wiring module
        self.chrono = chrono
        self.doctor = doctor
        self.neural_stack = neural_stack
        self.school_bridge = school_bridge
        self.sensory_bus = sensory_bus
        self.live_loop = live_loop
        self.leg = leg
        self.ziman_leg = ziman_leg
        self.cartographer_leg = cartographer_leg
        self.idea_graph = idea_graph
        self.pacemaker = pacemaker
        self.rhythm = rhythm
        self.circadian = circadian
        self.chan = chan


class BeatContext:
    """Per-cycle dynamic data the metabolic core computes and hands to the pipeline."""

    def __init__(self, *, wired: Wired, latch: StateLatch, snap: dict, conflicts: list,
                 cstat: Optional[dict], now: float, correlation_id: str = "") -> None:
        self.wired = wired
        self.latch = latch
        self.snap = snap
        self.conflicts = conflicts
        self.cstat = cstat
        self.now = now
        self.correlation_id = correlation_id

    @property
    def beat(self) -> int:
        return self.cstat.get("beat", 0) if self.cstat else 0


# ─────────────────────────────── the organ pipeline ─────────────────────────────
class TickPipeline:
    """The ordered organ sequence transplanted from organism.py:452-812. Owns the
    cross-tick carry-state that used to be loop-locals (last_daily, next_epoch_at,
    _last_sigma, _last_afferent_ratio, _ziman_last). run(ctx) is byte-equivalent in
    behavior to today's inline block; only its host thread changed."""

    def __init__(self) -> None:
        self.last_daily: str = ""
        self.next_epoch_at: float = 0.0
        self.last_sigma: float = 0.0
        self.last_afferent_ratio: float = 1.0
        self.ziman_last: Optional[dict] = None
        self.protective_skip: bool = False

    def run(self, ctx: BeatContext) -> None:
        w = ctx.wired.w
        chrono = ctx.wired.chrono
        snap = ctx.snap
        conflicts = ctx.conflicts
        _cstat = ctx.cstat
        now = ctx.now
        latch = ctx.latch
        beat = ctx.beat
        self.protective_skip = False
        prot_state: dict = {}

        # ── neural reflex + protective override (organism.py:452-502) ─────────────
        _rhythm_state = None
        _circadian_state = None
        if ctx.wired.rhythm is not None:
            try:
                _budget_pct = opslib.usd(snap["month"].get("musd", 0)) / max(
                    opslib.load_budgets().get("global", {}).get("cap_monthly", 30), 1)
                _rhythm_state = w.rhythm_beat(ctx.wired.rhythm, readiness=0.6,
                                              stress=min(1.0, _budget_pct * 2),
                                              novelty=0.3, sigma=0.5)
            except Exception:  # noqa: BLE001
                _rhythm_state = None
        if ctx.wired.circadian is not None:
            try:
                _circadian_state = w.circadian_readiness(ctx.wired.circadian)
            except Exception:  # noqa: BLE001
                _circadian_state = None
        if ctx.wired.neural_stack is not None:
            try:
                _err_rate = 0.0
                try:
                    _sj = json.loads((opslib.STATE_DIR / "cortex" / "stress-latest.json")
                                     .read_text("utf-8"))
                    _err_rate = min(1.0, max(0.0, float(_sj.get("organism_stress", 0.0) or 0.0)))
                except Exception:  # noqa: BLE001
                    _err_rate = 0.0
                _neural_r = w.neural_beat(ctx.wired.neural_stack, beat, {
                    "rhythm": _rhythm_state or ({"chrono": _cstat} if _cstat else {}).get("chrono", {}),
                    "budget": {"pct": opslib.usd(snap["month"].get("musd", 0)) / max(
                        opslib.load_budgets().get("global", {}).get("cap_monthly", 30), 1)},
                    "spectral": {"sigma": self.last_sigma},
                    "sensory": {"afferent_ratio": self.last_afferent_ratio,
                                "error_rate": _err_rate},
                })
                if _neural_r:
                    _prot = w.protective_override(_neural_r)
                    if _prot.get("override") and not _prot.get("suppressible", True):
                        opslib.alert([f"NEURAL OVERRIDE: {_prot['reason']}"])
                        if _prot.get("action") == "protective_halt":
                            self.protective_skip = True
                            prot_state = {"protective_mode": True,
                                          "protective_reason": _prot["reason"]}
                            opslib.heartbeat(f"PROTECTIVE HALT: {_prot['reason']}")
                        elif _prot.get("action") == "throttle":
                            prot_state = {"protective_mode": "throttled",
                                          "protective_reason": _prot["reason"]}
                            self.next_epoch_at = now + 600
            except Exception as _ne:  # noqa: BLE001
                opslib.alert([f"neural wiring error (non-fatal): {type(_ne).__name__}: {_ne}"])

        _protective_skip = self.protective_skip

        # ── epoch (organism.py:505-511) ──────────────────────────────────────────
        epoch_info: dict = {}
        if not _protective_skip and now >= self.next_epoch_at:
            try:
                import governor_epoch
                rec = governor_epoch.run_epoch()
                self.next_epoch_at = now + rec["next_epoch_minutes"] * 60
                epoch_info = {"last_epoch": rec["ts"], "pressure": rec["pressure"],
                              "next_epoch_minutes": rec["next_epoch_minutes"]}
            except Exception as _ge:  # noqa: BLE001
                opslib.alert([f"epoch error (non-fatal): {type(_ge).__name__}"])

        # ── stale-effect sweep (organism.py:513-523) ─────────────────────────────
        try:
            if chrono is not None:
                _db_path = opslib.STATE_DIR / "chrono.db"
                if _db_path.exists():
                    _cdb = chrono.ChronoDB(str(_db_path))
                    _gate = chrono.EffectorGate(db=_cdb)
                    _sw = _gate.sweep_stale_effects()
                    if _sw["refused"] > 0:
                        epoch_info["effect_sweep"] = _sw
        except Exception:  # noqa: BLE001
            pass

        # ── daily (organism.py:524-578) ──────────────────────────────────────────
        daily: dict = {}
        if not _protective_skip and opslib.today() != self.last_daily:
            try:
                import fitness
                import replication
                fit = fitness.compute()
                rep = replication.evaluate()
                self.last_daily = opslib.today()
                daily = {"fitness_authoritative": fit["authoritative"],
                         "sigma": rep["sigma"]["sigma_effective"],
                         "sigma_zone": rep["sigma"]["zone"]}
                try:
                    self.last_sigma = float(rep["sigma"]["sigma_effective"] or 0.0)
                except (TypeError, ValueError, KeyError):
                    pass
                try:
                    _lok, _lreason = opslib.genome_ledger().verify()
                    daily["ledger_ok"] = bool(_lok)
                    if not _lok:
                        opslib.alert([f"GENOME LEDGER verify FAILED: {_lreason}"])
                except Exception as _lve:  # noqa: BLE001
                    daily["ledger_ok"] = None
                    opslib.alert([f"ledger verify error (non-fatal): {type(_lve).__name__}"])
                opslib.ledger_note("ORGANISM_DAILY", {
                    "month_aud": snap["month"]["aud"],
                    "suspects": snap["suspect_zero_total"],
                    "sigma": rep["sigma"]["sigma_effective"],
                    "conflicts": len(conflicts)}, actor="organism")
                try:
                    w.reconcile_beat(day=opslib.today())
                except Exception:  # noqa: BLE001
                    opslib.alert(["reconcile_beat error (non-fatal)"])
                if w.flag("OCTOPUS_WIRE_FISHER"):
                    try:
                        import fisher as _fisher_mod
                        _fr = _fisher_mod.compute_fisher(write=True) or {}
                        daily["fisher_condition"] = _fr.get("fisher_condition_number")
                    except Exception as _fe:  # noqa: BLE001
                        opslib.alert([f"fisher advisory error (non-fatal): {type(_fe).__name__}: {_fe}"])
                if w.flag("OCTOPUS_WIRE_C6_RESEARCH"):
                    try:
                        import c6_trigger as _c6
                        _c6.seed_default_hypothesis()
                        _c6.c6_research_beat(state_dir=str(opslib.STATE_DIR),
                                             channel=ctx.wired.chan, beat=beat)
                    except Exception as _c6e:  # noqa: BLE001
                        opslib.alert([f"c6_research_beat error (non-fatal): {type(_c6e).__name__}: {_c6e}"])
            except Exception as _de:  # noqa: BLE001
                opslib.alert([f"daily beat error (non-fatal): {type(_de).__name__}: {_de}"])

        # ── doctor (organism.py:579-585) ─────────────────────────────────────────
        _doctor_result = None
        if not _protective_skip and ctx.wired.doctor is not None and _cstat is not None:
            try:
                _doctor_result = w.doctor_beat(ctx.wired.doctor, beat)
            except Exception:  # noqa: BLE001
                opslib.alert(["doctor_beat error (non-fatal)"])

        # ── doctor self-knowledge (organism.py:590-593; spawns its own daemon) ────
        try:
            w.doctor_selfknowledge_beat(beat=beat)
        except Exception as _ske:  # noqa: BLE001
            opslib.alert([f"doctor_selfknowledge_beat error (non-fatal): {type(_ske).__name__}"])

        # ── consolidation (organism.py:596-601) ──────────────────────────────────
        if not _protective_skip and ctx.wired.neural_stack is not None and _cstat is not None:
            try:
                w.consolidation_beat(ctx.wired.neural_stack,
                                     school_bridge=ctx.wired.school_bridge, beat=beat)
            except Exception as _ce:  # noqa: BLE001
                opslib.alert([f"consolidation_beat error (non-fatal): {type(_ce).__name__}: {_ce}"])

        # ── cockpit / tg-exec (organism.py:602-610) ──────────────────────────────
        if not _protective_skip:
            try:
                _tgx = w.cockpit_requests_beat(state_dir=str(opslib.STATE_DIR),
                                               doctor=ctx.wired.doctor, channel=ctx.wired.chan)
                if _tgx.get("ran"):
                    opslib.heartbeat(f"tg-exec ran: {_tgx['ran']}")
            except Exception as _qe:  # noqa: BLE001
                opslib.alert([f"cockpit_requests_beat error (non-fatal): {type(_qe).__name__}"])

        # ── afferent (organism.py:611-630) ───────────────────────────────────────
        _afferent_status = None
        if not _protective_skip and ctx.wired.sensory_bus is not None and _cstat is not None:
            try:
                _aff = w.afferent_beat(ctx.wired.sensory_bus,
                                       school_bridge=ctx.wired.school_bridge,
                                       snap=snap, beat=beat)
                if _aff and _aff.get("school_report"):
                    _afferent_status = _aff.get("sensory_status")
                if _aff and isinstance(_aff.get("sensory_status"), dict):
                    try:
                        _v = float(_aff["sensory_status"].get("afferent_ratio", 1.0))
                        if 0.0 <= _v <= 1.0:
                            self.last_afferent_ratio = _v
                    except (TypeError, ValueError):
                        pass
            except Exception as _ae:  # noqa: BLE001
                opslib.alert([f"afferent_beat error (non-fatal): {type(_ae).__name__}: {_ae}"])

        # ── publish tick signals (organism.py:631-643) ───────────────────────────
        if not _protective_skip and ctx.wired.live_loop is not None:
            try:
                _rh = _rhythm_state or ({"chrono": _cstat} if _cstat else {}).get("chrono") or None
                w.publish_tick_signals(ctx.wired.live_loop, beat=beat, rhythm_state=_rh,
                                       afferent_status=_afferent_status,
                                       doctor_result=_doctor_result)
            except Exception as _pe:  # noqa: BLE001
                opslib.alert([f"publish_tick_signals error (non-fatal): {type(_pe).__name__}: {_pe}"])

        # ── leg (organism.py:644-653) ────────────────────────────────────────────
        _leg_status = None
        if not _protective_skip and ctx.wired.leg is not None and ctx.wired.pacemaker is not None:
            try:
                _leg_status = w.leg_beat(ctx.wired.leg, pacemaker=ctx.wired.pacemaker, beat=beat)
            except Exception as _le:  # noqa: BLE001
                opslib.alert([f"leg_beat error (non-fatal): {type(_le).__name__}: {_le}"])

        # ── ziman (organism.py:654-665) ──────────────────────────────────────────
        _ziman_status = None
        if not _protective_skip and ctx.wired.ziman_leg is not None:
            try:
                _ziman_status = w.ziman_beat(ctx.wired.ziman_leg, beat=beat,
                                             doctor=ctx.wired.doctor)
            except Exception as _ze:  # noqa: BLE001
                opslib.alert([f"ziman_beat error (non-fatal): {type(_ze).__name__}: {_ze}"])
        self.ziman_last = _ziman_status or self.ziman_last

        # ── proposal router (organism.py:666-684) ────────────────────────────────
        _proposal_router = None
        _proposal_metrics = None
        if not _protective_skip and ctx.wired.live_loop is not None:
            try:
                _proposal_router = ctx.wired.live_loop.route_leg_proposals(
                    [x for x in (ctx.wired.leg, ctx.wired.ziman_leg,
                                 ctx.wired.cartographer_leg) if x is not None],
                    deliver=True, limit=5)
            except Exception as _pre:  # noqa: BLE001
                opslib.alert([f"proposal_router error (non-fatal): {type(_pre).__name__}: {_pre}"])
            try:
                # C7 (گامِ ۱۷): منبعِ عددها داخلِ خودِ `proposal_metrics()` تصحیح
                # شد — این‌جا هنوز همان زنجیرهٔ تک‌نویسنده است (latch →
                # organism._write_state) و عمداً نویسندهٔ دومی اضافه نمی‌شود.
                _proposal_metrics = ctx.wired.live_loop.proposal_metrics()
            except Exception as _pme:  # noqa: BLE001
                # کلید را **حذف** نکن: غیابش یعنی `_write_state.merge_prev` مقدارِ
                # چرخهٔ قبل را back-fill می‌کند و هم‌زمان `ts` سطحِ بالا را جلو
                # می‌برد — عددی کهنه که تازه به‌نظر می‌رسد (ناوردیِ ۴ ِ
                # `provenance`). UNKNOWNِ صریح بهتر از صفرِ بی‌صداست.
                _proposal_metrics = {"unknown": True, "reason": type(_pme).__name__}

        # ── cartographer (organism.py:686-695) ───────────────────────────────────
        _cartographer_status = None
        if not _protective_skip and ctx.wired.cartographer_leg is not None:
            try:
                _cartographer_status = w.cartographer_beat(ctx.wired.cartographer_leg, beat=beat)
            except Exception as _ce:  # noqa: BLE001
                opslib.alert([f"cartographer_beat error (non-fatal): {type(_ce).__name__}: {_ce}"])

        # ── business/asset/acct/email/harvest/lead/cultivation (organism.py:697-763)
        _biz_legs = _asset_map = _acct_beat = _lead_disc = _harvest = _legs_cult = None
        if not _protective_skip:
            try:
                _biz_legs = w.business_legs_beat(beat=beat, write=False)
            except Exception as _ble:  # noqa: BLE001
                opslib.alert([f"business_legs_beat error (non-fatal): {type(_ble).__name__}: {_ble}"])
            try:
                _asset_map = w.asset_map_beat(beat=beat)
            except Exception as _ame:  # noqa: BLE001
                opslib.alert([f"asset_map_beat error (non-fatal): {type(_ame).__name__}: {_ame}"])
            try:
                _acct_beat = w.acct_beat(beat=beat)
            except Exception as _acbe:  # noqa: BLE001
                opslib.alert([f"acct_beat error (non-fatal): {type(_acbe).__name__}: {_acbe}"])
            try:
                w.email_beat(beat=beat)
            except Exception as _eme:  # noqa: BLE001
                opslib.alert([f"email_beat error (non-fatal): {type(_eme).__name__}: {_eme}"])
            try:
                _harvest = w.harvest_beat(beat=beat)
            except Exception as _hve:  # noqa: BLE001
                opslib.alert([f"harvest_beat error (non-fatal): {type(_hve).__name__}: {_hve}"])
            try:
                _lead_disc = w.lead_discovery_beat(ctx.wired.leg, beat=beat)
            except Exception as _lde:  # noqa: BLE001
                opslib.alert([f"lead_discovery_beat error (non-fatal): {type(_lde).__name__}: {_lde}"])
            try:
                _legs_cult = w.legs_cultivation_beat(beat=beat,
                                                     sensory_bus=ctx.wired.sensory_bus,
                                                     school_bridge=ctx.wired.school_bridge)
            except Exception as _lce:  # noqa: BLE001
                opslib.alert([f"legs_cultivation_beat error (non-fatal): {type(_lce).__name__}: {_lce}"])
            # scheduler seed (organism.py:764-771)
            try:
                w.scheduler_seed_beat(doctor=ctx.wired.doctor, pacemaker=ctx.wired.pacemaker, beat=beat)
            except Exception as _sse:  # noqa: BLE001
                opslib.alert([f"scheduler_seed_beat error (non-fatal): {type(_sse).__name__}"])

        # ── idea / epistemics / heart (organism.py:772-793) ──────────────────────
        _heart_status = None
        if not _protective_skip and ctx.wired.idea_graph is not None and _cstat is not None:
            try:
                w.idea_beat(ctx.wired.idea_graph, beat=beat)
            except Exception as _ie:  # noqa: BLE001
                opslib.alert([f"idea_beat error (non-fatal): {type(_ie).__name__}: {_ie}"])
        if not _protective_skip and _cstat is not None:
            try:
                w.epistemics_beat(live_loop=ctx.wired.live_loop, beat=beat)
            except Exception as _ee:  # noqa: BLE001
                opslib.alert([f"epistemics_beat error (non-fatal): {type(_ee).__name__}: {_ee}"])
        if not _protective_skip and _cstat is not None:
            try:
                _heart_status = w.heart_beat(beat=beat, snap=snap)
            except Exception as _hbe:  # noqa: BLE001
                opslib.alert([f"heart_beat error (non-fatal): {type(_hbe).__name__}: {_hbe}"])

        # ── nudges / digests (organism.py:794-812) — telegram IO ─────────────────
        if not _protective_skip and _cstat is not None:
            try:
                w.needs_nudge_beat(ctx.wired.chan, beat=beat)
                w.discovery_nudge_beat(ctx.wired.chan, beat=beat)
                w.heartbeat_summary_beat(ctx.wired.chan, beat=beat)
                w.cortex_vitals_beat(beat=beat)
                w.doctor_digest_beat(ctx.wired.chan, beat=beat)
                w.brain_digest_beat(ctx.wired.chan, beat=beat)
                w.heart_card_beat(ctx.wired.chan, beat=beat)
            except Exception as _nne:  # noqa: BLE001
                opslib.alert([f"needs_nudge error (non-fatal): {type(_nne).__name__}: {_nne}"])

        # ── publish organ blocks into the latch (metabolic core does the disk write) ─
        block: dict = {"protective_skip": _protective_skip, **prot_state,
                       **epoch_info, **daily}
        if _leg_status:            block["leg"] = _leg_status
        if _ziman_status or self.ziman_last:
            block["ziman"] = _ziman_status or self.ziman_last
        if _cartographer_status:   block["cartographer"] = _cartographer_status
        if _biz_legs:              block["business_legs"] = _biz_legs
        if _asset_map:             block["asset_map"] = _asset_map
        if _acct_beat:             block["accounting"] = _acct_beat
        if _lead_disc:             block["lead_discovery"] = _lead_disc
        if _harvest:               block["harvest"] = _harvest
        if _proposal_router:       block["proposal_router"] = _proposal_router
        if _proposal_metrics is not None:
            block["proposal_metrics"] = _proposal_metrics
        if _legs_cult:             block["legs_cultivation"] = _legs_cult
        if _heart_status:          block["heart"] = _heart_status
        latch.update(block)


# ─────────────────────────────── the worker pool ────────────────────────────────
class BrainWorkerPool:
    """Bounded queue + supervised daemon worker(s). The metabolic core is the producer
    (submit_*), the workers are consumers. Crash-isolated at task and thread level."""

    def __init__(self, wired: Wired, latch: StateLatch, *,
                 n_workers: int | None = None) -> None:
        self.wired = wired
        self.latch = latch
        self.n_workers = max(1, n_workers if n_workers is not None
                             else _envi("OCTOPUS_BRAIN_WORKERS", 1))
        self.q: "queue.Queue[tuple]" = queue.Queue(maxsize=_envi("OCTOPUS_BRAIN_QUEUE_MAX", 4))
        self.pipeline = TickPipeline()
        self._tick_lock = threading.Lock()   # only one tick cycle at a time (order safety)
        self._stop = threading.Event()
        self._threads: list[threading.Thread] = []
        self._restart_log: list[float] = []
        self._restart_max = _envi("OCTOPUS_BRAIN_RESTART_MAX", 3)
        self._restart_window = _envi("OCTOPUS_BRAIN_RESTART_WINDOW_S", 300)

    # ---- producer side (called by the metabolic core; never blocks) --------------
    def submit_tick(self, ctx: BeatContext) -> bool:
        return self._offer(("tick", ctx))

    def submit_cockpit(self) -> bool:
        """Immediate owner-command handling — the latency payoff. Enqueues a cockpit
        task a free worker runs within seconds instead of waiting for the next tick."""
        return self._offer(("cockpit", None))

    def submit(self, kind: str, payload: Any = None) -> bool:
        return self._offer((kind, payload))

    def _offer(self, item: tuple) -> bool:
        if self._stop.is_set():
            return False
        try:
            self.q.put_nowait(item)
            return True
        except queue.Full:
            # overloaded: previous cycle still running. Coalesce/drop — harmless
            # (cadence-gated, idempotent; durability is in chrono.db/ledger).
            opslib.alert(["brain queue full — coalesced a tick (workers overloaded)"])
            return False

    # ---- consumer side ----------------------------------------------------------
    def start(self) -> "BrainWorkerPool":
        for i in range(self.n_workers):
            self._spawn(i)
        opslib.heartbeat(f"brain-workers=START n={self.n_workers} "
                         f"qmax={self.q.maxsize}")
        return self

    def _spawn(self, idx: int) -> None:
        t = threading.Thread(target=self._supervise, args=(idx,), daemon=True,
                             name=f"brain-worker-{idx}")
        t.start()
        self._threads.append(t)

    def _supervise(self, idx: int) -> None:
        """Per-thread layer: if the worker loop escapes, restart it under a breaker so a
        worker crash can never become a silent stall — and never touches the core."""
        while not self._stop.is_set():
            try:
                self._worker_loop(idx)
                return   # clean exit on stop
            except Exception as e:  # noqa: BLE001 — should be unreachable (loop is guarded)
                now_s = time.time()
                self._restart_log = [t for t in self._restart_log
                                     if now_s - t < self._restart_window]
                if len(self._restart_log) >= self._restart_max:
                    self.latch.set("workers_down",
                                   f"brain-worker breaker tripped: {type(e).__name__}")
                    opslib.alert([f"brain-worker {idx} breaker tripped — "
                                  f"NOT restarting ({type(e).__name__}: {e})"])
                    return
                self._restart_log.append(now_s)
                opslib.alert([f"brain-worker {idx} crashed, restarting "
                              f"({type(e).__name__}: {e})"])

    def _worker_loop(self, idx: int) -> None:
        while not self._stop.is_set():
            try:
                kind, payload = self.q.get(timeout=1.0)
            except queue.Empty:
                continue
            # per-task layer + one correlation id per cycle
            _tok = _events.begin_run() if _events is not None else None
            try:
                self._dispatch(kind, payload)
            except Exception as e:  # noqa: BLE001 — a task must never kill the worker
                opslib.alert([f"brain task '{kind}' error (non-fatal): "
                              f"{type(e).__name__}: {e}"])
            finally:
                if _events is not None:
                    _events.end_run(_tok)
                self.q.task_done()

    def _dispatch(self, kind: str, payload: Any) -> None:
        # kill is supreme — refuse work under STOP/halt (defense in depth; each beat and
        # EffectorGate re-check independently too).
        if opslib.STOP_ORGANISM.exists() or opslib.halted():
            return
        if kind == "tick":
            ctx: BeatContext = payload
            # only one tick cycle runs at a time regardless of worker count (order safety)
            with self._tick_lock:
                self.pipeline.run(ctx)
        elif kind == "cockpit":
            try:
                _tgx = self.wired.w.cockpit_requests_beat(
                    state_dir=str(opslib.STATE_DIR), doctor=self.wired.doctor,
                    channel=self.wired.chan)
                if _tgx.get("ran"):
                    opslib.heartbeat(f"tg-exec (immediate) ran: {_tgx['ran']}")
            except Exception as _qe:  # noqa: BLE001
                opslib.alert([f"cockpit (immediate) error (non-fatal): {type(_qe).__name__}"])
        # unknown kinds are ignored (fail-soft)

    def workers_alive(self) -> int:
        return sum(1 for t in self._threads if t.is_alive())

    def stop(self, join_timeout: float | None = None) -> None:
        """Signal + join workers. Daemon threads → process exit is clean regardless;
        this just gives in-flight tasks a bounded chance to finish."""
        self._stop.set()
        jt = join_timeout if join_timeout is not None else _envi("OCTOPUS_BRAIN_STOP_JOIN_S", 5)
        for t in self._threads:
            try:
                t.join(timeout=jt)
            except Exception:  # noqa: BLE001
                pass


def start_pool(wired: Wired, latch: StateLatch) -> Optional[BrainWorkerPool]:
    """Boot entry point for organism.py. flag off → None (inline pipeline stays).
    fail-soft: any failure returns None so the organism falls back to inline behavior."""
    if not flag_on():
        return None
    try:
        return BrainWorkerPool(wired, latch).start()
    except Exception as e:  # noqa: BLE001 — a broken pool must not break boot
        opslib.alert([f"brain-worker pool start failed (non-fatal): {type(e).__name__}: {e}"])
        return None
