"""Telegram interface — commands + push notifications."""
from __future__ import annotations

import logging
from datetime import datetime, timedelta

from sqlmodel import select
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import Application, CommandHandler, ContextTypes

from config import settings
from db import Channel, Lead, get_session

logger = logging.getLogger(__name__)


def _is_authorized(update: Update) -> bool:
    """Allow only the configured chat (int user id OR @channel username)."""
    if update.effective_chat is None:
        return False
    raw = str(settings.telegram_chat_id).strip()
    if raw.startswith("@"):
        return (update.effective_chat.username or "").lower() == raw[1:].lower()
    try:
        return update.effective_chat.id == int(raw)
    except ValueError:
        return False


def _format_lead(lead: Lead) -> str:
    # action lives at the front of score_reason: "action=draft | ..."
    action = "save"
    if lead.score_reason.startswith("action="):
        action = lead.score_reason.split("|", 1)[0].replace("action=", "").strip()

    action_emoji = {"draft": "🟢", "save": "🟡", "skip": "⚪️"}.get(action, "🔹")
    cat_emoji = {
        "strata_remedial": "🏘️",
        "government_education": "🏛️",
        "new_residential_multi": "🏗️",
        "commercial_fitout": "🏢",
        "filtered": "🚫",
        "uncategorised": "❓",
        # legacy
        "gov": "🏛️", "commercial": "🏢", "strata": "🏘️",
        "residential": "🏠", "da": "📋",
    }.get(lead.category, "🔹")

    parts = [
        f"{action_emoji} *{lead.source}* | score: *{lead.score}* | {cat_emoji} {lead.category}",
        f"📌 {lead.title[:180]}",
    ]
    if lead.value_aud:
        parts.append(f"💰 ~${lead.value_aud:,} AUD")
    if lead.deadline:
        parts.append(f"📅 closes: {lead.deadline.strftime('%Y-%m-%d')}")
    if lead.suburb:
        parts.append(f"📍 {lead.suburb}")
    if lead.url:
        parts.append(f"🔗 {lead.url}")
    if lead.score_reason:
        parts.append(f"\n_{lead.score_reason}_")
    # Order action buttons so the recommended one is first
    order = {
        "draft": [f"/draft\\_{lead.id}", f"/save\\_{lead.id}", f"/skip\\_{lead.id}"],
        "save":  [f"/save\\_{lead.id}",  f"/draft\\_{lead.id}", f"/skip\\_{lead.id}"],
        "skip":  [f"/skip\\_{lead.id}",  f"/save\\_{lead.id}",  f"/draft\\_{lead.id}"],
    }.get(action, [f"/save\\_{lead.id}", f"/draft\\_{lead.id}", f"/skip\\_{lead.id}"])
    parts.append("\n" + "  ".join(order))
    return "\n".join(parts)


async def cmd_start(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
    if not _is_authorized(update):
        return
    await update.message.reply_text(
        f"👋 Salam {settings.operator_name}! Paint Leads bot ready.\n\n"
        "Commands:\n"
        "/new — leads from last 24h\n"
        "/digest — today's top picks\n"
        "/hunt — force Hunter run now\n"
        "/channels — pending channels from Hunter\n"
        "/stats — counts\n"
        "/help — this message"
    )


cmd_help = cmd_start


async def cmd_new(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
    if not _is_authorized(update):
        return
    cutoff = datetime.utcnow() - timedelta(hours=24)
    with get_session() as s:
        q = (
            select(Lead)
            .where(Lead.discovered_at >= cutoff)
            .order_by(Lead.score.desc())
            .limit(10)
        )
        leads = list(s.exec(q).all())
    if not leads:
        await update.message.reply_text("🦗 No new leads in last 24h.")
        return
    for lead in leads:
        await update.message.reply_text(
            _format_lead(lead), parse_mode=ParseMode.MARKDOWN, disable_web_page_preview=True
        )


async def cmd_digest(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
    if not _is_authorized(update):
        return
    cutoff = datetime.utcnow() - timedelta(hours=24)
    with get_session() as s:
        q = (
            select(Lead)
            .where(Lead.discovered_at >= cutoff)
            .where(Lead.score >= 70)
            .order_by(Lead.score.desc())
            .limit(5)
        )
        top = list(s.exec(q).all())
    if not top:
        await update.message.reply_text("🥱 No high-score leads today.")
        return
    await update.message.reply_text(f"☀️ *Top {len(top)} امروز*", parse_mode=ParseMode.MARKDOWN)
    for lead in top:
        await update.message.reply_text(
            _format_lead(lead), parse_mode=ParseMode.MARKDOWN, disable_web_page_preview=True
        )


async def cmd_channels(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
    if not _is_authorized(update):
        return
    with get_session() as s:
        q = select(Channel).where(Channel.status == "pending").order_by(Channel.score.desc())
        rows = list(s.exec(q).all())
    if not rows:
        await update.message.reply_text("🌱 No pending channels. /hunt to discover.")
        return
    for ch in rows[:10]:
        msg = (
            f"🆕 *{ch.name}*\n"
            f"🏷️ {ch.type} | score: *{ch.score}*\n"
            f"💰 {ch.typical_value} | volume: {ch.lead_volume} | cost: {ch.cost_to_enter}\n"
            f"🚪 access: {ch.access}\n"
            f"🔗 {ch.url}\n\n"
            f"_{ch.notes[:400]}_\n\n"
            f"/approve\\_{ch.id}  /reject\\_{ch.id}"
        )
        await update.message.reply_text(
            msg, parse_mode=ParseMode.MARKDOWN, disable_web_page_preview=True
        )


async def cmd_stats(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
    if not _is_authorized(update):
        return
    from db import RunLog

    with get_session() as s:
        total_leads = len(list(s.exec(select(Lead)).all()))
        recent = len(
            list(
                s.exec(
                    select(Lead).where(
                        Lead.discovered_at >= datetime.utcnow() - timedelta(days=7)
                    )
                ).all()
            )
        )
        channels = len(list(s.exec(select(Channel)).all()))
        runs = len(list(s.exec(select(RunLog)).all()))
    await update.message.reply_text(
        f"📊 *Stats*\n"
        f"Leads total: *{total_leads}*\n"
        f"Leads last 7d: *{recent}*\n"
        f"Channels: *{channels}*\n"
        f"Runs: *{runs}*",
        parse_mode=ParseMode.MARKDOWN,
    )


async def cmd_hunt(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
    if not _is_authorized(update):
        return
    await update.message.reply_text("🕵️ Hunter run starting (async)…")
    # Lazy import to avoid circular
    from hunter.agent import run_hunter

    found = await run_hunter()
    await update.message.reply_text(f"✅ Hunter finished — {found} new channels proposed.")


async def push(text: str, parse_mode: str | None = ParseMode.MARKDOWN) -> None:
    """Standalone push to operator (used by scheduler jobs)."""
    from telegram import Bot

    bot = Bot(token=settings.telegram_bot_token)
    await bot.send_message(
        chat_id=settings.chat_id_for_telegram,
        text=text,
        parse_mode=parse_mode,
        disable_web_page_preview=True,
    )


def build_app() -> Application:
    app = Application.builder().token(settings.telegram_bot_token).build()
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("help", cmd_help))
    app.add_handler(CommandHandler("new", cmd_new))
    app.add_handler(CommandHandler("digest", cmd_digest))
    app.add_handler(CommandHandler("hunt", cmd_hunt))
    app.add_handler(CommandHandler("channels", cmd_channels))
    app.add_handler(CommandHandler("stats", cmd_stats))
    return app
