#!/usr/bin/env python3
"""center.py — «مرکزِ فرماندهیِ تلگرام» (hub): حلقهٔ setup/beat/poll روی TgClient.

نقش (قراردادِ telegram_center):
  * ensure_setup() — idempotent: تاپیکِ هر ۸ پا، منوی commandها، و پیامِ statusِ
    پین‌شده «فقط یک‌بار» ساخته می‌شوند؛ حافظه = فایلِ config (state/telegram/center-config.json).
  * beat() — statusِ پین‌شده را edit می‌کند (هرگز دوباره send نمی‌کند)، دایجستِ هر پا را
    طبقِ cadence (پیش‌فرض ۲۴h، قابلِ override در config) پست می‌کند، و تصمیم‌های نوی
    جعبهٔ راهنمایی را با کیبورد می‌فرستد (dedupe با seen-ids در config).
  * handle_update(u) — فقط مالک (allowlist): /now → ارسالِ status؛ callbackهای
    ok/no/later → ثبتِ verdict به الگوی approval-file + events.emit (اگر import شود)
    + answer_callback. ok اگر رازِ HH_HUMAN_GUARD_SECRET در env باشد یک توکنِ
    HumanAppendGuard هم mint می‌کند؛ بی‌راز = ثبتِ بدونِ توکن، هرگز crash.
  * run_once() — یک دورِ poll + dispatch (offset در config، restart-safe).
  * توقف (رفعِ G-no-master-halt، 2026-07-13؛ restart-aware WP3، owner decision #25):
    حلقهٔ run با هر یک از این‌ها می‌ایستد — `HALT-ALL` یا `STOP(architect)` (مرزِ سختِ
    سراسریِ opslib.master_halted؛ هیچ‌کس نادیده نمی‌گیرد) یا `STOP-TG-CENTER` (scoped ِ خودِ
    این کانکتور). `STOP-ORGANISM` هم می‌ایستاند مگر هم‌راهش `RESTART-REQUESTED` باشد — که
    یعنی ری‌استارتِ روتینِ داشبورد و tg-center باید تا relaunch جان به‌در ببرد.

ناوردی‌ها: $0/stdlib-only · flag-off (بدونِ token/چت = هر متدِ عمومی no-opِ امن با
خروجیِ پیش‌فرض) · import-time خالص (نه شبکه، نه نوشتن) · fail-soft همه‌جا (هر خطا →
پیش‌فرضِ امن، هرگز crashِ صداکننده، یک تلاش در هر فراخوان — بدونِ retry-storm) ·
containment: کلیدهای پا content-free اند؛ نامِ نمایشی از configِ مالک می‌آید
(پیش‌فرضِ پای pf = «استودیو»)؛ لایهٔ دومِ scrub با _BANNED_ECHO (parity با
registry_scan/events). تنها میزبانِ راهِ دور = api.telegram.org و آن هم فقط داخلِ
TgClient و فقط با tokenِ پیکربندی‌شده — این ماژول خودش هیچ HTTPی نمی‌زند.

تست: `_ops/tests/test_tg_center.py` (client/render/clockِ تزریقی — صفر شبکه).
"""
from __future__ import annotations

import json
import os
import re
import sys
import time
from pathlib import Path

# ── bootstrap مسیر (idiomِ codebase: opslib از _ops/budget) ────────────────────
_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))
if str(_HERE.parent / "budget") not in sys.path:
    sys.path.insert(0, str(_HERE.parent / "budget"))
import opslib  # noqa: E402 — import خالص (فقط مسیرها/env)
# ماژول‌های فاز C/D/E (همگی در همین پکیج، stdlib-only، import-time خالص):
import intent as intent_mod        # noqa: E402 — طبقه‌بندِ نیتِ پیامِ آزاد
import metadata_scan as ms_mod     # noqa: E402 — نقشه‌برداریِ فقط‌خواندنیِ metadata
import approval_store as aps_mod   # noqa: E402 — پلِ صفِ تأیید اختاپوس
import callback_token as cbtok      # noqa: E402 — P3: توکنِ HMACِ callback (فلگ OCTOPUS_WIRE_CB_TOKEN)
import mission as mission_mod       # noqa: E402 — Mission Genome: intent→mission→approval
try:
    import mission_runner as runner_mod   # noqa: E402 — Runner v0: اجرای ایزولهٔ allowlisted (پشتِ فلگ)
except Exception:  # noqa: BLE001 — fail-soft: نبودِ runner نباید center را بشکند
    runner_mod = None  # type: ignore
try:
    import live_commands as live_cmd_mod  # noqa: E402 — /id /box /code /live (2026-07-25)
except Exception:  # noqa: BLE001
    live_cmd_mod = None  # type: ignore

# فایلِ توقفِ حلقه (هم‌خانوادهٔ STOP-ORGANISM/STOP-CORTEX؛ فقط مالک می‌سازد)
STOP_TG_CENTER = opslib.OPS / "STOP-TG-CENTER"

# نشانگرِ ری‌استارتِ داشبورد (dashboard/server.py می‌سازدش هم‌راهِ STOP-ORGANISM؛ RUN-ORGANISM.bat
# هر دو را پاک و با env نو دوباره بوت می‌کند). حضورش یعنی «STOP-ORGANISM موقتی است»، پس این
# کانکتور نباید در یک ری‌استارتِ روتین بمیرد (owner decision #25). مرزِ سختِ سراسری استثنا ندارد.
RESTART_REQUESTED = opslib.OPS / "RESTART-REQUESTED"
RESTART_FRESH_S = 900   # carve-outِ ری‌استارت فقط وقتی markerِ RESTART-REQUESTED «تازه» است
                        # مجاز است؛ markerِ کهنه نباید STOP-ORGANISMِ «ایستِ کامل» را نامحدود ماسک کند.


def _restart_pending() -> bool:
    """آیا یک ری‌استارتِ روتینِ تازه در جریان است؟ RESTART-REQUESTED فقط اگر وجود داشته
    باشد و mtimeاش تازه‌تر از RESTART_FRESH_S باشد معتبر است. در تردید/خطا → False
    (یعنی «ری‌استارتِ معتبر نیست» → STOP-ORGANISMِ کامل غالب می‌شود؛ fail-safe به‌سمتِ توقف)."""
    try:
        if not RESTART_REQUESTED.exists():
            return False
        return (time.time() - RESTART_REQUESTED.stat().st_mtime) <= RESTART_FRESH_S
    except OSError:
        return False

DEFAULT_DIGEST_S = 86400          # cadence پیش‌فرضِ دایجستِ هر پا: ۲۴ ساعت
SEEN_CAP = 200                    # سقفِ حافظهٔ dedupeِ تصمیم‌ها در config
POLL_TIMEOUT_S = 25               # long-poll ($0-idle، هم‌راستا با approval_channel)
# کارتِ زندهٔ پاها: یک پا در هر بازه. کمی زیرِ beat_every_s=300 تا jitter ِ حلقه
# یک نوبت را نپرانَد، و اندازه‌ای که ۱۰ پا در ~۵۰ دقیقه یک دور کامل بزنند.
LEG_CARD_EVERY_S = 240.0
# 2026-07-25 (build-spec §4): دایجستِ ادغام‌شده — یک پیام در topic=system به‌جایِ
# ۹ پیامِ جدا به ۹ تاپیک. پشتِ فلگ (پیش‌فرض خاموش) تا رفتارِ فعلی حفظ شود.
# وقتی روشن است، به‌جایِ حلقهٔ per-leg، همهٔ پاهایِ due در یک پیام جمع می‌شوند.
MERGED_DIGEST_FLAG = "OCTOPUS_TG_MERGED_DIGEST"
# 2026-07-26: جواب در همان تاپیکی بیفتد که مالک پرسیده (گروهِ مرکز فوروم است).
# پیش‌فرض خاموش = رفتارِ امروز؛ روشن = پاسخ به `message_thread_id`ِ همان پیام.
TOPIC_REPLY_FLAG = "OCTOPUS_TG_TOPIC_REPLY"

# containment (parity با registry_scan.scrub / events._scrub_str) — لایهٔ دوم؛
# لایهٔ اول render.scrub است. هیچ رشتهٔ ممنوع هرگز echo نمی‌شود.
_BANNED_ECHO = ("اونلی", "onlyfans", "صبا")

# کلیدهای ۸ پا — content-free (fallback وقتی render.LEGS در دسترس نیست)
LEG_KEYS = ("lead", "ziman", "mining", "crypto", "accounting",
            "studio_pf", "system", "knowledge", "cartographer")

# نامِ نمایشیِ پیش‌فرض — configِ مالک (display_names) همیشه برنده است.
# پای pf فقط با aliasِ سازمانیِ «استودیو» دیده می‌شود (containment).
DEFAULT_DISPLAY = {
    "lead": "Lead-نقاشی",
    "ziman": "Ziman Galerry",
    "mining": "Mining",
    "crypto": "Crypto-etoro",
    "accounting": "Accounting",
    "studio_pf": "استودیو",
    "system": "سیستم",
    "knowledge": "دانش",
}

# منوی command — فقط چیزی که این مرکز واقعاً handle می‌کند (قرارداد: /now)
COMMANDS: list[tuple[str, str]] = [
    ("menu", "🎛 منوی فرماندهی — همه‌چیز از اینجا"),
    ("now", "📊 وضعیت — همین حالا"),
    ("budget", "🐙 پیشنهادِ تخصیصِ ماهِ بعد (propose-only)"),
    ("revenue", "💰 درآمدِ تأییدشده (aggregate)"),
    ("missions", "🧬 مأموریت‌ها — Mission Genome"),
    # 2026-07-25 live path — identity / blackbox / collab / summary
    ("live", "🐙 خلاصهٔ زنده‌بودن (flags + هویت + جعبه‌سیاه)"),
    ("id", "🧬 مگا-معادلاتِ هویت (read-only)"),
    ("box", "📦 نقشهٔ جعبه‌سیاه‌ها"),
    ("code", "🧩 هم‌کدنویسی propose-only با مالک"),
    # ۲۰۲۶-۰۷-۲۷ — این فهرست ۹ تا بود در حالی که handlerها ۲۰ تا بودند. یعنی
    # نصفِ دستورها **کار می‌کردند ولی در منوی تلگرام دیده نمی‌شدند**: مالک باید
    # از قبل می‌دانست وجود دارند تا بتواند تایپشان کند. همان کژیِ کارت‌های
    # نامرئی، یک لایه بالاتر — و `test_command_discoverability` حالا قفلش می‌کند.
    ("x", "🗂 هر چیزی که می‌توانم نشانت بدهم"),
    ("stuck", "💰 پرداخت‌های نیمه‌کاره"),
    ("verdicts", "🗳 رأی‌هایی که دیگر سؤال نیستند"),
    ("lead", "🎨 قیمتِ یک کارِ نقاشی (تا مرزِ ارسال)"),
    ("deal", "🤝 پیشنهادِ خودم را بشنو"),
    ("doctrine", "📖 دکترینِ اپراتور"),
    ("eq", "🧬 معادلاتِ هویت"),
    ("funnel", "📈 قیفِ لید — چه می‌دانیم و چه نه"),
    ("won", "🎉 این لید را بردیم"),
    ("lost", "❌ این لید از دست رفت"),
    ("paid", "💰 پولِ این لید رسید (گزارش، نه تراکنش)"),
    ("sent", "📤 برای این لید پیام رفت"),
    ("replied", "💬 مشتری جواب داد"),
    ("meeting", "📅 قرارِ بازدید گذاشته شد"),
    ("quote", "🧾 قیمت برایش فرستاده شد"),
]

# منوی commandهای باتِ inner (@Robo2725، فقط-ارسال از دیدِ مرکز) — آیتم ۴ِ TG-P2.
# این بات درونِ ارگانیسم است (سلامت/هشدار/دایجست) و مرکز رویش فقط می‌فرستد،
# فرمان نمی‌گیرد (pollerش approval_channel است، در پروسهٔ جدا). پس منوی کوچک/خالی:
# فقط اطلاع‌رسانیِ «این باتِ درون است». flag-off → این پروفایل اصلاً ثبت نمی‌شود
# (کلاینتِ inner هم ساخته نمی‌شود) تا پاریتیِ تک-outerِ امروز بایت‌به‌بایت بماند.
COMMANDS_INNER: list[tuple[str, str]] = [
    ("status", "🐙 این باتِ درونِ ارگانیسم است — وضعیت را اینجا ببین"),
]

# دستورهایی که مرکز خودش پشتِ فلگ ثبت می‌کند — پل از آن‌ها رد می‌شود تا
# پاریتهٔ فلگ نشکنند. هر مدخل باید دلیلِ فلگ‌دار بودنش را داشته باشد.
_CENTRE_GATED = {"/panel": "OCTOPUS_WIRE_MENU_V2 — منوی v2",
                 "/mining": "OCTOPUS_WIRE_MINING_UI — منوی ⛏ زیر-OSِ Mining"}

_VERDICTS = ("ok", "no", "later")
_VERDICT_TOAST = {"ok": "تأیید شد ✅", "no": "رد شد ❌", "later": "بعداً ⏳"}
_VERDICT_APPROVAL_STATE = {"ok": "approved", "no": "denied", "later": "required"}


# ─── ابزارهای ماژول‌سطح (همه fail-soft، هیچ اثرِ import-time) ─────────────────────
def _fa_num(n) -> str:
    """عدد با رقمِ فارسی — عددِ لاتین وسطِ جملهٔ RTL جابه‌جا رندر می‌شود (bidi)."""
    return str(n).translate(str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹"))


def _scrub(s: object) -> str:
    """رشتهٔ حاویِ echo ِ ممنوع → کاملاً redact (parity با registry_scan.scrub)."""
    v = str(s if s is not None else "")
    low = v.lower()
    if any(b in low or b in v for b in _BANNED_ECHO):
        return "(redacted:containment)"
    return v


def _config_path() -> Path:
    return opslib.STATE_DIR / "telegram" / "center-config.json"


def _load_config() -> dict:
    """config = حافظهٔ idempotency. نبود/خرابی فایل → {} (fail-soft)."""
    try:
        p = _config_path()
        if not p.exists():
            return {}
        data = json.loads(p.read_text("utf-8"))
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


def _save_config(cfg: dict) -> bool:
    """نوشتنِ اتمیک (tmp + os.replace، idiomِ opslib.LockedJson.write). شکست → False."""
    try:
        p = _config_path()
        p.parent.mkdir(parents=True, exist_ok=True)
        tmp = p.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(cfg, ensure_ascii=False, indent=2), "utf-8")
        os.replace(tmp, p)
        return True
    except (OSError, TypeError, ValueError):
        return False


def _decision_id(item: dict) -> str:
    """شناسهٔ پایدارِ یک تصمیم برای dedupe/callback. اگر خودش id داشت همان؛ وگرنه
    هشِ محتوا (content-free در config — فقط hash ذخیره می‌شود، نه متن)."""
    did = str(item.get("id") or "").strip()
    if did:
        return re.sub(r"[^A-Za-z0-9_\-]", "-", did)[:64]
    import hashlib
    base = json.dumps([item.get("q", ""), item.get("source", "")], ensure_ascii=False)
    return hashlib.sha256(base.encode("utf-8")).hexdigest()[:16]


def _sanitize_id(raw: str) -> str:
    """idِ رسیده از callback data — هرگز خام واردِ نامِ فایل نمی‌شود (ضدِ path-traversal)."""
    return re.sub(r"[^A-Za-z0-9_\-]", "-", str(raw or ""))[:64] or "unknown"


def _mint_ha_token(approval_id: str, event_type: str = "APPROVAL") -> "str | None":
    """توکنِ human-append فقط اگر رازِ HH_HUMAN_GUARD_SECRET در env باشد (قراردادِ
    مرکز). بی‌راز/هر شکست → None (ثبتِ بدونِ توکن، هرگز crash). راز هرگز لاگ/ذخیره
    نمی‌شود — فقط خروجیِ HMAC (توکن) در رکورد می‌نشیند."""
    secret = str(os.environ.get("HH_HUMAN_GUARD_SECRET", "") or "").strip()
    if not secret:
        return None
    try:
        from human_append_guard import HumanAppendGuard
        g = HumanAppendGuard(secret.encode("utf-8"))
        return g.mint(str(approval_id).replace(".", "-"), event_type)
    except Exception:  # noqa: BLE001 — mint هرگز مسیرِ ثبت را نمی‌کشد
        return None


def _emit_event(event_name: str, **kw) -> None:
    """events.emit اگر import شود (fail-soft؛ نبودِ events = سکوتِ امن)."""
    try:
        if str(_HERE.parent) not in sys.path:
            sys.path.insert(0, str(_HERE.parent))
        import events
        events.emit(event_name, "tg-center", **kw)
    except Exception:  # noqa: BLE001
        pass


# ─── Center ──────────────────────────────────────────────────────────────────────
class Center:
    """حلقهٔ مرکز: client (TgClient یا fakeِ تست) + clockِ تزریقی + renderِ تزریقی.

    flag-off: اگر client نباشد یا client.wired() False باشد، هر متدِ عمومی no-opِ
    امن است (خروجیِ پیش‌فرض، صفر شبکه، صفر نوشتن)."""

    def __init__(self, client=None, clock=time.time, render_mod=None):
        self._clock = clock
        self._render = render_mod          # تزریقِ تست؛ None → importِ lazyِ render
        self._client = client if client is not None else self._default_client()

    # ── سیم‌کشیِ fail-soft ───────────────────────────────────────────────────────
    @staticmethod
    def _default_client():
        """TgClient از قرارداد (env-driven). نبودِ ماژول/خطا → None (no-opِ امن)."""
        try:
            import tg_api
            return tg_api.TgClient()
        except Exception:  # noqa: BLE001
            return None

    # ─ـ دو-باتیِ TG-P2 (آیتم ۲) ──────────────────────────────────────────────────
    # کلاینتِ outer = self._client (روی TG_CENTER_BOT_TOKEN، pollerِ اصلی مرکز).
    # کلاینتِ inner = فقط-ارسال روی TELEGRAM_BOT_TOKEN (همان باتی که approval_channel
    # در پروسهٔ organism رویش poll می‌کند). قاعدهٔ ۲ِ TG-SPLIT: هیچ pollerِ نو؛ این
    # کلاینت هرگز getUpdates صدا نمی‌زند — sendMessage آپدیت مصرف نمی‌کند و امن است.
    # نبودِ TELEGRAM_BOT_TOKEN → inner=None → surface_router به outer سقوط می‌کند + alert.
    def _inner_client(self):
        """کلاینتِ inner (فقط-ارسال). ساختهٔ lazy و fail-soft؛ None اگر توکنِ inner نباشد."""
        if getattr(self, "_inner", None) is not None:
            return self._inner
        try:
            import tg_api
            import os as _os
            inner_tok = (_os.environ.get("TELEGRAM_BOT_TOKEN") or "").strip()
            if not inner_tok:
                if not getattr(self, "_inner_missing_alerted", False):
                    self._inner_missing_alerted = True
                    try:
                        opslib.alert(["tg-center: TELEGRAM_BOT_TOKEN غایب — کلاینتِ "
                                      "inner ساخته نشد؛ جریان‌های inner به outer سقوط می‌کنند."])
                    except Exception:  # noqa: BLE001
                        pass
                self._inner = None
                return None
            # owner/center همان outer است: DMِ مالک و گروهِ مرکز با همان chat idها.
            owner = getattr(self._client, "_owner", None) if self._client else None
            center = getattr(self._client, "_center", None) if self._client else None
            self._inner = tg_api.TgClient(
                token=inner_tok, owner_chat_id=owner, center_chat_id=center,
                post_fn=getattr(self._client, "_post", None),
                get_fn=getattr(self._client, "_get", None))
            return self._inner
        except Exception:  # noqa: BLE001
            self._inner = None
            return None

    def _clients_map(self) -> dict:
        """``{"inner": TgClient|None, "outer": TgClient|None}`` برایِ surface_router."""
        return {"inner": self._inner_client(), "outer": self._client}

    def _rmod(self):
        """ماژولِ render (تزریقی یا lazy). نبود → None (بخش‌های وابسته skip می‌شوند)."""
        if self._render is not None:
            return self._render
        try:
            import render as _r
            self._render = _r
        except Exception:  # noqa: BLE001
            return None
        return self._render

    def _menu2(self):
        """ماژولِ منوی v2 (lazy، fail-soft). None اگر در دسترس نباشد. سیم‌کشیِ رفتاری
        فقط وقتی enabled() (پشتِ OCTOPUS_WIRE_MENU_V2) — flag خاموش → رفتارِ امروز بایت‌به‌بایت."""
        try:
            import menu_integration as _m2
            return _m2
        except Exception:  # noqa: BLE001
            return None

    def _mining_ui(self):
        """UIِ زیر-OSِ Mining (lazy، fail-soft). None = «وصل نیست» → رفتارِ امروز بایت‌به‌بایت.

        ۲۰۲۶-۰۷-۲۸ — بازسازیِ هوکِ گم‌شده. `mining_os/ACTIVATION.md` ادعا می‌کرد این UI
        «با ۳ هوکِ additive به center.py وصل شد»، ولی در درخت صفر ارجاع بود و خودِ فلگ
        هم وجود نداشت. بسته بیرونِ `_ops` است (پوشهٔ پروژه = مالکِ canonical)، پس مسیر
        اینجا افزوده می‌شود — از `__file__`، پس worktree-safe."""
        if os.environ.get("OCTOPUS_WIRE_MINING_UI") != "1":
            return None
        try:
            _mdir = str(_HERE.parent.parent / "03 - Projects" / "Mining")
            if _mdir not in sys.path:
                sys.path.insert(0, _mdir)
            from mining_os.ui import tg_mining as _mo
            return _mo
        except Exception:  # noqa: BLE001 — نبودِ پوشهٔ پروژه نباید مرکز را بکشد
            return None

    def _handle_mining_callback(self, cbq: dict, data: str, mo) -> dict:
        """verbِ mo: — منوی زیر-OSِ Mining (پشتِ OCTOPUS_WIRE_MINING_UI). editِ درجای همان
        پیام؛ fail-soft. صفر settle/effector/پول — ناوبری + ثبتِ verdict در لاگِ mining-owned
        (سینک به VERDICT_QUEUE.md خودش پشتِ فلگِ جداگانهٔ OCTOPUS_WIRE_MINING_VERDICT_SYNC)."""
        msg = cbq.get("message") or {}
        mid = msg.get("message_id")
        chat = (msg.get("chat") or {}).get("id")
        toast = ""
        try:
            txt, kb, toast = mo.handle_callback(data)
            if isinstance(mid, int):
                self._client.edit(mid, _scrub(str(txt or "")), keyboard=kb, chat_id=chat)
        except Exception:  # noqa: BLE001
            pass
        self._answer(cbq, toast)
        return {"kind": "mining", "data": data}

    def _handle_menu2_callback(self, cbq: dict, data: str, m2) -> dict:
        """verbِ m: — منوی v2 (پشتِ OCTOPUS_WIRE_MENU_V2). dispatch → editِ درجای همان پیام؛
        fail-soft. صفر settle/effector — فقط ناوبریِ منو (render)."""
        msg = cbq.get("message") or {}
        mid = msg.get("message_id")
        chat = (msg.get("chat") or {}).get("id")
        try:
            txt, kb = m2.dispatch(data)
            if isinstance(mid, int):
                self._client.edit(mid, _scrub(str(txt or "")), keyboard=kb, chat_id=chat)
        except Exception:  # noqa: BLE001
            pass
        self._answer(cbq)
        return {"kind": "menu2", "data": data}

    def wired(self) -> bool:
        """لوله وصل است؟ هر خطا/نبودِ client = False (fail-closed برای اثرگذاری)."""
        try:
            return bool(self._client is not None and self._client.wired())
        except Exception:  # noqa: BLE001
            return False

    _wired = wired  # نامِ داخلیِ هم‌معنا (خوانایی در متدها)

    def stopped(self) -> bool:
        """توقفِ حلقه.
        **مرزِ سختِ سراسری** (HALT-ALL / STOP ِ معمار via master_halted) و STOP-TG-CENTER
        همیشه می‌ایستانند — این کانکتورِ بیرونی هرگز حق ندارد مرزِ سراسری را نادیده بگیرد
        (رفعِ یافتهٔ G-no-master-halt؛ این شرط‌ها هرگز ضعیف نمی‌شوند).
        اما STOP-ORGANISM فقط وقتی یک «ایستِ کامل» است این کانکتور را می‌ایستاند؛ اگر
        هم‌راهش RESTART-REQUESTED باشد یعنی یک ری‌استارتِ روتینِ داشبورد است و tg-center باید
        از آن جان به‌در ببرد تا relaunch (owner decision #25 / WP3). خطای دیسک در چکِ توقف →
        «ایست» (امن‌ترین: fail-safe)."""
        try:
            return (STOP_TG_CENTER.exists()
                    or opslib.master_halted() is not None
                    or (opslib.STOP_ORGANISM.exists() and not _restart_pending()))
        except OSError:
            return True

    # ── کلیدها/نام‌ها/cadence ────────────────────────────────────────────────────
    def _legs(self) -> list[str]:
        """ترتیبِ پاها از render.LEGS (منبعِ قرارداد)؛ نبود → fallbackِ محلی."""
        r = self._rmod()
        try:
            keys = list(getattr(r, "LEGS", {}).keys()) if r is not None else []
        except Exception:  # noqa: BLE001
            keys = []
        return keys or list(LEG_KEYS)

    @staticmethod
    def _display_names(cfg: dict) -> dict:
        names = dict(DEFAULT_DISPLAY)
        dn = cfg.get("display_names")
        if isinstance(dn, dict):
            names.update({str(k): str(v) for k, v in dn.items()})
        return names

    @staticmethod
    def _cadence_for(cfg: dict, leg: str) -> float:
        """cadence دایجستِ یک پا: config['cadence_s'] یا dict per-leg با 'default'؛
        هر ناسازگاری → پیش‌فرضِ ۲۴h (fail-soft)."""
        cad = cfg.get("cadence_s", DEFAULT_DIGEST_S)
        try:
            if isinstance(cad, dict):
                return float(cad.get(leg, cad.get("default", DEFAULT_DIGEST_S)))
            return float(cad)
        except (TypeError, ValueError):
            return float(DEFAULT_DIGEST_S)

    def _status_text(self) -> str:
        """متنِ status از render (fail-soft → '')."""
        r = self._rmod()
        if r is None:
            return ""
        try:
            return str(r.render_status(r.collect_feeds() or {}) or "")
        except Exception:  # noqa: BLE001
            return ""

    def _live_cmd(self, text: str) -> str:
        """مسیرِ زنده‌سازی 2026-07-25: /id /box /code /live — fail-soft، read/propose-only."""
        try:
            if live_cmd_mod is None:
                return "live_commands در دسترس نیست."
            return str(live_cmd_mod.dispatch(text) or "")
        except Exception as e:  # noqa: BLE001
            return f"live_cmd fail-soft: {type(e).__name__}"

    # ── ensure_setup: idempotent — config حافظه است ─────────────────────────────
    def ensure_setup(self) -> bool:
        """تاپیک‌های ناقص را می‌سازد، منو را یک‌بار ست می‌کند، status را یک‌بار
        می‌سازد+پین می‌کند. دوبار اجرا = صفر کارِ تکراری (تستِ idempotency)."""
        if not self._wired():
            return False
        cfg = _load_config()
        dirty = False

        # chat_id: از config (رأی مالک) وگرنه از خودِ client (env TG_CENTER_CHAT_ID)
        if not cfg.get("chat_id"):
            cid = getattr(self._client, "center_chat_id", None)
            if cid:
                cfg["chat_id"] = cid
                dirty = True
        chat_id = cfg.get("chat_id")

        # نام‌های نمایشی: یک‌بار پیش‌فرض‌ها را در config بنشان تا مالک قابلِ‌ویرایش ببیند
        if not isinstance(cfg.get("display_names"), dict):
            cfg["display_names"] = dict(DEFAULT_DISPLAY)
            dirty = True
        names = self._display_names(cfg)

        # تاپیکِ هر پا — فقط پاهای بدونِ topic_id (نبودِ پاسخ = تلاشِ دوباره در setup بعدی)
        topics = cfg.setdefault("topics", {})
        if not isinstance(topics, dict):
            topics = cfg["topics"] = {}
        r = self._rmod()
        for leg in self._legs():
            if isinstance(topics.get(leg), int):
                continue                            # قبلاً ساخته شده — idempotent
            # عنوانِ تاپیک: آیکنِ برندِ پا + نامِ نمایشی (render.topic_title)؛ fallback = نامِ خالی
            try:
                title = r.topic_title(leg, cfg) if (r is not None and hasattr(r, "topic_title")) \
                    else names.get(leg, leg)
            except Exception:  # noqa: BLE001
                title = names.get(leg, leg)
            try:
                tid = self._client.create_topic(_scrub(title),
                                                chat_id=chat_id)
            except Exception:  # noqa: BLE001 — یک تلاش، بدونِ storm
                tid = None
            if isinstance(tid, int):
                topics[leg] = tid
                dirty = True

        # منوی commandها — ثبتِ مجدد وقتی فهرست عوض شود (پرچم = تعدادِ ثبت‌شده).
        # آیتم ۴ِ TG-P2: زیرِ split، inner و outer هرکدام منویِ خودشان را می‌گیرند.
        # flag-off → فقط outer (پاریتیِ تک-outerِ امروز بایت‌به‌بایت)؛ flag-on → هر دو.
        if cfg.get("commands_set") != len(COMMANDS):
            try:
                ok = bool(self._client.set_commands(list(COMMANDS)))
            except Exception:  # noqa: BLE001
                ok = False
            if ok:
                cfg["commands_set"] = len(COMMANDS)
                dirty = True
        try:
            import surface_router as _sr
            _split_on = _sr.enabled()
        except Exception:  # noqa: BLE001
            _split_on = False
        if _split_on:
            inner = self._inner_client()
            if inner is not None and cfg.get("commands_set_inner") != len(COMMANDS_INNER):
                try:
                    ok_in = bool(inner.set_commands(list(COMMANDS_INNER)))
                except Exception:  # noqa: BLE001
                    ok_in = False
                if ok_in:
                    cfg["commands_set_inner"] = len(COMMANDS_INNER)
                    dirty = True

        # پیامِ statusِ پین‌شده — فقط یک‌بار ساخته می‌شود؛ بعداً فقط edit (beat)
        if not isinstance(cfg.get("status_message_id"), int):
            text = self._status_text() or "🐙 مرکزِ فرماندهی — راه‌اندازی…"
            try:
                mid = self._client.send(_scrub(text), chat_id=chat_id, pin=True)
            except Exception:  # noqa: BLE001
                mid = None
            if isinstance(mid, int):
                cfg["status_message_id"] = mid
                dirty = True

        # ── دستورالعملِ پین‌شدهٔ General (۲۰۲۶-۰۷-۳۰) ──────────────────────────
        # مالک: «گروه تلگرام هیچی نداره که دستورالعمل». راهنما از قبل در
        # ابسیدین بود — ولی راهنمایی که در جای دیگری باشد راهنما نیست. یک‌بار
        # ساخته و پین می‌شود؛ بعد فقط اگر **متن** عوض شد ویرایش می‌شود (هش)،
        # پس هر restart یک پیامِ تازه نمی‌سازد.
        try:
            import hashlib
            import guide as _gd
            _gt = _gd.group_text()
            _gh = hashlib.sha256(_gt.encode("utf-8", "replace")).hexdigest()[:16]
            _gmid = cfg.get("guide_message_id")
            if isinstance(_gmid, int) and cfg.get("guide_hash") == _gh:
                pass                                   # بی‌تغییر — دست نزن
            elif isinstance(_gmid, int):
                try:
                    if self._client.edit(_gmid, _scrub(_gt), chat_id=chat_id):
                        cfg["guide_hash"] = _gh
                        dirty = True
                except Exception:  # noqa: BLE001
                    pass
            else:
                try:
                    _gmid = self._client.send(_scrub(_gt), chat_id=chat_id,
                                              pin=True)
                except Exception:  # noqa: BLE001
                    _gmid = None
                if isinstance(_gmid, int):
                    cfg["guide_message_id"] = _gmid
                    cfg["guide_hash"] = _gh
                    dirty = True
        except Exception:  # noqa: BLE001 — راهنما هرگز راه‌اندازی را نمی‌کشد
            pass

        if dirty:
            _save_config(cfg)
        return True

    # ── beat: edit status + دایجستِ سررسیده + تصمیم‌های نو ─────────────────────────
    def beat(self) -> dict:
        """یک ضربان. خروجی = {edited, digests, decisions} (شمارش برای مشاهده).
        statusِ پین‌شده فقط edit می‌شود — هرگز sendِ دوباره."""
        out = {"edited": False, "digests": 0, "decisions": 0}
        if not self._wired():
            return out
        cfg = _load_config()
        r = self._rmod()
        feeds: dict = {}
        if r is not None:
            try:
                feeds = r.collect_feeds() or {}
            except Exception:  # noqa: BLE001
                feeds = {}
        chat_id = cfg.get("chat_id")
        topics = cfg.get("topics") if isinstance(cfg.get("topics"), dict) else {}
        dirty = False

        # ۱) statusِ پین‌شده: همیشه edit (ensure_setup مسئولِ ساخت است)
        mid = cfg.get("status_message_id")
        if r is not None and isinstance(mid, int):
            try:
                txt = str(r.render_status(feeds) or "")
            except Exception:  # noqa: BLE001
                txt = ""
            if txt:
                try:
                    out["edited"] = bool(self._client.edit(mid, _scrub(txt),
                                                           chat_id=chat_id))
                except Exception:  # noqa: BLE001
                    pass

        # ۲) دایجستِ هر پا — سررسید با clockِ تزریقی؛ موفقیت = جلو رفتنِ last_digest
        now = float(self._clock())
        last = cfg.setdefault("last_digest", {})
        if not isinstance(last, dict):
            last = cfg["last_digest"] = {}
        if r is not None:
            legs_map = feeds.get("legs") if isinstance(feeds.get("legs"), dict) else {}
            _merged = str(os.environ.get(MERGED_DIGEST_FLAG, "0")).strip() in ("1", "true", "yes", "on")
            if _merged:
                # 2026-07-25 (build-spec §4): یک پیامِ ادغام‌شده در topic=system.
                # همهٔ پاهایِ due را جمع می‌کنیم؛ اگر حداقل یک پا متنی داشت، یک پیام
                # در topic=system می‌فرستیم و سررسیدِ همهٔ پاهایِ due را جلو می‌بریم.
                # این جایگزینِ ۹ پیامِ جدا می‌شود — رباتِ آرام‌تر.
                due_legs = []
                merged_lines = []
                for leg in self._legs():
                    try:
                        lr = float(last.get(leg, 0.0) or 0.0)
                    except (TypeError, ValueError):
                        lr = 0.0
                    if lr > 0.0 and now - lr < self._cadence_for(cfg, leg):
                        continue
                    due_legs.append(leg)
                    leg_data = legs_map.get(leg) or feeds.get(leg) or {}
                    try:
                        txt = str(r.render_leg_digest(leg, leg_data) or "")
                    except Exception:  # noqa: BLE001
                        txt = ""
                    if txt:
                        merged_lines.append(txt)
                if due_legs and merged_lines:
                    body = "\n\n".join(merged_lines)
                    try:
                        # ۰۷-۳۰: دایجستِ ادغامی خلاصهٔ هسته‌ای است نه پیامِ یک پا —
                        # مقصد از center-digest می‌آید (فلگ خاموش = همان system).
                        m = self._route_send("center-digest", body, cfg=cfg)
                    except Exception:  # noqa: BLE001
                        m = None
                    if m is not None:
                        for leg in due_legs:
                            last[leg] = now
                        out["digests"] += 1
                        dirty = True
                elif due_legs:
                    # پاهای due بودند ولی متنی نبودند — سررسید را جلو ببر (نویز نزن).
                    for leg in due_legs:
                        last[leg] = now
                    dirty = True
            else:
                # رفتارِ فعلی (پیش‌فرض): یک پیامِ جدا به هر پا، در تاپیکِ خودش.
                for leg in self._legs():
                    try:
                        lr = float(last.get(leg, 0.0) or 0.0)
                    except (TypeError, ValueError):
                        lr = 0.0
                    # lr==0 یعنی «هرگز پست نشده» → فوراً due (مستقل از epochِ clockِ تزریقی)
                    if lr > 0.0 and now - lr < self._cadence_for(cfg, leg):
                        continue
                    leg_data = legs_map.get(leg) or feeds.get(leg) or {}
                    try:
                        txt = str(r.render_leg_digest(leg, leg_data) or "")
                    except Exception:  # noqa: BLE001
                        continue
                    # حقیقتِ Taskهای ۲۴ ساعتِ پا (رأیِ ۰۷-۳۱: گزارشِ روزانه) —
                    # قراردادِ سکوت سرِ جایش می‌ماند: هر دو خالی ⇒ پیامی نیست.
                    try:
                        import leg_tasks as _lt2
                        _rep = _lt2.daily_report_text(leg, now=now)
                    except Exception:  # noqa: BLE001
                        _rep = ""
                    if _rep:
                        txt = (txt + "\n\n" + _rep) if txt else _rep
                    if not txt:
                        last[leg] = now                  # چیزی برای گفتن نیست — سررسید جلو
                        dirty = True
                        continue
                    try:
                        m = self._client.send(_scrub(txt), topic_id=topics.get(leg),
                                              chat_id=chat_id)
                    except Exception:  # noqa: BLE001
                        m = None
                    if m is not None:
                        last[leg] = now
                        out["digests"] += 1
                        dirty = True

        # ۳) تصمیم‌های نوی جعبهٔ راهنمایی — dedupe با seen-ids در config
        if r is not None:
            g = feeds.get("guidance") if isinstance(feeds.get("guidance"), dict) else {}
            items = g.get("items") if isinstance(g.get("items"), list) else []
            seen = [s for s in (cfg.get("seen") or []) if isinstance(s, str)]
            for it in items[:8]:
                if not isinstance(it, dict):
                    continue
                did = _decision_id(it)
                if did in seen:
                    continue
                it2 = dict(it)
                it2.setdefault("id", did)            # هم‌راستاییِ callback_data با dedupe
                try:
                    res = r.render_decision(it2)
                    txt, kb = res if isinstance(res, tuple) else (str(res), None)
                    kb = self._tok_kb(kb)        # P3 (D4): توکنِ ok/no/later وقتی فلگ روشن (وگرنه no-op)
                except Exception:  # noqa: BLE001
                    continue
                try:
                    # ۰۷-۳۰: کارتِ تصمیم دکمه دارد و دکمه‌هایش را خودِ همین مرکز
                    # رسیدگی می‌کند ⇒ target باید روی outer بماند (surface-routing
                    # همین را می‌گوید) وگرنه کارتِ مرده می‌سازیم — درسِ tr/iv.
                    m = self._route_send("center-decision", txt, cfg=cfg,
                                         keyboard=kb)
                except Exception:  # noqa: BLE001
                    m = None
                if m is not None:
                    seen.append(did)
                    out["decisions"] += 1
                    dirty = True
            cfg["seen"] = seen[-SEEN_CAP:]

        if dirty:
            _save_config(cfg)
        # فاز A (event bridge، هماهنگ با c6_state_machine از Opus مافوق): push رویدادهای
        # بحرانی به مالک. پشتِ OCTOPUS_WIRE_EVENT_BRIDGE؛ fail-soft (§۴).
        try:
            import event_bridge as _eb
            _eb.beat(self)
        except Exception:  # noqa: BLE001 — bridge هرگز beat را نمی‌کشد
            pass
        # 2026-07-25: money-pulse — فازِ جدید. درآمدِ پاها رو می‌خونه (propose-only،
        # هرگز MONEY_ATTRIBUTION جعلی). پشتِ OCTOPUS_WIRE_MONEY_PULSE؛ fail-soft.
        try:
            sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "heart"))
            import money_pulse as _mp
            _mp.beat(self)
        except Exception:  # noqa: BLE001 — pulse هرگز beat را نمی‌کشد
            pass
        # 2026-07-29: doctor-link — کارت‌های صف‌شدهٔ دکترِ اختاپوس (OCTOPUS-DOCTOR،
        # حالتِ outbox) با clientِ همین مرکز فرستاده می‌شوند؛ اتصالِ دومی به تلگرام
        # باز نمی‌شود. پشتِ OCTOPUS_WIRE_DOCTOR_TG؛ fail-soft.
        try:
            import doctor_link as _dl
            _dl.beat(self)
        except Exception:  # noqa: BLE001 — link هرگز beat را نمی‌کشد
            pass
        # ── VQ-TG-HOLD-001: outboxِ فوری + دایجستِ سلامتِ ساعتی ────────────────
        # ارگانیسم (پروسهٔ دیگر) پیام‌های بحرانی/گذار/recovery را در outbox
        # می‌گذارد و آیتم‌های نو را در بافرِ digest؛ این‌جا — تنها جایی که
        # کلاینتِ inner ِ send-only داریم — تحویل می‌دهیم. الگوی doctor_link:
        # هیچ poller یا اتصالِ تازه‌ای باز نمی‌شود. هر شکست فقط همان بخش را
        # می‌اندازد؛ نشانگرِ flush فقط بعد از ارسالِ موفق جلو می‌رود.
        try:
            import hold_policy as _hp
            _urg = _hp.urgent_pending(now=now, cap=5)
            _sent_upto = None
            for _u in _urg:
                _m = self._route_send("center-urgent",
                                      str(_u.get("text") or ""), cfg=cfg)
                if _m is None:
                    break                       # ارسال نشد → نشانگر جلو نمی‌رود
                _sent_upto = float(_u.get("ts") or 0)
            if _sent_upto:
                _hp.mark_urgent_flushed(_sent_upto)
            if _hp.digest_due(now=now):
                _dg = _hp.flush_digest(now=now)
                if _dg:
                    self._route_send("center-health-digest", _dg, cfg=cfg)
        except Exception:  # noqa: BLE001 — تحویلِ hold-policy هرگز beat را نمی‌کشد
            pass
        # ── موتورِ کارهای پاها (رأیِ ۰۷-۳۰ شب): یک کار در هر ضربان ──────────────
        self._drive_leg_engine()
        # ── کارتِ زندهٔ هر پا، حتی وقتی بیکار است ────────────────────────────
        # ⚠️ تا امروز کارت فقط وقتی ساخته می‌شد که کاری وجود داشت یا دکمه‌ای
        # زده می‌شد. نتیجه: مالک گروه را باز می‌کرد و **هیچ کارتی نبود** —
        # «گروه هیچی نداره». حالا هر ضربان تازه می‌شود؛ ضدِ سیل هم هست چون
        # `_refresh_leg_card` روی هشِ متن زود برمی‌گردد و بی‌تغییر ویرایش
        # نمی‌زند. یک پا در هر ضربان تا رگبارِ ۹ ویرایشی نسازد.
        # ⚠️ نسخهٔ اولِ این بند شمارنده را روی همین `cfg` ِ beat می‌نوشت و
        # `dirty = True` می‌زد. اجرای واقعی نشانش داد که **دو** جا می‌بازد:
        # (۱) خطِ `if dirty: _save_config(cfg)` ِ پایین داخلِ شرطِ ساعتیِ پالس
        #     است، پس ذخیره فقط ساعتی یک بار رخ می‌داد؛
        # (۲) `_refresh_leg_card` خودش `_load_config()` می‌کند و ذخیره می‌کند،
        #     پس نوشتنِ من روی نسخهٔ کهنه هر طور بود دور می‌رفت.
        # نتیجه در گروه: شمارنده روی صفر گیر کرد، هر ضربان همان پای اول را
        # می‌گرفت، روی هش برمی‌گشت ⇒ فقط **یک** کارت تا ابد. حالا شمارنده را
        # بعد از refresh از دیسکِ تازه می‌خوانم و همان‌جا می‌نویسم.
        # کادنس (نه «هر beat»): با حلقهٔ زندهٔ ۳۰۰ثانیه‌ای عملاً یک پا در هر
        # ضربان است، ولی دو beat با ساعتِ یکسان دومی را رد می‌کند — پس ناوردیِ
        # «ضربانِ بلافاصلهٔ دوم صفر send» که از قبل اینجا بود دست‌نخورده می‌مانَد.
        try:
            _legs = self._legs()
            _c0 = _load_config()
            _ll = float(_c0.get("last_leg_card", 0.0) or 0.0)
        except (TypeError, ValueError, OSError):  # noqa: BLE001
            _legs, _c0, _ll = [], None, 0.0
        if _legs and now - _ll >= LEG_CARD_EVERY_S:
            try:
                _i = int(_c0.get("leg_card_cursor", 0) or 0) % len(_legs)
                self._refresh_leg_card(_legs[_i])
                _c1 = _load_config()          # شاملِ نوشته‌های خودِ refresh
                _c1["leg_card_cursor"] = (_i + 1) % len(_legs)
                _c1["last_leg_card"] = now
                _save_config(_c1)
                # ⚠️⚠️ و اینجا بزرگ‌ترین تلهٔ این تابع: `cfg` در خطِ ۵۵۵ از دیسک
                # خوانده شده و هر `_save_config(cfg)` ِ بعدی در همین beat آن
                # نسخهٔ کهنه را می‌نویسد — پس نوشتهٔ `_refresh_leg_card` (که
                # کلاینتِ خودش را دارد و مستقل ذخیره می‌کند) **بلعیده** می‌شود.
                # اجرای واقعی نشانش داد: refresh کارتِ `lead` را با شناسهٔ ۱۱۰
                # ثبت کرد و همان beat به None برگشت، چون شاخهٔ پالس ساعتی
                # (last_pulse=0 ⇒ بارِ اول همیشه سررسیده) بعدش cfg ِ کهنه را
                # نوشت. روی درختِ زنده تصادفاً جان برد چون آن ضربان پالس نداشت.
                # درمان: نوشته‌های refresh را به cfg برگردان تا هر نویسندهٔ
                # بعدی هم آن‌ها را داشته باشد. (دو نویسنده روی یک فایلِ حالت.)
                for _k in ("leg_card_ids", "leg_card_hash",
                           "leg_card_cursor", "last_leg_card"):
                    if _k in _c1:
                        cfg[_k] = _c1[_k]
            except Exception:  # noqa: BLE001 — کارت هرگز beat را نمی‌کشد
                pass
        # ── پالسِ ساعتیِ لنگر (رأیِ مالک ۲۰۲۶-۰۷-۳۰: «پالسِ ساعتی») ────────────
        # یک ضربانِ کوتاه در ساعت به DM ِ مالک — حسِ «زنده است» بدونِ رگبار.
        # هیچ فلگِ تازه‌ای ندارد: مقصدش از `center-pulse` می‌آید که current اش
        # `none` است ⇒ تا OCTOPUS_TG_SPLIT_V1 مسلح نشود، _route_send عمداً
        # هیچ‌چیز نمی‌فرستد و فقط سررسید جلو می‌رود. بارِ اول بعد از فلگ، خودِ
        # پیامِ خانه هم ساخته و پین می‌شود (hm:* دکمه‌هایش را همین مرکز دارد).
        try:
            _lp = float(cfg.get("last_pulse", 0.0) or 0.0)
        except (TypeError, ValueError):
            _lp = 0.0
        if now - _lp >= 3600.0:
            cfg["last_pulse"] = now
            dirty = True
            try:
                _pt = self._home_pulse_text()
                if _pt:
                    _kb = self._home_keyboard()
                    _mid = self._route_send("center-pulse", _pt, cfg=cfg,
                                            keyboard=_kb)
                    out["pulse"] = _mid is not None
                    # خانهٔ پین‌شده: بارِ اولی که پالس واقعاً به DM رسید، همان
                    # پیام پین می‌شود تا «خانه» همیشه بالای چت باشد.
                    if (_mid is not None
                            and not isinstance(cfg.get("home_message_id"), int)):
                        try:
                            _own = getattr(self._client, "owner_chat_id", None)
                            if _own is not None:
                                self._client.pin_message(_mid, chat_id=_own)
                                cfg["home_message_id"] = _mid
                        except Exception:  # noqa: BLE001 — pin نشد → پالس سرِ جایش است
                            pass
            except Exception:  # noqa: BLE001 — پالس هرگز beat را نمی‌کشد
                pass
            if dirty:
                _save_config(cfg)
                dirty = False
        return out

    # ── خانهٔ لنگر: متن و دکمه‌ها ──────────────────────────────────────────────
    def _home_pulse_text(self) -> str:
        """متنِ پالسِ ساعتی — کوتاه، فارسی، بدونِ فهرستِ بلند.

        رقم‌ها فارسی نوشته می‌شوند؛ عددِ لاتین وسطِ جملهٔ RTL جابه‌جا می‌شود
        (درسِ bidi). هر بخش fail-soft است: نبودِ هر منبع ⇒ همان بخش حذف."""
        lines = ["🐙 <b>نبضِ اختاپوس</b>"]
        try:
            txt = self._status_text() or ""
            head = [ln for ln in txt.splitlines() if ln.strip()][:3]
            lines += head
        except Exception:  # noqa: BLE001
            pass
        try:
            import surface_policy as _spol
            held = len(_spol.held_since(500))
            if held:
                lines.append(f"🔇 نگه‌داشته‌شده: {_fa_num(held)} مورد (با دکمهٔ زیر ببین)")
        except Exception:  # noqa: BLE001
            pass
        # صفِ ساختِ خود + یادآوریِ راهِ اصلی. یک خطِ متن، صفر دکمهٔ اضافه —
        # نقشِ «مامور»: یاد بده، نه اینکه تصمیمِ تازه اضافه کن.
        try:
            import build_cmd as _bc
            _s = _bc.loop_status()
            if _s.get("tasks") or _s.get("patches"):
                lines.append(f"🛠 صفِ ساخت: {_fa_num(_s['tasks'])} · "
                             f"پچِ منتظرِ رأی: {_fa_num(_s['patches'])}")
            else:
                lines.append("🛠 بنویس «بساز: …» تا خودش را بسازد")
        except Exception:  # noqa: BLE001
            pass
        return "\n".join(lines[:9])

    def _home_keyboard(self) -> list:
        """سه دکمه — نه بیشتر. قاعدهٔ خودِ مالک است و گاردش
        (`t_the_home_keyboard_never_exceeds_three_decision_points`) دکمهٔ
        چهارمِ «ساختِ خود» را گرفت. گارد بازنویسی **نشد**: درِ ساخت به سطحِ
        دوم رفت (زیرِ «وضعیتِ کامل») و راهِ اصلی‌اش متنِ آزادِ «بساز: …» است
        که در پالس هم یادآوری می‌شود. یک تصمیمِ کمتر در سطحِ اول."""
        return [[{"text": "🐙 وضعیتِ کامل", "callback_data": "hm:st"}],
                [{"text": "🦵 پاها", "callback_data": "hm:legs"},
                 {"text": "🔇 ناگفته‌ها", "callback_data": "hm:held"}]]

    def _handle_home_callback(self, cbq: dict, data: str) -> dict:
        """دکمه‌های خانهٔ لنگر — همه read-only، صفر جهش، صفر خرج.

        مالکیت را `handle_update → _is_owner` از قبل گیت کرده؛ این‌جا فقط
        رندر است. هر شکست ⇒ متنِ صادقِ کوتاه، هرگز سکوت."""
        verb = str(data or "").split(":", 1)[-1]
        msg = cbq.get("message") or {}
        chat = (msg.get("chat") or {}).get("id")
        try:
            self._client.answer_callback(cbq.get("id"), "")
        except Exception:  # noqa: BLE001
            pass
        if verb == "st":
            body = self._status_text() or "هنوز چیزی برای گفتن ندارم."
            # درِ «ساختِ خود» در سطحِ **دوم** — سطحِ اول سه دکمه می‌ماند.
            try:
                self._client.send(_scrub(body), chat_id=chat, keyboard=[
                    [{"text": "🛠 ساختِ خود", "callback_data": "hm:build"}]])
                return {"kind": "home", "verb": verb}
            except Exception:  # noqa: BLE001
                pass
        elif verb == "legs":
            rows = []
            try:
                cfg = _load_config()
                r = self._rmod()
                feeds = (r.collect_feeds() or {}) if r is not None else {}
                legs_map = feeds.get("legs") if isinstance(feeds.get("legs"), dict) else {}
                for leg in self._legs():
                    d = legs_map.get(leg) or {}
                    mark = "🟢" if d else "⚪️"
                    rows.append(f"{mark} {leg}")
            except Exception:  # noqa: BLE001
                pass
            body = ("🦵 <b>پاها</b>\n" + "\n".join(rows)) if rows else \
                "🦵 هنوز گزارشی از پاها ندارم — تاپیک‌هایشان در گروه است."
        elif verb == "held":
            # رأی §۶ VQ-TG-HOLD-001: فقط خلاصه/دسته‌بندی · حداکثر ۱۰ · متن echo
            # نمی‌شود (نسخهٔ اول text[:80] را نشان می‌داد — همان نقضی که رأی
            # بست) · خواندن = HELD_VIEWED، نه sent، و هیچ ارسال/اجرایی نمی‌سازد.
            try:
                import hold_policy as _hp
                import surface_policy as _spol
                body = _hp.held_view(_spol.held_since(500))
            except Exception:  # noqa: BLE001
                body = "🔇 فهرستِ ناگفته‌ها در دسترس نیست."
        elif verb == "build":
            # زیرمنوی «ساختِ خود» — وضعیتِ صادقِ هر پلهٔ حلقه + صف + پچ‌ها.
            try:
                import build_cmd as _bc
                body = (_bc.status_text() + "\n\n" + _bc.queue_text()
                        + "\n\n" + _bc.patches_text())
                kb = [[{"text": "📥 صف", "callback_data": "hm:bq"},
                       {"text": "🧩 پچ‌ها", "callback_data": "hm:bp"}]]
                try:
                    self._client.send(_scrub(body), chat_id=chat, keyboard=kb)
                except Exception:  # noqa: BLE001
                    pass
                return {"kind": "home", "verb": verb}
            except Exception:  # noqa: BLE001
                body = "🛠 حلقهٔ ساخت در دسترس نیست."
        elif verb == "bq":
            try:
                import build_cmd as _bc
                body = _bc.queue_text()
            except Exception:  # noqa: BLE001
                body = "📥 صف در دسترس نیست."
        elif verb == "bp":
            try:
                import build_cmd as _bc
                body = _bc.patches_text()
            except Exception:  # noqa: BLE001
                body = "🧩 فهرستِ پچ در دسترس نیست."
        else:
            body = "این دکمه را نمی‌شناسم — خانه را دوباره باز کن."
        try:
            self._client.send(_scrub(body), chat_id=chat)
        except Exception:  # noqa: BLE001
            pass
        return {"kind": "home", "verb": verb}

    # ── مدلِ Task ِ پاها: کارت، دکمه‌ها، موتور ─────────────────────────────
    def _refresh_leg_card(self, leg: str) -> None:
        """کارتِ زندهٔ پا — یک پیام در تاپیکِ خودش که فقط **ویرایش** می‌شود.
        ساخت فقط بارِ اول؛ ویرایش فقط وقتی متن عوض شده (ضدِ سیل). pin ِ
        fail-soft. هر شکست بی‌صدا — کارت هرگز مسیرِ اصلی را نمی‌کشد."""
        try:
            import hashlib
            import leg_tasks as _lt
            import power as _pw
            cfg = _load_config()
            topics = cfg.get("topics") if isinstance(cfg.get("topics"), dict) else {}
            tid = topics.get(leg)
            # ⚠️ نسخهٔ اول `chat is None` را هم شرطِ بازگشت گذاشته بود — از خودِ
            # مرکز سخت‌گیرتر: در همه‌جای دیگر `chat_id=None` مسیرِ قانونی است و
            # خودِ client حلش می‌کند (env TG_CENTER_CHAT_ID). روی درختِ زنده
            # اتفاقی ست بود پس کار می‌کرد؛ در هر نصبی که نبود، کارتِ پاها بی‌صدا
            # هرگز ساخته نمی‌شد. فقط تاپیک لازم است.
            chat = cfg.get("chat_id")
            if not isinstance(tid, int):
                return
            paused = False
            try:
                paused = bool(_pw.leg_paused(leg))
            except Exception:  # noqa: BLE001
                pass
            body = _lt.card_text(leg, paused=paused,
                                 kpi=self._kpi_target(cfg, leg))
            h = hashlib.sha256(body.encode("utf-8", "replace")).hexdigest()[:16]
            hashes = cfg.setdefault("leg_card_hash", {})
            ids = cfg.setdefault("leg_card_ids", {})
            # ⚠️ ۲۰۲۶-۰۷-۳۰: این خطِ «بی‌تغییر ⇒ برگرد» یک تلهٔ ماندگار داشت.
            # وجودِ **واقعیِ** پیام را نمی‌سنجید؛ فقط عدد بودنِ id را. پس یک
            # شناسهٔ جعلی + هشِ منطبق = کارت **هرگز** ساخته نمی‌شود، برای همیشه.
            # و همین افتاد: پروبِ e2e ِ خودم با کلاینتِ جاسوس (که 9000+n
            # برمی‌گرداند) روی config ِ **زنده** نوشت، پس `lead` شناسهٔ ۹۰۱۰
            # گرفت و کارتش دیگر ساخته نشد. گارد حالا شناسه‌های بازهٔ جاسوس را
            # نامعتبر می‌شمارد و از نو می‌سازد.
            _bogus = isinstance(ids.get(leg), int) and 9000 <= ids[leg] < 9100
            if _bogus:
                ids.pop(leg, None)
                hashes.pop(leg, None)
                _save_config(cfg)
            if (not _bogus and hashes.get(leg) == h
                    and isinstance(ids.get(leg), int)):
                return                              # بی‌تغییر — ویرایشِ بیهوده نزن
            kb = _lt.card_keyboard(leg)
            mid = ids.get(leg)
            ok = False
            if isinstance(mid, int):
                try:
                    ok = bool(self._client.edit(mid, _scrub(body), keyboard=kb,
                                                chat_id=chat))
                except Exception:  # noqa: BLE001
                    ok = False
            if not ok:
                try:
                    mid = self._client.send(_scrub(body), chat_id=chat,
                                            topic_id=tid, keyboard=kb,
                                            stream=f"leg-card-{leg}")
                except TypeError:
                    mid = self._client.send(_scrub(body), chat_id=chat,
                                            topic_id=tid, keyboard=kb)
                if isinstance(mid, int):
                    ids[leg] = mid
                    try:
                        self._client.pin_message(mid, chat_id=chat)
                    except Exception:  # noqa: BLE001
                        pass
            if isinstance(ids.get(leg), int):
                hashes[leg] = h
                _save_config(cfg)
        except Exception:  # noqa: BLE001
            pass

    def _handle_tasks_callback(self, cbq: dict, data: str) -> dict:
        """tk:<op>:<leg>[:<id>] — چهار دکمهٔ کارت + شروع/لغوِ کار. همه
        برگشت‌پذیر و بدونِ اثرِ بیرونی؛ توقف/ادامه از power ِ ممیزی‌شده."""
        parts = str(data or "").split(":")
        op = parts[1] if len(parts) > 1 else ""
        leg = parts[2] if len(parts) > 2 else ""
        tid = parts[3] if len(parts) > 3 else ""
        msg = cbq.get("message") or {}
        chat = (msg.get("chat") or {}).get("id")
        thread = msg.get("message_thread_id")
        try:
            self._client.answer_callback(cbq.get("id"), "")
        except Exception:  # noqa: BLE001
            pass
        import leg_tasks as _lt
        body = ""
        kb = None
        # چهار دکمهٔ کارت = همان چهار فرمانِ طبیعی (یک منبع: _exec_leg_command).
        if op == "c":
            body = self._exec_leg_command("resume", leg)[0]
        elif op == "p":
            body = self._exec_leg_command("pause", leg)[0]
        elif op == "q":
            body = self._exec_leg_command("queue", leg)[0]
        elif op == "r":
            body = self._exec_leg_command("receipts", leg)[0]
        elif op == "s" and tid:
            t = _lt.set_state(leg, tid, _lt.WORKING)
            body = (f"▶️ {tid} شروع شد — نتیجه با رسید می‌آید.") if t else \
                f"{tid} پیدا نشد."
        elif op == "x" and tid:
            t = _lt.cancel(leg, tid)
            body = f"❌ {tid} لغو شد." if t else f"{tid} پیدا نشد."
        elif op == "g" and tid:
            # بازخوردِ مثبت (بند ۱۱) — به همان پا و همان کار سنجاق می‌شود.
            t = _lt.record_feedback(leg, tid, "good")
            body = "🧠 ثبت شد — همین مسیر ادامه پیدا می‌کند." if t else \
                f"{tid} پیدا نشد."
        elif op == "b" and tid:
            # بازخوردِ منفی: اول دلیل — بدونِ دلیل، درسِ قابلِ‌مصرف نمی‌شود.
            t = _lt.record_feedback(leg, tid, "bad")
            if t:
                body = "مشکل چه بود؟"
                kb = _lt.bad_feedback_keyboard(leg, {"id": tid})
            else:
                body = f"{tid} پیدا نشد."
        elif op == "br" and tid and len(parts) > 4:
            code = parts[4]
            label = _lt.FEEDBACK_REASONS.get(code, "")
            t = _lt.record_feedback(leg, tid, "bad", reason=code) if label \
                else None
            body = (f"ثبت شد: «{label}» — در گزارشِ روزانه و درسِ همین پا "
                    "دیده می‌شود.") if t else "دلیلِ ناشناخته."
        else:
            body = "این دکمه را نمی‌شناسم."
        try:
            self._client.send(_scrub(body), chat_id=chat, topic_id=thread,
                              keyboard=kb)
        except Exception:  # noqa: BLE001
            pass
        self._refresh_leg_card(leg)
        return {"kind": "leg-task", "op": op, "leg": leg}

    @staticmethod
    def _kpi_target(cfg: dict, leg: str) -> "int | None":
        """هدفِ روزانهٔ مالک برای این پا از config — نبود/خرابی → None (خطِ
        KPI فقط با هدفِ واقعی روی کارت می‌آید، عددسازی ممنوع)."""
        try:
            kd = (cfg or {}).get("kpi_daily")
            n = int(kd.get(leg)) if isinstance(kd, dict) else 0
            return n if n > 0 else None
        except (TypeError, ValueError, AttributeError):
            return None

    @staticmethod
    def _media_task_text(msg: dict) -> str:
        """پیامِ غیرمتنی → متنِ کار: برچسبِ نوع + caption (بند ۸ فاز ۲).

        فقط توصیف — نه دانلود، نه پردازش؛ file بر روی سرورِ تلگرام می‌ماند و
        موتورِ read-only فقط با همین متن کار می‌کند (اگر کافی نبود، صادقانه
        BLOCKED می‌شود و از مالک توضیح می‌خواهد)."""
        cap = str(msg.get("caption") or "").strip()[:300]
        if msg.get("photo"):
            tag = "[عکس]"
        elif isinstance(msg.get("document"), dict):
            name = str(msg["document"].get("file_name") or "فایل")[:60]
            tag = f"[فایل: {name}]"
        elif msg.get("voice") or msg.get("audio"):
            tag = "[صدا]"
        elif msg.get("video") or msg.get("video_note"):
            tag = "[ویدئو]"
        elif isinstance(msg.get("location"), dict):
            loc = msg["location"]
            tag = f"[لوکیشن {loc.get('latitude')}, {loc.get('longitude')}]"
        else:
            return ""
        return f"{tag} {cap}".strip()

    def _exec_leg_command(self, cmd: str, leg: str) -> tuple:
        """(body, keyboard|None) برای فرمان‌های طبیعیِ leg_commands.COMMANDS.

        هیچ قابلیتِ تازه‌ای نمی‌سازد — نامِ طبیعی به همان مسیرهای ممیزی‌شدهٔ
        دکمه‌ها می‌رسد (توقف/ادامه از power ِ audit-دار، صف/رسید از
        leg_tasks). هر کلیدِ COMMANDS این‌جا شاخه دارد؛ تستِ ضدِ دکمهٔ مرده
        این را قفل می‌کند."""
        import leg_tasks as _lt
        if cmd == "status":
            paused = False
            try:
                import power as _pw
                paused = bool(_pw.leg_paused(leg))
            except Exception:  # noqa: BLE001
                pass
            kpi = self._kpi_target(_load_config(), leg)
            return (_lt.card_text(leg, paused=paused, kpi=kpi),
                    _lt.card_keyboard(leg))
        if cmd == "queue":
            rows = _lt.queue(leg)
            return (("📋 <b>صفِ " + leg + "</b>\n" + "\n".join(
                f"· {t['id']} [{t['state']}] {t['text'][:60]}"
                for t in rows[:10])) if rows else "📋 صف خالی است."), None
        if cmd == "resume":
            try:
                import power as _pw
                ok, why = _pw.resume_leg(leg)
                return ("▶️ ادامه — پا برگشت." if ok
                        else f"ادامه نشد: {why}"), None
            except Exception:  # noqa: BLE001
                return "ادامه نشد — power در دسترس نیست.", None
        if cmd == "pause":
            try:
                import power as _pw
                ok, why = _pw.pause_leg(leg)
                return ("⏸ متوقف شد — با «ادامه» برمی‌گردد." if ok
                        else f"توقف نشد: {why}"), None
            except Exception:  # noqa: BLE001
                return "توقف نشد — power در دسترس نیست.", None
        if cmd == "next":
            t = _lt.start_next(leg)
            return ((f"▶️ {t['id']} شروع شد — نتیجه با رسید می‌آید.") if t
                    else "چیزی در صف نیست."), None
        if cmd == "blockers":
            return _lt.blockers_text(leg), None
        if cmd == "receipts":
            done = _lt.recent_done(leg, 5)
            return ("\n\n".join(_lt.receipt_text(t) for t in done)
                    if done else "هنوز نتیجه‌ای ثبت نشده."), None
        if cmd == "report":
            rep = _lt.daily_report_text(leg)
            return (rep or "در ۲۴ ساعتِ گذشته فعالیتی ثبت نشده."), None
        return "این فرمان را نمی‌شناسم.", None

    def _drive_leg_engine(self) -> None:
        """در هر ضربان حداکثر **یک** کارِ WORKING از کلِ پاها به مغزِ
        read-only داده می‌شود (محلی-اول، صفر اثرِ بیرونی). جوابِ «داده کم
        است» ⇒ BLOCKED با کارتِ سؤال؛ وگرنه DONE با رسید و شاهد."""
        try:
            import leg_tasks as _lt
            cfg = _load_config()
            topics = cfg.get("topics") if isinstance(cfg.get("topics"), dict) else {}
            chat = cfg.get("chat_id")
            for leg in self._legs():
                t = _lt.claim_next(leg)
                if not t:
                    continue
                try:
                    import ask_brain as _ab
                    a = _ab.ask(t["text"], topic_key=leg)
                    answer = str(a.get("text") or "") if a.get("ok") else ""
                except Exception:  # noqa: BLE001
                    answer = ""
                state, q = _lt.judge_engine_answer(answer)
                if state == _lt.DONE:
                    done = _lt.set_state(leg, t["id"], _lt.DONE,
                                         result=answer[:200] or "انجام شد",
                                         evidence=answer)
                    if done:
                        try:
                            # رسید + دو دکمهٔ رأیِ کیفی (بند ۱۱) — بازخورد
                            # به همین کار سنجاق می‌شود، نه مجوزِ عمومی.
                            self._client.send(_scrub(_lt.receipt_text(done)),
                                              chat_id=chat,
                                              topic_id=topics.get(leg),
                                              keyboard=_lt.receipt_keyboard(
                                                  leg, done))
                        except Exception:  # noqa: BLE001
                            pass
                else:
                    blk = _lt.set_state(leg, t["id"], _lt.BLOCKED, question=q)
                    if blk:
                        try:
                            self._client.send(
                                _scrub(_lt.blocked_text(blk)), chat_id=chat,
                                topic_id=topics.get(leg),
                                keyboard=_lt.blocked_keyboard(leg, blk))
                        except Exception:  # noqa: BLE001
                            pass
                self._refresh_leg_card(leg)
                break                              # یک کار در هر ضربان — beat سبک بماند
        except Exception:  # noqa: BLE001 — موتور هرگز beat را نمی‌کشد
            pass

    def _send_console_reply(self, reply: dict, src: dict) -> dict:
        """پاسخِ مامور را به همان چتی که پیام از آن آمد بفرست (همیشه DM ِ مالک —
        گیتِ adapter فقط core_conversation را رد کرده). fail-soft."""
        msg = (src.get("message") or {}) if isinstance(src, dict) else {}
        chat = (msg.get("chat") or {}).get("id")
        kb = reply.get("keyboard") or None
        try:
            cbid = src.get("id") if isinstance(src, dict) else None
            if cbid:
                self._client.answer_callback(cbid, "")
        except Exception:  # noqa: BLE001
            pass
        try:
            self._client.send(_scrub(str(reply.get("text") or "")),
                              chat_id=chat, keyboard=kb)
        except Exception:  # noqa: BLE001
            pass
        return {"kind": "owner-console", "console_kind": reply.get("kind")}

    # ── مسیریابیِ ارسالِ محیطی (رأیِ مالک ۲۰۲۶-۰۷-۳۰: «بله، هر سه را انجام بده») ──
    def _route_send(self, stream: str, text: str, *, cfg=None, keyboard=None,
                    pin: bool = False):
        """ارسالِ یک جریانِ محیطیِ مرکز از راهِ surface_router.resolve.

        این همان صداکننده‌ای است که `resolve` از روزِ ساختش نداشت — تستش ۱۲/۱۲
        سبز بود و در مسیرِ زندهٔ ارسال هیچ نقشی نداشت؛ به همین دلیل ۵۸ پیامِ
        هسته‌ای با topic=None در General نشسته بود.

        قرارداد:
        · فلگ خاموش (`OCTOPUS_TG_SPLIT_V1`) ⇒ resolve بلوکِ `current` را می‌خواند
          که واقعیتِ امروز است ⇒ رفتار بایت‌به‌بایت همان قبل.
        · فلگ روشن ⇒ بلوکِ `target`: جریانِ هسته‌ای به DM می‌رود (قراردادِ
          legs-only)، `center-alert` به رباتِ inner (بی‌دکمه، پس بدونِ ریسکِ
          کارتِ مرده — دکمه‌دارها روی همان outer می‌مانند که خودش handler دارد).
        · `(None, None, None)` از resolve (بلوکِ `none`) ⇒ عمداً هیچ ارسالی.
        · هر خطا در خودِ روتر ⇒ سقوط به مسیرِ قدیمی (گروه/تاپیکِ system) —
          پیامِ گم‌شده بدتر از پیامِ در جای اشتباه است.
        """
        if not self._wired() or not text:
            return None
        if cfg is None:
            cfg = _load_config()
        try:
            import surface_router as _sr
            cl, cid, tid = _sr.resolve(stream, clients=self._clients_map(), cfg=cfg)
        except Exception:  # noqa: BLE001 — روتر هرگز ارسال را نمی‌کشد
            topics = cfg.get("topics") if isinstance(cfg.get("topics"), dict) else {}
            cl, cid, tid = self._client, cfg.get("chat_id"), topics.get("system")
        if cl is None:
            return None                      # بلوکِ none — سکوتِ عمدی (مثلِ pulse ِ پیش‌ازفلگ)
        try:
            return cl.send(_scrub(text), chat_id=cid, topic_id=tid,
                           keyboard=keyboard, pin=pin, stream=stream)
        except TypeError:
            # کلاینتِ تستی/کهنه بدونِ پارامترِ stream — قراردادِ عمومی حفظ می‌شود.
            return cl.send(_scrub(text), chat_id=cid, topic_id=tid,
                           keyboard=keyboard, pin=pin)

    def push_alert(self, text: str) -> bool:
        """push یک پیامِ alert. منبعِ ارسالِ event_bridge و push-per-event.
        fail-soft، scrubشده (parity با _scrub:120). false = ارسال نشد/خطا.

        ۲۰۲۶-۰۷-۳۰: مقصد دیگر هاردکدِ topic=system نیست — از `center-alert` در
        surface-routing.json می‌آید. فلگ خاموش = همان system ِ قبلی؛ فلگ روشن =
        DM ِ رباتِ اختاپوس (inner)، طبقِ قراردادِ critical-alerts."""
        if not self._wired() or not text:
            return False
        try:
            return self._route_send("center-alert", text) is not None
        except Exception:  # noqa: BLE001
            return False

    def _topic_key(self, msg: dict) -> str:
        """نامِ پا برای تاپیکی که پیام در آن آمده — یا "" (General/خصوصی/ناشناخته).

        وارونهٔ نگاشتِ `topics` در center-config. کاربردش این است که سؤالِ آزادِ
        مالک در تاپیکِ 🦑lead، contextِ لید بگیرد نه contextِ عمومی — یعنی جای
        پرسیدن هم بخشی از سؤال باشد. fail-soft: هر ابهام → "" (contextِ عمومی)."""
        try:
            tid = msg.get("message_thread_id")
            if not isinstance(tid, int) or not msg.get("is_topic_message"):
                return ""
            topics = (_load_config() or {}).get("topics") or {}
            for name, num in topics.items():
                if num == tid:
                    return str(name)
        except Exception:  # noqa: BLE001
            pass
        return ""

    # ── handle_update: فقط مالک — /now و callbackهای ok/no/later ─────────────────
    @staticmethod
    def _reply_thread(msg: dict):
        """تاپیکی که باید در آن جواب داد — یا None.

        باگِ ۲۰۲۶-۰۷-۲۶: گروهِ مرکز فوروم است. جوابِ بی‌`message_thread_id` در
        تاپیکِ **General** می‌افتد، نه آن‌جا که مالک پرسیده. یعنی بات جواب می‌داد و
        مالک هرگز نمی‌دید — «فرستادم» درست بود و «رسید» غلط، بدونِ هیچ خطایی.

        فقط وقتی thread می‌فرستیم که تلگرام خودش گفته باشد این پیام در یک تاپیک
        است (`is_topic_message`). در Generalِ فوروم و در چتِ خصوصی این پرچم نیست →
        None → رفتارِ امروز بایت‌به‌بایت. ارسالِ thread_idِ نامعتبر خطای ۴۰۰ می‌دهد،
        پس این باریک‌بینی عمدی است.
        """
        if os.environ.get(TOPIC_REPLY_FLAG, "").strip().lower() not in (
                "1", "true", "yes", "on"):
            return None
        try:
            if not msg.get("is_topic_message"):
                return None
            tid = msg.get("message_thread_id")
            return int(tid) if isinstance(tid, int) else None
        except (TypeError, ValueError, AttributeError):
            return None

    def _is_owner(self, u: dict) -> bool:
        """allowlist. اول helperِ قراردادیِ client.is_owner؛ هر خطا/ابهام = False
        (fail-closed: غیرمالک هرگز فرمان نمی‌دهد — قانونِ P3 §5)."""
        try:
            fn = getattr(self._client, "is_owner", None)
            if callable(fn):
                return bool(fn(u))
        except Exception:  # noqa: BLE001
            return False
        try:
            owner = getattr(self._client, "owner_chat_id", None)
            frm = ((u.get("message") or {}).get("from")
                   or (u.get("callback_query") or {}).get("from") or {})
            return owner is not None and frm.get("id") == owner
        except Exception:  # noqa: BLE001
            return False

    def handle_update(self, u) -> "dict | None":
        """یک update. غیرمالک/ناوصل/ناسازگار → None (صفر اثر، صفر پاسخ)."""
        if not self._wired() or not isinstance(u, dict):
            return None
        if not self._is_owner(u):
            return None                              # سکوتِ کامل برای غیرمالک
        # ── سیاستِ ورودی (VQ-TG-GAP-INPUT-001، رأیِ مالک ۲۰۲۶-۰۷-۳۰ گزینهٔ A) ──
        # تا امروز فقط **خروجی** سیاست داشت، پس گروه فرمانِ هسته‌ای می‌گرفت حتی
        # وقتی هیچ خروجیِ هسته‌ای به آن نمی‌رفت. این‌جا ورودی هم گیت می‌شود:
        # General/تاپیکِ ناشناخته و فرمانِ هسته‌ای در گروه → deny + هدایت به DM.
        # فلگ ندارد چون قرارداد canonical است؛ ولی fail-**open** است در یک نکته:
        # نبودِ ماژول یا هر استثنا ⇒ رفتارِ قبلی. دلیل: این گیت یک لایهٔ
        # **باریک‌کننده** است، و اگر خودش بشکند نباید کلِ مرکز را کر کند.
        #
        # WARN: مالکیت این‌جا دوباره استنتاج نمی‌شود — خطِ بالا با
        # `self._is_owner(u)` از قبل گیت کرده. اگر `owner_chat_id` در
        # دسترس نباشد (کلاینتِ ناپیکربندی/تستی) گیت **رد** می‌شود، نه
        # اینکه همه‌چیز deny شود: نسخهٔ اول همین را نداشت و ۱۵ تستِ مرکز
        # را قرمز کرد، چون سیاست مالک را نمی‌شناخت و همهٔ پیام‌ها را
        # می‌بلعید. «نمی‌دانم مالک کیست» نباید به «همه ممنوع» ترجمه شود
        # وقتی لایهٔ بالادست از قبل جواب داده است.
        try:
            import input_surface_policy as _isp
            _own = getattr(self._client, "owner_chat_id", None)
            if _own is None:
                raise RuntimeError("owner-unresolvable")
            _cfg = _load_config()
            _d = _isp.classify(
                u, bot_role="outer", owner_id=_own,
                group_id=_cfg.get("chat_id"),
                topics=_cfg.get("topics") if isinstance(_cfg.get("topics"), dict) else {})
            if not _d.get("allow"):
                _t = _isp.redirect_text(_d)
                if _t:
                    _m = (u.get("message")
                          or (u.get("callback_query") or {}).get("message") or {})
                    try:
                        self._client.send(_t, chat_id=(_m.get("chat") or {}).get("id"),
                                          topic_id=_m.get("message_thread_id"))
                    except Exception:  # noqa: BLE001 — هدایت هرگز مرکز را نمی‌کشد
                        pass
                return {"kind": "input-policy", "mode": _d.get("mode"),
                        "reason": _d.get("reason")}
            # ── «بساز: …» → صفِ ساختِ خود (رأیِ مالک ۰۷-۳۰) ──────────────────
            # قبل از مامور، چون مامور متنِ آزاد را clarify می‌کند و این یک
            # نیتِ صریح است. فقط Outer DM (تصمیمِ core_conversation)؛ از گروه
            # ساختاراً نمی‌رسد. هیچ اجرایی این‌جا نیست — فقط صف.
            try:
                _mgb = u.get("message")
                _txb = str((_mgb or {}).get("text") or "").strip()
                if _txb and _d.get("mode") == "core_conversation":
                    import build_cmd as _bc
                    if _bc.is_build_request(_txb):
                        _body = _bc.strip_prefix(_txb)
                        if not _body:
                            # «بساز:» ِ تنها. حدس نمی‌زنیم — می‌پرسیم.
                            _res = {"ok": False, "id": None,
                                    "note": ("چه چیزی بسازم؟ مسیرِ فایل را هم "
                                             "بنویس.\nمثال: <code>بساز: یک تابع "
                                             "شمارشِ لید به _ops/cortex/"
                                             "improve.py اضافه کن</code>")}
                        else:
                            _res = _bc.enqueue(_body)
                        _bt = (f"📥 کارِ ساخت ثبت شد: <code>{_res['id']}</code>\n"
                               f"{_res['note']}") if _res.get("ok") else \
                            f"ثبت نشد — {_res.get('note')}"
                        try:
                            self._client.send(
                                _scrub(_bt),
                                chat_id=(_mgb.get("chat") or {}).get("id"),
                                keyboard=[[{"text": "🛠 وضعیتِ حلقه",
                                            "callback_data": "hm:build"}]])
                        except Exception:  # noqa: BLE001
                            pass
                        return {"kind": "build-task", "ok": _res.get("ok"),
                                "task": _res.get("id")}
            except Exception:  # noqa: BLE001 — صفِ شکسته = مسیرِ قبلی، نه سکوت
                pass
            # ── مامور (owner_console) — فقط با تصمیمِ مجازِ core_conversation ──
            # وصل طبقِ HANDOFF-TO-TELEGRAM-SENIOR بعد از سبزیِ ۱۹+۴ سنجه و ۹
            # جهشِ قرمز. adapter مالکیت/سطح را دوباره حدس نمی‌زند — همان تصمیمِ
            # _d را می‌گیرد (identity-strict).
            # یک انحرافِ سنجیده از اسکریپتِ handoff: پاسخِ `clarify` بلعیده
            # نمی‌شود — متنِ آزادی که مامور نمی‌فهمد به مسیرِ گفت‌وگوی کاملِ
            # موجود (مغز) می‌افتد؛ وگرنه وصلِ مامور، چتِ آزادِ مصوبِ Outer DM
            # را می‌کشت. دکمه‌های oc:* هم این‌جا handler می‌گیرند — بستنِ
            # کارتِ مردهٔ VQ-OWNER-CONSOLE-001.
            try:
                from owner_console import telegram_adapter as _oc
                _cb = u.get("callback_query")
                if isinstance(_cb, dict) and str(_cb.get("data") or "").startswith("oc:"):
                    _r = _oc.handle_callback(str(_cb.get("data") or ""),
                                             surface_decision=_d)
                    if _r.get("handled") and _r.get("reply"):
                        return self._send_console_reply(_r["reply"], _cb)
                _mg = u.get("message")
                if isinstance(_mg, dict) and str(_mg.get("text") or "").strip():
                    _r = _oc.handle_message(str(_mg.get("text") or ""),
                                            surface_decision=_d)
                    _rep = _r.get("reply") if _r.get("handled") else None
                    if _rep and _rep.get("kind") != "clarify":
                        return self._send_console_reply(_rep, {"message": _mg})
            except Exception:  # noqa: BLE001 — مامورِ شکسته = مسیرِ قبلی، نه سکوت
                pass
            # ── مدلِ Task ِ گروهِ پاها (رأیِ مالک ۰۷-۳۰ شب + ۰۷-۳۱) ─────────
            # «هر پیامِ تو = یک کار برای همان پا» — با سه استثنای صریح، به
            # همین ترتیب: (الف) ریپلای به کارتِ 🚧 = رفعِ مانعِ همان کار؛
            # (ب) ۹ فرمانِ طبیعیِ نسخهٔ اول (leg_commands، تطابقِ کامل) =
            # همان اثرِ دکمه‌های ممیزی‌شده؛ (ج) پیشوندِ «به صف اضافه کن».
            # سؤال همان لحظه از مسیرِ موجودِ چت جواب می‌گیرد؛ باقی → TASK ِ
            # صف‌شده + کارتِ [شروع][لغو]. اجرا فقط بعدِ تپِ «شروع»، در beat،
            # با مغزِ read-only — هیچ اثرِ بیرونی از گروه ممکن نیست.
            try:
                if _d.get("mode") == "leg_scoped" and _d.get("leg"):
                    _mg2 = u.get("message")
                    _tx = str((_mg2 or {}).get("text") or "").strip()
                    # ورودیِ غیرمتنی (فاز ۲ بند ۸): عکس/فایل/صدا/لوکیشن در
                    # تاپیکِ پا = کارِ همان پا، با برچسبِ نوع + caption.
                    # مستقیم صف می‌شود (سؤال/فرمان روی رسانه معنا ندارد —
                    # مغزِ متنی تصویر را نمی‌بیند و حدس نمی‌زنیم). ارسالِ
                    # فایل به‌تنهایی هیچ اقدامِ بیرونی ندارد — موتور read-only.
                    if not _tx and isinstance(_mg2, dict):
                        _mtx = self._media_task_text(_mg2)
                        if _mtx:
                            import leg_tasks as _lt
                            _task = _lt.add(_d["leg"], _mtx)
                            if _task:
                                try:
                                    self._client.send(
                                        _scrub(_lt.intake_text(_task)),
                                        chat_id=(_mg2.get("chat") or {}).get("id"),
                                        topic_id=_mg2.get("message_thread_id"),
                                        keyboard=_lt.intake_keyboard(
                                            _d["leg"], _task))
                                except Exception:  # noqa: BLE001
                                    pass
                                self._refresh_leg_card(_d["leg"])
                                return {"kind": "leg-task", "media": True,
                                        "task": _task["id"], "leg": _d["leg"]}
                    if _tx and not _tx.startswith("/"):
                        import leg_commands as _lc
                        import leg_tasks as _lt
                        _leg = _d["leg"]
                        _ch2 = (_mg2.get("chat") or {}).get("id")
                        _th2 = _mg2.get("message_thread_id")
                        _rt = str(((_mg2.get("reply_to_message") or {})
                                   .get("text")) or "")
                        _cmd = _lc.classify(_tx)
                        if (_cmd is None and "🚧" in _rt
                                and not _lt.is_question(_tx)):
                            _mrt = re.search(r"TASK-\d+", _rt)
                            _res = (_lt.resolve_blocked(_leg, _mrt.group(0),
                                                        _tx)
                                    if _mrt else None)
                            if _res:
                                try:
                                    self._client.send(_scrub(
                                        f"🔓 مانع {_res['id']} برطرف شد — "
                                        "ادامه می‌دهم."),
                                        chat_id=_ch2, topic_id=_th2)
                                except Exception:  # noqa: BLE001
                                    pass
                                self._refresh_leg_card(_leg)
                                return {"kind": "leg-task-unblock",
                                        "task": _res["id"], "leg": _leg}
                        if _cmd is not None:
                            _b2, _k2 = self._exec_leg_command(_cmd, _leg)
                            try:
                                self._client.send(_scrub(_b2), chat_id=_ch2,
                                                  topic_id=_th2, keyboard=_k2)
                            except Exception:  # noqa: BLE001
                                pass
                            self._refresh_leg_card(_leg)
                            return {"kind": "leg-cmd", "cmd": _cmd,
                                    "leg": _leg}
                        # «هدف روزانه N» — KPI ِ همان پا (بند ۱۳). رأیِ مالک
                        # در تاپیکِ خودِ پا = مجوزِ همان پا؛ برگشت‌پذیر.
                        _kpi = _lc.parse_kpi_set(_tx)
                        if _kpi is not None:
                            _cfgk = _load_config()
                            _kd = _cfgk.setdefault("kpi_daily", {})
                            if isinstance(_kd, dict):
                                _kd[_leg] = int(_kpi)
                                _save_config(_cfgk)
                            try:
                                self._client.send(_scrub(
                                    f"🎯 هدف روزانهٔ این پا: {_kpi} — روی "
                                    "کارت دیده می‌شود."),
                                    chat_id=_ch2, topic_id=_th2)
                            except Exception:  # noqa: BLE001
                                pass
                            self._refresh_leg_card(_leg)
                            return {"kind": "leg-cmd", "cmd": "kpi-set",
                                    "leg": _leg, "kpi": _kpi}
                        _enq = _lc.strip_enqueue_prefix(_tx)
                        if _enq is not None:
                            # «این را» بدونِ متن = پیامِ ریپلای‌شده؛ هیچ‌کدام
                            # نبود ⇒ صادقانه بپرس، حدس نزن.
                            _tx = _enq or _rt.strip()
                            if not _tx:
                                try:
                                    self._client.send(_scrub(
                                        "چه چیزی را به صف اضافه کنم؟ متن را "
                                        "بنویس یا به پیامش ریپلای کن."),
                                        chat_id=_ch2, topic_id=_th2)
                                except Exception:  # noqa: BLE001
                                    pass
                                return {"kind": "leg-cmd",
                                        "cmd": "enqueue-empty", "leg": _leg}
                        if not _lt.is_question(_tx):
                            _task = _lt.add(_leg, _tx)
                            if _task:
                                try:
                                    self._client.send(
                                        _scrub(_lt.intake_text(_task)),
                                        chat_id=_ch2, topic_id=_th2,
                                        keyboard=_lt.intake_keyboard(
                                            _leg, _task))
                                except Exception:  # noqa: BLE001
                                    pass
                                self._refresh_leg_card(_leg)
                                return {"kind": "leg-task",
                                        "task": _task["id"],
                                        "leg": _leg}
            except Exception:  # noqa: BLE001 — صفِ شکسته = مسیرِ قبلی، نه سکوت
                pass
        except Exception:  # noqa: BLE001 — گیتِ شکسته = رفتارِ قبلی، نه سکوت
            pass
        cbq = u.get("callback_query")
        if isinstance(cbq, dict):
            return self._handle_callback(cbq)
        msg = u.get("message")
        if isinstance(msg, dict):
            return self._handle_message(msg)
        return None

    def _handle_message(self, msg: dict) -> "dict | None":
        text = str(msg.get("text") or "").strip()
        if not text:
            return None
        cmd = text.split()[0].split("@")[0].lower()
        chat_id = (msg.get("chat") or {}).get("id")  # پاسخ به همان‌جا که پرسید

        # ۲۰۲۶-۰۷-۲۷ — عبارت‌های مجوزِ قرارداد (`OWNER_AUTH: …`) تا امروز در
        # **هیچ خطی از کد** شناخته نمی‌شدند. یعنی اگر مالک نیمه‌شب مجوزی می‌داد و
        # هیچ ایجنتی بیدار نبود، آن جمله تبخیر می‌شد: تصمیمِ مالک فرّارترین دادهٔ
        # کلِ سیستم بود. حالا ثبت می‌شود.
        #
        # ⚠️ **ثبت، نه اجرا.** فلیپِ فلگ و کامیت و ریستارت عملِ استقرارند نه پیام؛
        # ماشه‌کردنشان با متنِ چت یعنی ساختنِ یک مجریِ خودکار که ورودی‌اش
        # جعل‌شدنی و فورواردشدنی است.
        if "OWNER_AUTH" in text.upper():
            try:
                import owner_auth_log as _oa
                rec = _oa.record(text, chat_ok=True, source="tg")
                if rec is not None:
                    # ⚠️ نسخهٔ اولِ همین شاخه (چند ساعت پیش، همین جلسه) جواب را
                    # **می‌ساخت و دور می‌ریخت** — هیچ `send`ی نداشت. یعنی مالک
                    # مجوز می‌داد و بات ساکت بود؛ دقیقاً همان «انجام شد ولی اثری
                    # ندارد» که کلِ این جلسه دربارهٔ آن بود، این بار در کدِ خودم.
                    _ack = _oa.ack(rec)
                    _mid = None
                    try:
                        _mid = self._client.send(
                            _scrub(_ack), chat_id=chat_id,
                            topic_id=self._reply_thread(msg))
                    except Exception:  # noqa: BLE001
                        pass
                    return {"kind": "owner-auth", "text": _ack,
                            "sent": _mid is not None,
                            "chat_id": chat_id, "auth_kind": rec.get("kind")}
            except Exception:  # noqa: BLE001 — ثبت نشدن نباید پیام را بخورد
                pass
        handlers = {
            "/now": lambda: self._status_text() or "🐙 هنوز چیزی برای گفتن ندارم.",
            "/budget": self._budget_text,
            "/revenue": self._revenue_text,
            "/missions": lambda: self._page("ms"),
            "/menu": lambda: self._page("menu"),
            "/start": lambda: self._page("menu"),
            # 2026-07-25 live path — full text after command is passed through
            "/live": lambda: self._live_cmd(text),
            "/id": lambda: self._live_cmd(text),
            "/eq": lambda: self._live_cmd(text),
            "/box": lambda: self._live_cmd(text),
            "/code": lambda: self._live_cmd(text),
            "/doctrine": lambda: self._live_cmd(text),
            # ۲۰۲۶-۰۷-۲۷ — مذاکره **هیچ راهِ شروعی نداشت**: `make_offer` تنها از
            # شاخهٔ شرط‌گذاری صدا زده می‌شد، پس مالک هرگز پیشنهادِ اولی نمی‌گرفت و
            # کلِ حلقه نامرئی بود. شروع عمداً **دستِ مالک** است نه یک beat: تا وقتی
            # نسنجیده‌ایم شرط‌های او واقعاً پیشنهادها را بهتر می‌کند یا نه، ارگانیسم
            # نباید خودش شروع به چانه‌زدن کند.
            "/deal": lambda: self._deal_cmd(),
            # ۲۰۲۶-۰۷-۲۷ (رأیِ مالک «کامل تا مرزِ ارسال») — موتورِ قیمت‌گذاری
            # کامل نوشته شده بود و **صفر مصرف‌کننده** داشت. این تنها راهِ
            # کوت‌گرفتن در تلگرام است؛ ارسال همچنان یک تپِ جداست.
            "/lead": lambda: self._quote_cmd(text),
            # «اول فقط منقضی‌ها را نشانم بده» (رأیِ مالک ۲۰۲۶-۰۷-۲۷): از ۴۸ رأیِ
            # باز، آن‌هایی که واقعیت **از قبل جوابشان را داده** — با شاهدِ فیزیکی.
            # فایل هرگز بازنویسی نمی‌شود؛ بستن دستِ مالک است (قانونِ اساسی §۷).
            "/verdicts": lambda: self._verdicts_cmd(),
            # نقطهٔ کورِ ۱۳۴: کارتِ پولی که در نیمهٔ راه یخ زده. فقط نشان می‌دهد —
            # بستنِ کارتِ پولی هرگز خودکار نیست.
            "/stuck": lambda: self._stuck_cmd(),
            # فهرستِ خودکشف: هر ماژولی که کارتِ بی‌آرگومان دارد این‌جا می‌آید،
            # بدونِ اینکه کسی لازم باشد این فایل را دست بزند. شکاف را ساختاری
            # می‌بندد نه موردی.
            "/x": lambda: self._capabilities_cmd(),
            "/توان": lambda: self._capabilities_cmd(),
            # D3b (۲۰۲۶-۰۷-۲۷) — مالک واقعیتِ بازار را می‌گوید. `funnel_store`
            # کامل نوشته شده بود و سربرگش خودش می‌گفت «صفر caller تا wiring
            # بعداً»؛ آن wiring هرگز ساخته نشد، پس ارگانیسمی که مأموریتش پول
            # است هیچ‌وقت نمی‌فهمید کدام لید برنده شد. صفر پول، صفر ارسال.
            "/won": lambda: self._funnel_cmd(text),
            "/lost": lambda: self._funnel_cmd(text),
            "/paid": lambda: self._funnel_cmd(text),
            "/sent": lambda: self._funnel_cmd(text),
            "/replied": lambda: self._funnel_cmd(text),
            "/meeting": lambda: self._funnel_cmd(text),
            "/quote": lambda: self._funnel_cmd(text),
            "/funnel": lambda: self._funnel_cmd(""),
            "/رفتار": lambda: self._live_cmd(text),
            "/کد": lambda: self._live_cmd(text),
            # ۲۰۲۶-۰۷-۲۸ — خودنگری. منطق عمداً در `introspect_cmd.py`
            # است نه این‌جا: این فایل ۱۳۰ کیلوبایت و پرترافیک است، و
            # کوچک‌ترین دیف کم‌ریسک‌ترین دیف است. هر چهار فقط‌خواندنی‌اند.
            "/flags": lambda: _introspect("flags"),
            "/trace": lambda: _introspect("trace", text),
            "/scan": lambda: _introspect("scan"),
            "/insight": lambda: _introspect("insight"),
        }
        # Menu v2 (پشتِ OCTOPUS_WIRE_MENU_V2): فقط با فلگِ روشن /panel اضافه می‌شود.
        # flag خاموش → /panel در handlers نیست → مسیرِ «command ناشناس» امروز (return None). parity.
        _m2 = self._menu2()
        if _m2 is not None and _m2.enabled():
            handlers["/panel"] = _m2.render_menu
        # زیر-OSِ Mining (پشتِ OCTOPUS_WIRE_MINING_UI): فقط با فلگِ روشن /mining اضافه
        # می‌شود. flag خاموش → در handlers نیست، و چون در _CENTRE_GATED هست پل هم آن را
        # به باتِ ارگانیسم نمی‌برد → مسیرِ «command ناشناس» امروز. parity.
        _mo = self._mining_ui()
        if _mo is not None:
            handlers["/mining"] = _mo.render_menu
        fn = handlers.get(cmd)
        # ۲۰۲۶-۰۷-۲۷ — **پلِ دو-باتی.** یافتهٔ دبل‌چکِ همان روز: ۳۲ دستوری که
        # کارت‌ها صریحاً به مالک پیشنهاد می‌دهند («/heart set …»، «/doctor focus …»،
        # «/brain guide …»، «۲۵۲ تراکنش منتظرِ توست — /review») فقط در روترِ باتِ
        # ارگانیسم‌اند. و آن بات `TELEGRAM_ALLOWED_CHAT_IDS` ندارد، پس پیامِ گروه را
        # **رد می‌کند** و offset را جلو می‌برد.
        #
        # نتیجهٔ زیسته: مالک ساعت‌ها در گروه حرف زد و «متوجه نشدم» گرفت — و در آن ۳۲
        # تا `/panic` و `/stop` هم بودند، یعنی کلیدهای اضطراری از جایی که او
        # می‌خواند در دسترس نبودند.
        #
        # پل، نه ادغام: `handle_command` **در همین پروسه** صدا زده می‌شود (نه
        # pollerِ دوم، پس ریسکِ 409 صفر). و `from_id` واقعی پاس داده می‌شود تا
        # گیت‌های owner-only خودِ آن تابع **واقعاً شلیک کنند** — پیش‌فرضِ None
        # آن‌ها را رد می‌کرد، پس این مسیر از فراخوانِ برنامه‌ای هم سخت‌گیرتر است.
        # استثنا: دستورهایی که **خودِ مرکز** پشتِ فلگ گیت کرده. «ناشناس بودن»شان
        # وقتی فلگ خاموش است یک قرارداد است نه یک اتفاق — و گاردِ parity همان
        # روز گرفتش. پل نباید تصمیمِ فلگ را دور بزند.
        # سقف‌دار و مستند؛ اگر این مجموعه رشد کند، پل دیگر عام نیست.
        if fn is None and cmd.startswith("/") and cmd not in _CENTRE_GATED:
            _bridged = self._bridge_to_organism(text, chat_id, msg)
            if _bridged is not None:
                return _bridged
        if fn is None:
            # پیامِ آزادِ مالک = پرسش/دستورِ نرم. اجرای مستقیمِ مخرب هرگز؛ فقط
            # نگاشتِ intent → کارت/دکمهٔ عملگرا یا پاسخِ آرام (stdlib-only، بدون LLM).
            if not text.startswith("/"):
                # اتاقِ چت اول: اگر جملهٔ فارسی صریحاً یک کارمند را نشان داد،
                # همان جواب می‌دهد. خاموش یا بی‌تطابق → مسیرِ امروز، بی‌تغییر.
                _room = self._chat_room(msg, text)
                if _room is not None:
                    return _room
                return self._handle_ask(msg, text)
            return None                    # قراردادها: command ناشناس نادیده
        try:
            out = fn()
            txt, kb = out if isinstance(out, tuple) else (str(out or ""), None)
            mid = self._client.send(_scrub(txt), chat_id=chat_id, keyboard=kb,
                                    topic_id=self._reply_thread(msg))
        except Exception as _e:  # noqa: BLE001
            # ۲۰۲۶-۰۷-۲۷ — این `except` بی‌صدا بود: نه پیامی به مالک، نه آلارم،
            # نه ردی در لاگ. و چون آفستِ update به‌هرحال جلو می‌رفت، هرگز retry
            # هم نمی‌شد. یعنی مالک `/budget` می‌زد، هیچ جوابی نمی‌گرفت، و
            # **سکوت را «چیزی نبود» می‌خواند** در حالی که کد ترکیده بود.
            mid = None
            try:
                opslib.alert([f"tg-center: دستورِ {cmd} شکست — "
                              f"{type(_e).__name__}"])
            except Exception:  # noqa: BLE001
                pass
            try:
                self._client.send(
                    f"⚠️ <code>{cmd}</code> خطا داد ({type(_e).__name__}).\n"
                    "▸ سکوت یعنی خطا، نه «چیزی نبود».",
                    chat_id=chat_id, topic_id=self._reply_thread(msg))
            except Exception:  # noqa: BLE001
                pass
        return {"kind": cmd.lstrip("/"), "sent": mid is not None}

    def _verdicts_cmd(self):
        """رأی‌هایی که دیگر سؤال نیستند — فقط‌خواندنی، $۰، بدونِ تماسِ مغز."""
        try:
            import verdict_probe as _vp
            return _vp.card()
        except Exception:  # noqa: BLE001
            return "🗳 صفِ رأی در دسترس نیست."

    def _stuck_cmd(self):
        """پرداخت‌های نیمه‌کاره — فقط‌خواندنی، $۰، هیچ گذارِ پولی."""
        try:
            import stuck_money as _sm
            return _sm.card()
        except Exception:  # noqa: BLE001
            return "💰 آشکارسازِ پرداختِ نیمه‌کاره در دسترس نیست."

    def _capabilities_cmd(self):
        """`/x` → فهرستِ هر چیزی که ارگانیسم می‌تواند نشان دهد، با دکمه."""
        try:
            import capability_registry as _cr
            return _cr.card(), _cr.keyboard(0)
        except Exception:  # noqa: BLE001
            return "🗂 فهرستِ توانایی‌ها در دسترس نیست."

    def _bridge_to_organism(self, text: str, chat_id, msg: dict):
        """دستورِ ناشناخته در مرکز → روترِ باتِ ارگانیسم، در همین پروسه.

        هیچ گاردی دور زده نمی‌شود: `handle_command` خودش owner-only را می‌سنجد و
        `from_id` واقعی را می‌گیرد. ناشناخته برای هر دو → None → مسیرِ امروز."""
        try:
            import sys as _s
            from pathlib import Path as _P
            _b = str(_P(__file__).resolve().parent.parent / "budget")
            if _b not in _s.path:
                _s.path.insert(0, _b)
            import approval_channel as _ac
            ch = _ac.TelegramApprovalChannel()
            out = ch.handle_command(text, chat_id=chat_id,
                                    from_id=(msg.get("from") or {}).get("id"))
        except Exception:  # noqa: BLE001 — پل هرگز مسیرِ مرکز را نمی‌شکند
            return None
        if not out:
            return None
        body, kb = (out if isinstance(out, tuple) else (out, None))
        if isinstance(body, dict):
            # ⚠️ ۲۰۲۶-۰۷-۲۸ — این خط فقط `keyboard` را می‌خواند، ولی روترِ
            # ارگانیسم `reply_markup` برمی‌گرداند (approval_channel: `/queue`
            # ۱۰ ردیف، `/doctor` ۶، `/money` ۵، `/organs` ۴، `/school` ۳،
            # `/heart` ۱ — اندازه‌گیری‌شده). یعنی **۲۹ ردیف دکمه** بی‌صدا دور
            # ریخته می‌شد: متن می‌رسید، دکمه‌ها نه، و هیچ خطایی هم نبود چون
            # `None` یک مقدارِ معتبر برای keyboard است.
            #
            # هر دو نام پذیرفته می‌شود چون دو تولیدکننده با دو قرارداد وجود
            # دارد و یکی‌کردنشان تغییرِ بزرگ‌تری است؛ این‌جا فقط مصرف‌کننده
            # سخاوتمند می‌شود. `test_tg_bridge_keyboard` هر دو را قفل می‌کند.
            body, kb = (body.get("text", ""),
                        body.get("reply_markup") or body.get("keyboard"))
        try:
            mid = self._client.send(_scrub(str(body)), chat_id=chat_id, keyboard=kb,
                                    topic_id=self._reply_thread(msg))
        except Exception:  # noqa: BLE001
            mid = None
        return {"kind": "bridged", "cmd": text.split()[0], "sent": mid is not None}

    def _funnel_cmd(self, text: str):
        """`/won lead-123` → ثبتِ نتیجهٔ بازار. هرگز پول، هرگز ارسال."""
        try:
            import funnel_cmd as _fc
            return _fc.handle(text)
        except Exception:  # noqa: BLE001
            return "📈 قیفِ لید در دسترس نیست."

    def _quote_cmd(self, text: str):
        """`/lead …` → کارتِ قیمتِ واقعی. هرگز ارسال نمی‌کند."""
        try:
            import quote_cmd as _q
            return _q.quote(text, leg=getattr(self, "_leg", None))
        except Exception:  # noqa: BLE001
            return "🎨 کارتِ قیمت در دسترس نیست."

    def _deal_cmd(self):
        """`/deal` — یک پیشنهادِ شرط‌دار از اهدافِ خودِ اختاپوس.

        اگر پیشنهادی از قبل باز است، همان را دوباره نشان می‌دهد به‌جای ساختنِ
        دومی: `MAX_OPEN` در negotiate هست چون «بیش از دو پیشنهادِ باز = فشار روی
        مالک، نه مذاکره»."""
        try:
            import negotiate as _ng
            if not _ng.enabled():
                return ("🤝 مذاکره خاموش است.\n"
                        "▸ نکنی: چیزی عوض نمی‌شود — فلگش را روشن کن و مرکز را ری‌استارت.")
            openi = _ng.open_offers()
            if openi:
                return _ng.card(openi[0])
            r = _ng.make_offer()
            if r.get("ok"):
                return _ng.card(r["offer"])
            why = {"too-many-open": "دو پیشنهادِ باز داری — اول به آن‌ها جواب بده",
                   "not-a-paid-brain": "مغزِ گران الان در دسترس نیست",
                   "bad-format": "مغز جوابِ خارج از قرارداد داد — چیزی ثبت نشد",
                   "no-answer": "مغز جواب نداد"}.get(
                       str(r.get("reason") or "").split(":")[0])
            if str(r.get("reason") or "").startswith(("too-soon", "daily-cap")):
                why = "سهمیهٔ گفتگوی امروز پر است — چند دقیقهٔ دیگر"
            return f"🤝 الان پیشنهادی ندارم — {why or r.get('reason')}"
        except Exception:  # noqa: BLE001
            return "🤝 مذاکره در دسترس نیست."

    def _chat_room(self, msg: dict, text: str) -> "dict | None":
        """اتاقِ چت — فارسیِ ساده → کارمندِ درست. `None` یعنی دست نزدم.

        رأیِ مالک ۲۰۲۶-۰۷-۲۸: «یک جا در گروه بگذار از طریقش همه پاها را کنترل
        کنم … تعامل‌ها را چت‌گونه می‌خواهم» — و اندازه‌گیریِ همان روز نشان داد
        ۶۱ فرمان تبلیغ می‌شد که ۸ تایشان در هیچ باتی وجود نداشت. مشکل نبودِ
        کارمند نبود، نبودِ در بود.

        سه تصمیمِ عمدی:

        · **بازپخش، نه پیاده‌سازیِ دوم.** فرمانِ کارمند به‌عنوان یک پیامِ تازه
          به همین تابع برمی‌گردد. اگر به‌جایش handler را مستقیم صدا می‌زدم،
          کلوژرِ `text` هنوز متنِ فارسیِ مالک را می‌بست و `_funnel_cmd(text)`
          آرگومان را از جملهٔ فارسی می‌خواند — یک باگِ بی‌صدا. بازگشت بی‌پایان
          ممکن نیست: متنِ ساخته‌شده با `/` شروع می‌شود و این شاخه فقط برای
          متنِ غیر-`/` است. `_depth` گاردِ دومِ صریح است.
        · **مبهم = می‌پرسد.** مسیریابیِ غلطِ بی‌صدا بدترین حالت است؛ جوابِ
          کارمندِ اشتباه شبیهِ جوابِ درست به نظر می‌رسد.
        · **بدونِ تطابق = هیچ.** به `_handle_ask` امروزی می‌افتد، دست‌نخورده.
        """
        try:
            import chat_room as _cr
        except Exception:  # noqa: BLE001
            return None
        if not _cr.enabled():
            return None
        # اتاق بخشی از سؤال است (رأیِ مالک: «گروه بشه پایگاهِ پروژه‌ها و پاها»).
        # `_topic_key` از ۰۷-۲۶ همین را می‌دانست و فقط اتاقِ آینه و مغزِ پولی
        # مصرفش می‌کردند؛ برای پاها هرگز وصل نشده بود.
        #
        # ⚠️ جدا و دفاعی، عمداً: نسخهٔ اولِ همین چند خط `_topic_key` را داخلِ
        # همان `try`ی گذاشته بود که خطایش `return None` می‌داد — یعنی یک نقصِ
        # کوچک در **تشخیصِ اتاق** کلِ اتاقِ چت را بی‌صدا خاموش می‌کرد. تست‌های
        # سیم‌کشی همان لحظه گرفتندش. نشناختنِ اتاق باید یعنی «اتاق ندارم»، نه
        # «اصلاً حرف نزن».
        room = ""
        try:
            room = self._topic_key(msg) or ""
        except Exception:  # noqa: BLE001
            room = ""
        try:
            hit = _cr.classify(text, room=room)
        except TypeError:
            hit = _cr.classify(text)          # نسخهٔ قدیمیِ ماژول → رفتارِ قبلی
        except Exception:  # noqa: BLE001
            return None                       # اتاقِ چت هرگز مرکز را نمی‌شکند
        chat_id = (msg.get("chat") or {}).get("id")
        if hit.get("tied"):
            try:
                mid = self._client.send(_scrub(_cr.ask_which(hit["tied"])),
                                        chat_id=chat_id,
                                        topic_id=self._reply_thread(msg))
            except Exception:  # noqa: BLE001
                mid = None
            return {"kind": "chat-room-ask", "sent": mid is not None,
                    "tied": hit["tied"]}
        cmd = hit.get("command")
        if not cmd:
            return None
        if int(msg.get("_chat_room_depth") or 0) >= 1:
            return None
        out = self._handle_message({**msg, "text": cmd, "_chat_room_depth": 1})
        if out is None and hit.get("match"):
            # فرمانِ اختصاصی خاموش است — ولی کارتِ عمومیِ همان اندام زنده است.
            #
            # ۲۰۲۶-۰۷-۲۸، بعد از آزمونِ زندهٔ مالک: «چطوره؟» در بازوی معدن درست
            # مسیریابی شد و کارتِ «خاموش است» گرفت. مالک گفت «دکمه نداشت» —
            # و حق داشت: آن کارت یک **بن‌بست** بود. می‌گفت خاموشم و راهی نشان
            # نمی‌داد، یعنی همان تجربه‌ای که کلِ هفته ازش شکایت داشت، فقط
            # مؤدبانه‌تر.
            #
            # این fallback عام است نه وصلهٔ ماینینگ: هر پایی که فرمانِ
            # اختصاصی‌اش گیت باشد، جوابِ واقعیِ `/organs <slug>` را می‌گیرد.
            # اگر آن هم نبود، تازه کارتِ خاموشی می‌آید.
            # ⚠️ فقط برای **پاها**. اگر فرمانِ یک مغز (doctor/heart/money/…)
            # گیت شود، `/organs doctor` جوابِ «اندامی به این نام نیست» می‌دهد —
            # که از بن‌بست هم گیج‌کننده‌تر است، چون یک جوابِ *غلط* است نه یک
            # سکوت. `LEGS` دقیقاً همان هفت اندامِ رجیستری است.
            _alt = f"/organs {hit['match']}"
            if _alt != cmd and hit["match"] in getattr(_cr, "LEGS", {}):
                out = self._handle_message(
                    {**msg, "text": _alt, "_chat_room_depth": 1})
                if out is not None:
                    return {**out, "routed_from": "chat-room-fallback",
                            "gated": cmd, "served": _alt}
        if out is None:
            # کارمند هست ولی الان جواب نداد — فرمان پشتِ فلگ گیت شده
            # (`_CENTRE_GATED`) یا روتر نشناختش. **سکوت ممنوع**: کلِ شکایتِ مالک
            # از تلگرام همین بود، «گمراه‌کننده و بی‌کاره». اینجا با یک لیستِ
            # هاردکدِ فرمان‌های گیت‌شده نمی‌جنگم — هر مسیرِ ساکتی، هر وقت،
            # همین جواب را می‌گیرد. نمونهٔ زنده: `/mining` پشتِ
            # `OCTOPUS_WIRE_MINING_UI`؛ «ماینینگ چطوره» بی این شاخه هیچ می‌شد.
            try:
                mid = self._client.send(
                    _scrub(f"🔇 <b>{hit.get('display','')}</b> الان جواب نمی‌دهد.\n"
                           f"▸ <code>{cmd}</code> پشتِ یک فلگِ خاموش است.\n"
                           "<i>سکوت را «چیزی نبود» نخوان — این‌جا خاموشی است، "
                           "نه نبودِ کارمند.</i>"),
                    chat_id=chat_id, topic_id=self._reply_thread(msg))
            except Exception:  # noqa: BLE001
                mid = None
            return {"kind": "chat-room-dark", "sent": mid is not None,
                    "command": cmd}
        return {**out, "routed_from": "chat-room", "hits": hit.get("hits", [])}

    def _handle_ask(self, msg: dict, text: str) -> dict:
        """پرسش‌وپاسخِ زندهٔ مالک با اختاپوس، بدون LLM و بدون اجرای مبهم.

        این لایه از intent.classify (ماژولِ جدا) برای تشخیصِ نیت استفاده می‌کند،
        سپس intent را به کارت/دکمهٔ عملگرا نگاشت می‌کند. هرگز اجرای مستقیمِ مخرب؛
        مکث/ادامه فقط دکمهٔ lg:*؛ scan فقط کارتِ map:start؛ تأییدها فقط کارتِ ap.

        ارتقا از LLM پشتِ فلگِ OCTOPUS_TG_LLM_ASK=1 در آینده بدونِ لمسِ این لایه
        ممکن است (intent.classify را می‌توان با wrapperِ LLM عوض کرد)."""
        chat_id = (msg.get("chat") or {}).get("id")
        # متنِ شرط، بعد از دکمهٔ «✍️ شرط بگذار». اولویتش بالاتر از هر مسیرِ دیگری
        # است چون مالک دارد جوابِ یک سؤالِ مشخص را می‌دهد، نه فرمانِ تازه.
        _await = getattr(self, "_awaiting_counter", None)
        if _await:
            self._awaiting_counter = None
            try:
                import negotiate as _ng
                r = _ng.respond(_await, "counter", counter=text)
                if r.get("ok"):
                    rev = _ng.make_offer(revise_of=_await)
                    if rev.get("ok"):
                        _t, _k = _ng.card(rev["offer"])
                        mid = self._client.send(_scrub(_t), chat_id=chat_id,
                                                keyboard=_k,
                                                topic_id=self._reply_thread(msg))
                        return {"kind": "negotiate_revised", "sent": mid is not None}
                    self._client.send(
                        _scrub("✍️ شرطت ثبت شد. پیشنهادِ بازنگری‌شده الان نشد — "
                               f"({_scrub(str(rev.get('reason'))[:40])}) بعداً می‌آید."),
                        chat_id=chat_id, topic_id=self._reply_thread(msg))
                    return {"kind": "negotiate_counter", "revised": False}
            except Exception:  # noqa: BLE001
                pass
        # ── اتاقِ آینه (۲۰۲۶-۰۷-۲۷): در این تاپیک **هیچ** نگاشتِ فرمانی انجام
        # نمی‌شود. هر جمله مستقیم به لایهٔ خودشناسی می‌رود، با تاریخچهٔ گفتگو و
        # تصحیح‌های ثبت‌شدهٔ مالک. جای دیگری از بات عوض نمی‌شود؛ flag خاموش یا
        # هر شکست → مسیرِ عادیِ پایین، بایت‌به‌بایت.
        if self._topic_key(msg) == "mirror":
            try:
                import mirror_room as _mr
                if _mr.enabled():
                    _m = _mr.ask(text)
                    if _m.get("ok"):
                        _txt, _kb = _mr.card(_m["text"], _m.get("model") or "",
                                             bool(_m.get("recorded_correction")))
                        _mid = self._client.send(_scrub(_txt), chat_id=chat_id,
                                                 keyboard=_kb,
                                                 topic_id=self._reply_thread(msg))
                        return {"kind": "mirror", "sent": _mid is not None}
                    # شکست را **صادقانه** بگو — در این اتاق «متوجه نشدم» بی‌معنی است
                    _why = {"daily-cap": "سهمیهٔ امروزِ فکرِ عمیقم تمام شد",
                            "not-a-paid-brain": "مغزِ گرانم الان در دسترس نیست",
                            "no-answer": "مغزم جواب نداد",
                            }.get(str(_m.get("reason") or "").split(":")[0], "")
                    if _why:
                        _mid = self._client.send(
                            _scrub(f"🪞 {_why} — چند دقیقهٔ دیگر دوباره بپرس."),
                            chat_id=chat_id, topic_id=self._reply_thread(msg))
                        return {"kind": "mirror_busy", "sent": _mid is not None}
            except Exception:  # noqa: BLE001 — آینه هرگز مسیرِ بات را نمی‌کشد
                pass
        try:
            # Mission Genome: درخواست‌های کدنویسی/تست/یادگیری/جهش نباید به منوی ثابت
            # سقوط کنند. اول به Mission قابل‌ردیابی تبدیل می‌شوند؛ اجرا/apply همچنان
            # پشتِ action_graph/approval می‌ماند و اینجا فقط کارتِ کنترل ساخته می‌شود.
            mt = mission_mod.infer_mission_type(text)
            # Trust-Engine wiring (پشتِ OCTOPUS_TG_LLM_ASK، پیش‌فرض خاموش): اگر تشخیصِ
            # rule-based «general» شد، مغزِ خودِ بات (llm_intent.understand) free-text را می‌فهمد
            # و اگر needs_mission بود، به مأموریتِ گیت‌شده ارتقا می‌دهد — فقط پیشنهاد، اجرا همچنان
            # پشتِ همان گیت (autonomy_matrix دوباره چک می‌کند؛ مدل هرگز گیت را پایین نمی‌آورد).
            # flag خاموش → این بلوک هیچ اجرا نمی‌شود؛ مسیرِ امروز بایت‌به‌بایت.
            _brain_busy = ""
            if mt == "general":
                try:
                    import llm_intent as _li
                    if _li.enabled():
                        _u = _li.understand(text)
                        if isinstance(_u, dict) and _u.get("ok") and _u.get("needs_mission"):
                            mt = "self_coding" if _u.get("intent") == "code" else "verification"
                        elif isinstance(_u, dict) and not _u.get("ok"):
                            # ۲۰۲۶-۰۷-۲۶: مغزِ محلی بینِ دو call فاصلهٔ اجباری دارد
                            # (OLLAMA_MIN_INTERVAL_S، زندهْ ۲۰ثانیه — گاردِ انصافِ GPU).
                            # پیامِ دومِ مالک در آن پنجره بی‌صدا به «متوجه نشدم» سقوط
                            # می‌کرد: بات «احمقم» می‌گفت درحالی‌که حقیقت «مشغولم» بود.
                            # اینجا فقط *علت* نگه داشته می‌شود تا کارت راست بگوید؛
                            # هیچ گاردی دور زده نمی‌شود.
                            _brain_busy = str(_u.get("reason") or "")
                except Exception:  # noqa: BLE001 — فهمِ LLM هرگز مسیرِ بات را نمی‌کشد
                    pass
            if mt != "general":
                m = mission_mod.create_mission(text, source="telegram", mission_type=mt)
                # bridge به صفِ تأیید unified: مأموریت‌های approval-required در mn:ap هم دیده شوند.
                if m.get("approval") == "required":
                    try:
                        aps_mod.add_pending({"id": m.get("id"), "type": "mission",
                                             "title": m.get("owner_intent", "mission"),
                                             "risk": m.get("risk", "medium"),
                                             "requires_confirmation": True,
                                             "source": "telegram"})
                    except Exception:  # noqa: BLE001
                        pass
                txt, kb = mission_mod.mission_card(m.get("id"))
                kb = self._tok_kb(kb)            # P3 (D4): توکنِ ms: وقتی فلگ روشن (وگرنه no-op)
                mid = self._client.send(_scrub(txt), chat_id=chat_id, keyboard=kb,
                                        topic_id=self._reply_thread(msg))
                return {"kind": "ask_mission", "mission_id": m.get("id"), "sent": mid is not None}

            res = intent_mod.classify(text)
            it = res["intent"]
            leg = res.get("leg")
            # نگاشتِ intent → kind (نام‌های قدیمی برای سازگاریِ عقب حفظ شدند)
            kind_map = {"status": "ask_status", "revenue": "ask_revenue",
                        "budget": "ask_budget", "help": "ask_menu",
                        "pause_leg": "ask_pause", "resume_leg": "ask_resume",
                        "scan_metadata": "ask_scan_metadata",
                        "approvals": "ask_approvals",
                        "identity": "ask_identity", "blackbox": "ask_blackbox",
                        "collab_code": "ask_collab", "live_summary": "ask_live",
                        "unknown": "ask_unknown"}
            kind = kind_map.get(it, "ask_unknown")
            if it in ("identity", "blackbox", "collab_code", "live_summary"):
                out = self._live_cmd(text)
            elif it == "status":
                out = self._page("st")
            elif it == "revenue":
                out = self._revenue_text()
            elif it == "budget":
                out = self._page("bg")
            elif it == "help":
                out = self._page("menu")
            elif it == "pause_leg":
                out = self._ask_pause_card(text) if leg else ("کدام پا را مکث کنم؟",
                                                               self._leg_choice_keyboard("p"))
            elif it == "resume_leg":
                out = self._ask_resume_card(text) if leg else ("کدام پا را ادامه بدهم؟",
                                                               self._leg_choice_keyboard("r"))
            elif it == "scan_metadata":
                out = self._page("map")        # کارتِ شروع scan (نه اجرای مستقیم)
            elif it == "approvals":
                out = self._page("ap")
            else:
                # ۲۰۲۶-۰۷-۲۷ — قبل از «متوجه نشدم»، یک‌بار واقعاً بپرس.
                # تا امروز هر جملهٔ آزادی که به فرمان نگاشت نمی‌شد به کارتِ ثابت
                # می‌افتاد؛ `llm_intent` فقط **دسته‌بندی** می‌کرد و هرگز جواب نمی‌داد.
                # `ask_brain` فقط جواب می‌دهد و هیچ گیتی را لمس نمی‌کند — هر اقدامی
                # همچنان از mission/action_graph/approval می‌رود. flag خاموش یا هر
                # شکست → دقیقاً کارتِ امروز، بایت‌به‌بایت.
                out = None
                try:
                    import ask_brain as _ab
                    if _ab.enabled():
                        _a = _ab.ask(text, topic_key=self._topic_key(msg))
                        if _a.get("ok"):
                            out = _ab.card(_a["text"], _a.get("model") or "")
                        elif _a.get("reason") in ("not-a-paid-brain", "no-answer",
                                                  "ask-exception"):
                            _brain_busy = "llm-no-answer"
                except Exception:  # noqa: BLE001 — گفتگو هرگز مسیرِ بات را نمی‌کشد
                    out = None
                if out is None:
                    out = self._ask_unknown_card(_brain_busy)
            txt, kb = out if isinstance(out, tuple) else (str(out or ""), None)
            mid = self._client.send(_scrub(txt), chat_id=chat_id, keyboard=kb,
                                    topic_id=self._reply_thread(msg))
        except Exception:  # noqa: BLE001
            mid, kind = None, "ask_error"
        return {"kind": kind, "sent": mid is not None}

    @staticmethod
    def _leg_from_text(text: str) -> "str | None":
        """حدسِ content-free از نامِ پا در متنِ مالک. فقط whitelist؛ ابهام → None."""
        low = str(text or "").lower()
        aliases = {
            "lead": ("lead", "لید", "نقاش", "نقاشی"),
            "ziman": ("ziman", "گالری", "gallery", "ziman"),
            "mining": ("mining", "ماینینگ", "min"),
            "crypto": ("crypto", "کریپتو", "etoro", "etoro"),
            "accounting": ("accounting", "حساب", "اکانتینگ"),
            "studio_pf": ("studio", "استودیو", "project-f", "project f"),
            "knowledge": ("knowledge", "دانش"),
            "cartographer": ("cartographer", "نقشه", "نقشه‌بردار", "نقشه بردار"),
        }
        hits = [k for k, vals in aliases.items() if any(v.lower() in low for v in vals)]
        return hits[0] if len(hits) == 1 else None

    def _ask_pause_card(self, text: str) -> tuple:
        key = self._leg_from_text(text)
        if key:
            return (f"⏸ مکثِ <code>{key}</code>؟\nیک‌تاپ بزن؛ از ضربانِ بعد اثر می‌کند.",
                    [[{"text": f"⏸ مکث {key}", "callback_data": f"lg:{key}:p"}],
                     [{"text": "🔙 منو", "callback_data": "mn:menu"}]])
        return ("کدام پا را مکث کنم؟", self._leg_choice_keyboard("p"))

    def _ask_resume_card(self, text: str) -> tuple:
        key = self._leg_from_text(text)
        if key:
            return (f"▶️ ادامهٔ <code>{key}</code>؟\nیک‌تاپ بزن؛ اگر مکث باشد برداشته می‌شود.",
                    [[{"text": f"▶️ ادامه {key}", "callback_data": f"lg:{key}:r"}],
                     [{"text": "🔙 منو", "callback_data": "mn:menu"}]])
        return ("کدام پا را ادامه بدهم؟", self._leg_choice_keyboard("r"))

    @staticmethod
    def _leg_choice_keyboard(act: str) -> list:
        rows, legs = [], ("lead", "ziman", "mining", "crypto", "accounting",
                          "studio_pf", "knowledge", "cartographer")
        for i in range(0, len(legs), 2):
            rows.append([{"text": ("⏸ " if act == "p" else "▶️ ") + k,
                          "callback_data": f"lg:{k}:{act}"} for k in legs[i:i + 2]])
        rows.append([{"text": "🔙 منو", "callback_data": "mn:menu"}])
        return rows

    @staticmethod
    def _ask_unknown_card(brain_busy: str = "") -> tuple:
        """کارتِ «نفهمیدم» — ولی وقتی *نفهمیدن* واقعاً *نرسیدن به مغز* بوده،
        همان را بگو. «متوجه نشدم» در آن حالت دروغِ کوچکی است که مالک را به این
        نتیجه می‌رساند که بات کودن است، درحالی‌که فقط پنجرهٔ ۲۰ثانیه‌ایِ مغزِ
        محلی هنوز باز نشده. (۲۰۲۶-۰۷-۲۶)"""
        if brain_busy in ("llm-no-answer", "llm-error", "router-unavailable"):
            text = ("🧠 <b>مغزم چند ثانیه دیگر آزاد می‌شود</b>\n"
                    "▸ حرفت را نفهمیدم چون نرسید به مغز، نه چون بی‌معنی بود\n"
                    "▸ نکنی: همین‌طور می‌ماند — دوباره بفرست، همان جمله کافی است\n"
                    "<i>یا از این‌ها یکی را بزن:</i>")
        else:
            text = "🐙 متوجه نشدم. منظورت یکی از این‌هاست؟"
        kb = [[{"text": "📊 وضعیت", "callback_data": "mn:st"},
               {"text": "🧭 تصمیم‌ها", "callback_data": "mn:ap"}],
              [{"text": "🦵 مکث/ادامه پاها", "callback_data": "mn:lg"},
               {"text": "💰 درآمد", "callback_data": "mn:rv"}],
              [{"text": "🐙 منو", "callback_data": "mn:menu"}]]
        return text, kb

    def _budget_text(self) -> str:
        """کارتِ پیشنهادِ تخصیصِ ماهِ بعد (propose-only). render → متن؛ اسنپ‌شاتِ
        propose-only ثبت می‌کند (هرگز budgets.yaml). fail-soft → پیام آرام."""
        r = self._rmod()
        if r is None or not hasattr(r, "render_budget_proposal"):
            return "🐙 پیشنهادِ بودجه در دسترس نیست."
        try:
            txt = str(r.render_budget_proposal() or "")
        except Exception:  # noqa: BLE001
            return "🐙 پیشنهادِ بودجه در دسترس نیست."
        self._persist_proposal(txt)
        return txt or "🐙 هنوز پیشنهادی نیست."

    @staticmethod
    def _persist_proposal(text: str) -> bool:
        """اسنپ‌شاتِ propose-only از کارتِ بودجه (state/telegram/proposals/). هرگز
        budgets.yaml/ledger — فقط رکوردِ تاریخ‌دار. fail-soft → False."""
        try:
            d = opslib.STATE_DIR / "telegram" / "proposals"
            d.mkdir(parents=True, exist_ok=True)
            opslib.append_jsonl(d / "budget-proposals.jsonl",
                                {"ts": opslib.now_iso(), "kind": "budget_proposal",
                                 "propose_only": True, "text": text})
            return True
        except Exception:  # noqa: BLE001
            return False

    def _revenue_text(self) -> str:
        """کارتِ نمایشِ درآمد (aggregate، PII-safe). attribution.confirmed_revenue() را
        می‌خواند و render می‌کند (فقط‌خواندنی). fail-soft → پیام آرام."""
        r = self._rmod()
        if r is None or not hasattr(r, "render_revenue"):
            return "🐙 نمایِ درآمد در دسترس نیست."
        try:
            import attribution
            rev = attribution.confirmed_revenue()
        except Exception:  # noqa: BLE001
            rev = {}
        try:
            return str(r.render_revenue(rev) or "") or "🐙 هنوز درآمدِ تأییدشده‌ای نیست."
        except Exception:  # noqa: BLE001
            return "🐙 نمایِ درآمد در دسترس نیست."

    # ── مرکزِ فرماندهی: صفحه‌ها + اکشن‌ها (رأی مالک 2026-07-17) ────────────────────
    @staticmethod
    def _power_mod():
        """importِ lazyِ power (fail-soft → None = دکمه‌های کنترل بی‌اثرِ امن)."""
        try:
            import power
            return power
        except Exception:  # noqa: BLE001
            return None

    def _page(self, name: str) -> tuple:
        """(متن، کیبورد)ِ هر صفحهٔ منو — ناوبری با editِ همان پیام.

        از این نقطه به بعد UI باید «زنده» باشد: هر render تا حد ممکن feeds تازه و
        paused_map تازه می‌گیرد. خطا = fallback آرام، نه crash."""
        r, pw = self._rmod(), self._power_mod()
        back = [[{"text": "🔙 منو", "callback_data": "mn:menu"}]]
        p_on = bool(pw and pw.power_on())
        if r is None:
            return "🐙 render در دسترس نیست.", None
        try:
            feeds = r.collect_feeds() if hasattr(r, "collect_feeds") else {}
        except Exception:  # noqa: BLE001
            feeds = {}
        try:
            if name == "st":
                kb = [[{"text": "🔄 تازه‌سازی", "callback_data": "mn:st"}]]
                try:
                    n = int(((feeds.get("guidance") or {}).get("n") or 0)) if isinstance(feeds, dict) else 0
                except (TypeError, ValueError):
                    n = 0
                if n:
                    kb.append([{"text": f"🧭 {n} تصمیم‌ها", "callback_data": "mn:ap"}])
                kb += back
                return str(r.render_status(feeds) or ""), kb
            if name == "qr":
                return self._quarantine_text(feeds), [[{"text": "🔄 تازه‌سازی", "callback_data": "mn:qr"}]] + back
            if name == "ap":
                return self._approvals_queue_page()
            if name == "map":
                try:
                    scan_state = ms_mod.load_state()
                except Exception:  # noqa: BLE001
                    scan_state = {}
                return r.render_map_page(scan_state)
            if name == "ms":
                return mission_mod.mission_card()
            if name == "lg" and pw:
                return r.render_organs(pw.paused_map(), _load_config())
            if name == "bg":
                kb = ([[{"text": "💰 اعمالِ سقف‌ها (دوکلیک)", "callback_data": "pw:ba"}]]
                      if p_on else []) + back
                return self._budget_text(), kb
            if name == "rv":
                return self._revenue_text(), back
            if name == "sy":
                s = {"stop": opslib.STOP_ORGANISM.exists(),
                     "halt": opslib.HALT_ALL.exists(),
                     "restart": RESTART_REQUESTED.exists()}
                return r.render_power(p_on, s)
            if name == "fl" and pw:
                return r.render_flags({n: pw.flag_state(n) for n in pw.FLAG_MENU})
        except Exception:  # noqa: BLE001
            pass
        try:
            paused = pw.paused_map() if pw else {}
            return r.render_menu(p_on, feeds=feeds, paused=paused)
        except TypeError:
            return r.render_menu(p_on)
        except Exception:  # noqa: BLE001
            return "🐙 منو در دسترس نیست.", back

    @staticmethod
    def _quarantine_text(feeds: dict | None = None) -> str:
        """کارتِ قرنطینهٔ content-free: فقط شمارش و مسیرِ رسیدگی؛ محتوا/هویت echo نمی‌شود."""
        f = feeds if isinstance(feeds, dict) else {}
        board = f.get("board") if isinstance(f.get("board"), dict) else {}
        counts = board.get("counts") if isinstance(board.get("counts"), dict) else {}
        try:
            n = int(counts.get("quarantined") or 0)
        except (TypeError, ValueError):
            n = 0
        if n <= 0:
            return "☣️ <b>قرنطینه</b>\nفعلاً چیزی در قرنطینه گزارش نشده."
        return (f"☣️ <b>قرنطینه</b>\n"
                f"<code>{n}</code> مورد نیازمند رسیدگی است.\n"
                "محتوا اینجا نشان داده نمی‌شود؛ فقط کنترل و شمارش.")

    def _approvals_text(self) -> str:
        """صفِ تأییدها (legacy): شمارش + آخرین verdictها (content-free — فقط id/فعل).

        حفظ‌شده برای سازگاری با پاسخ‌های متنی قدیمی؛ کارتِ کامل با کیبورد از
        _approvals_queue_page می‌آید."""
        try:
            sync = aps_mod.sync_to_octopus_state()
        except Exception:  # noqa: BLE001
            sync = {"count": 0, "recent": []}
        lines = [f"✅ <b>تأییدها</b> · {sync.get('count', 0)} تصمیمِ ثبت‌شده تا حالا."]
        for v in sync.get("recent", [])[:5]:
            if isinstance(v, dict):
                emo = {"ok": "✅", "no": "❌", "later": "⏳"}.get(str(v.get("verdict")), "•")
                lines.append(f"{emo} <code>{v.get('id', '?')}</code>")
        return "\n".join(lines)

    def _approvals_queue_page(self) -> tuple:
        """صفحهٔ کاملِ صف تأیید با کیبوردِ عملگرا (فاز E).

        هم pending queue اختاپوس و هم تاریخچهٔ verdict قدیمی را نشان می‌دهد.
        هر job دکمه‌های ap:ok/no/detail دارد (اجرای واقعی در callback handler)."""
        r = self._rmod()
        if r is None or not hasattr(r, "render_approvals_queue"):
            return self._approvals_text(), [[{"text": "🔙 منو", "callback_data": "mn:menu"}]]
        try:
            pending = aps_mod.load_pending()
            counts = aps_mod.summary()
            legacy = aps_mod.sync_to_octopus_state().get("recent", [])
        except Exception:  # noqa: BLE001
            pending, counts, legacy = [], {}, []
        # P3 (Stage-1): پشتِ OCTOPUS_WIRE_CB_TOKEN → mintِ توکنِ HMAC per-job، bind به
        # owner_id + action_hash(content_sha256 روی type/risk) + expires_epoch. فلگ خاموش
        # → mint=None → کارتِ tokenless بایت‌به‌بایتِ قبلی.
        _mint = None
        try:
            if cbtok.flag_on():
                _owner = getattr(self._client, "owner_chat_id", None)
                _by_id = {str(j.get("id")): j for j in pending if isinstance(j, dict)}
                _mint = lambda jid, act: cbtok.mint(
                    str(jid), act, _owner,
                    self._ap_action_hash(act, str(jid), _by_id.get(str(jid), {})),
                    str(_by_id.get(str(jid), {}).get("expires_epoch", "")))
        except Exception:  # noqa: BLE001 — mint اختیاری؛ خطا = کارتِ عادی
            _mint = None
        try:
            return r.render_approvals_queue(pending, counts, legacy, mint=_mint,
                                            offset=int(getattr(self, "_ap_offset", 0)))
        except TypeError:
            # rendererِ قدیمی offset ندارد — سازگاریِ عقب‌رو، بدونِ صفحه‌بندی.
            return r.render_approvals_queue(pending, counts, legacy, mint=_mint)
        except Exception:  # noqa: BLE001
            return self._approvals_text(), [[{"text": "🔙 منو", "callback_data": "mn:menu"}]]

    def _edit_page(self, cbq: dict, page: str) -> None:
        """editِ درجای همان پیام به صفحهٔ خواسته (ناوبریِ منو)."""
        msg = cbq.get("message") or {}
        mid = msg.get("message_id")
        chat = (msg.get("chat") or {}).get("id")
        if not isinstance(mid, int):
            return
        txt, kb = self._page(page)
        try:
            self._client.edit(mid, _scrub(str(txt or "")), keyboard=kb, chat_id=chat)
        except Exception:  # noqa: BLE001
            pass

    def _handle_center_callback(self, cbq: dict, data: str) -> dict:
        """verbهای مرکز: mn (ناوبری) · lg (مکث/ادامهٔ پا — ردهٔ A) ·
        pw (مسلح‌کردنِ اکشنِ حساس) · pwc (تأییدِ دوکلیک — ردهٔ B)."""
        pw = self._power_mod()
        parts = data.split(":")
        verb = parts[0]

        if verb == "mn" and len(parts) == 2:
            self._edit_page(cbq, parts[1])
            self._answer(cbq)
            return {"kind": "center", "page": parts[1]}

        # اتاقِ آینه (۲۰۲۶-۰۷-۲۷): دو دکمهٔ فقط‌خواندنی و $۰ — «چه می‌دانم» و
        # «تصحیح‌ها». هیچ‌کدام مغز صدا نمی‌زند و هیچ state ای عوض نمی‌کند؛ فقط
        # همان چیزی را نشان می‌دهد که در contextِ گفتگو هم می‌رود.
        # مذاکره (۲۰۲۶-۰۷-۲۷): سه جواب به‌جای دو — قبول / نه / **شرط بگذار**.
        # «قبول» هیچ چیز را اجرا نمی‌کند؛ فقط ثبت می‌شود. اجرا همچنان از همان
        # گیت‌هایی می‌رود که این مسیر اصلاً لمسشان نمی‌کند.
        if verb == "ng" and len(parts) == 3:
            act, oid = parts[1], parts[2]
            msg = cbq.get("message") or {}
            chat_id = (msg.get("chat") or {}).get("id")
            try:
                import negotiate as _ng
                if act == "c":
                    # شرط‌گذاری: منتظرِ متنِ بعدیِ مالک می‌مانیم (RAM؛ ری‌استارت =
                    # لغوِ امن، مثلِ _awaiting_rfc_edit).
                    self._awaiting_counter = oid
                    self._client.send(
                        _scrub("✍️ شرطت را بنویس — پیشنهادِ بعدی‌ام آن را رعایت می‌کند."),
                        chat_id=chat_id, topic_id=self._reply_thread(msg))
                    self._answer(cbq, "منتظرِ شرطتم")
                    return {"kind": "negotiate", "awaiting": oid}
                r = _ng.respond(oid, "accept" if act == "a" else "reject")
                self._answer(cbq, "ثبت شد" if r.get("ok") else str(r.get("reason"))[:60])
                if r.get("ok"):
                    self._client.send(
                        _scrub("✅ پذیرفتم — ثبت شد. اجرا هنوز نشده؛ از مسیرِ تأیید می‌آید."
                               if act == "a" else "❌ باشد، کنارش گذاشتم."),
                        chat_id=chat_id, topic_id=self._reply_thread(msg))
                return {"kind": "negotiate", "verdict": act, "ok": r.get("ok")}
            except Exception:  # noqa: BLE001
                self._answer(cbq)
                return {"kind": "negotiate", "ok": False}

        # کوت (۲۰۲۶-۰۷-۲۷): «بفرست» **ارسال نمی‌کند** — رأیِ مالک را ثبت می‌کند و
        # کار را به همان مسیرِ تأییدِ موجود می‌سپارد. مرزِ «تا مرزِ ارسال» یعنی
        # همین: دکمه هست، ولی اجرا از این‌جا شروع نمی‌شود.
        if verb == "qt" and len(parts) == 3:
            act, qt = parts[1], _sanitize_id(parts[2])
            msg = cbq.get("message") or {}
            chat_id = (msg.get("chat") or {}).get("id")
            if act == "s":
                self._record_approval({"id": f"quote-{qt}", "verdict": "ok",
                                       "ts": opslib.now_iso(), "source": "tg-quote"})
                body = ("📤 تأییدت ثبت شد.\n"
                        "▸ ارسالِ واقعی از مسیرِ تأیید می‌رود — هنوز چیزی نرفته.\n"
                        "▸ نکنی: کوت همان‌جا پیش‌نویس می‌ماند.")
            else:
                body = ("✏️ برای بازنگری، `/lead` را با اعدادِ تازه دوباره بفرست — "
                        "نسخهٔ جدید با همان شمارهٔ کوت ثبت می‌شود.")
            try:
                self._client.send(_scrub(body), chat_id=chat_id,
                                  topic_id=self._reply_thread(msg))
            except Exception:  # noqa: BLE001
                pass
            self._answer(cbq, "ثبت شد")
            return {"kind": "quote", "act": act, "qt": qt}

        # «کمتر حرف بزن» — سقفِ روزانهٔ ابتکار را نصف می‌کند. مالک باید بتواند
        # صدای اختاپوس را با یک تپ کم کند، وگرنه اولین سرریز کلِ کانال را می‌بندد.
        if verb == "iv" and len(parts) == 2 and parts[1] == "q":
            msg = cbq.get("message") or {}
            try:
                import initiative as _iv
                r = _iv.quieter()
                body = (f"🔇 باشد — از این به بعد حداکثر {r['cap']} بار در روز.\n"
                        "▸ نکنی: همین‌قدر می‌ماند. باز هم بزنی، کمتر می‌شود.")
            except Exception:  # noqa: BLE001
                body = "🔇 نشد."
            try:
                self._client.send(_scrub(body),
                                  chat_id=(msg.get("chat") or {}).get("id"),
                                  topic_id=self._reply_thread(msg))
            except Exception:  # noqa: BLE001
                pass
            self._answer(cbq, "کمتر حرف می‌زنم")
            return {"kind": "initiative", "act": "quieter"}

        # `x:c:<key>` یک کارت را باز می‌کند، `x:p:<n>` صفحهٔ فهرست را عوض.
        # هر دو فقط‌خواندنی‌اند و هیچ چیزی را اجرا نمی‌کنند.
        if verb == "x" and len(parts) >= 3:
            msg = cbq.get("message") or {}
            try:
                import capability_registry as _cr
                if parts[1] == "c":
                    body, kb = _cr.render(parts[2]), None
                else:
                    body, kb = _cr.card(), _cr.keyboard(int(parts[2] or 0))
            except Exception:  # noqa: BLE001
                body, kb = "🗂 فهرست در دسترس نیست.", None
            try:
                self._client.send(_scrub(body),
                                  chat_id=(msg.get("chat") or {}).get("id"),
                                  topic_id=self._reply_thread(msg), keyboard=kb)
            except Exception:  # noqa: BLE001
                pass
            self._answer(cbq)
            return {"kind": "capability", "act": parts[1]}

        # «🔍 مدرک کم است» — dg:e:<trace_id>. فقط توضیح می‌دهد؛ هیچ تصمیمی را
        # نه اجرا می‌کند نه عوض. رأی همچنان از ok/no/later می‌آید.
        if verb == "dg" and len(parts) >= 2 and parts[1] == "e":
            try:
                import decision_gate as _dg
                body = _dg.explain(parts[2] if len(parts) > 2 else "")
            except Exception:  # noqa: BLE001
                body = "🔍 گیتِ تصمیم در دسترس نیست."
            msg = cbq.get("message") or {}
            try:
                self._client.send(_scrub(body),
                                  chat_id=(msg.get("chat") or {}).get("id"),
                                  topic_id=self._reply_thread(msg))
            except Exception:  # noqa: BLE001
                pass
            self._answer(cbq)
            return {"kind": "decision-gate", "view": "evidence"}

        if verb == "mr" and len(parts) == 2:
            try:
                import mirror_room as _mr
                body = (_mr.know_card() if parts[1] == "know"
                        else _mr.corrections_card())
            except Exception:  # noqa: BLE001
                body = "🪞 آینه در دسترس نیست."
            msg = cbq.get("message") or {}
            try:
                self._client.send(_scrub(body),
                                  chat_id=(msg.get("chat") or {}).get("id"),
                                  topic_id=self._reply_thread(msg))
            except Exception:  # noqa: BLE001
                pass
            self._answer(cbq)
            return {"kind": "mirror", "view": parts[1]}

        if verb == "lg" and len(parts) == 3 and pw:
            key, act = _sanitize_id(parts[1]), parts[2]
            ok, msg = (pw.pause_leg(key) if act == "p" else pw.resume_leg(key))
            self._answer(cbq, msg[:180])
            self._edit_page(cbq, "lg")
            return {"kind": "center", "leg": key, "ok": ok}

        if verb == "pw" and len(parts) == 2 and pw:
            act = _sanitize_id(parts[1])
            label = (f"🚩 toggleِ فلگ {act[3:]}" if act.startswith("fg-")
                     else pw.POWER_ACTIONS.get(act, ("؟",))[0])
            cfg = _load_config()
            cfg["pw_arm"] = {"act": act, "ts": float(self._clock())}
            _save_config(cfg)
            r = self._rmod()
            msg = cbq.get("message") or {}
            mid = msg.get("message_id")
            chat = (msg.get("chat") or {}).get("id")
            if r is not None and isinstance(mid, int):
                txt, kb = r.render_confirm(label, act)
                try:
                    self._client.edit(mid, _scrub(txt), keyboard=kb, chat_id=chat)
                except Exception:  # noqa: BLE001
                    pass
            self._answer(cbq, "برای اجرا، تأییدِ دوم را بزن")
            return {"kind": "center", "armed": act}

        if verb == "pwc" and len(parts) == 2 and pw:
            act = _sanitize_id(parts[1])
            cfg = _load_config()
            arm = cfg.get("pw_arm") if isinstance(cfg.get("pw_arm"), dict) else {}
            fresh = (arm.get("act") == act and
                     float(self._clock()) - float(arm.get("ts", 0) or 0) <= pw.ARM_FRESH_S)
            cfg.pop("pw_arm", None)
            _save_config(cfg)
            if not fresh:
                self._answer(cbq, "تأیید منقضی/نامعتبر — دوباره از منو")
                self._edit_page(cbq, "sy")
                return {"kind": "center", "expired": act}
            if act.startswith("fg-"):
                ok, msg = pw.toggle_flag(act[3:])
            else:
                fn = pw.POWER_ACTIONS.get(act, (None, None))[1]
                ok, msg = fn() if fn else (False, "اکشنِ ناشناخته")
            self._answer(cbq, msg[:180])
            self._edit_page(cbq, "fl" if act.startswith("fg-") else "sy")
            return {"kind": "center", "power": act, "ok": ok}

        self._answer(cbq, "نادیده")
        return {"kind": "center", "ignored": data[:24]}

    def _handle_map_callback(self, cbq: dict, data: str) -> dict:
        """verbهای نقشه‌برداریِ metadata (فاز D — فقط‌خواندنی، propose-only).

        - map:start → یک job در صف تأیید می‌سازد (risk=read) و در همین لحظه یک scan
          محدود و sync روی ریشه اجرا می‌کند (fail-soft؛ خطر کم چون فقط metadata).
          برای scanِ کامل (بدونِ سقف) کارت تأیید جداگانه می‌سازد.
        - map:status → صفحهٔ map را refresh می‌کند (mn:map).
        - map:report → آخرین گزارش را در یک پیامِ نوی نشان می‌دهد.

        امنیت: فقط metadata؛ هیچ محتوای فایل خوانده نمی‌شود (gating در metadata_scan).
        کارت تأیید بیشتر برای UX (هشدارِ طولِ احتمالی) است تا gating واقعی."""
        parts = data.split(":")
        if len(parts) < 2:
            self._answer(cbq, "نادیده")
            return {"kind": "map", "ignored": data[:24]}
        action = parts[1]
        msg = cbq.get("message") or {}
        mid = msg.get("message_id")
        chat = (msg.get("chat") or {}).get("id")

        if action == "start":
            # یک scan محدود و sync همین حالا (خطرِ کم: فقط metadata)
            try:
                result = ms_mod.scan_metadata(max_files=50_000, max_seconds=60)
                paths = ms_mod.write_manifest(result)
                summary = ms_mod.summarize_manifest(result)
                # job در صف تأیید (برای بازبینیِ انسان)
                try:
                    aps_mod.add_pending({
                        "type": "metadata_scan", "title": "نقشه‌برداری metadata",
                        "risk": "read", "requires_confirmation": False,
                        "dry_run_report": paths.get("report", "")[:500],
                        "source": "telegram"})
                except Exception:  # noqa: BLE001
                    pass
                toast = summary[:180]
            except Exception as e:  # noqa: BLE001
                toast = f"خطا: {type(e).__name__}"
                summary = "🗺️ خطا در اسکن"
            self._answer(cbq, toast)
            # refresh صفحهٔ map با stateِ نو
            self._edit_page(cbq, "map")
            return {"kind": "map", "action": "start", "summary": summary[:200]}

        if action == "report":
            try:
                st = ms_mod.load_state()
                latest_report = None
                rp_dir = ms_mod._REPORTS_DIR
                if rp_dir.exists():
                    files = sorted(rp_dir.glob("metadata_scan_*.md"),
                                   key=lambda p: p.stat().st_mtime, reverse=True)
                    latest_report = files[0] if files else None
                if latest_report and latest_report.exists():
                    txt = latest_report.read_text("utf-8")[:3500]
                    self._client.send(_scrub(txt), chat_id=chat)
                    self._answer(cbq, "گزارش ارسال شد")
                else:
                    self._answer(cbq, "هنوز گزارشی نیست — اول map:start را بزن")
            except Exception:  # noqa: BLE001
                self._answer(cbq, "گزارش در دسترس نیست")
            return {"kind": "map", "action": "report"}

        # action == "status" یا هر چیزِ دیگر → refresh
        self._edit_page(cbq, "map")
        self._answer(cbq, "تازه‌سازی شد")
        return {"kind": "map", "action": action}

    def _handle_mission_callback(self, cbq: dict, data: str) -> dict:
        """verbهای Mission Genome (ms:*).

        این handler فقط state مأموریت را عوض/ثبت می‌کند و هیچ patch/code.apply واقعی
        انجام نمی‌دهد. apply واقعی همچنان مسیر جداگانهٔ code_autonomy + approval +
        shadow-green + rollback دارد. دکمه‌های test/review فقط request/note ثبت می‌کنند
        تا UI دروغ نگوید که تست یا دکتر واقعاً اجرا شده است."""
        parts = data.split(":", 2)
        if len(parts) < 2:
            self._answer(cbq, "نادیده")
            return {"kind": "mission", "ignored": data[:24]}
        action = parts[1]
        mid = _sanitize_id(parts[2]) if len(parts) > 2 else ""
        msg = cbq.get("message") or {}
        m_id = msg.get("message_id")
        chat = (msg.get("chat") or {}).get("id")

        if action == "open" and mid:
            txt, kb = mission_mod.mission_card(mid)
            kb = self._tok_kb(kb)                # P3 (D4): توکنِ ms: وقتی فلگ روشن (وگرنه no-op)
            try:
                if isinstance(m_id, int):
                    self._client.edit(m_id, _scrub(txt), keyboard=kb, chat_id=chat)
            except Exception:  # noqa: BLE001
                pass
            self._answer(cbq, "Mission")
            return {"kind": "mission", "action": "open", "id": mid}

        if action == "test" and mid:
            # فلگ‌خاموش پیش‌فرض: بدونِ فلگ، دقیقاً رفتارِ قبلی (فقط request/note ثبت می‌شود،
            # UI دروغ نمی‌گوید). با OCTOPUS_WIRE_MISSION_RUNNER=1 runnerِ v0 واقعاً در worktreeِ
            # ایزوله تست‌های allowlisted را اجرا می‌کند (هرگز apply/patch؛ درختِ زنده لمس نمی‌شود).
            wired = os.environ.get("OCTOPUS_WIRE_MISSION_RUNNER") == "1" and runner_mod is not None
            if wired:
                try:
                    out = runner_mod.run_mission(mid)
                    toast = ("🧪 اجرا سبز (شواهد ثبت شد)" if out.get("ok")
                             else f"🧪 اجرا: {out.get('refused') or 'قرمز'} — شواهد ثبت شد")
                except Exception:  # noqa: BLE001 — fail-soft: هر خطا → note، هرگز crash
                    mission_mod.add_note(mid, "runner error; fell back to request-only")
                    toast = "🧪 خطای runner؛ فقط درخواست ثبت شد"
            else:
                mission_mod.add_note(mid, "owner requested tests/fitness from Telegram; runner flag off (staged)")
                mission_mod.set_state(mid, "planned", "test requested; awaiting runner")
                toast = "درخواست تست ثبت شد؛ اجرا جداست"
            txt, kb = mission_mod.mission_card(mid)
            kb = self._tok_kb(kb)                # P3 (D4): توکنِ ms: وقتی فلگ روشن (وگرنه no-op)
            try:
                if isinstance(m_id, int):
                    self._client.edit(m_id, _scrub(txt), keyboard=kb, chat_id=chat)
            except Exception:  # noqa: BLE001
                pass
            self._answer(cbq, toast)
            return {"kind": "mission", "action": "test_request", "id": mid, "wired": wired}

        if action == "review" and mid:
            mission_mod.add_note(mid, "owner requested doctor/epistemics review from Telegram; reviewer not executed by center")
            mission_mod.set_state(mid, "planned", "review requested; awaiting doctor/epistemics")
            txt, kb = mission_mod.mission_card(mid)
            kb = self._tok_kb(kb)                # P3 (D4): توکنِ ms: وقتی فلگ روشن (وگرنه no-op)
            try:
                if isinstance(m_id, int):
                    self._client.edit(m_id, _scrub(txt), keyboard=kb, chat_id=chat)
            except Exception:  # noqa: BLE001
                pass
            self._answer(cbq, "درخواست review ثبت شد")
            return {"kind": "mission", "action": "review_request", "id": mid}

        if action in ("approve", "reject") and mid:
            # P3 (D4): فلگ روشن → این verbِ رأی‌دهنده باید توکنِ HMACِ معتبر داشته باشد
            # (ms:<action>:<mid>:<token>). tokenlessِ قدیمی/جعلی/منقضی = رد (fail-closed،
            # دقیقاً مثلِ ap:). فلگ خاموش → این بلوک اجرا نمی‌شود و mid همان مقدارِ بالا می‌ماند.
            if cbtok.flag_on():
                seg = data.split(":")                        # ms : action : mid [: token]
                mid = _sanitize_id(seg[2]) if len(seg) > 2 else ""   # midِ تمیز (token جدا)
                token = seg[3] if len(seg) > 3 else None
                _exp = self._cb_expires_for(mid)
                if not mid or not self._cb_verify(token, mid, action, _exp):
                    self._answer(cbq, "توکنِ نامعتبر — کارت را از منو دوباره باز کن")
                    return {"kind": "mission", "rejected": "bad-token", "id": mid}
                if _exp:                                     # enforceِ جداگانهٔ انقضا (مثلِ ap:)
                    try:
                        import time as _t
                        if _t.time() > float(_exp):
                            self._answer(cbq, "کارت منقضی شده — از منو دوباره باز کن")
                            return {"kind": "mission", "rejected": "expired", "id": mid}
                    except (TypeError, ValueError):
                        pass
            approved = action == "approve"
            out = mission_mod.set_owner_verdict(mid, approved)
            try:
                if approved:
                    aps_mod.approve(mid)
                    aps_mod.record_legacy_verdict(mid, "ok")
                else:
                    aps_mod.reject(mid)
                    aps_mod.record_legacy_verdict(mid, "no")
            except Exception:  # noqa: BLE001
                pass
            if out:
                # Wave1-A: رأیِ مالک روی missionِ همین کارت هم measurementِ پایدار می‌شود
                # (idempotent — اگر همان job از مسیرِ ap: هم رأی بخورد، رویدادِ تکراری نمی‌نشیند).
                self._durable_verdict_outcome("ok" if approved else "no", mid,
                                              {"type": "mission"})
            txt, kb = mission_mod.mission_card(mid)
            kb = self._tok_kb(kb)                # P3 (D4): توکنِ ms: وقتی فلگ روشن (وگرنه no-op)
            try:
                if isinstance(m_id, int):
                    self._client.edit(m_id, _scrub(txt), keyboard=kb, chat_id=chat)
            except Exception:  # noqa: BLE001
                pass
            self._answer(cbq, "تأیید شد" if approved else "رد شد")
            return {"kind": "mission", "action": action, "id": mid, "ok": bool(out)}

        self._answer(cbq, "نادیده")
        return {"kind": "mission", "ignored": data[:24]}

    def _ap_action_hash(self, action: str, jid: str, job: dict) -> str:
        """P3: hashِ محتوایی برای bindِ توکنِ callback — content_sha256(action, jid, {type,risk}).
        anti-TOCTOU: اگر type/riskِ job عوض شود توکن باطل می‌شود. fail-soft → "" (آنگاه
        verify بر jid/action/owner/expires تکیه می‌کند)."""
        try:
            import mission_contract as _mc
            return _mc.content_sha256(action, str(jid),
                                      {"type": (job or {}).get("type"),
                                       "risk": (job or {}).get("risk")})
        except Exception:  # noqa: BLE001
            return ""

    # ── P3 (D4): توکنِ HMACِ callback برای verbهای legacy (ok/no/later) و mission (ms:) ──
    # همان طرحِ ap: (jid|action|owner|action_hash|expires) از callback_token — «طرحِ دوم»
    # اختراع نمی‌شود. این verbها jobِ محتوایی مثلِ ap: ندارند → action_hash="". فقط mission
    # می‌تواند expires داشته باشد (اگر missionِ ذخیره‌شده expires_epoch داشته باشد). فلگ خاموش
    # → این مسیرها اصلاً لمس نمی‌شوند (بایت‌به‌بایتِ امروز). is_owner از handle_update اول است.
    def _cb_expires_for(self, mid: str) -> str:
        """expires_epochِ missionِ ذخیره‌شده (برای bind/enforceِ توکنِ ms:) یا "" (بی‌انقضا).
        fail-soft → "" (هرگز نمی‌شکند)."""
        try:
            m = mission_mod.get(mid)
            return str((m or {}).get("expires_epoch", "")) if isinstance(m, dict) else ""
        except Exception:  # noqa: BLE001
            return ""

    def _cb_mint(self, jid: str, action: str, expires: str = "") -> str:
        """mintِ توکنِ HMAC با همان cbtok.mint (action_hash=""). بی‌راز/خطا → "" (fail-closed:
        کارتِ tokenlessِ inert، نه یک توکنِ جعلی‌پذیر)."""
        try:
            owner = getattr(self._client, "owner_chat_id", None)
            return cbtok.mint(str(jid), action, owner, "", expires)
        except Exception:  # noqa: BLE001
            return ""

    def _cb_verify(self, token, jid: str, action: str, expires: str = "") -> bool:
        """verifyِ متقارن با _cb_mint. نبودِ token/secret یا هر عدم‌تطابق = False (fail-closed)."""
        try:
            owner = getattr(self._client, "owner_chat_id", None)
            return cbtok.verify(token, str(jid), action, owner, "", expires)
        except Exception:  # noqa: BLE001
            return False

    def _tok_btn(self, btn: dict) -> dict:
        """یک دکمه را در صورتِ لزوم توکن‌دار کن (فقط verbهای گیت‌شده). idempotent:
        اگر callback_data قبلاً توکن دارد یا verbِ گیت‌نشده است، دست‌نخورده برمی‌گردد."""
        cd = btn.get("callback_data")
        if not isinstance(cd, str):
            return btn
        seg = cd.split(":")
        new_cd = None
        if len(seg) == 2 and seg[0] in _VERDICTS:            # legacy ok/no/later:<did> (بی‌توکن)
            tok = self._cb_mint(seg[1], seg[0], "")
            if tok:
                new_cd = f"{cd}:{tok}"
        elif len(seg) == 3 and seg[0] == "ms" and seg[1] in ("approve", "reject"):  # ms:<v>:<mid>
            exp = self._cb_expires_for(seg[2])
            tok = self._cb_mint(seg[2], seg[1], exp)
            if tok:
                new_cd = f"{cd}:{tok}"
        if new_cd is None:
            return btn
        nb = dict(btn)
        nb["callback_data"] = new_cd
        return nb

    def _tok_kb(self, kb):
        """کیبورد را وقتی OCTOPUS_WIRE_CB_TOKEN روشن است توکن‌دار کن تا کارتِ legacy/mission با
        handlerِ token-gated کار کند («exactly like ap:»). فلگ خاموش → kb بایت‌به‌بایت بدونِ تغییر.
        فقط verbهای گیت‌شده لمس می‌شوند؛ ap:/mn:/lg:/ms:open|test|review دست‌نخورده."""
        try:
            if not cbtok.flag_on() or not isinstance(kb, list):
                return kb
        except Exception:  # noqa: BLE001
            return kb
        out = []
        for row in kb:
            if not isinstance(row, list):
                out.append(row)
                continue
            out.append([self._tok_btn(b) if isinstance(b, dict) else b for b in row])
        return out

    def _handle_approval_callback(self, cbq: dict, data: str) -> dict:
        """verbهای صفِ تأیید (فاز E — bridge اختاپوس).

        - ap:ok:<id>  → approval_store.approve(id) + record_legacy_verdict + refresh
        - ap:no:<id>  → approval_store.reject(id)  + record_legacy_verdict + refresh
        - ap:detail:<id> → کارتِ جزئیاتِ content-free (فقط title/type/risk؛ نه محتوا)

        توجه: این فقط state را عوض می‌کند (pending → approved/rejected). اجرای واقعیِ
        job (اگر risk=high) به handlerهای جداگانه یا power-gate واگذار می‌شود — این
        لایه فقط صف است. risk=high → هشدار در toast."""
        # `ap:page:<n>` — ناوبریِ خالص. هیچ state ای عوض نمی‌کند و هیچ رأیی ثبت
        # نمی‌کند، پس توکنِ HMAC لازم ندارد (توکن به job بایند می‌شود، نه به صفحه).
        # بدونِ این، دکمهٔ «بعدی» ساخته می‌شد ولی به هیچ‌جا نمی‌رسید — همان مدِ
        # خرابیِ پنج دکمهٔ مردهٔ امروز صبح.
        _seg = data.split(":")
        if len(_seg) >= 3 and _seg[1] == "page":
            try:
                self._ap_offset = max(0, int(_seg[2]))
            except (TypeError, ValueError):
                self._ap_offset = 0
            self._answer(cbq)
            self._edit_page(cbq, "ap")
            return {"kind": "approval", "act": "page", "offset": self._ap_offset}

        # P3 (Stage-1): وقتی فلگ OCTOPUS_WIRE_CB_TOKEN روشن است، ok/no باید توکنِ HMACِ
        # معتبر داشته باشند (ap:<action>:<jid>:<token>). callbackِ قدیمیِ tokenless یا
        # توکنِ نامعتبر/دستکاری‌شده = رد (fail-closed). فلگ خاموش → مسیرِ قبلی بایت‌به‌بایت.
        if cbtok.flag_on():
            seg = data.split(":")
            action = seg[1] if len(seg) > 1 else ""
            jid = _sanitize_id(seg[2]) if len(seg) > 2 else ""
            token = seg[3] if len(seg) > 3 else None
            if not action or not jid:
                self._answer(cbq, "نادیده")
                return {"kind": "approval", "ignored": data[:24]}
            if action in ("ok", "no"):
                _job = aps_mod.get(jid)
                _owner = getattr(self._client, "owner_chat_id", None)
                _ah = self._ap_action_hash(action, jid, _job or {})
                _exp = str((_job or {}).get("expires_epoch", ""))
                # (1) صحتِ HMAC (شاملِ content + expires) — دستکاری/جعل/tokenless قدیمی = رد
                if not cbtok.verify(token, jid, action, _owner, _ah, _exp):
                    self._answer(cbq, "توکنِ نامعتبر — کارت را از منو دوباره باز کن")
                    return {"kind": "approval", "rejected": "bad-token", "id": jid}
                # (2) enforcement جداگانهٔ انقضا — 5.3
                # ۲۰۲۶-۰۷-۲۷ (نقطهٔ کورِ ۱۳۵): این چک `time.time()` خام می‌خواند،
                # که **قابلِ تنظیم** است. پرشِ ساعت به عقب (تصحیحِ NTP، دستِ کاربر،
                # باتریِ ساعتِ سخت‌افزاری) هر کارتِ سوخته را دوباره معتبر می‌کرد —
                # یعنی یک تأییدِ پولیِ منقضی می‌توانست زنده شود.
                # `clock_guard` روی ابهام fail-closed می‌دهد: ساعتِ بی‌اعتماد =
                # منقضی، چون اگر ندانیم ساعت چند است نمی‌توانیم بگوییم وقت هست.
                if _exp:
                    try:
                        import clock_guard as _cg
                        _gone, _why = _cg.is_expired(_exp)
                    except Exception:  # noqa: BLE001 — نبودِ گارد = رفتارِ قبلی
                        import time as _t
                        try:
                            _gone, _why = (_t.time() > float(_exp)), "مهلت گذشته"
                        except (TypeError, ValueError):
                            _gone, _why = False, ""
                    if _gone:
                        self._answer(cbq, f"کارت منقضی شده ({_why[:40]}) — از منو دوباره باز کن")
                        return {"kind": "approval", "rejected": "expired", "id": jid}
                # (3) destination binding — 5.4 (علاوه بر is_owner از from.id)
                _chat = ((cbq.get("message") or {}).get("chat") or {}).get("id")
                _allowed = {str(x) for x in (getattr(self._client, "owner_chat_id", None),
                                             getattr(self._client, "center_chat_id", None))
                            if x is not None}
                if _allowed and _chat is not None and str(_chat) not in _allowed:
                    self._answer(cbq, "مقصدِ نامعتبر")
                    return {"kind": "approval", "rejected": "bad-destination", "id": jid}
        else:
            parts = data.split(":", 2)
            if len(parts) < 3:
                self._answer(cbq, "نادیده")
                return {"kind": "approval", "ignored": data[:24]}
            action, jid = parts[1], _sanitize_id(parts[2])
        ok, msg, verdict = False, "", ""
        try:
            if action == "ok":
                job_before = aps_mod.get(jid)
                ok = aps_mod.approve(jid)
                verdict = "ok"
                msg = "✅ تأیید شد" if ok else "یافت نشد/قبلاً تصمیم گرفته شده"
                if ok:
                    aps_mod.record_legacy_verdict(jid, "ok")
                    # Wave1-A: فقط پس از transitionِ single-use ِ موفق (approve=True) —
                    # replay/تکرار به این خط نمی‌رسد؛ durable هم خودش idempotent است.
                    self._durable_verdict_outcome("ok", jid, job_before)
                    if (isinstance(job_before, dict) and job_before.get("type") == "mission") or mission_mod.get(jid):
                        mission_mod.set_owner_verdict(jid, True)
            elif action == "no":
                job_before = aps_mod.get(jid)
                ok = aps_mod.reject(jid)
                verdict = "no"
                msg = "❌ رد شد" if ok else "یافت نشد/قبلاً تصمیم گرفته شده"
                if ok:
                    aps_mod.record_legacy_verdict(jid, "no")
                    self._durable_verdict_outcome("no", jid, job_before)   # Wave1-A: ردِ پایدار
                    if (isinstance(job_before, dict) and job_before.get("type") == "mission") or mission_mod.get(jid):
                        mission_mod.set_owner_verdict(jid, False)
            elif action == "detail":
                job = aps_mod.get(jid)
                if job:
                    r = self._rmod()
                    # HTML-escape محلی (center._esc نداشت؛ html.escape کافی + scrub)
                    import html as _html
                    esc = lambda s: _html.escape(str(s if s is not None else ""))
                    risk = str(job.get("risk", "read"))
                    detail_text = (f"📝 <b>جزئیاتِ job</b>\n"
                                   f"<code>{_scrub(job.get('id', '?'))}</code>\n"
                                   f"نوع: {_scrub(job.get('type', '?'))}\n"
                                   f"ریسک: <code>{esc(risk)}</code>\n"
                                   f"وضعیت: {_scrub(job.get('status', '?'))}\n"
                                   f"عنوان: {_scrub(str(job.get('title', '?'))[:120])}")
                    if r is not None and isinstance(cbq.get("message"), dict):
                        m = cbq["message"]
                        try:
                            self._client.edit(m.get("message_id"), _scrub(detail_text),
                                              chat_id=(m.get("chat") or {}).get("id"))
                        except Exception:  # noqa: BLE001
                            pass
                    self._answer(cbq, "جزئیات (content-free)")
                    return {"kind": "approval", "action": "detail", "id": jid}
                else:
                    msg = "job یافت نشد"
        except Exception as e:  # noqa: BLE001
            msg = f"خطا: {type(e).__name__}"

        self._answer(cbq, msg[:180])
        # refresh صفحهٔ approvals برای نشان‌دادنِ تغییر
        self._edit_page(cbq, "ap")
        return {"kind": "approval", "action": action, "id": jid, "ok": ok, "verdict": verdict}

    def _handle_callback(self, cbq: dict) -> dict:
        """callback data = '<verb>:<id>' با verb ∈ ok/no/later (قراردادِ render_decision)
        یا verbهای مرکزِ فرماندهی (mn/lg/pw/pwc → _handle_center_callback) یا
        verbهای فاز D/E (map → _handle_map_callback، ap → _handle_approval_callback).
        ثبت به الگوی approval-file + رویداد + answer_callback؛ ok = mintِ اختیاریِ
        توکنِ HumanAppendGuard (فقط با رازِ env)."""
        data = str(cbq.get("data") or "")
        verb = data.split(":", 1)[0]
        # ۲۰۲۶-۰۷-۳۰ — دکمه‌های خانهٔ لنگر (hm:*). عمداً **این‌جا** dispatch می‌شود،
        # جدا و بالاتر از جدولِ مرکز، تا با هانکِ کامیت‌نشدهٔ جلسهٔ موازی روی همان
        # جدول تصادم نکند (§ درختِ مشترک). read-only اند و مالکیت را لایهٔ
        # بالادست (handle_update → _is_owner) از قبل گیت کرده.
        if verb == "hm":
            return self._handle_home_callback(cbq, data)
        if verb == "tk":
            # دکمه‌های کارتِ پا (رأیِ ۰۷-۳۰ شب). مالکیت را بالادست گیت کرده.
            return self._handle_tasks_callback(cbq, data)
        if verb == "oc":
            # مامور (owner_console) — مسیرِ اصلی در handle_update است (با تصمیمِ
            # سطحِ کامل)؛ این شاخه هم اعلامِ مسیر برای گاردِ parity است و هم
            # fallback ِ واقعی وقتی گیتِ بالادست exception خورده باشد. تصمیمِ
            # سطح همان‌جور ساخته می‌شود — نه حدس، همان classify.
            try:
                import input_surface_policy as _isp2
                from owner_console import telegram_adapter as _oc2
                _cfg2 = _load_config()
                _d2 = _isp2.classify(
                    {"callback_query": cbq}, bot_role="outer",
                    owner_id=getattr(self._client, "owner_chat_id", None),
                    group_id=_cfg2.get("chat_id"),
                    topics=_cfg2.get("topics")
                    if isinstance(_cfg2.get("topics"), dict) else {})
                _r2 = _oc2.handle_callback(data, surface_decision=_d2)
                if _r2.get("handled") and _r2.get("reply"):
                    return self._send_console_reply(_r2["reply"], cbq)
            except Exception:  # noqa: BLE001
                pass
            return {"kind": "owner-console", "console_kind": "blocked"}
        # 2026-07-29: کارتِ دکترِ اختاپوس callbackِ سه‌تکه دارد (ok|no:gate:mission)؛
        # اگر قبل از fallbackِ ok/no:<id> جدا نشود، به‌عنوانِ approvalِ بی‌ربط ثبت
        # می‌شود و دکتر هرگز رأی را نمی‌بیند. پشتِ OCTOPUS_WIRE_DOCTOR_TG؛ fail-soft.
        try:
            import doctor_link as _dl
            if _dl.handle_callback(self, cbq):
                return {"kind": "callback", "doctor": True}
        except Exception:  # noqa: BLE001 — link هرگز dispatch را نمی‌کشد
            pass
        # ۲۰۲۶-۰۷-۲۷ — `ng` و `mr` این‌جا جا افتاده بودند، پس هر پنج دکمهٔ ساخته‌شدهٔ
        # همان روز (سه دکمهٔ مذاکره + دو دکمهٔ آینه) به handlerشان **نمی‌رسیدند** و
        # در شاخهٔ ok/no/later «نادیده» می‌شدند. تستِ آن روز فقط شکلِ صفحه‌کلید را
        # می‌سنجید نه مسیرِ dispatch را — همان «سبز به‌خاطرِ نبودِ خطا».
        # گاردِ `t_every_emitted_callback_verb_is_routed` حالا هر فعلی را که کد
        # تولید می‌کند با همین جدول تطبیق می‌دهد.
        if verb in ("mn", "lg", "pw", "pwc", "ng", "mr", "qt", "iv", "dg", "x"):
            return self._handle_center_callback(cbq, data)
        if verb == "map":
            return self._handle_map_callback(cbq, data)
        if verb == "ap":
            return self._handle_approval_callback(cbq, data)
        if verb == "ms":
            return self._handle_mission_callback(cbq, data)
        if verb == "mo":
            _mo = self._mining_ui()
            if _mo is not None:
                return self._handle_mining_callback(cbq, data, _mo)
            # flag خاموش → سقوط به fallbackِ امروز (mo در _VERDICTS نیست → «نادیده»). parity.
        if verb == "m":
            _m2 = self._menu2()
            if _m2 is not None and _m2.enabled():
                return self._handle_menu2_callback(cbq, data, _m2)
            # flag خاموش → سقوط به fallbackِ امروز (m در _VERDICTS نیست → «نادیده»). parity.
        parts = data.split(":", 1)
        if len(parts) != 2 or parts[0] not in _VERDICTS:
            self._answer(cbq, "نادیده")
            return {"kind": "callback", "verdict": None}
        verb = parts[0]
        # P3 (D4): فلگ روشن → ok/no/later هم باید توکنِ HMACِ معتبر داشته باشند
        # (<verb>:<did>:<token>). tokenlessِ قدیمی/جعلی = رد (fail-closed، مثلِ ap:). این
        # کارت‌ها jobِ محتوایی/انقضا ندارند → action_hash/expires="". فلگ خاموش → مسیرِ قدیمی
        # بایت‌به‌بایت (did = _sanitize_id(parts[1])). is_owner از handle_update از قبل اول است.
        if cbtok.flag_on():
            seg = data.split(":")
            did = _sanitize_id(seg[1]) if len(seg) > 1 else ""
            token = seg[2] if len(seg) > 2 else None
            if not did or not self._cb_verify(token, did, verb, ""):
                self._answer(cbq, "توکنِ نامعتبر — کارت را از منو دوباره باز کن")
                return {"kind": "callback", "verdict": None, "rejected": "bad-token", "id": did}
        else:
            did = _sanitize_id(parts[1])
        rec = {"id": did, "verdict": verb, "ts": opslib.now_iso(), "source": "tg-center"}
        if verb == "ok":
            tok = _mint_ha_token(did)                # بی‌راز → None → ثبتِ بدونِ توکن
            if tok:
                rec["ha_token"] = tok
        recorded = self._record_approval(rec)
        # Wave1-A: همان رأیِ احرازشدهٔ مالک (کارتِ تصمیمِ ok/no/later) به‌شکلِ measurement
        # در OutcomeStoreِ پایدار هم می‌نشیند — پشتِ فلگ، fail-soft، later=deferred.
        self._durable_verdict_outcome(verb, did)
        _emit_event("task.completed",
                    summary=f"verdict {verb} ثبت شد",      # content-free (فقط کلید/فعل)
                    approval_state=_VERDICT_APPROVAL_STATE.get(verb, "unknown"),
                    trace_id=did, status="ok" if recorded else "warn")
        self._answer(cbq, _VERDICT_TOAST.get(verb, ""))
        return {"kind": "callback", "verdict": verb, "id": did, "recorded": recorded}

    def _durable_verdict_outcome(self, verdict: str, proposal_id: str,
                                 job: "dict | None" = None) -> "bool | None":
        """Wave1-A (Part2): رأیِ احرازشدهٔ مالک از همین update-handler → OutcomeStoreِ
        پایدار (measurement-only)، پشتِ OCTOPUS_WIRE_VERDICT_OUTCOME (پیش‌فرض خاموش؛
        خاموش → None و **صفر** side-effect — parity بایت‌به‌بایت با امروز).

        فقط بعد از گیتِ is_owner صدا زده می‌شود (غیرمالک هرگز به handlerها نمی‌رسد) و
        فقط واژگانِ سنجش: ok/no/later → accepted-measurement/rejected/deferred — هرگز
        approval/delivery/settle/revenue استنتاج نمی‌شود (نگاشت+ناوردی‌ها در
        verdict_recorder ِ مشترک enforce؛ idempotent روی corr|proposal|event_type →
        دو-تپ/replay رویدادِ نو نمی‌نویسد). شناسه‌های «موجود» (mission/leg/lead) حفظ
        می‌شوند، هیچ‌کدام اختراع نمی‌شوند؛ صفِ تأیید مبلغ ندارد → value=0 (بدونِ CLAIM).
        fail-soft: هر خطا → None؛ مسیرِ callback هرگز نمی‌میرد."""
        try:
            for _p in (str(_HERE.parent / "outcomes"), str(_HERE.parent / "spine")):
                if _p not in sys.path:
                    sys.path.insert(0, _p)
            import verdict_recorder as _vr   # lazy — flag خاموش → همین‌جا خروجِ امن
            if not _vr.flag_on():
                return None
            import outcome_store as _osx
            odir = opslib.STATE_DIR / "outcomes"
            odir.mkdir(parents=True, exist_ok=True)
            o = _osx.OutcomeStore(path=odir / "outcomes.db")
            spine = None
            try:   # هم‌الگوی live_loop (Sol-T4): dual-write به spine فقط با flagِ خودش
                import event_spine as _esx
                if _esx.flag_on():
                    sdir = opslib.STATE_DIR / "spine"
                    sdir.mkdir(parents=True, exist_ok=True)
                    spine = _esx.EventSpine(path=sdir / "spine.db")
            except Exception:  # noqa: BLE001
                spine = None
            try:
                j = job if isinstance(job, dict) else {}
                res = _vr.record_owner_verdict(
                    o, proposal_id=str(proposal_id), verdict=str(verdict),
                    correlation_id=j.get("correlation_id"),
                    mission_id=(j.get("mission_id")
                                or (str(proposal_id) if j.get("type") == "mission" else None)),
                    leg_id=j.get("leg_id") or j.get("leg") or "unknown",
                    value_aud_claimed=0.0,
                    event_spine=spine,
                    lead_id=j.get("lead_id") or j.get("attribution_id"),
                    source="tg-center")
                return bool(res.get("recorded"))
            finally:
                o.close()
                if spine is not None:
                    try:
                        spine.close()
                    except Exception:  # noqa: BLE001
                        pass
        except Exception:  # noqa: BLE001 — ثبتِ رأی هرگز مسیرِ دکمه را نمی‌کشد
            return None

    @staticmethod
    def _record_approval(rec: dict) -> bool:
        """الگوی approval-file: یک فایل per-decision (آخرین verdict) + jsonl ِ تاریخچه.
        اتمیک، fail-soft (شکست → False، هرگز crash)."""
        try:
            d = opslib.STATE_DIR / "telegram" / "approvals"
            d.mkdir(parents=True, exist_ok=True)
            p = d / f"{rec['id']}.json"
            tmp = p.with_suffix(".json.tmp")
            tmp.write_text(json.dumps(rec, ensure_ascii=False, indent=2), "utf-8")
            os.replace(tmp, p)
            opslib.append_jsonl(d / "approvals.jsonl", rec)
            return True
        except Exception:  # noqa: BLE001
            return False

    def _answer(self, cbq: dict, text: str = "") -> bool:
        """answer_callback — dismiss ِ spinner. fail-soft."""
        try:
            cid = cbq.get("id")
            if not cid:
                return False
            return bool(self._client.answer_callback(cid, text))
        except Exception:  # noqa: BLE001
            return False

    # ── run: یک دورِ poll+dispatch / حلقه با STOP ────────────────────────────────
    def run_once(self) -> int:
        """یک دورِ poll + dispatch. خروجی = تعدادِ updateهای پردازش‌شده.
        STOP/ناوصل → 0 (بدونِ هیچ فراخوانی). offset در config (restart-safe)."""
        if self.stopped() or not self._wired():
            return 0
        cfg = _load_config()
        try:
            offset = int(cfg.get("last_offset", 0) or 0)
        except (TypeError, ValueError):
            offset = 0
        try:
            ups = self._client.poll_updates(offset=offset, timeout_s=POLL_TIMEOUT_S) or []
        except Exception:  # noqa: BLE001 — خطای شبکه = دورِ خالی، حلقه زنده می‌ماند
            return 0
        n = 0
        max_id = offset - 1
        for u in ups:
            if not isinstance(u, dict):
                continue
            uid = u.get("update_id")
            if isinstance(uid, int) and uid > max_id:
                max_id = uid
            try:
                self.handle_update(u)
            except Exception:  # noqa: BLE001 — یک updateِ خراب حلقه را نمی‌کشد
                pass
            n += 1
        if max_id + 1 > offset:
            cfg["last_offset"] = max_id + 1
            _save_config(cfg)
        return n

    def run_forever(self, *, beat_every_s: float = 300.0) -> None:
        """حلقهٔ اصلی: poll پیوسته + beat دوره‌ای. ناوصل یا STOP → بازگشتِ فوری
        (حتی ensure_setup اجرا نمی‌شود — STOP مقدم بر همه‌چیز)."""
        if not self._wired() or self.stopped():
            return
        self.ensure_setup()
        # P3 (Stage-1، review-3): اگر قیدِ توکن روشن ولی OCTOPUS_CB_SECRET تنظیم نشده →
        # هشدارِ fail-soft (بدونِ echoِ مقدارِ secret). fail-closed از قبل برقرار است (توکن‌ها
        # verify نمی‌شوند → دکمه‌ها inert)؛ این فقط دیده‌شدنیِ misconfig را تأمین می‌کند.
        try:
            if cbtok.flag_on() and not cbtok.ready():
                import opslib as _ol
                _ol.alert(["⚠️ OCTOPUS_WIRE_CB_TOKEN روشن ولی OCTOPUS_CB_SECRET تنظیم نشده — "
                           "کارت‌های تأیید fail-closed/inert می‌مانند تا secret ست شود "
                           "(مقدارِ secret هرگز log نمی‌شود)."])
        except Exception:  # noqa: BLE001
            pass
        last_beat = 0.0
        while not self.stopped():
            self.run_once()
            now = float(self._clock())
            self._pulse(now)
            if now - last_beat >= float(beat_every_s):
                self.beat()
                last_beat = now

    # ── نبضِ زنده‌بودن (۲۰۲۶-۰۷-۲۹، رأیِ مالک) ──────────────────────────────
    # چرا: مرکز تا امروز **هیچ سیگنالِ زنده‌بودنی** نمی‌نوشت. عصرِ همین روز بین
    # ۲۰:۲۸ و ۲۰:۴۲ مرد و هیچ سطحی نفهمید — نه واچ‌داگ (شرطش «هر دو مرده» بود)
    # نه کابین. تنها ردِ حیاتش لاگِ ارسال بود که فقط وقتی چیزی می‌فرستد پر
    # می‌شود، پس سکوتِ سالم از مرگ جدا نبود.
    # قرارداد: هر تکرارِ حلقه، نوشتنِ اتمیک، fail-soft، **صفر شناسه/راز**.
    def _pulse(self, now: float) -> None:
        try:
            p = opslib.STATE_DIR / "pulse" / "tg-center.json"
            p.parent.mkdir(parents=True, exist_ok=True)
            tmp = p.with_suffix(".json.tmp")
            tmp.write_text(json.dumps(
                {"ts": opslib.now_iso(), "pid": os.getpid(), "mono": round(now, 1)},
                ensure_ascii=False), "utf-8")
            os.replace(tmp, p)
        except OSError:      # دیسکِ پر/قفل نباید مرکز را بکشد
            pass




def _introspect(which: str, text: str = "") -> str:
    """پلِ تنبل به `introspect_cmd`. importِ داخلِ تابع عمدی است: اگر آن ماژول
    نبود یا شکست، فقط این چهار فرمان یک جملهٔ فارسی می‌دهند و بقیهٔ مرکز
    دست‌نخورده می‌ماند (هیچ‌وقت importِ سطحِ فایل برای یک قابلیتِ جانبی)."""
    try:
        import introspect_cmd as _ic
        return {"flags": _ic.flags_text,
                "trace": lambda: _ic.trace_text(text),
                "scan": _ic.scan_text,
                "insight": _ic.insight_text}[which]()
    except Exception as exc:  # noqa: BLE001
        return f"🚩 خودنگری در دسترس نیست: {type(exc).__name__}: {exc}"

# ── قفلِ تک‌نمونه (۲۰۲۶-۰۷-۲۹، رأیِ مالک) ────────────────────────────────────
# چرا سوکت و نه فایلِ قفل: سیستم‌عامل موقعِ مرگِ پروسه خودش آزادش می‌کند، پس
# «قفلِ یتیمِ بعد از کرش» وجود ندارد — همان الگویی که organism/cortex/live از
# bindِ پورتشان مجانی می‌گیرند. مرکز HTTP لازم ندارد؛ این سوکت فقط mutex است.
#
# تلهٔ ویندوز (از کامنتِ organism._ExclusiveHTTPServer، جلسهٔ ۱۹): SO_REUSEADDR
# اجازهٔ double-bindِ ساکت می‌دهد. پس هرگز ست نمی‌شود و به‌جایش
# SO_EXCLUSIVEADDRUSE پیش از bind ست می‌شود.
CENTER_LOCK_PORT = int(os.environ.get("TG_CENTER_LOCK_PORT", "8776"))
_SINGLETON_SOCK = None      # ارجاعِ ماژول-سطح = قفل نگه‌داشته می‌شود (GC نبندَدش)


def acquire_singleton(port: int | None = None):
    """قفل را بگیر. برمی‌گرداند (sock, reason):

      (sock, None)          قفل گرفته شد — ارجاع را نگه دار وگرنه آزاد می‌شود
      (None, "in-use")      نمونهٔ دیگری زنده است → صدازننده باید تمیز خارج شود
      (None, "error: ...")  خطای غیرمنتظره → **قفل نگرفتیم ولی متوقف هم نمی‌کنیم**

    آن شاخهٔ سوم عمدی است: نبودِ قفل همان وضعِ پیش از امروز است (رگرسیون نیست)،
    ولی مرکزی که به‌خاطرِ یک ایرادِ سوکت اصلاً بالا نیاید رگرسیونِ واقعی است.
    """
    global _SINGLETON_SOCK
    import socket
    p = int(CENTER_LOCK_PORT if port is None else port)
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        if hasattr(socket, "SO_EXCLUSIVEADDRUSE"):
            s.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
        s.bind(("127.0.0.1", p))
        s.listen(1)
    except OSError as exc:
        s.close()
        if getattr(exc, "errno", None) in (48, 98, 10048) or "use" in str(exc).lower():
            return None, "in-use"
        return None, f"error: {type(exc).__name__}: {exc}"
    if port is None:
        _SINGLETON_SOCK = s      # فقط قفلِ واقعی سراسری می‌شود، نه قفلِ تست
    return s, None


if __name__ == "__main__":
    # مسیرِ رسمیِ لودِ .env (مثل model_router/approval_channel): بدونِ این،
    # TELEGRAM_* در os.environ نیست و رانر «not wired»ِ کاذب می‌دهد. fail-soft.
    try:
        import env_loader
        env_loader.load_env()
    except Exception:  # noqa: BLE001
        pass
    # قفلِ تک‌نمونه پیش از هر کارِ دیگر: دو مرکز روی یک توکن = 409 و بلعیدنِ
    # دکمه‌های همدیگر. شبِ ۰۷-۲۹ واقعاً رخ داد. اول قفل، بعد هر تصمیمِ دیگر.
    _lock, _why = acquire_singleton()
    if _why == "in-use":
        # حالتِ بیمار: پورت در دستِ *چیزِ دیگری* است و هیچ مرکزی نبض نمی‌زند.
        # بدونِ این چک، مرکز تا ابد رد می‌شود، واچ‌داگ بی‌وقفه دوباره راه
        # می‌اندازد، و کلِ ماجرا بی‌صداست — همان مرگِ نامرئی که امروز بستیم.
        try:
            import json as _j, time as _t
            _p = opslib.STATE_DIR / "pulse" / "tg-center.json"
            _age = (_t.time() - _p.stat().st_mtime) if _p.exists() else 1e9
            if _age > 180:
                opslib.alert([f"🚩 tg-center: پورتِ قفل {CENTER_LOCK_PORT} گرفته "
                              f"است ولی هیچ مرکزی {int(_age)}s نبض نزده — احتمالاً "
                              "برنامهٔ دیگری آن پورت را دارد. TG_CENTER_LOCK_PORT را "
                              "عوض کن وگرنه مرکز هرگز بالا نمی‌آید."])
        except Exception:  # noqa: BLE001
            pass
        print("tg-center: نمونهٔ دیگری روی قفلِ "
              f"127.0.0.1:{CENTER_LOCK_PORT} زنده است — خروجِ تمیز.")
        sys.exit(0)
    if _why:
        try:
            opslib.alert([f"⚠️ tg-center: قفلِ تک‌نمونه گرفته نشد ({_why}) — "
                          "بدونِ قفل ادامه می‌دهم (وضعِ پیش از ۰۷-۲۹). "
                          "اگر تکرار شد، دو مرکز ممکن است هم‌زمان بدوند."])
        except Exception:  # noqa: BLE001
            pass
    c = Center()
    if not c.wired():
        print("tg-center: not wired (TELEGRAM_BOT_TOKEN/چت پیکربندی نشده) — خروجِ امنِ no-op")
        sys.exit(0)
    if c.stopped():
        print("tg-center: STOP-TG-CENTER هست — اجرا نمی‌شوم")
        sys.exit(0)
    # عکسِ envِ همین پروسه سرِ boot (رأیِ مالک ۲۰۲۶-۰۷-۲۹) — `_ops` روی sys.path
    # نیست، پس append (نه insert) تا هیچ ماژولی سایه نیفتد. fail-soft مطلق.
    try:
        _ops_dir = str(_HERE.parent)
        if _ops_dir not in sys.path:
            sys.path.append(_ops_dir)
        import flag_drift
        flag_drift.snapshot_boot("center")
    except Exception:  # noqa: BLE001
        pass
    print("tg-center: زنده — kill تمیز: فایلِ _ops/STOP-TG-CENTER را بساز")
    c.run_forever()
    print("tg-center: ایستاد (STOP)")
