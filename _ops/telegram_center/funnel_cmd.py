"""funnel_cmd — مالک واقعیتِ بازار را به ارگانیسم می‌گوید (D3b).

چرا این مهم‌ترین حلقهٔ گمشده بود
────────────────────────────────
`outcomes/funnel_store.py` کاملاً نوشته شده — SQLite، append-only، fold، متریک —
و در سربرگِ خودش نوشته: «دستوراتِ مالک (`/sent /replied /meeting /won /lost
/dead`) در D3b. این store صرفاً داده‌خور/خواننده است، **صفر caller** تا wiring
بعداً.» آن wiring هرگز ساخته نشد. اسکنِ ۲۰۲۶-۰۷-۲۷ ماژول را به‌عنوان یتیم پیدا
کرد و شش ایجنتِ مستقل تأیید کردند که «نتیجهٔ بازار» نه‌تنها از تلگرام، بلکه از
**کلِ ارگانیسم** غایب است.

نتیجه‌اش این بود: ارگانیسمی که مأموریتش پول است، هیچ‌وقت نمی‌فهمید کدام لید
**برنده** شد. لید می‌ساخت، امتیاز می‌داد، پیشنهاد می‌نوشت — و بعد سکوت. هیچ
سیگنالی از واقعیت برنمی‌گشت، پس هیچ چیزی هم قابلِ یادگیری نبود.

این ماژول همان یک سیم است: مالک می‌گوید چه شد، و گفته‌اش می‌ماند.

مرزها
─────
· **صفر پول جابه‌جا نمی‌شود.** `invoice.paid` این‌جا یک **گزارش** است نه یک
  تراکنش؛ به هیچ ledger و هیچ درآمدِ تأییدشده‌ای وصل نیست.
· **صفر ارسالِ بیرونی.** هیچ‌کدام از این افعال به مشتری چیزی نمی‌فرستند.
· append-only. اشتباه با یک رویدادِ تازه اصلاح می‌شود، نه با پاک‌کردن.
· فلگ‌دار و پیش‌فرض خاموش.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

_OPS = Path(__file__).resolve().parent.parent
for _p in (str(_OPS), str(_OPS / "outcomes"), str(_OPS / "budget"),
           str(_OPS / "legs")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

FLAG = "OCTOPUS_WIRE_FUNNEL_CMD"
CARD_TITLE = "📈 قیفِ لید"

# فعلِ فارسی/انگلیسیِ مالک → رویدادِ قراردادیِ store. عمداً کوچک: هر فعلی که
# معنایش مبهم باشد، دادهٔ مبهم می‌سازد و بعد نمی‌شود از دادهٔ واقعی جدایش کرد.
VERBS = {
    "sent":     ("communication.sent", "پیام برایش رفت"),
    "replied":  ("customer.replied", "جواب داد"),
    "meeting":  ("inspection.booked", "قرارِ بازدید گذاشته شد"),
    "quote":    ("quote.sent", "قیمت فرستاده شد"),
    "won":      ("quote.won", "🎉 برنده شدیم"),
    "lost":     ("quote.lost", "از دست رفت"),
    "paid":     ("invoice.paid", "💰 پول رسید (گزارش، نه تراکنش)"),
}


def enabled() -> bool:
    import os
    return str(os.environ.get(FLAG, "")).strip().lower() in ("1", "true", "yes", "on")


def _store():
    import funnel_store
    return funnel_store.FunnelStore()


# ── واقعیتِ ارسالِ بیرونی (۲۰۲۶-۰۸-۰۱، شکافِ ۳ از ۳ پیش از arming) ──────────────
# کارت تا امروز فقط برده/باخته/پول‌رسیده را می‌گفت — یعنی نیمهٔ **برگشتِ** قیف.
# نیمهٔ **رفت** (چند تا واقعاً بیرون رفت؟ چند تا در صف است؟) هیچ‌جای تلگرام دیده
# نمی‌شد. بعد از arming این یعنی مالک صفر دید روی خروجی دارد، در حالی که سقفِ
# روزانه‌اش ۱۰ است. این بلوک همان دید است — و از **همان منابعی** می‌خواند که
# نویسنده در آن‌ها می‌نویسد، نه یک انبارِ تازهٔ اختراعی.
_NO_ANSWER = "نامعلوم"


def _why_fa(why: str, subject: str = "شمارندهٔ ارسال") -> str:
    """چرا نمی‌دانیم — به زبانِ مالک. «نمی‌دانم»ِ بی‌دلیل هم یک‌جور دروغ است."""
    w = str(why or "")
    if w in ("no-counter", "no-authz"):
        return f"{subject} هنوز ساخته نشده"
    if w == "corrupt":
        return f"{subject} خراب است"
    if w.startswith("unreadable"):
        return f"{subject} خوانده نشد"
    if w.startswith("no-worker") or w.startswith("no-path") or w.startswith("no-gate"):
        return "پایِ ارسال در دسترس نیست"
    return "دلیلش معلوم نیست"


def _authz_path():
    """مسیرِ دفترِ مجوزِ ارسال (`lead_effect_gate._authz_store()`).

    عمداً خودِ `lead_effect_gate` import نمی‌شود: آن ماژول `consent_firewall`
    و بقیهٔ زنجیره را می‌کشد و این کارت on-demand در حلقهٔ poll رندر می‌شود.
    در عوض تست برابریِ این مسیر با مسیرِ خودِ گیت را قفل می‌کند، پس drift
    قرمز می‌شود نه ساکت."""
    import opslib   # noqa: WPS433 — budget از قبل روی sys.path است
    return opslib.STATE_DIR / "legs" / "lead-effect-authz.json"


def _authorized_count() -> tuple:
    """چند effect تا حالا مجازِ ارسال شده. خروجی: (n:int|None, why:str).

    ⚠️ این عدد «تا حالا» است، نه «همین الان در صف»: دفترِ مجوز بعد از ارسال
    پاک نمی‌شود. کارت هم دقیقاً همین را می‌گوید و بیشتر ادعا نمی‌کند."""
    try:
        p = _authz_path()
        raw = p.read_text("utf-8")
    except FileNotFoundError:
        return None, "no-authz"
    except OSError as e:  # noqa: BLE001
        return None, f"unreadable:{type(e).__name__}"
    except Exception as e:  # noqa: BLE001
        return None, f"no-gate:{type(e).__name__}"
    try:
        d = json.loads(raw)
        if not isinstance(d, dict):
            raise ValueError("authz store must be a dict")
    except (ValueError, TypeError):
        return None, "corrupt"
    return sum(1 for v in d.values() if isinstance(v, dict)), "ok"


def outbound_snapshot(*, now=None) -> dict:
    """چند تا امروز رفت، از چه سقفی — و اگر نمی‌دانیم، صریح بگو نمی‌دانیم.

    خروجی: {"today": int|None, "cap": int|None, "armed": bool|None, "why": str}
    `today is None` یعنی **نمی‌دانم**؛ هرگز صفرِ مطمئن جای ندانستن نمی‌نشیند.

    دو نکتهٔ عمدی:
      · `outbound_worker.sends_today()` این‌جا صدا **نمی‌شود**. آن تابع عمداً
        fail-closed است (فایلِ خراب ⇒ خودِ سقف) چون کارش جلوگیری از ارسالِ
        اضافه است. برای یک کارتِ گزارشی همان عدد یک دروغِ تمام‌عیار است:
        «۱۰ تا رفت» در حالی که هیچ‌کس نمی‌داند چند تا رفت.
      · روزِ «امروز» از خودِ `_day_str` ِ نویسنده گرفته می‌شود، نه از ساعتِ
        مستقلِ خودمان — وگرنه همان دامِ همیشگی: نویسنده محلی، خواننده UTC.
    """
    snap = {"today": None, "cap": None, "armed": None, "why": ""}
    try:
        import outbound_worker as _ow   # noqa: WPS433 — lazy: کارت on-demand است
    except Exception as e:  # noqa: BLE001
        snap["why"] = f"no-worker:{type(e).__name__}"
        return snap
    try:
        snap["cap"] = int(_ow.LEAD_DAILY_SEND_CAP)
    except Exception:  # noqa: BLE001
        snap["cap"] = None
    try:
        snap["armed"] = bool(_ow.enabled())
    except Exception:  # noqa: BLE001
        snap["armed"] = None
    try:
        p = _ow._counter_path()
        raw = p.read_text("utf-8")
    except FileNotFoundError:
        snap["why"] = "no-counter"
        return snap
    except OSError as e:  # noqa: BLE001 — قفل/دسترسی/دیسک: ندانستن، نه صفر
        snap["why"] = f"unreadable:{type(e).__name__}"
        return snap
    except Exception as e:  # noqa: BLE001
        snap["why"] = f"no-path:{type(e).__name__}"
        return snap
    try:
        d = json.loads(raw)
        if not isinstance(d, dict):
            raise ValueError("counter must be a dict")
        n = max(0, int(d.get("sent", 0)))
        day = str(d.get("date") or "")
    except (ValueError, TypeError):
        snap["why"] = "corrupt"
        return snap
    if day != _ow._day_str(now):
        # شمارنده هست ولی مالِ روزِ دیگری است ⇒ امروز واقعاً صفر (rollover).
        snap["today"], snap["why"] = 0, "rollover"
    else:
        snap["today"], snap["why"] = n, "ok"
    return snap


def _sent_lines(m, *, now=None, no_ledger: str = "دفترِ قیف خوانده نشد") -> list:
    """بلوکِ «رفت» برای کارت. `m` = متریکِ قیف یا None (دفتر در دسترس نبود).

    `no_ledger` دلیلِ نبودِ دفتر است — «خوانده نشد» و «اصلاً پرسیده نشد» دو
    چیزند و یکی‌کردنشان همان دروغی است که این شکاف را ساخت.
    هیچ شناسه، هیچ آدرس، هیچ نامِ مشتری — فقط شمار و وضعیت (رأیِ PII).
    """
    snap = outbound_snapshot(now=now)
    cap = snap.get("cap")
    cap_txt = str(cap) if isinstance(cap, int) else "؟"
    today = snap.get("today")
    if today is None:
        lines = [f"▸ ارسالِ امروز: {_NO_ANSWER} — {_why_fa(snap.get('why'))} "
                 f"· سقفِ روزانه: {cap_txt}"]
    else:
        lines = [f"▸ ارسالِ امروز: {today} از {cap_txt}"]
        if isinstance(cap, int) and today >= cap:
            lines.append("▸ سقفِ امروز پر شده — تا فردا چیزی بیرون نمی‌رود.")
    if snap.get("armed") is False:
        lines.append("▸ لولهٔ ارسال خاموش است — پس هیچ ارسالی ممکن نیست.")
    ok_n = None
    if isinstance(m, dict):
        by = m.get("events_by_type") or m.get("by_event") or m.get("counts") or {}
        ok_n = int(by.get("communication.sent", 0) or 0)
        bad_n = int(by.get("communication.failed", 0) or 0)
        lines.append(f"▸ در دفتر: {ok_n} ارسالِ تأییدشده · {bad_n} ناموفق")
        # `send_pending` فقط وقتی نشان داده می‌شود که واقعاً چیزی در دفتر باشد.
        # امروز هیچ‌کس `effect.released` را در funnel.db نمی‌نویسد (گیت آن را در
        # `events.jsonl` می‌زند)، پس چاپِ «در صف: 0» یک صفرِ مطمئنِ بی‌پشتوانه
        # بود: مالک می‌خواند «هیچ در صف نیست» در حالی که دفتر اصلاً صف را
        # نمی‌شناسد. اگر روزی نویسنده‌ای پیدا شد، این خط خودش برمی‌گردد.
        waiting = int((m.get("leads_by_state") or {}).get("send_pending", 0) or 0)
        if waiting:
            lines.append(f"▸ در صف: {waiting} منتظرِ ارسال")
    else:
        lines.append(f"▸ کل ارسالِ دفتر: {_NO_ANSWER} — {no_ledger}.")
    n_auth, why_a = _authorized_count()
    if n_auth is None:
        lines.append(f"▸ مجازِ ارسال: {_NO_ANSWER} — "
                     f"{_why_fa(why_a, 'دفترِ مجوزِ ارسال')}")
    elif ok_n is None:
        lines.append(f"▸ مجازِ ارسال: {n_auth} تا حالا")
    else:
        lines.append(f"▸ مجازِ ارسال: {n_auth} تا حالا · حداکثر "
                     f"{max(0, n_auth - ok_n)} هنوز نرفته")
    return lines


def record(verb: str, lead_id: str, note: str = "") -> dict:
    """ثبتِ یک نتیجهٔ بازار. خروجی: {ok, msg}."""
    v = str(verb or "").strip().lower().lstrip("/")
    if v not in VERBS:
        return {"ok": False, "msg": f"«{v}» فعلِ شناخته‌شده‌ای نیست"}
    lid = str(lead_id or "").strip()[:64]
    if not lid:
        return {"ok": False, "msg": "شناسهٔ لید لازم است"}
    if not enabled():
        return {"ok": False, "msg": "flag-off"}
    et, label = VERBS[v]
    try:
        st = _store()
        try:
            fresh = st.record({"event_type": et, "lead_id": lid,
                               "source": "owner-telegram",
                               "payload": {"note": str(note or "")[:200]}})
        finally:
            try:
                st.close()
            except Exception:  # noqa: BLE001
                pass
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "msg": f"ثبت نشد: {type(e).__name__}"}
    return {"ok": True, "fresh": bool(fresh), "event": et,
            "msg": label + ("" if fresh else " (از قبل ثبت شده بود)")}


def handle(text: str) -> str:
    """`/won lead-123 توضیح` → کارتِ جواب. هیچ ارسالی، هیچ پولی."""
    import html
    parts = str(text or "").split()
    if not parts:
        return card()
    verb = parts[0].lstrip("/").lower()
    if verb not in VERBS:
        return card()
    if len(parts) < 2:
        return (f"📈 <b>{html.escape(VERBS[verb][1])}</b>\n"
                f"▸ شناسهٔ لید را هم بنویس: <code>/{verb} lead-123</code>\n"
                "▸ نکنی: چیزی ثبت نمی‌شود.")
    r = record(verb, parts[1], " ".join(parts[2:]))
    if not r["ok"] and r["msg"] == "flag-off":
        return ("📈 <b>قیفِ لید خاموش است</b>\n"
                "▸ چیزی ثبت نمی‌شود.\n"
                f"🔑 برای روشن‌کردنش: <code>OWNER_AUTH: ARM FLAG {FLAG}</code>")
    head = "✅" if r["ok"] else "⚠️"
    return (f"📈 {head} <b>{html.escape(r['msg'])}</b>\n"
            f"▸ لید: <code>{html.escape(parts[1][:40])}</code>\n"
            "▸ این فقط ثبتِ واقعیت است — نه پولی جابه‌جا شد نه پیامی رفت.\n"
            "▸ نکنی: هیچ.")


def card(*, now=None) -> str:
    """کارتِ قیف: چه می‌دانیم و چه نمی‌دانیم."""
    if not enabled():
        # بلوکِ «رفت» به فلگِ قیف بند نیست: شمارندهٔ ارسال منبعِ دیگری دارد.
        # اگر این‌جا هم نیاید، کارتِ خاموش می‌شود سیاه‌چالهٔ کاملِ خروجی —
        # یعنی مالک ۱۰ ارسال در روز داشته باشد و کارت بگوید «هیچ».
        return "\n".join(
            ["📈 <b>قیفِ لید: خاموش</b>",
             "▸ نتیجهٔ بازار هیچ‌جا ثبت نمی‌شود — یعنی ارگانیسم هرگز "
             "نمی‌فهمد کدام لید برنده شد."]
            + _sent_lines(None, now=now, no_ledger="دفترِ قیف خاموش است")
            + ["▸ نکنی: همین‌طور می‌ماند."])
    try:
        st = _store()
        try:
            m = st.metrics() or {}
        finally:
            st.close()
    except Exception as e:  # noqa: BLE001
        return "\n".join([f"📈 قیف در دسترس نیست: {type(e).__name__}"]
                         + _sent_lines(None, now=now))
    # ⚠️ ۲۰۲۶-۰۸-۰۱: این خط `m.get("by_event") or m.get("counts")` بود و
    # `metrics()` کلیدش `events_by_type` است — یعنی خواننده و نویسنده هرگز
    # همدیگر را ندیده بودند و کارت **همیشه** «برده: 0 · باخته: 0» می‌داد،
    # حتی با بردِ ثبت‌شده در دفتر. کلیدِ واقعی اول، دو کلیدِ قدیمی به‌عنوان
    # fallback سرِ جایشان (هیچ‌چیز حذف نشد).
    counts = m.get("events_by_type") or m.get("by_event") or m.get("counts") or {}
    won = int(counts.get("quote.won", 0) or 0)
    lost = int(counts.get("quote.lost", 0) or 0)
    paid = int(counts.get("invoice.paid", 0) or 0)
    lines = ["📈 <b>قیفِ لید</b>",
             f"▸ برده: {won} · باخته: {lost} · پول رسیده: {paid}"]
    if won + lost == 0:
        lines.append("▸ هنوز هیچ نتیجه‌ای نگفته‌ای — پس هیچ چیزی هم "
                     "قابلِ یادگیری نیست.")
    lines += _sent_lines(m, now=now)
    lines += ["",
              "<b>افعال:</b> " + " · ".join(f"/{v}" for v in VERBS),
              "مثال: <code>/won lead-123</code>",
              "",
              "▸ نکنی: هیچ — ثبتِ نتیجه اختیاری است، ولی بدونش قیف کور است."]
    return "\n".join(lines)


if __name__ == "__main__":   # pragma: no cover
    print(card())
