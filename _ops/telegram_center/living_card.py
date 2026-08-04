#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""living_card.py — یک موضوع، یک پیام؛ به‌روز می‌شود، تکثیر نمی‌شود.

چرا (فاز ۱، ۲۰۲۶-۰۸-۰۴) — و چرا **نه** آن چیزی که پلن اول گفته بود
──────────────────────────────────────────────────────────────────────
پلن فرض کرده بود مشکل «دیوارِ کارتِ تکراری» است. اندازه‌گیریِ لاگِ زنده آن
فرض را رد کرد:

    ۲۴ ساعتِ اخیر:  ۷۶ پیامِ نو ·  ۳۲۸ ویرایش ·  تکراری فقط **۴٪**

یعنی سیستم از قبل بیشترش ویرایش‌محور است و حجم/تکرار مشکلِ امروز نیست.
(خوشهٔ ۲۱۶تاییِ یکسان که اول پیدا کردم مالِ ۰۸-۰۲ بود و از ۰۸-۰۳ خودش رفع
شده — عددِ تجمعی گمراه‌کننده بود، همان تلهٔ «۲۵۴ دایجست/روز».)

آنچه داده **می‌گوید**: بی‌نظمیِ **ساختاری**. در DM شش تولیدکنندهٔ مستقل
(center · summary · doctor · brain · heart · بی‌نام) هرکدام پیامِ خودش را
جدا می‌فرستد و هیچ «خانه»ای وجود ندارد. این ماژول همان خانه را ممکن می‌کند.

قرارداد
────────
    put(client, name="home", text=..., keyboard=...)  →  dict

هر `name` دقیقاً **یک** پیام دارد. بارِ اول ساخته می‌شود، بعدش فقط ویرایش.

سه رفتاری که این را از یک `edit` ِ ساده جدا می‌کند
──────────────────────────────────────────────────
۱. **بی‌تغییر ⇒ صفر فراخوانِ شبکه.** گروه امروز ~۳۲۸ ویرایش در ۲۴ ساعت
   می‌خورد با ریتمِ ثابتِ ~۱۵ در ساعت، شبانه‌روز. ویرایشی که چیزی را عوض
   نمی‌کند، سهمیه می‌سوزاند و در لاگ نویز می‌سازد.
۲. **ویرایشِ شکست‌خورده ⇒ ساختِ دوباره.** `TgClient.edit` فقط `bool`
   برمی‌گرداند، پس «پیام پاک شده» از «شبکه قطع بود» قابلِ تفکیک نیست. اگر
   مالک کارت را پاک کند، `edit` تا ابد False می‌دهد و کارت **هرگز
   برنمی‌گردد** — یک مرگِ خاموشِ دائمی. این‌جا شکستِ ویرایش یعنی «از نو
   بساز»، پس بدترین حالت یک پیامِ اضافه است نه یک کارتِ مردهٔ همیشگی.
۳. **شمارنده.** هر کارت `edits`/`resends`/`sends` را نگه می‌دارد، تا
   «آیا این واقعاً پیامِ نو را کم کرد؟» یک عدد باشد نه یک ادعا.

ناوردی‌ها: فلگ‌دار و پیش‌فرض **خاموش** (خاموش = رفتارِ امروز، بیت‌به‌بیت) ·
stdlib-only · fail-soft مطلق (کارت هرگز مسیرِ صداکننده را نمی‌کشد) · هرگز
متنِ پیام را ذخیره نمی‌کند، فقط هشِ آن (§۱۰).
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
import time
from pathlib import Path

_HERE = Path(__file__).resolve().parent
for _p in (str(_HERE.parent), str(_HERE.parent / "budget")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import opslib  # noqa: E402

SCHEMA = "living-card.v1"

#: پیش‌فرض **خاموش**. خاموش یعنی `put` هیچ نمی‌کند و صداکننده مسیرِ قدیمِ
#: خودش را می‌رود — دکمهٔ برگشتِ فاز ۱ همین است.
FLAG = "OCTOPUS_TG_LIVING_CARD"

#: سقفِ کارت‌های ثبت‌شده. یک state ِ بی‌سقف خودش یک باگ است.
MAX_CARDS = 200


def enabled() -> bool:
    return str(os.environ.get(FLAG, "") or "").strip().lower() in (
        "1", "true", "yes", "on")


def _state_path() -> Path:
    return opslib.STATE_DIR / "telegram" / "living-cards.json"


def digest(text: str, keyboard=None) -> str:
    """اثرِ انگشتِ آنچه مالک **می‌بیند** — متن و دکمه‌ها با هم.

    دکمه‌ها عمداً داخلِ هش‌اند: کارتی که متنش یکی است ولی دکمه‌هایش عوض شده،
    از دیدِ مالک **عوض شده**. اگر فقط متن هش شود، آن تغییر بی‌صدا گم می‌شود."""
    h = hashlib.sha256()
    h.update(str(text or "").encode("utf-8", "replace"))
    if keyboard:
        try:
            h.update(json.dumps(keyboard, ensure_ascii=False,
                                sort_keys=True).encode("utf-8", "replace"))
        except (TypeError, ValueError):
            h.update(repr(keyboard).encode("utf-8", "replace"))
    return h.hexdigest()[:16]


def _load() -> dict:
    try:
        p = _state_path()
        if not p.exists():
            return {}
        d = json.loads(p.read_text("utf-8"))
        return d if isinstance(d, dict) else {}
    except (OSError, ValueError):
        return {}                      # state ِ خراب = از نو، نه انفجار


def _save(d: dict) -> bool:
    try:
        p = _state_path()
        p.parent.mkdir(parents=True, exist_ok=True)
        tmp = p.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(d, ensure_ascii=False, indent=1), "utf-8")
        os.replace(tmp, p)             # اتمیک — نوشتنِ نیمه‌کاره state را نمی‌خورد
        return True
    except OSError:
        return False


def get(name: str) -> dict:
    return dict(_load().get(str(name)) or {})


def put(client, *, name: str, text: str, keyboard=None, chat_id=None,
        topic_id=None, now: "float | None" = None) -> dict:
    """کارت را به این متن برسان. **همیشه dict، هرگز استثنا.**

    خروجیِ `action`:
        off       — فلگ خاموش؛ صداکننده باید مسیرِ قدیمش را برود
        unchanged — همان محتوا؛ **هیچ فراخوانِ شبکه‌ای نشد**
        sent      — بارِ اول ساخته شد
        edited    — همان پیام به‌روز شد
        resent    — ویرایش شکست خورد (احتمالاً پاک شده) ⇒ از نو ساخته شد
        failed    — نه ویرایش شد نه ساخته
    """
    _now = float(now if now is not None else time.time())
    if not enabled():
        return {"action": "off", "message_id": None,
                "reason": f"{FLAG} خاموش است"}
    key = str(name or "").strip()
    if not key:
        return {"action": "failed", "message_id": None, "reason": "نامِ خالی"}
    body = str(text or "")
    if not body.strip():
        # ⚠️ متنِ خالی را به تلگرام نمی‌دهیم: `send` قبل از نوشتنِ رسید
        # برمی‌گردد، پس یک ارسالِ خالی **هیچ ردی** نمی‌گذارد — یک no-op ِ
        # نامرئی، دقیقاً همان چیزی که فاز ۰ ریشه‌کن کرد.
        return {"action": "failed", "message_id": None, "reason": "متنِ خالی"}

    state = _load()
    row = state.get(key) if isinstance(state.get(key), dict) else {}
    sha = digest(body, keyboard)
    mid = row.get("message_id")
    same_place = (row.get("chat") == chat_id and row.get("topic") == topic_id)

    if isinstance(mid, int) and same_place and row.get("sha") == sha:
        return {"action": "unchanged", "message_id": mid, "reason": "بی‌تغییر"}

    action, new_mid, reason = None, None, ""
    if isinstance(mid, int) and same_place:
        try:
            ok = bool(client.edit(mid, body, keyboard, chat_id))
        except Exception as e:  # noqa: BLE001 — کارت هرگز صداکننده را نمی‌کشد
            ok, reason = False, f"{type(e).__name__}"
        if ok:
            action, new_mid = "edited", mid
        else:
            # ⚠️ نمی‌دانیم «پاک شده» بود یا «شبکه قطع». `edit` فقط bool
            # می‌دهد. اگر ساکت برگردیم، کارتِ پاک‌شده **هرگز** برنمی‌گردد.
            # پس از نو می‌سازیم: بدترین حالت یک پیامِ اضافه، به‌جای یک
            # کارتِ مردهٔ دائمی.
            try:
                new_mid = client.send(body, keyboard=keyboard, chat_id=chat_id,
                                      topic_id=topic_id, stream=f"card:{key}")
            except Exception as e:  # noqa: BLE001
                new_mid, reason = None, f"{type(e).__name__}"
            action = "resent" if new_mid is not None else "failed"
    else:
        try:
            new_mid = client.send(body, keyboard=keyboard, chat_id=chat_id,
                                  topic_id=topic_id, stream=f"card:{key}")
        except Exception as e:  # noqa: BLE001
            new_mid, reason = None, f"{type(e).__name__}"
        action = "sent" if new_mid is not None else "failed"

    if new_mid is None:
        return {"action": "failed", "message_id": None,
                "reason": reason or "ارسال/ویرایش ناموفق"}

    counts = row if isinstance(row, dict) else {}
    state[key] = {
        "chat": chat_id, "topic": topic_id,
        "message_id": new_mid, "sha": sha, "ts": _now,
        "sends": int(counts.get("sends") or 0) + (1 if action == "sent" else 0),
        "edits": int(counts.get("edits") or 0) + (1 if action == "edited" else 0),
        "resends": int(counts.get("resends") or 0) + (1 if action == "resent" else 0),
    }
    if len(state) > MAX_CARDS:         # کهنه‌ترین‌ها بروند، نه تازه‌ترین‌ها
        for k in sorted(state, key=lambda k: float(
                (state[k] or {}).get("ts") or 0))[:len(state) - MAX_CARDS]:
            state.pop(k, None)
    _save(state)
    return {"action": action, "message_id": new_mid, "reason": reason}


def stats() -> dict:
    """«آیا این واقعاً پیامِ نو را کم کرد؟» — عدد، نه ادعا."""
    d = _load()
    return {
        "schema": SCHEMA, "cards": len(d),
        "sends": sum(int((v or {}).get("sends") or 0) for v in d.values()),
        "edits": sum(int((v or {}).get("edits") or 0) for v in d.values()),
        "resends": sum(int((v or {}).get("resends") or 0) for v in d.values()),
    }


if __name__ == "__main__":  # pragma: no cover — گزارشِ دستی، صفر ارسال
    print(json.dumps({"enabled": enabled(), "state": str(_state_path()),
                      **stats()}, ensure_ascii=False, indent=2))
