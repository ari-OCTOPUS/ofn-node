#!/usr/bin/env python3
"""tg_api.py — کلاینتِ نازکِ Bot API تلگرام برای «مرکزِ تلگرام» (telegram_center).

نقش: فقط لولهٔ HTTP (stdlib/urllib) — صفر منطقِ business. الگوی approval_channel
(لایهٔ budget) بازمصرف شده: token فقط از env، هرگز hardcode/لاگ/echo؛ long-poll =
$0-idle؛ تنها میزبانِ مجاز api.telegram.org؛ هر متد دقیقاً یک تلاشِ HTTP (بدونِ
retry-storm) و fail-soft (هر خطا → پیش‌فرضِ امن: None/False/[]، هرگز crashِ صداکننده).

flag-off = no-op: بدونِ TELEGRAM_BOT_TOKEN (یا بدونِ هیچ chat id) همهٔ متدهای عمومی
no-opِ تمیزند و **صفر** تماسِ شبکه رخ می‌دهد. import-time خالص است: نه شبکه، نه
نوشتنِ دیسک، نه importِ هستهٔ ارگانیسم (opslib فقط lazy برای هشدارِ fail-soft).

تزریق‌پذیر برای تست: post_fn(url, body) / get_fn(url, timeout_s) — هم‌سان با
http_get/http_post ِ TelegramApprovalChannel، تا تست بدونِ شبکه/کلید برود.

containment: هر متنِ خروجی از scrubِ _BANNED_ECHO می‌گذرد (هیچ رشتهٔ هویتِ ممنوع
echo نمی‌شود — parity با events._scrub_str / registry_scan.scrub). نام‌های نمایشی
در زمانِ اجرا از configِ مالک می‌آیند؛ کد فقط legهای کلیدیِ بی‌محتوا می‌شناسد.

secret-guard (I9): token فقط در URL است و URL هرگز لاگ/alert نمی‌شود؛ repr و
خطاها فقط نسخهٔ mask‌شده را نشان می‌دهند.
"""
from __future__ import annotations

import html
import json
import os
import re
import time
import urllib.parse
import urllib.request

TELEGRAM_API_BASE = "https://api.telegram.org"   # تنها میزبانِ مجازِ این ماژول
DEFAULT_LONGPOLL_S = 25                          # $0-idle: getUpdates روی سرور بلوکه می‌ماند
_ALERT_THROTTLE_S = 3600                         # هشدارِ شکست: حداکثر ۱/ساعت به‌ازای هر متد
_TEXT_CAP = 4096                                 # سقفِ متنِ پیامِ تلگرام
_TOAST_CAP = 200                                 # سقفِ متنِ answerCallbackQuery
_429_MAX_SYNC_SLEEP_S = 30                        # سقفِ فقط برای sleep همگام؛ زمانِ ممنوعیتِ تلگرام cap نمی‌شود
_429_MAX_RETRIES = 1                             # فقط یک تلاشِ مجدد (هرگز retry-storm)
_FILE_MAX_BYTES = 25 * 1024 * 1024               # سقفِ دانلودِ فایلِ ورودی (۲۵MB)
_FILE_TIMEOUT_S = 30.0                           # مهلتِ دانلود (ویسِ چنددقیقه‌ای هم جا می‌شود)

# containment — تنها جای مجاز برای این رشته‌ها (parity با events/_scrub، registry_scan)
_BANNED_ECHO = ("اونلی", "onlyfans", "صبا")


# ─── env / کمکی‌های کوچک (الگوی approval_channel) ────────────────────────────
def _env_str(name: str, default: str = "") -> str:
    v = os.environ.get(name, default)
    return v.strip() if isinstance(v, str) else default


def _env_int(name: str, default: int) -> int:
    try:
        return int(os.environ.get(name, default))
    except (TypeError, ValueError):
        return default


def _coerce_id(v) -> int | None:
    """chat id → int (سوپرگروه‌ها منفی‌اند). خرابی → None (fail-soft)."""
    try:
        return int(v)
    except (TypeError, ValueError):
        return None


def _mask_token(tok: str) -> str:
    """برای repr/خطا: فقط ۴ نویسهٔ نخست + … (هرگز کلِ token)."""
    if not tok:
        return "∅"
    return (tok[:4] + "…") if len(tok) > 4 else "…"


def _scrub(text: str) -> str:
    """containment: هر رخدادِ رشتهٔ ممنوع در متنِ خروجی → ▮ (لاتین case-insensitive).
    برخلافِ events._scrub_str (که کلِ رشته را redact می‌کند)، این‌جا فقط رخدادها
    جایگزین می‌شوند تا بقیهٔ دایجستِ بی‌گناه از بین نرود."""
    v = str(text or "")
    for b in _BANNED_ECHO:
        if b.isascii():
            v = re.sub(re.escape(b), "▮", v, flags=re.IGNORECASE)
        else:
            v = v.replace(b, "▮")
    return v


def _scrub_keyboard(keyboard) -> list:
    """کیبوردِ inline را کپی + متنِ دکمه‌ها را scrub می‌کند (callback_data = legهای
    کلیدیِ بی‌محتوا، دست‌نخورده). فرمِ خراب → [] (fail-soft).

    هر دو شکل پذیرفته می‌شود: rowsِ خام (list[list[dict]]) و markupِ کاملِ
    {"inline_keyboard": rows}. پلِ دو-باتی (center._bridge_to_organism) دومی را
    مستقیم می‌دهد؛ بدونِ این باز کردن، dict به dict(char) می‌رسید، ValueError
    می‌داد و کلِ کیبورد بی‌صدا [] می‌شد (دکمه‌های رأیِ /queue،/doctor،/money حذف)."""
    if isinstance(keyboard, dict):
        keyboard = keyboard.get("inline_keyboard")
    try:
        return [[{**dict(b), "text": _scrub(str(dict(b).get("text", "")))}
                 for b in row] for row in (keyboard or [])]
    except Exception:  # noqa: BLE001
        return []


def _toast_plain(text: str) -> str:
    """answerCallbackQuery متنِ ساده است (HTML render نمی‌شود) — تگ‌ها را بردار و
    entityها را باز کن (همان الگوی TelegramApprovalChannel._toast_plain)."""
    return html.unescape(re.sub(r"<[^>]+>", "", str(text or ""))).strip()


def _send_log_record(**kw) -> None:
    """رسید در tg-send-log — lazy و fail-soft؛ خطای لاگ هرگز مسیرِ ارسال را عوض
    نمی‌کند. یک‌جا تا send و edit یک قلم بنویسند (edit تا ۰۷-۳۱ اصلاً رسید
    نداشت — ~۲۸۸ ویرایشِ بی‌رد در روز)."""
    try:
        import sys as _sys
        from pathlib import Path as _P
        _ops = str(_P(__file__).resolve().parent.parent)
        if _ops not in _sys.path:
            _sys.path.insert(0, _ops)
        import tg_send_log as _tsl  # noqa: WPS433
        _tsl.record(**kw)
    except Exception:  # noqa: BLE001
        pass


def _alert_soft(msg: str) -> None:
    """هشدارِ fail-soft و lazy به opslib.alert — importِ opslib فقط هنگامِ نیاز تا
    import-time این ماژول خالص/stdlib-only بماند. msg هرگز token/URL ندارد. شکست = سکوت."""
    try:
        import sys as _s
        from pathlib import Path as _P
        _budget = _P(__file__).resolve().parents[1] / "budget"
        if str(_budget) not in _s.path:
            _s.path.insert(0, str(_budget))
        import opslib  # lazy — هشدار هرگز مسیرِ caller را نمی‌کشد
        opslib.alert([msg])
    except Exception:  # noqa: BLE001
        pass


# ─── transportهای پیش‌فرض (stdlib-only، فقط api.telegram.org) ─────────────────
def _url_json_get(url: str, timeout_s: float) -> dict:
    """getterِ پیش‌فرض. timeout کمی بیشتر از longpoll تا پاسخِ دیررس هم خوانده شود.
    هرگز URL را لاگ نمی‌کند (token داخلش است)."""
    if not url.startswith(TELEGRAM_API_BASE + "/"):
        raise ValueError("blocked host (only api.telegram.org)")
    req = urllib.request.Request(url, headers={"User-Agent": "octopus-tg-center/0.1"})
    with urllib.request.urlopen(req, timeout=timeout_s + 5) as resp:  # noqa: S310 — only TELEGRAM_API_BASE
        return json.loads(resp.read().decode("utf-8"))


def _http_err_desc(exc) -> str:
    """descriptionِ Bot API از بدنهٔ HTTPError (مثلاً «Bad Request: message is not
    modified») — generic و بدونِ token/URL. هر شکست → '' (fail-soft)."""
    return str(_http_err_json(exc).get("description") or "")[:200]


def _http_err_json(exc) -> dict:
    """بدنهٔ JSONِ یک HTTPError (مثلاً ۴۲۹ با retry_after) — برایِ تشخیصِ rate-limit.
    هر شکست/غیر-HTTPError → {} (fail-soft). یک‌جا خوانده می‌شود تا دوبار read نشود."""
    try:
        import urllib.error
        if isinstance(exc, urllib.error.HTTPError):
            raw = exc.read(2048).decode("utf-8", "replace")
            data = json.loads(raw)
            return data if isinstance(data, dict) else {}
    except Exception:  # noqa: BLE001
        return {}
    return {}


def _retry_after_from_429(data: dict) -> float | None:
    """Extract Telegram's full ``parameters.retry_after`` prohibition.

    This value is never capped. ``_429_MAX_SYNC_SLEEP_S`` limits only how long
    this process may block synchronously; a longer prohibition must be stored
    as ``retry_not_before`` by the durable scheduler instead of retrying early.
    Invalid/missing values return None.
    """
    try:
        params = (data or {}).get("parameters") or {}
        ra = float(params.get("retry_after"))
    except (TypeError, ValueError):
        return None
    if ra <= 0:
        return None
    return ra


def _sync_retry_delay(retry_after: float | None) -> float | None:
    """Return a safe synchronous wait, or None when durable deferral is needed."""
    if retry_after is None or retry_after > _429_MAX_SYNC_SLEEP_S:
        return None
    return retry_after


def _defer_long_retry(client, method: str, retry_after: float | None) -> None:
    """Offer a long prohibition to an injected durable scheduler, fail-soft."""
    if retry_after is None or retry_after <= _429_MAX_SYNC_SLEEP_S:
        return
    try:
        client._defer(str(method), float(retry_after))
    except Exception:  # noqa: BLE001 — deferral instrumentation never breaks caller
        pass


def _url_json_post(url: str, body: dict, timeout_s: float = 10.0) -> dict:
    """posterِ پیش‌فرض (JSON body). body هرگز token ندارد (token در URL است)."""
    if not url.startswith(TELEGRAM_API_BASE + "/"):
        raise ValueError("blocked host (only api.telegram.org)")
    data = json.dumps(body, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(url, data=data,
                                 headers={"User-Agent": "octopus-tg-center/0.1",
                                          "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout_s) as resp:  # noqa: S310 — only TELEGRAM_API_BASE
        return json.loads(resp.read().decode("utf-8"))


def _url_bytes_get(url: str, timeout_s: float, max_bytes: int) -> bytes:
    """دانلودِ باینریِ فایلِ ورودی از endpointِ فایلِ تلگرام.

    ⚠️ این URL شکلِ دیگری دارد: ``/file/bot<token>/<file_path>`` — پس گاردِ
    میزبان جدا نوشته شده. هرگز URL لاگ نمی‌شود (token داخلش است).

    سقف در **لحظهٔ خواندن** اعمال می‌شود، نه فقط روی Content-Length: سروری که
    طولِ دروغ اعلام کند نباید بتواند حافظه را پر کند. یک بایت بیشتر ⇒ رد."""
    if not url.startswith(TELEGRAM_API_BASE + "/file/"):
        raise ValueError("blocked host (only api.telegram.org file endpoint)")
    cap = int(max_bytes)
    req = urllib.request.Request(url, headers={"User-Agent": "octopus-tg-center/0.1"})
    with urllib.request.urlopen(req, timeout=timeout_s) as resp:  # noqa: S310 — only TELEGRAM_API_BASE
        blob = resp.read(cap + 1)
    if len(blob) > cap:
        raise ValueError("file too large")
    return blob


# ── سلامتِ گوش: هر دورِ getUpdates ثبت می‌شود، نه فقط دورهای موفق ─────────────
# چرا (۲۰۲۶-۰۸-۰۱، صبحی که منتظرِ «سلام» مالک بودیم): مسیرِ **دریافت** تنها
# چیزی است که هیچ ردی از خودش نمی‌گذارد. ارسال رسید دارد، ۴۰۹ از ۰۷-۳۱ هشدار
# دارد — ولی هر خطای دیگری (URLError، DNS، تایم‌اوت) بی‌صدا [] می‌دهد و از
# بیرون دقیقاً شبیهِ «کسی پیام نداده» است. آن صبح دو ساعت نمی‌شد این دو را از
# هم جدا کرد، و همان لاگ نشان داد ۰۶:۴۴ یک URLError واقعاً خورده بود.
#
# فایل هرگز توکن/URL/متنِ پیام ندارد — فقط زمانِ آخرین دورِ **موفق** و شمارِ
# شکست‌های پشتِ‌سرِ هم. نوشتن بی‌قید است (درسِ «ثبت را گیت نکن، تحویل را»)؛
# فقط هشدار throttle دارد، هم‌شکلِ هشدارِ ۴۰۹ ِ پایین‌تر.
POLL_HEALTH_NAME = "poll-health.json"
POLL_DEAF_AFTER_S = 300.0        # پنجِ دقیقه شکستِ پیاپی = گوش مرده، نه نوسان


def _poll_health_path():
    """مسیرِ فایلِ سلامت، بدونِ importِ سنگین. env اول (تست‌ها ایزوله می‌شوند)."""
    from pathlib import Path as _P
    base = str(os.environ.get("OCTOPUS_STATE_DIR", "") or "").strip()
    root = _P(base) if base else (_P(__file__).resolve().parents[1] / "state")
    return root / "telegram" / POLL_HEALTH_NAME


def _record_poll(ok: bool, reason: str = "") -> dict:
    """یک دورِ poll را ثبت کن و وضعیتِ تازه را برگردان. هر خطا ⇒ سکوت
    (رصد هرگز حلقهٔ poll را نمی‌کشد)."""
    path = _poll_health_path()
    now = time.time()
    state = {"last_ok_ts": 0.0, "consecutive_failures": 0, "last_reason": ""}
    try:
        if path.exists():
            loaded = json.loads(path.read_text("utf-8"))
            if isinstance(loaded, dict):
                state.update(loaded)
    except (OSError, ValueError):
        pass
    if ok:
        state["last_ok_ts"] = now
        state["consecutive_failures"] = 0
        state["last_reason"] = ""
    else:
        state["consecutive_failures"] = int(state.get("consecutive_failures", 0)) + 1
        state["last_reason"] = str(reason or "unknown")[:80]
    state["last_round_ts"] = now
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(state, ensure_ascii=False), "utf-8")
        os.replace(tmp, path)
    except OSError:
        pass
    return state


def poll_deaf_for_s(now: "float | None" = None) -> "float | None":
    """چند ثانیه است که هیچ دورِ موفقی نداشته‌ایم؟ None = نمی‌دانیم (هنوز فایلی
    نیست) — «نمی‌دانم» هرگز «سالم» گزارش نمی‌شود."""
    try:
        state = json.loads(_poll_health_path().read_text("utf-8"))
        last = float(state.get("last_ok_ts") or 0.0)
    except (OSError, ValueError, TypeError):
        return None
    if last <= 0:
        return None
    return max(0.0, float(now if now is not None else time.time()) - last)


class TgClient:
    """کلاینتِ نازک و بی‌حالتِ Bot API. همهٔ متدهای عمومی fail-soft و flag-off-امن‌اند:
    not wired → پیش‌فرضِ امن، صفر شبکه. keyboard = list[list[{'text','callback_data'}]].
    parse_mode همیشه HTML."""

    def __init__(self, token: str | None = None, owner_chat_id=None,
                 center_chat_id=None, post_fn=None, get_fn=None,
                 download_fn=None):
        # TG_CENTER_BOT_TOKEN = باتِ اختصاصیِ مرکزِ گروه (توصیه: باتِ دوم تا با pollerِ
        # approval_channel داخلِ organism روی یک توکن جنگِ 409 نشود)؛ fallback = باتِ اصلی.
        tg_center_tok = _env_str("TG_CENTER_BOT_TOKEN")
        main_tok = _env_str("TELEGRAM_BOT_TOKEN")
        if token is not None:
            self._token = token
            self._token_source = "explicit"
        elif tg_center_tok:
            self._token = tg_center_tok
            self._token_source = "TG_CENTER_BOT_TOKEN"
        else:
            # fallback خطرناک: اگر approval_channel هم با همین توکن poll کند → 409.
            self._token = main_tok
            self._token_source = "FALLBACK_TELEGRAM_BOT_TOKEN"
            # یک بار در هر پروسه هشدار بده (نه throttle ۱/ساعت؛ چون این حالت پایدار است
            # و اپراتور باید بداند مرکز روی باتِ اصلی سوار شده). فقط وقتی واقعاً وصل است.
            if main_tok and (owner_chat_id is not None or center_chat_id is not None
                             or _env_int("TELEGRAM_OWNER_CHAT_ID", 0)
                             or _env_int("TG_CENTER_CHAT_ID", 0)):
                _alert_soft("tg-center: TG_CENTER_BOT_TOKEN غایب — fallback به "
                            "TELEGRAM_BOT_TOKEN؛ ریسکِ 409 Conflict با approval_channel.")
        self._owner = (_coerce_id(owner_chat_id) if owner_chat_id is not None
                       else (_env_int("TELEGRAM_OWNER_CHAT_ID", 0) or None))
        self._center = (_coerce_id(center_chat_id) if center_chat_id is not None
                        else (_env_int("TG_CENTER_CHAT_ID", 0) or None))
        self._post = post_fn or _url_json_post
        self._get = get_fn or _url_json_get
        # transportِ سومِ تزریق‌پذیر: (url, timeout_s, max_bytes) → bytes.
        # تست هرگز شبکه نمی‌زند؛ همین امضا در تست جعل می‌شود.
        self._download = download_fn or _url_bytes_get
        self._sleep = time.sleep                   # تزریقی برایِ تستِ ۴۲۹ بدونِ انتظارِ واقعی
        self._defer = lambda method, retry_after: None  # default-off durable scheduler hook
        self._last_alert: dict[str, float] = {}   # ضدِ اسپم: هشدارِ شکست ۱/ساعت/متد

    # ── وضعیت ────────────────────────────────────────────────────────────────
    def wired(self) -> bool:
        """لوله وصل است؟ token + دست‌کم یک chat id لازم. نبودِ هر = no-opِ امن."""
        return bool(self._token) and (self._owner is not None or self._center is not None)

    def __repr__(self) -> str:
        return (f"<TgClient wired={self.wired()} token={_mask_token(self._token)} "
                f"owner={self._owner} center={self._center}>")

    def diagnostics(self) -> dict:
        """خلاصهٔ content-free از وضعیتِ سیم‌کشی برای گزارشِ دیباگ (فاز G).

        هیچ token/URL/chat-id حساس برگردانده نمی‌شود — فقط presence/mask/source.
        مصرف‌کننده: TG-LIVE-DEBUG-REPORT.md generator."""
        return {
            "wired": self.wired(),
            "token_present": bool(self._token),
            "token_mask": _mask_token(self._token),
            "token_source": getattr(self, "_token_source", "unknown"),
            "owner_configured": self._owner is not None,
            "center_configured": self._center is not None,
            "is_forum_center": isinstance(self._center, int) and self._center < -1000,
        }

    # ── allowlist (قانونِ P3 §5: فقط مالک فرمان/کلیک می‌دهد) ──────────────────
    # ── دو خواندنیِ عمومی (۲۰۲۶-۰۷-۳۰) ──────────────────────────────────
    # `surface_router._chat_for` از روزِ اول `getattr(client, "owner_chat_id")`
    # و `center_chat_id` را می‌خواند، ولی این کلاس فقط `_owner`/`_center` ِ
    # خصوصی داشت — یعنی `getattr` همیشه `None` برمی‌گرداند و مسیرِ `dm`
    # **بی‌صدا** بی‌مقصد می‌شد. تستِ آن ماژول این را نگرفت چون کلاینتِ ساختگیِ
    # تست این دو صفت را دارد: فیکی که تابعِ واقعی را دور می‌زند.
    #
    # ⚠️ این باگ از قبل بود، ولی تغییرِ امروزِ من (ابهام → DM به‌جای گروه)
    # دامنه‌اش را از «فقط dm» به «هر جریانِ مبهم» گسترش می‌داد. پس قرارداد
    # واقعی می‌شود، نه اینکه صداکننده به مسیرِ خصوصی دست ببرد.
    @property
    def owner_chat_id(self):
        return self._owner

    @property
    def center_chat_id(self):
        return self._center

    def is_owner(self, update) -> bool:
        """آیا این update از خودِ مالک است؟ منبعِ حقیقت = from.id (نه chat.id، چون در
        سوپرگروهِ مرکز chat.id ≠ مالک). مالکِ پیکربندی‌نشده → False (fail-closed)."""
        if self._owner is None:
            return False
        try:
            u = update or {}
            frm = ((u.get("message") or {}).get("from")
                   or (u.get("callback_query") or {}).get("from")
                   or (u.get("edited_message") or {}).get("from") or {})
            return int(frm.get("id")) == int(self._owner)
        except (TypeError, ValueError, AttributeError):
            return False

    # ── هستهٔ HTTP (یک تلاش، fail-soft، بدونِ leakِ URL/token) ────────────────
    def _build_url(self, method: str, params: dict | None = None) -> str:
        """ساختِ URLِ Bot API. هرگز کلِ URL را لاگ نکن (token داخلش است)."""
        url = f"{TELEGRAM_API_BASE}/bot{self._token}/{method}"
        if params:
            url += "?" + urllib.parse.urlencode(params)
        return url

    def _call_post(self, method: str, body: dict) -> dict | None:
        """یک POST؛ خطا/پاسخِ نامعتبر → None. هشدارِ شکست throttled و بدونِ token.

        استثنا: «message is not modified» = وضعِ مطلوب از قبل برقرار → موفق، بی‌هشدار
        (وگرنه هر بوت یک ⚠️ کاذب در /alerts می‌نشیند و کانال بی‌اعتبار می‌شود).

        ۴۲۹ Too Many Requests: تلگرام ``parameters.retry_after`` می‌گوید. ما تا سقفِ
        امن صبر می‌کنیم و **یک‌بار** دوباره تلاش می‌کنیم (آیتم ۵ِ TG-P2). هیچ‌گاه
        retry-storm درست نمی‌شود؛ شکستِ دوم = fail-soft مثلِ بقیه."""
        # DA-4-P1 (PHASE02 2026-08-16): ناظرِ سایهٔ PEP — فقط ثبت، صفر تغییر رفتار.
        try:
            import budget.telegram_pep_shadow as _pep  # noqa: WPS433
            _pep.hook(sender="tg_api._call_post", action=method, params=body)
        except Exception:  # noqa: BLE001
            pass
        for _attempt in range(_429_MAX_RETRIES + 1):   # ۱ تلاشِ اولیه + ۱ retry
            try:
                data = self._post(self._build_url(method), body)
            except Exception as e:  # noqa: BLE001 — fail-soft، بدونِ leakِ URL/token
                # بدنهٔ HTTPError یک stream است و فقط یک‌بار خوانده می‌شود؛ پس JSON را
                # یک‌بار بیرون بکش و هر دو (retry_after + description) را از آن بگیر.
                err_json = _http_err_json(e)
                ra = _retry_after_from_429(err_json)
                desc = str(err_json.get("description") or "")[:200]
                if "message is not modified" in desc:
                    return {"ok": True, "result": True, "not_modified": True}
                _sync = _sync_retry_delay(ra)
                if _sync is not None and _attempt < _429_MAX_RETRIES:
                    try:
                        self._sleep(_sync)
                    except Exception:  # noqa: BLE001
                        pass
                    continue
                # long prohibition (or none): do not retry early — fail-soft so
                # the durable scheduler owns retry_not_before.
                _defer_long_retry(self, method, ra)
                self._note_fail(method, e, desc)
                return None
            if not isinstance(data, dict):
                return None
            if data.get("ok"):
                return data
            # پاسخِ ok=False: اگر ۴۲۹ است و retry_after ِ کوتاه دارد، یک‌بار دوباره.
            ra = _retry_after_from_429(data) if int(data.get("error_code") or 0) == 429 else None
            _sync = _sync_retry_delay(ra)
            if _sync is not None and _attempt < _429_MAX_RETRIES:
                try:
                    self._sleep(_sync)
                except Exception:  # noqa: BLE001
                    pass
                continue
            _defer_long_retry(self, method, ra)
            return None
        return None

    def _note_fail(self, method: str, exc: Exception, desc: str = "") -> None:
        """هشدارِ fail-softِ throttled (۱/ساعت/متد) — نامِ متد + نوعِ خطا + descriptionِ
        کوتاهِ Bot API (generic و بدونِ token/URL/پیام — عیب‌یابیِ آینده)."""
        now = time.time()
        if now - self._last_alert.get(method, 0.0) < _ALERT_THROTTLE_S:
            return
        self._last_alert[method] = now
        extra = f" ({desc[:80]})" if desc else ""
        _alert_soft(f"tg_api {method} failed: {type(exc).__name__}{extra}")

    def _resolve_chat(self, chat_id) -> int | None:
        """chatِ مقصد: صریح > مرکز > مالک. نامعتبر → None (fail-soft)."""
        if chat_id is not None:
            return _coerce_id(chat_id)
        return self._center if self._center is not None else self._owner

    def _bot_role(self) -> str | None:
        """outer|inner|None برای رسیدِ ارسال (منشور UX-8) — از منبعِ token.

        توکنِ صریح (مرکز کلاینتِ inner را با توکنِ صریح می‌سازد) با env مقایسه
        می‌شود؛ خودِ token هرگز لاگ/برگردانده نمی‌شود — فقط نقش."""
        src = getattr(self, "_token_source", "")
        if src == "TG_CENTER_BOT_TOKEN":
            return "outer"
        if src == "FALLBACK_TELEGRAM_BOT_TOKEN":
            return "inner"
        tok = self._token or ""
        if tok:
            if tok == _env_str("TG_CENTER_BOT_TOKEN"):
                return "outer"
            if tok == _env_str("TELEGRAM_BOT_TOKEN"):
                return "inner"
        return None

    def _surface_of(self, cid) -> str | None:
        """dm|group|None برای رسید: DM ِ مالک وقتی chat همان مالک است؛
        group وقتی chat یک گروه/سوپرگروه است (id منفی)."""
        if self._owner is not None and cid == self._owner:
            return "dm"
        if isinstance(cid, int) and cid < 0:
            return "group"
        return None

    # ── متدهای عمومی (قراردادِ telegram_center) ───────────────────────────────
    def send(self, text: str, *, topic_id=None, keyboard=None,
             chat_id=None, pin: bool = False, stream: str = "center") -> int | None:
        """sendMessage (HTML). خروجی = message_id یا None. topic_id → message_thread_id
        (تاپیکِ سوپرگروه). pin=True → بعد از ارسالِ موفق، pin هم می‌شود (شکستِ pin
        ارسال را باطل نمی‌کند). not wired / متنِ خالی / chatِ نامعتبر → None، صفر شبکه.

        `stream` (۰۷-۳۰): برچسبِ رسید در tg-send-log. پیش‌فرض همان «center» ِ
        همیشگی — صداکنندهٔ قدیمی هیچ تغییری نمی‌بیند؛ ولی مسیرِ `_route_send`
        نامِ دقیق (center-digest/…) می‌دهد تا رسیدها قابلِ‌پروب باشند."""
        # ADR-042 Phase 0: record call site (not outcome). Fail-soft; no return change.
        try:
            import sys as _sys_fire
            from pathlib import Path as _P_fire
            _ops_fire = str(_P_fire(__file__).resolve().parent.parent)
            if _ops_fire not in _sys_fire.path:
                _sys_fire.path.insert(0, _ops_fire)
            import tg_site_fire_log as _fire  # noqa: WPS433
            _fire.record_call(sender="tg_api.send")
        except Exception:  # noqa: BLE001
            pass
        if not self.wired():
            return None
        cid = self._resolve_chat(chat_id)
        body_text = _scrub(text)[:_TEXT_CAP]
        if cid is None or not body_text.strip():
            return None
        body: dict = {"chat_id": cid, "text": body_text, "parse_mode": "HTML"}
        # message_thread_id فقط روی سوپرگروهِ forum معنا دارد (cid < -1000). فرستادنش
        # به یک چتِ خصوصی (DM، cid ≥ ۰) = ۴۰۰ Bad Request از تلگرام (آیتم ۳ِ TG-P2).
        # حتی اگر صداکننده اشتباهاً topic_id بدهد، اینجا بی‌اثر می‌شود.
        if topic_id is not None and isinstance(cid, int) and cid < -1000:
            tid = _coerce_id(topic_id)
            if tid is not None:
                body["message_thread_id"] = tid
        if keyboard:
            body["reply_markup"] = {"inline_keyboard": _scrub_keyboard(keyboard)}
        delivery = None
        _durable = None
        try:
            import durable_loop as _durable  # noqa: WPS433
        except Exception:  # noqa: BLE001 — boundary absent → legacy direct send
            _durable = None
        if _durable is not None:
            try:
                if _durable.enabled() and _durable.current_context() is not None:
                    delivery = _durable.deliver(
                        text=body_text, chat_id=cid,
                        topic_id=body.get("message_thread_id"),
                        stream=str(stream or "center"),
                        send_fn=lambda: self._call_post("sendMessage", body),
                    )
            except Exception:  # noqa: BLE001 — mid-delivery error fails closed
                delivery = {"managed": True, "ok": False, "message_id": None,
                            "state": "DURABILITY_ERROR"}
        if isinstance(delivery, dict) and delivery.get("managed"):
            data = ({"ok": True, "result": {"message_id": delivery.get("message_id")}}
                    if delivery.get("ok") else None)
        else:
            data = self._call_post("sendMessage", body)
        # سنجشِ حجم/تکرار — همان لاگی که approval_channel می‌نویسد. بدونِ این خط،
        # کلِ ارسال‌های باتِ مرکز (پاسخِ دستورها، دایجستِ تاپیک‌ها، کارتِ تصمیم)
        # از شمارش بیرون می‌ماند و «تکرار صفر است» یک ادعای نیم‌بند می‌شود.
        # فقط hashِ متن ثبت می‌شود، نه متن. خطای لاگ هرگز ارسال را عوض نمی‌کند.
        # bot_role از token_source می‌آید نه هاردکدِ "outer" — کلاینتِ inner ِ
        # داخلِ مرکز هم از همین کلاس است؛ هاردکد یعنی رسیدِ دروغ برای آن نمونه.
        # شکستِ شبکه state="sent" + ok=False است، نه "blocked" (blocked = ردِ سیاست).
        _send_log_record(chat_id=cid, topic_id=body.get("message_thread_id"),
                         text=body_text, stream=str(stream or "center"),
                         ok=data is not None, disposition="attempted",
                         bot_role=self._bot_role(), surface=self._surface_of(cid))
        if data is None:
            return None
        mid = _coerce_id((data.get("result") or {}).get("message_id"))
        if mid is not None and pin:
            self.pin_message(mid, chat_id=cid)   # fail-soft: pin نشد → پیام سرِ جایش است
        return mid

    def edit(self, message_id, text: str, keyboard=None, chat_id=None) -> bool:
        """editMessageText (HTML). خروجی = موفق شد؟ not wired/نامعتبر → False، صفر شبکه."""
        if not self.wired():
            return False
        cid = self._resolve_chat(chat_id)
        mid = _coerce_id(message_id)
        body_text = _scrub(text)[:_TEXT_CAP]
        if cid is None or mid is None or not body_text.strip():
            return False
        body: dict = {"chat_id": cid, "message_id": mid,
                      "text": body_text, "parse_mode": "HTML"}
        if keyboard:
            body["reply_markup"] = {"inline_keyboard": _scrub_keyboard(keyboard)}
        ok = self._call_post("editMessageText", body) is not None
        # رسیدِ edit (اسکن A T-8، ۰۷-۳۱): کارتِ pin شده و کارتِ پاها با edit تازه
        # می‌شوند — ~۲۸۸ ویرایش/روز که تا امروز در هیچ لاگی نبود؛ حالا هر edit
        # یک ردیفِ attempted با stream="edit" می‌گذارد.
        _send_log_record(chat_id=cid, topic_id=None, text=body_text,
                         stream="edit", ok=ok, disposition="attempted",
                         bot_role=self._bot_role(), surface=self._surface_of(cid))
        return ok

    def delete(self, message_id, chat_id=None) -> bool:
        """deleteMessage. خروجی = موفق شد؟ not wired/نامعتبر → False، صفر شبکه.

        تلگرام حذفِ پیام‌های >۴۸ساعته را رد می‌کند (fail-soft، نه استثنا) —
        صداکننده باید این را «حذف نشد، مهم نیست» بخواند، نه خطا."""
        if not self.wired():
            return False
        cid = self._resolve_chat(chat_id)
        mid = _coerce_id(message_id)
        if cid is None or mid is None:
            return False
        return self._call_post("deleteMessage", {"chat_id": cid, "message_id": mid}) is not None

    def pin_message(self, message_id, chat_id=None) -> bool:
        """pinChatMessage (بی‌صدا — بدونِ نوتیفِ اضافه). not wired/نامعتبر → False."""
        if not self.wired():
            return False
        cid = self._resolve_chat(chat_id)
        mid = _coerce_id(message_id)
        if cid is None or mid is None:
            return False
        return self._call_post("pinChatMessage",
                               {"chat_id": cid, "message_id": mid,
                                "disable_notification": True}) is not None

    def delete_message(self, message_id, chat_id=None) -> bool:
        """deleteMessage. پیامِ خودِ ربات (یا reply-to-own) را حذف می‌کند.
        Bot API تلگرام فقط پیام‌های اخیر (<48h برای دیگران، نامحدود برای رباتِ خود)
        را حذف می‌کند. not wired/نامعتبر → False."""
        if not self.wired():
            return False
        cid = self._resolve_chat(chat_id)
        mid = _coerce_id(message_id)
        if cid is None or mid is None:
            return False
        return self._call_post("deleteMessage",
                               {"chat_id": cid, "message_id": mid}) is not None

    def create_topic(self, name: str, chat_id=None) -> int | None:
        """createForumTopic در سوپرگروهِ مرکز. خروجی = message_thread_id یا None."""
        if not self.wired():
            return None
        cid = self._resolve_chat(chat_id)
        topic_name = _scrub(name)[:128].strip()
        if cid is None or not topic_name:
            return None
        data = self._call_post("createForumTopic",
                               {"chat_id": cid, "name": topic_name})
        if data is None:
            return None
        return _coerce_id((data.get("result") or {}).get("message_thread_id"))

    def edit_topic(self, topic_id, name: str, chat_id=None) -> bool:
        """editForumTopic — نامِ یک تاپیکِ موجود را عوض می‌کند (رأیِ مالک، ۲۰۲۶-۰۷-۲۶).

        `create_topic` فقط تاپیکِ نبوده را می‌سازد، پس بدونِ این متد تغییرِ
        `display_names` در config هرگز روی تاپیک‌های ساخته‌شده دیده نمی‌شد —
        یعنی config یک‌چیز می‌گفت و سایدبارِ تلگرام چیزِ دیگر: باز هم دو حقیقت.
        not wired / نامِ خالی / id نامعتبر → False، صفر شبکه."""
        if not self.wired():
            return False
        cid = self._resolve_chat(chat_id)
        tid = _coerce_id(topic_id)
        nm = _scrub(name)[:128].strip()
        if cid is None or tid is None or not nm:
            return False
        data = self._call_post("editForumTopic",
                               {"chat_id": cid, "message_thread_id": tid, "name": nm})
        return bool(data)

    def set_commands(self, commands, *, scope: dict | None = None) -> bool:
        """setMyCommands از list[tuple[str, str]] = (command, description).
        فرمِ خراب/لیستِ خالی → False، صفر شبکه.

        `scope` (منشور UX-5، ۰۷-۳۱): dict ِ BotCommandScope تلگرام (مثلاً
        {"type": "all_private_chats"}) — منوی گروه ≠ منوی DM. None = رفتارِ
        قبلی بایت‌به‌بایت (scope ِ پیش‌فرضِ تلگرام)."""
        if not self.wired():
            return False
        cmds: list[dict] = []
        try:
            for c, d in list(commands or []):
                cmd = str(c).strip().lstrip("/")[:32]
                if cmd:
                    cmds.append({"command": cmd, "description": _scrub(d)[:256]})
        except (TypeError, ValueError):
            return False
        if not cmds:
            return False
        body: dict = {"commands": cmds}
        if scope is not None:
            body["scope"] = scope
        return self._call_post("setMyCommands", body) is not None

    def delete_commands(self, *, scope: dict | None = None) -> bool:
        """deleteMyCommands — پاک‌کردنِ منوی یک scope (یا پیش‌فرض).

        لازمهٔ منوی scope-دار: بدونِ حذفِ scope ِ قدیمی، منوی کهنه در کشِ
        تلگرام می‌ماند و دو حقیقت ساخته می‌شود. not wired → False، صفر شبکه."""
        if not self.wired():
            return False
        body: dict = {}
        if scope is not None:
            body["scope"] = scope
        return self._call_post("deleteMyCommands", body) is not None

    def poll_updates(self, offset: int = 0, timeout_s: int = DEFAULT_LONGPOLL_S) -> list[dict]:
        """یک دورِ long-pollِ getUpdates ($0-idle). خروجی = لیستِ updateها (dict) —
        خطای شبکه/پاسخِ بد → [] بی‌صدا (حلقهٔ poll نباید alert-spam کند؛ الگوی
        approval_channel.poll_once). offsetِ بعدی با next_offset حساب می‌شود.

        ۴۲۹: اگر تلگرام rate-limit بگوید (retry_after)، قبل از برگشتنِ [] به‌اندازهٔ
        آن صبر می‌کنیم تا حلقهٔ poll بلافاصله دوباره برخورد نکند و spinِ ۴۲۹ نسازد.
        sleep واقعی فقط در تولید است؛ تست با ``_sleep`` تزریقی ثبت می‌کند."""
        if not self.wired():
            return []
        try:
            params = {"offset": int(offset), "timeout": int(timeout_s),
                      "allowed_updates": json.dumps(["message", "callback_query"])}
            data = self._get(self._build_url("getUpdates", params), float(timeout_s))
        except Exception as e:  # noqa: BLE001 — بی‌صدا، بدونِ leakِ URL/token
            st = _record_poll(False, type(e).__name__)
            self._maybe_alert_deaf(st)
            return []
        if not isinstance(data, dict) or not data.get("ok"):
            _code = data.get("error_code") if isinstance(data, dict) else "no-dict"
            self._maybe_alert_deaf(_record_poll(False, "api:%s" % (_code,)))
            ra = _retry_after_from_429(data if isinstance(data, dict) else {})
            _sync = _sync_retry_delay(ra)
            if _sync is not None:
                try:
                    self._sleep(_sync)
                except Exception:  # noqa: BLE001
                    pass
            # (۲۰۲۶-۰۷-۳۱، رفعِ boundary-12) — تشخیصِ pollerِ رقیب: 409 Conflict
            # یعنی مصرف‌کنندهٔ دیگری روی همین توکن getUpdates می‌زند (کنترل‌مغزِ
            # قدیمی، دستگاهِ دیگر، یا وب‌هوک) و آپدیت‌ها را می‌بلعد. تا امروز این
            # مسیر بی‌صدا [] برمی‌گرداند — تنها نشانه، یک «غیبت» بود (بات ساکت،
            # صفر لاگ، صفر رسید). الگوی approval_channel.poll_once (جلسه ۴۶) اینجا
            # آورده شد: هشدارِ throttled (۱/ساعت) تا spam نکند.
            if isinstance(data, dict) and data.get("error_code") == 409:
                import time as _t409
                if _t409.time() - getattr(self, "_last_409_alert", 0.0) > 3600:
                    self._last_409_alert = _t409.time()
                    _alert_soft("tg-center getUpdates 409 Conflict — pollerِ رقیب روی "
                                "همین توکن! آپدیت‌ها را او می‌بلعد (پروسهٔ دوم؟ "
                                "وب‌هوک؟). تا حل نشود بات ساکت خواهد بود.")
            return []
        _record_poll(True)
        return [u for u in (data.get("result") or []) if isinstance(u, dict)]

    def _maybe_alert_deaf(self, state: dict) -> None:
        """گوشِ مرده را یک‌بار در ساعت فریاد بزن. «مرده» = هیچ دورِ موفقی در
        POLL_DEAF_AFTER_S، نه یک شکستِ تکی (شبکه تک‌وتوک می‌لرزد و هشدارِ
        گرگ‌گرگ بدتر از سکوت است)."""
        try:
            last_ok = float((state or {}).get("last_ok_ts") or 0.0)
            fails = int((state or {}).get("consecutive_failures") or 0)
        except (TypeError, ValueError):
            return
        if fails < 2 or last_ok <= 0:
            return
        quiet_s = time.time() - last_ok
        if quiet_s < POLL_DEAF_AFTER_S:
            return
        if time.time() - getattr(self, "_last_deaf_alert", 0.0) <= 3600:
            return
        self._last_deaf_alert = time.time()
        _alert_soft("tg-center getUpdates: %.0f دقیقه هیچ دورِ موفقی نبوده "
                    "(%d شکستِ پیاپی، آخرین دلیل: %s). ارسال ممکن است سالم "
                    "به‌نظر برسد ولی بات پیام‌های مالک را **نمی‌شنود**."
                    % (quiet_s / 60.0, fails,
                       str((state or {}).get("last_reason") or "?")))

    @staticmethod
    def next_offset(updates, current: int = 0) -> int:
        """ریاضیِ offsetِ getUpdates: بیشینهٔ update_id + 1 (وگرنه همان current).
        همان قاعدهٔ TelegramApprovalChannel.poll_once — caller بینِ pollها نگه می‌دارد."""
        try:
            off = int(current or 0)
        except (TypeError, ValueError):
            off = 0
        for u in updates or []:
            try:
                uid = int((u or {}).get("update_id"))
            except (TypeError, ValueError, AttributeError):
                continue
            if uid + 1 > off:
                off = uid + 1
        return off

    # ── فایلِ ورودی (getFile + دانلود) — لِینِ ویس، منشور رأی ۹ ────────────────
    # این دو متد **ورودی**اند: هیچ رسیدِ ارسال نمی‌نویسند (tg-send-log فقط
    # خروجی را می‌شمارد؛ یک ردیفِ attempted برایِ یک دانلود = آلوده‌کردنِ سنجهٔ
    # «چقدر حرف زدیم»). همان discipline بقیه: fail-soft، ۴۲۹-aware، بی‌leakِ URL.
    def _build_file_url(self, file_path: str) -> str:
        """URLِ endpointِ فایل: ``/file/bot<token>/<file_path>``. هرگز لاگ نشود."""
        safe = urllib.parse.quote(str(file_path or ""), safe="/")
        return f"{TELEGRAM_API_BASE}/file/bot{self._token}/{safe}"

    def get_file(self, file_id) -> dict | None:
        """getFile → dictِ resultِ تلگرام ({file_path, file_size, …}) یا None.

        سقفِ ۲۵MB همین‌جا هم سنجیده می‌شود: وقتی تلگرام `file_size` می‌دهد،
        دانلودِ فایلِ بزرگ اصلاً شروع نمی‌شود (رد کردن **قبل از** مصرفِ پهنای
        باند). نبودِ file_size ⇒ سقف در خودِ دانلود اعمال می‌شود."""
        if not self.wired():
            return None
        fid = str(file_id or "").strip()
        if not fid:
            return None
        data = self._call_post("getFile", {"file_id": fid})
        if data is None:
            return None
        res = data.get("result")
        if not isinstance(res, dict) or not str(res.get("file_path") or "").strip():
            return None
        try:
            size = int(res.get("file_size"))
        except (TypeError, ValueError):
            size = None
        if size is not None and size > _FILE_MAX_BYTES:
            self._note_fail("getFile", ValueError("file too large"),
                            f"{size} > {_FILE_MAX_BYTES} bytes")
            return None
        return res

    def download_file(self, file_path: str, dest: str) -> bool:
        """فایلِ تلگرام → مسیرِ محلیِ `dest`. موفق؟ not wired/نامعتبر → False.

        نوشتن atomic است (tmp + os.replace) تا مصرف‌کننده هرگز فایلِ نیم‌کاره
        نبیند. `file_path` از خودِ تلگرام می‌آید ولی باز هم سنجیده می‌شود:
        مسیرِ مطلق یا `..` رد می‌شود (اعتماد به ورودیِ بیرونی = رد شدنِ گارد)."""
        if not self.wired():
            return False
        fp = str(file_path or "").strip().replace("\\", "/")
        dst = str(dest or "").strip()
        if not fp or not dst:
            return False
        if fp.startswith("/") or ".." in fp.split("/") or ":" in fp.split("/")[0]:
            return False
        url = self._build_file_url(fp)
        blob = None
        for _attempt in range(_429_MAX_RETRIES + 1):
            try:
                blob = self._download(url, _FILE_TIMEOUT_S, _FILE_MAX_BYTES)
            except Exception as e:  # noqa: BLE001 — fail-soft، بدونِ leakِ URL/token
                err_json = _http_err_json(e)
                ra = _retry_after_from_429(err_json)
                _sync = _sync_retry_delay(ra)
                if _sync is not None and _attempt < _429_MAX_RETRIES:
                    try:
                        self._sleep(_sync)
                    except Exception:  # noqa: BLE001
                        pass
                    continue
                self._note_fail("getFileDownload", e,
                                str(err_json.get("description") or "")[:200])
                return False
            break
        if not isinstance(blob, (bytes, bytearray)) or not blob:
            return False
        if len(blob) > _FILE_MAX_BYTES:      # transportِ تزریقی هم باید سقف بخورد
            self._note_fail("getFileDownload", ValueError("file too large"),
                            f"{len(blob)} > {_FILE_MAX_BYTES} bytes")
            return False
        try:
            parent = os.path.dirname(os.path.abspath(dst))
            if parent:
                os.makedirs(parent, exist_ok=True)
            tmp = dst + ".part"
            with open(tmp, "wb") as fh:
                fh.write(blob)
            os.replace(tmp, dst)
        except OSError as e:
            self._note_fail("getFileDownload", e, "write failed")
            return False
        return True

    def fetch_file(self, file_id, dest: str) -> bool:
        """getFile + دانلود در یک قدم — تا سیم‌کشیِ صداکننده یک خط بماند.
        هر شکستِ میانی → False (بدونِ استثنا، بدونِ فایلِ نیم‌کاره)."""
        info = self.get_file(file_id)
        if not info:
            return False
        return self.download_file(str(info.get("file_path") or ""), dest)

    def answer_callback(self, callback_id, text: str = "") -> bool:
        """answerCallbackQuery — بستنِ spinnerِ دکمه. متنِ toast ساده است (HTML render
        نمی‌شود) → strip تگ + unescape (باگِ toastِ جلسه ۴۶ تکرار نشود)."""
        if not self.wired() or not callback_id:
            return False
        return self._call_post(
            "answerCallbackQuery",
            {"callback_query_id": str(callback_id),
             "text": _toast_plain(_scrub(text))[:_TOAST_CAP],
             "cache_time": 0}) is not None
