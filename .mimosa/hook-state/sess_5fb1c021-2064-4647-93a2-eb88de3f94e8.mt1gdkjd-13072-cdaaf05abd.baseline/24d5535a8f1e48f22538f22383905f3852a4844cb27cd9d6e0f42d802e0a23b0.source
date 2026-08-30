"""Telegram interface — commands + push notifications.

All outgoing messages use HTML parse mode with escaped dynamic fields.
(Markdown crashed whenever a lead title contained * _ [ characters.)
"""
from __future__ import annotations

import asyncio
import html
import logging
import re
from datetime import timedelta

from sqlmodel import func, select
from telegram import Bot, Update
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from config import settings
from db import Channel, Lead, RunLog, get_session, utcnow

logger = logging.getLogger(__name__)

# /save_12 /skip_12 /draft_12 (leads) — /approve_3 /reject_3 (channels)
ACTION_RE = re.compile(r"^/(save|skip|draft|approve|reject)_(\d+)")

# Strong refs to fire-and-forget tasks so the GC can't drop them mid-flight
_BG_TASKS: set[asyncio.Task] = set()


def _spawn(coro) -> None:
    task = asyncio.get_running_loop().create_task(coro)
    _BG_TASKS.add(task)
    task.add_done_callback(_BG_TASKS.discard)


def esc(value: object) -> str:
    """Escape dynamic text for Telegram HTML parse mode."""
    return html.escape(str(value or ""), quote=False)


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
    if (lead.score_reason or "").startswith("action="):
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
        f"{action_emoji} <b>{esc(lead.source)}</b> | score: <b>{lead.score}</b>"
        f" | {cat_emoji} {esc(lead.category)}",
        f"📌 {esc((lead.title or '')[:180])}",
    ]
    if lead.value_aud:
        parts.append(f"💰 ~${lead.value_aud:,} AUD")
    if lead.deadline:
        parts.append(f"📅 closes: {lead.deadline.strftime('%Y-%m-%d')}")
    if lead.suburb:
        parts.append(f"📍 {esc(lead.suburb)}")
    if lead.url:
        parts.append(f"🔗 {esc(lead.url)}")
    if lead.score_reason:
        parts.append(f"\n<i>{esc(lead.score_reason)}</i>")
    # Order action buttons so the recommended one is first
    save, draft, skip = f"/save_{lead.id}", f"/draft_{lead.id}", f"/skip_{lead.id}"
    order = {
        "draft": [draft, save, skip],
        "save": [save, draft, skip],
        "skip": [skip, save, draft],
    }.get(action, [save, draft, skip])
    parts.append("\n" + "  ".join(order))
    return "\n".join(parts)


def _format_channel(ch: Channel) -> str:
    return (
        f"🆕 <b>{esc(ch.name)}</b>\n"
        f"🏷️ {esc(ch.type)} | score: <b>{ch.score}</b>\n"
        f"💰 {esc(ch.typical_value)} | volume: {esc(ch.lead_volume)}"
        f" | cost: {esc(ch.cost_to_enter)}\n"
        f"🚪 access: {esc(ch.access)}\n"
        f"🔗 {esc(ch.url)}\n\n"
        f"<i>{esc((ch.notes or '')[:400])}</i>\n\n"
        f"/approve_{ch.id}  /reject_{ch.id}"
    )


# ---------------------------------------------------------------- commands

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
        "/report — weekly pattern report\n"
        "/help — this message\n\n"
        "Per-item actions (buttons under each message):\n"
        "/save_ID /skip_ID — file or dismiss a lead\n"
        "/draft_ID — Claude drafts an outreach email (YOU send it manually)\n"
        "/approve_ID /reject_ID — accept or reject a discovered channel"
    )


cmd_help = cmd_start


async def cmd_new(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
    if not _is_authorized(update):
        return
    cutoff = utcnow() - timedelta(hours=24)
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
            _format_lead(lead), parse_mode=ParseMode.HTML, disable_web_page_preview=True
        )


async def cmd_digest(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
    if not _is_authorized(update):
        return
    cutoff = utcnow() - timedelta(hours=24)
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
    await update.message.reply_text(
        f"☀️ <b>Top {len(top)} امروز</b>", parse_mode=ParseMode.HTML
    )
    for lead in top:
        await update.message.reply_text(
            _format_lead(lead), parse_mode=ParseMode.HTML, disable_web_page_preview=True
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
        await update.message.reply_text(
            _format_channel(ch), parse_mode=ParseMode.HTML, disable_web_page_preview=True
        )


async def cmd_stats(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
    if not _is_authorized(update):
        return
    with get_session() as s:
        def _count(stmt) -> int:
            return s.exec(stmt).one()

        total_leads = _count(select(func.count()).select_from(Lead))
        recent = _count(
            select(func.count())
            .select_from(Lead)
            .where(Lead.discovered_at >= utcnow() - timedelta(days=7))
        )
        saved = _count(
            select(func.count()).select_from(Lead).where(Lead.status == "saved")
        )
        channels = _count(select(func.count()).select_from(Channel))
        approved = _count(
            select(func.count()).select_from(Channel).where(Channel.status == "approved")
        )
        runs = _count(select(func.count()).select_from(RunLog))
    await update.message.reply_text(
        "📊 <b>Stats</b>\n"
        f"Leads total: <b>{total_leads}</b>\n"
        f"Leads last 7d: <b>{recent}</b>\n"
        f"Leads saved: <b>{saved}</b>\n"
        f"Channels: <b>{channels}</b> (approved: {approved})\n"
        f"Runs: <b>{runs}</b>",
        parse_mode=ParseMode.HTML,
    )


async def cmd_hunt(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
    if not _is_authorized(update):
        return
    await update.message.reply_text(
        "🕵️ Hunter run started in background — I'll message you when it finishes."
    )

    async def _bg() -> None:
        from hunter.agent import run_hunter

        try:
            found = await asyncio.to_thread(run_hunter)
            await push(f"✅ Hunter finished — <b>{found}</b> new channels proposed. /channels")
        except Exception:
            logger.exception("Hunter background run failed")
            try:
                await push("❌ Hunter run failed — check the logs.")
            except Exception:
                logger.exception("Could not report hunter failure")

    _spawn(_bg())


# ------------------------------------------------- per-item action commands

async def cmd_action(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /save_N /skip_N /draft_N (leads) and /approve_N /reject_N (channels)."""
    if not _is_authorized(update):
        return
    m = ACTION_RE.match((update.message.text or "").strip())
    if not m:
        return
    verb, obj_id = m.group(1), int(m.group(2))

    if verb in ("save", "skip", "draft"):
        with get_session() as s:
            lead = s.get(Lead, obj_id)
            if lead is None:
                await update.message.reply_text(f"❓ Lead #{obj_id} not found.")
                return
            if verb == "draft":
                await update.message.reply_text(
                    f"✍️ Drafting outreach email for lead #{obj_id}…"
                )

                async def _bg_draft(lead_id: int = obj_id) -> None:
                    from drafts import generate_draft

                    with get_session() as s2:
                        fresh = s2.get(Lead, lead_id)
                        if fresh is None:
                            return
                        try:
                            text = await asyncio.to_thread(generate_draft, fresh)
                        except Exception:
                            logger.exception("draft generation failed")
                            await push(
                                f"❌ Draft for lead #{lead_id} failed — "
                                "check ANTHROPIC_API_KEY / credit."
                            )
                            return
                        if fresh.status in ("new", "shown"):
                            fresh.status = "saved"
                            s2.add(fresh)
                            s2.commit()
                    await push(
                        f"📧 <b>Draft for lead #{lead_id}</b> — review, edit, "
                        f"send manually from your own email:\n\n"
                        f"<pre>{esc(text)}</pre>\n\n"
                        "⚠️ ارسال فقط دستی. قبل از ارسال، گیرنده و الزامات "
                        "Spam Act (معرفی فرستنده + امکان opt-out) را چک کن."
                    )

                _spawn(_bg_draft())
                return
            new_status = "saved" if verb == "save" else "skipped"
            if lead.status == new_status:
                await update.message.reply_text(
                    f"ℹ️ Lead #{obj_id} is already <b>{new_status}</b>.",
                    parse_mode=ParseMode.HTML,
                )
                return
            lead.status = new_status
            s.add(lead)
            s.commit()
            emoji = "💾" if new_status == "saved" else "🗑"
            await update.message.reply_text(
                f"{emoji} Lead #{obj_id} → <b>{new_status}</b>\n"
                f"📌 {esc((lead.title or '')[:100])}",
                parse_mode=ParseMode.HTML,
            )
        return

    # approve / reject → channels
    with get_session() as s:
        ch = s.get(Channel, obj_id)
        if ch is None:
            await update.message.reply_text(f"❓ Channel #{obj_id} not found.")
            return
        new_status = "approved" if verb == "approve" else "rejected"
        if ch.status == new_status:
            await update.message.reply_text(
                f"ℹ️ Channel #{obj_id} is already <b>{new_status}</b>.",
                parse_mode=ParseMode.HTML,
            )
            return
        ch.status = new_status
        ch.approved_at = utcnow() if verb == "approve" else None
        s.add(ch)
        s.commit()
        name = esc(ch.name)
    if verb == "approve":
        await update.message.reply_text(
            f"✅ Channel #{obj_id} <b>approved</b>: {name}\n"
            "Hunter will treat it as known. To auto-harvest leads from it, "
            "a dedicated harvester gets added (see README «افزودن Harvester جدید»).",
            parse_mode=ParseMode.HTML,
        )
    else:
        await update.message.reply_text(
            f"🚫 Channel #{obj_id} <b>rejected</b>: {name}\n"
            "Hunter won't propose it again (it stays in DB as rejected).",
            parse_mode=ParseMode.HTML,
        )



# ----------------------------------------------------------- weekly report

def build_report_text(
    days: int,
    per_source: list[tuple[str, int, float]],
    statuses: list[tuple[str, int]],
    pending_channels: int,
    approved_channels: int,
    hunter_runs: int,
    hunter_tokens: tuple[int, int],
    run_errors: int,
) -> str:
    """Pure formatter — unit-tested."""
    lines = [f"📈 <b>Report — last {days}d</b>", ""]
    lines.append("<b>Leads per source</b> (count | avg score)")
    if per_source:
        for name, cnt, avg in per_source:
            lines.append(f"  • {esc(name)}: {cnt} | {avg:.0f}")
    else:
        lines.append("  • هیچ لیدی در این بازه نیست")
    lines.append("")
    lines.append("<b>Pipeline</b>")
    for status, cnt in statuses:
        lines.append(f"  • {esc(status)}: {cnt}")
    lines.append("")
    lines.append(
        f"<b>Channels</b>: pending {pending_channels} | approved {approved_channels}"
    )
    tin, tout = hunter_tokens
    lines.append(f"<b>Hunter</b>: {hunter_runs} runs | tokens {tin:,}→{tout:,}")
    if run_errors:
        lines.append(f"⚠️ runs with errors: {run_errors}")
    return "\n".join(lines)


async def cmd_report(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
    if not _is_authorized(update):
        return
    days = 7
    cutoff = utcnow() - timedelta(days=days)
    with get_session() as s:
        per_source = [
            (row[0], row[1], float(row[2] or 0))
            for row in s.exec(
                select(Lead.source, func.count(), func.avg(Lead.score))
                .select_from(Lead)
                .where(Lead.discovered_at >= cutoff)
                .group_by(Lead.source)
            ).all()
        ]
        statuses = [
            (row[0], row[1])
            for row in s.exec(
                select(Lead.status, func.count())
                .select_from(Lead)
                .where(Lead.discovered_at >= cutoff)
                .group_by(Lead.status)
            ).all()
        ]
        pending = s.exec(
            select(func.count()).select_from(Channel).where(Channel.status == "pending")
        ).one()
        approved = s.exec(
            select(func.count()).select_from(Channel).where(Channel.status == "approved")
        ).one()
        hunter_runs = s.exec(
            select(func.count())
            .select_from(RunLog)
            .where(RunLog.kind == "hunter", RunLog.started_at >= cutoff)
        ).one()
        tin = s.exec(
            select(func.coalesce(func.sum(RunLog.tokens_in), 0))
            .select_from(RunLog)
            .where(RunLog.started_at >= cutoff)
        ).one()
        tout = s.exec(
            select(func.coalesce(func.sum(RunLog.tokens_out), 0))
            .select_from(RunLog)
            .where(RunLog.started_at >= cutoff)
        ).one()
        errors = s.exec(
            select(func.count())
            .select_from(RunLog)
            .where(RunLog.error != "", RunLog.started_at >= cutoff)
        ).one()
    await update.message.reply_text(
        build_report_text(
            days, per_source, statuses, pending, approved,
            hunter_runs, (int(tin), int(tout)), errors,
        ),
        parse_mode=ParseMode.HTML,
    )


# ----------------------------------------------------------------- plumbing

_push_bot: Bot | None = None


async def push(text: str, parse_mode: str | None = ParseMode.HTML) -> None:
    """Standalone push to operator (used by scheduler jobs)."""
    global _push_bot
    if _push_bot is None:
        _push_bot = Bot(token=settings.telegram_bot_token)
    await _push_bot.send_message(
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
    app.add_handler(CommandHandler("report", cmd_report))
    # /save_12 style commands carry their id in the command itself →
    # matched via regex, not CommandHandler
    app.add_handler(MessageHandler(filters.Regex(ACTION_RE), cmd_action))
    return app
