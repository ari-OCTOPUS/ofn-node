#!/usr/bin/env python3
"""bcm.py — Blueprint Phase 3: تثبیت حافظه با قانون BCM (Bienenstock-Cooper-Munro).

بدون فراموشیِ کنترل‌شده، حافظه اشباع می‌شود و ناپایدار (memory reward-hacking):
هر embedding که یک‌بار وارد latent space شد، ابدی می‌ماند و retrieval را غرق می‌کند.

قانون BCM (ریاضی — ✅ در جدول ریسک بلوپرینت):
  y        = فعال‌سازیِ یک حافظه در این گام (بازیابی/تقویت، clip به [0,1])
  θ_i      = آستانهٔ متحرکِ هر کلید = EMA(y_i²)   ← «average square activation»
  φ(y,θ)   = y·(y − θ)          ← بالای θ تقویت (LTP)، زیر θ تضعیف (LTD)
  Δw       = η·φ(y,θ) − β·w     ← جملهٔ فراموشی: −β·w (زوالِ وزن)
  w        = clip(w + Δw, 0, w_cap)

ویژگی هومئوستاتیک (ضدِ reward-hacking حافظه): θ با فعالیت بالا می‌رود، پس
فعال‌سازیِ دائمیِ اشباع‌شده (y=1 ابدی) خودش سرکوب می‌شود — هیچ حافظه‌ای نمی‌تواند
با «همیشه فعال ماندن» رشد بی‌کران بگیرد (w ≤ w_cap و در y=1 پایدار، تعادل w*→0).

مرزها:
  - فقط ایندکسِ retrieval (latent space) هرس می‌شود؛ تاریخچهٔ append-only
    (consolidation.json — I1) هرگز لمس نمی‌شود. حافظهٔ بلندمدت cold-reconstructable می‌ماند.
  - فقط دانشِ gate-passed وارد می‌شود: BCM هرگز خودش key نمی‌سازد —
    کلیدها فقط از known_keys (= آنچه verification-gate قبلاً embed کرده) می‌آیند.
  - deterministic: هیچ random. $0 آفلاین. stdlib-only.

پیش‌ثبتِ متریک‌ها (state/phase-metrics.jsonl):
  memory_decay_rate = β > 0 (کنترل‌شده) · memory_saturation ≤ 1.0 · held-out 5/5.
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path

def _default_persist() -> Path:
    """مسیرِ پیش‌فرضِ persist — env-اول (OPS_DIR) تا تست‌های harness-ایزوله هرگز
    state واقعی را آلوده نکنند (درسِ 2026-07-10: پیش‌فرضِ __file__-محور از
    ایزولاسیونِ tmp-vault فرار می‌کرد و وزنِ جعلیِ تست وارد state واقعی می‌شد)."""
    ops = os.environ.get("OPS_DIR")
    base = Path(ops) if ops else Path(__file__).resolve().parent.parent
    return base / "state" / "bcm-weights.json"


def _env_float(name: str, default: float) -> float:
    v = os.environ.get(name)
    if v is None:
        return default
    try:
        return float(v)
    except ValueError:
        return default


def _env_int(name: str, default: int) -> int:
    v = os.environ.get(name)
    if v is None:
        return default
    try:
        return int(v)
    except ValueError:
        return default


@dataclass
class BCMReport:
    """گزارش یک گام BCM — برای observability در ConsolidatedInsight."""
    step: int
    theta_mean: float
    decayed: int            # تعداد کلیدهایی که این گام Δw<0 گرفتند
    reinforced: int         # تعداد کلیدهایی که این گام Δw>0 گرفتند
    pruned: list[str] = field(default_factory=list)   # حذف‌شده از ایندکس retrieval
    saturation: float = 0.0  # len(weights)/max_keys — متریکِ پیش‌ثبت‌شده (≤ 1.0)
    weights_count: int = 0
    decay_rate: float = 0.0  # β — متریکِ پیش‌ثبت‌شده (> 0)


class BCMStabilizer:
    """تثبیت‌کنندهٔ حافظه با BCM. هر گام = یک cycle واقعیِ consolidation.

    زمانِ حافظه بر حسب «گام‌های consolidation» می‌گذرد نه wall-clock —
    cycleهای خالی (bare, nothing-to-consolidate) زوال ایجاد نمی‌کنند
    (قرارداد early-return فاز ۱ دست‌نخورده می‌ماند).
    """

    def __init__(self, persist_path: str | Path | None = None,
                 beta: float | None = None, eta: float | None = None,
                 theta_alpha: float | None = None, w_init: float = 1.0,
                 w_floor: float | None = None, w_cap: float = 4.0,
                 max_keys: int | None = None):
        # env-tunable با پیش‌فرض امن؛ پارامتر صریح همیشه بر env می‌چربد
        self._beta = beta if beta is not None else _env_float("OCTOPUS_BCM_BETA", 0.02)
        self._eta = eta if eta is not None else _env_float("OCTOPUS_BCM_ETA", 0.5)
        self._theta_alpha = (theta_alpha if theta_alpha is not None
                             else _env_float("OCTOPUS_BCM_THETA_ALPHA", 0.1))
        self._w_init = w_init
        self._w_floor = w_floor if w_floor is not None else _env_float("OCTOPUS_BCM_W_FLOOR", 0.05)
        self._w_cap = w_cap
        self._max_keys = max_keys if max_keys is not None else _env_int("OCTOPUS_BCM_MAX_KEYS", 512)
        self._path = Path(persist_path) if persist_path else _default_persist()
        self._weights: dict[str, dict] = {}
        self._step_count = 0
        self._load()

    # ─── properties (متریک‌های پیش‌ثبت‌شده) ────────────────────────────────

    @property
    def decay_rate(self) -> float:
        """memory_decay_rate = β (باید > 0 باشد — فراموشیِ کنترل‌شده، نه صفر)."""
        return self._beta

    @property
    def saturation(self) -> float:
        """memory_saturation = len(weights)/max_keys (همیشه ≤ 1.0 بعد از step)."""
        if self._max_keys <= 0:
            return 0.0
        return len(self._weights) / self._max_keys

    @property
    def step_count(self) -> int:
        return self._step_count

    def weight(self, key: str) -> float | None:
        """وزن فعلی یک کلید (read-only). None اگر وجود ندارد."""
        rec = self._weights.get(key)
        return rec["w"] if rec else None

    def theta(self, key: str) -> float | None:
        """آستانهٔ متحرک θ_i یک کلید (read-only)."""
        rec = self._weights.get(key)
        return rec["theta"] if rec else None

    def keys(self) -> list[str]:
        return list(self._weights.keys())

    # ─── core: یک گام BCM ────────────────────────────────────────────────

    def step(self, activations: dict[str, float],
             known_keys: list[str] | None = None) -> BCMReport:
        """یک گام BCM روی همهٔ حافظه‌های شناخته‌شده.

        activations: {key: y∈[0,1]} — فعال‌سازیِ این گام (غایب = 0 → فقط زوال).
        known_keys: کلیدهای موجود در ایندکس retrieval (gate-passed). BCM با این
        لیست sync می‌شود: کلید جدید → w_init؛ کلیدِ حذف‌شده از بیرون → drop.
        BCM هرگز خودش key اختراع نمی‌کند.

        خروجی: BCMReport (pruned = کلیدهایی که caller باید از ایندکس حذف کند).
        """
        self._step_count += 1

        if known_keys is not None:
            known = set(known_keys)
            # FIX #214 (2026-07-28): لیستِ خالی = «اطلاعاتی دربارهٔ ایندکس نداریم»،
            # نه «ایندکس خالی است». نسخهٔ قبلی وقتی latent_space.keys() خالی بود
            # (startup، corruption #53، یا bare cycle) همهٔ وزن‌ها را پاک می‌کرد —
            # ریشهٔ خالی‌بودنِ BCM. محافظه‌کارانه‌ترین تفسیر: وقتی نمی‌دانیم،
            # چیزی را پاک نکن. فقط وقتی لیست غیرخالی است sync اجرا شه.
            if known:
                # sync: کلیدهایی که دیگر در ایندکس نیستند → از weights حذف
                for k in [k for k in self._weights if k not in known]:
                    del self._weights[k]
                # کلیدهای تازه (فقط از known_keys — دانش gate-passed)
                for k in known_keys:
                    if k not in self._weights:
                        self._weights[k] = {"w": self._w_init, "theta": 0.0}

        decayed = 0
        reinforced = 0
        for k, rec in self._weights.items():
            y = float(activations.get(k, 0.0))
            y = 0.0 if y < 0.0 else (1.0 if y > 1.0 else y)
            theta = rec["theta"]
            phi = y * (y - theta)            # BCM: بالای θ تقویت، زیر θ تضعیف
            dw = self._eta * phi - self._beta * rec["w"]   # −β·w = فراموشی
            w_new = rec["w"] + dw
            rec["w"] = 0.0 if w_new < 0.0 else (self._w_cap if w_new > self._w_cap else w_new)
            # آستانهٔ متحرک: θ ← EMA(y²) — بعد از وزن، تا فعال‌سازیِ اول قویاً تثبیت کند
            rec["theta"] = (1.0 - self._theta_alpha) * theta + self._theta_alpha * (y * y)
            if dw < 0:
                decayed += 1
            elif dw > 0:
                reinforced += 1

        # هرس ۱: زیر کف → فراموشیِ کامل از ایندکس retrieval
        pruned: list[str] = []
        for k in [k for k, r in self._weights.items() if r["w"] < self._w_floor]:
            del self._weights[k]
            pruned.append(k)

        # هرس ۲: سقفِ اشباع — ضعیف‌ترین‌ها حذف تا max_keys (deterministic tie-break)
        if self._max_keys > 0 and len(self._weights) > self._max_keys:
            by_weight = sorted(self._weights.items(), key=lambda kv: (kv[1]["w"], kv[0]))
            excess = len(self._weights) - self._max_keys
            for k, _ in by_weight[:excess]:
                del self._weights[k]
                pruned.append(k)

        thetas = [r["theta"] for r in self._weights.values()]
        report = BCMReport(
            step=self._step_count,
            theta_mean=(sum(thetas) / len(thetas)) if thetas else 0.0,
            decayed=decayed, reinforced=reinforced, pruned=pruned,
            saturation=self.saturation, weights_count=len(self._weights),
            decay_rate=self._beta)
        self._save()
        return report

    # ─── persistence (atomic، fail-soft — الگوی latent_space) ───────────────

    def _save(self) -> None:
        try:
            doc = {"step": self._step_count,
                   "beta": self._beta,
                   "keys": self._weights}
            self._path.parent.mkdir(parents=True, exist_ok=True)
            tmp = self._path.with_suffix(".tmp")
            tmp.write_text(json.dumps(doc, ensure_ascii=False), "utf-8")
            tmp.replace(self._path)
        except OSError:
            pass  # fail-soft: persist نباید BCM را بکشد

    def _load(self) -> None:
        if not self._path.exists():
            return
        try:
            doc = json.loads(self._path.read_text("utf-8"))
            keys = doc.get("keys", {})
            if isinstance(keys, dict):
                for k, rec in keys.items():
                    if (isinstance(rec, dict)
                            and isinstance(rec.get("w"), (int, float))
                            and isinstance(rec.get("theta"), (int, float))):
                        self._weights[k] = {"w": float(rec["w"]),
                                            "theta": float(rec["theta"])}
            step = doc.get("step", 0)
            if isinstance(step, int) and step >= 0:
                self._step_count = step
        except (json.JSONDecodeError, OSError, ValueError):
            pass  # corrupt → start fresh (fail-soft)
