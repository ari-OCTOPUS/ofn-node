#!/usr/bin/env python3
"""outbound_worker.py — Trust-Engine P0 · LEAD-SAFETY-C1: workerِ ارسالِ خروجی که **نمی‌فرستد**.

اسکلتِ مسیرِ ارسالِ لید که عمداً هیچ transportِ واقعی ندارد: هر adapter یک stub است که
`NOT_ARMED` برمی‌گرداند. تنها مسیرِ آزادسازی از `lead_effect_gate` (per-effect، fail-closed)
می‌گذرد — هرگز مستقیم به شبکه، هرگز batch. این ماژول قوسِ ارسال را «سیم‌کشی‌شده ولی مسلح‌نشده»
می‌کند: پلامبینگ کامل و امن است، ولی هیچ بایتی به دنیای واقعی نمی‌رود.

خطوطِ قرمز (LEAD-SAFETY-C1):
  · هیچ import شبکه (smtplib/requests/twilio/…). transport = stubِ NOT_ARMED.
  · flag OCTOPUS_WIRE_LEAD_OUTBOUND خاموش = بی‌اثرِ مطلق.
  · dry-run پیش‌فرض؛ حتی با فلگ روشن، هیچ ارسالِ واقعی (transport مسلح نیست).
  · ارسال فقط از مسیرِ lead_effect_gate.release_and_settle (STOP/consent/authorization/idempotent).

stdlib-only. propose-only تا مالک صریحاً transport مسلح کند (رأیِ جدا، خارج از این جلسه).
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))
sys.path.insert(0, str(_HERE.parent / "budget"))
import opslib   # noqa: E402

FLAG = "OCTOPUS_WIRE_LEAD_OUTBOUND"


def enabled() -> bool:
    """flag خاموش (پیش‌فرض، خارج از PAPER_FULL) = worker بی‌اثر."""
    return os.environ.get(FLAG) == "1"


# ── transport adaptersِ stub — هیچ‌کدام نمی‌فرستند (NOT_ARMED) ─────────────────────
def _transport_for(channel: str):
    """آداپترِ transport برای کانالِ ترجیحیِ مشتری. همه stubِ NOT_ARMED‌اند تا مالک مسلح کند."""
    def _stub(candidate: dict, draft: str) -> dict:
        # هیچ ارسالِ واقعی: transport مسلح نیست. صرفاً نیت را ثبت می‌کند.
        return {"sent": False, "status": "NOT_ARMED", "channel": channel,
                "detail": "transport adapter is a stub — no real send is possible"}
    return _stub


def send_one(effect_id: str, candidate: dict, draft: str = "", *, gate, now_ms: int | None = None) -> dict:
    """یک effectِ لید را (اگر flag روشن) از گیتِ per-effect بگذران و به transport بده.
    همیشه dict؛ هرگز استثنا؛ هرگز ارسالِ واقعی.

    خروجی: {ok, sent, status, gate_reason?, reason?}
    """
    # D1 (2026-07-23): halt-authorityِ سراسری supreme است — قبل از flag و قبل از هر gate/
    # transport رد کن، نه با تکیه بر settle-gateِ downstream یا stubِ NOT_ARMED. master_halted()
    # = HALT-ALL ← architect STOP (تک‌oracleِ opslib). fail-closed؛ صفر ارسال زیرِ halt.
    _halt = opslib.master_halted()
    if _halt:
        return {"ok": False, "sent": False, "status": "halted", "reason": _halt}
    if not enabled():
        return {"ok": False, "sent": False, "status": "flag_off", "reason": "OCTOPUS_WIRE_LEAD_OUTBOUND off"}
    try:
        sys.path.insert(0, str(_HERE))
        import lead_effect_gate as leg   # noqa: WPS433 — lazy، هم‌پوشه
        res = leg.release_and_settle(effect_id, candidate, gate=gate, now_ms=now_ms)
        if not res.get("settled"):
            # گیت اجازه نداد → هیچ transportی صدا نمی‌شود (هیچ ارسال).
            return {"ok": False, "sent": False, "status": "gate_denied",
                    "gate_reason": res.get("reason")}
        # گیت settle کرد؛ حالا transport — که stub است و NOT_ARMED می‌دهد (هیچ ارسال).
        channel = str(((candidate or {}).get("contact") or {}).get("preferred_channel")
                      or ((candidate or {}).get("source") or {}).get("channel") or "unknown")
        out = _transport_for(channel)(candidate, draft)
        try:
            opslib.alert([f"lead outbound cleared gate but transport NOT_ARMED "
                          f"(eid={effect_id}, ch={channel}) — no send"])
        except Exception:  # noqa: BLE001
            pass
        return {"ok": True, "sent": bool(out.get("sent")), "status": out.get("status"),
                "channel": channel, "gate_reason": res.get("reason")}
    except Exception as e:  # noqa: BLE001 — worker هرگز crash نمی‌کند و هرگز نمی‌فرستد
        return {"ok": False, "sent": False, "status": "worker_error", "reason": type(e).__name__}


if __name__ == "__main__":
    import json
    print(json.dumps({"enabled": enabled(),
                      "note": "flag روشن هم = NOT_ARMED؛ transport مسلح نیست. صفر ارسال."},
                     ensure_ascii=False))
