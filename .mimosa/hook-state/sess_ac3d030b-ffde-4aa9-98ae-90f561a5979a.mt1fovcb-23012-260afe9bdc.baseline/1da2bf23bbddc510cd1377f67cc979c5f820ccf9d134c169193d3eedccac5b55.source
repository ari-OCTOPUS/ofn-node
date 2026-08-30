#!/usr/bin/env python3
"""studio_telegram.py — سطحِ تلگرامِ صبا برای Content Studio (Project-F، T-STUDIO).

باتِ جدای صبا (توکن/allowlistِ جدا از باتِ آری). content_studio را سرو می‌کند:
منو → ویوها (بریف/تقویم/ترند/PPV/آنالیز/قواعد/محدوده) + ثبتِ درفت(self-cert) + halt.

خطوطِ قرمزِ منشورِ Project-F (baked):
  - فقط متادیتا/پلن/آنالیزِ تجمیعی — این لایه هرگز رسانه/هویت/PII فن نمی‌فرستد. content_studio تضمین
    می‌کند (تست‌شده)؛ این transport هیچ‌چیزِ دیگری اضافه نمی‌کند و attachment/photo ورودی را هرگز
    پردازش/بازتاب نمی‌کند (فقط whitelistِ دستور/callback اجرا می‌شود).
  - دوکلیده: صبا ثبت → «در انتظارِ آری». این بات هرگز approve/publish نمی‌کند (انتشار درون‌پلتفرم + تأییدِ آری).
  - پرداخت فقط درون‌پلتفرم — بات هرگز مذاکرهٔ پرداخت نمی‌کند.
  - محدودهٔ صبا مقدمِ مطلق: /halt یک‌ضربه (content_studio.halt).
  - allowlist: فقط chat_idِ صبا؛ بقیه ignore. ورودیِ غیرِ whitelist = quarantine (DATA، هرگز اجرا).
  - secret-guard (I9): توکن فقط از env (TELEGRAM_SABA_BOT_TOKEN)، هرگز hardcode/log/commit؛ URL هرگز لاگ نمی‌شود.
    نبودِ توکن یا chat_id = no-opِ امن (fail-closed)، نه crash.

ایزوله: stdlib-only، $0 آفلاین، هیچ import از *_gate/chrono/money/production یا _ops.
http_get/http_post قابل‌تزریق‌اند (تست بدونِ شبکه/کلید).
"""
from __future__ import annotations

import html
import json
import os
import threading
import urllib.error
import urllib.parse
import urllib.request

from content_studio import ContentStudio   # هم‌پوشه، ایزوله

TELEGRAM_API_BASE = "https://api.telegram.org"
LONGPOLL_TIMEOUT_S = 30

# منوی §۲ → callback به ویوهای content_studio
MENU = [
    [("📋 بریف‌ها", "studio:drafts"), ("📤 ثبتِ درفت", "studio:submit")],
    [("🗓 تقویم", "studio:calendar"), ("🔎 ترند/ایده", "studio:trend")],
    [("💡 پلنِ PPV", "studio:ppv"), ("📈 آنالیز", "studio:analytics")],
    [("🔒 قواعد", "studio:rules"), ("✋ محدودهٔ من", "studio:scope")],
]
_VIEW = {"drafts": "drafts_html", "calendar": "calendar_html", "trend": "trend_feed_html",
         "ppv": "ppv_plan_html", "analytics": "analytics_html", "rules": "rules_html",
         "scope": "scope_html"}


def _env_str(name: str, default: str = "") -> str:
    v = os.environ.get(name, default)
    return v.strip() if isinstance(v, str) else default


def _env_int(name: str, default: int) -> int:
    try:
        return int(os.environ.get(name, default))
    except (TypeError, ValueError):
        return default


def _mask_token(tok: str) -> str:
    if not tok:
        return "∅"
    return (tok[:4] + "…") if len(tok) > 4 else "…"


def _url_json_get(url: str, timeout_s: float) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": "octopus-studio/0.1"})
    with urllib.request.urlopen(req, timeout=timeout_s + 5) as resp:  # noqa: S310 — only TELEGRAM_API_BASE
        return json.loads(resp.read().decode("utf-8"))


def _url_json_post(url: str, body: dict, timeout_s: float = 10.0) -> dict:
    data = json.dumps(body, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(url, data=data,
                                 headers={"User-Agent": "octopus-studio/0.1",
                                          "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout_s) as resp:  # noqa: S310 — only TELEGRAM_API_BASE
        return json.loads(resp.read().decode("utf-8"))


class StudioTelegram:
    """باتِ صبا. wired = token + saba_chat_id هر دو. content_studio را رندر و سرو می‌کند."""

    name = "studio-telegram"

    def __init__(self, studio: ContentStudio | None = None, token: str | None = None,
                 saba_chat_id: int | None = None, http_get=None, http_post=None,
                 kill_check=None, longpoll_timeout: int | None = None):
        self._studio = studio or ContentStudio()
        self._token = token if token is not None else _env_str("TELEGRAM_SABA_BOT_TOKEN")
        self._saba = int(saba_chat_id) if saba_chat_id is not None else (
            _env_int("TELEGRAM_SABA_CHAT_ID", 0) or None)
        self._http_get = http_get or _url_json_get
        self._http_post = http_post or _url_json_post
        self._kill = kill_check
        self._lp = int(longpoll_timeout if longpoll_timeout is not None else LONGPOLL_TIMEOUT_S)
        self._lk = threading.Lock()
        self._offset = 0
        self._quarantine: list[dict] = []
        self._stop = False

    @property
    def wired(self) -> bool:
        return bool(self._token) and self._saba is not None

    def __repr__(self) -> str:
        return (f"<StudioTelegram wired={self.wired} token={_mask_token(self._token)} "
                f"saba={self._saba} halted={self._studio.is_halted}>")

    def stop(self) -> None:
        self._stop = True

    def _killed(self) -> bool:
        if self._stop:
            return True
        if self._kill is not None:
            try:
                return bool(self._kill())
            except Exception:  # noqa: BLE001 — kill_checkِ خراب = امن بایست
                return True
        return False

    def _build_url(self, method: str, params: dict) -> str:
        """URLِ Telegram API. هرگز کلِ URL را لاگ نکن (token داخلش است)."""
        return f"{TELEGRAM_API_BASE}/bot{self._token}/{method}?{urllib.parse.urlencode(params)}"

    def _menu_keyboard(self) -> dict:
        return {"inline_keyboard": [
            [{"text": t, "callback_data": d} for (t, d) in row] for row in MENU]}

    def send(self, text: str, reply_markup: dict | None = None) -> bool:
        """پیامِ متنی به صبا (تنها). not wired → False. fail-soft. فقط متن/HTML — هرگز رسانه."""
        if not self.wired:
            return False
        body = {"chat_id": self._saba, "text": text, "parse_mode": "HTML"}
        if reply_markup:
            body["reply_markup"] = reply_markup
        try:
            self._http_post(self._build_url("sendMessage", {}), body)
        except Exception:  # noqa: BLE001
            return False
        return True

    # ─── routerها (whitelist؛ ورودیِ ناشناخته هرگز اجرا نمی‌شود) ───────────────────
    def handle_command(self, text: str) -> str | None:
        """دستوراتِ متنیِ صبا. فقط whitelist. خروجی = متنِ پاسخ یا None (نادیده → quarantine)."""
        t = (text or "").strip()
        if not t:
            return None
        if t in ("/start", "/menu"):
            return self._studio.main_menu()
        if t == "/halt":                       # محدودهٔ صبا مقدمِ مطلق
            return self._studio.halt()
        if t == "/stop":
            self.stop()
            return "⏹ متوقف شد."
        if t == "/drafts":
            return self._studio.drafts_html()
        if t == "/rules":
            return self._studio.rules_html()
        if t == "/scope":
            return self._studio.scope_html()
        if t.startswith("/submit"):
            return self._cmd_submit(t[len("/submit"):].strip())
        return None                            # ناشناخته → quarantine

    def dispatch_callback(self, data: str) -> str | None:
        """callback منو → ویوی content_studio. data = 'studio:<view>'. نامعتبر → None."""
        parts = str(data or "").split(":")
        if len(parts) != 2 or parts[0] != "studio":
            return None
        view = parts[1]
        if view == "submit":
            return ("📤 <b>ثبتِ درفت</b>\n──────────\n"
                    "برای ثبت: <code>/submit عنوان | faceless,feet_only,no_explicit,over_18</code>\n"
                    "<i>self-cert اجباری — رسانهٔ خام رد می‌شود.</i>")
        meth = _VIEW.get(view)
        if meth and hasattr(self._studio, meth):
            return getattr(self._studio, meth)()
        return None

    def _cmd_submit(self, arg: str) -> str:
        """پارسِ «/submit عنوان | cert1,cert2,...». self-cert اجباری، fail-closed. دوکلیده."""
        if self._studio.is_halted:
            return "✋ متوقف — محدودهٔ صبا مقدم."
        if "|" not in arg:
            return ("قالب: <code>/submit عنوان | faceless,feet_only,no_explicit,over_18</code>\n"
                    "<i>رسانهٔ خام رد می‌شود؛ فقط متادیتا.</i>")
        title, _, certs = arg.partition("|")
        cert = {c.strip(): True for c in certs.split(",") if c.strip()}
        r = self._studio.submit_draft(title.strip() or "بی‌عنوان", cert)
        if not r["ok"]:
            return f"❌ ثبت نشد: {html.escape(str(r.get('error', '')))}"
        return (f"✅ درفت ثبت شد: <code>{html.escape(r['draft_id'])}</code>\n"
                f"وضعیت: ⏳ در انتظارِ تأییدِ آری (دوکلیده).\n"
                f"<i>انتشار فقط درون‌پلتفرم، پس از تأییدِ آری.</i>")

    def poll_once(self) -> int:
        """یک دورِ long-poll. not wired/killed → 0 (no-opِ امن). allowlist=صبا؛ بقیه ignore.
        ورودیِ صبا از routerِ whitelist می‌گذرد؛ ناشناخته/رسانه → quarantine (DATA، بی‌اجرا).
        خطای شبکه fail-soft (۰، حلقه کشته نمی‌شود؛ URL/token هرگز لاگ نمی‌شود)."""
        if not self.wired or self._killed():
            return 0
        try:
            data = self._http_get(self._build_url("getUpdates",
                                  {"offset": self._offset, "timeout": self._lp}), float(self._lp))
        except Exception:  # noqa: BLE001
            return 0
        if not isinstance(data, dict) or not data.get("ok"):
            return 0
        processed = 0
        for upd in data.get("result") or []:
            uid = upd.get("update_id")
            if isinstance(uid, int) and uid + 1 > self._offset:
                self._offset = uid + 1
            is_cb = "callback_query" in upd
            msg = upd.get("message") or upd.get("callback_query", {}).get("message") or {}
            chat_id = msg.get("chat", {}).get("id")
            if chat_id != self._saba:           # allowlist: فقط صبا
                processed += 1
                continue
            resp = (self.dispatch_callback(upd.get("callback_query", {}).get("data"))
                    if is_cb else self.handle_command(msg.get("text")))
            if resp is not None:
                self.send(resp, self._menu_keyboard())
            else:                                # ناشناخته/رسانه = DATA در quarantine (بی‌اجرا)
                with self._lk:
                    self._quarantine.append({"update_id": uid,
                                             "text": str(msg.get("text") or "")[:500]})
            processed += 1
        return processed

    def run_forever(self) -> None:
        """حلقهٔ long-pollِ پس‌زمینه. not wired → فوراً برمی‌گردد. kill supreme."""
        if not self.wired:
            return
        while not self._killed():
            self.poll_once()
