"""Base class for harvesters. Each source subclasses this."""
from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from db import Lead, RunLog, get_session, save_lead, utcnow

logger = logging.getLogger(__name__)

# Slit Sensilla quarantine (2026-07-12): every fetched Lead passes through
# save_lead_safe() instead of save_lead() directly. Falls back to the legacy
# path if quarantine import fails, so a missing/broken quarantine module can
# never break the harvester. Set QUARANTINE_ENABLED=False to bypass entirely.
try:
    from quarantine import save_lead_safe, Verdict
    _QUARANTINE_OK = True
except Exception as _e:  # pragma: no cover - defensive fallback
    logger.warning("quarantine module unavailable (%s); using legacy save_lead", _e)
    _QUARANTINE_OK = False

QUARANTINE_ENABLED = True


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
        """Returns (total_fetched, new_saved).

        Leads pass through the Slit Sensilla quarantine gate when available:
        each is ADMITTED (→ save_lead), QUARANTINED (parked), or REJECTED
        (dropped). Counts are logged separately so an operator can see signal
        vs. noise at a glance.
        """
        log = RunLog(kind=f"harvester:{self.name}")
        with get_session() as s:
            s.add(log)
            s.commit()
            s.refresh(log)
            log_id = log.id

        new_count = 0
        quarantined = 0
        rejected = 0
        total = 0
        error = ""
        try:
            leads = await self.fetch()
            total = len(leads)
            for lead in leads:
                if QUARANTINE_ENABLED and _QUARANTINE_OK:
                    verdict, reason = save_lead_safe(lead)
                    if verdict is Verdict.ADMIT:
                        new_count += 1
                    elif verdict is Verdict.QUARANTINE:
                        quarantined += 1
                        logger.info("[%s] quarantined lead %s: %s",
                                    self.name, lead.external_id, reason)
                    else:
                        rejected += 1
                else:
                    # legacy path (quarantine disabled or broken)
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

        logger.info("[%s] fetched=%d admitted=%d quarantined=%d rejected=%d error=%s",
                    self.name, total, new_count, quarantined, rejected, error or "-")
        return total, new_count
