"""APScheduler jobs — per-source harvester loops, hunter loop, daily digest.

Design notes:
- Each harvester gets its OWN job with its own interval
  (Harvester.interval_minutes) so rate-limited sources like PlanningAlerts
  (1000 req/day free tier) don't burn quota on a global 15-min cadence.
- BUGFIX: the old single job passed next_run_time=None, which in APScheduler
  means "paused" — the harvest loop never actually ran on schedule; only the
  one-off startup kick worked.
- max_instances=1 + coalesce=True → a slow run never overlaps with the next.
"""
from __future__ import annotations

import asyncio
import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from sqlmodel import select

from config import settings
from db import Lead, get_session, utcnow
from harvesters import ALL as HARVESTERS
from scorer import score_unscored
from telegram_bot import _format_lead, push

logger = logging.getLogger(__name__)

HOT_SCORE = 85  # leads at/above this push to Telegram instantly


async def score_and_push() -> None:
    """Score whatever's new, then push the very high-score ones immediately."""
    scored = score_unscored()
    if scored:
        logger.info("Scored %d new leads", scored)

    with get_session() as s:
        q = (
            select(Lead)
            .where(Lead.score >= HOT_SCORE, Lead.status == "new")
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


async def run_harvester(cls: type) -> None:
    """One scheduled run of a single harvester, then score + push."""
    try:
        await cls().run()
    except Exception:
        logger.exception("Harvester %s crashed", cls.__name__)
    await score_and_push()


async def harvest_all() -> None:
    """Run every harvester once (used by the startup kick)."""
    logger.info("=== Full harvest cycle ===")
    for cls in HARVESTERS:
        try:
            await cls().run()
        except Exception:
            logger.exception("Harvester %s crashed", cls.__name__)
    await score_and_push()


async def hunter_loop() -> None:
    """Wrapper for scheduled Hunter run (run_hunter is blocking → thread)."""
    from hunter.agent import run_hunter

    try:
        n = await asyncio.to_thread(run_hunter)
        if n > 0:
            await push(
                f"🕵️ Hunter found <b>{n}</b> new candidate channels. Use /channels to review."
            )
    except Exception:
        logger.exception("Hunter run failed")


async def daily_digest() -> None:
    """Send top 5 picks of last 24h."""
    from datetime import timedelta

    cutoff = utcnow() - timedelta(hours=24)
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
    await push(f"☀️ <b>Daily digest — top {len(top)}</b>")
    for lead in top:
        await push(_format_lead(lead))


def build_scheduler() -> AsyncIOScheduler:
    sched = AsyncIOScheduler(timezone=settings.timezone)
    for cls in HARVESTERS:
        minutes = cls.interval_minutes or settings.harvester_run_every_minutes
        sched.add_job(
            run_harvester,
            IntervalTrigger(minutes=minutes),
            args=[cls],
            id=f"harvester:{cls.name}",
            coalesce=True,
            max_instances=1,
        )
        logger.info("Scheduled harvester %s: every %d min", cls.name, minutes)
    sched.add_job(
        hunter_loop,
        IntervalTrigger(hours=settings.hunter_run_every_hours),
        id="hunter",
        coalesce=True,
        max_instances=1,
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
