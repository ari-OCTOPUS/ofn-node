"""SQLite schema for leads, channels, runs."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import UniqueConstraint
from sqlalchemy.exc import IntegrityError
from sqlmodel import Field, Session, SQLModel, create_engine, select

from config import settings


def utcnow() -> datetime:
    """Naive UTC now.

    The DB stores naive UTC timestamps; datetime.utcnow() is deprecated in
    Python 3.12+, so every module uses this helper instead. Keeping values
    naive avoids aware/naive comparison crashes with existing rows.
    """
    return datetime.now(timezone.utc).replace(tzinfo=None)


class Lead(SQLModel, table=True):
    """A single lead/opportunity discovered by a harvester."""

    __table_args__ = (
        UniqueConstraint("source", "external_id", name="uq_lead_source_external_id"),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    source: str = Field(index=True)  # e.g. "planning_alerts", "austender"
    external_id: str = Field(index=True)  # unique id within source
    title: str
    description: str = ""
    url: str
    value_aud: Optional[int] = None
    deadline: Optional[datetime] = None
    suburb: str = ""
    category: str = ""  # gov/commercial/strata/residential
    raw_json: str = ""  # full source payload
    score: int = 0  # 0-100
    score_reason: str = ""
    status: str = "new"  # new / shown / saved / skipped / quoted / won / lost
    discovered_at: datetime = Field(default_factory=utcnow, index=True)


class Channel(SQLModel, table=True):
    """A discovered lead channel (managed by Hunter agent)."""

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    type: str  # gov / commercial / strata / insurance / fm / remedial / developer ...
    url: str
    access: str  # open-tender / panel-application / cold-outreach / api / scrape / email
    cost_to_enter: str = "free"
    lead_volume: str = "medium"  # low / medium / high
    typical_value: str = "$30K-250K"
    competition: str = "medium"
    geo: str = "Sydney"
    sample_lead: str = ""
    notes: str = ""
    score: int = 0
    status: str = "pending"  # pending / approved / rejected / active
    discovered_at: datetime = Field(default_factory=utcnow)
    approved_at: Optional[datetime] = None


class RunLog(SQLModel, table=True):
    """Track each Hunter/Harvester run for debugging + analytics."""

    id: Optional[int] = Field(default=None, primary_key=True)
    kind: str  # "hunter" | "harvester:<source>"
    started_at: datetime = Field(default_factory=utcnow)
    finished_at: Optional[datetime] = None
    items_found: int = 0
    items_new: int = 0
    error: str = ""
    tokens_in: int = 0   # LLM usage (hunter/draft runs) — cost visibility
    tokens_out: int = 0


engine = create_engine(f"sqlite:///{settings.db_path}", echo=False)


def init_db() -> None:
    SQLModel.metadata.create_all(engine)


def get_session() -> Session:
    return Session(engine)


def lead_exists(source: str, external_id: str) -> bool:
    with get_session() as s:
        q = select(Lead).where(Lead.source == source, Lead.external_id == external_id)
        return s.exec(q).first() is not None


def save_lead(lead: Lead) -> bool:
    """Returns True if saved (new), False if duplicate.

    The (source, external_id) unique constraint is the real guarantee;
    lead_exists() is just a fast path to skip most duplicates cheaply.
    """
    if lead_exists(lead.source, lead.external_id):
        return False
    try:
        with get_session() as s:
            s.add(lead)
            s.commit()
    except IntegrityError:
        return False
    return True


def recent_leads(hours: int = 24) -> list[Lead]:
    cutoff = utcnow() - timedelta(hours=hours)
    with get_session() as s:
        q = select(Lead).where(Lead.discovered_at >= cutoff).order_by(Lead.score.desc())
        return list(s.exec(q).all())
