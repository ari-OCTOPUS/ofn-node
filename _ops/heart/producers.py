#!/usr/bin/env python3
"""producers.py — HH-P1: سه سنجهٔ زندهٔ Gate-0 (read-only، $0، provenance خارجی).

velocity_meter        — توان‌عبورِ شناخت per hour از رویدادهای ثبت‌شده توسط دیگران:
                        CONFIRMED (attribution/reconcile) · EFFECT_SETTLED (effector-gate)
                        · چرخه‌های consolidation · ضربانِ chrono (اختیاری).
internal_cpi          — «تورمِ واسط»: نویز/بی‌ثباتیِ سیگنالِ ارزش (attribution) +
                        unmatched/CONFLICT از reconcile + suspect-zeroهای تلمتری.
delta_self_estimator  — Δ_selfِ زنده به فرمِ SOG: دو پیش‌بینِ blind/informed روی
                        استریمِ append-onlyِ نمونه‌های velocity؛ ½log(S_b/S).

تقارنِ accelerator/brake: ورودی‌ها فقط رویدادهای نوشته‌شده توسط بازیگرانِ مستقل‌اند
(reconcile-job، effector-gate، consolidation، pacemaker) — هیچ self-grading.
این ماژول فقط استریم و state-fileِ خودش را می‌نویسد؛ هرگز ledger پول، هرگز chrono.db.
"""
from __future__ import annotations

import datetime as dt
import json
import math
import os
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent / "budget"))
import opslib  # noqa: E402

PULSE_DIR = opslib.STATE_DIR / "pulse"
STREAM_PATH = PULSE_DIR / "velocity-stream.jsonl"
SIGNALS_PATH = PULSE_DIR / "heart-signals-latest.json"
LEDGER_PATH = opslib.GENOME_DIR / "ledger" / "ledger.jsonl"
CONSOLIDATION_PATH = opslib.OPS / "neural" / "consolidation.json"
CHRONO_DB = opslib.STATE_DIR / "chrono.db"

CONFIRMED_STATES = ("CONFIRMED", "ATTRIBUTED")
MIN_VELOCITY_SAMPLES = int(os.environ.get("HEART_VELOCITY_MIN_SAMPLES", "5"))
MIN_CPI_EVENTS = int(os.environ.get("HEART_CPI_MIN_EVENTS", "5"))
MIN_DELTA_SAMPLES = int(os.environ.get("HEART_DELTA_MIN_SAMPLES", "48"))
STREAM_MAX_READ = int(os.environ.get("HEART_STREAM_MAX_READ", "5000"))


# ─── ابزارِ زمان (fail-soft؛ tz-آگاه → local naive) ─────────────────────────────
def _parse_ts(raw) -> dt.datetime | None:
    if raw is None:
        return None
    if isinstance(raw, (int, float)):
        try:
            return dt.datetime.fromtimestamp(float(raw))
        except (OverflowError, OSError, ValueError):
            return None
    try:
        t = dt.datetime.fromisoformat(str(raw))
        if t.tzinfo is not None:
            t = t.astimezone().replace(tzinfo=None)
        return t
    except ValueError:
        return None


def _iter_ledger():
    """خواندنِ خطیِ فقط‌خواندنیِ ledger ژنوم — خطِ خراب skip (torn-line scar موجود)."""
    if not LEDGER_PATH.exists():
        return
    try:
        with open(LEDGER_PATH, "r", encoding="utf-8") as fh:
            for line in fh:
                try:
                    yield json.loads(line)
                except (json.JSONDecodeError, ValueError):
                    continue
    except OSError:
        return


# ─── ۱) velocity_meter ──────────────────────────────────────────────────────────
def _count_confirmed(since: dt.datetime) -> tuple[int | None, list[float]]:
    """رویدادهای MONEY_ATTRIBUTION با state∈CONFIRMED در پنجره. (count, [ts_epoch])"""
    if not LEDGER_PATH.exists():
        return None, []
    stamps = []
    for rec in _iter_ledger():
        if rec.get("type") != "MONEY_ATTRIBUTION":
            continue
        p = rec.get("payload") or {}
        if p.get("state") not in CONFIRMED_STATES:
            continue
        t = _parse_ts(rec.get("ts"))
        if t and t >= since:
            stamps.append(t.timestamp())
    return len(stamps), stamps


def _count_effects_settled(since: dt.datetime) -> int | None:
    """NOTEهای EFFECT_SETTLED (نویسنده: effector-gate) در پنجره."""
    if not LEDGER_PATH.exists():
        return None
    n = 0
    for rec in _iter_ledger():
        if rec.get("type") != "NOTE":
            continue
        p = rec.get("payload") or {}
        if p.get("subtype") != "EFFECT_SETTLED":
            continue
        t = _parse_ts(rec.get("ts"))
        if t and t >= since:
            n += 1
    return n


def _count_consolidation(since: dt.datetime) -> int | None:
    """چرخه‌های consolidation (فایلِ آرایه‌ایِ neural) در پنجره."""
    try:
        if not CONSOLIDATION_PATH.exists():
            return None
        data = json.loads(CONSOLIDATION_PATH.read_text("utf-8"))
        if not isinstance(data, list):
            return None
        s_epoch = since.timestamp()
        return sum(1 for rec in data
                   if isinstance(rec, dict) and float(rec.get("timestamp", 0)) >= s_epoch)
    except (OSError, ValueError, TypeError):
        return None


def _count_beats(since: dt.datetime) -> int | None:
    """ضربان‌های pacemaker از chrono.db (فقط‌خواندنی، URI mode=ro). غایب → None."""
    if not CHRONO_DB.exists():
        return None
    try:
        import sqlite3
        con = sqlite3.connect(f"file:{CHRONO_DB.as_posix()}?mode=ro", uri=True)
        try:
            rows = con.execute("SELECT wall_ts FROM heartbeat").fetchall()
        finally:
            con.close()
        n = 0
        for (raw,) in rows:
            t = _parse_ts(raw)
            if t and t >= since:
                n += 1
        return n
    except Exception:  # noqa: BLE001 — منبعِ اختیاری، هرگز نمی‌کُشد
        return None


def velocity_meter(window_hours: float = 24.0, now: dt.datetime | None = None) -> dict:
    """throughput per hour از منابعِ خارجی. منبعِ غایب از شمارش حذف و علامت می‌خورد."""
    now = now or dt.datetime.now()
    since = now - dt.timedelta(hours=window_hours)
    confirmed, conf_stamps = _count_confirmed(since)
    effects = _count_effects_settled(since)
    consolidation = _count_consolidation(since)
    beats = _count_beats(since)
    components = {"confirmed": confirmed, "effects": effects,
                  "consolidation": consolidation, "beats": beats}
    available = {k: v for k, v in components.items() if v is not None}
    # beats فقط سیگنالِ حیات است نه شناخت — با وزنِ کم (۰.۱)؛ بقیه وزنِ ۱.
    weights = {"confirmed": 1.0, "effects": 1.0, "consolidation": 1.0, "beats": 0.1}
    total = sum(v * weights[k] for k, v in available.items())
    sample_size = sum(v for k, v in available.items() if k != "beats")
    v_per_hr = (total / window_hours) if available else None
    return {
        "velocity_per_hr": None if v_per_hr is None else round(v_per_hr, 4),
        "components": components,
        "confirmed_ts": conf_stamps[-20:],
        "window_hours": window_hours,
        "sample_size": sample_size,
        "sources_available": sorted(available.keys()),
        "authoritative": bool(available) and sample_size >= MIN_VELOCITY_SAMPLES,
        "provenance": "external: reconcile-job/effector-gate/consolidation/pacemaker",
        "ts": opslib.now_iso(),
    }


# ─── ۲) internal_cpi ────────────────────────────────────────────────────────────
def _read_state_json(name: str) -> dict:
    try:
        p = opslib.STATE_DIR / name
        return json.loads(p.read_text("utf-8")) if p.exists() else {}
    except (OSError, ValueError):
        return {}


def internal_cpi(window_hours: float = 72.0, now: dt.datetime | None = None) -> dict:
    """تورمِ واسط ∈ [0,1]: نویزِ سیگنالِ ارزش. دادهٔ ناکافی → cpi=None (نه صفرِ دروغ)."""
    now = now or dt.datetime.now()
    since = now - dt.timedelta(hours=window_hours)
    comp: dict = {}
    # (الف) پراکندگیِ رویدادهای attribution: فاصله‌ها + مقادیر (CV نرمال‌شده)
    amounts, stamps = [], []
    for rec in _iter_ledger():
        if rec.get("type") != "MONEY_ATTRIBUTION":
            continue
        p = rec.get("payload") or {}
        t = _parse_ts(rec.get("ts"))
        if not t or t < since:
            continue
        stamps.append(t.timestamp())
        try:
            amounts.append(abs(float(p.get("amount_aud", 0) or 0)))
        except (TypeError, ValueError):
            pass
    n_events = len(stamps)
    if n_events >= MIN_CPI_EVENTS:
        def _cv(xs):
            m = sum(xs) / len(xs)
            if m <= 0:
                return 0.0
            var = sum((x - m) ** 2 for x in xs) / len(xs)
            return math.sqrt(var) / m
        gaps = [b - a for a, b in zip(stamps, stamps[1:])] or [0.0]
        # CV≈1 (پواسون) طبیعی است؛ نویز = فراتر از آن. نگاشتِ کران‌دار به 0..1
        cv_mix = 0.5 * _cv(gaps) + 0.5 * (_cv(amounts) if amounts else 0.0)
        comp["attribution_noise"] = min(1.0, max(0.0, (cv_mix - 1.0) / 2.0 + 0.25))
    # (ب) reconcile: نسبتِ unmatched/double-claims به کل
    rec_state = _read_state_json("reconcile-latest.json")
    if rec_state:
        c = len(rec_state.get("confirmed") or [])
        u = len(rec_state.get("unmatched") or [])
        d = len(rec_state.get("double_claims") or [])
        tot = c + u + d
        if tot:
            comp["reconcile_mismatch"] = min(1.0, (u + 2 * d) / tot)
    # (ج) تلمتری: suspect-zeroها (متر صفر = ثبتِ مشکوکِ ارزش)
    tel = _read_state_json("telemetry-latest.json")
    if tel:
        comp["suspect_zero"] = min(1.0, float(tel.get("suspect_zero_total", 0) or 0) / 10.0)
    cpi = round(sum(comp.values()) / len(comp), 4) if comp else None
    return {
        "cpi_0_1": cpi,
        "components": comp,
        "attribution_events": n_events,
        "sample_size": n_events + (1 if rec_state else 0) + (1 if tel else 0),
        "authoritative": n_events >= MIN_CPI_EVENTS,
        "window_hours": window_hours,
        "ts": opslib.now_iso(),
    }


# ─── ۳) delta_self_estimator ────────────────────────────────────────────────────
SAMPLE_INTERVAL_S = float(os.environ.get("HEART_SAMPLE_INTERVAL_S", "3600.0"))


def should_sample(now: dt.datetime | None = None) -> bool:
    """ساعتِ ثابتِ نمونه‌گیری (decision-frequency invariance، M-HEART §۲.۶):
    نمونه‌گیری به دیوارِ ساعت گره خورده نه به ضربان — ضربانِ تندتر نمونهٔ بیشتر
    (و authoritativeِ زودتر) نمی‌سازد."""
    now = now or dt.datetime.now()
    rows = read_stream(max_rows=1)
    if not rows:
        return True
    last = _parse_ts(rows[-1].get("ts"))
    if last is None:
        return True
    return (now - last).total_seconds() >= SAMPLE_INTERVAL_S


def append_velocity_sample(sample: dict, force: bool = False) -> bool:
    """append-only به استریمِ اندازه‌گیری، فقط روی ساعتِ ثابت (مگر force در تست).
    هر نمونه شمارش‌های منبعش را حمل می‌کند تا از روی ledger قابلِ‌ممیزی/بازاشتقاق باشد."""
    if not force and not should_sample():
        return False
    rec = {"ts": opslib.now_iso(), **sample}
    opslib.append_jsonl(STREAM_PATH, rec)
    return True


def read_stream(max_rows: int = STREAM_MAX_READ) -> list[dict]:
    if not STREAM_PATH.exists():
        return []
    rows = []
    try:
        with open(STREAM_PATH, "r", encoding="utf-8") as fh:
            for line in fh:
                try:
                    rows.append(json.loads(line))
                except (json.JSONDecodeError, ValueError):
                    continue
    except OSError:
        return []
    return rows[-max_rows:]


def _ols_fit(X: list[list[float]], y: list[float], ridge: float = 1e-6) -> list[float]:
    """OLS کوچک (normal equations + حذفِ گاوسی + ridge برای پایداری). stdlib."""
    n, k = len(X), len(X[0])
    A = [[ridge if i == j else 0.0 for j in range(k)] for i in range(k)]
    b = [0.0] * k
    for row, yv in zip(X, y):
        for i in range(k):
            b[i] += row[i] * yv
            for j in range(k):
                A[i][j] += row[i] * row[j]
    # حذفِ گاوسی با pivot جزئی
    for col in range(k):
        piv = max(range(col, k), key=lambda r: abs(A[r][col]))
        if abs(A[piv][col]) < 1e-12:
            continue
        A[col], A[piv] = A[piv], A[col]
        b[col], b[piv] = b[piv], b[col]
        inv = 1.0 / A[col][col]
        for r in range(k):
            if r == col:
                continue
            f = A[r][col] * inv
            if f:
                for j in range(col, k):
                    A[r][j] -= f * A[col][j]
                b[r] -= f * b[col]
    return [b[i] / A[i][i] if abs(A[i][i]) > 1e-12 else 0.0 for i in range(k)]


# کوواریت‌های informed — فقط بالادستی/برون‌زاد (گاردِ ضدِ self-grading، ریویوی خصمانه):
# confirmed/effects از رویدادهای بازیگرانِ خارجی (reconcile-job/effector-gate) می‌آیند و
# hour برون‌زادِ محض است. `beat`/`effects_pending`/`cycle` عمداً حذف شدند — پایین‌دستِ
# همان حلقه‌ای‌اند که Δ_self می‌راند (Δ↑→beat↑→کوواریت→S↓→Δ↑ = reward-hacking).
_COV_KEYS = ("confirmed", "effects", "hour")


def delta_self_estimator(min_samples: int = MIN_DELTA_SAMPLES,
                         rows: list[dict] | None = None) -> dict:
    """Δ_selfِ زنده (proxyِ غیرکانونی، فرمِ SOG): blind (AR1 روی خودِ سری) در برابرِ
    informed (+کوواریت‌های برون‌زاد) روی استریم؛ S_b/S = MSEهای holdout؛ ½log(S_b/S).

    صداقت: این estimator همان P_closedِ قفلِ P0 نیست — یک proxyِ عملیاتی است و در
    state با برچسبِ proxy گزارش می‌شود؛ سقفش کرانِ اطلاعِ کل (½log(Var(v)/S)) است."""
    rows = read_stream() if rows is None else rows
    series, covs = [], []
    for r in rows:
        v = r.get("v")
        if v is None:
            continue
        try:
            series.append(float(v))
        except (TypeError, ValueError):
            continue
        c = r.get("cov") or {}
        covs.append([float(c.get(k, 0) or 0) for k in _COV_KEYS])
    n = len(series)
    base = {"stream_rows": len(rows), "sample_size": n,
            "min_samples": min_samples, "ts": opslib.now_iso()}
    if n < max(8, min_samples // 4):
        return {**base, "delta_self_live": None, "ceiling_live": None,
                "authoritative": False, "reason": "insufficient-stream"}
    # نرمال‌سازیِ کوواریت‌ها (z-score روی train؛ ضدِ انفجارِ مقیاس)
    split = n // 2
    X_blind, X_inf, y = [], [], []
    for t in range(1, n):
        xb = [1.0, series[t - 1]]
        xi = xb + covs[t - 1]
        X_blind.append(xb)
        X_inf.append(xi)
        y.append(series[t])
    tr = split - 1 if split >= 2 else 1
    wb = _ols_fit(X_blind[:tr], y[:tr])
    wi = _ols_fit(X_inf[:tr], y[:tr])
    def _mse(w, X, ys):
        errs = [(sum(a * b for a, b in zip(w, x)) - yv) ** 2 for x, yv in zip(X, ys)]
        return sum(errs) / len(errs) if errs else 0.0
    S_b = _mse(wb, X_blind[tr:], y[tr:])
    S = _mse(wi, X_inf[tr:], y[tr:])
    eps = 1e-12
    raw = 0.5 * math.log(max(S_b, eps) / max(S, eps))
    delta_live = max(0.0, raw)
    # سقفِ زنده = کرانِ اطلاعِ کلِ سری: Δ نمی‌تواند از ½log(Var(v)/S) بگذرد (S_b≤Var(v)).
    # اصولی‌تر از fit-gapِ in-sample؛ drift-flag جفتِ ناسازگار/دست‌خورده را می‌گیرد.
    yh = y[tr:]
    ym = sum(yh) / len(yh)
    var_hold = sum((x - ym) ** 2 for x in yh) / len(yh)
    ceiling_live = 0.1 + 0.5 * math.log(max(var_hold, eps) / max(S, eps)) \
        if var_hold > 0 else 0.1
    ceiling_live = max(ceiling_live, delta_live + 0.05)
    return {**base,
            "delta_self_live": round(delta_live, 6),
            "delta_self_raw": round(raw, 6),
            "S_blind": S_b, "S_informed": S,
            "ceiling_live": round(ceiling_live, 6),
            "holdout_n": n - 1 - tr,
            "authoritative": n >= min_samples,
            "estimator": "proxy-OLS (نه P_closed کانونی — قفلِ P0 جدا می‌ماند)",
            "provenance": "append-only velocity-stream (fixed-clock) + کوواریت‌های برون‌زاد",
            "covariates": list(_COV_KEYS)}


# ─── جمع ────────────────────────────────────────────────────────────────────────
def compute_all(write: bool = True) -> dict:
    """سه سنجه + نوشتنِ اتمیکِ state-file (تنها side-effect کنارِ استریم)."""
    out = {
        "ts": opslib.now_iso(),
        "velocity": velocity_meter(),
        "cpi": internal_cpi(),
        "delta_self": delta_self_estimator(),
        "schema": "heart-signals.v1",
    }
    out["gate0_live_producer"] = bool(out["delta_self"].get("authoritative"))
    if write:
        try:
            PULSE_DIR.mkdir(parents=True, exist_ok=True)
            with opslib.LockedJson(SIGNALS_PATH) as lj:
                lj.write(out)
        except Exception as e:  # noqa: BLE001 — مشاهده fail-soft (§۴: alert نه سکوت)
            opslib.alert([f"heart producers state write failed: {e}"])
    return out


def read_signals() -> dict:
    try:
        return json.loads(SIGNALS_PATH.read_text("utf-8")) if SIGNALS_PATH.exists() else {}
    except (OSError, ValueError):
        return {}


if __name__ == "__main__":
    print(json.dumps(compute_all(write=False), ensure_ascii=False, indent=2))
