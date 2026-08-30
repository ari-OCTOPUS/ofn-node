"""رابط تلگرام — لایهٔ نازک. فقط فرمان‌ها را به هستهٔ منطقی وصل می‌کند.
از کتابخانهٔ python-telegram-bot نسخهٔ ۲۱ استفاده می‌کند."""
from functools import wraps

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
)

from core import governance
from core.models import State

_BADGE = {State.RUNNING: "🟢 روشن", State.STOPPED: "⚪️ خاموش", State.UNKNOWN: "❓ ناشناخته"}


def build_application(manager, safety, owner_id: int,
                      store=None, authz=None, registry=None) -> Application:
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

    def _ziman_role(update: Update) -> str:
        uid = update.effective_user.id if update.effective_user else 0
        if authz is not None:
            return authz.ziman_role_for_chat(uid)
        return "owner"  # owner_only قبلاً به مالک محدود کرده

    @owner_only
    async def cmd_queue(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if store is None:
            await update.effective_message.reply_text("صفِ حاکمیت در دسترس نیست.")
            return
        items = governance.pending_summary(store)
        if not items:
            await update.effective_message.reply_text("✅ هیچ proposalِ در انتظار نیست.")
            return
        lines = ["⏳ در انتظارِ تصمیم:"]
        for it in items:
            lines.append(f"• {it['ref']} [{it['risk']}] {it['kind']}: {it['detail']}")
        lines.append("\nتأیید: /approve <ZIM-DEC-id> · رد: /reject <id> · تعویق: /defer <id>")
        await update.effective_message.reply_text("\n".join(lines))

    async def _decide(update: Update, context: ContextTypes.DEFAULT_TYPE, outcome: str):
        if store is None:
            await update.effective_message.reply_text("حاکمیت در دسترس نیست.")
            return
        if not context.args:
            await update.effective_message.reply_text(f"استفاده: /{outcome} <ZIM-DEC-id>")
            return
        ref = context.args[0]
        actor = str(update.effective_user.id) if update.effective_user else "?"
        try:
            d = governance.decide_by_ref(store, ref, outcome, actor, _ziman_role(update))
            await update.effective_message.reply_text(
                f"✅ {outcome}: {d['decision_id']} (ریسک {d['risk']}) — هنوز اجرا نمی‌شود (shadow).")
        except PermissionError as e:
            await update.effective_message.reply_text(f"⛔ اجازه ندارید: {e}")
        except Exception as e:  # noqa: BLE001
            await update.effective_message.reply_text(f"⚠️ خطا: {e}")

    @owner_only
    async def cmd_approve(update: Update, context: ContextTypes.DEFAULT_TYPE):
        await _decide(update, context, "approve")

    @owner_only
    async def cmd_reject(update: Update, context: ContextTypes.DEFAULT_TYPE):
        await _decide(update, context, "reject")

    @owner_only
    async def cmd_defer(update: Update, context: ContextTypes.DEFAULT_TYPE):
        await _decide(update, context, "defer")

    @owner_only
    async def cmd_halt(update: Update, context: ContextTypes.DEFAULT_TYPE):
        safety.halt("از تلگرام")
        await update.effective_message.reply_text("⛔ قفل ایمنی روشن شد. همه‌چیز متوقف است.")

    @owner_only
    async def cmd_resume(update: Update, context: ContextTypes.DEFAULT_TYPE):
        safety.resume()
        await update.effective_message.reply_text("✅ قفل ایمنی برداشته شد.")

    @owner_only
    async def on_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
        q = update.callback_query
        await q.answer()
        action, _, pid = q.data.partition(":")
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
    if store is not None:   # هندلرهای حاکمیت فقط وقتی store هست
        app.add_handler(CommandHandler("queue", cmd_queue))
        app.add_handler(CommandHandler("approve", cmd_approve))
        app.add_handler(CommandHandler("reject", cmd_reject))
        app.add_handler(CommandHandler("defer", cmd_defer))
    app.add_handler(CallbackQueryHandler(on_button))
    return app


# ترفند کوچک تا توکن را جدا از منطق نگه داریم
_TOKEN_HOLDER = {"token": ""}


def set_token(token: str) -> None:
    _TOKEN_HOLDER["token"] = token
