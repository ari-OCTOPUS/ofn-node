"""Real batch implementation and SIGKILL rehearsal, isolated disk-backed sandbox.

Crash cases use explicitly synthetic fault fixtures. Performance inputs are the
unchanged 3000 real historical events, not synthetic or repeated records.
No production path is opened and no production process is signalled.
"""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import platform
import signal
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parent


def load_snapshot(kind="candidate"):
    path = ROOT / ("candidate/octopus_sensorium/snapshot.py" if kind == "candidate" else "original/snapshot.py")
    spec = importlib.util.spec_from_file_location("snapshot_" + kind, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def write_receipt(path, value):
    with path.open("w", encoding="utf-8") as handle:
        json.dump(value, handle)
        handle.flush()
        os.fsync(handle.fileno())


def worker(case, directory):
    snap = load_snapshot()
    original_write, original_fsync = snap.os.write, snap.os.fsync
    writes = 0
    def pause(stage):
        (directory / "reached.txt").write_text(stage, encoding="utf-8")
        while True:
            time.sleep(.02)
    def instrumented_write(fd, data):
        nonlocal writes
        writes += 1
        if case == "mid-record" and writes == 51:
            original_write(fd, data[:len(data)//2])
            pause("partial record 51, no batch acknowledgment")
        result = original_write(fd, data)
        if case == "mid-batch" and writes == 50:
            pause("50 complete records, no batch acknowledgment")
        return result
    def instrumented_fsync(fd):
        if case == "before-fsync":
            pause("100 complete records, zero successful fsync")
        return original_fsync(fd)
    snap.os.write = instrumented_write
    snap.os.fsync = instrumented_fsync
    records = [{"kind": "invalid_obs", "sensor_id": "SYNTHETIC-CRASH-FIXTURE", "fixture_index": n} for n in range(100)]
    acknowledged = snap.append_events(records, directory / "events.jsonl")
    snap.os.write, snap.os.fsync = original_write, original_fsync
    write_receipt(directory / "ack.json", {"seqs": [r["seq"] for r in acknowledged]})
    pause("batch fsync and caller acknowledgment completed")


def crash_case(case, output):
    directory = output / case
    directory.mkdir()
    child = subprocess.Popen([sys.executable, str(Path(__file__).resolve()), "--worker", case, "--directory", str(directory)])
    deadline = time.monotonic() + 10
    try:
        while not (directory / "reached.txt").exists():
            if child.poll() is not None:
                raise RuntimeError(f"worker exited unexpectedly {child.returncode}")
            if time.monotonic() > deadline:
                raise TimeoutError("worker barrier timeout")
            time.sleep(.01)
        child.kill()  # SIGKILL for this exact child PID on Linux.
        code = child.wait(timeout=5)
    finally:
        if child.poll() is None:
            child.kill()
            child.wait(timeout=5)
    snap = load_snapshot()
    journal = directory / "events.jsonl"
    data = journal.read_bytes()
    records = snap.load_events(journal)
    ack = json.loads((directory / "ack.json").read_text()) if (directory / "ack.json").exists() else {"seqs": []}
    seqs = [r["seq"] for r in records]
    assert code == -signal.SIGKILL, code
    assert seqs == list(range(1, len(seqs)+1))
    assert not set(ack["seqs"]) - set(seqs), "ACKed event missing"
    restart_refused = None
    if case == "mid-record":
        before = hashlib.sha256(data).hexdigest()
        try:
            snap.append_event({"kind": "invalid_obs"}, journal)
        except snap.JournalWriteError:
            restart_refused = True
        else:
            restart_refused = False
        assert restart_refused and hashlib.sha256(journal.read_bytes()).hexdigest() == before
    return {"case": case, "worker_returncode": code, "barrier": (directory / "reached.txt").read_text(),
            "replayable_records": len(records), "acknowledged_records": len(ack["seqs"]),
            "acknowledged_missing": len(set(ack["seqs"]) - set(seqs)), "ends_with_newline": data.endswith(b"\n"),
            "torn_tail_restart_refused_without_rewrite": restart_refused, "journal_sha256": hashlib.sha256(data).hexdigest()}


def benchmark(output):
    fixture = ROOT / "original/benchmark-events.jsonl"
    records = [json.loads(line) for line in fixture.read_text().splitlines()]
    records = [{k: v for k, v in row.items() if k != "seq"} for row in records]
    variants = []
    for kind, batch in (("original", 1), ("candidate", 1), ("candidate", 100)):
        snap = load_snapshot(kind)
        destination = output / f"{kind}-batch{batch}.jsonl"
        calls = 0
        real_fsync = snap.os.fsync
        def counted_fsync(fd):
            nonlocal calls
            calls += 1
            return real_fsync(fd)
        snap.os.fsync = counted_fsync
        start = time.perf_counter()
        try:
            for index in range(0, len(records), batch):
                if batch == 1:
                    snap.append_event(records[index], destination)
                else:
                    snap.append_events(records[index:index+batch], destination)
        finally:
            snap.os.fsync = real_fsync
        wall = time.perf_counter() - start
        variants.append({"source": kind, "batch_size": batch, "wall_seconds": wall, "events": len(records),
                         "real_fsync_calls": calls, "journal_sha256": hashlib.sha256(destination.read_bytes()).hexdigest(),
                         "replay_state_hash": snap.state_hash(snap.replay(destination))})
    assert len({v["journal_sha256"] for v in variants}) == 1
    assert len({v["replay_state_hash"] for v in variants}) == 1
    return {"fixture_sha256": hashlib.sha256(fixture.read_bytes()).hexdigest(), "fixture_kind": "real historical 3000-event benchmark fixture", "variants": variants,
            "limitation": "one run each on node100 filesystem; not node182 service throughput, memory acceptance, or batching consumer integration"}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--worker")
    parser.add_argument("--directory", type=Path)
    args = parser.parse_args()
    if args.worker:
        worker(args.worker, args.directory)
        return
    output = ROOT / "linux-run-01"
    output.mkdir()  # refuse accidental overwrite of earlier receipts
    result = {"at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "platform": platform.platform(),
              "source_hashes": {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in (ROOT / "candidate/octopus_sensorium").glob("*.py")},
              "crash_cases": [crash_case(case, output) for case in ("mid-batch", "mid-record", "before-fsync", "after-ack")],
              "benchmark": benchmark(output),
              "power_loss_durability": "NOT_TESTED: SIGKILL leaves kernel page cache intact",
              "runtime_batch_integration": "NOT_IMPLEMENTED: live app remains append_event with one event/fsync",
              "full_replica_boot": "NOT_RUN", "t_plus_1h_rss": "NOT_RUN"}
    write_receipt(output / "RESULT.json", result)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
