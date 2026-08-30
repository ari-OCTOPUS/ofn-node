"""leg_room_report — به پاها در گروه صدا بده، ولی فقط وقتی حرفی دارند.

رأیِ مالک ۲۰۲۶-۰۷-۲۸: «گروه و پاها همه‌رو اتصالات رو کدنویسی کن پروژه‌هارو».

اندازه‌گیری‌ای که این ماژول را ساخت
──────────────────────────────────
گروه ۱۰ تاپیک دارد و ۷ تایشان از روزِ ساختشان **یک پیام** هم نگرفته‌اند. علت
آن چیزی نبود که به‌نظر می‌رسید. `surface_policy.LEG_TOPIC` شش جریانِ پا را به
اتاق‌هایشان نگاشت می‌کند و آن نگاشت **درست** است — ولی وقتی نامِ جریان‌هایی را
شمردم که تا امروز واقعاً فرستاده شده‌اند، هشت‌تا بود:

    center · needs · discovery · brain · doctor · heart · cortisol · (بی‌نام)

و ارگانیسم در کلِ `wiring.py` دقیقاً پنج جریان تولید می‌کند: needs، discovery،
doctor، brain، heart. **صفر جریانِ پا.** یعنی لایهٔ نگاشت کامل بود و لایهٔ
تولید اصلاً وجود نداشت؛ اتاق‌های پاها ساختاراً محکوم به خالی‌ماندن بودند.

چرا این ماژول محتوا اختراع نمی‌کند
─────────────────────────────────
هر پا از قبل یک سلولِ واقعی در read-model دارد (`business_legs`): `live`،
`signal`، `note`، `age_days`، و برای پاهای زنده چیزهای بیشتر. این داده ساخته
می‌شود و امروز فقط در کارتِ جمعیِ `/organs` دیده می‌شود — یعنی مالک باید
بپرسد تا بداند. این‌جا همان دادهٔ موجود به اتاقِ خودش می‌رود؛ هیچ متنِ تازه‌ای
تولید نمی‌شود.

چرا «تغییر»، نه «دوره‌ای»
────────────────────────
مالک همان هفته گفت «فقط وقتی واقعاً به من نیاز داری حرف بزن». گزارشِ دوره‌ای
همان چیزی است که گروه را به لولهٔ سروصدا تبدیل کرد (۶۲٪ از ۱۷۶ ارسالِ دو روز در
General افتاده بود). پس ماشه **تغییرِ سیگنال** است، نه گذشتِ زمان.

⚠️ و شمارنده در کلیدِ dedup نمی‌آید. همان روز سه بار این باگ را دیدم: `age_days`
هر روز عوض می‌شود، پس اگر واردِ هش شود هر پا هر روز یک‌بار حرف می‌زند و ما
اسمش را می‌گذاریم «تغییر». تغییرِ **وضعیت** با گذشتِ **زمان** یکی نیست.

مرزها
─────
· فلگ `OCTOPUS_WIRE_LEG_ROOMS` پیش‌فرض خاموش؛ خاموش = هیچ ارسالی، بایت‌به‌بایت.
· پایی که سلول ندارد ساکت می‌ماند — کارتِ «داده‌ای نیست» خودش سروصداست.
· حالت روی دیسک است نه در حافظه: بوتِ تازه نباید همهٔ پاها را با هم شلیک کند
  (همان رگبارِ کادنس که ۰۷-۲۸ در ۱۸ جا فیکس شد).
· هیچ‌چیز اجرا نمی‌شود؛ فقط متن. صفر effector، صفر پول.
· ونچر (`studio`) محتوا-آزاد است: این ماژول هرگز به پوشهٔ آن نگاه نمی‌کند و
  فقط سلولِ read-model را می‌خواند مثلِ بقیه.
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

FLAG = "OCTOPUS_WIRE_LEG_ROOMS"
STATE = opslib.STATE_DIR / "leg-room-report.json"

# فاصلهٔ کفِ هر پا. حتی اگر سیگنال بلرزد، بیش از این حرف نمی‌زند.
MIN_HOURS = 6.0

# برچسبِ نمایشیِ هر پا. کلید = همان کلیدِ سلولِ read-model و نامِ جریان.
#
# ⚠️ منبعِ حقیقت `chat_room.LEGS` است، نه این جدول. ۲۰۲۶-۰۷-۲۸ مالک نامِ واقعیِ
# اتاق‌های گروه را داد («مغز دانش‌نامه، قلب سیستم، چشم نقشه‌بردار») و نام‌های
# `chat_room` هم‌تراز شد — ولی این فایل جا ماند و کارت‌هایش هنوز «⛏ Mining»
# می‌گفتند در حالی که اتاق «بازوی معدن» بود. دو جدول برای یک نام یعنی یکی‌شان
# همیشه کهنه است؛ آزمونِ زنده همان لحظه نشانش داد.
#
# `_FALLBACK` فقط برای وقتی است که ماژول واقعاً نباشد — و کلیدهایش عمداً همان
# هفت‌تاست تا `test_leg_rooms` بتواند هم‌ارزی را بسنجد.
_FALLBACK = {
    "lead": "🎨 بازوی رنگ", "ziman": "🖼 بازوی گالری", "mining": "⛏ بازوی معدن",
    "crypto": "🪙 بازوی سکه", "accounting": "📒 بازوی دفتر",
    "knowledge": "🧠 مغز", "cartographer": "👁 چشم",
}


def _labels() -> dict:
    """نام‌ها از `chat_room` — همان‌هایی که مالک در گروه می‌بیند.

    مسیر صریح insert می‌شود چون `chat_room` در `telegram_center` است و این
    ماژول در `legs`؛ importِ لخت فقط از یک پروسه resolve می‌شد. همان باگی که
    امروز در `approval_channel` پیدا شد و نصفِ سیستم را بی‌صدا دوپاره کرده بود.
    """
    try:
        import sys as _s
        _tgc = str(_HERE.parent / "telegram_center")
        if _tgc not in _s.path:
            _s.path.insert(0, _tgc)
        import chat_room as _cr
        got = {k: v[0] for k, v in _cr.LEGS.items() if v and v[0]}
        return got or dict(_FALLBACK)
    except Exception:  # noqa: BLE001 — نام هرگز گزارش را نمی‌کشد
        return dict(_FALLBACK)


LABEL = _labels()


def enabled() -> bool:
    return str(os.environ.get(FLAG, "") or "").strip().lower() in (
        "1", "true", "yes", "on")


def _load() -> dict:
    try:
        return json.loads(STATE.read_text("utf-8"))
    except (OSError, ValueError):
        return {}


def _save(d: dict) -> None:
    try:
        STATE.parent.mkdir(parents=True, exist_ok=True)
        STATE.write_text(json.dumps(d, ensure_ascii=False), "utf-8")
    except OSError:
        pass                       # حالت گم شود بدتر از سکوت نیست؛ کرش هست


def signal_hash(cell: dict) -> str:
    """اثرانگشتِ **وضعیت**، نه گذرِ زمان.

    عمداً بیرون: `age_days` و هر شمارندهٔ یکنواخت. اگر واردش کنی، هر پا هر روز
    یک‌بار «تغییر» می‌کند و گارد صفر اثر دارد — دقیقاً باگی که ۰۷-۲۸ سه بار در
    سه جای مختلف پیدا شد و بعد از حذفِ شمارنده نرخِ حرف‌زدن ۱.۴۰ → ۰.۱۵ در
    دقیقه شد.
    """
    if not isinstance(cell, dict):
        return ""
    keep = {k: cell.get(k) for k in ("live", "signal", "note", "status")
            if cell.get(k) is not None}
    # پاهای زنده فیلدهای عددیِ معنادار دارند؛ گرد می‌شوند تا نوسانِ اعشاری
    # «تغییر» شمرده نشود.
    for k in ("confirmed_revenue_aud", "inbox", "artifacts"):
        v = cell.get(k)
        if isinstance(v, (int, float)):
            keep[k] = round(float(v), 2)
        elif isinstance(v, (list, dict)):
            keep[k] = len(v)
    if not keep:
        return ""
    blob = json.dumps(keep, ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()[:16]


def card(leg: str, cell: dict) -> str:
    """کارتِ یک پا — کوتاه، چون در اتاقِ خودش است و بافت لازم ندارد."""
    label = LABEL.get(leg, leg)
    live = "🟢 زنده" if cell.get("live") else "⚪ اسکلت"
    lines = [f"{label} · {live}"]
    sig = str(cell.get("signal") or cell.get("note") or "").strip()
    if sig:
        lines.append(sig[:200])
    rev = cell.get("confirmed_revenue_aud")
    if isinstance(rev, (int, float)):
        lines.append(f"درآمدِ تأییدشده: AU${float(rev):.2f}")
    for k, fa in (("inbox", "صندوق"), ("artifacts", "سند")):
        v = cell.get(k)
        if isinstance(v, (list, dict)) and len(v):
            lines.append(f"{fa}: {len(v)}")
    age = cell.get("age_days")
    if isinstance(age, (int, float)) and age >= 1:
        lines.append(f"<i>آخرین دادهٔ تازه: {int(age)} روز پیش</i>")
    return "\n".join(lines)


def due(legs: dict, *, now: float | None = None) -> list:
    """کدام پاها الان حرفِ تازه دارند؟ خروجی: [(leg, متنِ کارت, هش), …]

    `now` تزریق‌شدنی است — و **همهٔ** شاخه‌ها از همین می‌خوانند. ساعتِ
    نیمه‌تزریقی (تابعی که `now` می‌گیرد ولی یک شاخه‌اش `time.time()` صدا
    می‌زند) روزها سبز و شب‌ها قرمز می‌شود؛ ۰۷-۲۸ یکی‌شان پیدا شد و هیچ اسکنی
    نگرفته بودش — گذشتِ زمان گرفتش.
    """
    if not enabled() or not isinstance(legs, dict):
        return []
    t = time.time() if now is None else float(now)
    st = _load()
    out = []
    for leg, cell in sorted(legs.items()):
        if leg not in LABEL or not isinstance(cell, dict):
            continue                      # پای ناشناخته یا سلولِ بدقواره
        h = signal_hash(cell)
        if not h:
            continue                      # داده‌ای نیست → ساکت، نه کارتِ خالی
        prev = st.get(leg) or {}
        if prev.get("hash") == h:
            continue                      # وضعیت عوض نشده
        last = float(prev.get("ts") or 0)
        if last and (t - last) < MIN_HOURS * 3600.0:
            continue                      # لرزشِ سیگنال اتاق را غرق نکند
        out.append((leg, card(leg, cell), h))
    return out


def mark(sent: list, *, now: float | None = None) -> None:
    """ثبتِ آنچه **واقعاً** فرستاده شد.

    جدا از `due` عمدی است: اگر ارسال شکست بخورد، هیچ‌چیز mark نمی‌شود و دفعهٔ
    بعد دوباره تلاش می‌شود. علامت‌زدنِ قصد به‌جای اثر همان «انجام شد فلگ نیست،
    اثر است» است که این هفته سه بار به آن خوردیم.
    """
    if not sent:
        return
    t = time.time() if now is None else float(now)
    st = _load()
    for leg, h in sent:
        st[leg] = {"hash": h, "ts": t}
    _save(st)


def card_status() -> str:
    """کارتِ `/organs` را کامل می‌کند: چند پا صدا دارند و کِی حرف زدند."""
    st = _load()
    if not enabled():
        return (f"🔇 گزارشِ اتاقِ پاها خاموش است ({FLAG}).\n"
                f"▸ {len(LABEL)} پا تعریف شده، صفر ارسال.")
    spoke = len(st)
    return (f"🔊 گزارشِ اتاقِ پاها روشن · {spoke}/{len(LABEL)} پا تا حالا حرف زده\n"
            f"▸ ماشه = تغییرِ وضعیت، نه گذشتِ زمان · کفِ فاصله {MIN_HOURS:g} ساعت")
