"""SQLite schema for leads, channels, runs."""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlmodel import Field, Session, SQLModel, create_engine, select

from config import settings


class Lead(SQLModel, table=True):
    """A single lead/opportunity discovered by a harvester."""

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
    score: int = 0  # 0-100 from LLM
    score_reason: str = ""
    status: str = "new"  # new / shown / saved / skipped / quoted / won / lost
    discovered_at: datetime = Field(default_factory=datetime.utcnow, index=True)

    class Config:
        # uniqueness on (source, external_id) to dedupe
        pass


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
    discovered_at: datetime = Field(default_factory=datetime.utcnow)
    approved_at: Optional[datetime] = None


class RunLog(SQLModel, table=True):
    """Track each Hunter/Harvester run for debugging + analytics."""

    id: Optional[int] = Field(default=None, primary_key=True)
    kind: str  # "hunter" | "harvester:<source>"
    started_at: datetime = Field(default_factory=datetime.utcnow)
    finished_at: Optional[datetime] = None
    items_found: int = 0
    items_new: int = 0
    error: str = ""


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
    """Returns True if saved (new), False if duplicate."""
    if lead_exists(lead.source, lead.external_id):
        return False
    with get_session() as s:
        s.add(lead)
        s.commit()
    return True


def recent_leads(hours: int = 24) -> list[Lead]:
    from datetime import timedelta

    cutoff = datetime.utcnow() - timedelta(hours=hours)
    with get_session() as s:
        q = select(Lead).where(Lead.discovered_at >= cutoff).order_by(Lead.score.desc())
        return list(s.exec(q).all())
