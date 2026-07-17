#!/usr/bin/env python3
"""sync_health.py — سلامتِ sync operations (M2): lag، drift، divergence، alert.

منابع حقیقت:
  • پرچم‌های sync-source (فایلِ last-success-{source}.json در _ops/state/sync/).
  • تلمتری از telemetry.py (snapshot).
  • اعداد از budgets.yaml (I6)؛ نبود = default با tag EST.

خط‌قرمزهای سخت:
  • fail-soft: هر source ناخوانا = report بدون alert سراسری.
  • alert فقط از opslib.alert (append-only governor-alerts.md).
  • FREEZE اگر divergence > threshold (I3).
  • stdlib-only؛ $0 offline؛ propose-only.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_OPS = _HERE.parent
for _p in (str(_HERE), str(_OPS / "budget"), str(_OPS / "state")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import opslib  # noqa: E402

SYNC_DIR = opslib.STATE_DIR / "sync"
HEALTH_PATH = opslib.STATE_DIR / "sync-health.json"


def _cfg() -> dict:
    """پیکربندی از budgets.yaml → resilience.sync_health."""
    try:
        b = opslib.load_budgets()
    except Exception:  # noqa: BLE001
        b = {}
    r = (b.get("resilience") or {}).get("sync_health") or {}
    return {
        "warn_lag_seconds": float(r.get("warn_lag_seconds", 3600)),
        "err_lag_seconds": float(r.get("err_lag_seconds", 86400)),
        "divergence_pct": float(r.get("divergence_pct", 0.20)),
        "max_fail_streak": int(r.get("max_fail_streak", 5)),
        "tag": "FACT(budgets.yaml)" if r else "EST(default)",
    }


def _source_path(source: str) -> Path:
    SYNC_DIR.mkdir(parents=True, exist_ok=True)
    return SYNC_DIR / f"last-success-{source}.json"


def _health_path() -> Path:
    HEALTH_PATH.parent.mkdir(parents=True, exist_ok=True)
    return HEALTH_PATH


def record_success(source: str, meta: dict | None = None) -> dict:
    """ثبت موفقیتِ sync برای source."""
    sp = _source_path(source)
    rec = {"ts": opslib.now_iso(), "epoch": time.time(), "meta": meta or {}}
    sp.write_text(json.dumps(rec, ensure_ascii=False, indent=2), encoding="utf-8")
    # update health aggregate
    health = _load_health()
    h = health.setdefault("sources", {}).setdefault(source, {})
    h["last_ok_ts"] = rec["ts"]
    h["last_ok_epoch"] = rec["epoch"]
    h["fail_count"] = 0
    h["last_fail_ts"] = None
    h["status"] = "ok"
    _save_health(health)
    return {"source": source, "status": "ok"}


def record_failure(source: str, reason: str = "") -> dict:
    """ثبت شکستِ sync؛ اگر streak به max_fail_streak رسید → alert."""
    health = _load_health()
    h = health.setdefault("sources", {}).setdefault(source, {})
    h["last_fail_ts"] = opslib.now_iso()
    h["fail_count"] = h.get("fail_count", 0) + 1
    h["status"] = "fail"
    _save_health(health)
    cfg = _cfg()
    if h["fail_count"] >= cfg["max_fail_streak"]:
        opslib.alert([f"sync {source} failed {h['fail_count']}× consecutive (max {cfg['max_fail_streak']}) — {reason}"])
    return {"source": source, "status": "fail", "fail_count": h["fail_count"]}


def check(source: str) -> dict:
    """بررسی سلامتِ یک source: lag، streak، drift."""
    cfg = _cfg()
    health = _load_health()
    h = health.get("sources", {}).get(source, {})
    last_ok = h.get("last_ok_epoch")
    lag_s = None
    if last_ok:
        lag_s = round(time.time() - last_ok, 1)
    level = "ok"
    reason = None
    if lag_s is None:
        level, reason = "err", "no successful sync recorded"
    elif lag_s >= cfg["err_lag_seconds"]:
        level, reason = "err", f"lag {lag_s}s >= {cfg['err_lag_seconds']}s"
    elif lag_s >= cfg["warn_lag_seconds"]:
        level, reason = "warn", f"lag {lag_s}s >= {cfg['warn_lag_seconds']}s"
    return {
        "source": source,
        "status": level,
        "lag_seconds": lag_s,
        "fail_count": h.get("fail_count", 0),
        "last_ok_ts": h.get("last_ok_ts"),
        "last_fail_ts": h.get("last_fail_ts"),
        "reason": reason,
        "config_tag": cfg["tag"],
    }


def divergence_check(source_a: str, source_b: str,
                     value_a: float, value_b: float) -> dict:
    """بررسی divergence بین دو source (مثلاً billed↔telemetry)."""
    cfg = _cfg()
    if value_a <= 0 and value_b <= 0:
        return {"divergence": 0.0, "status": "ok", "reason": "both zero"}
    denom = max(abs(value_a), abs(value_b), 0.000001)
    div = abs(value_a - value_b) / denom
    status = "ok"
    reason = None
    if div > cfg["divergence_pct"]:
        status = "err"
        reason = f"divergence {div:.1%} > threshold {cfg['divergence_pct']:.1%}"
        opslib.alert([f"sync divergence {source_a}↔{source_b}: {reason}"])
        # I3: divergence = FREEZE
        opslib.freeze(f"sync divergence {source_a}↔{source_b}: {reason}")
    return {"divergence": round(div, 4), "status": status, "reason": reason}


def snapshot() -> dict:
    """عکس واحد از سلامتِ تمام sourceهای شناخته‌شده."""
    health = _load_health()
    cfg = _cfg()
    sources = list(health.get("sources", {}).keys())
    out = {"ts": opslib.now_iso(), "config": cfg, "sources": {}}
    for s in sources:
        out["sources"][s] = check(s)
    # summary
    ok = sum(1 for v in out["sources"].values() if v["status"] == "ok")
    warn = sum(1 for v in out["sources"].values() if v["status"] == "warn")
    err = sum(1 for v in out["sources"].values() if v["status"] == "err")
    out["summary"] = {"total": len(sources), "ok": ok, "warn": warn, "err": err}
    return out


def write_snapshot() -> dict:
    """ثبت snapshot روی دیسک."""
    s = snapshot()
    with opslib.LockedJson(_health_path()) as lj:
        lj.write(s)
    return s


# ─── helpers ─────────────────────────────────────────────────────────────────
def _load_health() -> dict:
    try:
        with opslib.LockedJson(_health_path()) as lj:
            return lj.read()
    except Exception:  # noqa: BLE001
        return {}


def _save_health(data: dict) -> None:
    with opslib.LockedJson(_health_path()) as lj:
        lj.write(data)


if __name__ == "__main__":
    import sys
    if "--check" in sys.argv:
        idx = sys.argv.index("--check")
        source = sys.argv[idx + 1] if idx + 1 < len(sys.argv) else "unknown"
        print(json.dumps(check(source), ensure_ascii=False, indent=2))
    else:
        print(json.dumps(write_snapshot(), ensure_ascii=False, indent=2))
