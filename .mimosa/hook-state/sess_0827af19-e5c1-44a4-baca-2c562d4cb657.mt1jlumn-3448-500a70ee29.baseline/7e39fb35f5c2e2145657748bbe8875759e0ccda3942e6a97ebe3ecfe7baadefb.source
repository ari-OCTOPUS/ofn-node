"""Base class for harvesters. Each source subclasses this."""
from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from db import Lead, RunLog, get_session, save_lead, utcnow

logger = logging.getLogger(__name__)


class Harvester(ABC):
    """One harvester = one source. Run produces Lead rows."""

    name: str = "base"

    # Per-source schedule override (minutes). None → settings.harvester_run_every_minutes.
    # Set this on rate-limited sources so they don't burn their daily quota.
    interval_minutes: int | None = None

    @abstractmethod
    async def fetch(self) -> list[Lead]:
        """Fetch raw leads from the source. Dedup happens in run()."""
        ...

    async def run(self) -> tuple[int, int]:
        """Returns (total_fetched, new_saved)."""
        log = RunLog(kind=f"harvester:{self.name}")
        with get_session() as s:
            s.add(log)
            s.commit()
            s.refresh(log)
            log_id = log.id

        new_count = 0
        total = 0
        error = ""
        try:
            leads = await self.fetch()
            total = len(leads)
            for lead in leads:
                if save_lead(lead):
                    new_count += 1
        except Exception as e:
            error = f"{type(e).__name__}: {e}"
            logger.exception("Harvester %s failed", self.name)

        with get_session() as s:
            row = s.get(RunLog, log_id)
            if row:
                row.finished_at = utcnow()
                row.items_found = total
                row.items_new = new_count
                row.error = error
                s.add(row)
                s.commit()

        logger.info("[%s] fetched=%d new=%d error=%s", self.name, total, new_count, error or "-")
        return total, new_count
