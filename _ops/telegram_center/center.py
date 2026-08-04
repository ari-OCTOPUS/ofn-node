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

# منوی command — منشورِ ۲۴-رأیی (TG-UI-CHARTER-2026-07-31 §۱ و §۶.۵):
# DM شخصی/وضعیتی است — بیزنس/قیفِ لید هرگز در منوی DM نیست و سقف ≤۱۰ فرمان.
# ۲۰۲۶-۰۷-۳۱ (رأی ۴، حذفِ بی‌رحمانه): بلوکِ ۹تاییِ قیفِ لید (lead/funnel/won/
# lost/paid/sent/replied/meeting/quote) + deal/revenue/id/box/code/doctrine/eq
# از منو خارج شدند — handlerهای تایپی سرِ جایشان ماندند (W3 مصرفشان می‌کند).
COMMANDS: list[tuple[str, str]] = [
    ("menu", "🎛 منوی فرماندهی — همه‌چیز از اینجا"),
    ("now", "📊 وضعیت — همین حالا"),
    ("live", "🐙 خلاصهٔ زنده‌بودن (flags + هویت + جعبه‌سیاه)"),
    ("missions", "🧬 مأموریت‌ها — Mission Genome"),
    ("verdicts", "🗳 رأی‌هایی که دیگر سؤال نیستند"),
    ("stuck", "💰 پرداخت‌های نیمه‌کاره"),
    ("x", "🗂 هر چیزی که می‌توانم نشانت بدهم"),
    ("budget", "🐙 پیشنهادِ تخصیصِ ماهِ بعد (propose-only)"),
]

# scope ِ منوها (قاعدهٔ UX §۶.۵: منوی گروه ≠ منوی DM). منوی تلگرام فقط
# فرمانِ اسلشِ لاتین می‌پذیرد؛ رابطِ گروه فارسیِ طبیعیِ LEG_VERBS است ⇒
# منوی گروه باید **خالی** باشد (deleteMyCommands روی scope گروه‌ها).
MENU_SCOPE_PRIVATE = {"type": "all_private_chats"}
MENU_SCOPE_GROUPS = {"type": "all_group_chats"}

# فرمان‌های جدولِ خودِ مرکز (کلیدهای handlers در _handle_message) — برای اینکه
# مامور (owner_console) هرگز فرمانِ اسلشِ شناخته‌شده را قبل از جدول نبلعد
# (یافتهٔ outer-bot-4: /menu و /start هرگز به _page نمی‌رسیدند).
_CENTER_SLASH = frozenset({
    "/now", "/budget", "/revenue", "/missions", "/menu", "/start", "/live",
    "/id", "/eq", "/box", "/code", "/doctrine", "/deal", "/lead", "/verdicts",
    "/stuck", "/x", "/توان", "/won", "/lost", "/paid", "/sent", "/replied",
    "/meeting", "/quote", "/funnel", "/رفتار", "/کد", "/flags", "/trace",
    "/scan", "/insight",
})

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
    """نوشتنِ اتمیکِ config با fsync و retry — شکست → False **و صدادار**.

    ⚠️ ۲۰۲۶-۰۷-۳۱ (یافتهٔ دیباگ W1): این تابع کپیِ دستیِ idiom بود و سخت‌سازیِ
    `opslib.LockedJson.write` (VQ-STATE-WRITE-001: fsync + retry روی
    `os.replace` ِ گذرا-شکسته) هرگز به آن نرسید. این فایل **هر نشانگرِ منو،
    هر cursor و هر شناسهٔ کارت** را نگه می‌دارد؛ یک قفلِ گذرای آنتی‌ویروس
    یعنی از دست رفتنِ بی‌صدای همان‌ها (بریفِ دوباره، کارتِ گم‌شده، منوی
    دوباره‌ثبت‌شده). حالا: تا ۴ تلاش با backoff، fsync قبل از replace، و
    شکستِ دائمی یک هشدارِ واقعی می‌دهد (نه فقط False ِ خاموش)."""
    p = _config_path()
    payload = None
    try:
        payload = json.dumps(cfg, ensure_ascii=False, indent=2)
        p.parent.mkdir(parents=True, exist_ok=True)
    except (OSError, TypeError, ValueError) as e:  # noqa: BLE001
        try:
            opslib.alert([f"tg-center: ساختِ payload ِ config شکست: {type(e).__name__}"])
        except Exception:  # noqa: BLE001
            pass
        return False
    tmp = p.with_suffix(".json.tmp")
    last = None
    for attempt in range(4):
        try:
            with open(tmp, "w", encoding="utf-8") as fh:
                fh.write(payload)
                fh.flush()
                os.fsync(fh.fileno())      # دوامِ واقعی، نه صرفاً بافرِ OS
            os.replace(tmp, p)
            return True
        except OSError as e:               # noqa: PERF203 — قفلِ AV گذراست
            last = e
            if attempt < 3:
                time.sleep(0.15 * (2 ** attempt))
    try:
        opslib.alert(["🚩 tg-center: نوشتنِ center-config پس از ۴ تلاش شکست "
                      f"({type(last).__name__}) — نشانگرها/cursorها به‌روز نشدند"])
    except Exception:  # noqa: BLE001 — هشدار هرگز مسیرِ ارسال را نمی‌کشد
        pass
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

# ── کارگرِ ویس: کارِ کند از حلقهٔ poll بیرون ─────────────────────────────────
# اندازه‌گیریِ ۲۰۲۶-۰۸-۰۱: ویسِ ۵ ثانیه‌ای مالک ۲۲.۶ ثانیه transcription برد و
# چون `_capture_hook` داخلِ `_handle_message` و آن داخلِ dispatch است، مرکز در
# تمامِ آن مدت به هیچ پیام و هیچ دکمه‌ای جواب نمی‌داد. با مدلِ `medium` (رأیِ
# مالک، ~۳ برابر کندتر) یک ویسِ نیم‌دقیقه‌ای بات را چند دقیقه می‌خواباند — و از
# بیرون، باتِ خواب با باتِ مرده یک شکل است.
#
# یک کارگر، نه استخر: transcription روی CPU است و دوتا هم‌زمان فقط هر دو را کند
# می‌کند. صف کوچک است؛ پرشدنش یعنی برگرد به همان مسیرِ همگام (کندی بهتر از
# گم‌شدنِ ویسِ مالک).
VOICE_QUEUE_MAX = 8

# ── لِینِ مغز (۲۰۲۶-۰۸-۰۳) ──────────────────────────────────────────────────
# ممیزیِ ۰۸-۰۳ اندازه گرفت: یک پیامِ آزادِ مالک می‌تواند **۲۳۵ ثانیه** مرکز را کر
# کند — `ask_brain` مستقیم به Fugu می‌رود (`OCTOPUS_TG_CHAT_LOCAL` ست نیست)، و
# زنجیرهٔ timeout ِ ۶۱.۵s + ۵۴s + ۱۲۰s روی همان تک‌رشتهٔ poll می‌نشیند. در تمامِ
# آن مدت هیچ دکمه‌ای در هیچ تاپیکی answerCallbackQuery نمی‌گیرد.
#
# **لِینِ جدا، نه صفِ مشترک با ویس.** ویس CPU-bound است (transcription) و باید
# سریال بماند؛ فراخوانِ مغز شبکه‌ای و تا ۲۷۰ ثانیه است. یک صفِ مشترک یعنی یک
# Fugu ِ کند، ویسِ مالک را پشتِ خودش حبس می‌کند.
BRAIN_QUEUE_MAX = 4

#: lane → (queue, thread). یک پیاده‌سازی، چند لِینِ نام‌دار — نه چند کپیِ کارگر.
_BG_LANES: dict = {}


def _bg_queue(lane: str, maxsize: int):
    """صفِ لِین را (تنبل) بساز و نخش را زنده نگه دار. None = نشد ⇒ همگام.

    ۲۰۲۶-۰۸-۰۳: تعمیمِ کارگرِ ویس. رفتارِ لِینِ `voice` بایت‌به‌بایتِ قبلی است
    (همان نامِ نخ `tg-voice-worker`، همان maxsize، همان fail-soft)."""
    try:
        import queue as _queue
        import threading as _threading
    except Exception:  # noqa: BLE001
        return None
    q, th = _BG_LANES.get(lane, (None, None))
    if q is None:
        q = _queue.Queue(maxsize=maxsize)
    if th is None or not th.is_alive():
        def _loop(_q=q, _lane=lane):
            while True:
                job = _q.get()
                if job is None:
                    return
                try:
                    job()
                except Exception as e:  # noqa: BLE001 — کارگر هرگز نمی‌میرد
                    try:
                        opslib.alert(["%s-worker: %s" % (_lane, type(e).__name__)])
                    except Exception:  # noqa: BLE001
                        pass
                finally:
                    _q.task_done()
        th = _threading.Thread(target=_loop, name="tg-%s-worker" % lane,
                               daemon=True)
        th.start()
    _BG_LANES[lane] = (q, th)
    return q


def _submit_bg_job(lane: str, job, maxsize: int) -> bool:
    """کار را به لِین بده. False = نشد ⇒ صداکننده همگام انجامش دهد.

    صفِ پر عمداً **همگام** برمی‌گردد نه بلاک: کندیِ یک پیام بهتر از گم‌شدنش است،
    و بلاک‌شدنِ اینجا دقیقاً همان کر‌شدنی است که این لِین آمده رفعش کند."""
    q = _bg_queue(lane, maxsize)
    if q is None:
        return False
    try:
        q.put_nowait(job)
        return True
    except Exception:  # noqa: BLE001 — صفِ پر = مسیرِ همگام
        return False


def _voice_queue():
    """سازگاریِ عقب‌رو — همان لِینِ `voice`."""
    return _bg_queue("voice", VOICE_QUEUE_MAX)


def _submit_voice_job(job) -> bool:
    """کار را به کارگر بده. False = نشد ⇒ صداکننده همگام انجامش دهد."""
    return _submit_bg_job("voice", job, VOICE_QUEUE_MAX)


def _submit_brain_job(job) -> bool:
    """کارِ مدل‌محور را از حلقهٔ poll بیرون ببر. False ⇒ مسیرِ همگامِ قبلی."""
    return _submit_bg_job("brain", job, BRAIN_QUEUE_MAX)

# ── /ops دکمه‌ای (لِینِ chat-actions) — فلگ، مارکرها، واژگانِ toast ─────────────
# فلگِ نو، پیش‌فرض **خاموش** و عمداً بیرونِ wiring.PAPER_FULL_FLAGS: خاموش یعنی
# `/ops` دقیقاً همان پیامِ بی‌کیبوردِ امروز است، `ops:` هرگز به روترِ callback
# نمی‌رسد، و ریپلای‌ها نادیده می‌مانند — parity بایت‌به‌بایت.
OPS_BUTTONS_FLAG = "OCTOPUS_TG_OPS_BUTTONS"
# مارکرهای پایدارِ ورودی — همان الگوی question_budget («سؤالِ اختاپوس»): ورودیِ
# جهش از **ریپلای به پیامِ نشان‌دار** می‌آید نه از ماشینِ حالتِ نو. تلگرام تگِ
# HTML را در reply-text می‌اندازد، پس مارکر عمداً متنِ ساده است نه تگ.
OPS_ASK_LEAD = "OPS-NEW-LEAD"
OPS_ASK_MONEY = "OPS-REC-MONEY"
# سقفِ هندلِ لید: `ops_actions.make_id` شناسه را `lead_<handle>` می‌سازد و
# callbackِ دکمهٔ پیگیری (`ops:t:<lead_id>`) باید زیرِ سقفِ ۶۴ بایتیِ تلگرام
# بماند: len("ops:t:")۶ + len("lead_")۵ + ۴۰ = ۵۱.
OPS_HANDLE_MAX = 40
_OPS_FA2EN = str.maketrans("۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩", "01234567890123456789")
_OPS_TOAST = {"APPLIED": "ثبت شد ✅",
              "DUPLICATE": "قبلاً ثبت شده بود — دوباره نساختم 🔁",
              "DENIED": "اجازه نیست",
              "BLOCKED": "رد شد"}


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

    @staticmethod
    def _menu_hash() -> str:
        """هشِ محتواییِ منوی DM (فهرست + scope) — نشانگرِ ثبتِ مجدد."""
        import hashlib as _hl
        base = json.dumps([list(COMMANDS), MENU_SCOPE_PRIVATE],
                          ensure_ascii=False, sort_keys=True)
        return _hl.sha256(base.encode("utf-8")).hexdigest()[:16]

    # ── نیتِ مقصدِ ارسال (ratchet ِ tg_send_audit) ──────────────────────────
    # DM و General ِ فوروم تاپیک ندارند؛ topic_id=None آن‌جا **درست** است ولی
    # از ارسالِ سرگردانِ بی‌تاپیک (که در General می‌نشیند) قابلِ‌تفکیک نبود.
    # این دو resolver همان None را با **نامِ نیت** می‌دهند تا هر سایتِ ارسال
    # مقصدش را اعلام کند و ممیزِ ایستا سایتِ بی‌نیت را جدا بشمارد.
    def _dm_topic(self):
        """مقصد by-design = DM ِ مالک (بدونِ تاپیک)."""
        return None

    def _general_topic(self):
        """مقصد by-design = General ِ گروه (پیامِ پین‌شدهٔ سراسری، بدونِ تاپیک)."""
        return None

    def _leg_pausable(self, leg: str) -> bool:
        """آیا این پا دکمهٔ ⏸/▶️ می‌گیرد؟ فقط اعضای power.PAUSABLE_LEGS.
        نبودِ power ⇒ False (به‌سمتِ دکمهٔ کمتر می‌افتد، نه دکمهٔ مرده — گروه ۵ِ اسکن)."""
        try:
            import power as _pw
            return str(leg) in tuple(getattr(_pw, "PAUSABLE_LEGS", ()))
        except Exception:  # noqa: BLE001
            return False

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
        fail-soft. صفر settle/effector — فقط ناوبریِ منو (render).

        گزینهٔ ② (قرارداد ORPHANS A1): «m:mission» **قبل از** dispatch به درِ
        واقعی می‌رسد — owner_menu.handle_panel_choice (kind == "prompt") — و
        متنِ بعدیِ مالک را _awaiting_mission مصرف می‌کند (الگوی
        _awaiting_counter؛ RAM، ری‌استارت = لغوِ امن). فقط kind == "delegate"
        حق دارد به menu_integration.dispatch سقوط کند (A3)."""
        msg = cbq.get("message") or {}
        mid = msg.get("message_id")
        chat = (msg.get("chat") or {}).get("id")
        if str(data or "") == "m:mission":
            try:
                import owner_menu as _om
                _out = _om.handle_panel_choice("m:mission", "")
                self._awaiting_mission = True
                if isinstance(mid, int):
                    self._client.edit(mid, _scrub(str(_out.get("text") or "")),
                                      keyboard=_out.get("keyboard"),
                                      chat_id=chat)
            except Exception:  # noqa: BLE001 — پنلِ شکسته هرگز dispatch را نمی‌کشد
                pass
            self._answer(cbq, "متنِ مأموریت را بنویس")
            return {"kind": "menu2", "data": data, "panel": "mission-prompt"}
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

    def _shell_cmd(self, text: str) -> str:
        """`/sh <فرمان>` — درِ شلِ خام. رأیِ صریحِ مالک ۲۰۲۶-۰۸-۰۴.

        این‌جا **هیچ گیتی پیاده نمی‌شود** و این عمدی است: فعال‌سازی، کیل‌سوییچ،
        deny-list و رسید همه در `shell_capability` هستند. یک کپیِ دومِ گیت در
        این‌جا یعنی دو تعریف از «مجاز» — و همان چیزی است که این مخزن مکرر
        گرفتارش شده. تنها کارِ این تابع: متن → `run()` → متنِ خوانا.

        مالکیت از قبل بالادست (`handle_update → _is_owner`) گیت شده.
        """
        cmd = str(text or "").split(None, 1)
        cmd = cmd[1].strip() if len(cmd) > 1 else ""
        try:
            import sys as _s
            _p = str(_HERE.parent)
            if _p not in _s.path:
                _s.path.insert(0, _p)
            import shell_capability as _sh  # noqa: WPS433
        except Exception as e:  # noqa: BLE001
            return f"🖥 ماژولِ شل در دسترس نیست ({type(e).__name__})."

        if not cmd:
            ok, why = _sh.active()
            tail = _sh.audit_tail(5)
            lim = _sh.limits()          # مرزها را **ماژول** اعلام می‌کند، نه در
            lines = [f"🖥 <b>شلِ خام</b> — {'🟢 فعال' if ok else '🔴 ' + why}",
                     f"ریشه: <code>{lim['cwd']}</code>",
                     f"سقف: {int(lim['timeout_s'])}s · {lim['max_output'] // 1000}KB · "
                     f"{lim['deny_rules']} قاعدهٔ ممنوعه (§۰ منشور)",
                     "مصرف: <code>/sh git status</code>"]
            if tail:
                lines.append("──────────")
                for r in tail[-5:]:
                    lines.append(f"· {str(r.get('ts'))[11:19]} "
                                 f"{r.get('phase')} — {_scrub(str(r.get('cmd'))[:44])}")
            return "\n".join(lines)

        r = _sh.run(cmd, reason="/sh از تلگرام")
        if not r.get("ran"):
            return f"🛑 اجرا نشد.\n▸ {_scrub(str(r.get('reason')))}"
        head = ("✅" if r.get("ok") else "⚠️") + f" کد={r.get('code')} · {r.get('ms')}ms"
        body = (r.get("stdout") or "") + (("\n[stderr]\n" + r["stderr"]) if r.get("stderr") else "")
        body = body.strip() or "(بدونِ خروجی)"
        # سقفِ تلگرام ۴۰۹۶ — بریدنِ وسطِ تگ یک‌بار هر دایجست را ۴۰۰ کرد.
        if len(body) > 3300:
            body = body[:3300] + "\n…(بریده شد)"
        return f"{head}\n<pre>{_scrub(body)}</pre>"

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

        # منوی commandها — scope-دار (منشور §۶.۵) و ثبتِ مجدد با **محتوا** نه فقط
        # طول (commands_set_v2 = هشِ فهرست+scope؛ عوض‌کردنِ متنِ توضیح هم باید
        # روی بات بنشیند — نشانگرِ طولی آن را نمی‌دید). نشانگرِ طولیِ قدیمی هم
        # نگه داشته می‌شود (گاردِ discoverability همان را متن‌سنجی می‌کند).
        _menu_hash = self._menu_hash()
        if (cfg.get("commands_set") != len(COMMANDS)
                or cfg.get("commands_set_v2") != _menu_hash):
            try:
                ok = bool(self._client.set_commands(
                    list(COMMANDS), scope=dict(MENU_SCOPE_PRIVATE)))
            except TypeError:
                # کلاینتِ قدیمی بدونِ scope — منو ثبت می‌شود ولی سراسری (fallback).
                try:
                    ok = bool(self._client.set_commands(list(COMMANDS)))
                except Exception:  # noqa: BLE001
                    ok = False
            except Exception:  # noqa: BLE001
                ok = False
            if ok:
                cfg["commands_set"] = len(COMMANDS)
                cfg["commands_set_v2"] = _menu_hash
                dirty = True
        # منوی گروه = خالی (منوی تلگرام لاتین-اسلش است؛ رابطِ گروه فارسیِ
        # طبیعی است — LEG_VERBS). فقط یک‌بار به‌ازای هر تغییرِ منو.
        if cfg.get("commands_group_cleared_v2") != _menu_hash:
            _del = getattr(self._client, "delete_commands", None)
            ok_g = False
            if callable(_del):
                try:
                    ok_g = bool(_del(scope=dict(MENU_SCOPE_GROUPS)))
                except Exception:  # noqa: BLE001
                    ok_g = False
            if ok_g:
                cfg["commands_group_cleared_v2"] = _menu_hash
                dirty = True
        # scope ِ default هم باید خالی شود — لیستِ کهنهٔ ۲۴تایی روی سرورِ تلگرام
        # می‌مانَد و گروه‌ها (که scope ِ گروهی‌شان خالی است) به آن fallback
        # می‌کنند (کشفِ readback ِ deploy ِ ۰۷-۳۱: private=۸ ولی default=۲۴ کهنه).
        if cfg.get("commands_default_cleared_v2") != _menu_hash:
            _del2 = getattr(self._client, "delete_commands", None)
            ok_d = False
            if callable(_del2):
                try:
                    ok_d = bool(_del2())          # بدونِ scope = default
                except Exception:  # noqa: BLE001
                    ok_d = False
            if ok_d:
                cfg["commands_default_cleared_v2"] = _menu_hash
                dirty = True
        # منوی باتِ inner دیگر از مرکز push نمی‌شود (outer-bot-12: دو نویسنده
        # با دو فهرستِ متفاوت روی یک بات = race ِ بی‌صدا). تک-نویسنده =
        # approval_channel در پروسهٔ organism.

        # پیامِ statusِ پین‌شده — فقط یک‌بار ساخته می‌شود؛ بعداً فقط edit (beat)
        if not isinstance(cfg.get("status_message_id"), int):
            text = self._status_text() or "🐙 مرکزِ فرماندهی — راه‌اندازی…"
            try:
                mid = self._client.send(_scrub(text), chat_id=chat_id,
                                        topic_id=self._general_topic(), pin=True)
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
                                              topic_id=self._general_topic(),
                                              pin=True)
                except Exception:  # noqa: BLE001
                    _gmid = None
                if isinstance(_gmid, int):
                    cfg["guide_message_id"] = _gmid
                    cfg["guide_hash"] = _gh
                    dirty = True
        except Exception:  # noqa: BLE001 — راهنما هرگز راه‌اندازی را نمی‌کشد
            pass

        # ── رسیدِ مرگ/بازگشت (۲۰۲۶-۰۷-۳۱، یافتهٔ منتقدِ اسکن) ─────────────────
        # امروز باتِ بیرونی ۳ ساعت و ۵۳ دقیقه مرده بود («centre down (silent
        # 14006s)») و واچ‌داگ احیایش کرد — ولی مالک **هرگز نفهمید**، چون اعلانِ
        # واچ‌داگ به event_bridge می‌رود که cursor اش اصلاً وجود ندارد. حالا
        # خودِ مرکز در بوت لاگِ واچ‌داگ را می‌خوانَد: اگر آخرین خطِ «launching»
        # تازه‌تر از آخرین رسیدِ داده‌شده باشد، یک خطِ کوتاه به DM ِ مالک
        # می‌گوید که مُرد و برگشت — با مدتِ سکوت. dedupe با cursor در config،
        # پس ری‌استارتِ عادی (بدونِ خطِ launching ِ تازه) هیچ نمی‌فرستد.
        try:
            _wl = opslib.STATE_DIR / "tg-center-watchdog-log.txt"
            if _wl.exists():
                _lines = [ln for ln in
                          _wl.read_text("utf-8", errors="replace").splitlines()
                          if "launching" in ln]
                if _lines:
                    _last = _lines[-1]
                    if _last != cfg.get("watchdog_receipt_cursor"):
                        _own2 = getattr(self._client, "owner_chat_id", None)
                        # VQ-DEATH-RECEIPT-LIES-001 (۲۰۲۶-۰۸-۰۴). این پیام دو
                        # چیزِ نادرست به مالک می‌گفت:
                        #
                        # (۱) عددِ جعلی. `tg-center-watchdog.ps1` مقدارِ
                        #     `silent 999999s` را هم به‌عنوانِ **سنتینلِ
                        #     «نامعلوم»** می‌نویسد (پیش‌فرضِ اولیه و مقدارِ
                        #     catch، یعنی «فایلِ نبض خوانده نشد»). این‌جا
                        #     `int(999999/60)` می‌شد **۱۶۶۶۶ دقیقه ≈ ۱۱٫۶ روز**
                        #     و به‌عنوان یک اندازه‌گیری روی گوشی می‌نشست. دو تا
                        #     از هشت قطعیِ ثبت‌شده همین سنتینل را داشتند.
                        #
                        # (۲) ادعای «ندیده‌ام» **بی‌پایه** بود. `run_once`
                        #     ‏`last_offset` را از config می‌خواند، dispatch
                        #     می‌کند، و **بعد** ذخیره می‌کند — یعنی صف بازپخش
                        #     می‌شود. طولانی‌ترین قطعیِ ثبت‌شده ۵٫۶۷ ساعت است،
                        #     خیلی داخلِ نگه‌داریِ ~۲۴ ساعتهٔ تلگرام. پس مالک
                        #     چیزهایی را دوباره می‌فرستاد که رسیده بودند — و
                        #     همین حسِ «دیده نمی‌شوم» را می‌ساخت.
                        #
                        # رسید حذف نشد (قطعیِ واقعی باید دیده شود)، فقط دیگر
                        # دروغ نمی‌گوید. صدای صادقِ گم‌شدنِ واقعی حالا
                        # `_dead_letter` است.
                        _m = re.search(r"silent (\d+)s", _last)
                        _s = int(_m.group(1)) if _m else None
                        if _s is None:
                            _dur = ""
                        elif _s >= 999999:
                            _dur = " — مدتش نامعلوم"
                        else:
                            _dur = f" — {_fa_num(int(_s / 60))} دقیقه ساکت بودم"
                        _txt = ("🩹 <b>مرده بودم و واچ‌داگ برم گرداند</b>"
                                f"{_dur}.\nصفِ پیام‌ها از نشانگرِ ذخیره‌شده "
                                "بازپخش شد، پس چیزی که فرستادی باید رسیده باشد. "
                                "اگر پیامی واقعاً پردازش نشود، جداگانه خبرت "
                                "می‌کنم.")
                        _sent2 = None
                        if _own2 is not None:
                            try:
                                _sent2 = self._client.send(
                                    _scrub(_txt), chat_id=_own2,
                                    topic_id=self._dm_topic())
                            except Exception:  # noqa: BLE001
                                _sent2 = None
                        if _sent2 is not None:
                            cfg["watchdog_receipt_cursor"] = _last
                            dirty = True
        except Exception:  # noqa: BLE001 — رسید هرگز راه‌اندازی را نمی‌کشد
            pass

        # ── رسیدِ بوت با نسخه (۲۰۲۶-۰۷-۳۱، حکمِ ضدِ فراموشیِ مالک) ────────────
        # هر بوتِ تازه (نه فقط بعدِ مرگِ واچ‌داگ) **یک خط** به DM: زنده‌ام —
        # PID + HEAD ِ کوتاهِ git + شمارِ فلگ‌های مسلحِ OCTOPUS_. dedupe با
        # pid در config: همان پروسه دوبار نمی‌گوید؛ پروسهٔ نو = بوتِ نو.
        try:
            _own3 = getattr(self._client, "owner_chat_id", None)
            _pid = os.getpid()
            if _own3 is not None and cfg.get("boot_receipt_pid") != _pid:
                _head = ""
                try:
                    import subprocess as _sp
                    _hv = _sp.run(["git", "rev-parse", "--short", "HEAD"],
                                  cwd=str(opslib.ORG_ROOT),
                                  capture_output=True, timeout=2)
                    if _hv.returncode == 0:
                        _head = _hv.stdout.decode("ascii", "replace").strip()
                except Exception:  # noqa: BLE001 — بی‌git ⇒ «نامعلوم»، نه سکوت
                    _head = ""
                _nf = sum(1 for _k, _v in os.environ.items()
                          if _k.startswith("OCTOPUS_") and
                          str(_v).strip().lower() in ("1", "true", "yes", "on"))
                _ver = f"⁦{_head}⁩" if _head else "نامعلوم"
                _bl = (f"🟢 بیدار شدم — PID ⁦{_pid}⁩ · نسخه: {_ver}"
                       f" · فلگِ فعال: {_fa_num(_nf)}")
                _bs = None
                try:
                    _bs = self._client.send(_scrub(_bl), chat_id=_own3,
                                            topic_id=self._dm_topic())
                except Exception:  # noqa: BLE001
                    _bs = None
                if _bs is not None:
                    cfg["boot_receipt_pid"] = _pid
                    dirty = True
        except Exception:  # noqa: BLE001 — رسیدِ بوت هرگز راه‌اندازی را نمی‌کشد
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
                    # بودجهٔ اعلان (منشور §۳): kind="card". سرریز ⇒ متنِ کارت
                    # در digest می‌نشیند و seen جلو می‌رود — تحویلِ digestی هم
                    # تحویل است (وگرنه هر ضربان دوباره defer = digest ِ تکراری).
                    m, _handed = self._budgeted_send(
                        "card", txt,
                        lambda _t=txt, _k=kb: self._route_send(
                            "center-decision", _t, cfg=cfg, keyboard=_k))
                except Exception:  # noqa: BLE001
                    m, _handed = None, False
                if _handed:
                    seen.append(did)
                    out["decisions"] += 1
                    dirty = True
            cfg["seen"] = seen[-SEEN_CAP:]

        # ── امیترِ کارت‌های decision_gate (رفعِ outer-bot-7؛ قرارداد ORPHANS B) ──
        # هندلرِ dg:e از قبل بود ولی هیچ امیتری نبود — دفترِ تصمیم پر می‌شد و
        # مالک هرگز کارتی نمی‌دید. گیت: فلگِ خودِ ماژول (OCTOPUS_WIRE_DECISION_GATE؛
        # B5: گیت روی beat، نه روی ماژول) — فلگ خاموش = بایت‌به‌بایتِ امروز.
        # B1: جریانِ center-decision (outer/DM — دکمه‌دار هرگز روی inner).
        # B2: _tok_kb اجباری. B3: نشانگر فقط بعدِ تحویلِ تأییدشده (mid ِ واقعی
        # یا defer ِ تأییدشدهٔ بودجه — هر دو handoff ِ تأییدشده‌اند). B4: صفرِ
        # کارت با last_scan در خروجیِ beat قابلِ‌مشاهده می‌شود، نه نامرئی.
        try:
            import decision_gate as _dgm
            if _dgm.enabled():
                try:
                    _dgcur = float(cfg.get("dg_cursor", 0.0) or 0.0)
                except (TypeError, ValueError):
                    _dgcur = 0.0
                _dgadv = _dgcur
                _dgcards = _dgm.pending_cards(now=now, limit=3, since=_dgcur)
                if not _dgcards:
                    out["dg_scan"] = _dgm.last_scan()
                for _cd in _dgcards:
                    _ckb = self._tok_kb(_cd.get("keyboard"))
                    _ctxt = str(_cd.get("text") or "")
                    _cm, _chand = self._budgeted_send(
                        "card", _ctxt,
                        lambda _t=_ctxt, _k=_ckb: self._route_send(
                            "center-decision", _t, cfg=cfg, keyboard=_k))
                    if not _chand:
                        break                # تحویل نشد ⇒ نشانگر جلو نمی‌رود
                    _dgadv = max(_dgadv, float(_cd.get("ts") or 0.0))
                    out["decisions"] += 1
                if _dgadv > _dgcur:
                    cfg["dg_cursor"] = _dgadv
                    dirty = True
        except Exception:  # noqa: BLE001 — امیترِ کارت هرگز beat را نمی‌کشد
            pass
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
        # ── VQ-MISSION-APPROVAL-001: کارتِ A3 ِ پلِ اقدام → صفِ تأیید → حکم ────
        # فقط در همین پروسه (invariant ِ approval_store: مصرفِ تک‌پروسه‌ای —
        # S1-05 t_o). فلگ غایب=خاموش؛ الگوی doctor_link: صفر poller ِ نو.
        try:
            import mission_approval_bridge as _mab
            if _mab.enabled():
                _mab.beat(now=now)
        except Exception:  # noqa: BLE001 — پلِ تأیید هرگز beat را نمی‌کشد
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
                    # (۲۰۲۶-۰۷-۳۱، رفعِ inner-5) — نشانگر فقط بعد از ارسالِ موفق
                    # جلو می‌رود، دقیقاً مثلِ مسیرِ urgent بالا. تا اینجا flush_digest
                    # خودش نشانگر را قبل از ارسال جلو می‌برد ⇒ یک ارسالِ شکست‌خورده
                    # آن ساعت را برای همیشه گم می‌کرد.
                    _dmid = self._route_send("center-health-digest", _dg, cfg=cfg)
                    if _dmid is not None:
                        _hp.mark_digest_flushed(now=now)
        except Exception:  # noqa: BLE001 — تحویلِ hold-policy هرگز beat را نمی‌کشد
            pass
        # ── لِین E (موج ۲): یادآوری‌ها + بریفِ صبح/شب — سوارِ همین beat ─────────
        # هر دو پشتِ فلگِ خودشان (پیش‌فرض خاموش). شکستِ ارسال داخلِ callback
        # عمداً استثنا می‌شود (نه بلعیده) تا reminders آن آیتم را fired نکند و
        # brief روزِ خود را سوخته حساب نکند — ضربانِ بعد دوباره می‌کوشد.
        try:
            import reminders as _rm
            if _rm.enabled():
                _rm.beat(now=now,
                         send_dm_fn=lambda text, rid:
                             self._reminder_dm_send(text, rid),
                         send_leg_fn=lambda leg, text:
                             self._reminder_leg_send(leg, text, cfg))
        except Exception:  # noqa: BLE001 — یادآور هرگز beat را نمی‌کشد
            pass
        try:
            import brief as _bf
            if _bf.enabled():
                # brief.beat cursorهایش را داخلِ همین cfg می‌نویسد (الگوی
                # last_pulse) — ذخیرهٔ فوری، وگرنه ری‌استارت = بریفِ دوباره.
                if _bf.beat(now=now, cfg=cfg,
                            send_dm_fn=self._dm_send_strict, state=cfg):
                    _save_config(cfg)
        except Exception:  # noqa: BLE001 — بریف هرگز beat را نمی‌کشد
            pass
        # ── لِین H (موج ۲/۴): مرورِ هفتگیِ شنبه + بودجهٔ ۳۰-سؤالی ──────────────
        try:
            import weekly_review as _wr
            if _wr.beat(now=now, cfg=cfg, send_dm_fn=self._dm_send_strict,
                        state=cfg):
                _save_config(cfg)      # cursor ِ هفته فقط بعدِ ارسالِ موفق
        except Exception:  # noqa: BLE001 — مرورِ هفتگی هرگز beat را نمی‌کشد
            pass
        # ── لِینِ ASKS: تولیدِ سؤال (ثبت است، نه تحویل) ──────────────────
        # عمداً بی‌فلگ و **قبل از** بلوکِ تحویل: درسِ «ثبت را گیت نکن، تحویل
        # را» — اگر scan پشتِ فلگ برود، صفی که فلگ قرار است آزادش کند هرگز پر
        # نمی‌شود. throttle (۹۰۰s) داخلِ خودِ ماژول است؛ آیتمِ error بلند
        # می‌شود، نه بی‌صدا (دکترینِ صداقت).
        try:
            import question_producers as _qp
            for _it in _qp.scan(now=now):     # throttle داخلِ خودِ ماژول
                if _it.get("status") == "error":
                    opslib.alert([f"question_producers: {_it.get('error')}"])
        except Exception:  # noqa: BLE001 — تولیدِ سؤال هرگز beat را نمی‌کشد
            pass
        try:
            import question_budget as _qb
            if _qb.enabled():
                _qi = _qb.pending(now)
                # (بازبینی ۰۷-۳۱، wiring-4) گاردِ نشتِ General: بدونِ DM ِ
                # مالک (owner_chat_id غایب/falsy) این ضربان اصلاً ارسال
                # نمی‌شود — chat_id=None در client به chat ِ پیش‌فرض (گروه)
                # می‌افتاد و سؤالِ هسته‌ای در General می‌نشست. بودجه هم
                # نمی‌سوزد؛ ضربانِ بعد (با DM ِ برگشته) دوباره می‌کوشد.
                _own_qb = getattr(self._client, "owner_chat_id", None)
                if _qi and _own_qb:
                    # بودجهٔ اعلان (منشور §۳): kind="question" قطع‌کننده است.
                    # سرریز ⇒ متنِ سؤال (با مارکرِ Q-n) در digest می‌نشیند و
                    # mark_asked می‌خورد — ریپلای به همان digest هم جواب را
                    # ثبت می‌کند (مارکر داخلِ متن است). ارسالِ شکست‌خورده ⇒
                    # asked نمی‌شود؛ ضربانِ بعد دوباره می‌کوشد.
                    _qtxt = _qb.question_text(_qi)
                    _qm, _qhand = self._budgeted_send(
                        "question", _qtxt,
                        lambda: self._client.send(
                            _scrub(_qtxt),
                            chat_id=_own_qb,
                            topic_id=self._dm_topic()))
                    if _qhand:
                        _qb.mark_asked(_qi["id"], now=now)  # فقط بعدِ تحویل
        except Exception:  # noqa: BLE001 — بودجهٔ سؤال هرگز beat را نمی‌کشد
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
                    # ⚠️ ۲۰۲۶-۰۷-۳۱ (یافتهٔ اسکن): خانهٔ پین‌شده یک‌بار نوشته
                    # می‌شد و دیگر هرگز — هر پالسِ بعدی پیامِ **نو** می‌فرستاد،
                    # پس «خانه»ی بالای چت یک عکسِ یک-روزه بود (پیامِ ۱۴۹ از
                    # ۱۸:۴۳ دیروز، ده پالسِ تازه‌تر زیرش رد شده بودند). حالا
                    # اول **ویرایشِ** همان پیامِ پین؛ فقط اگر ویرایش شکست
                    # (پیام پاک شده) پیامِ نو + پینِ دوباره.
                    _hid = cfg.get("home_message_id")
                    _own = getattr(self._client, "owner_chat_id", None)
                    _edited = False
                    if isinstance(_hid, int) and _own is not None:
                        try:
                            _edited = bool(self._client.edit(
                                _hid, _scrub(_pt), keyboard=_kb, chat_id=_own))
                        except Exception:  # noqa: BLE001
                            _edited = False
                    if _edited:
                        out["pulse"] = True
                    else:
                        _mid = self._route_send("center-pulse", _pt, cfg=cfg,
                                                keyboard=_kb)
                        out["pulse"] = _mid is not None
                        if _mid is not None and _own is not None:
                            try:
                                self._client.pin_message(_mid, chat_id=_own)
                                cfg["home_message_id"] = _mid
                            except Exception:  # noqa: BLE001 — pin نشد → پالس سرِ جایش است
                                pass
                    # ── راهنمای DM (یافتهٔ اسکن: dm_text صفر صداکننده) ──────
                    # دیشب راهنما در گروه پین شد ولی نسخهٔ DM ساخته شد و هرگز
                    # فرستاده نشد — سطحِ اصلیِ مالک بدونِ دستورالعمل ماند.
                    # همان الگوی guide ِ گروه: یک‌بار ساخت+پین، بعد فقط با
                    # تغییرِ هش ویرایش.
                    try:
                        import hashlib as _hl
                        import guide as _gd2
                        _dt = _gd2.dm_text()
                        _dh = _hl.sha256(
                            _dt.encode("utf-8", "replace")).hexdigest()[:16]
                        _dmid = cfg.get("dm_guide_message_id")
                        if isinstance(_dmid, int) and cfg.get("dm_guide_hash") == _dh:
                            pass                        # بی‌تغییر — دست نزن
                        elif isinstance(_dmid, int) and _own is not None:
                            if self._client.edit(_dmid, _scrub(_dt),
                                                 chat_id=_own):
                                cfg["dm_guide_hash"] = _dh
                                dirty = True
                        elif _own is not None:
                            _dmid = self._client.send(_scrub(_dt), chat_id=_own,
                                                      topic_id=self._dm_topic(),
                                                      pin=True)
                            if isinstance(_dmid, int):
                                cfg["dm_guide_message_id"] = _dmid
                                cfg["dm_guide_hash"] = _dh
                                dirty = True
                    except Exception:  # noqa: BLE001 — راهنما هرگز پالس را نمی‌کشد
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
        # سنجهٔ ضدِاسپم — تنها خوانندهٔ ساعتیِ tg_send_log (لِینِ رصد ۰۷-۳۱).
        # عدد از خودِ لاگ می‌آید، نه از حدس؛ None یعنی حرفی برای گفتن نیست.
        try:
            import tg_send_log as _tsl_pulse  # noqa: WPS433
            _pl = _tsl_pulse.pulse_line(24.0)
            if _pl:
                lines.append(_pl)
        except Exception:  # noqa: BLE001 — سنجه هرگز پالس را نمی‌کشد
            pass
        return "\n".join(lines[:9])

    def _home_keyboard(self) -> list:
        """سه دکمه — نه بیشتر. قاعدهٔ خودِ مالک است و گاردش
        (`t_the_home_keyboard_never_exceeds_three_decision_points`) دکمهٔ
        چهارمِ «ساختِ خود» را گرفت. گارد بازنویسی **نشد**: درِ ساخت به سطحِ
        دوم رفت (زیرِ «وضعیتِ کامل») و راهِ اصلی‌اش متنِ آزادِ «بساز: …» است
        که در پالس هم یادآوری می‌شود. یک تصمیمِ کمتر در سطحِ اول.

        استثنای رأی ۲۲ (Mini App، contract F.3): ردیفِ «📊 داشبورد» یک web_app
        ِ **نمایشی** است نه تصمیم — و فقط با فلگِ OCTOPUS_TG_MINIAPP + فایلِ
        URL ِ تازهٔ https ظاهر می‌شود؛ بدونِ URL ِ زنده، دکمه‌ای وجود ندارد."""
        rows = [[{"text": "🐙 وضعیتِ کامل", "callback_data": "hm:st"}],
                [{"text": "🦵 پاها", "callback_data": "hm:legs"},
                 {"text": "🔇 ناگفته‌ها", "callback_data": "hm:held"}]]
        _mu = self._miniapp_url()
        if _mu:
            rows.append([{"text": "📊 داشبورد", "web_app": {"url": _mu}}])
        return rows

    def _handle_home_callback(self, cbq: dict, data: str) -> dict:
        """دکمه‌های خانهٔ لنگر — همه read-only، صفر جهش، صفر خرج.

        مالکیت را `handle_update → _is_owner` از قبل گیت کرده؛ این‌جا فقط
        رندر است. هر شکست ⇒ متنِ صادقِ کوتاه، هرگز سکوت.

        ۲۰۲۶-۰۷-۳۱ (منشور §۶.۲/§۶.۳ — حذفِ منوی تو در تو): هر تپِ hm: همان
        پیام را **ویرایش** می‌کند (الگوی _edit_page)، پیامِ نو نمی‌بارد؛ عمقِ
        منو ≤۲ و «hm:home» راهِ برگشت به خانه است. زنجیرهٔ سه‌پیامیِ
        st→build→bq مُرد."""
        verb = str(data or "").split(":", 1)[-1]
        msg = cbq.get("message") or {}
        chat = (msg.get("chat") or {}).get("id")
        mid = msg.get("message_id")
        try:
            self._client.answer_callback(cbq.get("id"), "")
        except Exception:  # noqa: BLE001
            pass
        _back = [{"text": "🏠 خانه", "callback_data": "hm:home"}]
        kb = [_back]
        if verb == "home":
            body = self._home_pulse_text() or "🐙 هنوز چیزی برای گفتن ندارم."
            kb = self._home_keyboard()
        elif verb == "st":
            body = self._status_text() or "هنوز چیزی برای گفتن ندارم."
            # وضعیتِ حلقهٔ ساخت یک **خط** است نه یک منوی پایین‌تر (عمق ≤۲؛
            # درِ اصلیِ ساخت متنِ آزادِ «بساز: …» است که پالس یادش می‌دهد).
            try:
                import build_cmd as _bc
                _s = _bc.loop_status()
                if _s.get("tasks") or _s.get("patches"):
                    body += (f"\n\n🛠 صفِ ساخت: {_fa_num(_s['tasks'])} · "
                             f"پچِ منتظرِ رأی: {_fa_num(_s['patches'])}")
            except Exception:  # noqa: BLE001
                pass
            kb = [[{"text": "🔄 تازه‌سازی", "callback_data": "hm:st"}], _back]
        elif verb == "legs":
            rows = []
            try:
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
            # نمی‌شود · خواندن = HELD_VIEWED، نه sent، و هیچ ارسال/اجرایی نمی‌سازد.
            try:
                import hold_policy as _hp
                import surface_policy as _spol
                body = _hp.held_view(_spol.held_since(500))
            except Exception:  # noqa: BLE001
                body = "🔇 فهرستِ ناگفته‌ها در دسترس نیست."
        elif verb == "build":
            # صفحهٔ «ساختِ خود» — فقط از دکمهٔ ackِ «بساز: …» می‌آید (یک تاپ
            # تا اطلاعِ واقعی)؛ صف/پچ سطحِ دومِ همین صفحه‌اند.
            try:
                import build_cmd as _bc
                body = (_bc.status_text() + "\n\n" + _bc.queue_text()
                        + "\n\n" + _bc.patches_text())
                kb = [[{"text": "📥 صف", "callback_data": "hm:bq"},
                       {"text": "🧩 پچ‌ها", "callback_data": "hm:bp"}], _back]
            except Exception:  # noqa: BLE001
                body = "🛠 حلقهٔ ساخت در دسترس نیست."
        elif verb == "bq":
            try:
                import build_cmd as _bc
                body = _bc.queue_text()
            except Exception:  # noqa: BLE001
                body = "📥 صف در دسترس نیست."
            kb = [[{"text": "🛠 ساختِ خود", "callback_data": "hm:build"}], _back]
        elif verb == "bp":
            try:
                import build_cmd as _bc
                body = _bc.patches_text()
            except Exception:  # noqa: BLE001
                body = "🧩 فهرستِ پچ در دسترس نیست."
            kb = [[{"text": "🛠 ساختِ خود", "callback_data": "hm:build"}], _back]
        else:
            body = "این دکمه را نمی‌شناسم — خانه را دوباره باز کن."
        edited = False
        if isinstance(mid, int):
            try:
                edited = bool(self._client.edit(mid, _scrub(body), keyboard=kb,
                                                chat_id=chat))
            except Exception:  # noqa: BLE001
                edited = False
        if not edited:
            # پیامِ مرجع نیست/پاک شده — تنها آن‌وقت پیامِ نو (DM ِ مالک by-design).
            try:
                self._client.send(_scrub(body), chat_id=chat, keyboard=kb,
                                  topic_id=self._dm_topic())
            except Exception:  # noqa: BLE001
                pass
        return {"kind": "home", "verb": verb, "edited": edited}

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
            # گاردِ صفر-template (منشور §۵؛ قرارداد ORPHANS C1): کارتِ دوره‌ایِ
            # پا فقط رخدادِ واقعی — filler/قالبِ پرنشده هرگز بیرون نمی‌رود.
            # C5: بلاکِ بی‌صدا ممنوع — دلیل به‌عنوانِ ردیفِ held در send-log
            # می‌نشیند (متنِ ردیف = خودِ دلیل، تا رسید بگوید «چرا» نرفت).
            # C4: این گارد فقط همین خروجیِ دوره‌ای است؛ پاسخ به مالک/کارتِ
            # تأیید/جریانِ فوری هرگز از اینجا نمی‌گذرد.
            try:
                import leg_activation as _la
                _gv = _la.guard_send(body, leg=leg)
            except Exception:  # noqa: BLE001 — گاردِ غایب = رفتارِ امروز
                _gv = {"send": True, "reason": "guard-unavailable"}
            if not _gv.get("send"):
                try:
                    import tg_send_log as _tsl_lg  # noqa: WPS433
                    _tsl_lg.record(chat_id=chat, topic_id=tid,
                                   text=str(_gv.get("reason") or ""),
                                   stream=f"leg-card-{leg}", ok=False,
                                   bot_role="outer", surface="held",
                                   state="held")
                except Exception:  # noqa: BLE001
                    pass
                return
            # گروه ۵ِ اسکن: کارتِ پای بی-pause (system/mirror) دکمهٔ ⏸/▶️ نمی‌گیرد.
            kb = _lt.card_keyboard(leg, pausable=self._leg_pausable(leg))
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
            # VQ-LEG-CARD-SPIN-001 (۲۰۲۶-۰۸-۰۴): هش را **بی‌قید به موفقیتِ
            # ارسال** ذخیره کن. قبلاً داخلِ `if isinstance(ids.get(leg), int)`
            # بود، یعنی:
            #   ارسال held می‌شود ⇒ عددِ صحیح برنمی‌گردد ⇒ id ثبت نمی‌شود ⇒
            #   هش ذخیره نمی‌شود ⇒ دورِ بعد همان هش دوباره ساخته می‌شود، id
            #   پیدا نمی‌کند، و **دوباره می‌فرستد**.
            # اندازه‌گیریِ زنده: ۱۰۴ ارسالِ بایت‌به‌بایت یکسانِ همین کارت بینِ
            # ۰۵:۳۹ و ۰۷:۰۰ (کادنسِ ۴۶.۶ ثانیه) — ۱۰۳ تا held، ۱۰۲ تا به‌عنوانِ
            # تکراری آرشیو، و فقط **یکی** تحویل شد. یعنی یک hold تولیدکننده را
            # به یک چرخنده تبدیل می‌کرد. امروز روی گوشی بی‌ضرر بود چون سیاستِ
            # hold جذبش کرد؛ لحظه‌ای که آن سیاست عوض شود، رگبار است.
            #
            # ⚠️ کلید **محتوا** است نه زمان: بدنهٔ عوض‌شده هش را عوض می‌کند و
            # همان دور دوباره می‌فرستد. پس این «دیگر هرگز نفرست» نیست — «همان
            # متن را دوباره نفرست» است. گاردِ متناظر هر دو حالت را می‌سنجد.
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
                    _lt.card_keyboard(leg, pausable=self._leg_pausable(leg)))
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
        است» ⇒ BLOCKED با کارتِ سؤال؛ وگرنه DONE با رسید و شاهد.

        ۲۰۲۶-۰۸-۰۳ — این متد **inline** از `beat()` صدا زده می‌شود و `beat()`
        خودش inline از `run_forever` است. یعنی برخلافِ نامش، «beat» پس‌زمینه
        نبود: یک `ask_brain.ask` ِ کند اینجا همان حلقهٔ poll را می‌بست. حالا کلِ
        متد به لِینِ مغز می‌رود (نه تک‌تکِ askها — رسیدها را خودش می‌فرستد و به
        الگوی ack/edit نیاز ندارد).

        ⚠️ گاردِ تک‌اجرا اجباری است: `leg_tasks.claim_next` عمداً وضعیت را عوض
        **نمی‌کند** (فقط قدیمی‌ترین WORKING را برمی‌گرداند)، پس دو اجرای هم‌زمان
        همان تسک را برمی‌دارند و دوبار جواب می‌دهند. beat ِ بعدی اگر قبلی هنوز
        در پرواز باشد ساده رد می‌شود — کارِ جامانده نمی‌ماند، فقط یک ضربان دیرتر.
        """
        if getattr(self, "_leg_engine_busy", False):
            return
        if _submit_bg_job("brain", self._drive_leg_engine_now, BRAIN_QUEUE_MAX):
            return
        self._drive_leg_engine_now()      # لِین در دسترس نبود ⇒ همگام، مثلِ دیروز

    def _drive_leg_engine_now(self) -> None:
        """بدنهٔ واقعی. مستقیم صدا نزن مگر همگام لازم باشد — `_drive_leg_engine`
        گاردِ تک‌اجرا و مسیرِ لِین را دارد."""
        self._leg_engine_busy = True
        try:
            self._drive_leg_engine_body()
        finally:
            self._leg_engine_busy = False

    def _drive_leg_engine_body(self) -> None:
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
                              chat_id=chat, keyboard=kb,
                              topic_id=self._dm_topic())
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
            # (بازبینی ۰۷-۳۱، wiring-1) مسلح‌کردنِ گاردِ interactive: جریانِ
            # دکمه‌دار هرگز کلاینتِ send-only ِ inner را نمی‌گیرد — دکمهٔ روی
            # inner برای همیشه مرده است (الگوی «۳۵ کارتِ مرده»). fallback ِ
            # TypeError برای پنجرهٔ ماژولِ کهنه در حافظهٔ پروسهٔ زنده.
            try:
                cl, cid, tid = _sr.resolve(stream, clients=self._clients_map(),
                                           cfg=cfg, interactive=bool(keyboard))
            except TypeError:
                cl, cid, tid = _sr.resolve(stream, clients=self._clients_map(),
                                           cfg=cfg)
        except Exception:  # noqa: BLE001 — روتر هرگز ارسال را نمی‌کشد
            # (۲۰۲۶-۰۷-۳۱، رفعِ shared-transport-8) — تا اینجا سقوط به گروه + تاپیکِ
            # system بود. ولی surface_router خودش در ۰۷-۳۰ عمداً تغییر کرد تا ابهام
            # به DM برود نه گروه (گروه = فقط پاها). fallbackِ این caller هنوز
            # قانونِ قدیمیِ ردشده را داشت. حالا DM ِ مالک (پیامِ در جایِ اشتباه
            # بهتر از پیامِ گم‌شده است، ولی DM اشتباه‌تر از گروهِ اشتباه نیست).
            cl, cid, tid = (self._client,
                            getattr(self._client, "owner_chat_id", None), None)
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
            # بودجهٔ اعلان: kind="alert" **معاف** است (بحرانی هرگز گیت نمی‌شود)
            # ولی جدا شمرده می‌شود (exempt_used) تا گزارش صادق بماند —
            # «۵ عادی + ۳ بحرانی»، نه یک عددِ قاطیِ دروغ.
            _amid, _ = self._budgeted_send(
                "alert", text,
                lambda: self._route_send("center-alert", text),
                critical=True)
            return _amid is not None
        except Exception:  # noqa: BLE001
            return False

    # ── موج ۲ (لِین‌های D/E/F/H): capture · یادآور · بریف · vault · سؤال ─────
    def _capture_hook(self, msg: dict) -> "dict | None":
        """درزِ capture ِ یک‌ژسته (contract D). None = مسیرِ عادی ادامه یابد.

        سه ماشه: رسانه (عکس/ویس/سند/ویدیو) · پیشوندِ صریحِ «ثبت:» · متنی که
        طبقه‌بندِ خالصِ $0 آن را task/lead/idea/expense بداند. نوتِ ساده
        (kind=note) عمداً capture نمی‌شود — چتِ آزادِ رأی ۱۹ زنده می‌ماند.
        ریپلای به «سؤالِ اختاپوس» هم هرگز capture نمی‌شود (مسیرِ جوابِ qb).

        بازبینیِ متخاصمِ ۰۷-۳۱ (BLOCKER 1+4) — سه گیتِ سخت، به ترتیب:
        (الف) فقط DM ِ خصوصیِ مالک capture می‌شود. اتاق‌های system/mirror ِ
              گروه هم mode=core_conversation می‌گیرند ولی هرگز نباید بایگانی
              شوند — پیامشان به مسیرِ آینه/ask ِ موجود ادامه می‌یابد.
        (ب)  سؤالِ vault («از والت بپرس …») پیش از capture سنجیده می‌شود و
              همیشه به ask_vault می‌رسد، هرگز به بایگانی.
        (ج)  سؤال (is_question یا ؟/?) مالِ مغزِ چت است، نه بایگانی.
        استثنای صریح: «ثبت:» همیشه capture می‌شود؛ رسانه در DM هم."""
        import capture as _cap
        text = str(msg.get("text") or msg.get("caption") or "").strip()
        _rt = str((msg.get("reply_to_message") or {}).get("text") or "")
        if "سؤالِ اختاپوس" in _rt:
            return None                  # جوابِ بودجهٔ سؤال — _handle_message
        # ── (الف) گیتِ سطح: chat باید DM ِ مالک باشد ─────────────────────────
        _chat = msg.get("chat") if isinstance(msg.get("chat"), dict) else {}
        _is_private = str(_chat.get("type") or "").strip().lower() == "private"
        _own_dm = False
        try:
            _own_c = getattr(self._client, "owner_chat_id", None)
            _own_dm = (_own_c is not None and int(_own_c) > 0
                       and int(_chat.get("id")) == int(_own_c))
        except (TypeError, ValueError):
            _own_dm = False
        if not (_is_private or _own_dm):
            return None                  # اتاقِ گروه (system/mirror/…) ⇒ هرگز capture
        has_media = any(msg.get(k) for k in ("photo", "voice", "document",
                                             "video"))
        _explicit = text.startswith("ثبت:")
        if not (has_media or _explicit):
            if not text:
                return None
            # ── (ب) سؤالِ vault ⇒ ask_vault، هرگز بایگانی ────────────────────
            if self._vault_intent(text):
                return None
            # ── (ج) سؤال ⇒ مغزِ چت، نه بایگانی ───────────────────────────────
            _is_q = text.endswith(("؟", "?"))
            if not _is_q:
                try:
                    import leg_tasks as _ltq
                    _is_q = bool(_ltq.is_question(text))
                except Exception:  # noqa: BLE001 — طبقه‌بندِ غایب = فقط علامتِ ؟/?
                    _is_q = False
            if _is_q:
                return None
            if _cap.classify(text).get("kind") not in ("task", "lead",
                                                       "idea", "expense"):
                return None              # نوتِ ساده = گفتگو (درزِ عمدی)
        try:
            import leg_tasks as _lt
        except Exception:  # noqa: BLE001
            _lt = None
        _deps = {
            "leg_tasks_mod": _lt,
            "reminder_add_fn": self._capture_reminder_add,
            "lead_submit_fn": self._capture_lead_submit(),
            "download_fn": self._capture_voice_download,  # ← ویس (contract D-voice)
            "ask_fn": None,      # پالایشِ LLM فقط با فلگِ جدا — این موج خاموش
        }
        _chat_id = (msg.get("chat") or {}).get("id")

        # ویس تنها ورودیِ **کندِ** capture است (دانلود + مدلِ محلی). بقیه —
        # متن، عکس، سند — میلی‌ثانیه‌اند و همان مسیرِ همگامِ دیروز را می‌روند.
        if msg.get("voice") or msg.get("audio"):
            _mid = None
            try:
                _mid = self._client.send(
                    _scrub("🎧 ویس رسید — دارم گوش می‌دم…"),
                    chat_id=_chat_id, topic_id=self._dm_topic())
            except Exception:  # noqa: BLE001
                _mid = None

            def _job(_msg=msg, _d=_deps, _cid=_chat_id, _m=_mid):
                r = _cap.handle(_msg, deps=_d)
                _txt = (str(r.get("ack") or "ثبت شد ✅") if r.get("handled")
                        else "ویس ثبت نشد — capture ردش کرد (فلگ/گیت).")
                try:
                    if _m is not None:
                        # همان پیامِ «دارم گوش می‌دم» جایش را به نتیجه می‌دهد —
                        # دو پیام برای یک ژست، شلوغی است.
                        if self._client.edit(_m, _scrub(_txt), chat_id=_cid):
                            return
                    self._client.send(_scrub(_txt), chat_id=_cid,
                                      topic_id=self._dm_topic())
                except Exception:  # noqa: BLE001 — ack ِ گم‌شده ثبت را پس نمی‌گیرد
                    pass

            if _submit_voice_job(_job):
                return {"kind": "capture", "capture_kind": "voice",
                        "queued": True}
            # کارگر در دسترس نبود ⇒ همگام، دقیقاً مثلِ دیروز (کند ولی مطمئن)

        res = _cap.handle(msg, deps=_deps)
        if not res.get("handled"):
            return None                  # فلگ خاموش/رد ⇒ مسیرِ امروز
        try:
            self._client.send(_scrub(str(res.get("ack") or "ثبت شد ✅")),
                              chat_id=_chat_id, topic_id=self._dm_topic())
        except Exception:  # noqa: BLE001 — ack ِ گم‌شده نباید ثبت را پس بگیرد
            pass
        return {"kind": "capture", "capture_kind": res.get("kind"),
                "routed": res.get("routed"), "dup": bool(res.get("dup"))}

    def _defer_with_ack(self, chat_id, ack_text: str, work_fn,
                        *, topic_id=None, lane: str = "brain") -> bool:
        """الگوی «ثبتِ فوری → کارِ کند در پس‌زمینه → ویرایشِ همان پیام».

        ۲۰۲۶-۰۸-۰۳ — تعمیمِ همان چیزی که مسیرِ ویس از ۰۸-۰۱ اثباتش کرده. چرا
        اینجا و نه در هر صداکننده: تا امروز فقط ویس این را داشت و هر مسیرِ
        مدل‌محورِ دیگر (ask_brain / mirror_room / negotiate / llm_intent) روی
        همان تک‌رشتهٔ poll بلاک می‌شد.

        قرارداد:
          · `work_fn()` متن برمی‌گرداند، یا `(متن, کیبورد)` — همان شکلی که
            صداکننده‌های همگام از قبل می‌سازند (`ask_brain.card` یک tuple است).
            `None` ⇒ چیزی ویرایش نمی‌شود.
          · هر استثنایی داخلِ `work_fn` بلعیده می‌شود و به مالک متنِ صادقانه
            می‌رسد — کارگر هرگز به‌خاطرِ یک کارِ بد نمی‌میرد.
          · خروجی `True` = صف گرفت؛ `False` = صداکننده **باید** همان کارِ
            همگامِ قبلی را بکند (کندی بهتر از سکوت).

        عمداً پیامِ ack **قبل از** enqueue فرستاده می‌شود: اگر ارسال شکست بخورد
        هنوز می‌شود همگام ادامه داد، ولی اگر بعد از enqueue بفرستیم دو پیام
        برای یک ژست می‌سازیم.
        """
        try:
            mid = self._client.send(_scrub(ack_text), chat_id=chat_id,
                                    topic_id=topic_id)
        except Exception:  # noqa: BLE001
            mid = None

        def _job(_cid=chat_id, _m=mid, _tid=topic_id, _fn=work_fn):
            try:
                out = _fn()
            except Exception as e:  # noqa: BLE001
                out = "نشد — %s. دوباره بفرست." % type(e).__name__
            if out is None:
                return
            body, kb = out if isinstance(out, tuple) else (out, None)
            txt = _scrub(str(body or ""))
            try:
                if _m is not None and self._client.edit(_m, txt, keyboard=kb,
                                                        chat_id=_cid):
                    return
                self._client.send(txt, chat_id=_cid, keyboard=kb, topic_id=_tid)
            except Exception:  # noqa: BLE001 — پاسخِ گم‌شده کار را پس نمی‌گیرد
                pass

        return _submit_bg_job(lane, _job,
                              BRAIN_QUEUE_MAX if lane == "brain" else VOICE_QUEUE_MAX)

    @staticmethod
    def _capture_reminder_add(text, when):
        """adapter ِ دستِ لِین E (contract E.3): متن/زمانِ فارسی → reminders.add.
        زمانِ نافهمیده ⇒ None — بدونِ حدس (capture خودش صادقانه ack می‌سازد)."""
        import reminders as _rm
        now = time.time()
        due, cleaned = _rm.parse_when(str(text or ""), now=now)
        body = cleaned or str(text or "")
        if due is None and when:
            due, _c2 = _rm.parse_when(str(when), now=now)
            body = str(text or "") or _c2
        if due is None:
            return None
        return _rm.add(body, due_ts=due, scope="dm", now=now)

    def _capture_voice_download(self, file_id, dest) -> bool:
        """آداپترِ دانلودِ ویس (contract D-voice): file_id → فایلِ محلیِ موقت.
        tg_api خودش سقف‌دار/۴۲۹-aware/fail-soft است؛ اینجا فقط عبور.
        همان کلاینتی که پیام را گرفت باید فایل را بگیرد (توکنِ درست) —
        هرگز کلاینتِ نو ساخته نمی‌شود. dest داخلِ tempِ خودِ capture است و
        مرکز به آن دست نمی‌زند."""
        try:
            return bool(self._client.fetch_file(file_id, dest))
        except Exception:  # noqa: BLE001 — دانلودِ شکسته = دلیلِ صادقِ capture
            return False

    @staticmethod
    def _capture_lead_submit():
        """adapter ِ صفِ لید (contract D): payload → lead_candidate_inbox.
        importِ شکسته ⇒ None تا capture صادقانه «صفِ لید هنوز وصل نیست» بگوید.
        کانال telegram_manual = consented_inbound؛ فایروالِ consent دست‌نخورده."""
        try:
            _legs = str(_HERE.parent / "legs")
            if _legs not in sys.path:
                sys.path.insert(0, _legs)
            import lead_candidate_inbox as _lci

            def _submit(payload: dict):
                p = dict(payload or {})
                cand = {"source": {"channel": str(p.get("channel")
                                                 or "telegram_manual")},
                        "request": {"scope_text": str(p.get("summary") or "")},
                        "contact": {"phone": p.get("phone")},
                        "description": str(p.get("summary") or ""),
                        "source_note": p.get("source_note")}
                return _lci.submit_candidate(cand, source_id="tg-capture")
            return _submit
        except Exception:  # noqa: BLE001
            return None

    # ── بودجهٔ اعلان (منشور §۳: «≤۵ پیامِ قطع‌کننده در روز؛ سرریز → digest») ──
    @staticmethod
    def _nb():
        """notify_budget (lazy، fail-soft). None = بودجه در دسترس نیست ⇒ ارسالِ
        امروز — سقفِ شکسته نباید مرکز را کر کند (هم‌جهت با fail-safe ِ خودِ ماژول)."""
        try:
            import notify_budget as _nbm
            return _nbm
        except Exception:  # noqa: BLE001
            return None

    def _budgeted_send(self, kind, text, send_fn, *, critical: bool = False):
        """گیتِ بودجهٔ اعلان دورِ یک ارسالِ قطع‌کننده (قرارداد BUDGETS، یک درز).

        `send_fn()` = همان ارسالِ موجودِ صداکننده (بدونِ الگوی دوم). خروجی
        `(mid, handed)`:
          · mid = شناسهٔ پیامِ واقعی یا None.
          · handed = پیام «به مالک رسیده حساب می‌شود» — یا ارسالِ واقعی موفق
            بود، یا در بافرِ digest ِ hold_policy نشست (سرریزِ منشور: digest،
            هرگز حذف؛ flush ِ ساعتیِ همین beat آن را می‌بَرد).
        route == "digest" ⇒ عمداً هیچ ارسالی؛ "send-anyway" ⇒ بافر ننوشت،
        سکوت بدتر از سرریز است پس می‌فرستیم. ارسالِ شکست‌خورده بعد از
        allow=True ⇒ refund (واحدِ سوخته برمی‌گردد).
        اعلامِ صادقانهٔ سرریز (announce_line) مستقیم می‌رود — خودش هرگز از
        allow/route رد نمی‌شود و فقط بعد از ارسالِ واقعی mark می‌شود."""
        nb = self._nb()
        if nb is None:
            mid = send_fn()
            return mid, mid is not None
        now = float(self._clock())
        try:
            d = nb.route(kind, text, now, critical=critical)
        except Exception:  # noqa: BLE001 — بودجهٔ شکسته = ارسالِ امروز
            mid = send_fn()
            return mid, mid is not None
        mid, handed = None, False
        if d.get("route") in ("send", "send-anyway"):
            try:
                mid = send_fn()
            except Exception:  # noqa: BLE001
                mid = None
            if mid is None and d.get("route") == "send":
                try:
                    nb.refund(kind, now)
                except Exception:  # noqa: BLE001
                    pass
            handed = mid is not None
        elif d.get("route") == "digest":
            handed = True                    # در بافرِ digest نشست — گم نشد
        if d.get("announce"):
            try:
                _own = getattr(self._client, "owner_chat_id", None)
                _al = nb.announce_line(now)
                if _own is not None and _al:
                    if self._client.send(_scrub(_al), chat_id=_own,
                                         topic_id=self._dm_topic()) is not None:
                        nb.mark_announced(now)
            except Exception:  # noqa: BLE001 — اعلام هرگز ارسال را نمی‌کشد
                pass
        return mid, handed

    def _reminder_dm_send(self, text: str, rid: str):
        """ارسالِ یادآوریِ DM — شکست باید **بالا بیاید** تا reminders آن آیتم
        را fired نکند و ضربانِ بعد دوباره بکوشد (قراردادِ لِین E: بلعیدنِ
        خطا = fired روی پیامِ گم‌شده).

        بودجهٔ اعلان (منشور §۳): kind="reminder" قطع‌کننده است؛ یادآوریِ
        بحرانی/فوری با critical=True معاف. سرریز ⇒ متن در digest ِ ساعتی
        می‌نشیند و همان «رسیدن» است (fired جلو می‌رود — وگرنه هر ضربان دوباره
        defer می‌شد و digest پر از تکرار)."""
        import reminders as _rm
        _crit = False
        try:
            _crit = bool(_rm.is_critical(text))
        except Exception:  # noqa: BLE001
            _crit = False
        mid, handed = self._budgeted_send(
            "reminder", text,
            lambda: self._client.send(
                _scrub(text),
                chat_id=getattr(self._client, "owner_chat_id", None),
                keyboard=_rm.reminder_keyboard(rid),
                topic_id=self._dm_topic()),
            critical=_crit)
        if not handed:
            raise RuntimeError("reminder-dm-send-failed")
        return mid if mid is not None else True

    def _reminder_leg_send(self, leg: str, text: str, cfg: dict):
        """یادآوریِ بیزنسی در تاپیکِ همان پا (رأی ۶) — شکست بالا می‌آید."""
        topics = cfg.get("topics") if isinstance(cfg.get("topics"), dict) else {}
        mid = self._client.send(_scrub(text), chat_id=cfg.get("chat_id"),
                                topic_id=topics.get(leg))
        if mid is None:
            raise RuntimeError("reminder-leg-send-failed")
        return mid

    def _dm_send_strict(self, text: str):
        """ارسالِ DM که موفقیت را با خروجیِ truthy گواهی می‌دهد؛ شکست ⇒ استثنا.
        brief/weekly فقط روی تحویلِ واقعی cursor جلو می‌برند (contract E/H).

        بودجهٔ اعلان (منشور §۳): kind="brief" (بریفِ صبح/شب و مرورِ هفتگی هر
        دو از همین درز می‌روند). سرریز ⇒ متن در digest ِ ساعتی می‌نشیند و
        خروجی True است تا cursor جلو برود — تحویل از راهِ digest هم تحویل است
        (وگرنه هر ضربان دوباره defer می‌شد)."""
        mid, handed = self._budgeted_send(
            "brief", text,
            lambda: self._client.send(
                _scrub(text),
                chat_id=getattr(self._client, "owner_chat_id", None),
                topic_id=self._dm_topic()))
        if not handed:
            raise RuntimeError("dm-send-failed")
        return mid if mid is not None else True

    @staticmethod
    def _vault_intent(text: str) -> bool:
        """آیا این جمله صریحاً از vault می‌پرسد؟ (contract F.1 — ماشهٔ باریک:
        پیشوندِ صریح، یا سؤال‌بودن + یکی از واژه‌های vault)."""
        t = str(text or "").strip()
        if t.startswith(("از والت", "تو نوت‌هام", "/vault")):
            return True
        return (("؟" in t or "?" in t)
                and any(w in t for w in ("والت", "نوت", "ابسیدین")))

    def _miniapp_url(self) -> "str | None":
        """URL ِ داشبوردِ Mini App (contract F.3) — فقط فایلِ تازهٔ https.
        غایب/کهنه (≥۲۴h)/خالی/غیرِhttps ⇒ None ⇒ بدونِ دکمه — URL ِ مرده هرگز
        پیشنهاد نمی‌شود (tunnel هنگامِ stop فایل را با url:"" بازنویسی می‌کند)."""
        if os.environ.get("OCTOPUS_TG_MINIAPP", "0") != "1":
            return None
        try:
            p = opslib.STATE_DIR / "telegram" / "miniapp-url.json"
            if not p.exists() or (time.time() - p.stat().st_mtime) >= 86400.0:
                return None
            # utf-8-**sig**: نویسندهٔ فایل PowerShell است و `Set-Content -Encoding
            # utf8` در PS 5.1 با BOM می‌نویسد؛ خواندنِ ساده json را می‌ترکاند و
            # دکمه بی‌صدا ناپدید می‌شد (بلاکرِ B1 ِ دیباگِ ۰۷-۳۱ — tunnel زنده،
            # دکمه نامرئی). BOM حالا هم در نوشتن حذف شد هم این‌جا تحمل می‌شود.
            url = str((json.loads(p.read_text("utf-8-sig")) or {}).get("url") or "")
            return url if url.startswith("https://") else None
        except Exception:  # noqa: BLE001
            return None

    def _handle_reminder_callback(self, cbq: dict, data: str) -> dict:
        """rm:done:<id> / rm:snz:<id> — هر دو idempotent (دبل‌تاپ بی‌اثر)؛
        answer همیشه اول (مرگِ spinner §۶.۴)، بعد ویرایشِ کارت به وضعِ نو."""
        parts = str(data or "").split(":")
        act = parts[1] if len(parts) > 1 else ""
        rid = parts[2] if len(parts) > 2 else ""
        self._answer(cbq, {"done": "انجام شد ✅",
                           "snz": "نیم ساعت بعد ⏰"}.get(act, "نشناختم"))
        it = None
        try:
            import reminders as _rm
            if act == "done" and rid:
                it = _rm.done(rid)
            elif act == "snz" and rid:
                it = _rm.snooze(rid, 1800)   # قولِ دکمه: «نیم ساعت بعد»
        except Exception:  # noqa: BLE001
            it = None
        msg = cbq.get("message") or {}
        mid = msg.get("message_id")
        if it is not None and isinstance(mid, int):
            _b = (str(it.get("text") or "").replace("&", "&amp;")
                  .replace("<", "&lt;").replace(">", "&gt;"))
            new_txt = (f"✅ انجام شد: {_b}" if act == "done"
                       else f"⏰ نیم ساعت بعد دوباره می‌گویم: {_b}")
            try:
                self._client.edit(mid, _scrub(new_txt),
                                  chat_id=(msg.get("chat") or {}).get("id"))
            except Exception:  # noqa: BLE001
                pass
        return {"kind": "reminder", "act": act, "id": rid,
                "ok": it is not None}

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
            # غیرمالک عمداً حتی answer_callback هم نمی‌گیرد (fail-closed:
            # هر پاسخی وجودِ بات/مالک را لو می‌دهد) — spinner ِ غریبه مشکلِ ما نیست.
            #
            # ⚠️ سکوت **به بیرون** می‌ماند؛ ولی به **دفتر** نه. اگر مالک روزی
            # از یک اکانتِ دوم بنویسد و جواب نگیرد، باید بتواند بفهمد چرا —
            # وگرنه دقیقاً همان «هرکاری می‌کنم دیده نمی‌شود» می‌شود، این‌بار
            # با یک علتِ کاملاً درست که هیچ‌جا نوشته نشده.
            self._log_disposition(u, outcome="not-owner",
                                  reason="allowlist — فرستنده مالک نیست")
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
                _m = (u.get("message")
                      or (u.get("callback_query") or {}).get("message") or {})
                if _t:
                    try:
                        self._client.send(_t, chat_id=(_m.get("chat") or {}).get("id"),
                                          topic_id=_m.get("message_thread_id"))
                    except Exception:  # noqa: BLE001 — هدایت هرگز مرکز را نمی‌کشد
                        pass
                # مرگِ spinner (منشور §۶.۴): تپِ deny-شدهٔ مالک هم باید
                # answerCallbackQuery بگیرد وگرنه دکمه تا ابد می‌چرخد
                # (inner-bot-16/group-14 — سه کارتِ زندهٔ دکتر دقیقاً همین بودند).
                _cbq0 = u.get("callback_query")
                if isinstance(_cbq0, dict):
                    self._answer(_cbq0, (_t or "اجازه نیست")[:180])
                # رسیدِ state="blocked" (۰۷-۳۱، رفعِ boundary-13، لِینِ خواهر):
                # ردِ سیاستِ ورودی تا امروز هیچ اثری در send-log نداشت —
                # «بلعیده شد» و «هرگز نیامد» یک شکل بودند.
                try:
                    import tg_send_log as _tsl_blk  # noqa: WPS433
                    _cid = (_m.get("chat") or {}).get("id")
                    _tsl_blk.record(chat_id=_cid, topic_id=_m.get("message_thread_id"),
                                    text=_t or "", stream="input-policy", ok=False,
                                    bot_role="outer",
                                    surface="group" if _cid == _cfg.get("chat_id") else "dm",
                                    state="blocked")
                except Exception:  # noqa: BLE001
                    pass
                # و ردیفِ «چرا» کنارِ ردیفِ «رسید» — یک فایل، یک `update_id`.
                self._log_disposition(u, outcome="denied-by-input-policy",
                                      reason=str(_d.get("reason") or ""),
                                      detail=f"mode={_d.get('mode')}")
                return {"kind": "input-policy", "mode": _d.get("mode"),
                        "reason": _d.get("reason")}
            # ── جوابِ گزینهٔ ② پنل (قرارداد ORPHANS A2) ──────────────────────
            # مصرف‌کنندهٔ قرینهٔ _awaiting_mission — **قبل از** بساز/capture/
            # مامور، وگرنه متنِ مأموریتِ مالک را یکی از آن درزها می‌بلعید.
            # فقط Outer DM (core_conversation). kind == "error" عیناً به مالک
            # نشان داده می‌شود، هرگز بلعیده نمی‌شود (A3).
            try:
                if getattr(self, "_awaiting_mission", False):
                    _mgp = u.get("message")
                    _txp = str((_mgp or {}).get("text") or "").strip() \
                        if isinstance(_mgp, dict) else ""
                    if _txp and _d.get("mode") == "core_conversation":
                        self._awaiting_mission = False
                        import owner_menu as _om2
                        _po = _om2.handle_panel_choice("m:mission", _txp)
                        try:
                            self._client.send(
                                _scrub(str(_po.get("text") or "")),
                                chat_id=(_mgp.get("chat") or {}).get("id"),
                                topic_id=self._dm_topic(),
                                keyboard=self._tok_kb(_po.get("keyboard")))
                        except Exception:  # noqa: BLE001
                            pass
                        return {"kind": "panel-mission",
                                "panel_kind": _po.get("kind"),
                                "mission": (_po.get("mission") or {}).get(
                                    "mission_id")}
            except Exception:  # noqa: BLE001 — پنلِ شکسته = مسیرِ قبلی، نه سکوت
                pass
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
                                topic_id=self._dm_topic(),
                                keyboard=[[{"text": "🛠 وضعیتِ حلقه",
                                            "callback_data": "hm:build"}]])
                        except Exception:  # noqa: BLE001
                            pass
                        return {"kind": "build-task", "ok": _res.get("ok"),
                                "task": _res.get("id")}
            except Exception:  # noqa: BLE001 — صفِ شکسته = مسیرِ قبلی، نه سکوت
                pass
            # ── Capture ِ یک‌ژسته (لِین D، رأی ۹–۱۰؛ ۲۰۲۶-۰۷-۳۱) ─────────────
            # بعد از «بساز:» و قبل از مامور. درزِ عمدی (رأی ۱۹ — چتِ آزاد باید
            # زنده بماند): capture فقط برای رسانه، پیشوندِ «ثبت:»، یا متنی که
            # طبقه‌بندِ $0 آن را task/lead/idea/expense بداند صدا زده می‌شود؛
            # نوتِ سادهٔ kind=note به گفتگوی موجود (مامور/مغز) می‌افتد.
            # فلگ خاموش ⇒ این بلوک هیچ اجرا نمی‌شود — بایت‌به‌بایتِ امروز.
            try:
                _mgc = u.get("message")
                if (isinstance(_mgc, dict)
                        and _d.get("mode") == "core_conversation"
                        and os.environ.get("OCTOPUS_TG_CAPTURE", "0") == "1"):
                    _rc = self._capture_hook(_mgc)
                    if _rc is not None:
                        return _rc
            except Exception:  # noqa: BLE001 — capture ِ شکسته = مسیرِ قبلی، نه سکوت
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
                _mtx0 = str((_mg or {}).get("text") or "").strip() \
                    if isinstance(_mg, dict) else ""
                # outer-bot-4: فرمانِ اسلشِ جدولِ خودِ مرکز (/menu، /start، …)
                # هرگز به مامور نمی‌رسد — وگرنه regexِ مامور آن را می‌بلعید و
                # فرمانِ #۱ ِ تبلیغ‌شده هیچ‌وقت به _page("menu") نمی‌رسید.
                _cmd0 = (_mtx0.split()[0].split("@")[0].lower()
                         if _mtx0.startswith("/") else "")
                if _mtx0 and _cmd0 not in _CENTER_SLASH:
                    _r = _oc.handle_message(_mtx0, surface_decision=_d)
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
                        # تأییدِ لخت («موافقم/باشه/👍») کار نیست — اصطکاکِ زندهٔ
                        # ۰۷-۳۱ ۱۹:۵۰: مالک «موافقم» نوشت تا کارتِ لید را تأیید
                        # کند و TASK-2 ِ بی‌صاحب ساخته شد. حالا به‌جای صف، مسیرِ
                        # درست را می‌گوییم (دکمهٔ کارت / ریپلای به کارتِ 🚧).
                        if _lc.is_ack(_tx):
                            try:
                                self._client.send(
                                    _scrub("👍 گرفتم — ولی این‌جا فقط «کار» ثبت "
                                           "می‌شود.\nبرای تأییدِ یک کارت، دکمهٔ "
                                           "خودِ کارت را بزن.\nبرای جوابِ کارتِ "
                                           "🚧، روی همان کارت ریپلای کن."),
                                    chat_id=_ch2, topic_id=_th2)
                            except Exception:  # noqa: BLE001
                                pass
                            return {"kind": "leg-ack", "leg": _leg}
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
            # ── سکوتِ چهارم (ممیزیِ ۱۱-ایجنتهٔ فاز ۰) ─────────────────────
            # این return برای **همهٔ** پیام‌هایی می‌افتد که نه متن دارند نه
            # کپشن. عکس/ویس/سند/ویدئوی DM این‌جا نمی‌رسند — قلابِ capture
            # بالاتر (خطِ ۲۵۹۷) جوابشان را داده و برگشته، و فلگش هم روی
            # پروسهٔ زنده روشن است. ولی این‌ها می‌رسند و بی‌صدا می‌میرند:
            #     استیکر · لوکیشن · video_note · مخاطب · نظرسنجی · تاس ·
            #     صوتِ بی‌کپشن · animation/GIF · ونیو · پیام‌های سرویس
            # و مهم‌تر: **هر مدیایی در تاپیک‌های سیستمی/آینهٔ گروه**، چون گیتِ
            # قلابِ capture چتِ خصوصی می‌خواهد.
            #
            # رفتار عمداً عوض نمی‌شود (جوابِ خودکار به استیکر نویز است) — ولی
            # از این پس مالک می‌تواند بفهمد چرا هیچ نشد.
            self._log_disposition(
                None, outcome="no-text-body",
                reason="پیام نه متن دارد نه کپشن — هیچ روتری ورودی ندارد",
                detail=next((k for k in ("sticker", "animation", "location",
                                         "video_note", "contact", "poll", "dice",
                                         "audio", "venue", "photo", "voice",
                                         "document", "video")
                             if k in msg), "other"))
            return None
        cmd = text.split()[0].split("@")[0].lower()
        chat_id = (msg.get("chat") or {}).get("id")  # پاسخ به همان‌جا که پرسید

        # ── AGI2027/Owner Control Plane (2026-08-02) ─────────────────────────
        # owner-only already enforced in handle_update. Flag-off => None => exact fallthrough.
        # Commands: /ops, /repair list|plan|execute|rollback, /impact, /fugu.
        try:
            _ops_path = str(_HERE.parent)
            if _ops_path not in sys.path:
                sys.path.insert(0, _ops_path)
            from agi2027_control.integration import (  # noqa: WPS433
                try_handle_control as _agi_try_control,
                format_control_result as _agi_format_control,
            )
            _ctrl = _agi_try_control(text, {"is_owner": True})
            if _ctrl is not None:
                _mid = None
                # لِینِ chat-actions: کیبوردِ `/ops` **به همین روت** می‌چسبد،
                # روتِ دومی ساخته نمی‌شود. فلگ خاموش ⇒ `_okb` تهی ⇒ دقیقاً
                # همان فراخوانیِ امروز، بدونِ حتی یک kwargِ اضافه (parity).
                try:
                    _okb = self._ops_keyboard(text)
                except Exception:  # noqa: BLE001 — کیبورد هرگز جواب را نمی‌خورد
                    _okb = None
                _okw = {"chat_id": chat_id, "topic_id": self._reply_thread(msg)}
                if _okb:
                    _okw["keyboard"] = _okb
                try:
                    _mid = self._client.send(
                        _scrub(_agi_format_control(_ctrl)), **_okw)
                except Exception:  # noqa: BLE001
                    pass
                _ores = {"kind": "agi2027-control", "status": _ctrl.get("status"),
                         "ok": _ctrl.get("ok"), "sent": _mid is not None}
                if _okb:
                    _ores["ops_buttons"] = len(_okb)
                return _ores
        except Exception:  # noqa: BLE001 — control hook must never break normal TG flow
            pass
        # ── جوابِ دکمه‌های `/ops` (لِینِ chat-actions) ───────────────────────
        # ورودیِ جهش از ریپلای به پیامِ نشان‌دار می‌آید — همان جریانی که
        # question_budget دارد؛ ماشینِ حالتِ نو ساخته نمی‌شود. فلگ خاموش یا
        # بی‌مارکر ⇒ None ⇒ مسیرِ امروزِ پیام، دست‌نخورده.
        try:
            _opsr = self._ops_reply(msg, text, chat_id)
            if _opsr is not None:
                return _opsr
        except Exception:  # noqa: BLE001 — جریانِ ریپلای هرگز پیام را نمی‌بلعد
            pass

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
        # ── جوابِ سؤالِ بودجه (لِین H): ریپلای به پیامِ «سؤالِ اختاپوس» ──────
        # مارکرِ پایدار: question_text با «Q-<n> … سؤالِ اختاپوس» شروع می‌شود.
        # تلگرام تگِ HTML را در reply-text می‌اندازد ⇒ به تگ تکیه نمی‌کنیم.
        try:
            import question_budget as _qb
            if _qb.enabled() and not text.startswith("/"):
                _rt = str((msg.get("reply_to_message") or {}).get("text") or "")
                if "سؤالِ اختاپوس" in _rt:
                    _qm = re.search(r"Q-\d+", _rt)
                    if _qm:
                        _rec = _qb.record_answer(_qm.group(0), text)
                        _ak = (f"✍️ جوابت روی {_qm.group(0)} ثبت شد — ممنون."
                               if _rec is not None else
                               "این سؤال را پیدا نکردم — شاید مالِ هفتهٔ کهنه است.")
                        _mid = None
                        try:
                            _mid = self._client.send(
                                _scrub(_ak), chat_id=chat_id,
                                topic_id=self._reply_thread(msg))
                        except Exception:  # noqa: BLE001
                            pass
                        return {"kind": "qbudget-answer",
                                "id": _qm.group(0),
                                "recorded": _rec is not None,
                                "sent": _mid is not None}
        except Exception:  # noqa: BLE001 — جوابِ سؤال هرگز پیام را نمی‌کشد
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
            # ۲۰۲۶-۰۸-۰۴ — درِ شلِ خام (رأیِ صریحِ مالک). بدونِ این، ماژول
            # ساخته و مسلح بود ولی **صفر صداکننده** داشت — همان «قابلیتِ
            # تاریک» که کلِ امروز رفعش شد. مالکیت را `handle_update → _is_owner`
            # از قبل گیت کرده؛ گیتِ فعال‌سازی/کیل/deny مالِ خودِ ماژول است.
            "/sh": lambda: self._shell_cmd(text),
            "/شل": lambda: self._shell_cmd(text),
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
                # ⚠️ سکوتِ **خودنمایان‌گر** (کشفِ پروبِ فاز ۰): پل همیشه یک
                # dict برمی‌گرداند — حتی وقتی `self._client.send` استثنا داده
                # و `mid=None` شده. آن dict از بالادست «رسیدگی شد» به‌نظر
                # می‌رسد، پس هیچ‌کس پایین‌دست دنبالِ دلیل نمی‌گردد؛ ولی مالک
                # هیچ ندیده. این بدترین شکلِ سکوت است، چون **موفق ظاهر
                # می‌شود** — و دقیقاً همان چیزی که «رسید را گیت نکن» می‌گوید.
                if isinstance(_bridged, dict) and not _bridged.get("sent", True):
                    self._log_disposition(
                        None, outcome="bridge-send-failed",
                        reason="پلِ ارگانیسم جواب ساخت ولی ارسالش بیرون نرفت",
                        detail=cmd)
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
            # ── سکوتِ سوم (فاز ۰، ۰۸-۰۴) ──────────────────────────────────
            # این `return None` تا امروز کامنتش می‌گفت «command ناشناس
            # نادیده» — و دقیقاً همان «نادیده» شکایتِ مالک بود. رسیدِ زندهٔ
            # همین امروز نشانش داد: یک پیام رسید، ورودش ثبت شد، جواب نیامد،
            # و **دلیلی هم ثبت نشد**. رفتار عوض نمی‌شود (هنوز جواب نمی‌دهد،
            # چون پاسخ‌دادن به هر تایپوی اسلش خودش نویز است) — ولی از این
            # پس **قابلِ فهم** است.
            #
            # و دو سکوت که یکی به‌نظر می‌آمدند، حالا از هم جدا می‌شوند:
            #   unknown-command — هیچ روتری نمی‌شناسدش (تایپو، فرمانِ خیالی)
            #   gated-command   — مرکز می‌شناسدش ولی فلگش خاموش است
            # دومی درسِ ثبت‌شدهٔ «مسیریابی به فلگِ خاموش» است: مسیرِ درست به
            # فرمانِ خاموش، از بیرون عیناً شبیهِ خرابی است. حالا رسید می‌گوید
            # کدام‌یک، و مالک می‌داند فلگ را روشن کند یا املا را.
            self._log_disposition(
                None,
                outcome=("gated-command" if cmd in _CENTRE_GATED
                         else "unknown-command"),
                reason=(_CENTRE_GATED.get(cmd, "") if cmd in _CENTRE_GATED
                        else "در جدولِ مرکز نیست و پلِ ارگانیسم هم نشناخت"),
                detail=cmd)
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

    def _bridge_callback_to_organism(self, cbq: dict, data: str):
        """تپِ دکمه‌ای که مرکز نمی‌شناسد → روترِ callback ِ ارگانیسم، در همین
        پروسه. ناشناخته برای هر دو → None → «نادیده»ی امروز.

        قرینهٔ `_bridge_to_organism` برای دکمه‌ها. همان الگو: هیچ گاردی دور
        زده نمی‌شود — `dispatch_callback` با `external=True` و `from_id` ِ
        واقعی صدا می‌خورد و خودش mutating را owner-gate می‌کند."""
        try:
            import sys as _s
            from pathlib import Path as _P
            _b = str(_P(__file__).resolve().parent.parent / "budget")
            if _b not in _s.path:
                _s.path.insert(0, _b)
            import approval_channel as _ac
            ch = _ac.TelegramApprovalChannel()
            out = ch.dispatch_callback(
                data, from_id=(cbq.get("from") or {}).get("id"), external=True)
        except Exception:  # noqa: BLE001 — پل هرگز مسیرِ دکمه را نمی‌کشد
            return None
        if not out or out == "نادیده":
            return None
        _vb = data.split(":", 1)[0]
        if isinstance(out, dict):
            # پیامِ جداگانه با کیبورد (قراردادِ reply_markup ِ روترِ ارگانیسم —
            # همان دو-نامیِ مستندِ پلِ فرمان‌ها).
            _body = str(out.get("text", ""))
            _kb = out.get("reply_markup") or out.get("keyboard")
            _msg = cbq.get("message") or {}
            _sent = None
            try:
                _sent = self._client.send(
                    _scrub(_body), chat_id=(_msg.get("chat") or {}).get("id"),
                    topic_id=self._reply_thread(_msg), keyboard=_kb)
            except Exception:  # noqa: BLE001
                pass
            self._answer(cbq, "✅")
            return {"kind": "bridged-callback", "verb": _vb,
                    "sent": _sent is not None}
        self._answer(cbq, str(out)[:180])
        return {"kind": "bridged-callback", "verb": _vb}

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
        # union از لِینِ موازی (۰۸-۰۱) — `/lead` روی دو باتِ مالک دو گرامرِ
        # متفاوت دارد و فیلدِ دومش در یکی متر است و در دیگری AUD. اگر پیامِ
        # گرامرِ «ثبتِ لید» این‌جا بیفتد، پارسرِ کوت بی‌صدا AUD را متر می‌خواند.
        # منطقِ تشخیص عمداً در `chat_room` است (همان‌جا که «ابهام = می‌پرسد»
        # زندگی می‌کند) و این‌جا فقط یک صدا زدن است. فلگ خاموش → None →
        # مسیرِ امروز بایت‌به‌بایت.
        try:
            import chat_room as _cr
            _lg = _cr.lead_guard(text)
            if _lg:
                return _lg
        except Exception:  # noqa: BLE001 — تشخیصِ ابهام هرگز کوت را نمی‌کشد
            pass
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
                    # ۲۰۲۶-۰۸-۰۳ (لِینِ مغز): `make_offer` هم `tier="primary"` پین
                    # می‌کند. `respond` بالا حالت را از قبل ماندگار کرده، پس
                    # بازنگری بی‌خطر می‌تواند پس‌زمینه برود — شرطِ مالک در هر
                    # صورت ثبت شده است.
                    def _neg_work(_a=_await):
                        _rv = _ng.make_offer(revise_of=_a)
                        if _rv.get("ok"):
                            return _ng.card(_rv["offer"])
                        return ("✍️ شرطت ثبت شد. پیشنهادِ بازنگری‌شده الان نشد — "
                                f"({str(_rv.get('reason'))[:40]}) بعداً می‌آید.")

                    if self._defer_with_ack(
                            chat_id, "✍️ شرطت ثبت شد — دارم بازنگری می‌کنم…",
                            _neg_work, topic_id=self._reply_thread(msg)):
                        return {"kind": "negotiate_revised", "sent": True,
                                "queued": True}
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
                # ۲۰۲۶-۰۸-۰۳ (لِینِ مغز): `mirror_room.ask` هم `tier="primary"`
                # پین می‌کند، پس همان بلاکِ تا-۲۳۵ثانیه‌ای را داشت. صفِ پر ⇒
                # مسیرِ همگامِ زیر، بایت‌به‌بایت.
                if _mr.enabled():
                    def _mirror_work(_t=text):
                        _r = _mr.ask(_t)
                        if _r.get("ok"):
                            return _mr.card(_r["text"], _r.get("model") or "",
                                            bool(_r.get("recorded_correction")))
                        _w = {"daily-cap": "سهمیهٔ امروزِ فکرِ عمیقم تمام شد",
                              "not-a-paid-brain": "مغزِ گرانم الان در دسترس نیست",
                              "no-answer": "مغزم جواب نداد",
                              }.get(str(_r.get("reason") or "").split(":")[0], "")
                        return (f"🪞 {_w} — چند دقیقهٔ دیگر دوباره بپرس." if _w
                                else "🪞 نشد — دوباره بپرس.")

                    if self._defer_with_ack(
                            chat_id, "🪞 دارم فکر می‌کنم…", _mirror_work,
                            topic_id=self._reply_thread(msg)):
                        return {"kind": "mirror", "sent": True, "queued": True}
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
            # ── سؤال از vault با منبع (رأی ۹؛ لِین F.1؛ OCTOPUS_TG_ASK_VAULT) ──
            # قبل از mission-inference تا نیتِ صریحِ «از والت …» را چیزی نبلعد.
            # فلگ خاموش یا ok=False ⇒ سقوط به مسیرِ امروز — هرگز block.
            try:
                import ask_vault as _av
                if _av.enabled() and self._vault_intent(text):
                    _q = text[6:].strip() if text.startswith("/vault") else text
                    _rv = _av.query(_q)
                    if _rv.get("ok"):
                        import html as _h
                        _body = "🗄 " + _h.escape(
                            str(_rv.get("answer") or ""))[:3400]
                        mid = self._client.send(
                            _scrub(_body), chat_id=chat_id,
                            topic_id=self._reply_thread(msg))
                        return {"kind": "ask_vault", "sent": mid is not None,
                                "sources": len(_rv.get("sources") or [])}
            except Exception:  # noqa: BLE001 — vault هرگز مسیرِ پرسش را نمی‌کشد
                pass
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
            # تعارفِ کوتاه («سلام»/«مرسی») نیازی به دسته‌بندیِ نیت ندارد و آن
            # تماسِ محلی ~۲۰ ثانیه از جوابِ مالک می‌دزدد (اندازه‌گیریِ ۰۸-۰۱:
            # ۴۰ ثانیه با طبقه‌بند، ~۳ ثانیه بدونش). مأموریت از «سلام» درنمی‌آید.
            _social = False
            try:
                import ask_brain as _ab0
                _social = bool(_ab0._is_social(text))
            except Exception:  # noqa: BLE001 — نبودِ کمکی = رفتارِ قبلی
                _social = False
            if mt == "general" and not _social:
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
                    # ۲۰۲۶-۰۸-۰۳ (لِینِ مغز): این فراخوان تا ۲۳۵ ثانیه روی
                    # تک‌رشتهٔ poll می‌نشست و در تمامِ آن مدت هیچ پیام و هیچ
                    # دکمه‌ای در هیچ تاپیکی جواب نمی‌گرفت. حالا اول «دارم فکر
                    # می‌کنم» می‌رود، بعد همان پیام با جواب ویرایش می‌شود.
                    # صفِ پر/نخِ مرده ⇒ `False` ⇒ دقیقاً مسیرِ همگامِ زیر،
                    # بایت‌به‌بایتِ دیروز.
                    if _ab.enabled():
                        def _brain_work(_t=text, _key=self._topic_key(msg)):
                            _r = _ab.ask(_t, topic_key=_key)
                            if _r.get("ok"):
                                return _ab.card(_r["text"], _r.get("model") or "",
                                                tier=_r.get("tier") or "")
                            _why = (_r.get("reason")
                                    if _r.get("reason") in ("not-a-paid-brain",
                                                            "no-answer",
                                                            "ask-exception")
                                    else None)
                            return self._ask_unknown_card(
                                "llm-no-answer" if _why else _brain_busy)

                        if self._defer_with_ack(
                                chat_id, "🧠 دارم فکر می‌کنم…", _brain_work,
                                topic_id=self._reply_thread(msg)):
                            return {"kind": kind, "sent": True, "queued": True}
                    if _ab.enabled():
                        _a = _ab.ask(text, topic_key=self._topic_key(msg))
                        if _a.get("ok"):
                            # F.2: با نردبانِ محلی، مالک باید بداند جوابِ
                            # «🧠 محلی» را می‌خواند یا «🐡 گران». tier خالی =
                            # کارتِ قدیمی بایت‌به‌بایت.
                            out = _ab.card(_a["text"], _a.get("model") or "",
                                           tier=_a.get("tier") or "")
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
        except Exception as _ask_exc:  # noqa: BLE001
            mid, kind = None, "ask_error"
            # ── سکوتِ پنجم، و بدترینشان ───────────────────────────────────
            # این `except` پایانهٔ **همهٔ** متنِ آزادِ مسیریابی‌نشده است — یعنی
            # حرفِ عادیِ فارسیِ مالک. و چون استثنا این‌جا **گرفته** می‌شود،
            # هرگز به `run_once` و نامهٔ مرده نمی‌رسد: نه جواب، نه نامهٔ مرده،
            # نه هشدار. تنها تابعی که کارش «هرگز ساکت نباش» است، ساکت‌ترین
            # مسیرِ کلِ مرکز بود.
            #
            # ⚠️ فقط **نامِ نوعِ** استثنا ثبت می‌شود، نه متنش: پیامِ استثنا
            # می‌تواند خودِ حرفِ مالک را داخلش داشته باشد (§۱۰).
            self._log_disposition(
                None, outcome="ask-error",
                reason="مسیرِ پرسشِ آزاد استثنا داد و آن را بلعید",
                detail=type(_ask_exc).__name__)
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

                # ۲۰۲۶-۰۸-۰۱ — jobی که **خودِ همین رندر** وارد صف می‌کند در snapshot نیست.
                # `pending` بالا خوانده شده، ولی `render.ingest_debate_survivors` (پشتِ
                # OCTOPUS_WIRE_DEBATE_VERDICT) داخلِ خودِ render اجرا می‌شود و بازمانده‌های
                # مناظره را **بعد** از این snapshot به صف اضافه می‌کند. آن‌وقت mint با dictِ
                # تهی امضا می‌زد (type=None · risk=None · expires="") ولی handler لحظهٔ تپ
                # jobِ واقعی را می‌خواند (type=debate · risk=medium · expires=…) → hash فرق
                # می‌کرد → «توکنِ نامعتبر». یعنی دکمه دیده می‌شد، مالک می‌زد، و رأی هرگز
                # ثبت نمی‌شد. resolve به تعویق می‌افتد تا mint-time (بعد از ingest) و فقط
                # برای شناسه‌هایی که در snapshot نیستند — پس هر jobِ موجود دقیقاً همان
                # binding قبلی را می‌گیرد (anti-TOCTOU دست‌نخورده).
                def _job_at_mint(jid: str) -> dict:
                    j = _by_id.get(str(jid))
                    if j is None:
                        try:
                            j = aps_mod.get(str(jid))
                        except Exception:  # noqa: BLE001 — نبودِ job = رفتارِ قبلی ({})
                            j = None
                        _by_id[str(jid)] = j if isinstance(j, dict) else {}
                    return _by_id[str(jid)] or {}

                _mint = lambda jid, act: cbtok.mint(
                    str(jid), act, _owner,
                    self._ap_action_hash(act, str(jid), _job_at_mint(jid)),
                    str(_job_at_mint(jid).get("expires_epoch", "")))
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

        # ── رأیِ مالک روی درخواستِ ابزار (۲۰۲۶-۰۷-۳۰) ────────────────────────
        # `tr:y|n|l:<id>` = بگیر/نه/بعداً، و `tr:list` صفِ باز را نشان می‌دهد.
        # احرازِ مالک از قبل در `handle_update` انجام شده (خطِ ۷۲۴) — غیرمالک
        # هرگز اینجا نمی‌رسد. «بعداً» عمداً رأی نیست و درخواست را باز می‌گذارد؛
        # زمانِ انتظار (`wait_s`) از همین تپ محاسبه می‌شود و سنجهٔ «به‌موقع» است.
        if verb == "tr" and len(parts) >= 2:
            msg = cbq.get("message") or {}
            _VERDICTS = {"y": "granted", "n": "denied", "l": "later"}
            try:
                import tool_request as _tr
                if parts[1] == "list":
                    body, _kb = _tr.card()
                    toast = "صف"
                elif parts[1] in _VERDICTS and len(parts) >= 3:
                    v = _VERDICTS[parts[1]]
                    r = _tr.answer(_sanitize_id(parts[2]), v)
                    if not r.get("ok"):
                        body = f"🧰 نشد: {r.get('reason')}"
                        toast = "نشد"
                    elif v == "later":
                        body = ("🕓 باشد، باز می‌ماند — «بعداً» رأی نیست، پس این "
                                "درخواست بسته نشد و باز هم یادت می‌آورم.")
                        toast = "بعداً"
                    elif v == "granted":
                        body = ("✅ ثبت شد: بگیر.\n▸ تا وقتی ابزار واقعاً وصل نشود، "
                                "این فقط یک رأی است نه یک قابلیت.")
                        toast = "گرفتم"
                    else:
                        body = ("❌ ثبت شد: نه.\n▸ جایگزینی که خودش پیشنهاد داده بود "
                                "را پیش می‌برد.")
                        toast = "نه"
                    if r.get("wait_s") is not None:
                        body += f"\n<i>زمانِ انتظار: {int(r['wait_s'] // 60)} دقیقه</i>"
                else:
                    body, toast = "🧰 دستورِ نامعتبر.", "نامعتبر"
            except Exception:  # noqa: BLE001 — مسیرِ callback هرگز نمی‌میرد
                body, toast = "🧰 نشد.", "نشد"
            try:
                self._client.send(_scrub(body),
                                  chat_id=(msg.get("chat") or {}).get("id"),
                                  topic_id=self._reply_thread(msg))
            except Exception:  # noqa: BLE001
                pass
            self._answer(cbq, toast)
            return {"kind": "tool_request", "act": parts[1]}

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
                # C9: سقفِ فایل عمداً پاس نمی‌شود — metadata_scan.MAP_SCAN_MAX_FILES تنها محلِ
                # اعلام است. max_seconds=60 می‌ماند: اسکنِ بازگشتی روی این ماشین پاتولوژیک است.
                result = ms_mod.scan_metadata(max_seconds=60)
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
                    self._client.send(_scrub(txt), chat_id=chat,
                                      topic_id=self._dm_topic())
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
        # ── دو دکمهٔ مردهٔ کارتِ لید (VQ-DEAD-LEAD-BUTTONS-001، ۲۰۲۶-۰۸-۰۴) ──
        #
        # `lead_card.keyboard` دو دکمه می‌سازد — «📞 زنگ بزن» (`lcall`) و
        # «📤 پیش‌نویس» (`ldraft`) — و **هیچ‌کدام روت نداشتند**. مالک کلیک
        # می‌کرد و هیچ اتفاقی نمی‌افتاد؛ حتی spinner ِ تلگرام هم بی‌جواب
        # می‌ماند. دقیقاً همان «هرکاری می‌کنم دیده نمی‌شود».
        # `test_callback_routing` این را می‌دید و ۵/۶ بود، ولی قرمزش «همیشگی»
        # شمرده می‌شد نه رگرسیون.
        #
        # ⚠️ هر دو **فقط‌نمایش**اند و ماژول خودش این را تضمین می‌کند:
        # `SAFE_VERBS = {"lcall","ldraft"}` و `has_send_button()` گاردِ آن.
        # این‌جا هیچ transport ای صدا زده نمی‌شود، هیچ state ای عوض نمی‌شود،
        # و هیچ مغزی (پولی یا محلی) لمس نمی‌شود. صفر دلار، صفر اثرِ بیرونی.
        # ⚠️ `parts` در این متد وجود ندارد (مالِ `_handle_center_callback` است).
        # نسخهٔ اول از آن استفاده کرد و در زمانِ اجرا `UnboundLocalError` داد —
        # در حالی که `test_callback_routing` **۶/۶ سبز** بود، چون فقط سورس را
        # با regex می‌خواند و «روت شده» را از وجودِ `verb ==` نتیجه می‌گیرد.
        # سبزیِ آن تست دربارهٔ اجرا هیچ نمی‌گوید؛ فقط پروبِ رفتاری گرفتش.
        _lp = data.split(":")
        if verb in ("lcall", "ldraft") and len(_lp) == 2:
            lid = _lp[1]
            body = None
            try:
                import lead_card as _lc          # noqa: WPS433
                import lead_sense as _ls         # noqa: WPS433
                p = _ls.resolve_lead_path(lid)
                lead = json.loads(p.read_text("utf-8")) if p else None
                if lead is None:
                    body = "این لید دیگر پیدا نشد."
                elif verb == "lcall":
                    # `_contact_block` سه‌تاییِ (lines, missing, uri) می‌دهد.
                    # هدفِ این دکمه طبقِ سندِ خودِ ماژول: «شماره در گوشی قابلِ
                    # لمس شود» — پس بلوک به‌صورتِ **پیامِ نو** می‌رود، نه ویرایش.
                    lines, missing, _uri = _lc._contact_block(_lc.contact_of(lead))
                    head = [f"📞 <b>تماسِ لید</b> — <code>{lid}</code>"]
                    body = "\n".join(head + (list(lines) or ["—"]) + (
                        [f"<i>ناموجود: {'، '.join(missing)}</i>"] if missing else []))
                else:
                    body = _lc.draft_review_text(
                        (lead.get("first_reply") if isinstance(lead, dict) else None),
                        lead_id=lid)
            except Exception as _e:  # noqa: BLE001
                # ساکت نمی‌مانیم: یک دکمهٔ بی‌جواب همان باگی است که این بند
                # دارد رفعش می‌کند. پیامِ خطا به خودِ مالک می‌رود.
                body = f"نتوانستم این لید را باز کنم ({type(_e).__name__})."
            msg0 = cbq.get("message") or {}
            try:
                self._client.send(_scrub(str(body)),
                                  chat_id=(msg0.get("chat") or {}).get("id"),
                                  topic_id=self._reply_thread(msg0),
                                  stream=f"lead-{verb}")
            except Exception:  # noqa: BLE001
                pass
            self._answer(cbq)          # spinner ِ تلگرام حتماً بسته می‌شود
            return {"kind": "lead-card", "verb": verb, "lead_id": lid}

        if verb == "hm":
            return self._handle_home_callback(cbq, data)
        if verb == "tk":
            # دکمه‌های کارتِ پا (رأیِ ۰۷-۳۰ شب). مالکیت را بالادست گیت کرده.
            return self._handle_tasks_callback(cbq, data)
        if verb == "ops" and self._ops_buttons_on():
            # دکمه‌های `/ops` (لِینِ chat-actions، پشتِ OCTOPUS_TG_OPS_BUTTONS).
            # عمداً همین بالا و جدا از جدولِ مرکز — تا با هانکِ لِینِ موازی روی
            # آن جدول تصادم نکند (§ درختِ مشترک). فلگ خاموش ⇒ سقوط به مسیرِ
            # امروز (`ops` در _VERDICTS نیست → پل → «نادیده») — parity.
            return self._handle_ops_callback(cbq, data)
        if verb == "rm":
            # یادآورها (لِین E، پشتِ OCTOPUS_TG_REMINDERS). فلگ خاموش ⇒ سقوط به
            # مسیرِ امروز («نادیده») — parity. دبل‌تاپ بی‌اثر (done/snooze idempotent).
            try:
                import reminders as _rm0
                if _rm0.enabled():
                    return self._handle_reminder_callback(cbq, data)
            except Exception:  # noqa: BLE001
                pass
        if verb == "qb":
            # بودجهٔ سؤال (لِین H، پشتِ OCTOPUS_TG_QBUDGET): جوابِ واقعی از
            # **ریپلای** می‌آید نه تاپ — این شاخه فقط راه را می‌گوید و spinner
            # را می‌کشد (§۶.۴). فلگ خاموش ⇒ مسیرِ امروز — parity.
            try:
                import question_budget as _qb0
                if _qb0.enabled():
                    self._answer(cbq, "برای جواب، به پیامِ سؤال ریپلای کن")
                    return {"kind": "qbudget", "hint": True}
            except Exception:  # noqa: BLE001
                pass
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
            # مسیرِ blocked هم answer می‌گیرد — spinner ِ oc: (یافتهٔ §4 نقشه:
            # adapter بی‌جواب/exception ⇒ تا امروز هیچ answerCallbackQuery نبود).
            self._answer(cbq, "مامور جوابی نداشت")
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
        if verb in ("mn", "lg", "pw", "pwc", "ng", "mr", "qt", "iv", "dg", "x",
                    "tr"):
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
            # ── پلِ دکمه‌ها (۲۰۲۶-۰۷-۳۱، یافتهٔ اسکنِ عمیق) ──────────────────
            # پلِ فرمان‌ها (`_bridge_to_organism`) جواب را با **کیبوردش** روی
            # باتِ بیرونی می‌فرستد — ولی تپِ همان کیبورد به همین‌جا برمی‌گشت و
            # «نادیده» می‌گرفت: ~۳۵ فرمانِ bridged همگی کارتِ مرده بودند، از
            # جمله app:approve/deny (**پول**) و rfc:merge. پروبِ ۱۳ verb
            # اثباتش کرد (menu/card/pg/act/acct/jrn/rev/rfc/app/brain/home/
            # prop). حالا تپ هم همان پل را طی می‌کند — متقارن با فرمان.
            # امنیت دو-لایه: بالادست فقط مالک را به این‌جا می‌رساند، و خودِ
            # dispatch_callback با external=True هر mutating را fail-closed
            # می‌سنجد (C7.2/P0). ناشناخته برای هر دو → «نادیده»ی امروز.
            _r = self._bridge_callback_to_organism(cbq, data)
            if _r is not None:
                return _r
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

    # ══ /ops دکمه‌ای — لِینِ chat-actions (پشتِ OCTOPUS_TG_OPS_BUTTONS) ═══════
    #
    # چرا این‌جا و نه یک روتِ نو: `/ops` از قبل روت دارد — بلوکِ AGI2027 در
    # `_handle_message` که به `agi2027_control.integration.try_handle_control`
    # می‌رود و جوابش را با `format_control_result` می‌فرستد. این لِین همان روت
    # را **کامل** می‌کند (کیبورد به همان پیام می‌چسبد)؛ روتِ دوم ساخته نمی‌شود.
    #
    # مالکیت: گیتِ تازه‌ای اختراع نشده. `handle_update → _is_owner` غیرمالک را
    # کاملاً ساکت رد می‌کند (نه پیام، نه answer، نه رسید — عمدی و قفل‌شده در
    # test_tg_callback_answer)، و لایهٔ دومِ `OpsActionEngine.execute` هم
    # `actor["is_owner"]` می‌خواهد.
    #
    # جهش فقط از **همان** مسیرِ owner-gated ِ موجود (Ops Studio) می‌رود؛ هیچ
    # گیتی برداشته نمی‌شود — فقط دکمه به گیت وصل می‌شود.

    @staticmethod
    def _ops_buttons_on() -> bool:
        """فلگِ دکمه‌های `/ops` — پیش‌فرض خاموش."""
        return str(os.environ.get(OPS_BUTTONS_FLAG, "")).strip().lower() in (
            "1", "true", "yes", "on")

    @staticmethod
    def _ops_mod():
        """ماژولِ موتورِ اکشنِ Ops Studio — **همان** موتوری که MiniApp صدا می‌زند."""
        p = str(_HERE.parent)
        if p not in sys.path:
            sys.path.insert(0, p)
        import agi2027_control.ops_actions as _oa   # noqa: WPS433
        return _oa

    def _ops_receipt(self, **kw) -> bool:
        """رسیدِ هر تپ: که، چه، کِی، نتیجه — **شاملِ ردها**.

        چرا رسیدِ جدا و نه اتکا به AuditLog ِ خودِ موتور: `OpsActionEngine.
        execute` برای `DENIED`/`BLOCKED` **پیش از** `self.audit.append`
        برمی‌گردد — یعنی دقیقاً ردها بی‌رد می‌مانند. این‌جا رد هم می‌نشیند،
        وگرنه «هیچ اتفاقی نیفتاد» و «رد شد» یک شکل می‌شوند.

        هم‌ریشهٔ همان موتور (env-اول ⇒ تست خودکار ایزوله)، append-only + fsync.
        fail-soft: شکستِ رسید هرگز مسیرِ دکمه را عوض نمی‌کند."""
        try:
            _oa = self._ops_mod()
            from agi2027_control.runtime import AuditLog as _AL  # noqa: WPS433
            rt = Path(os.environ.get(
                "OCTOPUS_OPS_RUNTIME_DIR",
                str(_oa.ROOT / "_ops" / "agi2027_runtime")))
            rec = {"event": "ops_button", "source": "tg-center"}
            rec.update(kw)
            _AL(rt / "ops-buttons-audit.jsonl").append(rec)
            return True
        except Exception:  # noqa: BLE001
            return False

    def _ops_miniapp_url(self) -> "str | None":
        """URL ِ کاکپیت از **همان دو منبعی که از قبل هست**: فایلِ تازهٔ
        `_miniapp_url()` (contract F.3) و بعد `OCTOPUS_MINIAPP_URL` که
        ControlPlane ِ `/ui` می‌خوانَد. منبعِ سوم اختراع نمی‌شود."""
        try:
            u = self._miniapp_url()
            if u:
                return u
        except Exception:  # noqa: BLE001
            pass
        u = str(os.environ.get("OCTOPUS_MINIAPP_URL", "") or "").strip()
        return u if u.startswith("https://") else None

    def _ops_keyboard(self, text: str) -> "list | None":
        """کیبوردِ `/ops`. فلگ خاموش یا فرمانِ غیرِ `/ops` ⇒ None ⇒ همان پیامِ
        بی‌کیبوردِ امروز.

        ناوبری `web_app` است و فقط به تب‌هایی می‌رود که **امروز در
        `miniapp/index.html` وجود دارند** (home/studio/approvals). بدونِ
        URL ِ زنده هیچ دکمهٔ web_app ساخته نمی‌شود — جایش یک callback که
        صادقانه علت را می‌گوید؛ دکمهٔ مرده هرگز.

        ⚠️ ثبت‌شده و اثبات‌شده: `miniapp/app.js` امروز `location.hash` را
        نمی‌خوانَد (همیشه `render("home")`)، پس `#tab=` هنوز عمق-لینکِ
        **واقعی نیست** — فرگمنت جلوجلو فرستاده می‌شود تا لحظه‌ای که لِینِ
        MiniApp خواننده‌اش را اضافه کند کار کند. این فایل مالکِ app.js نیست."""
        if not self._ops_buttons_on():
            return None
        raw = str(text or "").strip()
        if not raw or raw.split()[0].split("@")[0].lower() != "/ops":
            return None
        url = self._ops_miniapp_url()

        def _nav(label: str, tab: str, cb: str) -> dict:
            if url:
                return {"text": label, "web_app": {"url": f"{url}#tab={tab}"}}
            return {"text": label, "callback_data": cb}

        return [
            [_nav("🖥 کاکپیت", "home", "ops:ui"),
             _nav("📋 کارهای امروز", "studio", "ops:tsk")],
            [{"text": "🆕 لیدِ نو", "callback_data": "ops:lead"},
             {"text": "💰 ثبتِ پول", "callback_data": "ops:money"}],
            [{"text": "🧠 وضعیتِ مغز", "callback_data": "ops:brain"},
             _nav("✅ تأییدها", "approvals", "ops:apr")],
        ]

    def _handle_ops_callback(self, cbq: dict, data: str) -> dict:
        """دکمه‌های `/ops`. **هر مسیر** — شاملِ رد و ناشناخته — answer می‌گیرد
        (منشور §۶.۴: دکمه‌ای که تا ابد می‌چرخد دکمهٔ مرده است) و رسید می‌گذارد.

        مالکیت بالادست گیت شده؛ این‌جا گیتِ دوم ساخته نمی‌شود."""
        seg = str(data or "").split(":")
        act = seg[1] if len(seg) > 1 else ""
        who = (cbq.get("from") or {}).get("id")
        if act in ("lead", "money"):
            return self._ops_ask(cbq, act, who)
        if act == "t":
            return self._ops_followup_task(
                cbq, seg[2] if len(seg) > 2 else "", who)
        msg = cbq.get("message") or {}
        if act == "brain":
            self._answer(cbq, "وضعیتِ مغز")
            _sent = None
            try:
                _sent = self._client.send(
                    _scrub(self._ops_brain_text()),
                    chat_id=(msg.get("chat") or {}).get("id"),
                    topic_id=msg.get("message_thread_id"))
            except Exception:  # noqa: BLE001
                pass
            self._ops_receipt(actor=who, act="brain", outcome="OK",
                              mutated=False, sent=_sent is not None)
            return {"kind": "ops-button", "act": "brain", "outcome": "OK",
                    "mutated": False, "sent": _sent is not None}
        if act in ("ui", "tsk", "apr"):
            # این callbackها فقط وقتی **ساخته** می‌شوند که URL ِ زنده نبوده
            # (وگرنه همان دکمه web_app است و اصلاً callback نمی‌فرستد). پس
            # تنها جوابِ صادق «هنوز آدرسی نیست» است، نه spinner.
            self._answer(cbq, "کاکپیت هنوز URL ندارد — OCTOPUS_MINIAPP_URL یا "
                              "تونلِ MiniApp را روشن کن")
            self._ops_receipt(actor=who, act=act, outcome="CONFIG_NEEDED",
                              mutated=False)
            return {"kind": "ops-button", "act": act,
                    "outcome": "CONFIG_NEEDED", "mutated": False}
        self._answer(cbq, "این دکمه را نمی‌شناسم")
        self._ops_receipt(actor=who, act=act or None, outcome="UNKNOWN_BUTTON",
                          mutated=False)
        return {"kind": "ops-button", "act": act or None,
                "outcome": "UNKNOWN_BUTTON", "mutated": False}

    def _ops_ask(self, cbq: dict, kind: str, who) -> dict:
        """دکمهٔ جهش‌زایی که **ورودی لازم دارد** → جریانِ ریپلایِ موجود.

        ماشینِ حالتِ نو ساخته نمی‌شود: پیامِ راهنما یک مارکرِ پایدار دارد و
        مصرف‌کننده‌اش (`_ops_reply`) فقط `reply_to_message` را می‌بیند — همان
        الگویی که question_budget با «سؤالِ اختاپوس» دارد.

        نتیجه: خودِ تپ **هیچ رکوردی نمی‌سازد** (دبل‌تپ هم صفر)؛ ثبت با ریپلای
        است و آن هم به `message_id` ِ همان ریپلای idempotent شده."""
        if kind == "lead":
            body = ("🆕 <b>لیدِ نو</b>\n"
                    "▸ به همین پیام ریپلای کن و فقط نام/هندلِ لید را بنویس.\n"
                    "▸ مثال: <code>علی چتسوود</code>\n"
                    f"<code>{OPS_ASK_LEAD}</code>")
        else:
            body = ("💰 <b>ثبتِ پول</b>\n"
                    "▸ به همین پیام ریپلای کن: اول مبلغ، بعد توضیحِ کوتاه.\n"
                    "▸ مثال: <code>۴۵۰ بیعانهٔ چتسوود</code>\n"
                    "▸ این فقط یک <b>ثبت</b> است — هیچ پولی جابه‌جا نمی‌شود.\n"
                    f"<code>{OPS_ASK_MONEY}</code>")
        self._answer(cbq, "به پیامِ راهنما ریپلای کن")
        msg = cbq.get("message") or {}
        _sent = None
        try:
            _sent = self._client.send(
                _scrub(body), chat_id=(msg.get("chat") or {}).get("id"),
                topic_id=msg.get("message_thread_id"))
        except Exception:  # noqa: BLE001
            pass
        self._ops_receipt(actor=who, act=kind, outcome="PROMPTED",
                          mutated=False, sent=_sent is not None)
        return {"kind": "ops-button", "act": kind, "outcome": "PROMPTED",
                "mutated": False, "sent": _sent is not None}

    def _ops_action(self, action: str, payload: dict, action_id: str) -> dict:
        """اجرا از **همان** مسیرِ owner-gated ِ موجود (`OpsActionEngine`).

        هیچ گیتی برداشته نمی‌شود: خودِ `execute` مالکیت، allowlist ِ اکشن و
        ممنوعیتِ اتوماسیونِ پلتفرم‌های بیرونی را می‌سنجد، و `IdempotencyStore`
        تضمین می‌کند دو بار = یک رکورد. `actor` دقیقاً مثلِ بلوکِ AGI2027 ِ
        بالادست ساخته می‌شود، چون `_is_owner` قبلاً شلیک کرده و غیرمالک اصلاً
        به این‌جا نمی‌رسد."""
        eng = None
        try:
            eng = self._ops_mod().OpsActionEngine()
            return eng.execute(action, payload, {"is_owner": True},
                               action_id=action_id)
        except Exception as _e:  # noqa: BLE001 — موتورِ خراب = ردِ صادق نه crash
            return {"ok": False, "status": "ERROR",
                    "reason": f"ops_engine_exception:{type(_e).__name__}"}
        finally:
            if eng is not None:
                try:
                    eng.close()
                except Exception:  # noqa: BLE001
                    pass

    def _ops_followup_task(self, cbq: dict, lead_id: str, who) -> dict:
        """`ops:t:<lead_id>` — کارِ پیگیری برای لیدی که همین‌الان ساخته شد.

        تنها دکمهٔ جهش‌زایی که **ورودی نمی‌خواهد**، پس دبل‌تپ را مستقیم
        می‌سنجد. دو گاردِ مستقل: (۱) `action_id` قطعی است
        (`tgops:task.create:<lead>`) ⇒ تپِ دوم `DUPLICATE` می‌گیرد؛ (۲) حتی
        اگر کلید عوض شود، `id` ِ قطعیِ کار باعثِ UPSERT روی همان ردیف می‌شود."""
        lid = _sanitize_id(lead_id)
        if not str(lead_id or "").strip() or lid == "unknown":
            self._answer(cbq, "شناسهٔ لید نامعتبر")
            self._ops_receipt(actor=who, act="t", outcome="BLOCKED",
                              reason="invalid_lead_id", mutated=False)
            return {"kind": "ops-button", "act": "t", "outcome": "BLOCKED",
                    "mutated": False}
        key = f"tgops:task.create:{lid}"
        res = self._ops_action(
            "task.create",
            {"id": f"followup-{lid}", "title": f"پیگیریِ {lid}",
             "kind": "followup", "target_type": "lead", "target_id": lid}, key)
        st = str(res.get("status") or "ERROR")
        self._answer(cbq, _OPS_TOAST.get(st, f"نشد: {st}"))
        self._ops_receipt(actor=who, act="t", action="task.create",
                          action_id=key, outcome=st, ok=bool(res.get("ok")),
                          mutated=(st == "APPLIED"))
        return {"kind": "ops-button", "act": "t", "outcome": st,
                "mutated": st == "APPLIED", "task_id": res.get("task_id")}

    def _ops_refuse(self, kind: str, reason: str, chat_id, msg: dict, who,
                    say: str) -> dict:
        """ردِ ورودی — و **ثبتش**. رد بی‌رسید یعنی «هیچ اتفاقی نیفتاد» و
        «رد شد» یک شکل شوند (درسِ ثبت-همیشه/گیتِ-تحویل)."""
        _sent = None
        try:
            _sent = self._client.send(_scrub(f"⚠️ {say}"), chat_id=chat_id,
                                      topic_id=self._reply_thread(msg))
        except Exception:  # noqa: BLE001
            pass
        self._ops_receipt(actor=who, act=kind, outcome="REFUSED",
                          reason=reason, mutated=False, sent=_sent is not None)
        return {"kind": "ops-reply", "act": kind, "outcome": "REFUSED",
                "reason": reason, "mutated": False}

    def _ops_reply(self, msg: dict, text: str, chat_id) -> "dict | None":
        """ریپلای به پیامِ راهنمای `/ops` → جهش از مسیرِ owner-gated.

        فلگ خاموش یا بی‌مارکر ⇒ None ⇒ مسیرِ امروزِ پیام، بایت‌به‌بایت.

        idempotency: کلید به هویتِ **همان پیامِ ریپلای** بسته است
        (`tgops:<action>:<chat>:<message_id>`)، پس تحویلِ دوبارهٔ همان update
        رکوردِ دوم نمی‌سازد؛ و شناسهٔ خودِ رکورد هم از محتوا ساخته می‌شود
        (UPSERT)، پس دو ریپلایِ هم‌محتوا هم یک ردیف می‌مانند."""
        if not self._ops_buttons_on():
            return None
        _rt = str((msg.get("reply_to_message") or {}).get("text") or "")
        if OPS_ASK_LEAD in _rt:
            kind, action = "lead", "lead.create"
        elif OPS_ASK_MONEY in _rt:
            kind, action = "money", "value.record_event"
        else:
            return None
        who = (msg.get("from") or {}).get("id")
        body = str(text or "").strip()
        if not body:
            return self._ops_refuse(kind, "empty_input", chat_id, msg, who,
                                    "چیزی ننوشتی — دوباره ریپلای کن.")
        key = f"tgops:{action}:{chat_id}:{msg.get('message_id')}"
        if kind == "lead":
            handle = body.splitlines()[0].strip()[:OPS_HANDLE_MAX]
            if not handle:
                return self._ops_refuse(kind, "missing_handle", chat_id, msg,
                                        who, "نام/هندلِ لید خالی بود.")
            payload = {"handle": handle, "stage": "new", "source": "tg-ops",
                       "platform": "manual", "notes": body}
        else:
            _m = re.search(r"\d+(?:[.,]\d+)?", body.translate(_OPS_FA2EN))
            if _m is None:
                return self._ops_refuse(kind, "missing_amount", chat_id, msg,
                                        who, "مبلغ پیدا نشد — اول عدد بنویس.")
            payload = {"leg": "ops_studio", "event": "money_in",
                       "value_type": "money",
                       "output_score": float(_m.group(0).replace(",", ".")),
                       "metadata": {"note": body[:200], "source": "tg-ops"}}
        res = self._ops_action(action, payload, key)
        st = str(res.get("status") or "ERROR")
        _inner = res.get("result") if isinstance(res.get("result"), dict) else {}
        rid = str(res.get("lead_id") or res.get("value_event_id")
                  or _inner.get("lead_id") or _inner.get("value_event_id") or "")
        if st == "APPLIED":
            head = "🆕 لید ثبت شد ✅" if kind == "lead" else "💰 ثبت شد ✅"
        elif st == "DUPLICATE":
            head = "🔁 قبلاً ثبت شده بود — رکوردِ دومی ساخته نشد."
        else:
            head = f"⚠️ نشد: <code>{_sanitize_id(st)}</code>"
        lines = [head]
        if rid:
            lines.append(f"▸ <code>{_sanitize_id(rid)}</code>")
        if kind == "money":
            lines.append("▸ فقط ثبت شد — هیچ پولی جابه‌جا نشد.")
        kb = None
        # ⚠️ فقط شناسه‌ای که **رفت‌وبرگشت** می‌کند دکمه می‌گیرد: `make_id` نویسه‌های
        # `.:@` را هم مجاز می‌داند، ولی `:` جداکنندهٔ خودِ callback است و
        # `_sanitize_id` هم `@` را به `-` می‌برد — یعنی دکمه به شناسهٔ دیگری اشاره
        # می‌کرد. سقفِ ۵۶ هم بودجهٔ ۶۴بایتیِ تلگرام را تضمین می‌کند (۶+۵۶=۶۲).
        if (kind == "lead" and rid and st in ("APPLIED", "DUPLICATE")
                and re.fullmatch(r"[A-Za-z0-9_-]{1,56}", rid)):
            kb = [[{"text": "🗒 کارِ پیگیری", "callback_data": f"ops:t:{rid}"}]]
        _sent = None
        try:
            _sent = self._client.send(
                _scrub("\n".join(lines)), chat_id=chat_id, keyboard=kb,
                topic_id=self._reply_thread(msg))
        except Exception:  # noqa: BLE001
            pass
        self._ops_receipt(actor=who, act=kind, action=action, action_id=key,
                          outcome=st, ok=bool(res.get("ok")),
                          mutated=(st == "APPLIED"), record_id=rid,
                          sent=_sent is not None)
        return {"kind": "ops-reply", "act": kind, "outcome": st,
                "mutated": st == "APPLIED", "record_id": rid,
                "sent": _sent is not None}

    def _ops_brain_text(self) -> str:
        """وضعیتِ مغز — فقط‌خواندنی، $۰، بدونِ هیچ تماسِ LLM.

        عمداً به تبِ MiniApp لینک **نمی‌شود**: امروز در `miniapp/index.html`
        تبِ Brain وجود ندارد (تب‌ها: home/studio/outbound/approvals/legs/
        value/registry/truth). لینک به تبی که نیست همان کارتِ مرده است."""
        try:
            import ask_brain as _ab   # noqa: WPS433
        except Exception:  # noqa: BLE001
            return "🧠 ماژولِ مغز در دسترس نیست."
        lines = ["🧠 <b>وضعیتِ مغز</b>"]
        try:
            lines.append("▸ مغزِ گران: "
                         + ("روشن" if _ab.enabled() else "خاموش"))
            lines.append("▸ گفتگوی محلی: "
                         + ("روشن" if _ab.chat_local_enabled() else "خاموش"))
            _st = _ab._load_state()
            _used = (int(_st.get("used") or 0)
                     if _st.get("date") == opslib.today() else 0)
            lines.append(f"▸ سهمیهٔ پولیِ امروز: {_fa_num(_used)}"
                         f"/{_fa_num(_ab._daily_cap())}")
        except Exception:  # noqa: BLE001 — سنجه هرگز کارت را نمی‌کشد
            lines.append("▸ خواندنِ سهمیه نشد.")
        lines.append("▸ این کارت هیچ تماسی با مغز نمی‌گیرد — $۰.")
        return "\n".join(lines)

    # ── نامه‌های مرده: updateهایی که پردازششان شکست خورد ──────────────────────
    #
    # VQ-SILENT-DROP-001 (۲۰۲۶-۰۸-۰۴، از شکایتِ مالک «انگار هرکاری می‌کنم دیده
    # نمی‌شود»). حلقهٔ poll این شکل بود:
    #
    #     if isinstance(uid, int) and uid > max_id:
    #         max_id = uid            ← offset همین‌جا جلو می‌رفت
    #     try:
    #         self.handle_update(u)
    #     except Exception:
    #         pass                    ← شکست بی‌صدا بلعیده می‌شد
    #
    # یعنی **هر** استثنا وسطِ پردازشِ یک پیام، آن پیام را برای همیشه می‌بلعید:
    # ‏`max_id` از قبل جلو رفته بود، آخرِ حلقه در config ذخیره می‌شد، و تلگرام
    # دیگر هرگز تحویلش نمی‌داد. صفر لاگ، صفر شمارنده، صفر هشدار.
    #
    # چرا offset را روی شکست **عقب نمی‌بریم**: یک پیامِ سمی آن‌وقت تا ابد
    # بازپخش می‌شود و حلقه را گیر می‌اندازد — بدتر از گم‌شدن. پس الگوی
    # dead-letter: offset جلو می‌رود (حلقه سالم می‌ماند)، ولی خودِ update
    # **ماندگار** ذخیره می‌شود و مالک خبردار می‌شود. هیچ‌چیز بی‌صدا گم نمی‌شود.
    #
    # ⚠️ و هشدار خودش نباید منبعِ اسپمِ نو شود (شکایتِ دومِ مالک شلوغی بود):
    # همان نوعِ خطا در پنجرهٔ `_DL_ALERT_COOLDOWN_S` فقط **یک‌بار** هشدار
    # می‌دهد؛ بقیه فقط در فایل می‌نشینند.
    _DL_ALERT_COOLDOWN_S = 900.0

    def _dead_letter(self, update: dict, exc: BaseException) -> None:
        """updateِ شکست‌خورده را ماندگار کن و (با cooldown) مالک را خبر کن.

        خودش هرگز استثنا نمی‌دهد: گاردی که حلقه را بکشد بدتر از گاردِ نبوده."""
        kind = type(exc).__name__
        try:
            d = opslib.STATE_DIR / "telegram" / "dead-letters.jsonl"
            d.parent.mkdir(parents=True, exist_ok=True)
            with open(d, "a", encoding="utf-8", newline="\n") as fh:
                fh.write(json.dumps({
                    "ts": opslib.now_iso(),
                    "error": kind,
                    "detail": str(exc)[:300],
                    "update_id": update.get("update_id"),
                    "update": update,      # کاملِ update — همین‌جا در state، نه در چت
                }, ensure_ascii=False) + "\n")
        except Exception:  # noqa: BLE001
            pass
        try:
            last = getattr(self, "_dl_last", {})
            now = time.time()
            if now - float(last.get(kind, 0.0)) >= self._DL_ALERT_COOLDOWN_S:
                last[kind] = now
                self._dl_last = last
                opslib.alert([
                    f"⚠️ یک پیامِ تلگرام پردازش نشد و رد شد ({kind}). "
                    f"متنش در state/telegram/dead-letters.jsonl هست — گم نشده. "
                    f"اگر چیزی فرستادی و جواب نگرفتی، همین است."])
        except Exception:  # noqa: BLE001
            pass

    # ── لاگِ ورودی ────────────────────────────────────────────────────────────
    #
    # VQ-NO-INBOUND-LOG-001 (۲۰۲۶-۰۸-۰۴). ممیزیِ ۱۶-ایجنته این را علتِ
    # **ساختاریِ** حسِ «دیده نمی‌شوم» نامید، و درست گفت:
    #
    #   `tg-send-log.jsonl` فقط **خروجی** را ثبت می‌کند. هیچ جای سیستم
    #   نمی‌نویسد «آپدیتِ N رسید، از نوعِ X، ساعتِ T». پس سؤالِ «پیامی که
    #   فرستادم رسید؟» بعد از وقوع **جواب‌ناپذیر** بود — نه برای مالک، نه
    #   برای ایجنتِ بعدی، نه برای خودِ ارگانیسم.
    #
    # حالا هر update ِ رسیده یک ردیف می‌گذارد، **قبل** از dispatch. اگر
    # پردازش بترکد، ردیفِ ورودی از قبل نشسته و کنارِ نامهٔ مرده می‌نشیند:
    # یکی می‌گوید «رسید»، دیگری می‌گوید «پردازش نشد». با هم، تصویرِ کامل.
    #
    # ⚠️ §۱۰ منشور: متنِ پیام **ذخیره نمی‌شود** — فقط شکل و اندازه. متن اگر
    # لازم شد در نامهٔ مرده هست (فقط برای پیامی که شکست خورد). این‌جا هدف
    # «آیا رسید؟» است نه بایگانیِ مکالمه، و ذخیرهٔ همهٔ متن‌ها یک نشتیِ
    # PII ِ دائمی می‌ساخت که هیچ‌کس نخواسته بود.
    #
    # ⚠️ و هرگز alert نمی‌دهد: این لاگ **ساکت** است. مالک از شلوغی شکایت
    # داشت؛ یک ردیفِ روزمره خبر نیست.
    _INBOUND_KEEP = 5000            # سقفِ ردیف — لاگِ بی‌سقف خودش یک باگ است

    def _bind_send_correlation(self, update_id) -> None:
        """ارسال‌های این نخ را به این update بچسبان (یا با None رها کن).

        چرا لازم شد: `inbound-log` می‌گفت «رسید» و `tg-send-log` می‌گفت
        «فرستادم» — ولی هیچ کلیدِ مشترکی نداشتند (ISO در برابر اپاک). پس
        «آیا آن پیامِ من جواب گرفت؟» فقط با **همسایگیِ زمانی** حدس زده
        می‌شد، و وقتی دو بات به یک چت می‌فرستند آن حدس ابطال‌ناپذیر است.

        fail-soft مطلق: خودِ برچسب هرگز نباید پردازشِ update را بکشد — یک
        رسیدِ گم‌شده بد است، یک updateِ ازدست‌رفته بدتر."""
        try:
            import tg_send_log as _tsl_bind  # noqa: WPS433 — lazy، هم‌الگوی بقیه
            if update_id is None:
                _tsl_bind.clear_update()
            else:
                _tsl_bind.bind_update(update_id)
        except Exception:  # noqa: BLE001 — برچسب هرگز مسیرِ اصلی را نمی‌کشد
            pass

    def _log_inbound(self, u: dict) -> None:
        """یک ردیفِ ساکت به ازای هر update ِ رسیده. هرگز استثنا نمی‌دهد."""
        try:
            msg = u.get("message") or u.get("edited_message") or {}
            cq = u.get("callback_query") or {}
            if cq:
                kind, text = "callback_query", str(cq.get("data") or "")
            # ⚠️ `in` نه `.get()`: یک آبجکتِ **خالی** falsy است و یک ویسِ
            # ناقص به‌جای «voice» به‌عنوان چیزِ دیگری برچسب می‌خورد. دقیقاً
            # همان موردی است که اولین اجرای گاردِ متناظر گرفت. حضورِ کلید
            # جواب می‌دهد، نه صدقِ مقدارش.
            elif "voice" in msg:
                kind, text = "voice", ""
            elif "photo" in msg:
                kind, text = "photo", ""
            elif "document" in msg:
                kind, text = "document", ""
            elif "text" in msg:
                kind, text = "text", str(msg.get("text") or "")
            else:
                kind, text = (sorted(k for k in u if k != "update_id") or ["?"])[0], ""
            chat = (msg.get("chat") or (cq.get("message") or {}).get("chat") or {})
            row = {
                "ts": opslib.now_iso(),
                "update_id": u.get("update_id"),
                "kind": kind,
                # نه متن، نه chat_id: فقط چیزی که به «رسید یا نه» جواب می‌دهد.
                "chars": len(text),
                "is_command": text.startswith("/"),
                # اولین توکن یک فرمان محتوا نیست و برای عیب‌یابی حیاتی است.
                "cmd": (text.split() or [""])[0][:32] if text.startswith("/") else "",
                "chat_kind": str(chat.get("type") or ""),
                "from_owner": bool(
                    str((msg.get("from") or cq.get("from") or {}).get("id") or "")
                    == str(getattr(self._client, "owner_chat_id", "") or "")),
            }
            p = opslib.STATE_DIR / "telegram" / "inbound-log.jsonl"
            p.parent.mkdir(parents=True, exist_ok=True)
            with open(p, "a", encoding="utf-8", newline="\n") as fh:
                fh.write(json.dumps(row, ensure_ascii=False) + "\n")
            # چرخش: بی‌سقف یعنی یک فایلِ چندصدمگابایتی روی دیسکِ مکانیکی.
            try:
                if p.stat().st_size > 4_000_000:
                    keep = p.read_text("utf-8", errors="replace").splitlines()[-self._INBOUND_KEEP:]
                    p.write_text("\n".join(keep) + "\n", encoding="utf-8", newline="\n")
            except OSError:
                pass
        except Exception:  # noqa: BLE001 — لاگ هرگز حلقه را نمی‌کشد
            pass

    def _log_disposition(self, u: dict, *, outcome: str, reason: str = "",
                         detail: str = "") -> None:
        """چرا این update به جایی نرسید — کنارِ همان ردیفِ «رسید».

        VQ-ARRIVED-BUT-WHY-001 (۲۰۲۶-۰۸-۰۴، از مشاهدهٔ خودِ مالک). لاگِ ورودی
        می‌گفت «رسید» و بس. رسیدِ ردِ سیاستِ ورودی وجود داشت ولی در لاگِ
        **خروجی** (`tg_send_log`, `state="blocked"`) با مهرِ زمانیِ اپاک —
        یعنی مالک برای فهمیدنِ «رسید ولی چرا هیچ نشد؟» باید دو فایل با دو
        فرمتِ زمانی را دستی جوین می‌کرد.

        حالا هر دو ردیف در **یک** فایل و با همان `update_id` می‌نشینند، پس
        جوین‌شدنی‌اند. همان درسِ امروز از `_context`: دو فهرستِ درست که
        به‌هم وصل نمی‌شوند، عملاً هیچ‌اند.

        ⚠️ متن ذخیره نمی‌شود (§۱۰) — فقط دلیلِ ساختاری.
        """
        try:
            u = u if isinstance(u, dict) else {}
            msg = u.get("message") or (u.get("callback_query") or {}).get("message") or {}
            # مسیرهای عمیق (مثلِ dispatchِ فرمان) خودِ `u` را ندارند — فقط `msg`.
            # پس `update_id` از همان برچسبِ نخ می‌آید که `run_once` بسته است.
            # بدونِ این fallback، ردیفِ «چرا» یک `update_id: null` می‌گرفت و
            # **دقیقاً همان چیزی که قرار بود جوین‌شدنی باشد جوین‌ناپذیر می‌شد**.
            uid = u.get("update_id")
            if uid is None:
                try:
                    import tg_send_log as _tsl_uid  # noqa: WPS433 — lazy
                    uid = _tsl_uid.current_update()
                except Exception:  # noqa: BLE001
                    uid = None
            p = opslib.STATE_DIR / "telegram" / "inbound-log.jsonl"
            p.parent.mkdir(parents=True, exist_ok=True)
            with open(p, "a", encoding="utf-8", newline="\n") as fh:
                fh.write(json.dumps({
                    "ts": opslib.now_iso(),
                    "bot": "center",
                    "update_id": uid,
                    "kind": "disposition",
                    "outcome": str(outcome)[:32],
                    "reason": str(reason)[:80],
                    "detail": str(detail)[:120],
                    "chat_kind": str((msg.get("chat") or {}).get("type") or ""),
                }, ensure_ascii=False) + "\n")
        except Exception:  # noqa: BLE001 — ثبت هرگز مرکز را نمی‌کشد
            pass

    #: چند شکستِ **پیاپیِ** poll تا صدا در بیاید. یک قطعیِ گذرا باید ساکت باشد،
    #: وگرنه گاردِ گرگ‌گرگ می‌شود؛ ولی یک قطعیِ طولانی از «پیامی نیست» غیرقابلِ
    #: تفکیک است و دقیقاً همان چیزی است که یک‌بار ۳۱ ساعت قحطیِ دایجست ساخت.
    _POLL_FAIL_LOUD_AFTER = 5

    def _poll_failed(self, exc: BaseException) -> None:
        n = int(getattr(self, "_poll_fails", 0)) + 1
        self._poll_fails = n
        if n == self._POLL_FAIL_LOUD_AFTER:
            try:
                opslib.alert([
                    f"⚠️ {n} بارِ پیاپی poll ِ تلگرام شکست خورد "
                    f"({type(exc).__name__}). تا رفع نشود هیچ پیامی نمی‌رسد — "
                    "و این از «پیامی نیست» قابلِ تفکیک نبود."])
            except Exception:  # noqa: BLE001
                pass

    # ── run: یک دورِ poll+dispatch / حلقه با STOP ────────────────────────────────
    def run_once(self) -> int:
        """یک دورِ poll + dispatch. خروجی = تعدادِ updateهای پردازش‌شده.
        STOP/ناوصل → 0 (بدونِ هیچ فراخوانی). offset در config (restart-safe)."""
        if self.stopped() or not self._wired():
            return 0
        cfg = _load_config()
        try:
            offset = int(cfg.get("last_offset", 0) or 0)
        except (TypeError, ValueError) as exc:
            # ‏offset ِ خراب = `0` = «هرچه در صف داری بده» ⇒ تلگرام تا ۲۴ ساعت
            # آپدیت را دوباره تحویل می‌دهد و همه‌چیز بازپخش می‌شود. سکوت این‌جا
            # یعنی مالک یک رگبارِ تکراری می‌بیند و علتش را نمی‌فهمد.
            offset = 0
            try:
                opslib.alert([f"⚠️ last_offset ِ تلگرام خوانا نبود "
                              f"({type(exc).__name__}) — از صفر شروع شد؛ ممکن "
                              "است پیام‌های قدیمی دوباره پردازش شوند."])
            except Exception:  # noqa: BLE001
                pass
        try:
            ups = self._client.poll_updates(offset=offset, timeout_s=POLL_TIMEOUT_S) or []
        except Exception as exc:  # noqa: BLE001 — خطای شبکه = دورِ خالی، حلقه زنده می‌ماند
            self._poll_failed(exc)          # ساکت تا N ِ پیاپی، بعد بلند
            return 0
        self._poll_fails = 0                # موفقیت = ریستِ شمارنده
        n = 0
        max_id = offset - 1
        for u in ups:
            if not isinstance(u, dict):
                continue
            uid = u.get("update_id")
            if isinstance(uid, int) and uid > max_id:
                max_id = uid
            # **قبل** از dispatch: اگر پردازش بترکد، ردیفِ «رسید» از قبل نشسته
            # و کنارِ نامهٔ مرده تصویرِ کامل می‌دهد.
            self._log_inbound(u)
            # فاز ۰ (۰۸-۰۴): هر ارسالی که از دلِ همین update بیرون بیاید،
            # `update_id` ِ او را حمل می‌کند ⇒ «جواب گرفت؟» یک join می‌شود نه
            # یک حدسِ زمانی. `finally` باربر است: بدونِ آن یک استثنا برچسب را
            # روی نخ جا می‌گذارد و **ارسالِ بعدی** به updateِ مرده می‌چسبد.
            self._bind_send_correlation(uid)
            try:
                self.handle_update(u)
            except Exception as exc:  # noqa: BLE001 — یک updateِ خراب حلقه را نمی‌کشد
                self._dead_letter(u, exc)   # ماندگار + هشدارِ cooldown‌دار
            finally:
                self._bind_send_correlation(None)
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
