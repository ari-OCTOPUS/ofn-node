"""رابط تلگرام — لایهٔ نازک. فقط فرمان‌ها را به هستهٔ منطقی وصل می‌کند.
از کتابخانهٔ python-telegram-bot نسخهٔ ۲۱ استفاده می‌کند."""
import logging
from functools import wraps

from telegram import ForceReply, InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.error import Conflict, NetworkError
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from core.models import State

_BADGE = {State.RUNNING: "🟢 روشن", State.STOPPED: "⚪️ خاموش", State.UNKNOWN: "❓ ناشناخته"}

_LOG = logging.getLogger("control-brain.telegram")
_ERR_SAMPLE = {"conflict": 0, "network": 0}


async def _on_error(update, context) -> None:
    """error handler سراسری PTB — به‌جای traceback اسپم، یک خط روشن و نمونه‌گیری‌شده."""
    err = context.error
    if isinstance(err, Conflict):
        _ERR_SAMPLE["conflict"] += 1
        n = _ERR_SAMPLE["conflict"]
        if n <= 2 or n % 30 == 0:
            print(f"⚠️ Conflict تلگرام (دفعهٔ {n}): یک نمونهٔ دیگر از همین ربات در حال polling است — "
                  "پنجرهٔ دوم یا autostart مخفی را ببند. (قفل تک‌نمونهٔ app.py اجراهای بعدی را خودش می‌گیرد.)")
        return
    if isinstance(err, NetworkError):
        _ERR_SAMPLE["network"] += 1
        n = _ERR_SAMPLE["network"]
        if n <= 2 or n % 10 == 0:
            print(f"🌐 خطای گذرای شبکهٔ تلگرام (دفعهٔ {n}): {err}")
        return
    _LOG.exception("خطای هندل‌نشده در ربات تلگرام", exc_info=err)


def build_application(manager, safety, owner_id: int,
                      memory=None, queue=None, gateway=None, evolution=None) -> Application:
    """v2: با memory/queue/gateway → صف تأیید + بریف + بودجه؛ evolution → کارت جهش (فاز ۴).
    بدون آن‌ها دقیقاً رفتار v1 (سازگاری کامل عقب‌رو)."""
    def owner_only(handler):
        @wraps(handler)
        async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
            user = update.effective_user
            if user is None or user.id != owner_id:
                if update.effective_message:
                    await update.effective_message.reply_text("⛔ دسترسی رد شد.")
                return
            return await handler(update, context)
        return wrapper

    def status_text() -> str:
        lines = ["📋 وضعیت پروژه‌ها:\n"]
        if safety.is_halted():
            lines.append("⛔ قفل ایمنی روشن است — هیچ پروژه‌ای روشن نمی‌شود.\n")
        for s in manager.status_all():
            h = "" if s.healthy is None else ("  ✅ سالم" if s.healthy else "  ⚠️ ناسالم")
            off = "" if s.enabled else "  (غیرفعال)"
            lines.append(f"• {s.name}{off} — {_BADGE.get(s.state, s.state)}{h}")
        if memory is not None:
            st = memory.stats()
            lines.append(f"\n🧠 مغز دوم: {st['briefs']} بریف · {st['pending']} منتظر تأیید"
                         f" · {st['sent']} ارسال‌شده · {st['knowledge']} دانش")
        if gateway is not None:
            lines.append(gateway.budget_line())
        return "\n".join(lines)

    def keyboard() -> InlineKeyboardMarkup:
        rows = []
        for p in manager.registry.all():
            rows.append([
                InlineKeyboardButton(f"▶️ {p.name[:18]}", callback_data=f"start:{p.id}"),
                InlineKeyboardButton("⏹", callback_data=f"stop:{p.id}"),
                InlineKeyboardButton("🧪", callback_data=f"test:{p.id}"),
            ])
        rows.append([InlineKeyboardButton("🔄 تازه‌سازی", callback_data="refresh:-")])
        return InlineKeyboardMarkup(rows)

    @owner_only
    async def cmd_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.effective_message.reply_text(status_text(), reply_markup=keyboard())

    @owner_only
    async def cmd_halt(update: Update, context: ContextTypes.DEFAULT_TYPE):
        safety.halt("از تلگرام")
        await update.effective_message.reply_text("⛔ قفل ایمنی روشن شد. همه‌چیز متوقف است.")

    @owner_only
    async def cmd_resume(update: Update, context: ContextTypes.DEFAULT_TYPE):
        safety.resume()
        await update.effective_message.reply_text("✅ قفل ایمنی برداشته شد.")

    @owner_only
    async def cmd_queue(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if queue is None:
            await update.effective_message.reply_text("صف تأیید هنوز فعال نیست.")
            return
        items = queue.pending()
        if not items:
            await update.effective_message.reply_text("📮 صف خالی است — هیچ پیامی منتظر تأیید نیست.")
            return
        for m in items[:10]:
            kb = InlineKeyboardMarkup([[
                InlineKeyboardButton("✅ بفرست", callback_data=f"ap:ok:{m.id}"),
                InlineKeyboardButton("✏️ ویرایش", callback_data=f"ap:ed:{m.id}"),
                InlineKeyboardButton("❌ رد", callback_data=f"ap:no:{m.id}"),
            ]])
            await update.effective_message.reply_text(
                f"📮 #{m.id} — {m.business} → {m.to_ref} ({m.channel})\n――――――――――\n{m.text[:3000]}",
                reply_markup=kb)

    @owner_only
    async def cmd_briefs(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if memory is None:
            await update.effective_message.reply_text("حافظه هنوز فعال نیست.")
            return
        bs = memory.recent_briefs(5)
        if not bs:
            await update.effective_message.reply_text("🧠 هنوز بریفی نیست — رکن A در فاز ۳ روشن می‌شود.")
            return
        for b in bs:
            kb = InlineKeyboardMarkup([[
                InlineKeyboardButton("👍 مفید", callback_data=f"fb:g:{b.id}"),
                InlineKeyboardButton("👎 بی‌فایده", callback_data=f"fb:b:{b.id}"),
            ]])
            await update.effective_message.reply_text(
                f"🧠 #{b.id} — {b.business}\n📌 {b.title}\n▶️ {b.action}\n🔗 {b.source}",
                reply_markup=kb)

    @owner_only
    async def on_edit_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """متن جایگزین بعد از دکمهٔ ✏️ — فقط وقتی edit در جریان است."""
        mid = context.user_data.pop("edit_id", None)
        if mid is None or queue is None:
            return
        queue.resolve(int(mid), "approved", edited_text=update.effective_message.text)
        await update.effective_message.reply_text(f"✏️→✅ پیام #{mid} با متن جدید ارسال شد.")

    @owner_only
    async def on_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
        q = update.callback_query
        await q.answer()
        action, _, pid = q.data.partition(":")
        if action == "fb" and memory is not None:
            kind, _, bid = pid.partition(":")
            from core.contracts import Feedback
            memory.add_feedback(Feedback(brief_id=int(bid), useful=(kind == "g")))
            await q.edit_message_reply_markup(None)
            await q.message.reply_text("ثبت شد — تحقیق بعدی هدفمندتر می‌شود. 🙏"
                                       if kind == "g" else "ثبت شد — این مسیر کم‌وزن می‌شود. 👌")
            return
        if action == "ev" and evolution is not None:
            kind, _, pid2 = pid.partition(":")
            msg = evolution.resolve(int(pid2), "approved" if kind == "ok" else "rejected")
            await q.edit_message_reply_markup(None)
            await q.message.reply_text(msg)
            return
        if action == "ap" and queue is not None:
            kind, _, mid = pid.partition(":")
            mid = int(mid)
            if kind == "ok":
                queue.resolve(mid, "approved")
                await q.edit_message_reply_markup(None)
                await q.message.reply_text(f"✅ پیام #{mid} ارسال شد.")
            elif kind == "no":
                queue.resolve(mid, "rejected")
                await q.edit_message_reply_markup(None)
                await q.message.reply_text(f"❌ پیام #{mid} رد شد.")
            elif kind == "ed":
                context.user_data["edit_id"] = mid
                await q.message.reply_text(
                    f"✏️ متن جدید پیام #{mid} را در جواب همین پیام بنویس:",
                    reply_markup=ForceReply(selective=True))
            return
        if action == "refresh":
            await q.edit_message_text(status_text(), reply_markup=keyboard())
            return
        if action == "start":
            r = manager.start(pid)
            msg = f"▶️ {r.name}: {r.detail}"
        elif action == "stop":
            r = manager.stop(pid)
            msg = f"⏹ {r.name}: {r.detail}"
        elif action == "test":
            ok, out = manager.test(pid)
            msg = f"🧪 {pid}: {'✅ سبز' if ok else '❌ قرمز'}\n\n{out[-500:]}"
        else:
            msg = "دستور ناشناخته"
        await q.message.reply_text(msg)
        await q.edit_message_text(status_text(), reply_markup=keyboard())

    app = Application.builder().token(_TOKEN_HOLDER["token"]).build()
    app.add_handler(CommandHandler(["start", "menu", "status"], cmd_status))
    app.add_handler(CommandHandler("halt", cmd_halt))
    app.add_handler(CommandHandler("resume", cmd_resume))
    app.add_handler(CommandHandler("queue", cmd_queue))
    app.add_handler(CommandHandler("briefs", cmd_briefs))
    app.add_handler(CallbackQueryHandler(on_button))
    app.add_handler(MessageHandler(filters.TEXT & filters.REPLY & ~filters.COMMAND, on_edit_reply))
    app.add_error_handler(_on_error)
    return app


# ترفند کوچک تا توکن را جدا از منطق نگه داریم
_TOKEN_HOLDER = {"token": ""}


def set_token(token: str) -> None:
    _TOKEN_HOLDER["token"] = token
