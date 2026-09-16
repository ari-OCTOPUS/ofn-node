#!/usr/bin/env python3
"""sparse_filter.py — Blueprint Phase 4 — فیلتر ورودیِ sparse: فقط سیگنالِ با خطای
پیش‌بینی بالا (novel) وارد حافظهٔ بلندمدت می‌شود؛ هندسهٔ الماس L1 نه کرهٔ L2.

ایده (L1 / prediction error):
  هر کلید عددی یک پیش‌بینی‌گر EMA دارد:  v ← (1−α)·v + α·x
  خطای پیش‌بینی:      err   = |x − v|          (کلید تازه: err = |x| و بی‌قید عبور می‌کند)
  انقباض نرم L1:       err_eff = max(0, err − λ)   ← هندسهٔ الماس: خطاهای کوچک دقیقاً صفر می‌شوند
  عبور ⇔ err_eff > threshold — سیگنالِ تکراری (قابل‌پیش‌بینی) وارد حافظهٔ بلندمدت نمی‌شود.

مرزها:
  - فیلتر هرگز ورودی را mutate نمی‌کند؛ فقط int/float واقعی (bool نه) را می‌سنجد.
  - deterministic: هیچ random، هیچ منطقِ زمان‌مند در تصمیم. $0 آفلاین. stdlib-only.
  - eviction قطعی: کم‌آپدیت‌ترین کلیدها (کمترین n، tie-break با خودِ کلید) تا max_keys.

پیش‌ثبتِ متریک‌ها (state/phase-metrics.jsonl → blueprint-phase-4-sparse):
  input_sparsity_ratio ∈ [0,1] و > 0.5 روی دادهٔ تکراری ·
  prediction_error_distribution دُم‌سنگین (heavy_tail_share) · no_regression (flag خاموش).
"""
from __future__ import annotations

import json
import math
import os
from dataclasses import dataclass, field
from pathlib import Path

def _default_persist() -> Path:
    """env-اول (OPS_DIR) تا تست‌های harness-ایزوله هرگز state واقعی را آلوده نکنند
    (درسِ 2026-07-10 — همان الگوی bcm.py)."""
    ops = os.environ.get("OPS_DIR")
    base = Path(ops) if ops else Path(__file__).resolve().parent.parent
    return base / "state" / "sparse-predictor.json"


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
class SparseFilterReport:
    """گزارش یک گام فیلتر — برای observability و متریک‌های پیش‌ثبت‌شده."""
    step: int
    passed: dict[str, float] = field(default_factory=dict)       # کلید → مقدارِ عبوری
    filtered: list[str] = field(default_factory=list)            # مسدودشده (قابل‌پیش‌بینی)
    prediction_errors: dict[str, float] = field(default_factory=dict)  # کلید → err خام
    sparsity_ratio: float = 0.0   # len(filtered)/total_numeric — متریکِ پیش‌ثبت‌شده
    novel_keys: list[str] = field(default_factory=list)          # کلیدهای بارِ اول


def heavy_tail_share(errors: dict[str, float] | list[float],
                     top_frac: float = 0.1) -> float:
    """سهمِ جرمِ |خطا| که در بالاترین ceil(top_frac·N) خطا جمع شده.

    توزیعِ دُم‌سنگین (متریکِ پیش‌ثبت‌شده): چند خطای بزرگ بیشترِ جرم را دارند → سهم ≫ top_frac.
    توزیعِ یکنواخت: سهم ≈ top_frac. ورودی خالی یا جرمِ صفر → 0.0.
    """
    vals = list(errors.values()) if isinstance(errors, dict) else list(errors)
    mags = sorted((abs(float(v)) for v in vals), reverse=True)
    if not mags:
        return 0.0
    total = sum(mags)
    if total <= 0.0:
        return 0.0
    k = math.ceil(top_frac * len(mags))
    k = max(0, min(k, len(mags)))
    return sum(mags[:k]) / total


class SparseInputFilter:
    """فیلتر ورودیِ sparse — دروازهٔ حافظهٔ بلندمدت بر اساس خطای پیش‌بینی.

    پیش‌بینی‌گرِ داخلی per-key: {"v": پیش‌بینی EMA, "n": شمارندهٔ آپدیت}.
    پارامترها env-tunable؛ آرگومانِ صریح همیشه بر env می‌چربد (الگوی bcm.py).
    """

    def __init__(self, persist_path: str | Path | None = None,
                 error_threshold: float | None = None,
                 ema_alpha: float | None = None,
                 l1_lambda: float | None = None,
                 max_keys: int | None = None):
        self._error_threshold = (error_threshold if error_threshold is not None
                                 else _env_float("OCTOPUS_SPARSE_ERROR_THRESHOLD", 0.05))
        self._ema_alpha = (ema_alpha if ema_alpha is not None
                           else _env_float("OCTOPUS_SPARSE_EMA_ALPHA", 0.2))
        self._l1_lambda = (l1_lambda if l1_lambda is not None
                           else _env_float("OCTOPUS_SPARSE_L1_LAMBDA", 0.0))
        self._max_keys = (max_keys if max_keys is not None
                          else _env_int("OCTOPUS_SPARSE_MAX_KEYS", 512))
        self._path = Path(persist_path) if persist_path else _default_persist()
        self._predictor: dict[str, dict] = {}
        self._step_count = 0
        self._load()

    # ─── properties (read-only) ──────────────────────────────────────────────

    @property
    def error_threshold(self) -> float:
        return self._error_threshold

    @property
    def ema_alpha(self) -> float:
        return self._ema_alpha

    @property
    def l1_lambda(self) -> float:
        return self._l1_lambda

    @property
    def max_keys(self) -> int:
        return self._max_keys

    @property
    def step_count(self) -> int:
        return self._step_count

    def keys(self) -> list[str]:
        return list(self._predictor.keys())

    def prediction(self, key: str) -> float | None:
        """پیش‌بینی EMA فعلی یک کلید (read-only). None اگر وجود ندارد."""
        rec = self._predictor.get(key)
        return rec["v"] if rec else None

    # ─── core: یک گام فیلتر ─────────────────────────────────────────────────

    def filter(self, observations: dict) -> SparseFilterReport:
        """یک گام فیلتر روی مشاهدات.

        فقط مقادیر int/float واقعی سنجیده می‌شوند (bool نه)؛ ورودی هرگز mutate نمی‌شود.
        کلید تازه → novel: بی‌قید عبور، err = |x|.
        کلید دیده‌شده → err = |x − v|؛ عبور ⇔ max(0, err − λ) > threshold.
        آپدیت EMA بعد از محاسبهٔ همهٔ خطاها انجام می‌شود (پیش‌بینی از همین گام نشت نمی‌کند).
        """
        self._step_count += 1

        # فقط عددی‌ها — bool صریحاً کنار گذاشته می‌شود (isinstance(True, int) صادق است)
        numeric: list[tuple[str, float]] = []
        for k, v in observations.items():
            if isinstance(v, bool) or not isinstance(v, (int, float)):
                continue
            numeric.append((k, float(v)))

        passed: dict[str, float] = {}
        filtered: list[str] = []
        prediction_errors: dict[str, float] = {}
        novel_keys: list[str] = []

        for k, x in numeric:
            rec = self._predictor.get(k)
            if rec is None:
                # کلید تازه: بی‌قید عبور — چیزی برای پیش‌بینی نداشتیم
                err = abs(x)
                prediction_errors[k] = err
                novel_keys.append(k)
                passed[k] = x
            else:
                err = abs(x - rec["v"])
                prediction_errors[k] = err
                err_eff = max(0.0, err - self._l1_lambda)   # انقباض نرم L1 (الماس)
                if err_eff > self._error_threshold:
                    passed[k] = x
                else:
                    filtered.append(k)

        # آپدیت پیش‌بینی‌گر — بعد از محاسبهٔ همهٔ خطاها
        for k, x in numeric:
            rec = self._predictor.get(k)
            if rec is None:
                self._predictor[k] = {"v": x, "n": 1}
            else:
                rec["v"] = (1.0 - self._ema_alpha) * rec["v"] + self._ema_alpha * x
                rec["n"] = rec["n"] + 1

        # eviction قطعی: کم‌آپدیت‌ترین‌ها (کمترین n، tie-break با کلید) تا max_keys
        if self._max_keys > 0 and len(self._predictor) > self._max_keys:
            by_updates = sorted(self._predictor.items(),
                                key=lambda kv: (kv[1]["n"], kv[0]))
            excess = len(self._predictor) - self._max_keys
            for k, _ in by_updates[:excess]:
                del self._predictor[k]

        total = len(numeric)
        report = SparseFilterReport(
            step=self._step_count,
            passed=passed,
            filtered=filtered,
            prediction_errors=prediction_errors,
            sparsity_ratio=(len(filtered) / total) if total > 0 else 0.0,
            novel_keys=novel_keys)
        self._save()
        return report

    # ─── persistence (atomic، fail-soft — الگوی bcm/latent_space) ────────────

    def _save(self) -> None:
        try:
            doc = {"step": self._step_count, "keys": self._predictor}
            self._path.parent.mkdir(parents=True, exist_ok=True)
            tmp = self._path.with_suffix(".tmp")
            tmp.write_text(json.dumps(doc, ensure_ascii=False), "utf-8")
            tmp.replace(self._path)
        except OSError:
            pass  # fail-soft: خطای persist نباید فیلتر را بکشد؛ گام بعدی دوباره تلاش می‌کند

    def _load(self) -> None:
        if not self._path.exists():
            return
        try:
            doc = json.loads(self._path.read_text("utf-8"))
            keys = doc.get("keys", {})
            if isinstance(keys, dict):
                for k, rec in keys.items():
                    if (isinstance(rec, dict)
                            and isinstance(rec.get("v"), (int, float))
                            and not isinstance(rec.get("v"), bool)
                            and isinstance(rec.get("n"), int)
                            and rec["n"] >= 1):
                        self._predictor[k] = {"v": float(rec["v"]), "n": rec["n"]}
            step = doc.get("step", 0)
            if isinstance(step, int) and step >= 0:
                self._step_count = step
        except (json.JSONDecodeError, OSError, ValueError):
            pass  # corrupt → start fresh (fail-soft)
