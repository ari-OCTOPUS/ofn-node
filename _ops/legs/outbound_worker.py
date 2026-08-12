#!/usr/bin/env python3
"""outbound_worker.py — Trust-Engine P0 · LEAD-SAFETY-C1 → Lane G: workerِ ارسالِ خروجی.

تاریخچه: تا ۲۰۲۶-۰۷-۳۱ هر adapter یک stubِ NOT_ARMED بود. با رأیِ ARM ِ مالک
(۲۰۲۶-۰۷-۳۱، رأی ۱۷ منشورِ TG-UI) کانالِ **email** به آداپترِ واقعیِ
`lead_outbound_transport` وصل شد. شبِ ۰۷-۳۱ لوله واقعاً بسته شد: credential از
`mail_credentials.resolve()` می‌آید — یا ۵ متغیرِ صریحِ `OCTOPUS_SMTP_*`، یا
fallback ِ Gmail (`GMAIL_ADDRESS`/`GMAIL_APP_PASSWORD` ِ موجود در `.env`) پشتِ
فلگِ `OCTOPUS_SMTP_USE_GMAIL`. حل‌نشدن = NOT_ARMED ِ صادق **با دلیلِ دقیق**
(نه سکوت). arming ِ عملی همچنان تصمیمِ deploy ِ مالک است، نه کد.
بقیهٔ کانال‌ها stub می‌مانند.

خطوطِ قرمز (LEAD-SAFETY-C1 + رأی ۱۷):
  · این ماژول خودش هیچ import شبکه ندارد؛ ارسالِ واقعی فقط در lead_outbound_transport.
  · flag OCTOPUS_WIRE_LEAD_OUTBOUND خاموش = بی‌اثرِ مطلق.
  · ارسال فقط از مسیرِ lead_effect_gate.release_and_settle (STOP/consent/authorization/idempotent).
  · سقفِ روزانهٔ عددی LEAD_DAILY_SEND_CAP=10 (رأی مالک ۲۰۲۶-۰۷-۳۱) در **دو** لایه:
    may_release (deny «daily-cap») + همین worker (کمربندِ CAP_REACHED **قبل از**
    release/settle — بازبینی ۰۷-۳۱: سقف‌خورده هرگز settle نمی‌شود).
    شمارنده فقط با sent=True ِ تأییدشدهٔ transport بالا می‌رود.
  · GAP-2 (۲۰۲۶-۰۸-۰۱): بدنهٔ ایمیل باید **مبلغِ ثبت‌شدهٔ کوت** را داشته باشد.
    منبع فقط `breakdown.total_incl_gst` ِ رکوردِ lead-quote.v1 (یا همان عدد در
    `proposal.payload.price_range_aud`) — بدونِ هیچ re-compute. کوتِ بی‌مبلغ
    ارسال نمی‌شود: skip + رسیدِ `no-price:<دلیل>` + alert به مالک (نه ارسالِ
    بی‌قیمت، نه سکوت). خطِ opt-out (الزامِ انطباق) دست‌نخورده می‌مانَد.
  · consent_gate D2a (۲۰۲۶-۰۸-۰۷): `consent_gate.may_draft`/`may_release` (store-backed،
    لایهٔ سومِ مستقلِ consent — جدا از consent_firewall ِ داخلِ lead_effect_gate) حالا
    دو نقطهٔ اتصالِ تولیدی دارند: may_draft قبلِ compose در `drive_outbound`، may_release
    قبلِ `release_and_settle` در `send_one`. deny = designed compliance gate، نه شکست:
    status=`consent-denied` (نه NOT_ARMED/FAILED)، هرگز alert، effect دست‌نخورده می‌مانَد.

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

# سقفِ روزانهٔ عددیِ ارسالِ لید — رأی مالک ۲۰۲۶-۰۷-۳۱ = ۱۰ پیش‌فرض.
# ۲۰۲۶-۰۸-۱۲: مالک «نمیخوام مرزی بمونه» → env override مجاز
# (OCTOPUS_LEAD_DAILY_SEND_CAP). مقدار ≤۰ = عملاً بدون سقف عددی
# (همچنان consent/effect_gate/STOP مقدم‌اند).
def _lead_daily_send_cap() -> int:
    raw = (os.environ.get("OCTOPUS_LEAD_DAILY_SEND_CAP") or "10").strip()
    try:
        n = int(raw)
    except ValueError:
        return 10
    return n


LEAD_DAILY_SEND_CAP = _lead_daily_send_cap()


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
    """سقفِ روزانه؛ ≤۰ = بدون سقف عددی (consent/STOP همچنان مقدم)."""
    global LEAD_DAILY_SEND_CAP
    LEAD_DAILY_SEND_CAP = _lead_daily_send_cap()
    if LEAD_DAILY_SEND_CAP <= 0:
        return False
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


# ── consent_gate D2a wiring (۲۰۲۶-۰۸-۰۷، رأیِ صریحِ مالک — چت مستقیم) ───────────────
# تا امشب `consent_gate.may_draft`/`may_release` صفر صداکنندهٔ تولیدی داشتند —
# تنها چیزی که «امن» نگهشان می‌داشت خاموش‌بودنِ OCTOPUS_WIRE_LEAD_OUTBOUND بود
# (تصمیمِ جداگانهٔ مالک). این‌جا لایهٔ سومِ مستقلِ consent وصل می‌شود (لایهٔ ۱:
# CHECK ساختاریِ consent_store؛ لایهٔ ۲: consent_firewall در lead_effect_gate —
# روی همان candidate dict که producer اعلام کرده؛ لایهٔ ۳ همین‌جا: consent_gate،
# store-backed، هرگز اعلامِ producer را نمی‌پذیرد، از persisted consent_current
# دوباره می‌خواند). دو نقطهٔ اتصال:
#   · may_draft — قبلِ compose در drive_outbound (پیش از _draft_for).
#   · may_release — قبلِ release_and_settle در send_one (نه بعدش — اگر بعد
#     چک شود و deny کند، effect برای‌همیشه سوخته می‌شود بدونِ transport؛ همان
#     دلیلِ historyِ کمربندِ cap_reached در send_one).
# rejectِ consent_gate «designed compliance gate» است، نه شکست: status ِ
# اختصاصیِ "consent-denied" (نه NOT_ARMED، نه FAILED) و **هرگز alert** —
# هم‌الگوی رفتارِ CAP_REACHED در همین فایل.
def _consent_check(kind: str, lead_id: str, *, effect_kind: str = "") -> tuple[bool, str]:
    """پوششِ فراخوانیِ consent_gate.may_draft/may_release با store ِ تازه (باز→پرسش→بسته،
    هم‌الگوی lead_outbound_transport._feed_suppression/_store_suppressed). خطای
    import/ساختِ store هم fail-closed (consent_gate خودش fail-closed است؛ این‌جا فقط
    لایهٔ محافظِ import). `kind`: "draft" یا "release"."""
    store = None
    try:
        import consent_store as _cs   # noqa: WPS433 — lazy، هم‌پوشه
        import consent_gate as _cg    # noqa: WPS433 — lazy، هم‌پوشه
        store = _cs.ConsentStore()
        if kind == "release":
            return _cg.may_release(lead_id, effect_kind, store=store)
        return _cg.may_draft(lead_id, store=store)
    except Exception as e:  # noqa: BLE001 — fail-closed حتی اگر import/ساخت بشکند
        return (False, f"consent-gate-unavailable:{type(e).__name__}")
    finally:
        if store is not None:
            try:
                store.close()
            except Exception:  # noqa: BLE001
                pass


# ── transport adapters — email واقعی (Lane G)، بقیه stubِ NOT_ARMED ────────────────
def _transport_for(channel: str, candidate: dict | None = None, now=None):
    """آداپترِ transport برای کانالِ ترجیحیِ مشتری.

    Lane G (رأی ۱۷، owner-armed در deploy): کانالِ «email» — یا کاندیدی که ایمیلِ تماس
    دارد — به آداپترِ واقعیِ lead_outbound_transport می‌رود (که اگر credential حل
    نشود خودش صادقانه NOT_ARMED می‌دهد). هر کانالِ دیگر همان stubِ NOT_ARMED ِ همیشگی است.
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
        # کمربندِ worker (defense in depth) — **قبل از** release_and_settle
        # (بازبینی ۰۷-۳۱، security W1): نسخهٔ قبلی این چک را بعدِ settle داشت،
        # پس اگر لایهٔ گیت (may_release) رگرس می‌شد، effect ِ سقف‌خورده اول
        # settle می‌شد (مصرف می‌شد) و بعد ارسال رد می‌شد — settle-بی‌ارسال =
        # effect ِ برای‌همیشه‌سوخته. سقف باید پیش از هر مصرفِ گیت بایستد؛
        # effect دست‌نخورده (releasable) می‌مانَد و بعدِ rollover می‌رود.
        if cap_reached(now=_now_s):
            _receipt("send.cap_reached", effect_id,
                     {"cap": LEAD_DAILY_SEND_CAP, "layer": "worker",
                      "sent_today": sends_today(now=_now_s)})
            return {"ok": False, "sent": False, "status": "CAP_REACHED",
                    "gate_reason": "daily-cap"}
        # consent_gate D2a wiring — may_release **قبل از** release_and_settle، هم‌جای
        # کمربندِ cap_reached بالا و به همان دلیل (effect دست‌نخورده/releasable بماند،
        # نه برای‌همیشه‌سوخته). لایهٔ سومِ مستقلِ consent، جدا از consent_firewall ِ
        # داخلِ lead_effect_gate — می‌تواند suppression/compliance/synthetic-hard-block
        # را که آن لایه نمی‌بیند بگیرد. rejectِ آن طراحی‌شده است، نه شکست: هیچ alert.
        lead_id = str((candidate or {}).get("lead_id") or "")
        c_ok, c_why = _consent_check("release", lead_id, effect_kind="lead_outbound")
        if not c_ok:
            _receipt("send.consent_denied", effect_id,
                     {"lead_id": lead_id, "reason": c_why})
            return {"ok": False, "sent": False, "status": "consent-denied",
                    "gate_reason": c_why}
        res = leg.release_and_settle(effect_id, candidate, gate=gate, now_ms=now_ms)
        if not res.get("settled"):
            # گیت اجازه نداد → هیچ transportی صدا نمی‌شود (هیچ ارسال).
            if str(res.get("reason")) == "daily-cap":
                # سقفِ روزانه (رأی مالک ۲۰۲۶-۰۷-۳۱: ۱۰) — لایهٔ گیت هم deny
                # می‌کند (may_release)؛ effect releasable می‌مانَد و فردا
                # (پس از rollover) دوباره می‌تواند برود.
                _receipt("send.cap_reached", effect_id,
                         {"cap": LEAD_DAILY_SEND_CAP, "layer": "gate",
                          "sent_today": sends_today(now=_now_s)})
                return {"ok": False, "sent": False, "status": "CAP_REACHED",
                        "gate_reason": "daily-cap"}
            return {"ok": False, "sent": False, "status": "gate_denied",
                    "gate_reason": res.get("reason")}
        # گیت settle کرد و سقف باز است؛ حالا transport (email = آداپترِ واقعیِ Lane G؛
        # بقیه stub). آداپترِ واقعی بدونِ envِ SMTP خودش NOT_ARMED می‌دهد.
        channel = str(((candidate or {}).get("contact") or {}).get("preferred_channel")
                      or ((candidate or {}).get("source") or {}).get("channel") or "unknown")
        out = _transport_for(channel, candidate, now=_now_s)(candidate, draft)
        if not out.get("sent") and str(out.get("status") or "") != "NOT_ARMED":
            # ۲۰۲۶-۰۸-۰۶: همان کلاسِ آلارمِ گمراه‌کنندهٔ امشب (model_router/
            # deep_think/self_patch — سقفِ روزانهٔ فوگو را «خرابی» می‌خواندند).
            # اینجا معادلش NOT_ARMED است: طبق docstring بالای فایل، هر کانالِ
            # غیرایمیل عمداً stub است («بقیهٔ کانال‌ها stub می‌مانند») — این
            # حالتِ طراحی‌شده روی **هر** effectِ کانالِ غیرایمیل رخ می‌دهد، نه
            # یک اتفاقِ نادر، پس alert کردنِ آن فقط نویزِ گرگ‌گرگ می‌سازد (رجوع:
            # درسِ «گاردِ گرگ‌گرگ خاموش می‌شود»). فقط شکستِ واقعیِ یک کانالِ
            # مسلح (مثلاً email با creds ولی SMTP ناموفق) alarming باقی می‌مانَد.
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


# ── درایورِ ارسال (بازبینی ۰۷-۳۱، wiring W2 — flag-off در deploy: تاریک ولی کامل) ──
def _candidate_from_inbox(lead_id: str):
    """بازسازیِ **فقط‌خواندنیِ** کاندید از `lead_sense.resolve_lead_path` (inbox یا
    processed/، هر کدام تازه‌تر بود — رفعِ قفلِ دوتایی ۲۰۲۶-۰۸-۰۳؛ همان مسیری که
    lead_effect_gate.bridge_from_inbox می‌گیرد، شاملِ contact تا transport گیرنده
    داشته باشد). خروجی: (candidate|None, attribution_id) — نبود/خراب ⇒ (None, "")."""
    try:
        lid = str(lead_id or "").strip()
        if not lid:
            return None, ""
        import lead_sense   # noqa: WPS433 — lazy، هم‌پوشه
        path = lead_sense.resolve_lead_path(lid)
        if path is None:
            return None, ""
        data = json.loads(path.read_text("utf-8"))
        if not isinstance(data, dict):
            return None, ""
        cb = data.get("candidate") or {}
        cand = {"lead_id": lid,
                "source": {"channel": data.get("source")},
                "candidate_type": cb.get("candidate_type"),
                "consent": cb.get("consent") or {},
                "request": cb.get("request") or {},
                "contact": cb.get("contact") or {}}
        aid = str(data.get("attribution_id") or cb.get("attribution_id") or "")
        return cand, aid
    except (OSError, ValueError, TypeError):
        return None, ""


# ── قیمت در بدنهٔ ایمیل (GAP-2، ۲۰۲۶-۰۸-۰۱) ──────────────────────────────────
# تا امروز بدنهٔ ایمیلِ مشتری فقط `intake.scope` بود — یعنی «کوت»ی که هیچ عددی
# نداشت. عدد از هوا ساخته نمی‌شود و **هرگز دوباره محاسبه نمی‌شود**: تنها منبعِ
# مجاز همان چیزی است که `lead_quote.create_quote` پایدار کرده —
# `breakdown.total_incl_gst` (بازهٔ [lo, hi] ِ شاملِ GST، خروجیِ
# `pricing.estimate_price`). مسیرِ دومِ **همان** عدد
# `proposal.payload.price_range_aud` است (نوشتهٔ `lead_leg.draft_quote` از روی
# همان bd_dict). re-compute ممنوع است چون نرخ‌های `pricing.py` تغییر می‌کنند و
# آن‌وقت عددِ ایمیل با عددِ ثبت‌شدهٔ کوت یکی نمی‌ماند — مشتری و دفتر دو عدد
# متفاوت می‌بینند.
AUD_PREFIX = "A$"


def _finite(v):
    """floatِ متناهی یا None. bool عدد نیست؛ رشتهٔ عددی پذیرفته می‌شود."""
    import math as _math   # noqa: WPS433
    if isinstance(v, bool):
        return None
    try:
        f = float(v)
    except (TypeError, ValueError):
        return None
    return f if _math.isfinite(f) else None


def _price_range(rec: dict):
    """بازهٔ قیمتِ **ثبت‌شدهٔ** همان کوت. خروجی: ((lo, hi), "") یا (None, "<دلیل>").

    دلیلِ ردشدن هرگز خالی نیست — صداکننده باید بتواند به مالک بگوید چرا این
    کوت ایمیل نشد (سکوت = همان باگی که این گارد می‌بندد)."""
    r = rec if isinstance(rec, dict) else {}
    bd = r.get("breakdown")
    src = bd.get("total_incl_gst") if isinstance(bd, dict) else None
    if src is None:
        prop = r.get("proposal")
        pay = prop.get("payload") if isinstance(prop, dict) else None
        src = pay.get("price_range_aud") if isinstance(pay, dict) else None
    if src is None:
        return None, "missing"
    if not isinstance(src, (list, tuple)) or len(src) != 2:
        return None, "malformed"
    lo, hi = _finite(src[0]), _finite(src[1])
    if lo is None or hi is None:
        return None, "non-numeric"
    if lo <= 0 or hi <= 0:
        return None, "zero-or-negative"
    if hi < lo:
        return None, "inverted"
    return (lo, hi), ""


def format_aud(lo, hi) -> str:
    """قالبِ پولی که مشتریِ استرالیایی انتظار دارد:
    نمادِ `A$` (نه `$` ِ مبهم)، کامای هزارگان، دو رقمِ اعشار، و افشای صریحِ GST
    (قیمتِ اعلامیِ مصرف‌کننده در استرالیا شاملِ GST است). بازه با en-dash؛
    lo == hi ⇒ یک عدد، نه بازهٔ تکراری."""
    lo_f, hi_f = float(lo), float(hi)
    lo_s = f"{AUD_PREFIX}{lo_f:,.2f}"
    hi_s = f"{AUD_PREFIX}{hi_f:,.2f}"
    body = lo_s if abs(hi_f - lo_f) < 0.005 else f"{lo_s} – {hi_s}"
    return f"{body} (incl. GST)"


def _draft_for(attribution_id: str):
    """پیش‌نویسِ ارسال از state/legs/lead-drafts/<attribution_id>.json — best-effort.
    فقط رکوردِ lead-quote.v1.

    خروجی: `(draft|None, reason)` — reason ِ خالی یعنی پیش‌نویس سالم است.
      · نبودِ فایل / JSON خراب / schema ِ دیگر ⇒ `(None, "no-draft")`
      · رکورد هست ولی مبلغِ ثبت‌شده ندارد (نبود/صفر/غیرعددی/وارونه) ⇒
        `(None, "no-price:<جزئیات>")` — ایمیلِ بی‌عدد **کوت نیست**؛ صداکننده
        skip می‌کند و مالک را خبر می‌کند، نه اینکه یک «کوت»ِ خالی بفرستد."""
    try:
        import re as _re   # noqa: WPS433
        aid = str(attribution_id or "").strip()
        if not aid:
            return None, "no-draft"
        safe = _re.sub(r"[^A-Za-z0-9_\-]", "-", aid)[:64]
        p = opslib.STATE_DIR / "legs" / "lead-drafts" / f"{safe}.json"
        if not p.exists():
            return None, "no-draft"
        rec = json.loads(p.read_text("utf-8"))
        if not isinstance(rec, dict) or rec.get("schema") != "lead-quote.v1":
            return None, "no-draft"
        rng, why = _price_range(rec)
        if rng is None:
            return None, f"no-price:{why}"
        scope = str(((rec.get("intake") or {}).get("scope") or "")).strip()
        qt = str(rec.get("qt_number") or aid)
        body = "\n".join([scope or "Please find our quotation below.", "",
                          f"Total price: {format_aud(rng[0], rng[1])}"])
        return {"subject": f"Quote {qt} — painting works", "body": body,
                "price_aud": [rng[0], rng[1]]}, ""
    except (OSError, ValueError, TypeError):
        return None, "no-draft"


def drive_outbound(*, gate, now_ms: int | None = None, cap_per_beat: int = 2) -> dict:
    """درایورِ قوسِ ارسال: effectهای authorized-ولی-unsettled ِ lead_outbound را
    یکی‌یکی از send_one (گیتِ per-effect → transport) عبور می‌دهد.

    مرزها (همان خطوطِ قرمزِ send_one، به‌علاوهٔ سقفِ ضربان):
      · فلگِ اصلی OCTOPUS_WIRE_LEAD_OUTBOUND **اول** چک می‌شود — خاموش ⇒
        {"driven": 0} و صفر اثرِ جانبی (هیچ خواندن/رسید/گیت).
      · halt سراسری مقدم؛ gate ِ غایب = هیچ.
      · کاندید از lead-inbox/<lead_id>.json بازسازی می‌شود (الگوی
        bridge_from_inbox شاملِ contact)؛ نبودش ⇒ skip با رسیدِ "no-candidate".
      · پیش‌نویس از lead-drafts/<attribution_id>.json؛ نبودش ⇒ skip با رسیدِ
        "no-draft" — ارسالِ بی‌پیش‌نویس ممنوع.
      · GAP-2 (۰۸-۰۱): پیش‌نویسِ بدونِ **مبلغِ ثبت‌شده** ⇒ skip با رسیدِ
        "no-price:<دلیل>" + alert به مالک. «کوت»ِ بی‌عدد کوت نیست؛ نه ارسالِ
        بی‌قیمت، نه سکوت.
      · توقف در cap_per_beat (پیش‌فرض ۲) یا سقفِ روزانهٔ ۱۰.
      · consent/authz/idempotency/سقف همه داخلِ send_one دوباره حاکم‌اند —
        market_signal حتی اگر به‌زور authorize شده باشد همان‌جا deny می‌شود.
    همیشه dict؛ هرگز استثنا."""
    out = {"driven": 0, "sent": 0, "skipped": 0, "results": []}
    try:
        if not enabled():
            return {"driven": 0}
        if opslib.master_halted():
            return {"driven": 0, "reason": "halted"}
        if gate is None:
            return {"driven": 0, "reason": "no-gate"}
        sys.path.insert(0, str(_HERE))
        import lead_effect_gate as leg   # noqa: WPS433 — lazy، هم‌پوشه
        _now_s = (float(now_ms) / 1000.0) if now_ms is not None else None
        for rec in leg.list_authorized():
            if out["driven"] >= int(cap_per_beat) or cap_reached(now=_now_s):
                break
            eid = str(rec.get("effect_id") or "")
            lid = str(rec.get("lead_id") or "")
            try:
                st = gate.status_of(eid)
            except Exception:  # noqa: BLE001 — گیتِ ناخوانا = skip، نه crash
                continue
            if st not in ("pending", "releasable"):
                continue                 # settled/refused/ناشناخته — idempotent skip
            cand, aid = _candidate_from_inbox(lid)
            if cand is None:
                _receipt("send.skipped", eid,
                         {"reason": "no-candidate", "lead_id": lid})
                out["skipped"] += 1
                continue
            # consent_gate D2a wiring — may_draft **قبل از** compose (_draft_for).
            # draft ساخته نمی‌شود اگر رضایتِ store-backed اجازه نمی‌دهد — حتی اگر
            # candidateِ inbox چیزِ دیگری اعلام کرده باشد (consent_gate هرگز اعلامِ
            # producer را نمی‌پذیرد). rejectِ آن طراحی‌شده است: صرفاً skip، هیچ alert.
            d_ok, d_why = _consent_check("draft", lid)
            if not d_ok:
                _receipt("send.skipped", eid,
                         {"reason": f"consent-denied:{d_why}", "lead_id": lid})
                out["skipped"] += 1
                continue
            draft, why = _draft_for(aid)
            if draft is None:
                reason = why or "no-draft"
                _receipt("send.skipped", eid,
                         {"reason": reason, "lead_id": lid,
                          "attribution_id": aid})
                if reason.startswith("no-price"):
                    # GAP-2: کوتِ بی‌عدد ایمیل نمی‌شود — ولی مالک هم بی‌خبر
                    # نمی‌مانَد. رسید همیشه نوشته می‌شود (بالا)؛ این alert
                    # همان رسید را به چشمِ مالک می‌رسانَد. سکوت پذیرفته نیست.
                    try:
                        opslib.alert([f"کوتِ لید بدونِ مبلغ بود و ایمیل نشد "
                                      f"(lead={lid}، quote={aid}، {reason}) — "
                                      f"قیمت را در پیش‌نویس بگذار"])
                    except Exception:  # noqa: BLE001
                        pass
                out["skipped"] += 1
                continue
            r = send_one(eid, cand, draft, gate=gate, now_ms=now_ms)
            out["driven"] += 1
            out["results"].append({"effect_id": eid, "status": r.get("status"),
                                   "sent": bool(r.get("sent"))})
            if r.get("sent"):
                out["sent"] += 1
            if r.get("status") in ("CAP_REACHED", "halted"):
                break
        return out
    except Exception as e:  # noqa: BLE001 — درایور هرگز beat را نمی‌کشد
        out["reason"] = f"driver_error:{type(e).__name__}"
        return out


if __name__ == "__main__":
    import json
    try:
        import mail_credentials as _mc   # noqa: WPS433 — هم‌پوشه
        _cred = {"armed": bool(_mc.status().get("ok")),
                 "how": _mc.status().get("how"),
                 "reason": _mc.status().get("reason")}
    except Exception as _e:  # noqa: BLE001
        _cred = {"armed": False, "how": None,
                 "reason": f"mail_credentials-unavailable:{type(_e).__name__}"}
    print(json.dumps({"enabled": enabled(), "cap": LEAD_DAILY_SEND_CAP,
                      "sent_today": sends_today(), "credentials": _cred,
                      "note": "email = آداپترِ واقعی؛ بقیهٔ کانال‌ها stub. "
                              "سقفِ روزانه = رأی مالک ۲۰۲۶-۰۷-۳۱."},
                     ensure_ascii=False))
