"""surface_router — مقصدِ ارسالِ هر جریانِ تلگرام را برایِ مرکز انتخاب می‌کند.

طرحِ دو-باتیِ TG-SPLIT (۲۰۲۶-۰۷-۲۹): هسته میانِ دو بات تقسیم می‌شود —
  · inner = @Robo2725_bot (`TELEGRAM_BOT_TOKEN`) — درونِ ارگانیسم: سلامت/هشدار/دایجست
  · outer = @intergrade2725_Bot (`TG_CENTER_BOT_TOKEN`) — رابطِ شخصیِ مالک

این ماژول **هیچ‌چیز نمی‌فرستد**. فقط می‌گوید یک جریانِ داده باید با کدام کلاینت،
در کدام chat و کدام topic (اگر گروه است) فرستاده شود. منبعِ حقیقت = فایلِ مالک
`surface-routing.json` که برایِ هر جریان دو بلوک دارد: `current` (واقعیتِ امروز) و
`target` (مقصدِ مصوب).

قاعدهٔ سختِ TG-SPLIT شمارهٔ ۲: **هیچ pollerِ نو ساخته نمی‌شود.** این ماژول هرگز
`getUpdates` صدا نمی‌زند — `sendMessage` آپدیت مصرف نمی‌کند و روی توکنِ inner
امن است. کلاینتِ inner فقط فرستنده است (send-only).

⚠️ آشتی با `surface_policy`: یک لایهٔ روتینگِ موازی هم هست (`surface_policy.route`،
پشتِ `OCTOPUS_TG_SURFACE_V2`) که در پروسهٔ organism/approval_channel کار می‌کند و
سه سطلِ GROUP/DM/HOLD دارد. این دو هم‌پوشانی ندارند — `surface_policy` روی فلگِ
جدا و در دنیایِ دیگری است. تقدم روی فلگ‌های خودشان است؛ این ماژول فقط دنیایِ
مرکز (outer/دنیای A) را می‌بیند.

flag-off = رفتارِ امروز بایت‌به‌بایت: ارسالِ تک-کلاینتِ outer، `chat_id` از config،
`topic_id` فقط وقتی گروه است. هر تغییری در این مسیر فقط پشتِ فلگِ روشن می‌آید.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
if str(_HERE.parent) not in sys.path:
    sys.path.insert(0, str(_HERE.parent))

FLAG = "OCTOPUS_TG_SPLIT_V1"

# نقشهٔ پیش‌فرض جریان ← کلیدِ تاپیک (وقتی stream پا یا عضو است). فقط برایِ سقوطِ
# fail-soft وقتی فایلِ surface-routing.json غایب/خراب است؛ در حالتِ عادی خودِ فایل
#منبعِ حقیقت است. هم‌خوان با LEG_KEYS/DEFAULT_DISPLAY در center.py.
_TOPIC_KEY = {
    "lead": "lead", "ziman": "ziman", "mining": "mining",
    "crypto": "crypto", "accounting": "accounting", "studio_pf": "studio_pf",
    "system": "system", "knowledge": "knowledge", "cartographer": "cartographer",
}


def enabled() -> bool:
    """فلگِ split روشن است؟ پیش‌فرض خاموش = رفتارِ امروز دست‌نخورده."""
    return str(os.environ.get(FLAG, "") or "").strip().lower() in (
        "1", "true", "yes", "on")


def _routing_path() -> Path:
    return _HERE / "surface-routing.json"


def _load_streams() -> dict:
    """نقشهٔ جریان‌ها از surface-routing.json. غایب/خراب → {} (fail-soft).

    محتوای فایل مالِ مالک است و دستکاری می‌شود؛ این تابع فقط می‌خواند و هر خرابی
    را بی‌صدا تحمل می‌کند تا مسیرِ زندهٔ ارسال هرگز از یک فایلِ JSONِ بد نخوابد."""
    try:
        p = _routing_path()
        if not p.exists():
            return {}
        data = json.loads(p.read_text("utf-8"))
        streams = data.get("streams") if isinstance(data, dict) else None
        return streams if isinstance(streams, dict) else {}
    except (OSError, ValueError):
        return {}


def _select_block(entry: dict) -> dict:
    """بلوکِ `current` (فلگِ خاموش) یا `target` (روشن). نبودِ بلوک → {}.

    این جایی است که واقعیتِ امروز (`current`) با مقصدِ مصوب (`target`) جدا
    می‌شود — هر مهاجرتِ جریان فقط با اضافه‌کردنِ یک مدخل در فایلِ مالک انجام
    می‌شود، نه با تغییرِ کد."""
    if not isinstance(entry, dict):
        return {}
    block_name = "target" if enabled() else "current"
    block = entry.get(block_name)
    return block if isinstance(block, dict) else {}


def _topic_id_for(stream: str, block: dict, cfg: dict) -> int | None:
    """topic_idِ مقصد — فقط برایِ سطحِ group. برایِ dm همیشه None.

    `surface==dm` ⇒ هرگز تاپیک: فرستادنِ message_thread_id به چتِ خصوصی = ۴۰۰
    Bad Request (آیتم ۳ِ TG-P2). `topic=="per-leg"` ⇒ topicِ خودِ آن جریان/پا از
    config. در غیر این صورت topic از کلیدِ شناخته‌شده. هر ابهام → None (نه خطا)."""
    surface = str(block.get("surface") or "").strip().lower()
    if surface != "group":
        return None                                    # dm / none / ناشناخته → بدونِ topic
    topics = cfg.get("topics") if isinstance(cfg, dict) else None
    if not isinstance(topics, dict):
        return None
    spec = block.get("topic")
    if spec == "per-leg":
        # اول کلیدِ خودِ جریان (مثلِ "legs-all" یا نامِ پا)؛ وگرنه نگاشتِ شناخته‌شده.
        s = str(stream or "").strip().lower()
        key = s if s in topics else _TOPIC_KEY.get(s)
    else:
        key = str(spec or stream or "").strip().lower()
        key = key if key in topics else _TOPIC_KEY.get(key)
    if not key:
        return None
    tid = topics.get(key)
    return int(tid) if isinstance(tid, int) else None


def _chat_for(block: dict, client, cfg: dict):
    """chat_idِ مقصد: group = center (سوپرگروه)، dm = owner (چتِ خصوصی).

    هر دو از خودِ کلاینت خوانده می‌شوند (نه از env خام) تا containment حفظ شود و
    هیچ chat_id در این ماژول لاگ/ذخیره نشود. ابهام → center (امن‌ترین: گروه)."""
    surface = str(block.get("surface") or "").strip().lower()
    if surface == "dm":
        owner = getattr(client, "owner_chat_id", None)
        return owner
    cid = cfg.get("chat_id") if isinstance(cfg, dict) else None
    if cid is not None:
        return cid
    return getattr(client, "center_chat_id", None)


def resolve(stream, *, clients: dict, cfg: dict) -> tuple:
    """(client, chat_id, topic_id) برایِ یک جریان.

    · `clients` = ``{"inner": TgClient, "outer": TgClient}`` — کلاینت‌هایی که مرکز
      ساخته و نگه می‌دارد. کلاینتِ inner فقط-ارسال است (هرگز poll).
    · `cfg` = center-config (برایِ `chat_id` گروه و `topics`).

    flag-off → `current` از فایل: ارسالِ تک-کلاینتِ outer، رفتارِ امروز بایت‌به‌بایت.
    flag-on → `target`: جریان‌های منتقل‌شده به inner/dm می‌روند.

    هر شکست (فایلِ نبود/خراب، کلاینتِ غایب، جریانِ ناشناس) → `(outer, chat_id_امروز,
    None)`، **نه سکوت** — پیامِ گم‌شده بدتر از پیامِ در جایِ اشتباه است. اگر کلاینتِ
    inner غایب باشد (توکنِ inner نیست) و جریان به inner برود، به outer سقوط می‌کند
    + یک هشدار، تا ارسال نایافتی نباشد.
    """
    outer = clients.get("outer")
    inner = clients.get("inner")
    streams = _load_streams()
    entry = streams.get(str(stream or "").strip()) if isinstance(streams, dict) else None
    block = _select_block(entry if isinstance(entry, dict) else {})

    bot = str(block.get("bot") or "").strip().lower()
    # انتخابِ کلاینت: inner فقط وقتی واقعاً هست و وصل است؛ وگرنه سقوط به outer.
    if bot == "inner" and inner is not None and _wired(inner):
        client = inner
    elif bot == "none":
        return (None, None, None)                     # جریانِ عمداً خاموش (مثل intuition)
    else:
        client = outer                                # outer یا سقوط
    if client is None:
        client = outer

    chat_id = _chat_for(block, client, cfg)
    topic_id = _topic_id_for(str(stream or ""), block, cfg or {})
    return (client, chat_id, topic_id)


def _wired(client) -> bool:
    """client.wired() — fail-soft: هر خطا/نبود → False."""
    try:
        return bool(client is not None and client.wired())
    except Exception:  # noqa: BLE001
        return False
