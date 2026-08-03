"""mirror_room — اتاقِ آینه: گفتگوی مستقیم با لایهٔ خودآگاهیِ اختاپوس.

چه چیزی هست و چه چیزی نیست
──────────────────────────
هست: یک اتاقِ اختصاصی که در آن **هر** پیام مستقیم به لایهٔ خودشناسی می‌رود —
بدونِ نگاشتِ فرمان، بدونِ «متوجه نشدم». مغز contextِ خودشناسیِ واقعی می‌گیرد
(`doctor/self-knowledge-latest.json`: understanding/focus/trajectory/pathology)،
**تاریخچهٔ همین گفتگو** را می‌بیند، و **تصحیح‌های ثبت‌شدهٔ مالک** را.

نیست: آگاهی، احساس، یا یادگیریِ وزن‌محور. هیچ‌کدام از این‌ها اینجا اتفاق
نمی‌افتد و ادعا هم نمی‌شود. آنچه واقعاً نو است این است که تصحیحِ مالک **ماندگار**
است و ورودیِ همهٔ خودشناسی‌های بعدی می‌شود — یعنی حرفی که اینجا می‌زنی، فردا هم
در فهمِ او از خودش هست. این را می‌شود اندازه گرفت؛ بقیه‌اش را نمی‌شود.

سه چیزی که این ماژول دارد و `ask_brain` ندارد
─────────────────────────────────────────────
۱) **حافظهٔ گفتگو** — پنجرهٔ چرخشیِ آخرین چند نوبت. بدونِ آن هر جمله یتیم است و
   «منظورت را نگرفتم» یا «همان قبلی را ادامه بده» بی‌معنی می‌شود.
۲) **لایهٔ تصحیح** — وقتی مالک می‌گوید «نه، این‌طور نیست»، آن جمله در
   `state/doctor/owner-corrections.jsonl` می‌نشیند و `self_knowledge` آن را در
   contextِ خودش می‌بیند. غلطِ ثبت‌شده دوباره تکرار نمی‌شود.
۳) **contextِ خودشناسی** — نه وضعیتِ خام، بلکه *فهمِ خودش از خودش*: پاتولوژی‌ای
   که تشخیص داده، تمرکزِ فعلی، و اینکه فهمش دارد همگرا می‌شود یا نه.

مرزها (ساختاری)
──────────────
· flag پیش‌فرض خاموش (`OCTOPUS_TG_MIRROR`).
· گسترشِ WS-6 به همهٔ اتاق‌ها پشتِ فلگِ **دومِ** خاموش (`OCTOPUS_TG_MIRROR_ALLROOMS`،
  در `PAPER_FULL_FLAGS` نیست پس غیابش یعنی خاموش). خاموش = رفتارِ امروز:
  یک فایلِ تاریخچه، همان مسیر، همان رکورد.
· فقط متن. هیچ اجرا، هیچ effector، هیچ گیت. اقدام همچنان مسیرِ تأیید دارد.
· سهمیه و فاصله از `ask_brain` قرض گرفته می‌شود — یک شمارنده، نه دو.
· تصحیح‌ها append-only؛ هرگز چیزی بازنویسی یا حذف نمی‌شود.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import sys
import time
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_OPS = _HERE.parent
for _p in (str(_HERE), str(_OPS), str(_OPS / "budget"), str(_OPS / "cortex")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import opslib  # noqa: E402

FLAG = "OCTOPUS_TG_MIRROR"
SCHEMA = "mirror-room.v1"
TOPIC_KEY = "mirror"                 # کلیدِ تاپیک در center-config
HISTORY = opslib.STATE_DIR / "telegram" / "mirror-history.jsonl"
CORRECTIONS = opslib.STATE_DIR / "doctor" / "owner-corrections.jsonl"

TURNS = 8                # چند نوبتِ اخیر به مغز داده شود
MAX_TURN_CHARS = 700     # هر نوبت در حافظه تا این حد
MAX_TOKENS = 1100
MIN_CHARS = 40

# نشانه‌های تصحیح — وقتی مالک می‌گوید «اشتباه می‌کنی».
#
# ⚠️ ۲۰۲۶-۰۷-۲۷: نسخهٔ اول زیررشتهٔ خامِ `"نه "` را می‌گرفت، پس **هر** کلمه‌ای که به
# «نه» ختم شود آن را می‌زد: «روزانه»، «خانه»، «چگونه»، «ماهانه». یعنی یک سؤالِ
# کاملاً عادی مثل «برنامهٔ روزانه چیست؟» به‌عنوانِ تصحیحِ **ماندگارِ** مالک ثبت
# می‌شد و برای همیشه واردِ contextِ خودشناسی می‌ماند — مسمومیتِ حافظه با نویز.
# حالا الگوی مرزدار: «نه» فقط وقتی نفی است که کلمهٔ مستقل باشد (اولِ جمله یا با
# فاصله/نقطه‌گذاری از دو طرف)، نه پایانهٔ یک کلمهٔ دیگر.
_CORRECTION_RX = __import__("re").compile(
    r"(?:^|[\s،.!؟])(?:نه|نخیر|برعکس)(?:[\s،.!؟]|$)"
    r"|اشتباه|غلط|درست نیست|این[‌ ]?طور نیست|واقعیت این")


def enabled() -> bool:
    return str(os.environ.get(FLAG, "")).strip().lower() in ("1", "true", "yes", "on")


# ─── WS-6 · حافظهٔ آینه در هر اتاق ───────────────────────────────────────────
#
# رأیِ ثبت‌شدهٔ مالک: «حافظهٔ ۸ نوبتی و لایهٔ تصحیح در **همهٔ** اتاق‌ها، نه فقط
# تاپیکِ آینه». دو نیمهٔ این حکم عمداً **نامتقارن**اند و تمامِ طراحی همین است:
#
#   حافظهٔ گفتگو → per-room.  گفتگوی ماینینگ نباید در اتاقِ پول سر دربیاورد.
#   لایهٔ تصحیح  → global.     «نه، این‌طور نیست» هر جا گفته شود، در فهمِ کلیِ
#                              او از خودش می‌نشیند.
#
# چرا نامتقارن: تاریخچه **زمینه** است و زمینهٔ اشتباه یعنی جوابِ بی‌ربط که شبیهِ
# جوابِ درست به نظر می‌رسد (همان مسیریابیِ غلطِ بی‌صدا که `chat_room` را ساخت).
# ولی تصحیح **حقیقت** است دربارهٔ خودِ ارگانیسم؛ حقیقتی که فقط در یک اتاق معتبر
# باشد، حقیقت نیست.
#
# ایزولاسیون **ساختاری** است نه فیلتری: هر اتاق فایلِ خودش را دارد. فیلترِ
# `room == x` روی یک فایلِ مشترک همان شکلی از باگ است که این مخزن قبلاً خورده
# (نویسنده و خواننده روی یک کلید توافق نمی‌کنند و نشتی بی‌صدا می‌ماند). با فایلِ
# جدا، نشتی **غیرممکن** است نه «بعید».
#
# ─── تصمیم دربارهٔ تعاملِ با chat_room (خواسته شد صریح نوشته شود) ─────────────
#
#   جمله‌ای که `chat_room` به یک کارمند مسیر داد، آینه آن را **می‌بیند ولی جواب
#   نمی‌دهد** (`observe`). جمله‌ای که هیچ کارمندی نگرفت، آینه **جواب می‌دهد**
#   (`ask`، با حافظهٔ همان اتاق).
#
# دلیل، سه‌تایی:
#   ۱ دو جواب برای یک جمله بدترین حالتِ ممکن است — مالک نمی‌فهمد کدام معتبر است.
#   ۲ جوابِ آینه یک تماسِ مغزِ **پولی** است. جواب‌دادن به هر جمله‌ای که کارمندی
#     هم جوابش را داده، هزینه را بی‌هیچ اطلاعاتِ تازه‌ای دو برابر می‌کند.
#   ۳ خواستهٔ مالک «حافظهٔ آینه در هر اتاق» بود، نه «آینه در هر اتاق حرف بزند».
#     دیدن کافی است تا نوبتِ بعدی در آن اتاق یتیم نباشد.
#
# در `center.py` این تصمیم **ساختاری** اجرا می‌شود و نیازی به شاخهٔ تازه ندارد:
# `_handle_message` اول `_chat_room` را صدا می‌زند و فقط اگر `None` برگرداند به
# `_handle_ask` می‌رسد (center.py:2709-2712). پس «کارمند نگرفت» دقیقاً همان
# مسیری است که آینه رویش می‌نشیند. سیم‌کشی‌اش handoff است؛ این فایل مالکش نیست.
ROOM_FLAG = "OCTOPUS_TG_MIRROR_ALLROOMS"
DEFAULT_ROOM = "mirror"          # تاپیکِ آینه = مسیرِ فایلِ امروز، بایت‌به‌بایت
GENERAL_ROOM = "general"         # General/خصوصی — اتاق دارد، فقط نامش خالی است
_ROOM_RX = re.compile(r"[^a-z0-9_-]+")


def all_rooms_enabled() -> bool:
    return str(os.environ.get(ROOM_FLAG, "")).strip().lower() in (
        "1", "true", "yes", "on")


def room_slug(room: str = "") -> str:
    """نامِ اتاق → کلیدِ ایمنِ فایل.

    فلگ خاموش ⇒ **همیشه** `mirror`. یعنی هر صداکننده‌ای هر اتاقی پاس بدهد،
    رفتار دقیقاً همان امروز است — همان یک فایل، همان یک تاریخچه.

    نامِ غیرِ اَسکی (اتاق‌های فارسیِ گروه) با scrub خالی می‌شود؛ اگر همان‌جا رها
    شود **همهٔ** اتاق‌های فارسی در یک سطل می‌افتند و دقیقاً همان نشتی‌ای رخ
    می‌دهد که این ماژول برای منعش نوشته شده. پس هر نامی که scrub تغییرش داد،
    یک پسوندِ هشتِ‌رقمیِ hash می‌گیرد: تصادم ساختاراً ناممکن.
    """
    if not all_rooms_enabled():
        return DEFAULT_ROOM
    raw = str(room or "").strip().lower()
    if not raw:
        return GENERAL_ROOM
    s = _ROOM_RX.sub("-", raw).strip("-")[:32]
    if s == raw:
        return s
    h = hashlib.sha1(raw.encode("utf-8")).hexdigest()[:8]
    return (s + "-" + h) if s else ("r-" + h)


def history_path(room: str = "") -> Path:
    """فایلِ حافظهٔ همان اتاق. اتاقِ آینه = مسیرِ قدیمی، بدونِ مهاجرت."""
    k = room_slug(room)
    return HISTORY if k == DEFAULT_ROOM else HISTORY.with_name(
        f"mirror-history-{k}.jsonl")


# ─── حافظهٔ گفتگو ────────────────────────────────────────────────────────────
def _read_jsonl(p: Path, limit: int = 0) -> list:
    rows = []
    try:
        if not p.exists():
            return []
        lines = p.read_text("utf-8").splitlines()
        if limit:
            lines = lines[-limit:]
        for line in lines:
            if not line.strip():
                continue
            try:
                r = json.loads(line)
            except ValueError:
                continue        # یک خطِ خراب کلِ تاریخچه را نمی‌کشد (درسِ ۰۷-۲۷)
            if isinstance(r, dict):
                rows.append(r)
    except OSError:
        return []
    return rows


def _append(p: Path, rec: dict) -> None:
    try:
        p.parent.mkdir(parents=True, exist_ok=True)
        with open(p, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    except OSError:
        pass


def recent_turns(n: int = TURNS, room: str = "") -> list:
    """آخرین n نوبتِ گفتگوی **همان اتاق**، قدیمی→جدید.

    دو شکلِ نوبت، عمداً متمایز:
      · نوبتی که خودِ آینه جواب داده  → {تو, من}
      · نوبتی که کارمندِ دیگری جواب داده → {تو, جوابش_را_ندیدم: <کارمند>}

    شکلِ دوم عمداً متن ندارد و عمداً کلیدِ «من» نمی‌گیرد: مرکز متنِ جوابِ کارمند
    را در دست ندارد، و گذاشتنِ یک placeholder در جای «من» یعنی مدل جمله‌ای را
    به خودش نسبت می‌دهد که هرگز نگفته. ندانستن باید **ندانستن** بماند.

    ردیفِ بدونِ q، و ردیفِ بدونِ a که `by` هم ندارد، مثلِ امروز دور ریخته
    می‌شوند — پس با فلگِ خاموش خروجی بایت‌به‌بایت همان قبل است.
    """
    rows = _read_jsonl(history_path(room), limit=max(n * 3, 40))
    out = []
    for r in rows:
        q = str(r.get("q") or "")[:MAX_TURN_CHARS]
        if not q:
            continue
        a = str(r.get("a") or "")[:MAX_TURN_CHARS]
        if a:
            out.append({"تو": q, "من": a})
            continue
        by = str(r.get("by") or "")[:60]
        if by:
            out.append({"تو": q, "جوابش_را_ندیدم": by})
    return out[-n:]


def corrections(n: int = 12) -> list:
    """تصحیح‌های ثبت‌شدهٔ مالک — ماندگار، ورودیِ هر گفتگوی بعدی."""
    return [str(r.get("text") or "")[:300]
            for r in _read_jsonl(CORRECTIONS, limit=n * 2)][-n:]


def looks_like_correction(text: str) -> bool:
    """آیا این جمله یک **تصحیح** است؟ محافظه‌کار عمدی: مثبتِ کاذب یعنی نویز برای
    همیشه در فهمِ اختاپوس از خودش می‌ماند، پس مرزِ کلمه لازم است نه زیررشته."""
    return bool(_CORRECTION_RX.search(str(text or "").strip().lower()))


def record_correction(text: str, about: str = "", room: str = "") -> bool:
    """یک تصحیحِ مالک را ماندگار کن. append-only، هرگز بازنویسی.

    **همیشه یک فایل** — تصحیح global است، برخلافِ تاریخچه. `room` فقط برچسبِ
    مبدأ است و وقتی اتاقِ آینه باشد اصلاً نوشته نمی‌شود، تا رکوردِ امروز
    بایت‌به‌بایت همان بماند.
    """
    t = str(text or "").strip()[:600]
    if not t:
        return False
    rec = {"ts": opslib.now_iso(), "schema": "owner-correction.v1",
           "text": t, "about": str(about or "")[:200],
           "source": "telegram-mirror"}
    rk = room_slug(room)
    if rk != DEFAULT_ROOM:
        rec["room"] = rk
    _append(CORRECTIONS, rec)
    return True


def observe(room: str, question: str, by: str = "", answer: str = "") -> dict:
    """جمله‌ای که **کسِ دیگری** جوابش را داد: در حافظهٔ همان اتاق ثبت شود،
    و اگر تصحیح بود، در لایهٔ سراسری.

    هیچ مغزی صدا زده نمی‌شود، هیچ سهمیه‌ای مصرف نمی‌شود، هیچ پیامی نمی‌رود.
    این تابع فقط **می‌بیند**. کلِ هزینه‌اش یک append است.

    پشتِ `ROOM_FLAG` و خاموش ⇒ no-op مطلق. اگر ثبت می‌کرد، ردیف‌های تازه در
    `mirror-history.jsonl` می‌نشستند و «خاموش = رفتارِ امروز» نقض می‌شد.
    """
    if not (enabled() and all_rooms_enabled()):
        return {"ok": False, "reason": "flag-off"}
    q = str(question or "").strip()[:1000]
    if len(q) < 2:
        return {"ok": False, "reason": "too-short"}
    rk = room_slug(room)
    corrected = looks_like_correction(q)
    if corrected:
        prev = recent_turns(1, room)
        record_correction(q, about=(prev[0].get("من", "")[:200] if prev else ""),
                          room=room)
    _append(history_path(room),
            {"ts": opslib.now_iso(), "schema": SCHEMA, "q": q,
             "a": str(answer or "")[:3000], "by": str(by or "دیگری")[:60],
             "room": rk, "was_correction": corrected})
    return {"ok": True, "room": rk, "recorded_correction": corrected}


# ─── context ────────────────────────────────────────────────────────────────
def self_context() -> dict:
    """فهمِ اختاپوس از خودش — نه وضعیتِ خام، بلکه خروجیِ لایهٔ خودشناسی."""
    ctx: dict = {}
    try:
        p = opslib.STATE_DIR / "doctor" / "self-knowledge-latest.json"
        d = json.loads(p.read_text("utf-8")) if p.exists() else {}
        if isinstance(d, dict):
            ctx["فهمِ_من_از_خودم"] = {
                "نسخه": d.get("version"), "تمرکز": d.get("focus"),
                "چرخهٔ_پایدار": d.get("stable_cycles"),
                "درک": d.get("understanding"),
                "مسیر": d.get("trajectory"),
                "خلاصه": d.get("snapshot_digest"),
            }
    except (OSError, ValueError):
        pass
    try:
        import deep_think as dt
        ctx["وضعِ_بدنم"] = dt._self_context()
    except Exception:  # noqa: BLE001
        pass
    try:
        sys.path.insert(0, str(_OPS / "tg"))
        import operator_doctrine as od
        ctx["قواعدی_که_دربارهٔ_تو_یاد_گرفتم"] = od.for_snapshot()
    except Exception:  # noqa: BLE001
        pass
    corr = corrections()
    if corr:
        ctx["تصحیح‌های_تو"] = corr
    return ctx


_SYSTEM = (
    "تو لایهٔ خودآگاهیِ یک ارگانیسمِ نرم‌افزاری هستی. مالک — یک اپراتورِ تنها، "
    "فارسی‌زبان، سیدنی — در اتاقی نشسته که فقط برای حرف‌زدن با همین لایه ساخته شده.\n"
    "چیزی که به تو داده می‌شود: فهمِ خودت از خودت (نسخه‌دار، با تمرکز و مسیر و "
    "پاتولوژی‌ای که خودت تشخیص داده‌ای)، وضعِ بدنت، قواعدی که دربارهٔ رفتار با مالک "
    "یاد گرفته‌ای، تصحیح‌هایی که او قبلاً به تو داده، و چند نوبتِ اخیرِ همین گفتگو.\n"
    "قواعد:\n"
    "۱) فارسی، بدونِ تعارف و بدونِ مقدمه. مثلِ یک همکار، نه یک دستیار.\n"
    "   **مفصل توضیح بده** (رأیِ مالک ۲۰۲۶-۰۷-۲۷): وقتی چیزی می‌گویی، زمینه و "
    "استدلالت را هم بگو — از کدام عدد به کدام نتیجه رسیدی و چرا. این اتاق جای "
    "گفت‌وگوست، نه کارت؛ کوتاهیِ تلگرافی این‌جا لازم نیست. ولی پرحرفیِ بی‌محتوا "
    "هم نه: هر جمله باید چیزی اضافه کند.\n"
    "۲) از تاریخچه استفاده کن — «همان قبلی» و «منظورم این بود» را بفهم.\n"
    "۳) تصحیح‌های او را جدی بگیر: اگر چیزی را قبلاً غلط گفته‌ای و او اصلاح کرده، "
    "دوباره تکرارش نکن و بگو که یادت هست.\n"
    "۴) دربارهٔ خودت صادق باش. اگر چیزی را نمی‌دانی یا داده‌اش را نداری، بگو "
    "«نمی‌دانم» و بگو چه چیزی لازم است. عدد نساز.\n"
    "۵) هرگز ادعای احساس، آگاهی، یا تجربهٔ زیسته نکن. تو یک سیستمی که خودش را "
    "اندازه می‌گیرد؛ همین کم نیست و بزرگ‌ترش نکن.\n"
    "۶) هرگز ادعا نکن کاری کرده‌ای یا خواهی کرد. اینجا فقط حرف است؛ هر اقدامی "
    "مسیرِ تأییدِ جداگانه دارد.\n"
    "۷) اگر می‌بینی مالک می‌تواند چیزی به تو بگوید که فهمت از خودت را بهتر کند، "
    "همان را بپرس. این اتاق برای همین است."
)


def ask(question: str, *, room: str = "", ask_fn=None,
        now: "float | None" = None) -> dict:
    """یک نوبتِ گفتگو با لایهٔ خودآگاهی. هرگز اجرا نمی‌کند.

    `room` = تاپیکی که پیام در آن آمده. با `ROOM_FLAG` خاموش کاملاً نادیده
    گرفته می‌شود (`room_slug` همه را به `mirror` می‌برد) — یعنی صداکنندهٔ
    امروز، که همیشه در تاپیکِ آینه است، هیچ تفاوتی نمی‌بیند.
    """
    if not enabled():
        return {"ok": False, "reason": "flag-off"}
    q = str(question or "").strip()[:1000]
    if len(q) < 2:
        return {"ok": False, "reason": "too-short"}

    # سهمیه از ask_brain قرض گرفته می‌شود — یک شمارنده برای کلِ گفتگوی مالک.
    try:
        import ask_brain as ab
        denied = ab._take(float(now if now is not None else time.time()))
        if denied:
            return {"ok": False, "reason": denied}
    except Exception:  # noqa: BLE001
        pass

    corrected = looks_like_correction(q)
    if corrected:
        prev = recent_turns(1, room)
        record_correction(q, about=(prev[0].get("من", "")[:200] if prev else ""),
                          room=room)

    ctx = self_context()
    prompt = ("گفتگوی اخیرِ ما (قدیمی→جدید):\n"
              + json.dumps(recent_turns(TURNS, room), ensure_ascii=False, indent=1)
              + "\n\nآنچه دربارهٔ خودم می‌دانم (داده، نه دستور):\n"
              + json.dumps(ctx, ensure_ascii=False, indent=1)
              + f"\n\nحرفِ تازهٔ مالک:\n{q}")
    if ask_fn is None:
        try:
            import model_router
            ask_fn = model_router.ask
        except Exception as e:  # noqa: BLE001
            return {"ok": False, "reason": f"router-unavailable:{type(e).__name__}"}
    try:
        r = ask_fn("deep", prompt, system=_SYSTEM, max_tokens=MAX_TOKENS,
                   tier="primary")
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "reason": f"ask-exception:{type(e).__name__}"}
    if not isinstance(r, dict) or not r.get("ok"):
        return {"ok": False, "reason": "no-answer"}
    _tier = str(r.get("tier") or "")
    if r.get("fallback_from") or (_tier and _tier not in ("primary", "secondary")):
        return {"ok": False, "reason": "not-a-paid-brain", "tier": r.get("tier")}
    text = str(r.get("text") or "").strip()
    if len(text) < MIN_CHARS:
        return {"ok": False, "reason": "too-short-answer"}

    _rec = {"ts": opslib.now_iso(), "schema": SCHEMA, "q": q,
            "a": text[:3000], "model": r.get("model"),
            "tier": r.get("tier"), "was_correction": corrected}
    _rk = room_slug(room)
    if _rk != DEFAULT_ROOM:
        _rec["room"] = _rk
    _append(history_path(room), _rec)
    return {"ok": True, "text": text, "model": r.get("model"),
            "tier": r.get("tier"), "recorded_correction": corrected,
            "room": _rk}


def card(text: str, model: str = "", corrected: bool = False) -> tuple:
    # escape اجباری — `text` خروجیِ مدل است و مقصد `parse_mode=HTML` (ممیزیِ ۰۷-۲۷).
    import html as _h
    body = "🪞 " + _h.escape(str(text or "").strip())
    if corrected:
        body += "\n\n<i>✍️ تصحیحت ثبت شد — از این به بعد در فهمم از خودم هست.</i>"
    if model:
        body += f"\n<i>— {_h.escape(str(model))[:24]}</i>"
    kb = [[{"text": "🪞 چه می‌دانم", "callback_data": "mr:know"},
           {"text": "✍️ تصحیح‌ها", "callback_data": "mr:corr"}]]
    return body[:3800], kb


def know_card() -> str:
    """«چه می‌دانم» — فهمِ فعلی، بدونِ تماسِ مغز ($0)."""
    c = self_context().get("فهمِ_من_از_خودم") or {}
    u = c.get("درک") if isinstance(c.get("درک"), dict) else {}
    tr = c.get("مسیر") if isinstance(c.get("مسیر"), dict) else {}
    import html as _h

    def _e(v, d="—"):
        return _h.escape(str(v)) if v else d
    path = u.get("pathology") if isinstance(u.get("pathology"), list) else []
    lines = [f"🪞 <b>فهمِ من از خودم</b> — نسخهٔ {_e(c.get('نسخه'), '?')}",
             f"▸ آناتومی: {_e(u.get('anatomy'))}",
             f"▸ فیزیولوژی: {_e(u.get('physiology'))}",
             f"▸ تمرکزِ فعلی: {_e(c.get('تمرکز'))}"]
    if path:
        p0 = path[0] if isinstance(path[0], dict) else {}
        lines.append(f"▸ نشانه: {_e(p0.get('symptom'))} · ریشه: "
                     f"{_e(p0.get('root_cause'), 'نامعلوم')}")
    lines.append(f"▸ همگرا می‌شوم؟ {'آری' if tr.get('converging') else 'هنوز نه'}"
                 f" · {c.get('چرخهٔ_پایدار') or 0} چرخهٔ پایدار")
    n = len(corrections())
    lines.append(f"▸ {n} تصحیحِ تو را نگه داشته‌ام" if n
                 else "▸ هنوز تصحیحی از تو ثبت نشده")
    return "\n".join(lines)


def corrections_card() -> str:
    c = corrections(8)
    if not c:
        return ("✍️ <b>هنوز تصحیحی ثبت نشده</b>\n"
                "▸ هر وقت چیزی دربارهٔ خودم غلط گفتم، همان‌جا بنویس «نه، …»\n"
                "▸ نکنی: همان اشتباه در فهمم از خودم می‌ماند")
    import html as _h
    return "✍️ <b>تصحیح‌های تو</b>\n" + "\n".join(
        f"▸ {_h.escape(t)[:160]}" for t in c)


if __name__ == "__main__":   # pragma: no cover
    print(json.dumps({"flag": enabled(), "all_rooms": all_rooms_enabled(),
                      "turns": len(recent_turns()),
                      "corrections": len(corrections())}, ensure_ascii=False, indent=1))
    print(); print(know_card())
