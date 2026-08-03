#!/usr/bin/env python3
"""تستِ رفتاریِ فاز۱b: اتصالِ checkpoint به unified_bus.

گپ: checkpoint.py ساخته+تست‌شده بود ولی unified_bus._checkpoint آن را duplicate
می‌کرد (نوشتن به duration_marker به‌جای جدولِ checkpoint اصلی). حالا _checkpoint
به checkpoint.checkpoint() delegate می‌کند (قراردادِ testable).

اثبات:
  (الف) unified_bus.publish → checkpoint.checkpoint نوشته می‌شود در جدولِ checkpoint.
  (ب) checkpoint.checkpoint روی db واقعی کار می‌کند (نه فقط stub).
  (ج) checkpoint.py دیگر shelfware نیست (از unified_bus قابل‌رسیدن است).
  (د) fail-soft: بدونِ db → False (ولی ledger source of truth).
$0 آفلاین.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import harness  # noqa: E402
ENV = harness.setup("checkpoint-wiring")

_OPS = (harness.SELF_OPS)
for _p in [str(_OPS), str(_OPS / "budget")]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

import chrono  # noqa: E402
import checkpoint  # noqa: E402


# ════════════════════════════════════════════════════════════════════════════════
# (الف) checkpoint.checkpoint روی db واقعی
# ════════════════════════════════════════════════════════════════════════════════

def t_checkpoint_writes_to_db():
    """checkpoint.checkpoint باید ردیفی در جدولِ checkpoint بنویسد."""
    db = chrono.ChronoDB(ENV["ops"] / "state" / "chrono-cp.db")
    ok = checkpoint.checkpoint(beat=42, hlc=(100, 5), ledger_hash="abc123",
                               db=db, snapshot={"type": "TEST"})
    assert ok is True
    row = db.q("SELECT beat_id, ledger_hash FROM checkpoint WHERE beat_id=?", (42,))
    assert row and row[0][0] == 42 and row[0][1] == "abc123"


def t_checkpoint_no_db_returns_false():
    """بدونِ db → False (fail-soft، ولی ledger source of truth)."""
    assert checkpoint.checkpoint(beat=1, hlc=(0, 0), ledger_hash="x", db=None) is False


# ════════════════════════════════════════════════════════════════════════════════
# (ب) unified_bus._checkpoint به checkpoint.checkpoint delegate می‌کند
# ════════════════════════════════════════════════════════════════════════════════

def test_unified_bus_delegates_to_checkpoint():
    """unified_bus._checkpoint باید به checkpoint.checkpoint delegate کند (نه inline DDL)."""
    src = (_OPS / "unified_bus.py").read_text("utf-8")
    assert "import checkpoint" in src or "from checkpoint" in src, \
        "unified_bus باید checkpoint را import کند (delegate، نه duplicate DDL)"
    # نباید inline DDL به duration_marker داشته باشد (duplicate حذف شد)
    bus_cp_idx = src.find("def _checkpoint")
    block = src[bus_cp_idx:bus_cp_idx + 700]
    assert "duration_marker" not in block, \
        "duplicate DDL به duration_marker باید حذف شود — delegate به checkpoint.checkpoint"


def test_unified_bus_publish_creates_checkpoint():
    """unified_bus.publish (با db) → checkpoint در جدولِ checkpoint نوشته می‌شود."""
    db = chrono.ChronoDB(ENV["ops"] / "state" / "chrono-cp2.db")
    # UnifiedBus با db واقعی
    sys.path.insert(0, str(_OPS))
    from unified_bus import UnifiedBus
    # ledger mock: append باید entry برگرداند
    class _MockLedger:
        def append(self, etype, payload, actor="system", is_human=False, beat=False):
            return {"type": etype, "payload": payload, "actor": actor,
                    "is_human": 1 if is_human else 0, "hash": "mockhash001",
                    "ts": "2026-07-09T00:00:00Z"}
        def filter(self, event_type=None):
            return []
    bus = UnifiedBus(ledger=_MockLedger(), db=db)
    bus.publish("NOTE", {"test": True}, actor="test")
    # باید چیزی در جدولِ checkpoint نوشته شده باشد
    rows = db.q("SELECT COUNT(*) FROM checkpoint")
    assert rows[0][0] >= 1, "publish باید checkpoint بنویسد"


# ════════════════════════════════════════════════════════════════════════════════
# (ج) replay از ledger (source of truth)
# ════════════════════════════════════════════════════════════════════════════════

def test_replay_from_ledger():
    """checkpoint.replay از ledger می‌آید (نه chrono cache). reconstructable."""
    class _MockLedger:
        def __init__(self):
            self._recs = [{"type": "NOTE", "ts": "2026-07-09", "actor": "a", "hash": "h1"},
                          {"type": "NOTE", "ts": "2026-07-10", "actor": "b", "hash": "h2"}]
        def filter(self, event_type=None):
            if event_type:
                return [r for r in self._recs if r["type"] == event_type]
            return list(self._recs)
    out = checkpoint.replay(ledger=_MockLedger())
    assert len(out) == 2


if __name__ == "__main__":
    failed = harness.run([
        ("checkpoint روی db واقعی", t_checkpoint_writes_to_db),
        ("بدونِ db → False", t_checkpoint_no_db_returns_false),
        ("unified_bus delegate می‌کند (structural)", test_unified_bus_delegates_to_checkpoint),
        ("publish → checkpoint نوشته", test_unified_bus_publish_creates_checkpoint),
        ("replay از ledger", test_replay_from_ledger),
    ])
    sys.exit(1 if failed else 0)
