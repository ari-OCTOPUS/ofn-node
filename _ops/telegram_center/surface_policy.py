"""surface_policy — کجا حرف بزند، و کِی اصلاً حرف نزند.

رأیِ مالک ۲۰۲۶-۰۷-۲۸، چهار جواب:
  ۱ گروه = **پاها**. گفت‌وگوی من و تو = **یک چتِ خصوصی، برای خودآگاهی**. بقیه جای دیگر.
  ۲ آنچه از گروه بیرون می‌رود → پیامِ خصوصی.
  ۳ خودش فقط وقتی شروع کند که **واقعاً به مالک نیاز دارد**.
  ۴ هر پیام = **یک چیز، یک دکمه**.

اندازه‌گیری‌ای که این طرح از آن آمد (۱۷۶ ارسال، ۲۶ تا ۲۸ جولای):

    General/بی‌تاپیک   ۱۰۹   ۶۲٪
    ⚙️ سیستم            ۴۰   ۲۳٪
    🧠 دانش             ۲۰   ۱۱٪
    ۷ تاپیکِ بیزنسی      ۱ تا هرکدام — فقط کارتِ ساخته‌شدنشان

یعنی هفت اتاق ساخته شده بود و هیچ‌کس داخلشان حرف نزده بود، و گروه در عمل
لولهٔ سروصدای سیستم بود. این ماژول آن را وارونه می‌کند.

⚠️ یک صداقتِ لازم: هیچ‌یک از نام‌های جریانِ امروز مالِ پا نیست (`heart` ·
`doctor` · `needs` · `summary` · `brain` · `discovery` · `c6` · `center`).
پس بلافاصله بعد از این تغییر **گروه ساکت می‌شود** — نه چون چیزی خراب شده،
بلکه چون پاها هنوز حرفی برای گفتن ندارند. آن سکوت خودش یک اندازه‌گیری است.

مرزها:
  · این ماژول **هیچ‌چیز نمی‌فرستد**. فقط مقصد را می‌گوید.
  · `cortisol` و `alert` هرگز نگه داشته نمی‌شوند — ایمنی سکوت نمی‌گیرد.
  · فلگ خاموش = رفتارِ قبلی بایت‌به‌بایت.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
for _p in (str(_HERE.parent), str(_HERE.parent / "budget")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import opslib  # noqa: E402

FLAG = "OCTOPUS_TG_SURFACE_V2"

# ─── سه مقصد ──────────────────────────────────────────────────────────────
GROUP = "group"     # اتاقِ پاها — کارِ بیرونی، پول، مشتری
DM = "dm"           # گفت‌وگوی من و تو + هر تصمیمی که فقط مالک می‌گیرد
HOLD = "hold"       # ثبت می‌شود، فرستاده نمی‌شود؛ با درخواست می‌آید

# پاها: کارِ بیرونی. هر پا به اتاقِ خودش.
#
# ۲۰۲۶-۰۷-۲۸ — کامنتِ قبلیِ همین خط می‌گفت «اگر روزی جریانی با این نام بفرستد»،
# و آن «اگر» جواب بود: از هشت نامِ جریانی که تا آن روز واقعاً فرستاده شده بودند
# (center · needs · discovery · brain · doctor · heart · cortisol · بی‌نام)
# **هیچ‌کدام پا نبود**، و کلِ `wiring.py` هم فقط پنج جریان تولید می‌کرد. یعنی این
# جدول درست بود و مصرف‌کننده نداشت — به همین دلیل ۷ تاپیکِ گروه از روزِ ساختشان
# یک پیام هم نگرفته بودند. تولیدکننده‌اش حالا `legs/leg_room_report.py` است.
#
# `cartographer` و `knowledge` همان روز اضافه شدند: تاپیک داشتند، اندام بودند،
# و در این جدول نبودند — پس حتی با تولیدکننده هم بی‌صدا در General می‌افتادند.
LEG_TOPIC = {
    "lead": "lead", "ziman": "ziman", "mining": "mining",
    "crypto": "crypto", "accounting": "accounting", "studio": "studio_pf",
    "knowledge": "knowledge", "cartographer": "cartographer",
}

# خودآگاهی: چیزی که دربارهٔ **خودش** است، نه دربارهٔ کار. این‌ها گفت‌وگویند.
SELF_STREAMS = frozenset({"brain", "discovery", "c6", "identity", "insight"})

# ایمنی: هرگز نگه داشته نمی‌شود، هرگز ساکت نمی‌شود.
SAFETY_STREAMS = frozenset({"cortisol", "alert"})


def enabled() -> bool:
    return str(os.environ.get(FLAG, "") or "").strip().lower() in (
        "1", "true", "yes", "on")


def route(stream, *, needs_owner: bool = False) -> tuple:
    """(destination, topic_key|reason).

    `needs_owner=True` یعنی صداکننده اعلام می‌کند این واقعاً تصمیمِ مالک است.
    عمداً پارامتر است نه حدس: خودِ ماژول نمی‌تواند بداند یک `doctor` معمولی
    است یا یک تصمیمِ واقعی. (از ۰۷-۳۰ فقط برچسبِ reason را عوض می‌کند —
    مقصد در هر دو حالت DM است.)

    ⚠️ **رأیِ مالک ۲۰۲۶-۰۷-۳۰: «ناگفته‌ها به DM اختاپوس بیایند.»**
    fallback ِ قبلی HOLD بود (رأیِ ۰۷-۲۸: «فقط وقتی واقعاً به من نیاز داری»)
    و از همان روز ~۱۷۰ پیامِ doctor/heart/needs بی‌صدا ثبت-و-فرستاده-نشده
    ماند. مالک وقتی شمار را در پالسِ لنگر دید، تحویل را انتخاب کرد. HOLD
    به‌عنوانِ مقصدِ route دیگر تولید نمی‌شود؛ خودِ سازوکارِ hold/held_since
    می‌ماند (آرشیو + دکمهٔ «ناگفته‌ها» + هر صداکنندهٔ آینده که صریح بخواهد).
    ساعتِ سکوت (۰ تا ۷، رأیِ ۰۷-۲۷) در لایهٔ بالادست (send_text) سرِ جایش
    است و این تغییر به آن دست نمی‌زند.
    """
    if not enabled():
        return (None, None)                    # فلگ خاموش → مسیرِ قدیمی دست‌نخورده
    s = str(stream or "").strip().lower()
    if s in SAFETY_STREAMS:
        return (DM, "safety")                  # ایمنی همیشه می‌رسد
    if s in LEG_TOPIC:
        return (GROUP, LEG_TOPIC[s])
    if s in SELF_STREAMS:
        return (DM, "self")
    if needs_owner:
        return (DM, "needs-owner")
    return (DM, "ambient")                     # رأیِ ۰۷-۳۰ — تحویل، نه سکوت


# ─── نگه‌داشته‌ها: ثبت می‌شوند تا گم نشوند ─────────────────────────────────
def _held_path() -> Path:
    return Path(opslib.STATE_DIR) / "telegram" / "held-stream.jsonl"


def hold(stream, text: str, *, cap: int = 4000) -> bool:
    """آنچه فرستاده نشد را ثبت کن. سکوت ≠ فراموشی.

    بدونِ این، «فقط وقتی لازم است حرف بزن» تبدیل می‌شود به «چیزهایی که
    نگفتم برای همیشه رفتند» — و آن‌وقت مالک نمی‌تواند بعداً بررسی کند که
    سکوت درست بوده یا نه.
    """
    try:
        p = _held_path()
        p.parent.mkdir(parents=True, exist_ok=True)
        with open(p, "a", encoding="utf-8") as f:
            f.write(json.dumps({"ts": opslib.now_iso(), "stream": str(stream or "")[:40],
                                "text": str(text or "")[:cap]}, ensure_ascii=False) + "\n")
        return True
    except Exception:  # noqa: BLE001
        # عمداً پهن: این تابع روی مسیرِ زندهٔ ارسال است و **هیچ** خطایی از آن
        # نباید بالا بیاید. تستِ خودش این را گرفت — مسیرِ نامعتبر `ValueError`
        # می‌دهد نه `OSError`، و گاردِ تنگ آن را رد می‌کرد.
        return False


def held_since(n: int = 20) -> list:
    """آخرین n موردِ نگه‌داشته‌شده — خوراکِ فرمانِ «چه چیزی را نگفتی؟»."""
    try:
        lines = _held_path().read_text("utf-8").splitlines()
    except OSError:
        return []
    out = []
    for line in lines[-max(1, int(n)):]:
        try:
            out.append(json.loads(line))
        except ValueError:
            continue
    return out


# ─── فرمِ «یک چیز، یک دکمه» ───────────────────────────────────────────────
def one_thing(headline: str, why: str = "", action: str = "") -> dict:
    """یک تصمیم، یک جملهٔ زمینه، حداکثر یک دکمه.

    چرا سقفِ **یک** دکمه: هر دکمهٔ اضافه یک تصمیمِ اضافه است، و کارتِ
    چنددکمه‌ای مالک را وادار می‌کند گزینه‌ها را هم‌زمان در ذهن نگه دارد.
    این فرم عمداً چیزی برای نگه‌داشتن باقی نمی‌گذارد — می‌شود وسطش رفت و
    برگشت بدونِ اینکه چیزی از دست برود.

    خروجی dict است نه رشته، تا فرستنده خودش تصمیم بگیرد چطور رندر کند.
    """
    head = str(headline or "").strip()
    if not head:
        return {"ok": False, "reason": "empty-headline"}
    body = head
    w = str(why or "").strip()
    if w:
        body += "\n" + w.split("\n")[0][:180]      # دقیقاً یک خطِ زمینه
    btn = str(action or "").strip()[:48]
    return {"ok": True, "text": body,
            "buttons": [btn] if btn else [],
            "n_buttons": 1 if btn else 0}


def card() -> str:
    """کارتِ وضعیتِ خودِ سیاست — برای `/x`."""
    if not enabled():
        return ("🗺 <b>سطحِ تلگرام — نسخهٔ ۲</b>\n"
                f"خاموش. روشن‌کردن: <code>OWNER_AUTH: ARM FLAG {FLAG}</code>\n"
                "خاموش یعنی همان رفتارِ امروز: همه‌چیز در گروه.")
    held = held_since(200)
    return ("🗺 <b>سطحِ تلگرام — نسخهٔ ۲</b> · روشن\n"
            f"گروه = پاها ({len(LEG_TOPIC)} اتاق) · چتِ خصوصی = خودآگاهی + تصمیم‌ها + محیطی (رأیِ ۰۷-۳۰)\n"
            f"آرشیوِ نگه‌داشته‌های قدیم: {len(held)} مورد (از ۰۷-۳۰ جریانِ تازه HOLD نمی‌شود)")
