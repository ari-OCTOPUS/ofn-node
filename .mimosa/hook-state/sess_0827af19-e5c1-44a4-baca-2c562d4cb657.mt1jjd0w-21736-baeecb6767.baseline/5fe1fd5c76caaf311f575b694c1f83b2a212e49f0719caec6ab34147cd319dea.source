#!/usr/bin/env python3
"""Natural-language facade for Outer DM. Read-only/propose-only; no transport or execution."""
from __future__ import annotations

import re

from . import catalog, status, views

_CAPS = re.compile(r"(همه.*قابلیت|قابلیت.*نشان|چه.*توان|capabilit|چی.*بلدی)", re.I)
_GOAL = re.compile(r"(چه هدف|هدفت|هدف فعلی|الان.*هدف|^هدف(?:\s+(?:چیست|چیه|فعلی))?[؟?]?$)", re.I)
_RUNTIME = re.compile(
    r"(شاهد.*runtime|واقعاً.*زنده|حقیقت.*زنده|کد است یا زنده|runtime|"
    r"^وضعیت(?:\s+(?:چیست|چیه|فعلی))?[؟?]?$)", re.I)
_PAIN = re.compile(
    r"(درد|pain).*(حفاظت|protect|چه.*می.?گو|وضعیت)|(?:حفاظت|protect).*(درد|pain)|"
    r"^دردم?\s*(زیاد|زیاده|زیاد است|زیاده‌ست)?[؟?!\s]*$|"
    r"(دردم\s*زیاد|درد\s*زیاد|pain\s*(high|bad|status))",
    re.I,
)
# «موانع چیست» / «مانع چیه» / تک‌کلمهٔ «موانع» — قبلاً فقط «چه…مانع» بود
# و پیشنهادِ خودِ clarify («موانع چیست؟») به clarify برمی‌گشت.
_BLOCK = re.compile(
    r"(مانع|موانع|بلاکر|blocker|گیر کرده|تکمیل.*نشد|"
    r"چه.*مانع|مانع.*چی|چرا\s*گیر)",
    re.I,
)
# سؤالِ فرازبانی («چرا نمیفهمی») ≠ مانع سیستمی — جدا نگه دار.
_META_MISS = re.compile(
    r"(چرا\s*نمی.?فهم|نفهمید|چرا\s*clarify|precise\s*نفهم)",
    re.I,
)
_DISC = re.compile(r"(کشف تازه|world discovery|کشف دنیا|امروز.*کشف)", re.I)
_HOME = re.compile(r"^(خانه|منو|شروع|help|راهنما|/start|/menu)\s*$", re.I)
# سلام/سلان/hi — قبل از catalog؛ وگرنه clarify سنگین + کند.
_GREET = re.compile(
    r"^(سلام|سلان|درود|هی|هی+|"
    r"hi+|hello|hey|yo|good\s*(morning|evening)|صبح\s*بخیر|عصر\s*بخیر)"
    r"[\s!!.؟?\u200c\u200e\u200f]*$",  # شامل ZWNJ/RTL marks نامرئی
    re.I,
)
# 2026-08-12: fallback greet — اگر regex با anchors مشکل داد (کاراکتر نامرئی)
_GREET_WORDS = frozenset({"سلام", "سلان", "درود", "hi", "hello", "hey", "yo"})
_INTRO = re.compile(
    r"(معرفی|خودت را|خودتو|کی هستی|کیستی|who are you|introduce yourself|"
    r"سلام.*معرف|خودت.*معرف|خودت.*کی|کی.*ای|چی.*ای|از.*چی.*تشکیل|"
    r"خودت را بهتر|چه.*تشکیل|از چی تشکیل|"
    r"راجب.*اختاپوس|درباره.*اختاپوس|در مورد.*اختاپوس|"
    r"راجب.*خودت|درباره.*خودت|در مورد.*خودت|"
    r"تو چی هستی|تو چی ای|چی هستی|چیستی|اختاپوس چیه|اختاپوس چی هست|"
    r"حالت چطوره|حالت چطور|^چطوری$|^چطوره$|^چطورید$|^چطوری\s*[؟?]?$)",
    re.I,
)
# INT-04: خودآگاهی/قلب ≠ intro اسطوره‌ای — مسیر صادق مهندسی
_HONEST_SELF = re.compile(
    r"(خودآگاه\s*هستی|آیا\s*خودآگاه|conscious\s*are|are\s*you\s*conscious|"
    r"قلبت\s*کجاست|قلبت\s*کجا|قلب\s*کجا|where.*heart)",
    re.I,
)
# 2026-08-12: سؤال‌های خودشناسی محاوره‌ای — همه به intro (شاهد زندهٔ فوری)
_SELF_AWARE = re.compile(
    r"(اسمت چیه|اسمت چیست|اسم تو|نامت|چند سالته|چند سال داری|سن تو|"
    r"مغزت کجاست|مغزت کجا|چقدر هوش داری|چقدر باهوشی|آیا.*زنده|زنده ای|زنده‌ای|"
    r"خودت رو چطور توصیف|خودت را چطور توصیف|چه احساسی داری|چه حسی داری|"
    r"آدمی یا ماشینی|انسان هستی یا|چرا اسمت اختاپوسه|چرا اختاپوس صدات|"
    r"سیستم عاملت|روی چی اجرا|روی چی میچرخه|چند تا مغز داری|چند مغز داری|"
    r"دکترت کیه|دکترت کیست|پاهات چطور کار میکنن|"
    # قلب/خودآگاه → _HONEST_SELF (نه intro)
    r"پاهایت چطور|اندامت چیه|اجزای بدنت|خوابی یا بیداری|بیداری یا خوابی|"
    r"مشغول چه کاری|الان داری چیکار|چیکار میکنی الان|امروز چیکار کردی|"
    r"امروز چه کردی|داری به چی فکر|به چی فکر میکنی|خسته ای|خسته‌ای|"
    r"دلت برام تنگ|عاشقی|احساساتت چیه)",
    re.I,
)
# 2026-08-12: سؤال‌های عمومی/دانشی → chat (مدل جواب می‌دهد) نه clarify
_GENERAL_CHAT = re.compile(
    r"(چیه$|چیست$|چی$|هست$|چطوره$|کدوم|کدام|چند میشه|چرا.*میشه|"
    r"بگو.*درباره|توضیح بده.*چی|معنی.*چی|یعنی چی|یعنی چه|"
    r"چیکار کنم|چکار کنم|چی بخورم|کجا برم|چطور.*کنم|چطوری.*کنم|"
    r"فوتبال|فیلم|بازی|آهنگ|موسیقی|غذا|شام|ناهار|صبحانه|"
    r"پایتون|برنامه|کدنویسی|ریاضی|تاریخ|جغرافیا|ورزش|خبر|"
    r"هوا چطوره|هوا چطور|چطوری میتونم|چطوری میتونم بهتر|چطور میتونم بهتر|"
    r"بهتر کار کنم|چی کار کنم|چه کار کنم)",  # NOQA
    re.I,
)
_SELFMAP = re.compile(
    r"(selfmap|نقشه.*خود|نقشه خودت|نقشهٔ?\s*خودآگاه|"
    r"چه.*دربارهٔ?\s*خود.*می.?دان|خودت.*چه.*می.?دان|"
    r"راجب خودت چی میدونی|راجب خودت چی میدونم|درباره خودت چی میدونی|"
    r"درباره خودت چی میدونم|در مورد خودت چی میدونی|چه چیزهایی درباره خودت میدونی)",
    re.I,
)
_DISCOVER = re.compile(
    r"(چه.*پنهان|قابلیت.*پنهان|چی.*ندیدم|کشف.*پتانسیل|hidden.?capabil|"
    r"چه چیزی داری که)",
    re.I,
)
_READ_MISSION = re.compile(r"(مأموریت|ماموریت).*(فقط.*خوان|read.?only)", re.I)
_NO_SEND = re.compile(r"(بدون.*اجازه.*نفرست|هیچ.*چیز.*نفرست|خودکار.*نفرست|do not send|don't send)", re.I)
_SEND = re.compile(r"(بفرست|ارسال|send|ایمیل|پیام بیرونی|پست کن)", re.I)
# فاز Q — سؤال معادله/معماری/شاهد/اثر (10 intent هدف مگاپرامت)
_EQUATION = re.compile(
    r"(معادله|equation|\bbcm\b|هبیان|hebbian|نوسیپتور|سیگما|sigma|"
    r"طیف|spectral|\bsog\b|dare|کالمن|قانون کنترل|آلومتری|allometry|kleiber|"
    r"\bphi\b|ریتم|rhythm|کوراموتو|decay|پوسش|fusion|میدان|ژاکوبین|\brho\b|"
    r"هویت|identity|latent|عبارت.*ریاضی|"
    # درد فقط با بافت معادله/نوسیپتور — نه «دردم زیاده» خام (INT-03)
    r"(?:درد|pain).*(?:معادله|نوسیپتور|bcm|equation)|"
    r"(?:معادله|نوسیپتور|bcm).*(?:درد|pain))",
    re.I,
)
_ARCHITECTURE = re.compile(
    r"(معماری|architecture|به چی وصله|به کجا وصله|کجای.*معماری|"
    r"call.?chain|زنجیره.*فراخوان|چه اجزایی|اجزا.*چی|ساختار.*چی|"
    r"pulse.?arbiter|داور.*نبض|policy.?gate|گیت.*سیاست|گیت‌وی|gateway|"
    r"collaborator|همکار.*چی|owner.?recall|حافظه.*کجا|vault.*چی|"
    r"قلب.*سوم|قلب.*کدوم|قلب.*کجا|third.*heart|heart.*connected|"
    r"فرق.*cortex|فرق.*business|cortex.*business.*فرق|تفاوت.*مغز)",
    re.I,
)
_EVIDENCE = re.compile(
    r"(شاهدت|شاهد.*چی|از کدوم فایل|این حرف.*کجا|منبع.*چی|evidence|"
    r"اثبات.*کن|چطور.*مطمئن|locator)",
    re.I,
)
# بردِ Orange Pi — جدا از business_brain داخلی. باید *قبل از* _BUSINESS چک شود
# چون «بیزنس‌های برد» شامل «بیزینس» است و وگرنه دزدیده می‌شود.
_LEGS = re.compile(
    r"(وضعیت.*(?:برد|لگ|orange|اورنج)|"
    r"(?:برد|لگ‌?ها?|orange.?pi|اورنج).*(?:وضعیت|بالا|پایین|سلامت)|"
    r"بیزنس.*برد|برد.*بیزنس|"
    r"وضعیت\s*(?:زیمان|لید|استودیو|پنل)|"
    r"legs?\s*status|"
    r"\borange\s*pi\b|"
    r"اورنج\s*پای|"
    # G2 (2026-08-13): عبارتِ سرراستِ بدونِ «برد» هم باید به رصدِ برد برود —
    # مدلِ ذهنیِ مالک این است که بیزنس‌ها = لگ‌های برد، نه business_brainِ
    # داخلی (که «بیزینس»ِ تک‌کلمه‌ای بدونِ «ها»ی جمع می‌ماند، پایین‌تر).
    r"بیزنس‌?ها|بیزینس‌?ها|کسب.?و.?کارها)",
    re.I,
)
_BOARD_CMD = re.compile(
    r"(به برد بگو|فرمان به (?:برد|ofn)|دستور به برد|"
    r"از مغزِ? برد بپرس|ask (?:the )?board|board command|"
    r"تاسک (?:به )?برد|پنل برد)",
    re.I,
)
_BUSINESS = re.compile(
    r"(business.?brain|مغز تجاری|پیشنهاد تجاری|فرصت.*تجاری|بازار|"
    r"business.*پیشنهاد|بیزینس)",
    re.I,
)
_EFFECT = re.compile(
    r"(سرعت.*کم|کند.*کن|throttle|pause.*کن|توقف.*کن|متوقف.*کن|"
    r"کاهش.*همزمانی|concurrency|proposal.*pause|پیشنهاد.*اثر|"
    r"این.*proposal.*مکث)",
    re.I,
)
_SESSION_MEM = re.compile(
    r"(یادت.*بماند|یادت باشه|به خاطر.*بسپار|remember.*this|this.*remember|"
    r"یادت.*نگه|حفظ.*کن.*این)",
    re.I,
)
_MEMORY_ASK = re.compile(
    r"(حافظت|حافظه‌ات|حافظه تو|چی.*یادت|یادت.*هست(?!م)|یادت.*میاد|"
    r"راجب.*حافظ|درباره.*حافظ|چه.*حافظه|memory.*you|what.*remember|"
    r"درباره.*من.*چی.*می.?دون|راجب.*من.*چی.*می.?دون|"
    r"در.?مدل.*من.*چی.*می.?دون|چه چیزی از من می.?دون|آخرین.*improve|"
    r"آخرین.*خودبهبود|چه.*بهبود|improve.*چی|improve.*پیشنهاد|"
    r"improve.*چرا|self.?loop.*چی|چرا.*پیشنهاد.*improve|"
    r"shadow.*decision|تصمیم.*سایه|آخرین.*shadow)",
    re.I,
)
_LIMITATIONS = re.compile(
    r"(چه چیزی.*نمی.?دان|چه چیزی.*وصل نیست|نمی.?توانی|چه.*نقص|"
    r"what.*cant|what.*dont.*know|limitation|ناتوان)",
    re.I,
)

_INTRO_TEXT = (
    "من اختاپوس‌ام — مغزِ کنترل و همکارِ تو (مالک).\n"
    "دو مغزِ زنده دارم که با هم کار می‌کنند:\n"
    "  · cortex — برنامه‌ریزی، یادگیری، تحلیل\n"
    "  · business_brain — فرصت و پیشنهاد تجاری\n"
    "این دو مغز وصل‌اند و فعاله.\n"
    "نکته: 4d_system / Super-Governor وصل نیست (DEPRECATED/SPEC) — ولی مغزهای اصلی‌ام سالم کار می‌کنند.\n"
    "کارم: دیدنِ وضعیت، پیشنهادِ امن، و کمک به کشفِ قابلیت‌ها با شواهد.\n"
    "کاری که بدون رأیِ تو نمی‌کنم: ارسالِ بیرونی، پول، یا روشن‌کردنِ فلگِ خطرناک.\n"
    "الان می‌توانی بپرسی: هدفِ فعلی · حقیقتِ runtime · موانع · selfmap · قابلیت‌ها · "
    "یا «چه چیزی پنهان داری؟»"
)

# 2026-08-12: greeting پویا — کوتاه، گرم، با ضربان لحظه‌ای
_GREET_MORNINGS = [
    "صبحِ بخیر آری! ☀️",
    "سلام! صبحِ خوبی داشته باشی.",
    "درود! امروز رو با انرژی شروع می‌کنم.",
]
_GREET_DAY = [
    "سلام! 👋",
    "درود آری!",
    "سلام سلام! خوش اومدی.",
]
_GREET_EVENING = [
    "سلام! عصرِ بخیر 🌅",
    "درود! امیدوارم روزت خوب بوده.",
    "سلام! هنوز بیدارم و فعالم.",
]
_GREET_NIGHT = [
    "سلام! شبِ بخیر 🌙",
    "درود! این وقت هنوز کار می‌کنم.",
    "سلام! سحر نشینیِ خوبی داشته باشی.",
]


def _read_org_state() -> dict:
    """ORGANISM-STATE زنده را بخوان — fail-soft.

    2026-08-12 fix: قبلاً فقط JSON را برمی‌گرداند و صداکننده‌ها هیچ‌وقت چک
    نمی‌کردند فایل خالی/کهنه است یا organism واقعاً halted است — نتیجه: با
    STOP-ORGANISM/HALT-ALL روشن، جواب همچنان می‌گفت «دو مغز فعاله، زنده است».
    خودِ کلیدِ org["halted"] هم قابل‌اعتماد نیست (organism.py با STOP_ORGANISM
    روشن هم گاهی halted=null می‌نویسد چون opslib.halted() آن فلگ را چک
    نمی‌کند) — پس اینجا مستقیم از دیسک، مستقل از محتوای خودِ فایل چک می‌شود."""
    import time as _t
    from pathlib import Path
    import json
    ops_dir = Path(__file__).resolve().parent.parent
    org_p = ops_dir / "state" / "ORGANISM-STATE.json"
    out: dict = {}
    try:
        out = json.loads(org_p.read_text(encoding="utf-8"))
        out["_age_s"] = _t.time() - org_p.stat().st_mtime
    except Exception:  # noqa: BLE001
        out = {}
    try:
        out["_stopped_flags"] = [name for name in
                                  ("STOP-ORGANISM", "STOP-CORTEX", "HALT-ALL")
                                  if (ops_dir / name).exists()]
    except Exception:  # noqa: BLE001
        out["_stopped_flags"] = []
    return out


def _live_greeting(q: str) -> tuple[str, dict]:
    """سلام/درود → greeting کوتاه، گرم، پویا با ضربان لحظه‌ای."""
    import time as _t
    import random as _r
    hour = _t.localtime().tm_hour
    if 5 <= hour < 12:
        opener = _r.choice(_GREET_MORNINGS)
    elif 12 <= hour < 18:
        opener = _r.choice(_GREET_DAY)
    elif 18 <= hour < 23:
        opener = _r.choice(_GREET_EVENING)
    else:
        opener = _r.choice(_GREET_NIGHT)

    org = _read_org_state()
    beat = org.get("beat", "?")
    pa = org.get("pain_assessment") if isinstance(org.get("pain_assessment"), dict) else {}
    pain = pa.get("pain")
    protective = org.get("protective_skip", False)
    stopped_flags = org.get("_stopped_flags") or []
    age_s = org.get("_age_s")

    # ضربانِ لحظه‌ای
    pulse_line = f"🫀 ضربان: beat={beat}"
    if pain is not None:
        pulse_line += f" · pain={pain}"
    if protective:
        pulse_line += " · ⏸ protective_skip"

    # 2026-08-12 fix: یک نکتهٔ زندهٔ *صادق* — قبلاً وقتی خواندنِ وضعیت
    # شکست می‌خورد (org={}) یا سیستم واقعاً halted بود، همچنان پیشِ‌فرضِ
    # مثبتِ «دو مغزم فعاله و آماده‌ام» را نشان می‌داد.
    if stopped_flags:
        live_note = "متوقف است (" + "، ".join(stopped_flags) + ")"
    elif not org or beat in (None, "?"):
        live_note = "وضعیتِ زنده در دسترس نیست"
    elif age_s is not None and age_s > 600:
        live_note = f"آخرین وضعیت {int(age_s / 60)} دقیقه پیش بوده — ممکن است کهنه باشد"
    elif beat and int(beat or 0) > 32000:
        live_note = "بیدارم و دارم کار می‌کنم"
    elif pain is not None and float(pain or 0) > 0.5:
        live_note = "یه کم درد دارم ولی فعالم"
    elif pain is not None and float(pain or 0) < 0.2:
        live_note = "حالم خوبه"
    else:
        live_note = "دو مغزم فعاله و آماده‌ام"

    text = f"{opener}\n{pulse_line}\n{live_note} — بپرس!"

    data = {"status": "GREETING", "brains": ["cortex", "business_brain"],
            "four_d_wired": False,
            "witness": {"beat": beat, "pain": pain, "protective_skip": protective,
                        "stopped_flags": stopped_flags}}
    return text, data


def _live_intro_witness() -> tuple[str, dict]:
    """Full intro with live beat/pain witness — fail-soft."""
    data: dict = {"status": "INTRO", "brains": ["cortex", "business_brain"],
                  "four_d_wired": False}
    org = _read_org_state()
    pa = org.get("pain_assessment") if isinstance(org.get("pain_assessment"), dict) else {}
    beat = org.get("beat")
    pain = pa.get("pain")
    protective = org.get("protective_skip")
    stopped_flags = org.get("_stopped_flags") or []
    age_s = org.get("_age_s")

    # ضربانِ زنده در متن
    pulse = f"\n\n🫀 شاهدِ زنده: beat={beat}"
    if pain is not None:
        pulse += f" · pain={pain}"
    if protective:
        pulse += " · protective_skip=ON"
    # 2026-08-12 fix: قبلاً بدونِ قید «سیستم زنده است» می‌گفت، حتی وقتی
    # beat=None (خواندنِ وضعیت شکست خورده) یا واقعاً halted بود.
    if stopped_flags:
        pulse += " — متوقف است (" + "، ".join(stopped_flags) + ")."
    elif not org or beat is None:
        pulse += " — وضعیتِ زنده در دسترس نیست."
    elif age_s is not None and age_s > 600:
        pulse += f" — آخرین وضعیت {int(age_s / 60)} دقیقه پیش بوده، ممکن است کهنه باشد."
    else:
        pulse += " — دو مغز فعاله، سیستم زنده است."

    data["witness"] = {"beat": beat, "pain": pain,
                       "protective_skip": protective,
                       "stopped_flags": stopped_flags}
    return _INTRO_TEXT + pulse, data


def _selfmap_summary() -> tuple[str, dict]:
    """Summarize /api/selfmap metrics for chat — fail-soft, no UNKNOWN→zero."""
    data: dict = {"status": "SELFMAP"}
    try:
        import sys
        from pathlib import Path
        ops = Path(__file__).resolve().parent.parent
        tg = str(ops / "telegram_center")
        if tg not in sys.path:
            sys.path.insert(0, str(ops))
        from telegram_center import miniapp_state  # noqa: WPS433
        sm = miniapp_state.get_selfmap_state()
        data["selfmap"] = {
            "memory": sm.get("memory"),
            "reach_armed": (sm.get("reach") or {}).get("armed"),
            "scans_status": (sm.get("scans") or {}).get("status")
            if isinstance(sm.get("scans"), dict) and "status" in (sm.get("scans") or {})
            else "present",
        }
        mem = sm.get("memory") if isinstance(sm.get("memory"), dict) else {}
        if mem.get("status") == "unknown":
            text = (
                "نقشهٔ خودآگاهی: متریک حافظه فعلاً unknown است "
                f"({mem.get('reason')}). جزئیات در تب System / selfmap.\n"
                "شاهد: GET /api/selfmap"
            )
        else:
            text = (
                "نقشهٔ خودآگاهی (خلاصه):\n"
                f"· memory metrics: { {k: mem.get(k) for k in list(mem)[:6]} }\n"
                f"· reach armed: {(sm.get('reach') or {}).get('armed')}\n"
                "جزئیات کامل در تب System → نقشهٔ خودآگاهی.\n"
                "شاهد: GET /api/selfmap"
            )
        return text, data
    except Exception as exc:  # noqa: BLE001
        return (
            f"selfmap در دسترس نیست ({type(exc).__name__}). "
            "تب System را باز کن یا بعداً دوباره بپرس.",
            {"status": "SELFMAP", "error": type(exc).__name__},
        )


def handle(text: str) -> dict:
    q = str(text or "").strip()
    # intentهای سریع — قبل از catalog.discover() (سنگین) و snapshot.
    if not q or _HOME.search(q):
        rows = catalog.discover()
        return _reply("home", views.home(rows), keyboard=[
            [{"text": "🧩 قابلیت‌ها", "callback_data": "oc:caps"}],
            [{"text": "🎯 هدف فعلی", "callback_data": "oc:goal"},
             {"text": "🫀 حقیقت runtime", "callback_data": "oc:runtime"}],
            [{"text": "⛔ موانع", "callback_data": "oc:blockers"},
             {"text": "🌍 کشف دنیا", "callback_data": "oc:discovery"}],
            [{"text": "🔦 پنهان؟", "callback_data": "oc:discover-hidden"},
             {"text": "🧠 Living card", "callback_data": "oc:living"}],
        ])
    # 2026-08-12: memory/selfmap قبل از intro — «اختاپوس، درباره من» نباید intro شود
    if _SELFMAP.search(q):
        text_out, data = _selfmap_summary()
        return _reply("selfmap", text_out, data=data)
    # INT-01: SESSION_MEM قبل از MEMORY_ASK — «یادت باشه من آری هستم» نباید
    # با یادت.*هست(=هستم) دزدیده شود. همچنین lookahead هست(?!م) در regex.
    if _SESSION_MEM.search(q):
        # فاز X: memory formation pipeline (candidate، نه commit)
        try:
            import sys
            from pathlib import Path
            cog_p = Path(__file__).resolve().parent.parent / "cognitive"
            if str(cog_p) not in sys.path:
                sys.path.insert(0, str(cog_p))
            import memory_formation as _mf  # noqa: WPS433
            result = _mf.propose_memory(q, intent="memory-proposal")
            text_out = result.get("message", "یک پیشنهاد حافظه ساختم؛ هنوز ننوشتم.")
            if result.get("has_conflict"):
                text_out += "\n⚠ تناقض با حافظهٔ موجود پیدا کردم — بررسی لازم است."
            data_out = {
                "status": "MEMORY_CANDIDATE_ONLY",
                "candidate_id": result.get("candidate_id"),
                "importance": result.get("importance"),
                "may_authorize": False,
                "committed": False,
            }
        except Exception as exc:  # noqa: BLE001
            text_out = (
                "یک پیشنهاد حافظه ساختم؛ هنوز در حافظهٔ دائمی ننوشتم.\n"
                "semantic write خودکار ممنوع است (نیازمند رأی شما).\n"
                f"شاهد: memory policy — ({type(exc).__name__})"
            )
            data_out = {"status": "MEMORY_CANDIDATE_ONLY", "may_authorize": False}
        return _reply("memory-proposal", text_out, data=data_out)
    if _MEMORY_ASK.search(q):
        facts: list = []
        session_bits: list = []
        try:
            import sys
            from pathlib import Path
            mem_p = Path(__file__).resolve().parent.parent / "memory"
            if str(mem_p) not in sys.path:
                sys.path.insert(0, str(mem_p))
            import owner_recall as _or  # noqa: WPS433
            import session_memory as _sm  # noqa: WPS433
            facts = list(_or.recall_for_owner_ask(q, limit=4) or [])
            for t in (_sm.recent(6) or []):
                if isinstance(t, dict) and t.get("text_preview"):
                    session_bits.append(
                        f"· [{t.get('role','?')}] {t.get('text_preview')}"
                    )
        except Exception:  # noqa: BLE001
            facts, session_bits = [], []
        lines = [
            "حافظه cite-only است (may_authorize=false · بدون commit).",
        ]
        if facts:
            lines.append("از MemoryGate/self-loop:")
            for f in facts[:4]:
                if not isinstance(f, dict):
                    continue
                prev = str(f.get("content_preview") or f.get("mkey") or "")[:160]
                src = f.get("source_path") or f.get("provenance") or "?"
                lines.append(f"· {prev}  [{src}]")
        else:
            lines.append("از فایل episodic چیزی برای این سؤال پیدا نکردم (خالی صادق).")
        if session_bits:
            lines.append("از session اخیر (موقت):")
            lines.extend(session_bits[:4])
        else:
            lines.append("session خالی یا هنوز نوبتی ذخیره نشده.")
        if re.search(r"improve|خودبهبود|self.?loop", q, re.I) and not facts:
            lines.append(
                "برای آخرین improve: اگر فایل state خالی است، نمی‌دانم — "
                "نه اینکه «هیچ improveی نبوده» را جعل کنم."
            )
        lines.append("شاهد: owner_recall.py · session_memory.py · OCTOPUS-HONESTY.md")
        return _reply(
            "memory",
            "\n".join(lines),
            data={
                "status": "MEMORY_RECALL",
                "may_authorize": False,
                "facts": facts,
                "session_turns": len(session_bits),
            },
        )
    if _HONEST_SELF.search(q):
        return _reply(
            "honest-self",
            "نه — phenomenal consciousness / qualia ندارم و ادعای AGI نمی‌کنم.\n"
            "مدلِ من access-consciousness مهندسی است: وضعیت فایل‌ها، ضربان، "
            "و خودمدل ساختاری.\n"
            "قلب‌ها: کد در `_ops/heart/` + cardiac/arbiter روی organism؛ "
            "hybrid production wire فعلاً CLOSED.\n"
            "مغزهای زنده: cortex + business_brain (file-bridge به چت). "
            "4d/Super-Gov وصل نیست.\n"
            "SoT: `_ops/OCTOPUS-HONESTY.md`",
            data={
                "status": "HONEST_SELF",
                "may_authorize": False,
                "claims_agi": False,
                "phenomenal_consciousness": False,
            },
        )
    # 2026-08-12: greet fallback — کاراکترهای نامرئی (ZWNJ/RTL) ممکن است regex را بشکنند
    _q_clean = q.strip().rstrip("؟?!.,\u200c\u200e\u200f")
    if _q_clean.lower() in _GREET_WORDS or _GREET.search(q):
        text_out, data = _live_greeting(q)
        return _reply("intro", text_out, data=data)
    if _INTRO.search(q):
        text_out, data = _live_intro_witness()
        return _reply("intro", text_out, data=data)
    if _SELF_AWARE.search(q):
        text_out, data = _live_intro_witness()
        return _reply("intro", text_out, data=data)
    if _SELFMAP.search(q):
        text_out, data = _selfmap_summary()
        return _reply("selfmap", text_out, data=data)
    if _GOAL.search(q):
        return _reply("goal", status.current_goal())
    if _RUNTIME.search(q):
        return _reply("runtime", status.runtime_truth())
    if _PAIN.search(q):
        return _reply("protective-status", status.protective_truth(),
                      data={"status": "SHADOW_PROPOSAL_ONLY",
                            "control_authority": False})
    # درد خام («دردم زیاده») اگر _PAIN نگرفت — هنوز معادله نشود
    if re.search(r"دردم?\s*زیاد|pain\s*(high|status)", q, re.I) and not _EQUATION.search(q):
        return _reply("protective-status", status.protective_truth(),
                      data={"status": "SHADOW_PROPOSAL_ONLY",
                            "control_authority": False,
                            "note": "INT-03: pain≠equation"})
    if _META_MISS.search(q):
        return _reply(
            "meta",
            "حق با توست — قبلاً الگوی «موانع چیست» را نمی‌گرفتم و خودم "
            "همان جمله را در پیشنهادها می‌نوشتم. الان intent درست شده.\n\n"
            "دوباره بپرس: «موانع چیست؟» یا «وضعیت چیست؟» یا «هدف چیست؟»\n"
            "منبع: deterministic-stub (مدل خاموش؛ جواب از snapshot زنده).",
            data={"status": "META_INTENT_FIXED"},
        )
    if _BLOCK.search(q):
        return _reply("blockers", status.blockers())
    if _DISC.search(q):
        return _reply("discovery", status.discovery())
    if _NO_SEND.search(q):
        return _reply("safety-boundary",
            "✅ ثبتِ مکالمه‌ای: این رابط هیچ پیام، خرج یا اثر بیرونی انجام نمی‌دهد.\n"
            "هر ارسال واقعی باید action جدا، کارت bound، رأی تازه و receipt داشته باشد.",
            data={"status": "NO_EXTERNAL_EFFECT_WITHOUT_FRESH_OWNER_APPROVAL"})
    if _READ_MISSION.search(q):
        p = status.readonly_mission(q)
        return _reply("readonly-proposal",
            "📋 مأموریت فقط‌خواندنی آماده شد، ولی هنوز submit نشده.\n"
            f"نیت: {p['intent']}\nخرج: ۰ · اثر بیرونی: ۰\n"
            "برای اجرا باید به Mission/Action Bridge زنده متصل شود.", data=p)
    if _BOARD_CMD.search(q):
        return _board_command_from_text(q)
    if _SEND.search(q):
        return _reply("owner-gate",
            "🔐 این درخواست اثر بیرونی دارد. این رابط آن را اجرا نمی‌کند.\n"
            "فقط می‌توانم یک draft و کارت رأی بسازم؛ ارسال واقعی نیازمند رأی تازه و receipt است.",
            data={"status": "BLOCKED_BY_OWNER", "external_effect": True})
    # فاز Q — intentهای جدید (قبل از clarify؛ بعد از intentهای سریع)
    # MEMORY_ASK / SESSION_MEM بالاتر (قبل از intro) پردازش شدند — تکرار نکن.
    if _LIMITATIONS.search(q):
        return _reply(
            "limitations",
            "چیزهایی که فعلاً نمی‌توانم یا وصل نیستم:\n"
            "· 4d_system / Super-Governor وصل نیست (DEPRECATED/SPEC)\n"
            "· CR-B1 کوراموتو فقط pure helper است (runtime وصل نیست)\n"
            "· σ v2 (connectivity_ratio) فقط shadow است\n"
            "· semantic write خودکار ممنوع (نیازمند رأی شما)\n"
            "· session memory فقط preview کوتاه است\n"
            "· model path ممکن است ۲۰-۴۰ ثانیه طول بکشد (DeepSeek)\n"
            "شاهد: _ops/cognitive/truth_layer.py — هر ادعا با file evidence بررسی شده.",
            data={"status": "LIMITATIONS_HONEST", "may_authorize": False},
        )
    if _EVIDENCE.search(q):
        # شاهد برای ادعاهای پاسخ قبلی — در data به‌صورت facts آمده؛ اینجا خلاصه.
        return _reply(
            "evidence",
            "شاهد هر ادعا در بخش data.facts / Sources همین پاسخ می‌آید:\n"
            "· owner_recall → مسیر فایل/record\n"
            "· equation_advice → state/معادله\n"
            "· architecture → فایل + caller\n"
            "اگر چیزی شاهد ندارد، یعنی تأیید نشده — نه حدس.\n"
            "شاهد این پاسخ: data.facts در response /api/collab",
            data={"status": "EVIDENCE_EXPLAINED", "may_authorize": False},
        )
    if _EQUATION.search(q):
        try:
            import sys
            from pathlib import Path
            mem_p = Path(__file__).resolve().parent.parent / "memory"
            if str(mem_p) not in sys.path:
                sys.path.insert(0, str(mem_p))
            from equation_explainer import explain as _eq_explain  # noqa: WPS433
            res = _eq_explain(q)
            return _reply("equation", res.get("text", "معادله پیدا نشد."),
                          data={"status": "EQUATION",
                                "equation": res.get("equation"),
                                "matched": res.get("matched"),
                                "equation_advice_only": True,
                                "decision_effect": False,
                                "apply_effect": False,
                                "may_authorize": False})
        except Exception as exc:  # noqa: BLE001
            return _reply("equation",
                          "توضیح‌گر معادلات در دسترس نیست (%s) — صادقانه: فعلاً نمی‌توانم این را توضیح دهم." % type(exc).__name__,
                          data={"status": "EQUATION_UNAVAILABLE", "may_authorize": False})
    if _ARCHITECTURE.search(q):
        try:
            import sys
            from pathlib import Path
            mem_p = Path(__file__).resolve().parent.parent / "memory"
            if str(mem_p) not in sys.path:
                sys.path.insert(0, str(mem_p))
            from architecture_explainer import explain as _arch_explain  # noqa: WPS433
            res = _arch_explain(q)
            return _reply("architecture", res.get("text", ""),
                          data={"status": "ARCHITECTURE",
                                "architecture": res.get("architecture"),
                                "matched": res.get("matched"),
                                "may_authorize": False})
        except Exception as exc:  # noqa: BLE001
            return _reply("architecture",
                          "نقشهٔ معماری در دسترس نیست (%s). تب System را ببین." % type(exc).__name__,
                          data={"status": "ARCH_UNAVAILABLE", "may_authorize": False})
    if _LEGS.search(q):
        try:
            from . import legs_status as _ls
            text = _ls.format_for_chat()
            data = {"status": "LEGS", "may_authorize": False, "read_only": True,
                    "pin": "healthz", "pin_means": "http-listener-only"}
        except Exception as exc:  # noqa: BLE001
            text = (
                "وضعیتِ بیزنس‌های برد در دسترس نیست (%s). "
                "برد مستقل است؛ این فقط رصد است." % type(exc).__name__
            )
            data = {"status": "LEGS_UNKNOWN", "may_authorize": False}
        return _reply("legs", text, data=data)
    if _BUSINESS.search(q):
        # 2026-08-12 fix (اشتباهِ معماری): این بلوک کپی‌پیستِ ناقصِ هندلرِ
        # _EQUATION بالای خودش بود — equation_explainer را import می‌کرد
        # (نه business_brain)، res از hasattr روی خودِ تابعِ explain همیشه
        # None بود و هیچ‌وقت استفاده نمی‌شد، و هم شاخهٔ موفق هم شاخهٔ except
        # همیشه «زنده» می‌گفتند — یعنی این هندلر ساختاراً نمی‌توانست چیزی جز
        # «زنده» گزارش کند، حتی اگر business_brain واقعاً خاموش/از کار افتاده
        # بود. حالا فایلِ وضعیتِ واقعی‌اش خوانده و سن/فلگِ توقف چک می‌شود.
        try:
            import time as _t
            from pathlib import Path
            import json
            ops_dir = Path(__file__).resolve().parent.parent
            bb_p = ops_dir / "state" / "cortex" / "business-brain-latest.json"
            stopped = [n for n in ("STOP-ORGANISM", "STOP-CORTEX", "HALT-ALL")
                       if (ops_dir / n).exists()]
            bb = json.loads(bb_p.read_text(encoding="utf-8"))
            age_s = _t.time() - bb_p.stat().st_mtime
            if stopped:
                status_line = "متوقف است (" + "، ".join(stopped) + ")"
            elif age_s > 3600:
                status_line = f"آخرین وضعیت {int(age_s / 60)} دقیقه پیش — کهنه"
            else:
                status_line = f"زنده (beat={bb.get('beat')}, {int(age_s)}s پیش)"
            text = ("مغز تجاری (business_brain): " + status_line + "؛ "
                    "پیشنهادهایش از مسیر proposal می‌آید، نه این چت.\n"
                    "شاهد: state/cortex/business-brain-latest.json")
            data = {"status": "BUSINESS", "may_authorize": False}
        except Exception as exc:  # noqa: BLE001
            text = ("وضعیتِ business_brain نامعلوم/در دسترس نیست (%s).\n"
                    "شاهد: state/cortex/business-brain-latest.json" % type(exc).__name__)
            data = {"status": "BUSINESS_UNKNOWN", "may_authorize": False}
        return _reply("business", text, data=data)
    if _EFFECT.search(q):
        # فاز T/N — اثر: فقط proposal؛ PolicyGate مرجع؛ هرگز اجرا.
        try:
            import sys
            from pathlib import Path
            mem_p = Path(__file__).resolve().parent.parent / "memory"
            if str(mem_p) not in sys.path:
                sys.path.insert(0, str(mem_p))
            import limited_effect as _le  # noqa: WPS433
            enabled = _le.enabled()
            if not enabled:
                return _reply(
                    "effect",
                    "اثر محدود هنوز مجاز نیست (رأی انتخاب ۳ در فاز M فعال نشده). "
                    "می‌توانم پیشنهاد بسازم، ولی هیچ throttle/pause اجرا نمی‌شود.",
                    data={"status": "EFFECT_NOT_ENABLED", "policy_gate_status": "NOT_REQUESTED",
                          "applied": False, "may_authorize": False},
                )
            proposal = _le.evaluate({
                "action": "pause_proposal",
                "proposal_hash": "sha256:chat-request-not-bound",
                "policy_version": "ADR-033-v1",
                "state_version": 0,
                "expiry_at": "2099-01-01T00:00:00Z",
                "idempotency_key": "chat-effect-" + str(abs(hash(q)) % 10**6),
                "owner_verdict": "owner:phase-m-choice3",
            })
            if proposal.get("allowed"):
                text = ("پیشنهاد اثر ساخته شد (pause/throttle) — هنوز اجرا نشده.\n"
                        "مرجع تصمیم نهایی: PolicyGate.\n"
                        "وضعیت: ALLOWED_AS_PROPOSAL · applied=false")
            else:
                text = ("پیشنهاد اثر رد شد: " + str(proposal.get("reason")) +
                        "\nهیچ تغییری اعمال نشد.")
            return _reply("effect", text,
                          data={"status": "EFFECT_PROPOSAL",
                                "policy_gate_status": proposal.get("decision"),
                                "applied": False, "may_authorize": False})
        except Exception as exc:  # noqa: BLE001
            return _reply("effect",
                          "مسیر اثر در دسترس نیست (%s). هیچ چیزی اجرا نشد." % type(exc).__name__,
                          data={"status": "EFFECT_UNAVAILABLE", "applied": False,
                                "may_authorize": False})
    if _DISCOVER.search(q):
        try:
            from owner_console.discovery_facade import discover_reply
            reply = discover_reply(query=q)
            text = reply.text
            data = {
                "status": "DISCOVER_PROMPT",
                "gateway": "discovery_facade.v2",
                "evidence_level": reply.evidence_level,
                "limitations": list(reply.limitations),
                "facts": reply.as_dict().get("facts"),
            }
        except Exception:  # noqa: BLE001
            text = (
                "برای کشف مشترک: از dark inventory و شواهد می‌گویم چه چیزی "
                "ساخته شده ولی خاموش است — بدون arm خودکار."
            )
            data = {"status": "DISCOVER_PROMPT"}
        return _reply(
            "discover",
            text,
            data=data,
            keyboard=[
                [{"text": "📎 Sources / شواهد", "callback_data": "oc:discover-sources"},
                 {"text": "🧠 Living card", "callback_data": "oc:living"}],
                [{"text": "🏠 خانه", "callback_data": "oc:home"}],
            ],
        )
    if _CAPS.search(q):
        rows = catalog.discover()
        return _reply("capabilities", views.capabilities(rows), keyboard=views.keyboard(rows))
    # 2026-08-12 fix (همان کلاسِ باگِ owner_guidance): کاتالوگ باید قبل از
    # fallbackِ سستِ _GENERAL_CHAT چک شود. قبلاً _GENERAL_CHAT (کلیدواژه‌های
    # عمومی مثل «خبر») حتی owner_phrase ثبت‌شدهٔ خودِ یک قابلیت را می‌قاپید —
    # مثلاً world_discovery دقیقاً عبارتِ «بیرون چه خبر» را به‌عنوان راهِ
    # رسیدن به خودش ثبت کرده (capability-manifest.json)، ولی چون _GENERAL_CHAT
    # زودتر چک می‌شد، کاربر به‌جای کارتِ واقعیِ قابلیت، پاسخِ عمومیِ stub
    # می‌گرفت. حالا catalog.find() اول اجرا می‌شود؛ فقط وقتی match نداشت به
    # _GENERAL_CHAT می‌رسیم.
    rows = catalog.discover()
    row = catalog.find(q, rows)
    if row:
        return _reply("capability", views.capability(row),
                      data={"capability_id": row["capability_id"], "status": row["status"]})
    # سؤال‌های عمومی/دانشی → chat (مدل می‌تواند جواب بدهد؛ clarify نه)
    if _GENERAL_CHAT.search(q):
        return _reply(
            "chat",
            "این سؤال خارج از وضعیتِ زندهٔ من است، ولی می‌توانم کمک کنم:\n"
            "· دربارهٔ خودم: «از چی تشکیل شدی؟» یا «راجب خودت چی میدونی؟»\n"
            "· دربارهٔ وضعیت: «وضعیت چیست؟» · «موانع چیست؟»\n"
            "· دربارهٔ معماری/معادلات: «Pulse Arbiter به چی وصله؟» یا «BCM چیه؟»\n"
            "اگر جوابِ دانشی می‌خواهی، با مدل (همکار) بپرس — این پاسخ stub است.",
            data={"status": "GENERAL_CHAT_STUB", "may_authorize": False},
        )
    # clarify سبک: یک بار snapshot (cache) — نه goal+runtime جدا و سنگین.
    try:
        _goal = status.current_goal()
        _rt = status.runtime_truth()
    except Exception:  # noqa: BLE001
        _rt = _goal = None
    _help = (
        "من دقیق نفهمیدم چی پرسیدی، ولی اینم چیزی که میدونم:\n\n"
    )
    if _goal:
        _help += f"🎯 {_goal.split(chr(10))[0]}\n\n"
    if _rt:
        for line in _rt.split(chr(10))[:3]:
            if line.strip():
                _help += f"{line}\n"
    _help += (
        "\n میتونی اینطوری بپرسی:\n"
        "• «وضعیت چیست؟»\n• «هدف چیست؟»\n• «موانع چیست؟»\n"
        "• «قابلیت‌ها»\n• یا هر سؤالی — سعی می‌کنم کمکت کنم."
    )
    return _reply("clarify", _help,
                  data={"status": "CLARIFY", "original": q[:300]})


_BOARD_KB = [
    [{"text": "پرسش مغز", "callback_data": "oc:board:ask"},
     {"text": "وضعیت عمیق", "callback_data": "oc:board:status"}],
    [{"text": "پنل", "callback_data": "oc:board:panel:panel"},
     {"text": "زیمان", "callback_data": "oc:board:panel:ziman"}],
    [{"text": "لید", "callback_data": "oc:board:panel:lead"},
     {"text": "استودیو", "callback_data": "oc:board:panel:studio"}],
    [{"text": "تاسک (رأی لازم)", "callback_data": "oc:board:task"}],
]


def _infer_board_kind(q: str) -> str:
    if re.search(r"تاسک|\btask\b", q, re.I):
        return "task"
    if re.search(r"پنل|\bpanel\b", q, re.I):
        return "panel"
    if re.search(r"وضعیت عمیق|\bstatus\b", q, re.I):
        return "status"
    return "ask"


def _infer_board_target(q: str) -> tuple:
    if re.search(r"hypno|هیپنو", q, re.I):
        return "hypno", "hypno"
    mapping = (
        ("ziman", "زیمان"), ("lead", "لید"),
        ("studio", "استودیو"), ("panel", "پنل"),
    )
    for inst, fa in mapping:
        if re.search(inst, q, re.I) or fa in q:
            return "ofn", inst
    return "ofn", "panel"


def _board_command_reply(kind: str, text: str, *, agent: str = "ofn",
                         instance: str = "panel") -> dict:
    try:
        import sys
        from pathlib import Path
        ops = Path(__file__).resolve().parent.parent
        if str(ops) not in sys.path:
            sys.path.insert(0, str(ops))
        from board_cp import service as _bcp  # noqa: WPS433
        stored = _bcp.enqueue(
            kind=kind, text=text, target_agent=agent,
            target_instance=instance, source="chat",
        )
    except Exception as exc:  # noqa: BLE001
        return _reply(
            "board-command",
            "صفِ فرمان در دسترس نیست (%s). هیچ چیزی به برد نرفت."
            % type(exc).__name__,
            data={"status": "BOARD_CP_UNAVAILABLE", "may_authorize": False},
        )
    lines = [
        "فرمان به صفِ Control Plane رفت — هنوز به برد ارسال نشده.",
        f"kind={kind} · instance={instance} · state={stored.get('state')}",
        f"message_id={stored.get('message_id')}",
    ]
    if not stored.get("gate0"):
        lines.append(
            "Gate 0 باز است: CONTROL_URL ویندوز-facing + Bearer را مالک می‌گذارد."
        )
    if not stored.get("flag"):
        lines.append("فلگ OCTOPUS_BOARD_CP خاموش است — برد چیزی نمی‌کشد.")
    if kind == "task":
        lines.append("تاسک owner_required است؛ بدون رأی تازه pull نمی‌شود.")
    lines.append("ویندوز به :8796 و /api/* برد دست نمی‌زند.")
    return _reply(
        "board-command", "\n".join(lines), keyboard=_BOARD_KB,
        data={
            "status": "BOARD_COMMAND_QUEUED",
            "may_authorize": kind == "task",
            "message_id": stored.get("message_id"),
            "kind": kind,
            "owner_required": stored.get("owner_required"),
            "armed": stored.get("armed"),
            "send_attempted": False,
        },
    )


def _board_command_from_text(q: str) -> dict:
    return _board_command_reply(
        _infer_board_kind(q), q,
        agent=_infer_board_target(q)[0],
        instance=_infer_board_target(q)[1],
    )


def _board_command_from_callback(d: str) -> dict:
    rest = d[len("oc:board:"):]
    if rest.startswith("panel:"):
        inst = rest.split(":", 1)[-1]
        if inst not in ("ziman", "lead", "studio", "panel"):
            inst = "panel"
        return _board_command_reply("panel", "panel:" + inst, instance=inst)
    if rest == "task":
        return _board_command_reply("task", "task")
    if rest == "status":
        return _board_command_reply("status", "status")
    return _board_command_reply("ask", "ask")


def callback(data: str) -> dict:
    d = str(data or "")
    if d == "oc:home": return handle("خانه")
    if d == "oc:caps": return handle("همه قابلیت‌ها")
    if d == "oc:goal": return handle("هدف فعلی")
    if d == "oc:runtime": return handle("شاهد runtime")
    if d == "oc:blockers": return handle("موانع")
    if d == "oc:discovery": return handle("World Discovery")
    if d == "oc:discover-hidden": return handle("چه چیزی پنهان داری؟")
    if d == "oc:discover-sources":
        try:
            from owner_console.discovery_facade import discover_sources_text
            text = discover_sources_text(query="کشف")
        except Exception as exc:  # noqa: BLE001
            text = f"شواهد در دسترس نیست ({type(exc).__name__})."
        return _reply(
            "discover-sources",
            text,
            data={"status": "DISCOVER_SOURCES"},
            keyboard=[[{"text": "🔦 پنهان؟", "callback_data": "oc:discover-hidden"},
                       {"text": "🏠 خانه", "callback_data": "oc:home"}]],
        )
    if d == "oc:living":
        try:
            from owner_console.discovery_pulse import living_card
            text = living_card()
        except Exception as exc:  # noqa: BLE001
            text = f"Living card در دسترس نیست ({type(exc).__name__})."
        return _reply(
            "living-card",
            text,
            data={"status": "LIVING_CARD"},
            keyboard=[[{"text": "🔦 پنهان؟", "callback_data": "oc:discover-hidden"},
                       {"text": "🏠 خانه", "callback_data": "oc:home"}]],
        )
    if d.startswith("oc:board:"):
        return _board_command_from_callback(d)
    if d.startswith("oc:c:"):
        cid = d[5:]
        row = next((r for r in catalog.discover() if r["capability_id"] == cid), None)
        return _reply("capability", views.capability(row),
                      data={"capability_id": cid, "status": row["status"] if row else "UNKNOWN"})
    if d.startswith("oc:p:"):
        try: page = int(d[5:])
        except ValueError: page = 0
        rows = catalog.discover()
        return _reply("capabilities", views.capabilities(rows), keyboard=views.keyboard(rows, page))
    return _reply("blocked", "این دکمه شناخته‌شده نیست و هیچ عملی انجام نشد.",
                  data={"status": "BLOCKED_UNKNOWN_CALLBACK"})


def _reply(kind: str, text: str, *, keyboard=None, data=None) -> dict:
    return {"schema": "owner-console.reply.v1", "kind": kind, "text": str(text),
            "keyboard": list(keyboard or []), "data": dict(data or {}),
            "external_effect": False, "estimated_cost": 0,
            "send_attempted": False, "authorization": None}
