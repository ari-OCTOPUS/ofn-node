#!/usr/bin/env python3
"""saba_studio.py — 🎬 استودیوی صبا (رابط تلگرامیِ خوشگل و کارآمد، جدا از لنگر).

سیم‌کشی با معماری کل (blueprint §۳ two-brain · BRAIN-SPEC §۱ · CLAUDE.md):
  صبا (این بات) ──drafts.json──▶ ContentStudio (موتور) ──▶ آری/لنگر (/drafts)
                 ◀──for_saba.json (inbox آری)──────────────┘
  • منبع حقیقتِ درفت‌ها/کانفیگ = ContentStudio (drafts.json + config.json) — کانِن دوم نمی‌سازیم.
  • propose-only، دوکلیده: صبا ثبت → آری تأیید → انتشارِ درون‌پلتفرم. هیچ اکشن بیرونی این‌جا نیست.
  • صفر رسانه/هویت/PII — فقط متادیتا/متن. رسانهٔ واقعی هرگز وارد بات نمی‌شود.
  • محدودهٔ صبا مقدمِ مطلق: ✋ توقف پایدار (فایل HALT) که آری/لنگر هم می‌بینند.
  • فقط chat-id صبا؛ غریبه = سکوت. stdlib-only، $0، ایزوله.
"""
from __future__ import annotations
import html
import json
import os
import threading
import urllib.parse
import urllib.request
from datetime import date, datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent            # .../studio
PROJECT_ROOT = HERE.parent
DRAFTS_JSON = HERE / "drafts.json"
CONFIG_JSON = HERE / "config.json"
HALT_FILE = HERE / "HALT"                          # boundary halt (آری/لنگر می‌خوانند)
INBOX_JSON = HERE / "for_saba.json"                # آری → صبا
CAPACITY_JSON = HERE / "capacity.json"             # ظرفیت هفتگی صبا
BOUNDARY_LOG = HERE / "boundary_log.json"          # لاگ تغییر محدوده (append-only)
TELEGRAM_API = "https://api.telegram.org"

# موتور مشترک (اختیاری — نبودش fallback مستقل)
try:
    from content_studio import ContentStudio, COMPLIANCE_CHECKS
except Exception:
    ContentStudio = None
    COMPLIANCE_CHECKS = ["faceless", "feet_only", "no_explicit", "over_18"]

# لایهٔ گرم/تحسین‌گر (اختیاری — fail-soft؛ محتوا-آزاد، بدونِ برچسبِ شخصیت)
try:
    import sys as _sys
    if str(HERE) not in _sys.path:
        _sys.path.insert(0, str(HERE))
    import affirm
except Exception:
    affirm = None

CERT_LABELS = {
    "faceless": "بدون چهره",
    "feet_only": "فقط پا",
    "no_explicit": "بدون explicit",
    "over_18": "۱۸+ و با رضایت من",
}

MAIN_MENU = {"inline_keyboard": [
    [{"text": "📤 ثبت ایده/درفت", "callback_data": "s:new"},
     {"text": "📋 درفت‌های من", "callback_data": "s:drafts"}],
    [{"text": "🌟 امروز چیکار کنم؟", "callback_data": "s:today"},
     {"text": "🗓 تقویم هفته", "callback_data": "s:cal"}],
    [{"text": "🫶 ظرفیت من این هفته", "callback_data": "s:cap"},
     {"text": "📬 پیام‌های آری", "callback_data": "s:inbox"}],
    [{"text": "✋ محدودهٔ من", "callback_data": "s:scope"},
     {"text": "🔒 قول‌های ما", "callback_data": "s:rules"}],
    [{"text": "🧠 بریف هفته (heuristic)", "callback_data": "s:brief"},
     {"text": "⚙️ بیشتر", "callback_data": "s:more"}],
]}

# لایهٔ ۲ (2026-07-16): این صفحه‌ها executable هستند (از config.json می‌خوانند).
# برچسب‌ها truthful شده‌اند — دیگری «🔒 brain/engine» غلط بود چون واقعاً کار می‌کردند.
ADVANCED_MENU = {"inline_keyboard": [
    [{"text": "🔎 ترند و ایده", "callback_data": "s:trend"},
     {"text": "💡 پلن قیمت", "callback_data": "s:ppv"}],
    [{"text": "📈 نتیجه‌ها", "callback_data": "s:stats"},
     {"text": "↩️ منوی اصلی", "callback_data": "s:menu"}],
]}
BACK_KB = {"inline_keyboard": [[{"text": "↩️ منوی اصلی", "callback_data": "s:menu"}]]}


def _now() -> str: return datetime.now().isoformat(timespec="seconds")
def _load(path: Path, default):
    try: return json.loads(path.read_text(encoding="utf-8"))
    except Exception: return default
def _e(t: str) -> str: return html.escape(t or "")
def _mask(t): return (t[:4] + "…") if t and len(t) > 4 else ("∅" if not t else "…")
def _url_get(url, timeout):
    req = urllib.request.Request(url, headers={"User-Agent": "saba-studio/1.0"})
    with urllib.request.urlopen(req, timeout=timeout + 5) as r: return json.loads(r.read().decode())
def _url_post(url, body, timeout=10):
    d = json.dumps(body, ensure_ascii=False).encode()
    req = urllib.request.Request(url, data=d, headers={
        "User-Agent": "saba-studio/1.0", "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r: return json.loads(r.read().decode())


class SabaStudio:
    """رابط تلگرامیِ صبا. HTML غنی، منوی سه‌سطحی، conversation-state سبک."""

    name = "saba-studio"

    def __init__(self, studio=None, token=None, saba_chat_id=None,
                 http_get=None, http_post=None, brain=None, longpoll_timeout=30):
        self.studio = studio or (ContentStudio() if ContentStudio else None)
        self.token = token or os.environ.get("TELEGRAM_SABA_BOT_TOKEN", "").strip()
        cid = saba_chat_id if saba_chat_id is not None else os.environ.get("TELEGRAM_SABA_CHAT_ID", "0")
        self.saba = int(cid) if str(cid).strip() else 0
        self._get = http_get or _url_get
        self._post = http_post or _url_post
        self.brain = brain
        self._lp = longpoll_timeout
        self._lk = threading.Lock()
        self._offset = 0
        self._stop = False
        self._conv: dict[int, dict] = {}   # per-chat conversation state

    # ── وضعیت ──
    @property
    def wired(self) -> bool: return bool(self.token) and self.saba != 0
    @property
    def halted(self) -> bool: return HALT_FILE.exists()
    def __repr__(self): return f"<SabaStudio wired={self.wired} token={_mask(self.token)} halted={self.halted}>"
    def stop(self): self._stop = True
    def authorized(self, chat_id: int) -> bool: return self.saba != 0 and chat_id == self.saba

    # ── ارسال ──
    def send(self, text: str, reply_markup: dict | None = None) -> None:
        body = {"chat_id": self.saba, "text": text[:4000],
                "parse_mode": "HTML", "disable_web_page_preview": True}
        if reply_markup: body["reply_markup"] = reply_markup
        if not self.wired:
            print(text); return
        try: self._post(f"{TELEGRAM_API}/bot{self.token}/sendMessage", body)
        except Exception: pass

    # ── صفحه‌ها (HTML) ──
    def home(self) -> str:
        if self.halted:
            return ("✋ <b>الان روی توقف‌ای</b>\n"
                    "محدودهٔ تو مقدمِ همه‌چیزه. هر وقت خواستی برگردی، <code>/resume</code> بزن. 🌿")
        pend = self._pending_count()
        cap = _load(CAPACITY_JSON, {})
        theme = self._this_week_theme()
        unread = len([m for m in _load(INBOX_JSON, []) if not m.get("read")])
        greet = self._greeting()
        lines = [f"🎬 <b>استودیوی محتوا</b>", f"<i>{greet}</i>", "━━━━━━━━━━"]
        if affirm is not None:                       # یک خطِ گرم/تحسین‌گر (fail-soft)
            try:
                lines.append(f"<i>{_e(affirm.spotlight(pend))}</i>")
            except Exception:
                pass
        lines.append(f"📋 درفت‌های منتظر تأیید: <b>{pend}</b>")
        if theme: lines.append(f"🗓 تم این هفته: <b>{_e(theme)}</b>")
        if cap.get("hours"): lines.append(f"🫶 ظرفیت اعلامی: <b>{_e(str(cap['hours']))}</b> ساعت")
        if unread: lines.append(f"📬 <b>{unread}</b> پیام خوانده‌نشده از آری")
        lines.append("\nیه دکمه رو بزن ↓")
        return "\n".join(lines)

    def _advanced_page(self) -> str:
        """صفحهٔ پیشرفته — ترند/قیمت/آمار. همه از config.json واقعی می‌خوانند."""
        return ("⚙️ <b>بیشتر</b>\n"
                "این صفحه‌ها از دادهٔ پیکربندی پروژه می‌خوانند:\n"
                "• 🔎 ترند و ایده — تم‌های فعلی\n"
                "• 💡 پلن قیمت — تی‌یرهای PPV\n"
                "• 📈 نتیجه‌ها — آنالیتیکس پایه\n"
                "هر کدام را بزن.")

    def _greeting(self) -> str:
        h = datetime.now().hour
        if h < 12: return "صبحت قشنگ ☀️"
        if h < 18: return "بعدازظهر خوبی داشته باشی 🌸"
        return "شبت آروم 🌙"

    def _pending_count(self) -> int:
        data = _load(DRAFTS_JSON, [])
        return sum(1 for d in data if isinstance(d, dict) and d.get("status") == "pending")

    def _cfg(self) -> dict:
        return self.studio._config if self.studio else _load(CONFIG_JSON, {})

    def _this_week_theme(self) -> str:
        slots = self._cfg().get("calendar", {}).get("slots", [])
        return slots[0].get("theme", "") if slots else ""

    def drafts_page(self) -> str:
        data = [d for d in _load(DRAFTS_JSON, []) if isinstance(d, dict)]
        pend = [d for d in data if d.get("status") == "pending"]
        if not pend:
            return ("📋 <b>درفت‌های من</b>\n━━━━━━━━━━\n"
                    "هنوز درفتی منتظر تأیید نیست. با «📤 ثبت ایده/درفت» شروع کن. ✨")
        lines = ["📋 <b>درفت‌های من</b> (منتظر تأیید آری)", "━━━━━━━━━━"]
        for d in pend[-12:]:
            tier = f" · {_e(d.get('ppv_tier'))}" if d.get("ppv_tier") else ""
            lines.append(f"⏳ <code>{_e(d.get('draft_id',''))}</code> — {_e(d.get('title',''))}{tier}")
        if len(pend) > 12: lines.append(f"<i>… و {len(pend)-12} تای دیگر</i>")
        lines.append("\n<i>هر کدوم رو آری جدا تأیید می‌کنه (دوکلیده).</i>")
        return "\n".join(lines)

    def today_page(self) -> str:
        cfg = self.studio._config if self.studio else _load(CONFIG_JSON, {})
        cal = cfg.get("calendar", {}); slots = cal.get("slots", [])
        trends = cfg.get("trends", [])
        lines = ["🌟 <b>امروز چیکار کنم؟</b>", "━━━━━━━━━━"]
        if slots:
            s = slots[0]
            lines.append(f"🎯 تمرکز هفته: <b>{_e(s.get('theme',''))}</b>")
            lines.append(f"   کار: {_e(s.get('task',''))}")
        if trends:
            lines.append("\n💡 ایدهٔ سریع برای شوت امروز:")
            for t in trends[:2]:
                lines.append(f"   • {_e(t.get('tag',''))} — {_e(t.get('note',''))}")
        lines.append("\n<b>یادت باشه:</b> فقط پا 🦶 · بدون چهره/بدن · هر ست با بافر ≥۷ روز.")
        lines.append("<i>وقتی شوت آماده شد، «📤 ثبت ایده/درفت».</i>")
        return "\n".join(lines)

    def cal_page(self) -> str:
        cfg = self.studio._config if self.studio else _load(CONFIG_JSON, {})
        cal = cfg.get("calendar", {}); slots = cal.get("slots", [])
        lines = [f"🗓 <b>تقویم</b> · فصل: {_e(cal.get('season','?'))}", "━━━━━━━━━━"]
        if not slots: lines.append("<i>هنوز اسلاتی ثبت نشده.</i>")
        for s in slots:
            lines.append(f"هفته {s.get('week','?')}: <b>{_e(s.get('theme',''))}</b> — {_e(s.get('task',''))}")
        lines.append("<i>هیچ‌چی خودکار منتشر نمی‌شه.</i>")
        return "\n".join(lines)

    def trend_page(self) -> str:
        cfg = self.studio._config if self.studio else _load(CONFIG_JSON, {})
        trends = cfg.get("trends", [])
        if not trends: return "🔎 <b>ترند و ایده</b>\n━━━━━━━━━━\n<i>هنوز ترندی ثبت نشده.</i>"
        lines = ["🔎 <b>ترند و ایده</b>", "━━━━━━━━━━"]
        for t in trends:
            lines.append(f"📌 <b>{_e(t.get('tag',''))}</b>: {_e(t.get('note',''))} "
                         f"<i>({_e(t.get('optimal_time','?'))})</i>")
        lines.append("\n<i>هیچ‌کدوم اجباری نیست — الهام‌بخشه.</i>")
        return "\n".join(lines)

    def ppv_page(self) -> str:
        cfg = self.studio._config if self.studio else _load(CONFIG_JSON, {})
        ppv = cfg.get("ppv", {}); tiers = ppv.get("tiers", {})
        wall = ppv.get("wall_pct", 0.55)
        lines = ["💡 <b>پلن قیمت (PPV)</b>", "━━━━━━━━━━",
                 f"📊 صفحهٔ اصلی ~{wall*100:.0f}% · PPV ~{(1-wall)*100:.0f}%"]
        for name, c in tiers.items():
            lines.append(f"   {_e(name)}: <b>${c.get('price','?')}</b> — {_e(c.get('desc',''))}")
        lines.append("\n<i>اینا فقط پیشنهاده — قیمت نهایی رو آری قفل می‌کنه.</i>")
        return "\n".join(lines)

    def stats_page(self) -> str:
        cfg = self.studio._config if self.studio else _load(CONFIG_JSON, {})
        a = cfg.get("analytics", {})
        return ("📈 <b>نتیجه‌ها</b> (تجمیعی — صفر اطلاعاتِ خصوصیِ فن)\n━━━━━━━━━━\n"
                f"ماندگاری ۳۰ روزه: {a.get('retention_30d',0)*100:.0f}%\n"
                f"باز شدن PPV: {a.get('ppv_unlock_rate',0)*100:.0f}%\n"
                f"میانگین درآمد هر خریدار: ${a.get('arpu',0):.0f}\n"
                "<i>قبل از راه‌اندازی این‌ها نمونه‌اند؛ از هفتهٔ اول با دادهٔ واقعی پر می‌شن.</i>")

    def cap_page(self) -> str:
        cap = _load(CAPACITY_JSON, {})
        cur = f"الان: <b>{_e(str(cap.get('hours','—')))}</b> ساعت" if cap else "هنوز ثبت نشده"
        return ("🫶 <b>ظرفیت من این هفته</b>\n━━━━━━━━━━\n"
                f"{cur}\n\n"
                "چند ساعت این هفته می‌تونی برای شوت بذاری؟ عدد بفرست (مثلاً «۳»).\n"
                "<i>این کمک می‌کنه برنامه واقع‌بینانه بمونه — قول‌مون همینه.</i>")

    def inbox_page(self) -> str:
        msgs = _load(INBOX_JSON, [])
        if not msgs:
            return "📬 <b>پیام‌های آری</b>\n━━━━━━━━━━\n<i>فعلاً پیامی نیست.</i>"
        # علامت‌گذاری خوانده‌شده
        for m in msgs: m["read"] = True
        try: INBOX_JSON.write_text(json.dumps(msgs, ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception: pass
        lines = ["📬 <b>پیام‌های آری</b>", "━━━━━━━━━━"]
        for m in msgs[-8:]:
            lines.append(f"🗓 <i>{_e(m.get('date',''))}</i>\n{_e(m.get('text',''))}\n")
        return "\n".join(lines)

    def scope_page(self) -> str:
        return (
            "✋ <b>محدودهٔ من</b>\n━━━━━━━━━━\n"
            "این‌ها قفل‌ان و <b>حرفِ آخرِ تو</b>ست:\n"
            "🦶 فقط پا — بدون چهره، بدون بدن\n"
            "🚫 بدون هیچ محتوای explicit\n"
            "🔞 فقط ۱۸+، فقط با رضایتِ خودت\n\n"
            "هر وقت خواستی محدوده رو <b>تنگ‌تر</b> کنی، همین‌جا بنویس؛ فوراً اعمال می‌شه و به آری هم می‌رسه.\n"
            "می‌خوای همه‌چی وایسه؟ 👉 <code>/halt</code>  (هر وقت: <code>/resume</code>)")

    def rules_page(self) -> str:
        return ("🔒 <b>قول‌های ما</b>\n━━━━━━━━━━\n"
                "✅ فقط پا — چهره/بدن هیچ‌وقت\n"
                "✅ پرداخت فقط داخل پلتفرم (هیچ‌وقت بیرون)\n"
                "✅ حریمِ هر دومون محفوظ — صفر اسم/شهر\n"
                "✅ هیچ‌چی خودکار پست/دی‌ام نمی‌شه — همیشه آدم تأیید می‌کنه\n"
                "✅ گزارشِ پول هر هفته بهت می‌رسه، حتی اگه صفر باشه\n"
                "<i>هر چیزی خلافِ این‌ها = drop.</i>")

    def brief_page(self) -> str:
        brain_status = "online ✅" if self.brain else "offline 🔒"
        if self.brain:
            try:
                out = self.brain.think_and_communicate(draft_title="weekly")
                msgs = out.get("messages", []) if isinstance(out, dict) else []
                body = "\n".join(getattr(m, "text", str(m))[:280] for m in msgs[:3])
                if body: return f"🧠 <b>بریف هفته</b> (brain {brain_status})\n━━━━━━━━━━\n" + _e(body)
            except Exception as e:
                return (f"🧠 <b>بریف هفته</b> (brain {brain_status})\n━━━━━━━━━━\n"
                        f"مغز خطا داد: {e}\n"
                        f"پیش‌فرض: تمِ تقویم این هفته + ۱ ست تازه.")
        return (f"🧠 <b>بریف هفته</b> (brain {brain_status})\n━━━━━━━━━━\n"
                "تمرکز: تمِ تقویمِ این هفته + ۱ ست تازه با بافر.\n"
                "پیشنهادِ کپشن/قیمت رو آری از مغز می‌گیره و برات می‌فرسته.\n"
                "<i>بریفِ کاملِ AI بعد از وصل‌شدن مغز فعال می‌شه.</i>")

    # ── ثبت درفت (conversation) ──
    def _start_new(self, chat: int) -> tuple[str, dict]:
        self._conv[chat] = {"flow": "new", "step": "title", "cert": {}}
        return ("📤 <b>ثبت ایده/درفت</b>\n━━━━━━━━━━\n"
                "یه <b>عنوان کوتاه</b> برای این ست بفرست (فقط توضیح، بدون عکس).\n"
                "<i>مثلاً: «ست ابریشم — قرمز انار»</i>", BACK_KB)

    def _cert_kb(self, cert: dict) -> dict:
        rows = []
        for k in COMPLIANCE_CHECKS:
            mark = "✅" if cert.get(k) else "⬜️"
            rows.append([{"text": f"{mark} {CERT_LABELS.get(k,k)}", "callback_data": f"cert:{k}"}])
        rows.append([{"text": "✔️ ثبت نهایی", "callback_data": "cert:done"},
                     {"text": "↩️ لغو", "callback_data": "s:menu"}])
        return {"inline_keyboard": rows}

    def _handle_text(self, chat: int, text: str) -> tuple[str, dict]:
        conv = self._conv.get(chat)
        if conv and conv.get("flow") == "new" and conv.get("step") == "title":
            conv["title"] = text.strip()[:80]; conv["step"] = "cert"
            return ("عالی 🌟 حالا این‌ها رو تأیید کن (هر کدوم رو بزن تا ✅ شه):\n"
                    f"<b>{_e(conv['title'])}</b>", self._cert_kb(conv["cert"]))
        if conv and conv.get("flow") == "cap":
            digits = "".join(ch for ch in text if ch.isdigit() or ch in ".٫،")
            digits = digits.replace("٫", ".").replace("،", "")
            try: hours = float(digits or "0")
            except Exception: hours = 0.0
            self._conv.pop(chat, None)
            try:
                CAPACITY_JSON.write_text(json.dumps(
                    {"hours": hours, "date": date.today().isoformat()},
                    ensure_ascii=False, indent=2), encoding="utf-8")
            except Exception: pass
            return (f"ثبت شد 🫶 این هفته <b>{hours:g}</b> ساعت.\n"
                    "برنامه با همین تنظیم می‌شه — ممنون که واقع‌بینانه گفتی.", BACK_KB)
        if conv and conv.get("flow") == "scope_tighten":
            self._conv.pop(chat, None)
            self._log_boundary(text.strip()[:200])
            self._to_ari(f"صبا محدوده رو تنگ‌تر کرد: {text.strip()[:200]}")
            return ("گرفتم ✋ فوراً اعمال شد و به آری هم رسید. مرزِ تو همیشه مقدمه. 🌿", BACK_KB)
        # پیش‌فرض: راهنمای نرم
        return ("نفهمیدم دقیقاً 🌸 از منوی پایین یه دکمه بزن، یا برای شروعِ درفت «📤».",
                MAIN_MENU)

    def _finish_draft(self, chat: int) -> tuple[str, dict]:
        conv = self._conv.get(chat, {})
        title = conv.get("title", "بدون عنوان"); cert = conv.get("cert", {})
        missing = [CERT_LABELS.get(c, c) for c in COMPLIANCE_CHECKS if not cert.get(c)]
        if missing:
            return (f"هنوز این‌ها ✅ نشده: {'، '.join(missing)}\nهمه باید تأیید شن.",
                    self._cert_kb(cert))
        self._conv.pop(chat, None)
        if self.studio:
            res = self.studio.submit_draft(title=title, self_cert=cert)
            if res.get("ok"):
                return (f"ثبت شد ✅ کدِ درفت: <code>{res['draft_id']}</code>\n"
                        "رفت به صفِ تأییدِ آری (دوکلیده). ممنون 🌟", BACK_KB)
            return (f"ثبت نشد: {_e(str(res.get('error','')))}", BACK_KB)
        # fallback بدون موتور
        return ("ثبت شد ✅ (حالت آزمایشی — موتور وصل نیست).", BACK_KB)

    # ── handoff ──
    def _to_ari(self, note: str) -> None:
        """اعلان به آری از طریق inbox معکوس (studio/to_ari.json) — لنگر می‌خواند."""
        p = HERE / "to_ari.json"
        cur = _load(p, [])
        cur.append({"date": _now(), "text": note})
        try: p.write_text(json.dumps(cur[-50:], ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception: pass

    def _log_boundary(self, note: str) -> None:
        cur = _load(BOUNDARY_LOG, [])
        cur.append({"date": _now(), "change": note})
        try: BOUNDARY_LOG.write_text(json.dumps(cur, ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception: pass

    def halt(self) -> str:
        try: HALT_FILE.write_text(_now(), encoding="utf-8")
        except Exception: pass
        self._to_ari("صبا ✋ توقف زد — همه‌چی pause.")
        return ("✋ <b>باشه، همه‌چی وایساد.</b>\nهیچ فشاری نیست. هر وقت خواستی: <code>/resume</code> 🌿")

    def resume(self) -> str:
        try: HALT_FILE.unlink(missing_ok=True)
        except Exception: pass
        self._to_ari("صبا برگشت ▶️")
        return "خوش برگشتی 🌸 از منوی پایین ادامه بده."

    # ── روتر ──
    def route(self, chat: int, text: str = "", data: str = "") -> tuple[str, dict] | None:
        if not self.authorized(chat):
            return None  # سکوت مطلق برای غریبه
        # halt همیشه اول (جز resume)
        if self.halted and (data not in ("s:menu",) and text not in ("/resume", "/start")):
            if text == "/resume": return (self.resume(), MAIN_MENU)
            return (self.home(), {"inline_keyboard": [[{"text": "▶️ برگشت", "callback_data": "s:menu"}]]})
        if text in ("/start", "/menu") or data == "s:menu":
            self._conv.pop(chat, None)
            if self.halted and text == "/start":
                return (self.home(), None)
            return (self.home(), MAIN_MENU)
        if text == "/halt": return (self.halt(), None)
        if text == "/resume": return (self.resume(), MAIN_MENU)
        if text == "/help":
            return ("🎬 استودیوی صبا — از دکمه‌ها استفاده کن.\n"
                    "/menu منو · /halt توقف · /resume برگشت", MAIN_MENU)
        # callbackها
        if data == "s:new": return self._start_new(chat)
        if data == "s:drafts": return (self.drafts_page(), BACK_KB)
        if data == "s:today": return (self.today_page(), BACK_KB)
        if data == "s:cal": return (self.cal_page(), BACK_KB)
        if data == "s:more": return (self._advanced_page(), ADVANCED_MENU)
        if data == "s:trend": return (self.trend_page(), BACK_KB)
        if data == "s:ppv": return (self.ppv_page(), BACK_KB)
        if data == "s:stats": return (self.stats_page(), BACK_KB)
        if data == "s:inbox": return (self.inbox_page(), BACK_KB)
        if data == "s:rules": return (self.rules_page(), BACK_KB)
        if data == "s:brief": return (self.brief_page(), BACK_KB)
        if data == "s:cap":
            self._conv[chat] = {"flow": "cap"}; return (self.cap_page(), BACK_KB)
        if data == "s:scope":
            self._conv[chat] = {"flow": "scope_tighten"}; return (self.scope_page(), BACK_KB)
        if data.startswith("cert:"):
            key = data.split(":", 1)[1]; conv = self._conv.get(chat)
            if not conv: return (self.home(), MAIN_MENU)
            if key == "done": return self._finish_draft(chat)
            conv.setdefault("cert", {})[key] = not conv["cert"].get(key)
            return (f"<b>{_e(conv.get('title',''))}</b>", self._cert_kb(conv["cert"]))
        # متن آزاد → conversation
        if text: return self._handle_text(chat, text)
        return (self.home(), MAIN_MENU)

    # ── حلقهٔ long-poll ──
    def poll_forever(self) -> None:  # pragma: no cover
        if not self.wired:
            print("shadow-mode: TELEGRAM_SABA_BOT_TOKEN/TELEGRAM_SABA_CHAT_ID ست نیست.\n"
                  f"{self.home()}\nدستور/متن بده (stdin):")
            for line in __import__("sys").stdin:
                r = self.route(self.saba or 0, text=line.strip())
                if r: print(r[0])
            return
        self.send(self.home(), MAIN_MENU)
        while not self._stop:
            try:
                url = (f"{TELEGRAM_API}/bot{self.token}/getUpdates?" +
                       urllib.parse.urlencode({"timeout": self._lp, "offset": self._offset}))
                data = self._get(url, timeout=self._lp)
                for up in data.get("result", []):
                    self._offset = up["update_id"] + 1
                    if "message" in up:
                        m = up["message"]; chat = (m.get("chat") or {}).get("id", 0)
                        r = self.route(chat, text=m.get("text", ""))
                        if r: self.send(r[0], r[1])
                    elif "callback_query" in up:
                        cq = up["callback_query"]; chat = ((cq.get("message") or {}).get("chat") or {}).get("id", 0)
                        try:
                            self._post(f"{TELEGRAM_API}/bot{self.token}/answerCallbackQuery",
                                       {"callback_query_id": cq.get("id")})
                        except Exception: pass
                        r = self.route(chat, data=cq.get("data", ""))
                        if r: self.send(r[0], r[1])
            except Exception:
                __import__("time").sleep(5)


if __name__ == "__main__":  # pragma: no cover
    SabaStudio().poll_forever()
