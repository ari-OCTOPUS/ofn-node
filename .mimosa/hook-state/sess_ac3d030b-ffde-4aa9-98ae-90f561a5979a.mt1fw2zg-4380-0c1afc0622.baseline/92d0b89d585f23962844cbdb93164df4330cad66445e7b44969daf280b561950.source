"""Regression tests for the review/bugfix pass. Offline, stdlib. Exit 0 = pass.

Covers the seven fixes:
  1 ledger concurrency (parallel appends keep the hash chain intact)
  2 ledger reader tolerates a torn line
  3 guardian budget gate is LIVE (sums today's llm_cost_usd)
  4 guardian backup-age is REAL (computed from the last backup event's ts)
  5 guardian reused instance still HALTs on genome tamper
  6 indexer is thread-safe (index from another thread, no sqlite thread error)
  7 doctor ignores its own past reports when adjudicating
"""
from __future__ import annotations

import json
import shutil
import sys
import tempfile
import threading
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for sub in ("ledger", "common", "perception", "agents"):
    sys.path.insert(0, str(ROOT / sub))

from config import Genome            # noqa: E402
from ledger import Ledger           # noqa: E402
from indexer import Indexer         # noqa: E402
from guardian import Guardian       # noqa: E402
from creativity import Creativity   # noqa: E402
from doctor import Doctor           # noqa: E402


def main() -> int:
    work = Path(tempfile.mkdtemp())

    # 1 + 2) ledger concurrency + torn-line tolerance
    lg_path = work / "ledger.jsonl"
    lg = Ledger(lg_path)

    def spam(tag):
        w = Ledger(lg_path)
        for i in range(20):
            w.append("NOTE", {"t": tag, "i": i}, actor=f"w{tag}")

    threads = [threading.Thread(target=spam, args=(t,)) for t in range(4)]
    [t.start() for t in threads]
    [t.join() for t in threads]
    ok, msg = lg.verify()
    assert ok, f"concurrent appends broke the chain: {msg}"
    assert len(lg.tail(1000)) == 80, f"expected 80 records, got {len(lg.tail(1000))}"
    with open(lg_path, "a", encoding="utf-8") as fh:
        fh.write('{"type":"NOTE","actor":"x","ts":"now"  <torn')   # simulate a crash mid-write
    assert len(lg.filter(event_type="NOTE")) == 80, "torn line should be skipped by readers"
    print("1+2) ledger: 80 concurrent appends, chain intact, torn line tolerated")

    # genome copy for guardian tests
    gdir = work / "genome"
    shutil.copytree(ROOT / "genome", gdir)
    genome = Genome.load(gdir)

    # 3) guardian budget gate is live
    lg3 = Ledger(work / "l3.jsonl")
    lg3.append("METRIC", {"llm_cost_usd": 2.0, "model": "x"}, actor="router")  # > daily_ops (1.0)
    alerts = Guardian(genome, lg3).tick()["alerts"]
    assert any("LLM cost" in a for a in alerts), f"budget gate did not fire: {alerts}"
    print("3) guardian budget gate fires on today's real LLM spend")

    # 4) guardian backup-age is real
    lg4_path = work / "l4.jsonl"
    old_ts = (datetime.now(timezone.utc) - timedelta(hours=30)).isoformat()
    lg4_path.write_text(json.dumps({"type": "METRIC", "actor": "backup", "ts": old_ts,
                                    "payload": {"backup_last_success_age_h": 0},
                                    "meta": {}, "prev": "0" * 64, "id": "seed",
                                    "hash": "seed"}) + "\n", encoding="utf-8")
    alerts4 = Guardian(genome, Ledger(lg4_path)).tick()["alerts"]
    assert any("backup stale" in a for a in alerts4), f"stale-backup alert missing: {alerts4}"
    print("4) guardian backup-age computed from last backup ts (30h -> stale alert)")

    # 5) reused guardian still halts on tamper
    lg5 = Ledger(work / "l5.jsonl")
    guard = Guardian(genome, lg5)
    assert not guard.tick()["halt"], "clean genome should not halt"
    (gdir / "gates.yaml").write_text("tampered: true\n", encoding="utf-8")
    assert guard.tick()["halt"], "reused guardian must halt after tamper"
    print("5) reused guardian halts on genome tamper (baseline fixed at start)")

    # 6) indexer thread-safety
    ix = Indexer(work / "ix.db")
    f = work / "note.md"; f.write_text("threaded index note\n", encoding="utf-8")
    result = {}
    th = threading.Thread(target=lambda: result.update(r=ix.index_file(f)))
    th.start(); th.join()
    assert result.get("r") == "indexed", f"threaded index failed: {result}"
    assert ix.search("threaded"), "threaded-indexed file not searchable"
    print("6) indexer usable from a background thread (check_same_thread=False + lock)")

    # 7) doctor ignores its own past reports
    lg7 = Ledger(work / "l7.jsonl")
    Creativity(lg7).propose(topic="cost")          # 1 real proposal
    doc = Doctor(genome, lg7)
    doc.run()                                       # writes a doctor_report PROPOSAL
    doc.run()                                       # must NOT re-adjudicate that report
    assert len(doc._open_proposals()) == 1, \
        f"doctor should see 1 open proposal, saw {len(doc._open_proposals())}"
    print("7) doctor adjudicates only real proposals, not its own reports")

    print("\nPASS: all review/bugfix regressions green.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
