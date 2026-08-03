"""
Brushline -- Main entry point
Boots the Telegram bot with config validation and kill-switch check.
"""
import asyncio
import logging
import sys

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("brushline.main")


def _boot_check() -> bool:
    """Validate config and governance before starting. Returns True if OK."""
    from src.config import config
    from src import governance

    missing = config.validate()
    if missing:
        logger.error("Cannot start -- missing required config: %s", missing)
        logger.error("Fill in .env and restart.")
        return False

    if governance.is_kill_switch_active():
        logger.warning("Kill switch is ACTIVE at startup -- external actions blocked.")
        logger.warning("Run 'make unkill' or delete %s to resume.", config.KILL_SWITCH_FILE)
        # Don't exit -- bot still starts for /status and /kill_off commands

    logger.info("Config OK | business=%s | Serper=%s | TG chat IDs=%s",
                config.BUSINESS_NAME,
                "SET" if config.SERPER_API_KEY else "MISSING",
                config.ALLOWED_OPERATOR_CHAT_IDS)
    return True


async def main() -> None:
    if not _boot_check():
        sys.exit(1)

    from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
    from telegram.ext import (Application, CallbackQueryHandler,
                              MessageHandler, filters)

    from src.config import config
    from src.orchestrator import Orchestrator
    from src.telegram_bot import BrushlineBot, _fmt_card

    bot = BrushlineBot()
    # Arch review 2026-07-02: this injection was documented but never done --
    # bot.orchestrator stayed None in the live adapter.
    bot.orchestrator = Orchestrator()

    async def handle(update: Update, context) -> None:
        if not update.message or not update.message.text:
            return
        chat_id = update.message.chat_id
        text = update.message.text

        # /queue gets real inline-keyboard cards (Approve/Edit/Reject buttons);
        # everything else is a plain text reply. parse_mode is intentionally
        # NOT Markdown: draft bodies are arbitrary text and unbalanced * or _
        # would make Telegram reject the message (arch review 2026-07-02).
        if text.strip() == "/queue" and chat_id in config.ALLOWED_OPERATOR_CHAT_IDS:
            bot.approval_queue.escalate_overdue()
            items = bot.approval_queue.get_pending()
            if not items:
                await update.message.reply_text("Approval Queue is empty.")
                return
            for item in items:
                card = _fmt_card(item)
                kb = InlineKeyboardMarkup([[
                    InlineKeyboardButton(b["text"], callback_data=b["callback_data"])
                    for b in row
                ] for row in card["buttons"]])
                await update.message.reply_text(card["text"], reply_markup=kb)
            return

        response = await bot.handle_message(chat_id, text)
        if response:
            await update.message.reply_text(response)

    async def handle_button(update: Update, context) -> None:
        # Arch review 2026-07-02: CallbackQueryHandler was never registered,
        # so the P3 inline keyboard (the heart of INV-1 approval flow) was
        # unreachable in the live adapter. handle_callback re-checks the
        # operator allow-list itself (KB-05 s7).
        query = update.callback_query
        if query is None:
            return
        response = await bot.handle_callback(query.message.chat_id, query.data)
        await query.answer()
        if response:
            await query.message.reply_text(response)

    app = (
        Application.builder()
        .token(config.TELEGRAM_BOT_TOKEN)
        .build()
    )
    app.add_handler(CallbackQueryHandler(handle_button))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))
    app.add_handler(MessageHandler(filters.COMMAND, handle))

    logger.info("Brushline bot starting -- polling for messages...")
    async with app:
        await app.start()
        await app.updater.start_polling(drop_pending_updates=True)
        logger.info("Bot is live. Send /status to verify.")
        # Run until interrupted
        await asyncio.Event().wait()
        await app.updater.stop()
        await app.stop()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Brushline stopped by operator.")
