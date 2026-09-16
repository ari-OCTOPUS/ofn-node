"""Phase 3 — quality fixes: utcnow, memory trim, dedup constraint."""
import datetime as dt

from db import utcnow
from hunter.agent import _trim_memory


def test_utcnow_naive_and_current():
    now = utcnow()
    assert now.tzinfo is None
    real = dt.datetime.now(dt.timezone.utc).replace(tzinfo=None)
    assert abs((real - now).total_seconds()) < 5


def test_trim_memory_small_untouched():
    small = "## a\nb"
    assert _trim_memory(small) == small


def test_trim_memory_caps_and_keeps_newest():
    big = "## OLD\nold-entry\n" + ("x" * 120_000) + "\n## NEW\nnewest-entry\n"
    out = _trim_memory(big)
    assert len(out.encode("utf-8")) <= 51_000 + 50
    assert out.startswith("(older runs trimmed)")
    assert "newest-entry" in out
    assert "old-entry" not in out


def test_lead_dedup_via_unique_constraint(tmp_path, monkeypatch):
    # real sqlite — runs on the dev machine where sqlmodel is installed
    import db as dbmod
    from sqlmodel import SQLModel, create_engine

    eng = create_engine(f"sqlite:///{tmp_path/'t.db'}")
    monkeypatch.setattr(dbmod, "engine", eng)
    SQLModel.metadata.create_all(eng)

    a = dbmod.Lead(source="s", external_id="e1", title="t", url="")
    b = dbmod.Lead(source="s", external_id="e1", title="t2", url="")
    c = dbmod.Lead(source="s", external_id="e2", title="t3", url="")
    assert dbmod.save_lead(a) is True
    assert dbmod.save_lead(b) is False
    assert dbmod.save_lead(c) is True
