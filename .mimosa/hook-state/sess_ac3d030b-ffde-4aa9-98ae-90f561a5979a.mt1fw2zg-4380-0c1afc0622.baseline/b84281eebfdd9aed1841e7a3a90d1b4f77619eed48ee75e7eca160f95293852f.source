"""End-to-end integration test (offline, no API key needed).

Wires the whole system together and asserts the safety contracts hold:
  perception -> ledger -> creativity (propose-only) -> doctor (adjudicate) ,
  plus Guardian heartbeat + genome-tamper HALT + the watcher event logic.

Run:  python tests/integration_test.py     (needs: PyYAML; watchdog optional)
Exit 0 = pass.
"""
from __future__ import annotations

import shutil
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for sub in ("ledger", "common", "perception", "agents"):
    sys.path.insert(0, str(ROOT / sub))

from config import Genome            # noqa: E402
from ledger import Ledger           # noqa: E402
from indexer import Indexer         # noqa: E402
import watcher                       # noqa: E402
from guardian import Guardian       # noqa: E402
from creativity import Creativity   # noqa: E402
from doctor import Doctor           # noqa: E402


def main() -> int:
    work = Path(tempfile.mkdtemp())
    genome_dir = work / "genome"
    shutil.copytree(ROOT / "genome", genome_dir)     # tamperable copy
    vault = work / "vault"; vault.mkdir()
    (vault / "a.md").write_text("# note\nevent-driven beats polling\n", encoding="utf-8")
    (vault / "b.md").write_text("backup and disaster recovery matter\n", encoding="utf-8")

    genome = Genome.load(genome_dir)
    ledger = Ledger(work / "ledger.jsonl")
    indexer = Indexer(work / "index.db")

    # 1) perception: reconcile + search
    stats = watcher.reconcile(vault, indexer, ledger)
    assert stats["indexed"] == 2, stats
    assert indexer.search("polling"), "search returned nothing"
    print("1) perception: indexed 2, search works, fts5 =", indexer.stats()["fts5"])

    # 2) creativity: propose-only, humility contract enforced
    prop = Creativity(ledger, vault).propose(topic="cost")
    assert prop["type"] == "PROPOSAL" and prop["actor"] == "creativity"
    assert prop["payload"]["kill_criteria"], "kill_criteria must be present"
    assert 0.0 <= prop["payload"]["confidence"] <= 1.0
    try:
        Creativity(ledger).propose(llm_fn=lambda c: {
            "idea": "x", "why_it_might_be_genius": "y", "why_it_might_be_insane": "z",
            "confidence": 2.0, "kill_criteria": "", "smallest_test": "t", "reversible": True})
        print("FAIL: empty kill_criteria was accepted"); return 1
    except ValueError:
        pass
    print("2) creativity: PROPOSAL written; empty kill-criteria correctly rejected")

    # 3) guardian: heartbeat, then genome tamper -> HALT
    guard = Guardian(genome, ledger)
    r1 = guard.tick(uptime_s=1.0)
    assert not r1["halt"], "clean genome should not halt"
    (genome_dir / "gates.yaml").write_text("tampered: true\n", encoding="utf-8")
    r2 = guard.tick(uptime_s=2.0)
    assert r2["halt"], "genome tamper must halt"
    assert any("TAMPERED" in a for a in r2["alerts"])
    abort, why = guard.check_run(steps=999, cost_usd=0.0)
    assert abort and "steps" in why, "loop-guard should abort runaway step count"
    print("3) guardian: heartbeat ok; genome tamper -> HALT; loop-guard fires")

    # 4) doctor: health report + propose-only adjudication (never applies)
    report = Doctor(genome, ledger).run()
    assert "Health" in report and "Proposals adjudicated" in report
    applied = [e for e in ledger.iter_events() if e["type"] == "APPLY"]
    assert not applied, "no agent may APPLY -- propose-only invariant"
    print("4) doctor: report generated; zero APPLY events (propose-only holds)")

    # 5) watcher event logic (deterministic, no watchdog needed)
    live_ix = Indexer(work / "live.db"); live_lg = Ledger(work / "live.jsonl")
    live_vault = work / "live"; live_vault.mkdir()
    f = live_vault / "new.md"; f.write_text("freshly created note\n", encoding="utf-8")
    assert watcher.handle_event(live_ix, live_lg, str(f), "created") == "indexed"
    assert live_ix.search("freshly"), "created file not searchable"
    f.write_text("freshly EDITED note\n", encoding="utf-8")
    assert watcher.handle_event(live_ix, live_lg, str(f), "modified") == "reindexed"
    assert watcher.handle_event(live_ix, live_lg, str(f), "deleted") == "removed"
    assert not live_ix.search("freshly"), "deleted file still indexed"
    assert watcher.handle_event(live_ix, live_lg, str(live_vault / "x.png"), "created") == "ignored"
    print("5) watcher(logic): create/modify/delete + allowlist all correct")

    # 5b) optional live OS-event round-trip, only if watchdog is installed
    try:
        import threading
        from watchdog.observers import Observer  # noqa: F401
        lv = work / "live2"; lv.mkdir()
        ix2 = Indexer(work / "live2.db"); lg2 = Ledger(work / "live2.jsonl")
        threading.Thread(target=watcher.watch, args=(lv, ix2, lg2, 0.2), daemon=True).start()
        time.sleep(0.8)
        (lv / "n.md").write_text("os event note\n", encoding="utf-8")
        seen = False
        for _ in range(25):
            if ix2.search("event"):
                seen = True; break
            time.sleep(0.1)
        print("5b) watcher(live OS event):", "indexed via OS event" if seen else "no event seen")
    except ImportError:
        print("5b) watcher(live OS event): skipped (watchdog offline in this sandbox)")

    ok, msg = ledger.verify()
    assert ok, f"ledger chain broke: {msg}"
    print("\nPASS: full pipeline green; ledger hash-chain intact.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
