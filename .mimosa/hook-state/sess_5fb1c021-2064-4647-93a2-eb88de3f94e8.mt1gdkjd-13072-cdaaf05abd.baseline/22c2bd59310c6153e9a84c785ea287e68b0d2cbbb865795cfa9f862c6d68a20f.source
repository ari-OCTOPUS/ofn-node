"""
muse.py — ورودِ سبکِ Mind Monitor / Muse 2 (فقط stdlib، بدونِ numpy/scipy).

دو مسیر:
  ۱) اگر CSV ستونِ RR/IBI داشته باشد → مستقیم و دقیق با hrv.compute_rmssd.
  ۲) اگر فقط PPG خام باشد → peak detectionِ سبکِ pure-python (تقریبی، با برچسبِ کیفیت).

⚠️ PPGِ Muse 2 نویزی است؛ هیچ ادعای دقتِ بالینی نمی‌کنیم. خروجی «سیگنالِ شخصی» است.
"""

from __future__ import annotations

import csv
import io
import math
import statistics

import hrv

# نام‌های محتملِ ستون‌ها در خروجی Mind Monitor
_PPG = ["ppg_ir", "ppg_red", "ppg_ambient", "ppg", "ir", "red", "ambient"]
_RR = ["rr", "ibi", "rr_interval", "interbeat", "rr_ms"]
_TS = ["timestamp", "time", "timestamps"]


def parse_csv(text: str):
    """خروجی: (headers_lower, rows[list[dict]]). تحملِ خطا برای ستون‌های اضافی."""
    reader = csv.DictReader(io.StringIO(text))
    headers = [(h or "").strip() for h in (reader.fieldnames or [])]
    rows = list(reader)
    return headers, rows


def _find(headers_lower, candidates):
    for c in candidates:
        for h in headers_lower:
            if h == c or c in h:
                return h
    return None


def detect_columns(headers: list[str]) -> dict:
    low = {h.lower(): h for h in headers}
    keys = list(low.keys())
    found = {
        "rr": _find(keys, _RR),
        "ts": _find(keys, _TS),
        "ppg_ir": _find(keys, ["ppg_ir", "ir"]),
        "ppg_ambient": _find(keys, ["ppg_ambient", "ambient"]),
        "ppg_any": _find(keys, _PPG),
    }
    # نگاشت به نامِ اصلیِ ستون
    return {k: (low.get(v) if v else None) for k, v in found.items()}


def _floats(rows, col):
    out = []
    for r in rows:
        v = (r.get(col) or "").strip()
        try:
            out.append(float(v))
        except (ValueError, TypeError):
            out.append(None)
    return out


def _estimate_rate(rows, ts_col):
    """نرخِ نمونه‌برداری (Hz) از ستونِ زمان. None اگر نشد."""
    ts = [v for v in _floats(rows, ts_col) if v is not None]
    if len(ts) < 3:
        return None
    diffs = [ts[i + 1] - ts[i] for i in range(len(ts) - 1) if ts[i + 1] > ts[i]]
    if not diffs:
        return None
    dt = statistics.median(diffs)
    if dt <= 0:
        return None
    # اگر زمان بر حسب ثانیه باشد dt~0.0156 برای 64Hz؛ اگر ms باشد ~15.6
    return (1000.0 / dt) if dt > 1 else (1.0 / dt)


def _moving_avg(x, w):
    if w < 2:
        return x[:]
    out = []
    half = w // 2
    for i in range(len(x)):
        a = max(0, i - half)
        b = min(len(x), i + half + 1)
        out.append(sum(x[a:b]) / (b - a))
    return out


def _detect_peaks(sig, fs):
    """peak detectionِ ساده با آستانه‌ی تطبیقی و دوره‌ی نسوزِ ~۳۰۰ms."""
    n = len(sig)
    if n < int(fs * 2):
        return []
    base = _moving_avg(sig, max(2, int(fs)))          # detrend baseline
    d = [sig[i] - base[i] for i in range(n)]
    sm = _moving_avg(d, max(2, int(fs / 8)))          # smoothing
    pos = [v for v in sm if v > 0]
    if not pos:
        return []
    thr = statistics.mean(pos) + 0.5 * (statistics.pstdev(pos) or 0)
    refractory = int(0.3 * fs)
    peaks = []
    last = -refractory
    for i in range(1, n - 1):
        if sm[i] > thr and sm[i] >= sm[i - 1] and sm[i] > sm[i + 1] and (i - last) >= refractory:
            peaks.append(i)
            last = i
    return peaks


def compute_from_csv(text: str) -> dict:
    """
    تلاشِ best-effort برای RMSSD از یک CSV.
    خروجی: dict با ok, rmssd, mean_hr, beat_count, duration_sec, sample_rate,
            artifact_ratio, quality, detected_columns, source, reason
    """
    headers, rows = parse_csv(text)
    cols = detect_columns(headers)
    base = {
        "ok": False, "rmssd": None, "mean_hr": None, "beat_count": 0,
        "duration_sec": None, "sample_rate": None, "artifact_ratio": None,
        "quality": "unknown", "detected_columns": headers, "source": None,
        "reason": None,
    }
    if not rows:
        base["reason"] = "CSV خالی یا ناخوانا بود."
        return base

    # مسیر ۱ — ستونِ RR/IBI مستقیم
    if cols["rr"]:
        rr = [v for v in _floats(rows, cols["rr"]) if v is not None]
        res = hrv.compute_rmssd(rr)
        base["source"] = "muse_rr"
        if not res["ok"]:
            base["reason"] = res["reason"]
            return base
        base.update(ok=True, rmssd=round(res["rmssd"], 1), beat_count=res["n_used"] + 1,
                    artifact_ratio=res["n_dropped"] / max(1, len(rr)),
                    quality="good" if res["n_used"] >= 30 else "questionable")
        return base

    # مسیر ۲ — PPG خام
    ir = cols["ppg_ir"] or cols["ppg_any"]
    if not ir:
        base["reason"] = "ستونِ RR یا PPG پیدا نشد. فعلاً RMSSD را دستی وارد کن."
        return base

    sig = _floats(rows, ir)
    if cols["ppg_ambient"]:
        amb = _floats(rows, cols["ppg_ambient"])
        sig = [(sig[i] - amb[i]) if (sig[i] is not None and amb[i] is not None) else None
               for i in range(len(sig))]
    sig = [v for v in sig if v is not None]
    fs = _estimate_rate(rows, cols["ts"]) or 64.0  # پیش‌فرضِ Muse با هشدار
    base["sample_rate"] = round(fs, 1)
    base["source"] = "muse_ppg"
    base["duration_sec"] = round(len(sig) / fs, 1) if fs else None

    peaks = _detect_peaks(sig, fs)
    if len(peaks) < 4:
        base["reason"] = ("تشخیصِ ضربان از PPG قابلِ‌اتکا نبود. "
                          "فعلاً RMSSD را بیرونی حساب کن یا دستی وارد کن.")
        base["quality"] = "bad"
        return base

    ibi = [(peaks[i + 1] - peaks[i]) / fs * 1000.0 for i in range(len(peaks) - 1)]
    res = hrv.compute_rmssd(ibi)
    if not res["ok"]:
        base["reason"] = res["reason"]
        base["quality"] = "bad"
        return base

    mean_ibi = statistics.mean([x for x in ibi if 300 <= x <= 2000])
    base.update(
        ok=True, rmssd=round(res["rmssd"], 1), beat_count=len(peaks),
        mean_hr=round(60000.0 / mean_ibi, 1),
        artifact_ratio=round(res["n_dropped"] / max(1, len(ibi)), 2),
        # PPGِ Muse ذاتاً نویزی → سقفِ کیفیت questionable
        quality="questionable" if res["n_used"] >= 30 else "bad",
        reason="PPG تقریبی است؛ سیگنالِ شخصی، نه دقتِ بالینی.",
    )
    return base
