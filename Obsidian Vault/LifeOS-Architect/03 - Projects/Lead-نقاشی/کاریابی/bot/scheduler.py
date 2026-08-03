"""APScheduler jobs — harvester loop, hunter loop, daily digest."""
from __future__ import annotations

import asyncio
import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from sqlmodel import select

from config import settings
from db import Lead, get_session
from harvesters import ALL as HARVESTERS
from scorer import score_unscored
from telegram_bot import _format_lead, push

logger = logging.getLogger(__name__)


async def harvest_all() -> None:
    logger.info("=== Harvest cycle ===")
    for cls in HARVESTERS:
        try:
            await cls().run()
        except Exception:
            logger.exception("Harvester %s crashed", cls.__name__)

    # Score whatever's new
    scored = score_unscored()
    logger.info("Scored %d new leads", scored)

    # Push the *very* high-score ones immediately
    with get_session() as s:
        q = (
            select(Lead)
            .where(Lead.score >= 85, Lead.status == "new")
            .order_by(Lead.score.desc())
            .limit(5)
        )
        hot = list(s.exec(q).all())
        for lead in hot:
            try:
                await push(_format_lead(lead))
                lead.status = "shown"
                s.add(lead)
            except Exception:
                logger.exception("push failed")
        s.commit()


async def hunter_loop() -> None:
    """Wrapper for scheduled Hunter run."""
    from hunter.agent import run_hunter

    try:
        n = await run_hunter()
        if n > 0:
            await push(f"🕵️ Hunter found *{n}* new candidate channels. Use /channels to review.")
    except Exception:
        logger.exception("Hunter run failed")


async def daily_digest() -> None:
    """Send top 5 picks of last 24h."""
    from datetime import datetime, timedelta

    cutoff = datetime.utcnow() - timedelta(hours=24)
    with get_session() as s:
        q = (
            select(Lead)
            .where(Lead.discovered_at >= cutoff, Lead.score >= 70)
            .order_by(Lead.score.desc())
            .limit(5)
        )
        top = list(s.exec(q).all())
    if not top:
        await push("☀️ Digest: no high-score leads in last 24h.")
        return
    await push(f"☀️ *Daily digest — top {len(top)}*")
    for lead in top:
        await push(_format_lead(lead))


def build_scheduler() -> AsyncIOScheduler:
    sched = AsyncIOScheduler(timezone=settings.timezone)
    sched.add_job(
        harvest_all,
        IntervalTrigger(minutes=settings.harvester_run_every_minutes),
        id="harvester",
        next_run_time=None,  # run once immediately on startup via main()
    )
    sched.add_job(
        hunter_loop,
        IntervalTrigger(hours=settings.hunter_run_every_hours),
        id="hunter",
    )
    sched.add_job(
        daily_digest,
        CronTrigger(hour=settings.digest_hour_local, minute=0, timezone=settings.timezone),
        id="digest",
    )
    return sched


async def initial_kick() -> None:
    """Run harvesters once on startup so the user sees output immediately."""
    await asyncio.sleep(2)
    await harvest_all()
