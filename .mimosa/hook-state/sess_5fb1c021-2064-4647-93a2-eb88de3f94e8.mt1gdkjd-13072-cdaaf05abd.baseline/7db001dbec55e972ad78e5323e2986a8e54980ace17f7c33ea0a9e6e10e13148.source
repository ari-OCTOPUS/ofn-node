#!/usr/bin/env python3
"""telemetry.py — 📡 حلقه‌ی حسیِ ساخت‌یافته (gapِ §۳.۳ در OCTOPUS-ACTUATION-ALIGNMENT).

قبلاً فیدبکِ بازوها فقط exit-code/exception بود → learning brain قابلِ calibration نبود.
طبق §۵.۵: هر worker بعد از job یک رکوردِ ساخت‌یافته می‌نویسد:
  {job_id, organ, duration_ms, cost_usd, outcome, error}

+ stale detection (§۳.۳): TTL/freshness روی هر truth-card — «تصمیم بر اساس داده‌ی
قدیمی» را آشکار می‌کند به‌جای پنهان.

$0 · stdlib-only · append-only · صفر PII (فقط metadata).
"""
from __future__ import annotations

import json
import os
import time
from pathlib import Path

from . import config

OUTCOMES = frozenset({"ok", "failed", "blocked", "skipped"})


class JobTelemetry:
    """ثبت/خلاصه‌ی telemetry هر job. فایل: PF_STATE/telemetry.jsonl (append-only)."""

    def __init__(self, state_dir: str | Path | None = None):
        base = Path(state_dir) if state_dir else Path(config.ensure_pf_state())
        base.mkdir(parents=True, exist_ok=True)
        self.path = base / "telemetry.jsonl"

    def record(self, job_id: str, organ: str, duration_ms: int,
               outcome: str = "ok", cost_usd: float = 0.0, error: str = "") -> dict:
        """یک رکوردِ ساخت‌یافته. outcome ناشناخته → 'failed' (fail-closed در طبقه‌بندی)."""
        rec = {
            "ts": time.time(),
            "job_id": str(job_id)[:80],
            "organ": str(organ)[:40],
            "duration_ms": max(0, int(duration_ms)),
            "outcome": outcome if outcome in OUTCOMES else "failed",
            "cost_usd": round(max(0.0, float(cost_usd)), 6),
            "error": str(error)[:200],
        }
        try:
            with open(self.path, "a", encoding="utf-8") as f:
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        except OSError:
            pass
        return rec

    def _load(self, last_n: int = 2000) -> list[dict]:
        try:
            with open(self.path, encoding="utf-8") as f:
                lines = f.readlines()[-last_n:]
        except OSError:
            return []
        out = []
        for line in lines:
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError:
                continue
        return out

    def summary(self, last_n: int = 2000) -> dict:
        """per-organ: p50/p95 duration، error-rate، هزینه‌ی تجمعی — خوراکِ داشبورد/health."""
        recs = self._load(last_n)
        organs: dict[str, dict] = {}
        for r in recs:
            d = organs.setdefault(r.get("organ", "?"),
                                  {"jobs": 0, "failed": 0, "durations": [], "cost_usd": 0.0})
            d["jobs"] += 1
            if r.get("outcome") != "ok":
                d["failed"] += 1
            d["durations"].append(int(r.get("duration_ms", 0)))
            d["cost_usd"] += float(r.get("cost_usd", 0.0))
        for o, d in organs.items():
            ds = sorted(d.pop("durations"))
            n = len(ds)
            d["p50_ms"] = ds[n // 2] if n else 0
            d["p95_ms"] = ds[min(n - 1, int(n * 0.95))] if n else 0
            d["error_rate"] = round(d["failed"] / max(d["jobs"], 1), 3)
            d["cost_usd"] = round(d["cost_usd"], 4)
        return organs


# ─── stale detection (truth-card freshness) ──────────────────────────────────
def is_stale(ts_or_path, ttl_s: float) -> bool:
    """True اگر داده کهنه‌تر از TTL باشد. ورودی: epoch-ts یا مسیرِ فایل (mtime).
    نبودِ فایل/مقدارِ نامعتبر = stale (fail-closed: داده‌ی نامعلوم = کهنه)."""
    try:
        if isinstance(ts_or_path, (int, float)):
            ts = float(ts_or_path)
        else:
            ts = os.path.getmtime(str(ts_or_path))
    except (OSError, ValueError, TypeError):
        return True
    return (time.time() - ts) > float(ttl_s)


def freshness_report(paths: dict[str, str | Path], ttl_s: float = 86400.0) -> dict:
    """گزارشِ تازگیِ چند truth-card: {نام: {stale, age_s}}. برای داشبورد/کاکپیت."""
    out = {}
    now = time.time()
    for name, p in paths.items():
        try:
            age = now - os.path.getmtime(str(p))
            out[name] = {"stale": age > ttl_s, "age_s": round(age, 1)}
        except OSError:
            out[name] = {"stale": True, "age_s": None}
    return out
