#!/usr/bin/env python3
"""outbound_worker.py — Trust-Engine P0 · LEAD-SAFETY-C1 → Lane G: workerِ ارسالِ خروجی.

تاریخچه: تا ۲۰۲۶-۰۷-۳۱ هر adapter یک stubِ NOT_ARMED بود. با رأیِ ARM ِ مالک
(۲۰۲۶-۰۷-۳۱، رأی ۱۷ منشورِ TG-UI) کانالِ **email** به آداپترِ واقعیِ
`lead_outbound_transport` وصل شد — که خودش بدونِ ۵ envِ SMTP صادقانه NOT_ARMED
می‌دهد (arming ِ عملی = ستِ env در deploy، نه کد). بقیهٔ کانال‌ها stub می‌مانند.

خطوطِ قرمز (LEAD-SAFETY-C1 + رأی ۱۷):
  · این ماژول خودش هیچ import شبکه ندارد؛ ارسالِ واقعی فقط در lead_outbound_transport.
  · flag OCTOPUS_WIRE_LEAD_OUTBOUND خاموش = بی‌اثرِ مطلق.
  · ارسال فقط از مسیرِ lead_effect_gate.release_and_settle (STOP/consent/authorization/idempotent).
  · سقفِ روزانهٔ عددی LEAD_DAILY_SEND_CAP=10 (رأی مالک ۲۰۲۶-۰۷-۳۱) در **دو** لایه:
    may_release (deny «daily-cap») + همین worker (کمربندِ CAP_REACHED قبل از transport).
    شمارنده فقط با sent=True ِ تأییدشدهٔ transport بالا می‌رود.

stdlib-only در خودِ این ماژول.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))
sys.path.insert(0, str(_HERE.parent / "budget"))
import opslib   # noqa: E402

FLAG = "OCTOPUS_WIRE_LEAD_OUTBOUND"

# سقفِ روزانهٔ عددیِ ارسالِ لید — رأی مالک ۲۰۲۶-۰۷-۳۱ (رأی ARM ِ رأی ۱۷ منشور
# TG-UI-CHARTER-2026-07-31): حداکثر ۱۰ ارسالِ خروجی در روز. تغییرِ این عدد فقط
# با رأیِ جدیدِ مالک — نه پروفایل، نه env، نه ایجنت.
LEAD_DAILY_SEND_CAP = 10


def enabled() -> bool:
    """flag خاموش (پیش‌فرض، خارج از PAPER_FULL) = worker بی‌اثر."""
    return os.environ.get(FLAG, "0") == "1"


# ── شمارندهٔ پایدارِ سقفِ روزانه (state/legs/lead-send-counter.json) ──────────────
def _counter_path() -> Path:
    """هم‌الگوی lead_effect_gate._authz_store: مسیرِ state در call-time از opslib."""
    return opslib.STATE_DIR / "legs" / "lead-send-counter.json"


def _day_str(now=None) -> str:
    """YYYY-MM-DD محلی — rollover نیمه‌شب با مقایسهٔ رشتهٔ تاریخ. now تزریق‌پذیر (ثانیه)."""
    import datetime as _dt   # noqa: WPS433
    if now is None:
        return _dt.date.today().isoformat()
    return _dt.date.fromtimestamp(float(now)).isoformat()


def sends_today(*, now=None) -> int:
    """شمارِ ارسال‌های تأییدشدهٔ امروز. فایلِ غایب = ۰ (حالتِ اولیهٔ عادی)؛
    فایلِ خراب = خودِ سقف (fail-closed: شمارِ نامعلوم = ارسالِ بیشتر ممنوع)."""
    p = _counter_path()
    try:
        raw = p.read_text("utf-8")
    except OSError:
        return 0                       # هرگز نوشته نشده — صفر ارسال
    try:
        d = json.loads(raw)
        if not isinstance(d, dict):
            raise ValueError("counter must be a dict")
        if str(d.get("date") or "") != _day_str(now):
            return 0                   # روزِ نو — rollover
        return max(0, int(d.get("sent", 0)))
    except (ValueError, TypeError):
        return LEAD_DAILY_SEND_CAP     # خراب = نامعلوم = fail-closed


def cap_reached(*, now=None) -> bool:
    return sends_today(now=now) >= LEAD_DAILY_SEND_CAP


def record_send(*, now=None) -> int:
    """افزایشِ اتمیکِ شمارنده — **فقط** پس از sent=True ِ تأییدشدهٔ transport صدا زده
    می‌شود (صداکننده: lead_outbound_transport). خروجی: شمارِ جدیدِ امروز."""
    n = sends_today(now=now) + 1
    p = _counter_path()
    try:
        p.parent.mkdir(parents=True, exist_ok=True)
        tmp = p.with_suffix(".json.tmp")
        tmp.write_text(json.dumps({"date": _day_str(now), "sent": n},
                                  ensure_ascii=False), "utf-8")
        os.replace(tmp, p)
    except (OSError, TypeError, ValueError):
        try:
            opslib.alert(["lead-send-counter نوشته نشد — سقفِ روزانه ممکن است کم بشمارد"])
        except Exception:  # noqa: BLE001
            pass
    return n


def _receipt(event_type: str, corr: str, payload: dict) -> None:
    """رسیدِ append-only در events.jsonl — هم‌الگوی lead_effect_gate._emit. هرگز raise."""
    import uuid   # noqa: WPS433
    try:
        opslib.append_jsonl(opslib.STATE_DIR / "legs" / "lead-inbox" / "events.jsonl", {
            "event_id": uuid.uuid4().hex, "event_type": event_type,
            "occurred_at": opslib.now_iso(), "correlation_id": str(corr or ""),
            "source_component": "OutboundWorker", "schema_version": "1.0",
            "payload": payload})
    except Exception:  # noqa: BLE001
        pass


# ── transport adapters — email واقعی (Lane G)، بقیه stubِ NOT_ARMED ────────────────
def _transport_for(channel: str, candidate: dict | None = None, now=None):
    """آداپترِ transport برای کانالِ ترجیحیِ مشتری.

    Lane G (رأی ۱۷، owner-armed در deploy): کانالِ «email» — یا کاندیدی که ایمیلِ تماس
    دارد — به آداپترِ واقعیِ lead_outbound_transport می‌رود (که بدونِ ۵ envِ SMTP خودش
    صادقانه NOT_ARMED می‌دهد). هر کانالِ دیگر همان stubِ NOT_ARMED ِ همیشگی است.
    `now` به transport پاس می‌شود (شمارندهٔ سقف با clock ِ تزریقی — نه ساعتِ نیمه‌تزریقی)."""
    def _stub(cand: dict, draft: str) -> dict:
        # هیچ ارسالِ واقعی: transport مسلح نیست. صرفاً نیت را ثبت می‌کند.
        return {"sent": False, "status": "NOT_ARMED", "channel": channel,
                "detail": "transport adapter is a stub — no real send is possible"}
    try:
        _contact = ((candidate or {}).get("contact") or {})
        _has_email = bool(str(_contact.get("email") or (candidate or {}).get("email")
                              or "").strip())
        if str(channel).strip().casefold() == "email" or _has_email:
            import lead_outbound_transport as _lot   # noqa: WPS433 — lazy، هم‌پوشه
            return lambda cand, draft: _lot.send(cand, draft, now=now)
    except Exception:  # noqa: BLE001 — نبودِ آداپتر = stub (هرگز crash، هرگز ارسالِ کور)
        pass
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
        _now_s = (float(now_ms) / 1000.0) if now_ms is not None else None
        res = leg.release_and_settle(effect_id, candidate, gate=gate, now_ms=now_ms)
        if not res.get("settled"):
            # گیت اجازه نداد → هیچ transportی صدا نمی‌شود (هیچ ارسال).
            if str(res.get("reason")) == "daily-cap":
                # سقفِ روزانه (رأی مالک ۲۰۲۶-۰۷-۳۱: ۱۰) — گیت deny کرد؛ effect
                # releasable می‌مانَد و فردا (پس از rollover) دوباره می‌تواند برود.
                _receipt("send.cap_reached", effect_id,
                         {"cap": LEAD_DAILY_SEND_CAP, "layer": "gate",
                          "sent_today": sends_today(now=_now_s)})
                return {"ok": False, "sent": False, "status": "CAP_REACHED",
                        "gate_reason": "daily-cap"}
            return {"ok": False, "sent": False, "status": "gate_denied",
                    "gate_reason": res.get("reason")}
        # کمربندِ دوم (defense in depth): چکِ سقف بینِ settle ِ گیت و transport —
        # اگر لایهٔ گیت رگرس شد، این‌جا هم هیچ transportی صدا نمی‌شود.
        if cap_reached(now=_now_s):
            _receipt("send.cap_reached", effect_id,
                     {"cap": LEAD_DAILY_SEND_CAP, "layer": "worker",
                      "sent_today": sends_today(now=_now_s)})
            return {"ok": False, "sent": False, "status": "CAP_REACHED",
                    "gate_reason": res.get("reason")}
        # گیت settle کرد و سقف باز است؛ حالا transport (email = آداپترِ واقعیِ Lane G؛
        # بقیه stub). آداپترِ واقعی بدونِ envِ SMTP خودش NOT_ARMED می‌دهد.
        channel = str(((candidate or {}).get("contact") or {}).get("preferred_channel")
                      or ((candidate or {}).get("source") or {}).get("channel") or "unknown")
        out = _transport_for(channel, candidate, now=_now_s)(candidate, draft)
        if not out.get("sent"):
            try:
                opslib.alert([f"lead outbound cleared gate ولی transport نفرستاد "
                              f"(eid={effect_id}, ch={channel}, "
                              f"status={out.get('status')}) — no send"])
            except Exception:  # noqa: BLE001
                pass
        return {"ok": True, "sent": bool(out.get("sent")), "status": out.get("status"),
                "channel": channel, "gate_reason": res.get("reason")}
    except Exception as e:  # noqa: BLE001 — worker هرگز crash نمی‌کند و هرگز نمی‌فرستد
        return {"ok": False, "sent": False, "status": "worker_error", "reason": type(e).__name__}


if __name__ == "__main__":
    import json
    print(json.dumps({"enabled": enabled(), "cap": LEAD_DAILY_SEND_CAP,
                      "sent_today": sends_today(),
                      "note": "email = آداپترِ واقعی (بدونِ envِ SMTP هنوز NOT_ARMED)؛ "
                              "بقیهٔ کانال‌ها stub. سقفِ روزانه = رأی مالک ۲۰۲۶-۰۷-۳۱."},
                     ensure_ascii=False))
