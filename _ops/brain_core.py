#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""brain_core.py — C7 Slice 4 (C7.1 repair): ریشهٔ ترکیبِ ضربانِ سایه با **parityِ واقعی**.

BeatScheduler را از «harnessِ روی میز» به سیستمِ عصبیِ سایه‌ی production-wired تبدیل می‌کند —
پشتِ OCTOPUS_ONE_HEARTBEAT=0. adapterهای **واقعیِ read-only** ثبت می‌شوند؛ loopهای قدیمی
authoritative می‌مانند.

--- درسِ بازبینیِ C7.1 (چرا نسخهٔ اول false-parity بود) ---
  * ParityTracker تعریف شده بود ولی build_shadow_scheduler هرگز آن را نمی‌ساخت/صدا نمی‌زد
    → صفر مقایسهٔ واقعی؛ ۲۴ ساعت اجرا هم parityِ بی‌معنا (B11).
  * PARITY-GREEN با `compared>=100` سبز می‌شد — بدونِ هیچ سنجهٔ زمانی → پیش از ۲۴ ساعت سبز (B12).
  * وضعیتِ BrainCore در ORGANISM-STATE نبود (B13).

--- طراحیِ درست (C7.1) ---
  * هر organِ **comparable** (SENSE/RECORD) در **مسیرِ tick**، دو مقدارِ **مستقل** را compare می‌کند:
    legacy (artifactِ اقتدارِ legacy) در برابر shadow (محاسبهٔ مستقلِ خودِ سایه). **صفر self-comparison.**
  * organهای advisory (THINK/HEAL) فقط snapshot می‌کنند (cortex/doctor **دوباره اجرا نمی‌شوند**)؛
    در parityِ gate شرکت نمی‌کنند (صادقانه: «آنچه دوباره محاسبه نمی‌کنیم را parity نمی‌سنجیم»).
  * missing_old/missing_new از mismatched **جدا** شمرده می‌شوند.
  * **PARITY-GREEN فقط با: flag روشن + soakِ پیوستهٔ ≥۲۴h + نمونهٔ کافی + صفر mismatch + صفر
    critical-mismatch + بدونِ gapِ خارج از سیاست.** `compared>=N` به‌تنهایی ممنوع.
  * telemetryِ soak (started_at/last_sample_at/continuous_elapsed_s/restart_gaps/per-organ) durable.
  * **صفر ACT** در سایه؛ هر دو flag پیش‌فرض OFF.
"""
from __future__ import annotations

import hashlib
import json
import os
import sqlite3
import sys
import time
from pathlib import Path

_HERE = Path(__file__).resolve().parent
for _p in (str(_HERE), str(_HERE / "budget")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

FLAG = "OCTOPUS_ONE_HEARTBEAT"
SOAK_MIN_HOURS = 24.0                 # PARITY-GREEN پیش از این هرگز (B12)
MIN_SAMPLES = 100                     # حداقلِ نمونهٔ matched برای green
MIN_ORGAN_SAMPLES = 20               # حداقلِ نمونه per organِ comparable
MAX_RESTART_GAP_S = 3600.0           # gapِ بزرگ‌تر = گسستِ پیوستگی → started_at ری‌ست
# Only typed same-contract comparisons may gate promotion.  Stream-count observations
# are coverage telemetry, not parity, because events.jsonl and spine.db are not 1:1.
REQUIRED_COMPARATORS = frozenset({"health-contract-v1"})
HEALTH_CONTRACT_SCHEMA = "health-contract.v1:afferent_ratio>=0.5&&!protective_halt"


def flag_on() -> bool:
    return str(os.environ.get(FLAG, "")).strip().lower() in ("1", "true", "yes", "on")


def _state_dir():
    try:
        import opslib  # noqa: WPS433
        return Path(opslib.STATE_DIR)
    except Exception:  # noqa: BLE001
        return _HERE / "state"


def _parity_path(sd):
    return Path(sd) / "pulse" / "beat-parity.json"


def _norm(x):
    """نرمال‌سازیِ خروجی برای مقایسهٔ parity (کلیدهای مرتب، عددهای گرد؛ ts/beat حذف)."""
    if isinstance(x, dict):
        return {k: _norm(v) for k, v in sorted(x.items()) if k not in ("ts", "beat", "_rank", "at")}
    if isinstance(x, float):
        return round(x, 4)
    if isinstance(x, list):
        return [_norm(v) for v in x]
    return x


class ParityTracker:
    """شمارنده‌ها + telemetryِ soak. compare() دو مقدارِ مستقل را می‌سنجد. durable. clock تزریق‌پذیر."""

    def __init__(self, state_dir=None, clock=None):
        self.sd = Path(state_dir) if state_dir else _state_dir()
        self._clock = clock or (lambda: time.time())
        self.counters = {"compared": 0, "matched": 0, "mismatched": 0,
                         "missing_old": 0, "missing_new": 0, "critical_mismatched": 0}
        self.started_at = None
        self.last_sample_at = None
        self.restart_gaps = []
        self.per_organ = {}
        self.mismatches = []
        self.soak_fingerprint = self._fingerprint()
        self._load()

    @staticmethod
    def _fingerprint() -> str:
        """Pin code/schema/config for the whole soak; any change restarts the clock."""
        try:
            code_hash = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
        except OSError:
            code_hash = "unreadable"
        canon = json.dumps({"schema": HEALTH_CONTRACT_SCHEMA,
                            "required": sorted(REQUIRED_COMPARATORS),
                            "min_samples": MIN_SAMPLES,
                            "min_organ_samples": MIN_ORGAN_SAMPLES,
                            "max_gap": MAX_RESTART_GAP_S,
                            "code_sha256": code_hash}, sort_keys=True)
        return hashlib.sha256(canon.encode("utf-8")).hexdigest()

    def _load(self):
        try:
            p = _parity_path(self.sd)
            if p.exists():
                d = json.loads(p.read_text("utf-8"))
                if d.get("soak_fingerprint") != self.soak_fingerprint:
                    return  # code/schema/config changed: never inherit an old green soak
                self.counters.update(d.get("counters", {}))
                self.started_at = d.get("started_at")
                self.last_sample_at = d.get("last_sample_at")
                self.restart_gaps = d.get("restart_gaps", []) or []
                self.per_organ = d.get("per_organ", {}) or {}
        except Exception:  # noqa: BLE001
            pass

    def compare(self, name, legacy, shadow, *, critical=False, now=None) -> str:
        """legacy/shadow (دو منبعِ **مستقل**) را نرمال و مقایسه کن.
        خروجی: matched | mismatched | missing_old | missing_new. missing از mismatch جدا است."""
        n = now if now is not None else self._clock()
        # ── telemetryِ soakِ پیوسته: gapِ بزرگ = گسست → started_at ری‌ست (B12) ──
        if self.started_at is None:
            self.started_at = n
        elif self.last_sample_at is not None:
            gap = n - float(self.last_sample_at)
            if gap > MAX_RESTART_GAP_S:
                self.restart_gaps.append({"gap_s": round(gap, 1), "at": n})
                self.started_at = n            # پیوستگی شکست → soakِ ۲۴ساعته از نو
        self.last_sample_at = n
        self.counters["compared"] += 1
        self.per_organ[str(name)[:32]] = self.per_organ.get(str(name)[:32], 0) + 1
        if legacy is None:
            self.counters["missing_old"] += 1
            r = "missing_old"
        elif shadow is None:
            self.counters["missing_new"] += 1
            r = "missing_new"
        elif _norm(legacy) == _norm(shadow):
            self.counters["matched"] += 1
            r = "matched"
        else:
            self.counters["mismatched"] += 1
            if critical:
                self.counters["critical_mismatched"] += 1
            # فقط طبقهٔ ساختاری، نه محتوای خام (ضدِ PII/secret)
            self.mismatches.append({"organ": str(name)[:32],
                                    "class": "critical" if critical else "normal"})
            r = "mismatched"
        self._persist()
        return r

    def continuous_elapsed_s(self, now=None) -> float:
        if self.started_at is None:
            return 0.0
        n = now if now is not None else self._clock()
        return max(0.0, n - float(self.started_at))

    def _persist(self):
        try:
            p = _parity_path(self.sd)
            p.parent.mkdir(parents=True, exist_ok=True)
            tmp = p.with_suffix(".tmp")
            tmp.write_text(json.dumps({
                "counters": self.counters, "started_at": self.started_at,
                "last_sample_at": self.last_sample_at, "restart_gaps": self.restart_gaps[-20:],
                "per_organ": self.per_organ, "recent_mismatch": self.mismatches[-10:],
                "continuous_elapsed_s": round(self.continuous_elapsed_s(), 1),
                "soak_fingerprint": self.soak_fingerprint},
                ensure_ascii=False), "utf-8")
            os.replace(tmp, p)
        except Exception:  # noqa: BLE001
            pass

    def status(self, now=None) -> str:
        """HARNESS (flag خاموش) / SHADOW-LIVE (روشن، هنوز green نه) / PARITY-GREEN.
        PARITY-GREEN فقط با soakِ پیوستهٔ ≥۲۴h + نمونهٔ کافی + صفر mismatch/critical/missing_new."""
        if not flag_on():
            return "HARNESS"
        c = self.counters
        elapsed = self.continuous_elapsed_s(now)
        required_present = set(REQUIRED_COMPARATORS).issubset(set(self.per_organ))
        required_samples = all(self.per_organ.get(name, 0) >= MIN_ORGAN_SAMPLES
                               for name in REQUIRED_COMPARATORS)
        fresh = (self.last_sample_at is not None and
                 elapsed >= 0 and
                 (float(now if now is not None else self._clock()) -
                  float(self.last_sample_at)) <= MAX_RESTART_GAP_S)
        green = (elapsed >= SOAK_MIN_HOURS * 3600.0
                 and c["matched"] >= MIN_SAMPLES
                 and c["mismatched"] == 0
                 and c["critical_mismatched"] == 0
                 and c["missing_old"] == 0
                 and c["missing_new"] == 0
                 and required_present and required_samples and fresh)
        return "PARITY-GREEN" if green else "SHADOW-LIVE"

    def soak_report(self, now=None) -> dict:
        return {"status": self.status(now), "counters": dict(self.counters),
                "started_at": self.started_at, "last_sample_at": self.last_sample_at,
                "continuous_elapsed_s": round(self.continuous_elapsed_s(now), 1),
                "soak_min_hours": SOAK_MIN_HOURS, "restart_gaps": len(self.restart_gaps),
                "per_organ_samples": dict(self.per_organ),
                "required_comparators": sorted(REQUIRED_COMPARATORS),
                "soak_fingerprint": self.soak_fingerprint,
                "schema": HEALTH_CONTRACT_SCHEMA}


# ── adapterهای واقعیِ read-only ─────────────────────────────────────────────────
def _read_json(p):
    try:
        return json.loads(Path(p).read_text("utf-8"))
    except Exception:  # noqa: BLE001
        return None


def _spine_count(sd):
    db = Path(sd) / "spine" / "spine.db"
    if not db.exists():
        return None
    try:
        c = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
        n = c.execute("SELECT COUNT(*) FROM events").fetchone()[0]
        c.close()
        return n
    except sqlite3.Error:
        return None


def _events_jsonl_count(sd):
    p = Path(sd) / "events.jsonl"
    if not p.exists():
        return None
    try:
        return sum(1 for ln in p.read_text("utf-8").splitlines() if ln.strip())
    except OSError:
        return None


def make_sense_adapter(sd, parity):
    def sense(**kw):
        """Typed same-input contract comparison.

        Both implementations consume one immutable snapshot/correlation ID. This does not
        compare unrelated stream totals and is explicitly versioned by HEALTH_CONTRACT_SCHEMA.
        """
        sig = _read_json(Path(sd) / "pulse" / "heart-signals-latest.json")
        legacy_alive = shadow_alive = None
        if isinstance(sig, dict) and sig:
            ratio = sig.get("afferent_ratio")
            halt = bool(sig.get("protective_halt"))
            if ratio is not None:
                # Independent implementations of the same typed contract.
                legacy_alive = False if halt else (float(ratio) >= 0.5)
                shadow_alive = (not halt) and not (float(ratio) < 0.5)
        parity.compare("health-contract-v1", legacy_alive, shadow_alive, critical=True)
        return {"organ": "sense", "contract": HEALTH_CONTRACT_SCHEMA,
                "correlation_id": (sig or {}).get("correlation_id"),
                "shadow_alive": shadow_alive}
    return sense


def make_record_adapter(sd, parity):
    def record(**kw):
        """Coverage/freshness observation only — deliberately excluded from parity gate.

        events.jsonl and spine.db have different taxonomies and cardinality, so comparing
        their totals as if equivalent was a false-green/false-red metric.  We surface both
        counts honestly without calling ``parity.compare``.
        """
        shadow_n = _spine_count(sd)
        legacy_n = _events_jsonl_count(sd)
        return {"organ": "record", "metric": "COVERAGE",
                "spine_events": shadow_n, "legacy_event_lines": legacy_n}
    return record


def make_think_adapter(sd):
    def think(**kw):
        """THINK (advisory-only): snapshotِ خروجیِ آخرِ cortex. **cortex را دوباره اجرا نمی‌کند**
        → محاسبهٔ مستقلِ سایه‌ای وجود ندارد → در parity شرکت نمی‌کند (صادقانه، نه fake-match)."""
        cs = _read_json(Path(sd) / "cortex" / "cortex-state.json") or {}
        return {"organ": "think", "cortex_seen": bool(cs),
                "cycle": cs.get("cycle") if isinstance(cs, dict) else None, "advisory": True}
    return think


def make_heal_adapter(sd):
    def heal(**kw):
        """HEAL (advisory-only): snapshotِ RFCِ doctor. doctor را دوباره اجرا نمی‌کند → parity نه."""
        rf = _read_json(Path(sd) / "doctor" / "rfcs.json") or {}
        rfcs = rf.get("rfcs", []) if isinstance(rf, dict) else []
        return {"organ": "heal", "rfc_count": len(rfcs) if isinstance(rfcs, list) else 0,
                "advisory": True}
    return heal


def build_shadow_scheduler(*, state_dir=None, spine=None, clock=None, halted_fn=None):
    """ریشهٔ ترکیب: یک BeatScheduler + ۴ adapterِ read-only + ParityTracker **سیم‌کشی‌شده در tick**.
    **صفر ACT.** flag خاموش → None. tracker روی scheduler به‌عنوان `.parity` قرار می‌گیرد."""
    if not flag_on():
        return None
    import beat_scheduler as _bs  # noqa: WPS433
    sd = Path(state_dir) if state_dir else _state_dir()
    sch = _bs.BeatScheduler(state_path=Path(sd) / "pulse" / "beat-state.json",
                            clock=clock, spine=spine, halted_fn=halted_fn,
                            production_safe=True)
    parity = ParityTracker(state_dir=sd, clock=clock)
    sch.parity = parity                                     # در tick از طریقِ handlerها compare می‌شود
    sch.register_organ("health", "SENSE", make_sense_adapter(sd, parity), every_n_beats=1,
                       budget_ms=500, read_set=("pulse/heart-signals-latest.json",),
                       write_set=("beat-parity",))
    sch.register_organ("spine-observe", "RECORD", make_record_adapter(sd, parity), every_n_beats=1,
                       budget_ms=500, read_set=("spine/spine.db", "events.jsonl"),
                       write_set=("system.beat",))
    sch.register_organ("cortex-advisory", "THINK", make_think_adapter(sd), every_n_beats=3,
                       budget_ms=1000, read_set=("cortex/cortex-state.json",), write_set=())
    sch.register_organ("doctor-advisory", "HEAL", make_heal_adapter(sd), every_n_beats=5,
                       budget_ms=500, read_set=("doctor/rfcs.json",), write_set=())
    # ناوردی: هیچ organ در فازِ ACT ثبت نشده (صفر double-actuation)
    assert not any(o.phase in ("ACT", "LEARN") for o in sch._organs), \
        "shadow: no ACT/LEARN organ without transactional outbox"  # noqa: S101
    return sch


def registered_organ_phases(sch) -> list:
    return sorted({o.phase for o in sch._organs}) if sch else []


def organism_state_block(state_dir=None, sched=None) -> dict:
    """C7.1 (B13): بلوکِ وضعیتِ BrainCore برای ORGANISM-STATE. از فایل‌های durable می‌خواند
    (parity + beat-state) تا حتی وقتی tracker زنده نیست هم صادق باشد. برچسب: HARNESS (flag خاموش)
    / SHADOW-LIVE (روشن، پیش از green) / PARITY-GREEN (فقط gateِ ۲۴ساعتهٔ واقعی)."""
    sd = Path(state_dir) if state_dir else _state_dir()
    try:
        parity = sched.parity if (sched is not None and getattr(sched, "parity", None)) \
            else ParityTracker(state_dir=sd)
        report = parity.soak_report()
    except Exception:  # noqa: BLE001
        report = {"status": "HARNESS" if not flag_on() else "SHADOW-LIVE"}
    bs_state = _read_json(_parity_path(sd).parent / "beat-state.json") or {}
    return {"mode": report.get("status", "HARNESS"),
            "flag_on": flag_on(),
            "beat": bs_state.get("committed_counter", bs_state.get("beat_counter")),
            "degraded": (bs_state.get("current") or {}).get("status") in ("RESERVED", "DEGRADED"),
            "parity": report}
