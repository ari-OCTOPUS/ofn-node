#!/usr/bin/env python3
"""interface.py — HH-P2: مرزِ سختِ ADR-001 به‌صورتِ typed.

Doctor → Heart: فقط HeartParams (setpoint) — **هیچ فیلدِ rate/bpm/period وجود ندارد؛
این حذف ساختاری است** (anti-patternِ «نرخ‌دادن»، ADR-001 §۳.۱). نرخ از dynamics ظاهر می‌شود.
Heart → Doctor: فقط HeartSignal (چهار فیلدِ ADR) — read-only از منظرِ Doctor.
σ: همیشه از CONFIRMED (replication.sigma_state روی ledger)، هرگز ادعای Doctor/Heart.

تفسیرِ hybrid (master-plan بخش ۱): viable_band = باندِ هدفِ velocity (item/hr).
"""
from __future__ import annotations

import json
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent / "budget"))
import opslib  # noqa: E402

SETPOINT_PATH = opslib.STATE_DIR / "pulse" / "heart-setpoint-latest.json"

# کران‌های مطلقِ ایمنی (setpoint هرگز بیرونِ اینها نمی‌رود؛ config-پذیر با env نیست —
# عمداً ثابتِ کد تا Doctor نتواند با env بازشان کند)
ABS_BAND_MAX_PER_HR = 500.0
ABS_BEAT_CAP_MAX = 2000


@dataclass(frozen=True)
class HeartParams:
    """setpointِ Doctor→Heart (ADR-001 §مرز سخت). immutable — تغییر = setpointِ نو."""
    target_sigma: float = 1.0
    viable_band_lo: float = 0.5     # item/hr — باندِ هدفِ velocity
    viable_band_hi: float = 6.0
    epoch_seq: int = 0
    target_mass_scale: float = 1.0
    daily_beat_cap: int = 288
    baroreflex_gain: float = 0.0

    @property
    def viable_band(self) -> tuple[float, float]:
        """فرمِ tupleیِ ADR-001 §۵: viable_band:(lo,hi)."""
        return (self.viable_band_lo, self.viable_band_hi)

    def validate(self) -> list[str]:
        """لیستِ نقض‌ها (خالی = معتبر). σ-cap قانونِ اساسی: target_sigma≤1."""
        errs = []
        if not (0.0 <= self.target_sigma <= 1.0):
            errs.append(f"target_sigma خارج از [0,1]: {self.target_sigma}")
        if self.viable_band_lo < 0 or self.viable_band_hi <= 0:
            errs.append("باندِ velocity باید مثبت باشد")
        if self.viable_band_lo > self.viable_band_hi:
            errs.append("باندِ وارونه: lo>hi")
        if self.viable_band_hi > ABS_BAND_MAX_PER_HR:
            errs.append(f"باند بالای سقفِ مطلق {ABS_BAND_MAX_PER_HR}")
        if not (0 < self.daily_beat_cap <= ABS_BEAT_CAP_MAX):
            errs.append(f"daily_beat_cap خارج از (0,{ABS_BEAT_CAP_MAX}]")
        if self.epoch_seq < 0:
            errs.append("epoch_seq منفی")
        if not (0.1 <= self.target_mass_scale <= 10.0):
            errs.append("target_mass_scale خارج از [0.1,10]")
        if not (0.0 <= self.baroreflex_gain <= 1.0):
            errs.append("baroreflex_gain خارج از [0,1]")
        return errs

    def to_json(self) -> dict:
        return {"schema": "HeartParams.v1", **asdict(self)}

    @classmethod
    def from_json(cls, d: dict) -> "HeartParams":
        fields = {k: d[k] for k in cls.__dataclass_fields__ if k in d}
        return cls(**fields)


@dataclass(frozen=True)
class HeartSignal:
    """سیگنالِ Heart→Doctor — دقیقاً چهار فیلدِ ADR-001."""
    beat_seq: int
    period_s: float
    sigma_now: float | None
    baro_factor: float = 1.0

    def to_json(self) -> dict:
        return {"schema": "HeartSignal.v1", **asdict(self)}


@dataclass(frozen=True)
class HeartTelemetry:
    """متادیتای تشخیصیِ additive (velocity/cpi/Δ_self) — جدا از HeartSignal تا
    چهار-فیلدیِ ADR دست‌نخورده بماند. فقط برای کابین/لاگ؛ هیچ authorization."""
    velocity_per_hr: float | None = None
    cpi_0_1: float | None = None
    delta_self_live: float | None = None
    band_lo: float | None = None
    band_hi: float | None = None
    gates: dict = field(default_factory=dict)

    def to_json(self) -> dict:
        return {"schema": "HeartTelemetry.v1", **asdict(self)}


def write_setpoint(params: HeartParams, path: Path | None = None) -> bool:
    """نوشتنِ اتمیکِ setpoint (LockedJson). نامعتبر → False + alert (نه نوشتنِ خراب)."""
    errs = params.validate()
    if errs:
        opslib.alert([f"heart setpoint رد شد: {e}" for e in errs])
        return False
    p = path or SETPOINT_PATH
    try:
        p.parent.mkdir(parents=True, exist_ok=True)
        with opslib.LockedJson(p) as lj:
            lj.write({"ts": opslib.now_iso(), **params.to_json()})
        return True
    except Exception as e:  # noqa: BLE001
        opslib.alert([f"heart setpoint write failed: {e}"])
        return False


def read_setpoint(path: Path | None = None) -> HeartParams | None:
    """خواندنِ fail-soft — غایب/خراب/نامعتبر → None (control-law پیش‌فرضِ امن دارد)."""
    p = path or SETPOINT_PATH
    try:
        if not p.exists():
            return None
        d = json.loads(p.read_text("utf-8"))
        hp = HeartParams.from_json(d)
        return None if hp.validate() else hp
    except (OSError, ValueError, TypeError):
        return None
