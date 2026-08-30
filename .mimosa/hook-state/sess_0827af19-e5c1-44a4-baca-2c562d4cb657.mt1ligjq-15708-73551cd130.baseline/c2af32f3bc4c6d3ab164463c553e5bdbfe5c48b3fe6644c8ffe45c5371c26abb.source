#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""budget_frustration.py — شاخصِ ناامیدیِ بودجه (Budget Frustration Index).

الهامِ ریاضی: در مدل‌های parity/Ising، «frustration» = میزانِ نقضِ اجتناب‌ناپذیرِ
مجموعه‌ای از محدودیت‌ها که نمی‌توان همه‌شان را هم‌زمان برآورده کرد. اختاپوس
چند ارگان روی یک سقفِ ماهانه رقابت می‌کنند؛ وقتی organ_gate.reserve() deny
می‌زند، فقط یک خط به ORGAN_LOG می‌نویسد و ساکت می‌شود. این ماژول آن نقاط کوری
را قابل مشاهده می‌کند: هر ارگان چقدر تقاضا کرده، چقدر گرفته، چقدر نبرده.

قرارداد (MEGAPROMPT-BUDGET-FRUSTRATION-INDEX-2026-08-02):
  · pure در فازِ تجمیع — فقط می‌خواند، هرگز mutate.
  · fail-soft روی ردیفِ خراب (رد کن، نه crash).
  · صداقت: اگر ORGAN_LOG خالی است، «no signal» نه ۰.
  · additive، flag-off (OCTOPUS_WIRE_BUDGET_FRUSTRATION)، halt مقدم.
"""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

_HERE = Path(__file__).resolve().parent
_OPS = _HERE.parent
_BUDGET = _OPS / "budget"
for _p in (str(_OPS), str(_BUDGET)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

FLAG = "OCTOPUS_WIRE_BUDGET_FRUSTRATION"

try:
    import opslib  # noqa: E402
    ORGAN_LOG = opslib.ORGAN_LOG
    BUDGETS_YAML = _BUDGET / "budgets.yaml"
except Exception:  # noqa: BLE001
    opslib = None  # type: ignore
    ORGAN_LOG = _BUDGET / "organ-gate-log.jsonl"
    BUDGETS_YAML = _BUDGET / "budgets.yaml"


def enabled() -> bool:
    return os.environ.get(FLAG, "0") == "1"


def _halted() -> bool:
    if opslib is None:
        return False
    try:
        return bool(opslib.master_halted() or opslib.halted()
                    or opslib.STOP_ORGANISM.exists() or opslib.frozen())
    except Exception:  # noqa: BLE001
        return True  # fail-closed


def _parse_ts(ts: str) -> "datetime | None":
    """ISO8601 → datetime آگاه (UTC). None اگر ناخوانا. fail-soft."""
    if not isinstance(ts, str):
        return None
    s = ts.strip()
    if not s:
        return None
    if s.endswith(("Z", "z")):
        s = s[:-1] + "+00:00"
    for cand in (s, s + "T00:00:00"):
        try:
            dt = datetime.fromisoformat(cand)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
        except ValueError:
            continue
    return None


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def frustration_snapshot(log_path: "Path | None" = None,
                         window_hours: float = 24.0,
                         _now: "datetime | None" = None) -> dict:
    """تجمیعِ ORGAN_LOG → per-organ {requested/allowed/denied, usd, denial_rate}.

    pure، صفر mutate، صفر side-effect. fail-soft: ردیفِ خراب رد می‌شود نه crash.
    خروجی همیشه dict؛ هرگز استثنا.
    """
    path = Path(log_path) if log_path is not None else ORGAN_LOG
    now = _now if _now is not None else _now_utc()
    cutoff = now - timedelta(hours=max(0.0, float(window_hours)))
    organs: dict[str, dict[str, Any]] = {}
    parsed = unparseable = 0
    try:
        if not path.exists():
            return {"ok": True, "signal": "no_log_file", "organs": {},
                    "window_hours": window_hours, "rows_parsed": 0, "rows_unparseable": 0}
        with path.open("r", encoding="utf-8", errors="replace") as fh:
            for raw in fh:
                raw = raw.strip()
                if not raw:
                    continue
                try:
                    r = json.loads(raw)
                except (ValueError, TypeError):
                    unparseable += 1
                    continue
                parsed += 1
                ts = _parse_ts(str(r.get("ts") or ""))
                if ts is None or ts < cutoff:
                    continue
                organ = str(r.get("organ") or "?")
                est = float(r.get("est_usd") or 0.0)
                op = str(r.get("op") or "")
                allow = r.get("allow")
                ok = r.get("ok")
                # settle verdict: ok=True/False; reserve verdict: allow=True/False
                is_allow = (allow is True) or (op == "settle" and ok is True)
                is_deny = (allow is False) or (op == "settle" and ok is False)
                rec = organs.setdefault(organ, {
                    "requested_count": 0, "allowed_count": 0, "denied_count": 0,
                    "requested_usd": 0.0, "allowed_usd": 0.0, "denied_usd": 0.0,
                    "reasons": {}})
                # شمارش فقط reserve (نه settle) برای requested/allowed/denied:
                # settle نتیجهٔ reserve است، نه یک تقاضای نو.
                if op == "reserve":
                    rec["requested_count"] += 1
                    rec["requested_usd"] += est
                    if is_allow:
                        rec["allowed_count"] += 1
                        rec["allowed_usd"] += est
                    elif is_deny:
                        rec["denied_count"] += 1
                        rec["denied_usd"] += est
                        reason = str(r.get("reason") or "unknown")
                        # خلاصهٔ reason (پیشوندِ قبل از ':')
                        rec["reasons"][reason.split(":", 1)[0]] = \
                            rec["reasons"].get(reason.split(":", 1)[0], 0) + 1
        # محاسبهٔ denial_rate per organ
        for rec in organs.values():
            req = rec["requested_count"]
            rec["denial_rate"] = (rec["denied_count"] / req) if req > 0 else 0.0
            rec["top_reasons"] = sorted(rec["reasons"].items(),
                                        key=lambda kv: kv[1], reverse=True)[:3]
            rec.pop("reasons", None)
        return {"ok": True, "signal": "data", "organs": organs,
                "window_hours": window_hours, "rows_parsed": parsed,
                "rows_unparseable": unparseable, "log_path": str(path)}
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "error": f"{type(exc).__name__}:{exc}",
                "organs": {}, "rows_parsed": parsed, "rows_unparseable": unparseable}


def _organ_weights() -> dict:
    """اولویتِ ارگان از budgets.yaml (weights). fail-soft → {} اگر ناخوانا."""
    try:
        text = BUDGETS_YAML.read_text(encoding="utf-8")
    except Exception:  # noqa: BLE001
        return {}
    weights: dict[str, float] = {}
    for line in text.splitlines():
        s = line.strip()
        if s and not s.startswith("#") and ":" in s:
            name, _, rest = s.partition(":")
            name = name.strip()
            if name and name[0].isupper():
                weights[name] = 1.0  # هر ارگان پیش‌فرض وزن ۱
    return weights


def frustration_index(snapshot: dict, weights: "dict | None" = None) -> float:
    """شاخصِ ناامیدی در [0,1]. تعریف: سهمِ تقاضای برآورده‌نشده، وزن‌دار.

    نه «تعدادِ deny» به‌تنهایی (گمراه‌کننده: ارگانی با ۱۰ deny و ۱۰۰ allow
    سیرتر از ارگانی با ۱ deny و ۰ allow است). بلکه: denied_usd_w / requested_usd_w.
    اگر requested صفر است → 0 (no signal, نه frustration).
    """
    if not isinstance(snapshot, dict) or not snapshot.get("ok"):
        return 0.0
    organs = snapshot.get("organs") or {}
    if not organs:
        return 0.0
    w = weights if isinstance(weights, dict) else _organ_weights()
    total_req_w = total_denied_w = 0.0
    for organ, rec in organs.items():
        weight = float(w.get(organ, 1.0))
        req = float(rec.get("requested_usd", 0.0))
        den = float(rec.get("denied_usd", 0.0))
        total_req_w += req * weight
        total_denied_w += den * weight
    if total_req_w <= 0:
        return 0.0
    return max(0.0, min(1.0, total_denied_w / total_req_w))


def report(window_hours: float = 24.0) -> dict:
    """گزارشِ کامل برای CLI/observable. همیشه dict، هرگز استثنا."""
    if _halted():
        return {"ok": False, "reason": "halted", "flag": FLAG}
    snap = frustration_snapshot(window_hours=window_hours)
    idx = frustration_index(snap)
    snap["frustration_index"] = idx
    # علامت‌گذاریِ ارگان‌های گرسنه (denial_rate بالا)
    hungry = []
    for organ, rec in (snap.get("organs") or {}).items():
        if rec.get("denial_rate", 0.0) >= 0.5 and rec.get("denied_count", 0) > 0:
            hungry.append({"organ": organ, **{k: v for k, v in rec.items()
                                             if k != "top_reasons"}})
    snap["hungry_organs"] = hungry
    snap["enabled"] = enabled()
    snap["flag"] = FLAG
    return snap


if __name__ == "__main__":
    print(json.dumps(report(), ensure_ascii=False, indent=2))
