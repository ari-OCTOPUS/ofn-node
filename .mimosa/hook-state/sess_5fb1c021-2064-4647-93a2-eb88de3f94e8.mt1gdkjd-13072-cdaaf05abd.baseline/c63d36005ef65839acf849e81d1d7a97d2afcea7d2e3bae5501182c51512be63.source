#!/usr/bin/env python3
"""germline.py — Phase 5 · S-2/S-5: germline lag + MAX_LAG alarm + retry/backoff.

LifeDoctrine §۳: germline immortality = ۳-۲-۱ discipline (≥۳ کپی، ۲ مدیا، ۱ off-site).
germline_lag = now − max(آخرین bundle، آخرین hourly push). آلارم:
  warn   > ۲ ساعت (آیا پشتِ schedule افتاده؟)
  ERROR  > ۲۶ ساعت (خطرِ مرگِ واقعی — هر دو کپی در یک ساختمان؛ سرطانِ خاموشی)
  CRIT   > ۷۲ ساعت (نبودِ بکاپ = مرگِ قریب‌الوقوع طبقِ LifeDoctrine §۱)

S-2 retry/backoff: hourly push با retry منطقی — خطای اجباری لاگ+retry، بی‌صدا گم نشود.
off-siteِ رمزنگاری‌شده فقط runbook (credential مالک، هرگز .env/.key).

additive؛ stdlib-only؛ $0 آفلاین. PS1 موجود همین کار را می‌کند ولی آزمون‌پذیر نیست —
این ماژول قراردادِ testable را استخراج می‌کند.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path
from typing import Callable

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE / "budget"))
import opslib        # noqa: E402

# آستانه‌های MAX_LAG (LifeDoctrine §۳ + verdict آری ۲۰۲۶-۰۷-۰۷ germline_lag)
LAG_WARN_H = 2.0       # >۲ ساعت = warn (پشتِ schedule)
LAG_ERROR_H = 26.0     # >۲۶ ساعت = ERROR (هر دو کپی در یک ساختمان)
LAG_CRIT_H = 72.0      # >۷۲ ساعت = CRIT (نبودِ بکاپ = مرگِ قریب‌الوقوع)


def compute_lag_hours(last_backup_ts: str | None,
                      last_hourly_ts: str | None,
                      now_ts: str | None = None) -> float:
    """germline_lag = now − max(آخرین bundle، آخرین hourly push) به ساعت.
    هر دو غایب → inf (هیچ بکاپی نیست). fail-soft: ts نامعتبر → آن را نادیده بگیر."""
    from datetime import datetime, timezone
    if now_ts is None:
        now_ts = datetime.now(timezone.utc).isoformat()
    now = _parse_iso(now_ts)
    if now is None:
        return float("inf")
    candidates = []
    for ts in (last_backup_ts, last_hourly_ts):
        t = _parse_iso(ts)
        if t is not None:
            candidates.append(t)
    if not candidates:
        return float("inf")
    latest = max(candidates)
    delta_h = (now - latest).total_seconds() / 3600.0
    return max(0.0, delta_h)


def _parse_iso(ts: str | None):
    from datetime import datetime, timezone
    if not ts:
        return None
    try:
        t = datetime.fromisoformat(str(ts).replace("Z", "+00:00"))
        if t.tzinfo is None:
            t = t.replace(tzinfo=timezone.utc)
        return t
    except (ValueError, TypeError):
        return None


def lag_severity(lag_h: float) -> str:
    """طبقه‌بندیِ آلارمِ MAX_LAG. ok/warn/ERROR/CRIT."""
    if lag_h == float("inf"):
        return "CRIT"          # هیچ بکاپی = بحرانی
    if lag_h > LAG_CRIT_H:
        return "CRIT"
    if lag_h > LAG_ERROR_H:
        return "ERROR"
    if lag_h > LAG_WARN_H:
        return "warn"
    return "ok"


def lag_alarm() -> dict:
    """محاسبهٔ germline_lag از فایل‌های marker + severity. خروجی برای ORGANISM-STATE.
    markerها: E:\\germline\\hourly.log (mtime) + E:\\germline\\daily-bundle-latest (mtime).
    در محیطِ تست، paths قابل‌تزریق."""
    return lag_alarm_from_paths(
        hourly_log=Path("E:/germline/hourly.log"),
        bundle_dir=Path("E:/germline"))


def lag_alarm_from_paths(hourly_log: Path, bundle_dir: Path,
                         now_ts: str | None = None) -> dict:
    """نسخهٔ قابل‌تزریق برای تست. mtime فایل‌ها = آخرین بکاپ موفق."""
    from datetime import datetime, timezone
    hourly_ts = _mtime_iso(hourly_log)
    bundle_ts = _mtime_iso_latest_bundle(bundle_dir)
    lag_h = compute_lag_hours(hourly_ts, bundle_ts, now_ts)
    sev = lag_severity(lag_h)
    return {"germline_lag_h": round(lag_h, 2) if lag_h != float("inf") else None,
            "germline_alert": sev,
            "last_hourly": hourly_ts or "never",
            "last_bundle": bundle_ts or "never"}


def _mtime_iso(p: Path) -> str | None:
    try:
        if p.exists():
            from datetime import datetime, timezone
            return datetime.fromtimestamp(p.stat().st_mtime, tz=timezone.utc).isoformat()
    except OSError:
        pass
    return None


def _mtime_iso_latest_bundle(d: Path) -> str | None:
    """جدیدترین *.bundle یا bundle در دایرکتوری."""
    try:
        if not d.exists():
            return None
        bundles = list(d.glob("*.bundle")) + list(d.glob("hourly-latest.bundle"))
        if not bundles:
            return None
        latest = max(bundles, key=lambda p: p.stat().st_mtime)
        return _mtime_iso(latest)
    except OSError:
        return None


# ─── S-2: retry/backoff برای hourly push ───────────────────────────────────────
def run_with_retry(fn: Callable, max_retries: int = 3, base_backoff: float = 2.0,
                   logger: Callable[[str], None] | None = None) -> dict:
    """اجرای fn با retry/backoff نمایی. خطاها لاگ می‌شوند (نه بی‌صدا گم).
    خروجی: {ok, attempts, last_error, result}. fn باید True/False یا dict برگرداند."""
    log = logger or (lambda msg: opslib.alert([f"germline retry: {msg}"]))
    last_error = ""
    for attempt in range(1, max_retries + 1):
        try:
            result = fn()
            ok = result is True or (isinstance(result, dict) and result.get("ok"))
            if ok:
                return {"ok": True, "attempts": attempt, "last_error": "", "result": result}
            last_error = "fn returned not-ok"
        except Exception as e:  # noqa: BLE001 — خطا را بگیر، لاگ کن، retry
            last_error = f"{type(e).__name__}: {e}"
        if attempt < max_retries:
            backoff = base_backoff * (2 ** (attempt - 1))   # 2, 4, 8
            log(f"attempt {attempt}/{max_retries} failed ({last_error}); retry in {backoff:.0f}s")
            time.sleep(backoff)
    log(f"all {max_retries} attempts failed; last_error={last_error}")
    return {"ok": False, "attempts": max_retries, "last_error": last_error, "result": None}


if __name__ == "__main__":
    print(json.dumps(lag_alarm(), ensure_ascii=False, indent=2))
