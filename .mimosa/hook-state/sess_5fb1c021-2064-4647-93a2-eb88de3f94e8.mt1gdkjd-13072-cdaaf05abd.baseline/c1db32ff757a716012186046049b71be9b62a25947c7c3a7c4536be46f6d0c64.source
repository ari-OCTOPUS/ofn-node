#!/usr/bin/env python3
"""leg_feed.py — خوراکِ حسّیِ $0 برای پاهای CULTIVATED (رأی مالک 2026-08-12).

هدف: پاها «گرسنه» نمانند. الگوی صندوق همان leg_cultivate است:
  state/legs/<leg>-inbox/*.json  →  cultivate هضم می‌کند.

قواعد:
  - فقط metadata / label / kind / day — صفر مقدار/نام/عدد مالی (خط قرمز accounting).
  - idempotent روزانه: یک sense-pulse per (leg, day) مگر force=True.
  - منبعِ راکد (mining/ziman): سایدکارِ additive  state/legs/<leg>-source-pulse.json
    تا enrich سنِ تازه ببیند بدون دست‌کاری historyِ coordinator/catalog.
  - propose-only · صفر شبکه · صفر EXTERNAL_SEND · fail-soft.

فراخوانی: ensure_food() قبل از cultivate_all (از wiring.legs_cultivation_beat)
یا `python -m leg_feed` برای تغذیهٔ دستی.
"""
from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))
sys.path.insert(0, str(_HERE.parent / "budget"))
import opslib  # noqa: E402

try:
    import leg_cultivate as lc
except ImportError:  # pragma: no cover
    lc = None  # type: ignore


def _legs_state() -> Path:
    return opslib.STATE_DIR / "legs"


def _inbox(leg: str) -> Path:
    return _legs_state() / f"{leg}-inbox"


def _pulse_path(leg: str) -> Path:
    return _legs_state() / f"{leg}-source-pulse.json"


def _day() -> str:
    return opslib.today()


def _status_snapshot(leg: str) -> dict:
    """snapshot فقط‌خواندنی — fail-soft؛ بدون echo مالی."""
    try:
        if leg == "mining":
            import mining_leg
            st = mining_leg.mining_status()
        elif leg == "crypto":
            import crypto_leg
            st = crypto_leg.crypto_status()
        elif leg == "accounting":
            import accounting_leg
            st = accounting_leg.accounting_status()
        elif leg == "knowledge":
            import knowledge_leg
            st = knowledge_leg.knowledge_status()
        elif leg == "ziman":
            import ziman_leg
            # ziman_leg may expose module-level or class helper
            if hasattr(ziman_leg, "ziman_status"):
                st = ziman_leg.ziman_status()
            else:
                st = {"leg": "ziman", "live": False, "signal": "catalog",
                      "note": "status helper missing — pulse only"}
        else:
            st = {"leg": leg, "signal": "unknown"}
        if not isinstance(st, dict):
            return {"leg": leg, "signal": "bad-status"}
        # whitelist keys only (no accidental PII)
        keep = ("leg", "live", "signal", "note", "age_days", "phase")
        return {k: st.get(k) for k in keep if k in st}
    except Exception as e:  # noqa: BLE001
        return {"leg": leg, "signal": "status-error", "err": type(e).__name__}


def build_packet(leg: str, *, day: str | None = None) -> dict:
    day = day or _day()
    snap = _status_snapshot(leg)
    return {
        "schema": "leg-feed.v1",
        "kind": "sense-pulse",
        "label": f"{leg} sense {day}",
        "leg": leg,
        "day": day,
        "live": bool(snap.get("live")),
        "signal": str(snap.get("signal") or "")[:80],
        "note": str(snap.get("note") or "")[:120],
        "fed_by": "leg_feed.ensure_food",
    }


def _already_fed_today(leg: str, day: str) -> bool:
    """اگر در inbox یا processed امروز همان day باشد، دوباره نریز (مگر force)."""
    box = _inbox(leg)
    for folder in (box, box / "processed"):
        if not folder.is_dir():
            continue
        for p in folder.glob("*.json"):
            if p.name.endswith(".result.json") or p.name.startswith("_"):
                continue
            try:
                d = json.loads(p.read_text("utf-8"))
            except (OSError, ValueError):
                continue
            if isinstance(d, dict) and d.get("day") == day and d.get("kind") == "sense-pulse":
                return True
    return False


def drop_packet(leg: str, item: dict) -> Path | None:
    try:
        box = _inbox(leg)
        box.mkdir(parents=True, exist_ok=True)
        name = f"sense-{item.get('day') or _day()}.json"
        dest = box / name
        if dest.exists():
            # collision → unique suffix
            i = 1
            while (box / f"sense-{item.get('day')}.{i}.json").exists():
                i += 1
            dest = box / f"sense-{item.get('day')}.{i}.json"
        tmp = dest.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(item, ensure_ascii=False, indent=2), "utf-8")
        os.replace(tmp, dest)
        return dest
    except (OSError, TypeError, ValueError):
        return None


def write_source_pulse(leg: str, *, meta: dict | None = None) -> Path | None:
    """سایدکارِ تازگی برای enrich (mining/ziman) — سن از mtime همین فایل خوانده می‌شود."""
    if leg not in ("mining", "ziman"):
        return None
    try:
        _legs_state().mkdir(parents=True, exist_ok=True)
        payload = {
            "schema": "leg-source-pulse.v1",
            "leg": leg,
            "ts": opslib.now_iso(),
            "unix": time.time(),
            "meta": meta or {},
            "note": "additive freshness for cultivate enrich — does not mutate coordinator/catalog",
        }
        dest = _pulse_path(leg)
        tmp = dest.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2), "utf-8")
        os.replace(tmp, dest)
        return dest
    except (OSError, TypeError, ValueError):
        return None


def pulse_age_days(leg: str) -> float | None:
    try:
        from leg_freshness import age_days
    except ImportError:
        def age_days(p):  # type: ignore[misc]
            try:
                return (time.time() - Path(p).stat().st_mtime) / 86400.0
            except OSError:
                return None
    return age_days(_pulse_path(leg))


def ensure_food(*, force: bool = False, legs: tuple | list | None = None) -> dict:
    """برای هر پای CULTIVATED یک sense-pulse روزانه بریز + pulse تازگی منبع."""
    names = tuple(legs) if legs else (
        lc.CULTIVATED_LEGS if lc is not None else
        ("mining", "crypto", "accounting", "knowledge", "ziman")
    )
    day = _day()
    out = {"schema": "leg-feed-report.v1", "ts": opslib.now_iso(), "day": day,
           "fed": [], "skipped": [], "pulses": [], "errors": []}
    for leg in names:
        try:
            if not force and _already_fed_today(leg, day):
                out["skipped"].append(leg)
            else:
                pkt = build_packet(leg, day=day)
                path = drop_packet(leg, pkt)
                if path is None:
                    out["errors"].append({"leg": leg, "err": "drop-failed"})
                else:
                    out["fed"].append({"leg": leg, "path": path.name})
            if leg in ("mining", "ziman"):
                pp = write_source_pulse(leg, meta={"day": day})
                if pp is not None:
                    out["pulses"].append(leg)
        except Exception as e:  # noqa: BLE001
            out["errors"].append({"leg": leg, "err": f"{type(e).__name__}: {e}"})
    return out


if __name__ == "__main__":
    force = "--force" in sys.argv
    report = ensure_food(force=force)
    if lc is not None:
        cult = lc.cultivate_all(write_report=True)
        report["cultivate"] = {
            "starved_legs": cult.get("starved_legs"),
            "stale_legs": cult.get("stale_legs"),
            "digested": {n: (d.get("digested") if isinstance(d, dict) else None)
                         for n, d in (cult.get("legs") or {}).items()},
        }
    print(json.dumps(report, ensure_ascii=False, indent=2))
