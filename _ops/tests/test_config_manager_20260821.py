#!/usr/bin/env python3
"""Wave B — ConfigManager semantics (owner order 2026-08-21).

Proves:
- boot reads once; reload only on content digest change (generation)
- consumers receive immutable snapshots (mutation never reaches the cache)
- last-known-good + stale=true on stall; malformed never replaces LKG
- bounded read path (reader returning None = stall) never blocks
- mission sweep uses bounded_json_read (no raw read_text in hot loop)
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
import time
from pathlib import Path

_OPS = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_OPS))
sys.path.insert(0, str(_OPS / "telegram_center"))
sys.path.insert(0, str(_OPS / "tests"))

import harness  # noqa: E402
ENV = harness.setup("wave-b-config-manager")
_STATE = Path(tempfile.mkdtemp(prefix="wave-b-config-"))
os.environ["OCTOPUS_STATE_DIR"] = str(_STATE / "_ops" / "state")

from config_manager import ConfigManager, bounded_json_read  # noqa: E402


def _write(path: Path, cfg: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(cfg, ensure_ascii=False, indent=2), "utf-8")


def test_boot_reads_once_and_reload_only_on_digest_change():
    p = _STATE / "telegram" / "center-config.json"
    _write(p, {"a": 1, "last_offset": 10})
    reads = []
    def reader(path):
        reads.append(path.name)
        return path.read_text("utf-8")
    cm = ConfigManager(p, reader=reader)
    snap = cm.boot()
    assert snap == {"a": 1, "last_offset": 10}
    # untouched file: reload must not even read (stat generation unchanged)
    before = len(reads)
    snap2 = cm.reload()
    assert snap2 == {"a": 1, "last_offset": 10}
    assert len(reads) == before, "unchanged generation must skip the read"
    # same content, new mtime: one bounded read happens, but state is NOT
    # reloaded (digest identical) — no parse/state churn
    time.sleep(0.05)
    _write(p, {"a": 1, "last_offset": 10})
    before = len(reads)
    snap3 = cm.reload()
    assert snap3 == {"a": 1, "last_offset": 10}
    assert len(reads) == before + 1, "touched file is read once (bounded)"
    # changed content: digest differs -> state reloads
    _write(p, {"a": 1, "last_offset": 11})
    snap4 = cm.reload()
    assert snap4["last_offset"] == 11


def test_immutable_snapshot():
    p = _STATE / "telegram" / "immutable.json"
    _write(p, {"k": "v"})
    cm = ConfigManager(p)
    cm.boot()
    snap = cm.get()
    snap["k"] = "MUTATED"
    assert cm.get()["k"] == "v", "consumer mutation must never reach cache"
    # reload still serves the cached truth
    assert cm.reload()["k"] == "v"


def test_malformed_never_replaces_lkg():
    p = _STATE / "telegram" / "malformed.json"
    _write(p, {"good": True})
    cm = ConfigManager(p)
    cm.boot()
    assert cm.get()["good"] is True
    # malformed write on disk
    p.write_text("{not valid json!!", "utf-8")
    snap = cm.reload()
    assert snap.get("good") is True, "malformed must never replace last-known-good"
    assert cm.stale is True
    assert cm.last_known_good["good"] is True
    # recovery: valid content returns to fresh
    _write(p, {"good": True, "more": 1})
    snap = cm.reload()
    assert snap["more"] == 1
    assert cm.stale is False


def test_stall_serves_lkg_with_stale():
    p = _STATE / "telegram" / "stall.json"
    _write(p, {"k": "lkg"})
    cm = ConfigManager(p)
    cm.boot()
    assert cm.get() == {"k": "lkg"}
    # the file changes and the bounded reader then stalls (returns None):
    # reload must serve last-known-good with stale=True, never block
    _write(p, {"k": "new-on-disk"})
    cm._reader = lambda path: None
    snap = cm.reload()
    assert snap == {"k": "lkg"}, "stall must serve last-known-good"
    assert cm.stale is True


def test_missing_file_boot_is_empty_stale():
    p = _STATE / "telegram" / "missing.json"
    cm = ConfigManager(p)
    snap = cm.boot()
    assert snap == {}
    assert cm.stale is True


def test_commit_write_through():
    p = _STATE / "telegram" / "commit.json"
    _write(p, {"n": 0})
    cm = ConfigManager(p)
    cm.boot()
    ok = cm.commit({"n": 1, "x": [1, 2]})
    assert ok is True
    assert cm.get()["n"] == 1
    assert cm.digest is not None
    # on-disk matches
    on_disk = json.loads(p.read_text("utf-8"))
    assert on_disk["n"] == 1


def test_observe_write_external():
    p = _STATE / "telegram" / "observe.json"
    _write(p, {"n": 0})
    cm = ConfigManager(p)
    cm.boot()
    # external writer updated the file; center._save_config calls observe_write
    cm.observe_write({"n": 42})
    assert cm.get()["n"] == 42
    assert cm.stale is False


def test_bounded_json_read_mission_sweep():
    # mission-style read: valid -> parsed; malformed -> {}; missing -> {}
    p = _STATE / "missions.json"
    _write(p, {"missions": [{"id": "m1"}]})
    d = bounded_json_read(p)
    assert d["missions"][0]["id"] == "m1"
    p.write_text("broken{", "utf-8")
    assert bounded_json_read(p) == {}
    missing = _STATE / "nope.json"
    assert bounded_json_read(missing) == {}


def main() -> int:
    failed = []
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for fn in tests:
        try:
            fn()
            print(f"  ok  {fn.__name__}")
        except Exception as e:  # noqa: BLE001
            failed.append(fn.__name__)
            print(f"  FAIL {fn.__name__}: {type(e).__name__}: {e}")
    print(f"\n{len(tests) - len(failed)}/{len(tests)} passed")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
