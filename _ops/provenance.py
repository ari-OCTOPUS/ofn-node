"""provenance.py — تنها تعریفِ «عددِ تمبرخورده» در اختاپوس.

چرا این فایل وجود دارد (۲۰۲۶-۰۸-۰۳، گامِ ۱ ِ UNIFICATION-DESIGN):

    هر عددی که این ارگانیسم منتشر می‌کند یک اسکالرِ برهنه است. نتیجه‌اش این
    است که پنج چیزِ کاملاً متفاوت **یک‌شکل رندر می‌شوند**:

      · یک ثابتِ منجمد   — `_octopus/state/octopus_state.json::self_awareness`
                            "green"، ۱۶ روز بی‌تغییر، صفر نویسنده، صفر خواننده
      · یک اسنپ‌شاتِ نگه‌داشته‌شده — `control_law` که ۶۰.۰ می‌دهد و هر ۵ بیت
                            یک‌بار **نوشته** و هر تیک **خوانده** می‌شود
      · یک mtime ِ آرتیفکتِ merge — ۶ فایل از ۲۰ فایلِ `_ops/state/pulse/`
                            تا ۶.۶ ساعت جلوتر از `ts` درونی‌شان
      · یک اسکنِ بریده‌شده — `scan_metadata(max_files=50_000)` که دقیقاً
                            ۵۰٬۰۰۰ برمی‌گرداند
      · و یک اندازه‌گیریِ واقعی

    این ماژول همان تفاوت را به **نوع** تبدیل می‌کند: هر عدد با منبع، ریتم،
    آخرین تغییرِ واقعی، درجهٔ آزادی و حالتش سفر می‌کند.

قواعدِ حالت (به همین ترتیبِ تقدم):

    UNKNOWN   منبع یا observed_ts غایب است، یا observed_ts فقط یک mtime است
    HELD      age_s > 2 × cadence_s  — ظرف تازه نشده، مقدار نگه داشته شده
    CONSTANT  dof == 1 روی پنجره‌ای که ≥ ۳ × cadence_s را می‌پوشاند
    LIVE      هیچ‌کدام

ناوردی‌های عمدی:

    ۱. **این ماژول هیچ مسیری نمی‌خواند و هیچ‌چیز نمی‌نویسد.** توابعِ خالص روی
       مقادیری که caller قبلاً بارگذاری کرده. نه ثابتِ مسیر دارد نه persistence،
       پس نمی‌تواند با هیچ ظرفی مخالفت کند — فقط می‌تواند یکی را توصیف کند.

    ۲. **UNKNOWN کلیدِ `value` ندارد.** عمدی است: یک ورودیِ غایب نباید به صفرِ
       بی‌صدا تبدیل شود. `value_of()` روی UNKNOWN استثنا می‌دهد تا خطا در
       صداکننده بلند باشد، نه یک صفر که تا کارتِ مالک سفر کند.

    ۳. **mtime به‌عنوان observed_ts رد می‌شود.** `Mtime` را دور مقدار بپیچید و
       نتیجه `UNKNOWN/reason='mtime-only'` می‌شود. علتِ سنجیده‌شده: ۱۴ از ۲۰
       فایلِ `_ops/state/pulse/` گیت‌tracked اند و mtime شان آرتیفکتِ merge است.

    ۴. **`ts` ِ سطحِ بالای `ORGANISM-STATE.json` تازگیِ یک کلید را اثبات نمی‌کند.**
       مسیرِ `merge_prev` در `organism.py::_write_state` در مسیرِ خطا/STOP هر
       کلیدِ غایب را از حالتِ قبلی back-fill می‌کند و هم‌زمان `ts` سطحِ بالا را
       جلو می‌برد. پس `observed_ts` باید **داخلِ خودِ مقدار** باشد؛ برای همین
       `observed_in()` وجود دارد.

    ۵. **ساعت کاملاً تزریق‌پذیر است.** هیچ شاخه‌ای `time.time()` را مستقیم
       نمی‌خواند وقتی `now` داده شده — درسِ «ساعتِ نیمه‌تزریقی».
"""
from __future__ import annotations

import time
from datetime import datetime, timezone

__all__ = [
    "Mode", "Mtime", "stamp", "value_of", "is_trustworthy",
    "observed_in", "parse_ts",
]


class Mode:
    """حالت‌های ممکنِ یک عددِ تمبرخورده. رشته‌اند تا مستقیم JSON شوند."""

    LIVE = "LIVE"
    HELD = "HELD"
    CONSTANT = "CONSTANT"
    UNKNOWN = "UNKNOWN"

    ALL = (LIVE, HELD, CONSTANT, UNKNOWN)
    #: حالت‌هایی که می‌شود رویشان تصمیم گرفت. HELD عمداً اینجا نیست.
    TRUSTWORTHY = (LIVE,)


class Mtime(float):
    """نشانگرِ «این timestamp از فایل‌سیستم آمده، نه از داخلِ خودِ داده».

    `stamp()` این را همیشه رد می‌کند. وجودش برای این است که مسیرِ صادقانه
    آسان باشد: اگر فقط mtime داری، `Mtime(os.path.getmtime(p))` بده و
    نتیجه صادقانه UNKNOWN می‌شود — به‌جای اینکه یک آرتیفکتِ merge را
    به‌عنوان تازگی گزارش کنی.
    """

    __slots__ = ()


def parse_ts(value):
    """ISO-8601 یا epoch را به epoch-float تبدیل می‌کند. ناموفق ⇒ None.

    هر دو شکل در این ارگانیسم زنده‌اند: `heart-signals`/`heart-shadow`/
    `heartstate` رشتهٔ ISO می‌دهند، `heart-card-state`/`work-state` اپاکِ float.
    """
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if not isinstance(value, str):
        return None
    text = value.strip()
    if not text:
        return None
    try:
        return float(text)
    except ValueError:
        pass
    try:
        # `fromisoformat` در ۳.۱۱+ پسوندِ Z را می‌گیرد؛ برای نسخهٔ قدیمی‌تر دستی.
        if text.endswith("Z"):
            text = text[:-1] + "+00:00"
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.timestamp()


def observed_in(payload, *keys):
    """`observed_ts` را از **داخلِ خودِ مقدار** بیرون می‌کشد (ناوردیِ ۴).

    هیچ‌وقت به `ts` ِ سطحِ بالای سندِ دربرگیرنده تکیه نکن؛ آن یکی را
    `merge_prev` حتی وقتی این کلید به‌روز نشده جلو می‌برد.
    """
    if not isinstance(payload, dict):
        return None
    for key in (keys or ("ts", "observed_ts", "updated_ts", "timestamp")):
        if key in payload:
            got = parse_ts(payload[key])
            if got is not None:
                return got
    return None


def _distinct(values):
    """شمارِ مقادیرِ متمایز، با تحملِ خطای شناور."""
    seen = []
    for raw in values:
        try:
            item = float(raw)
        except (TypeError, ValueError):
            item = raw
        if isinstance(item, float):
            if not any(isinstance(s, float) and abs(s - item) <= 1e-9 for s in seen):
                seen.append(item)
        elif item not in seen:
            seen.append(item)
    return len(seen)


def _history_window(history, cadence_s):
    """طولِ زمانیِ پنجرهٔ history بر حسبِ ثانیه، و فهرستِ مقادیرش.

    دو شکل پذیرفته می‌شود: دنبالهٔ مقادیر (پنجره از len × cadence تخمین زده
    می‌شود) یا دنبالهٔ جفتِ (ts, value) که پنجرهٔ واقعی را می‌دهد.
    """
    if not history:
        return 0.0, []
    items = list(history)
    pairs = all(isinstance(x, (tuple, list)) and len(x) == 2 for x in items)
    if pairs:
        stamps = [parse_ts(x[0]) for x in items]
        stamps = [s for s in stamps if s is not None]
        values = [x[1] for x in items]
        span = (max(stamps) - min(stamps)) if len(stamps) >= 2 else 0.0
        return float(span), values
    span = max(0, len(items) - 1) * float(cadence_s or 0.0)
    return float(span), items


def stamp(value, source, observed_ts, cadence_s, history=None, writer="", now=None):
    """یک عدد را به یک عددِ تمبرخورده تبدیل می‌کند.

    برمی‌گرداند dict با کلیدهای:
        value (فقط اگر UNKNOWN نباشد) / source / observed_ts / age_s /
        cadence_s / last_change_ts / dof / mode / writer  [+ reason روی UNKNOWN]
    """
    now_s = float(now) if now is not None else time.time()
    cadence = float(cadence_s or 0.0)

    def unknown(reason):
        # عمداً بدونِ کلیدِ `value` — ناوردیِ ۲.
        return {
            "source": source,
            "observed_ts": None,
            "age_s": None,
            "cadence_s": cadence,
            "last_change_ts": None,
            "dof": 0,
            "mode": Mode.UNKNOWN,
            "writer": writer,
            "reason": reason,
        }

    if isinstance(observed_ts, Mtime):
        return unknown("mtime-only")
    if not source:
        return unknown("no-source")
    if value is None:
        return unknown("no-value")

    ts = parse_ts(observed_ts)
    if ts is None:
        return unknown("no-observed-ts")

    age = now_s - ts
    span, values = _history_window(history, cadence)
    dof = _distinct(values) if values else 1

    last_change = ts
    if values and dof > 1:
        # آخرین نقطه‌ای که مقدار عوض شد؛ اگر جفت‌دار باشد ts واقعی، وگرنه None.
        items = list(history)
        if all(isinstance(x, (tuple, list)) and len(x) == 2 for x in items):
            prev = None
            for raw_ts, raw_val in items:
                if prev is not None and raw_val != prev:
                    got = parse_ts(raw_ts)
                    if got is not None:
                        last_change = got
                prev = raw_val

    if cadence > 0 and age > 2 * cadence:
        mode = Mode.HELD
    elif dof == 1 and values and cadence > 0 and span >= 3 * cadence:
        mode = Mode.CONSTANT
    else:
        mode = Mode.LIVE

    return {
        "value": value,
        "source": source,
        "observed_ts": ts,
        "age_s": round(age, 3),
        "cadence_s": cadence,
        "last_change_ts": last_change,
        "dof": dof,
        "mode": mode,
        "writer": writer,
    }


def value_of(stamped):
    """مقدار را می‌دهد، یا روی UNKNOWN استثنا می‌دهد (ناوردیِ ۲).

    عمداً استثنا و نه پیش‌فرض: یک ورودیِ غایب باید صداکننده را بشکند، نه
    اینکه به صفری تبدیل شود که تا کارتِ مالک سفر می‌کند.
    """
    if not isinstance(stamped, dict):
        raise TypeError(f"not a stamp: {type(stamped).__name__}")
    if stamped.get("mode") == Mode.UNKNOWN or "value" not in stamped:
        raise KeyError(
            "stamp is UNKNOWN (reason=%s); it carries no value" % stamped.get("reason")
        )
    return stamped["value"]


def is_trustworthy(stamped):
    """آیا می‌شود روی این عدد تصمیم گرفت؟ فقط LIVE."""
    return isinstance(stamped, dict) and stamped.get("mode") in Mode.TRUSTWORTHY
