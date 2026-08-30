#!/usr/bin/env python3
"""studio_telegram_v3.py — تلگرامِ صبا (نسخه‌ی عمیق).

منوی کاملِ صفحات + callback + inline keyboard + rich HTML + config-driven.
۳ سطح: منوی اصلی → زیرمنو → اقدام. همه human-gated.
ایزوله: stdlib-only، $0، صفر رسانه/PII.
"""
from __future__ import annotations
import html
import json
import os
import threading
import urllib.error, urllib.parse, urllib.request
from pathlib import Path
from content_studio import ContentStudio, COMPLIANCE_CHECKS

TELEGRAM_API_BASE = "https://api.telegram.org"

# ─── منوی اصلی (۳ سطح) ────────────────────────────────────────────────────────
MAIN_MENU = {"inline_keyboard": [
    [{"text": "📋 بریف‌ها", "callback_data": "m:drafts"},
     {"text": "📤 ثبتِ درفت", "callback_data": "m:submit"}],
    [{"text": "🗓 تقویم", "callback_data": "m:calendar"},
     {"text": "🔎 ترند/ایده", "callback_data": "m:trend"}],
    [{"text": "💡 پلنِ PPV", "callback_data": "m:ppv"},
     {"text": "📈 آنالیز", "callback_data": "m:analytics"}],
    [{"text": "🔒 قواعد", "callback_data": "m:rules"},
     {"text": "✋ محدودهٔ من", "callback_data": "m:scope"}],
    [{"text": "🧠 بریفِ هفته (AI)", "callback_data": "m:brief"}],
]}

# زیرمنو برای بازگشت
BACK_KB = {"inline_keyboard": [[{"text": "↩️ بازگشت", "callback_data": "m:menu"}]]}

_VIEW_MAP = {
    "drafts": "drafts_html", "calendar": "calendar_html",
    "trend": "trend_feed_html", "ppv": "ppv_plan_html",
    "analytics": "analytics_html", "rules": "rules_html", "scope": "scope_html",
}


def _env_str(n, d=""): v=os.environ.get(n,d); return v.strip() if isinstance(v,str) else d
def _env_int(n, d=0):
    try: return int(os.environ.get(n,d))
    except: return d
def _mask(t): return (t[:4]+"…") if t and len(t)>4 else "∅" if not t else "…"
def _url_get(url, timeout):
    req = urllib.request.Request(url, headers={"User-Agent":"octopus-studio/0.1"})
    with urllib.request.urlopen(req, timeout=timeout+5) as r: return json.loads(r.read().decode())
def _url_post(url, body, timeout=10):
    d = json.dumps(body, ensure_ascii=False).encode()
    req = urllib.request.Request(url, data=d, headers={"User-Agent":"octopus-studio/0.1","Content-Type":"application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r: return json.loads(r.read().decode())


class StudioTelegramV3:
    """باتِ صبا v3 — منوی کاملِ صفحات + AI brief. ایزوله."""

    name = "studio-telegram-v3"

    def __init__(self, studio=None, token=None, saba_chat_id=None,
                 http_get=None, http_post=None, kill_check=None,
                 brain=None, longpoll_timeout=30):
        self._studio = studio or ContentStudio()
        self._token = token or _env_str("TELEGRAM_SABA_BOT_TOKEN")
        self._saba = int(saba_chat_id) if saba_chat_id is not None else (_env_int("TELEGRAM_SABA_CHAT_ID",0) or None)
        self._http_get = http_get or _url_get
        self._http_post = http_post or _url_post
        self._kill = kill_check
        self._brain = brain  # DualBrainV3 (optional)
        self._lp = longpoll_timeout
        self._lk = threading.Lock()
        self._offset = 0
        self._quarantine: list[dict] = []
        self._stop = False

    @property
    def wired(self): return bool(self._token) and self._saba is not None
    def __repr__(self): return f"<StudioV3 wired={self.wired} token={_mask(self._token)} saba={self._saba} halted={self._studio.is_halted}>"
    def stop(self): self._stop = True
    def _killed(self):
        if self._stop: return True
        if self._kill:
            try: return bool(self._kill())
            except: return True
        return False
    def _build_url(self, method, params):
        return f"{TELEGRAM_API_BASE}/bot{self._token}/{method}?{urllib.parse.urlencode(params)}"

    def send(self, text, reply_markup=None):
        if not self.wired: return False
        body = {"chat_id": self._saba, "text": text, "parse_mode": "HTML"}
        if reply_markup: body["reply_markup"] = reply_markup
        try: self._http_post(self._build_url("sendMessage", {}), body)
        except: return False
        return True

    # ─── دستوراتِ متنی ──────────────────────────────────────────────────────────
    def handle_command(self, text: str) -> str | None:
        t = (text or "").strip()
        if not t: return None
        if t in ("/start", "/menu"): return self._render("menu")
        if t == "/halt": return self._studio.halt()
        if t == "/stop": self.stop(); return "⏹ متوقف شد."
        if t == "/drafts": return self._studio.drafts_html()
        if t == "/rules": return self._studio.rules_html()
        if t == "/scope": return self._studio.scope_html()
        if t.startswith("/submit"): return self._cmd_submit(t[len("/submit"):].strip())
        if t == "/brief" and self._brain: return self._ai_brief()
        return None  # ناشناخته → quarantine

    def dispatch_callback(self, data: str) -> tuple[str | None, dict | None]:
        """callback → (text, keyboard). نامعتبر → (None, None)."""
        parts = str(data or "").split(":")
        if len(parts) < 2 or parts[0] != "m": return None, None
        view = parts[1]
        if view == "menu": return self._render("menu"), MAIN_MENU
        if view == "submit":
            return ("📤 <b>ثبتِ درفت</b>\n──────────\n"
                    "قالب: <code>/submit عنوان | faceless,feet_only,no_explicit,over_18</code>\n"
                    "<i>رسانهٔ خام رد می‌شود؛ فقط متادیتا.</i>"), BACK_KB
        if view == "brief" and self._brain:
            return self._ai_brief(), BACK_KB
        meth = _VIEW_MAP.get(view)
        if meth and hasattr(self._studio, meth):
            return getattr(self._studio, meth)(), BACK_KB
        return None, None

    def _render(self, view: str) -> str:
        if view == "menu":
            if self._studio.is_halted: return self._studio.halt()
            n = self._studio.draft_count
            return ("🎬 <b>استودیوی محتوا</b> — Project-F\n"
                    f"📋 درفت‌ها: {n}\n<i>یک گزینه را انتخاب کن.</i>")
        return None

    def _cmd_submit(self, arg: str) -> str:
        if self._studio.is_halted: return "✋ متوقف — محدودهٔ صبا مقدم."
        if "|" not in arg:
            return ("قالب: <code>/submit عنوان | faceless,feet_only,no_explicit,over_18</code>")
        title, _, certs = arg.partition("|")
        cert = {c.strip(): True for c in certs.split(",") if c.strip()}
        r = self._studio.submit_draft(title.strip() or "بی‌عنوان", cert)
        if not r["ok"]: return f"❌ {html.escape(str(r.get('error','')))}"
        return (f"✅ ثبت شد: <code>{html.escape(r['draft_id'])}</code>\n"
                f"⏳ در انتظارِ تأییدِ آری (دوکلیده).")

    def _ai_brief(self) -> str:
        """بریفِ هفته از DualBrain (اگر brain وصل باشد)."""
        if not self._brain:
            return "🧠 <b>بریفِ هفته</b>\n<i>مغز وصل نیست. بعداً دوباره تلاش کن.</i>"
        try:
            result = self._brain.think_and_communicate(checks={
                **{r: True for r in __import__("dual_brain_v3", fromlist=["COMPLIANCE_RULES"]).COMPLIANCE_RULES},
                **{r: True for r in __import__("dual_brain_v3", fromlist=["ETHICS_RULES"]).ETHICS_RULES},
            }, drafts_count=self._studio.draft_count)
            if result.get("blocked"):
                return "🧠 <b>بریف متوقف شد</b>\n<i>Guard فعال — پیشنهاد ممکن نیست.</i>"
            brief_msg = next((m for m in result["messages"] if m["kind"] == "brief_saba"), None)
            return brief_msg["text"] if brief_msg else "🧠 بریف خالی است."
        except Exception:  # noqa: BLE001
            return "🧠 <b>خطا در تولیدِ بریف.</b>"

    # ─── long-poll ──────────────────────────────────────────────────────────────
    def poll_once(self) -> int:
        if not self.wired or self._killed(): return 0
        try:
            data = self._http_get(self._build_url("getUpdates",
                {"offset": self._offset, "timeout": self._lp}), float(self._lp))
        except: return 0
        if not isinstance(data, dict) or not data.get("ok"): return 0
        processed = 0
        for upd in data.get("result") or []:
            uid = upd.get("update_id")
            if isinstance(uid, int) and uid + 1 > self._offset: self._offset = uid + 1
            is_cb = "callback_query" in upd
            msg = upd.get("message") or upd.get("callback_query", {}).get("message") or {}
            chat_id = msg.get("chat", {}).get("id")
            if chat_id != self._saba: processed += 1; continue
            if is_cb:
                text, kb = self.dispatch_callback(upd.get("callback_query", {}).get("data"))
                if text: self.send(text, kb or BACK_KB)
            else:
                resp = self.handle_command(msg.get("text"))
                if resp: self.send(resp, MAIN_MENU if msg.get("text","").startswith("/start") else None)
                else:
                    with self._lk:
                        self._quarantine.append({"text": str(msg.get("text",""))[:500]})
            processed += 1
        return processed

    def run_forever(self):
        if not self.wired: return
        while not self._killed(): self.poll_once()
