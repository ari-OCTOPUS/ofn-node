#!/usr/bin/env python3
"""heart/sensors.py — حسگرهای typed از state زنده (فقط‌خواندنی، fail-soft).

هر مشاهده: {metric, value, unit, wall_utc, age_s, quality, source}.
quality ∈ VALID/STALE/MISSING — غیبت هرگز صفر جعل نمی‌شود.
"""
from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_OPS = _HERE.parent
import os
import sys
for _p in (str(_OPS / "budget"), str(_OPS)):
    if _p not in sys.path:
        sys.path.insert(0, _p)
import opslib  # noqa: E402

STALE_S = {"organism": 900.0, "arbiter": 600.0, "heartstate": 1800.0,
           "stress": 7200.0, "provider": 86400.0, "telegram": 3600.0}


def _read_json(path: Path):
    try:
        d = json.loads(path.read_text("utf-8-sig"))
        return d if isinstance(d, dict) else {}
    except Exception:  # noqa: BLE001
        return {}


def _ts_age(d: dict) -> "float | None":
    try:
        ts = str(d.get("ts") or "").strip()
        if not ts:
            return None
        return max(0.0, time.time() - datetime.fromtimestamp(
            datetime.fromisoformat(ts.replace("Z", "+00:00")).timestamp()
            if False else _parse(ts)).timestamp())
    except Exception:  # noqa: BLE001
        return None


def _parse(ts: str) -> datetime:
    return datetime.fromisoformat(ts.replace("Z", "+00:00"))


def _age_of(d: dict, now: "float | None" = None):
    try:
        ts = str(d.get("ts") or "").strip()
        if not ts:
            return None
        return max(0.0, (now or time.time())
                   - _parse(ts).astimezone(timezone.utc).timestamp())
    except Exception:  # noqa: BLE001
        return None


def _quality(age, limit: float) -> str:
    if age is None:
        return "MISSING"
    return "VALID" if age <= limit else "STALE"


def _obs(metric, value, unit, age, limit, source) -> dict:
    return {"metric": metric, "value": value, "unit": unit,
            "age_s": None if age is None else round(age, 1),
            "quality": _quality(age, limit), "source": source}


def collect(state_dir=None) -> list[dict]:
    sd = Path(state_dir) if state_dir else opslib.STATE_DIR
    now = time.time()
    out: list[dict] = []

    org = _read_json(sd / "ORGANISM-STATE.json")
    age = _age_of(org, now)
    out.append(_obs("organism.beat", org.get("beat"), "count",
                    age, STALE_S["organism"], "ORGANISM-STATE.json"))
    out.append(_obs("organism.halted", org.get("halted"), "flag",
                    age, STALE_S["organism"], "ORGANISM-STATE.json"))
    out.append(_obs("organism.sleep_s", org.get("sleep_s_after_bias"), "s",
                    age, STALE_S["organism"], "ORGANISM-STATE.json"))

    arb = _read_json(sd / "pulse" / "arbiter-latest.json")
    aage = _age_of(arb, now)
    out.append(_obs("pulse.effective_period_s", arb.get("effective_period_s"), "s",
                    aage, STALE_S["arbiter"], "arbiter-latest.json"))
    out.append(_obs("pulse.driver", arb.get("driver"), "enum",
                    aage, STALE_S["arbiter"], "arbiter-latest.json"))
    out.append(_obs("pulse.n_present", arb.get("n_present"), "count",
                    aage, STALE_S["arbiter"], "arbiter-latest.json"))

    hs = _read_json(sd / "pulse" / "heartstate-latest.json")
    hage = _age_of(hs, now)
    stress = (hs.get("stress") or {}).get("organism") if isinstance(hs.get("stress"), dict) else None
    out.append(_obs("vitals.stress", stress, "0..1",
                    hage, STALE_S["heartstate"], "heartstate-latest.json"))

    st = _read_json(sd / "cortex" / "stress-latest.json")
    sage = _age_of(st, now)
    out.append(_obs("cortex.organism_stress",
                    st.get("organism_stress") if isinstance(st, dict) else None,
                    "0..1", sage, STALE_S["stress"], "stress-latest.json"))

    # provider freshness: آخرین paid-call موفق
    last_ok = None
    try:
        lines = (sd / "paid-calls.jsonl").read_text("utf-8").splitlines()
        for ln in reversed(lines[-400:]):
            try:
                r = json.loads(ln)
            except ValueError:
                continue
            if r.get("ok"):
                last_ok = r.get("ts")
                break
    except OSError:
        pass
    page = _age_of({"ts": last_ok}, now) if last_ok else None
    out.append(_obs("provider.deepseek_ok_age_s",
                    None if page is None else round(page, 1), "s",
                    page, STALE_S["provider"], "paid-calls.jsonl"))

    tg = _read_json(sd / "channel-status.json")
    tge = (tg.get("channels") or {}).get("telegram") if isinstance(tg.get("channels"), dict) else {}
    tage = _age_of(tg, now)
    out.append(_obs("telegram.live", bool(tge.get("live")) if isinstance(tge, dict) else None,
                    "bool", tage, STALE_S["telegram"], "channel-status.json"))

    # write-failures اخیر (سلامت دیسک)
    n_fail = 0
    try:
        for ln in (sd / "write-failures.jsonl").read_text("utf-8").splitlines()[-50:]:
            try:
                r = json.loads(ln)
                if (now - float(r.get("epoch") or 0)) < 3600.0:
                    n_fail += 1
            except (ValueError, TypeError):
                continue
    except OSError:
        pass
    out.append(_obs("disk.write_failures_1h", n_fail, "count",
                    0.0, STALE_S["organism"], "write-failures.jsonl"))
    return out


def summary(observations: list[dict]) -> dict:
    """خلاصهٔ ماشین‌خوان: کدام‌ها VALID، بدترین سن، شمار خرابی."""
    valid = [o for o in observations if o["quality"] == "VALID"]
    missing = [o["metric"] for o in observations if o["quality"] == "MISSING"]
    stale = [o["metric"] for o in observations if o["quality"] == "STALE"]
    fails = next((o["value"] for o in observations
                  if o["metric"] == "disk.write_failures_1h"), 0) or 0
    return {"n": len(observations), "n_valid": len(valid),
            "missing": missing, "stale": stale,
            "write_failures_1h": int(fails) if isinstance(fails, (int, float)) else 0}
