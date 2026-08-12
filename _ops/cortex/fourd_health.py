#!/usr/bin/env python3
"""fourd_health.py — probe فقط‌خواندنِ لایول‌نسِ 4d_system (observability، ADR-038).

4d_system تا امروز DEPRECATED و از ارگانیسمِ زنده قطع بوده. این probe **بدونِ هیچ
import از 4d_system و بدونِ هیچ write به آن**، فقط mtimeی daemon_state.json را
می‌خواند و تازگی‌اش را در یک shadow-report در _ops/state می‌نویسد تا بتوان آن را
به‌عنوان یک عضوِ فقط‌مشاهده‌شنی در registry/innervation ثبت کرد.

مرزِ سخت (non-negotiable):
  - فقط‌خواندن: هیچ import از 4d_system، هیچ write به 4d_system، هیچ اتصالِ اجرایی.
    (در دستهٔ read_only از autonomy_grant.)
  - پیش‌فرض خاموش: OCTOPUS_OBSERVE_4D=0. وقتی خاموش است → persist() یک no-op است.
  - absence ≠ healthy: نبودِ فایل = "missing"، هرگز "fresh"/"healthy".

$0 · stdlib · read-only · fail-soft.
"""
from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

_HERE = Path(__file__).resolve().parent
if str(_HERE.parent / "budget") not in sys.path:
    sys.path.insert(0, str(_HERE.parent / "budget"))
import opslib  # noqa: E402

SCHEMA = "fourd-health.v1"
FLAG = "OCTOPUS_OBSERVE_4D"
# daemon_state.json لایول‌نس‌فایلِ 4d_system است (repo-relative، مثبت‌شده).
# _HERE = _ops/cortex → parents[2] = repo-root.
DAEMON_STATE = _HERE.parents[2] / "4d_system" / "outputs" / "daemon_state.json"
REPORT = opslib.STATE_DIR / "pulse" / "fourd-health-latest.json"
DEFAULT_SLA_S = 7200.0   # ۲ ساعت — هم‌راستا با SLAی عضوِ registry


def _enabled() -> bool:
    return os.environ.get(FLAG, "0") == "1"


def _now_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def probe(sla_s: float = DEFAULT_SLA_S) -> dict:
    """تازگیِ daemon_state.json را طبقه‌بندی کن: fresh / stale / missing / corrupt.
    هرگز healthy-on-absence برنمی‌گرداند (absence = missing)."""
    rec: dict = {
        "schema": SCHEMA, "ts": _now_iso(), "observed_path": str(DAEMON_STATE),
        "status": "missing", "mtime": None, "age_s": None,
        "sla_s": float(sla_s), "advisory_only": True,
    }
    try:
        if not DAEMON_STATE.exists():
            return rec                       # missing — هرگز healthy
        mtime = DAEMON_STATE.stat().st_mtime
        # parse-test (تشخیصِ corrupt) — محتوا را نمی‌پذیریم، فقط parse می‌کنیم.
        try:
            json.loads(DAEMON_STATE.read_text("utf-8"))
        except (OSError, ValueError):
            rec["status"], rec["mtime"] = "corrupt", mtime
            return rec
        age = max(0.0, time.time() - mtime)
        rec["mtime"] = mtime
        rec["age_s"] = int(age)
        rec["status"] = "fresh" if age <= sla_s else "stale"
        return rec
    except OSError:
        return rec                           # missing در خطای I/O


def persist() -> dict | None:
    """وقتی flag روشن است، probe + write گزارش. وقتی خاموش است → no-op (None)."""
    if not _enabled():
        return None
    try:
        rec = probe()
        REPORT.parent.mkdir(parents=True, exist_ok=True)
        with opslib.LockedJson(REPORT) as lj:
            lj.write(rec)
        return rec
    except Exception as e:  # noqa: BLE001
        opslib.alert([f"fourd_health persist failed: {type(e).__name__}: {e}"])
        return None


def summary() -> dict | None:
    """خلاصه برای cortex tick؛ وقتی خاموش است None."""
    if not _enabled():
        return None
    rec = probe()
    return {"status": rec["status"], "age_s": rec.get("age_s"),
            "observed": rec["observed_path"]}


if __name__ == "__main__":
    print(json.dumps(probe(), ensure_ascii=False, indent=2))
