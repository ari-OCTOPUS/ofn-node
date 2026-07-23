#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""brain_core.py — C7 Slice 4: ریشهٔ ترکیبِ ضربانِ سایه (shadow composition root).

BeatScheduler را از «harnessِ روی میز» به یک سیستمِ عصبیِ **سایه‌ی production-wired** تبدیل
می‌کند — بدونِ big-bang، پشتِ OCTOPUS_ONE_HEARTBEAT=0. adapterهای **واقعیِ read-only/advisory**
ثبت می‌شوند؛ loopهای قدیمی همچنان authoritative می‌مانند.

اصولِ سخت (مأموریت Slice 4):
  - organism دقیقاً **یک** scheduler دارد (وقتی فلگ روشن است).
  - adapterها **read-only** legacy را snapshot می‌کنند؛ **هیچ loopِ پول‌دار/دومِ cortex** استارت
    نمی‌شود (فقط خروجیِ آخرِ cortex/doctor را می‌خوانند، دوباره اجرا نمی‌کنند).
  - **صفر ACT registration** در سایه؛ handlerها فقط artifactِ parity + system.beat می‌نویسند.
  - parity: شمارنده‌های rolling (compared/matched/mismatched/missing_old/missing_new) + دلیلِ
    mismatchِ پایدار (بدونِ PII/secret).
  - statusِ صادق: HARNESS / SHADOW-LIVE / PARITY-GREEN.
  - persistence-hardening از beat_scheduler به ارث می‌رسد (بدونِ هویتِ durable → بدونِ commit).
"""
from __future__ import annotations

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


class ParityTracker:
    """شمارنده‌های parity + ثبتِ mismatch (بدونِ PII). durable."""

    def __init__(self, state_dir=None):
        self.sd = Path(state_dir) if state_dir else _state_dir()
        self.counters = {"compared": 0, "matched": 0, "mismatched": 0,
                         "missing_old": 0, "missing_new": 0}
        self.mismatches = []
        self._load()

    def _load(self):
        try:
            p = _parity_path(self.sd)
            if p.exists():
                d = json.loads(p.read_text("utf-8"))
                self.counters.update(d.get("counters", {}))
        except Exception:  # noqa: BLE001
            pass

    def compare(self, name, old, new) -> str:
        """old/new را نرمال و مقایسه کن. خروجی: matched|mismatched|missing_old|missing_new."""
        self.counters["compared"] += 1
        if old is None:
            self.counters["missing_old"] += 1
            r = "missing_old"
        elif new is None:
            self.counters["missing_new"] += 1
            r = "missing_new"
        elif _norm(old) == _norm(new):
            self.counters["matched"] += 1
            r = "matched"
        else:
            self.counters["mismatched"] += 1
            # فقط دلیلِ ساختاری، نه محتوای خام (ضدِ PII/secret)
            self.mismatches.append({"organ": str(name)[:32], "reason": "normalized-output-differs"})
            r = "mismatched"
        self._persist()
        return r

    def _persist(self):
        try:
            p = _parity_path(self.sd)
            p.parent.mkdir(parents=True, exist_ok=True)
            tmp = p.with_suffix(".tmp")
            tmp.write_text(json.dumps({"counters": self.counters,
                                       "recent_mismatch": self.mismatches[-10:]},
                                      ensure_ascii=False), "utf-8")
            os.replace(tmp, p)
        except Exception:  # noqa: BLE001
            pass

    def status(self) -> str:
        """HARNESS (فلگ خاموش) / SHADOW-LIVE (روشن، هنوز parity کافی نه) / PARITY-GREEN."""
        if not flag_on():
            return "HARNESS"
        c = self.counters
        if c["compared"] >= 100 and c["mismatched"] == 0 and c["missing_new"] == 0:
            return "PARITY-GREEN"
        return "SHADOW-LIVE"


def _norm(x):
    """نرمال‌سازیِ خروجی برای مقایسهٔ parity (کلیدهای مرتب، عددهای گرد)."""
    if isinstance(x, dict):
        return {k: _norm(v) for k, v in sorted(x.items()) if k not in ("ts", "beat", "_rank")}
    if isinstance(x, float):
        return round(x, 4)
    if isinstance(x, list):
        return [_norm(v) for v in x]
    return x


# ── adapterهای واقعیِ read-only (snapshotِ خروجیِ legacy — نه اجرای دوباره) ───────
def _read_json(p):
    try:
        return json.loads(Path(p).read_text("utf-8"))
    except Exception:  # noqa: BLE001
        return None


def make_sense_adapter(sd):
    def sense(**kw):
        """SENSE: snapshotِ سلامت/تلمتری (read-only)."""
        hs = _read_json(Path(sd) / "pulse" / "heartstate-latest.json") or {}
        return {"organ": "sense", "health": bool(hs), "keys": sorted(list(hs))[:5]}
    return sense


def make_record_adapter(sd):
    def record(**kw):
        """RECORD: مشاهدهٔ spine (تعداد رویداد، read-only). خودِ system.beat را scheduler می‌زند."""
        db = Path(sd) / "spine" / "spine.db"
        n = None
        if db.exists():
            try:
                c = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
                n = c.execute("SELECT COUNT(*) FROM events").fetchone()[0]
                c.close()
            except sqlite3.Error:
                n = None
        return {"organ": "record", "spine_events": n}
    return record


def make_think_adapter(sd):
    def think(**kw):
        """THINK: snapshotِ **خروجیِ آخرِ** cortex (read-only) — **cortex را دوباره اجرا نمی‌کند**
        (بدونِ loopِ دومِ پول‌دار). فقط آنچه legacy تولید کرده را می‌خواند."""
        cs = _read_json(Path(sd) / "cortex" / "cortex-state.json") or {}
        return {"organ": "think", "cortex_seen": bool(cs),
                "cycle": cs.get("cycle") if isinstance(cs, dict) else None}
    return think


def make_heal_adapter(sd):
    def heal(**kw):
        """HEAL: snapshotِ سلامت/RFCِ doctor (read-only) — doctor را دوباره اجرا نمی‌کند."""
        rf = _read_json(Path(sd) / "doctor" / "rfcs.json") or {}
        rfcs = rf.get("rfcs", []) if isinstance(rf, dict) else []
        return {"organ": "heal", "rfc_count": len(rfcs) if isinstance(rfcs, list) else 0}
    return heal


def build_shadow_scheduler(*, state_dir=None, spine=None, clock=None, halted_fn=None):
    """ریشهٔ ترکیب: یک BeatScheduler با ۴ adapterِ read-only. **صفر ACT.** فلگ خاموش → None."""
    if not flag_on():
        return None
    import beat_scheduler as _bs  # noqa: WPS433
    sd = Path(state_dir) if state_dir else _state_dir()
    sch = _bs.BeatScheduler(state_path=Path(sd) / "pulse" / "beat-state.json",
                            clock=clock, spine=spine, halted_fn=halted_fn)
    sch.register_organ("health", "SENSE", make_sense_adapter(sd), every_n_beats=1, budget_ms=500,
                       read_set=("pulse/heartstate-latest.json",), write_set=("beat-parity",))
    sch.register_organ("spine-observe", "RECORD", make_record_adapter(sd), every_n_beats=1,
                       budget_ms=500, read_set=("spine/spine.db",), write_set=("system.beat",))
    sch.register_organ("cortex-advisory", "THINK", make_think_adapter(sd), every_n_beats=3,
                       budget_ms=1000, read_set=("cortex/cortex-state.json",), write_set=())
    sch.register_organ("doctor-advisory", "HEAL", make_heal_adapter(sd), every_n_beats=5,
                       budget_ms=500, read_set=("doctor/rfcs.json",), write_set=())
    # ناوردی: هیچ organ در فازِ ACT ثبت نشده (صفر double-actuation)
    assert not any(o.phase == "ACT" for o in sch._organs), "shadow: no ACT organ"  # noqa: S101
    return sch


def registered_organ_phases(sch) -> list:
    return sorted({o.phase for o in sch._organs}) if sch else []
