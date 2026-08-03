"""Entry point — `python main.py`."""
from __future__ import annotations

import asyncio
import logging
import signal

from rich.logging import RichHandler

from config import settings
from db import init_db
from scheduler import build_scheduler, initial_kick
from telegram_bot import build_app, push


def setup_logging() -> None:
    logging.basicConfig(
        level=settings.log_level,
        format="%(message)s",
        datefmt="[%X]",
        handlers=[RichHandler(rich_tracebacks=True)],
    )


async def amain() -> None:
    setup_logging()
    log = logging.getLogger("main")

    init_db()
    log.info("DB ready at %s", settings.db_path)

    app = build_app()
    sched = build_scheduler()

    await app.initialize()
    await app.start()
    await app.updater.start_polling(drop_pending_updates=True)
    sched.start()
    log.info("Telegram bot + scheduler running.")

    try:
        await push(
            "🚀 *Paint Leads bot online*\n"
            f"Harvester: every {settings.harvester_run_every_minutes}min\n"
            f"Hunter: every {settings.hunter_run_every_hours}h\n"
            f"Digest: daily at {settings.digest_hour_local}:00 {settings.timezone}\n\n"
            "Try /help"
        )
    except Exception:
        log.exception("Could not send startup ping (check telegram credentials)")

    # Run an initial harvester pass in the background
    asyncio.create_task(initial_kick())

    # Hold forever
    stop = asyncio.Event()

    def _on_signal(*_):
        log.info("Shutting down…")
        stop.set()

    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, _on_signal)
        except NotImplementedError:
            # Windows — fall back to KeyboardInterrupt
            pass

    try:
        await stop.wait()
    finally:
        sched.shutdown(wait=False)
        await app.updater.stop()
        await app.stop()
        await app.shutdown()


if __name__ == "__main__":
    try:
        asyncio.run(amain())
    except KeyboardInterrupt:
        pass
