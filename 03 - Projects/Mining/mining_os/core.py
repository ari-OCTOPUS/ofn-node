"""core.py — ``mining_beat``: تنها نقطهٔ ورودِ زیر-OSِ Mining به اختاپوس.

قرارداد (منطبق با الگوی business_legs_beat / make_ziman_leg):
  fail-soft · هرگز crash · فقط‌خواندنی · live=False تا دادهٔ واقعیِ ناوگان/برق.
اختاپوس این تابع را در هر beat صدا می‌زند و خروجی را زیرِ ⛏ (Topic 24) منتشر می‌کند.
"""
from __future__ import annotations

from datetime import datetime, timezone

from .organs.governance import electricity_gate, wallet_access_allowed
from .brains.hardware_brain import summarize_fleet
from .brains.coin_brain import summarize_coins


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def mining_beat(state: dict | None = None) -> dict:
    """snapshotِ فقط‌خواندنیِ زیر-OSِ Mining. هرگز استثنا پرتاب نمی‌کند."""
    try:
        if not isinstance(state, dict) or not isinstance(state.get("fleet"), dict):
            return _skeleton("no state wired yet")

        raw_fleet = state.get("fleet", {})
        fleet = summarize_fleet(raw_fleet)
        coins = summarize_coins(state.get("coins", {}))
        gate, gate_reason = electricity_gate(
            raw_fleet.get("electricity_price_kwh"),
            bool(raw_fleet.get("solar", False)),
        )
        blockers = list(state.get("blockers", []))
        open_verdicts = [v for v in state.get("verdicts", [])
                         if str(v.get("status", "open")).lower() == "open"]

        electricity_known = (raw_fleet.get("electricity_price_kwh") is not None
                             or bool(raw_fleet.get("solar", False)))
        # نامتغیرِ صداقت: live فقط با وضعیتِ نودِ واقعی + برقِ معلوم
        live = bool(fleet["nodes_total"] > 0 and fleet["status_known"] and electricity_known)

        readiness, reasons = _readiness(fleet, gate, blockers, coins)

        return {
            "leg": "mining",
            "live": live,
            "signal": "live" if live else "skeleton",
            "phase": state.get("phase", "P0"),
            "generated": _now(),
            "fleet": fleet,
            "coins": {"count": coins["count"], "top": coins["top"]},
            "electricity": {"gate": gate, "reason": gate_reason},
            "halt_proposal": gate == "HALT",
            "readiness": {"score": readiness, "reasons": reasons},
            "verdicts_open": len(open_verdicts),
            "open_verdict_ids": [v.get("id") for v in open_verdicts],
            "blockers": blockers,
            "wallet_access": wallet_access_allowed(),   # همیشه False (D-11)
            "note": _note(live, gate, blockers),
        }
    except Exception as exc:  # noqa: BLE001 — fail-soft، ارگانیسم نباید بترکد
        return _skeleton(f"beat error (fail-soft): {type(exc).__name__}")


def _skeleton(reason: str) -> dict:
    return {
        "leg": "mining", "live": False, "signal": "skeleton", "phase": "P0",
        "generated": _now(),
        # ۲۰۲۶-۰۸-۰۱ — اسکلت باید **همان شش کلیدی** را بدهد که summarize_fleet می‌دهد.
        # سه کلید غایب بود و UI کلیدِ غایب را ۰/«—» چاپ می‌کرد، یعنی به مالک می‌گفت
        # «اندازه گرفتیم، صفر بود» در حالی که اصلاً اندازه‌گیری نشده.
        "fleet": {"nodes_total": 0, "running": 0, "broken": 0, "unknown": 0,
                  "status_known": False, "thermal_warn": []},
        "coins": {"count": 0, "top": []}, "electricity": {"gate": "HALT", "reason": "نامعلوم"},
        # gate این‌جا "HALT" است پس halt_proposal هم باید True باشد — دقیقاً کاری که
        # مسیرِ زنده (`halt_proposal = gate == "HALT"`) می‌کند. تا امروز False بود و
        # کارت رویِ گیتِ HALT «برق OK» چاپ می‌کرد.
        "halt_proposal": True, "readiness": {"score": 0, "reasons": [reason]},
        "verdicts_open": 0, "open_verdict_ids": [], "blockers": [],
        "wallet_access": False,
        "note": f"skeleton — {reason} · scorer/afferent سیم‌کشی نشده؛ live جعل نمی‌شود.",
    }


def _readiness(fleet, gate, blockers, coins):
    score, reasons = 0, []
    if fleet["nodes_total"] > 0:
        score += 20; reasons.append("رجیستری سخت‌افزار موجود")
    else:
        reasons.append("رجیستری خالی")
    if fleet["running"] > 0:
        score += 25; reasons.append("حداقل یک نود running")
    else:
        reasons.append("هیچ نود running نیست")
    if gate == "OK":
        score += 25; reasons.append("گیت برق عبور کرد")
    else:
        reasons.append("گیت برق نامشخص/HALT")
    if not blockers:
        score += 15; reasons.append("بلاکر باز ندارد")
    else:
        reasons.append(f"{len(blockers)} بلاکر باز")
    if coins["count"] > 0:
        score += 15; reasons.append("کاندید کوین دارد")
    else:
        reasons.append("کاندید کوین ندارد")
    return min(score, 100), reasons


def _note(live, gate, blockers) -> str:
    if not live:
        return "اسکلتِ صادق — تا دادهٔ واقعیِ ناوگان/برق، live جعل نمی‌شود."
    if gate == "HALT":
        return "⚠️ گیت برق HALT — پیشنهادِ توقف (اجرا فقط با verdictِ مالک)."
    return "leg زنده (propose-only؛ هر اقدامِ اجرایی پشتِ کارتِ تأیید)."
