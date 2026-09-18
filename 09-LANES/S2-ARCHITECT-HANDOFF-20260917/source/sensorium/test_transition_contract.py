"""Exact-source component rehearsal; external board/bus dependencies are stubs.

This intentionally does not claim a booted replica or a complete service test.
Set S1_SOURCE=original to demonstrate the pre-existing faults with the same tests.
"""
import ast
import asyncio
import importlib.util
import json
import logging
import os
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

ROOT = Path(__file__).parent
SOURCE = ROOT / ("original" if os.environ.get("S1_SOURCE") == "original" else "candidate/octopus_sensorium")
spec = importlib.util.spec_from_file_location("s1_snapshot", SOURCE / "snapshot.py")
snap = importlib.util.module_from_spec(spec)
spec.loader.exec_module(snap)


class PipelineError(Exception):
    stage = "validate"
    message = "bad observation fixture"


class SensorError(Exception):
    pass


async def nothing(*args, **kwargs):
    return None


@pytest.fixture
def rig(tmp_path):
    journal = tmp_path / "events.jsonl"
    tree = ast.parse((SOURCE / "app.py").read_text(encoding="utf-8"))
    cls = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == "SensoriumApp")
    module = ast.Module(body=[ast.ImportFrom(module="__future__", names=[ast.alias(name="annotations")], level=0), cls], type_ignores=[])
    env = {
        "append_event": lambda event: snap.append_event(event, journal),
        "JournalWriteError": getattr(snap, "JournalWriteError", OSError),
        "PipelineError": PipelineError, "SensorError": SensorError,
        "persist_observation": Mock(), "persist_quarantine": Mock(),
        "LOG": logging.getLogger("s1-test"),
        "assert_no_sensor_id_collision": Mock(),
        "is_runtime_enabled": lambda spec: True,
        "reject_actuator_manifest": Mock(),
        "PluginState": SimpleNamespace(DISCOVERED="discovered", QUARANTINED="quarantine", VERIFIED="verified"),
    }
    exec(compile(ast.fix_missing_locations(module), str(SOURCE / "app.py"), "exec"), env)
    app = env["SensoriumApp"].__new__(env["SensoriumApp"])
    app.health = {}
    app.observations_published = 0
    app.invalid_observations = 0
    app.observation_hashes = []
    app.recent = []
    app.plugins = {}
    app.audit = SimpleNamespace(append=Mock())
    app.lifecycle = SimpleNamespace(mark=Mock())
    app.metrics = SimpleNamespace(sensorium_observations_total=0, observations_published=0, drop=Mock())
    app._publish = nothing
    app._feed_meta = nothing
    app._quarantine_record = Mock()
    return app, env, journal


def failing_plugin(error=RuntimeError("sensor unavailable"), failures=2, can_quarantine=True):
    async def observe():
        raise error
        yield  # make an async generator
    return SimpleNamespace(observe=observe, consecutive_failures=failures,
                           manifest={"publication": {"can_quarantine": can_quarantine}})


@pytest.mark.parametrize("failures,quarantine,expected", [(2, True, "degraded"), (9, True, "quarantine"), (9, False, "degraded")])
def test_runtime_failure_transition_replays(rig, failures, quarantine, expected):
    app, env, journal = rig
    env["append_event"]({"kind": "health", "sensor_id": "fixture", "status": "healthy"})
    app.health["fixture"] = "healthy"
    asyncio.run(app._tick_sensor("fixture", failing_plugin(failures=failures, can_quarantine=quarantine)))
    assert app.health["fixture"] == expected
    assert snap.replay(journal)["health"] == app.health


def test_constructor_quarantine_replays(rig):
    app, env, journal = rig
    def refuses(spec):
        raise SensorError("disabled fixture")
    app.registry_doc = {"sensors": [{"sensor_id": "fixture", "plugin": {"type": "refuses"}}]}
    env["PLUGIN_TYPES"] = {"refuses": refuses}
    app._instantiate_wave1()
    assert snap.replay(journal).get("health") == app.health == {"fixture": "quarantine"}


@pytest.mark.parametrize("status", ["healthy", "unavailable", "degraded", "quarantine"])
def test_each_health_status_committed_once(rig, status):
    app, env, journal = rig
    app._set_health("fixture", status)
    app._set_health("fixture", status)
    assert snap.replay(journal)["health"] == app.health
    assert len(snap.load_events(journal)) == 1


def test_health_commit_failure_keeps_projection(rig):
    app, env, journal = rig
    app.health["fixture"] = "healthy"
    env["append_event"] = Mock(side_effect=getattr(snap, "JournalWriteError", OSError)("full"))
    with pytest.raises(OSError):
        asyncio.run(app._tick_sensor("fixture", failing_plugin()))
    assert app.health == {"fixture": "healthy"}


def test_observation_append_failure_does_not_mutate_projection(rig):
    app, env, journal = rig
    env["append_event"] = Mock(side_effect=getattr(snap, "JournalWriteError", OSError)("full"))
    with pytest.raises(OSError):
        asyncio.run(app._emit("fixture", {"provenance": {"content_hash": "sha256:fixture"}}))
    assert (app.observation_hashes, app.observations_published, app.recent) == ([], 0, [])


@pytest.mark.parametrize("failure_site", ["persist", "publish", "meta"])
def test_committed_observation_remains_replayable_on_downstream_failure(rig, failure_site):
    app, env, journal = rig
    async def fails(*args):
        # At the first await, the live projection must already equal the journal.
        assert snap.replay(journal)["observations_published"] == app.observations_published
        raise OSError("downstream unavailable")
    if failure_site == "persist":
        env["persist_observation"] = Mock(side_effect=OSError("evidence disk full"))
    elif failure_site == "publish":
        app._publish = fails
    else:
        app._feed_meta = fails
    with pytest.raises(OSError):
        asyncio.run(app._emit("fixture", {"provenance": {"content_hash": "sha256:fixture"}}))
    state = snap.replay(journal)
    assert state["observations_published"] == app.observations_published == 1
    assert state["observation_hashes"] == app.observation_hashes


def test_invalid_observation_append_failure_does_not_advance_counter(rig):
    app, env, journal = rig
    app.health["fixture"] = "healthy"
    env["append_event"] = Mock(side_effect=getattr(snap, "JournalWriteError", OSError)("full"))
    with pytest.raises(OSError):
        asyncio.run(app._tick_sensor("fixture", failing_plugin(PipelineError())))
    assert app.invalid_observations == 0
    env["persist_quarantine"].assert_not_called()


def test_invalid_observation_commit_replays_after_audit_failure(rig):
    app, env, journal = rig
    app.health["fixture"] = "healthy"
    app.audit.append = Mock(side_effect=OSError("audit full"))
    with pytest.raises(OSError):
        asyncio.run(app._tick_sensor("fixture", failing_plugin(PipelineError())))
    assert snap.replay(journal).get("invalid_observations") == app.invalid_observations == 1


def test_short_writes_are_completed(tmp_path, monkeypatch):
    journal = tmp_path / "short.jsonl"
    real_write = snap.os.write
    monkeypatch.setattr(snap.os, "write", lambda fd, data: real_write(fd, data[:7]))
    snap.append_event({"kind": "health", "sensor_id": "fixture", "status": "degraded"}, journal)
    assert snap.replay(journal)["health"] == {"fixture": "degraded"}


def test_zero_write_is_fatal(tmp_path, monkeypatch):
    monkeypatch.setattr(snap.os, "write", lambda fd, data: 0)
    with pytest.raises(OSError):
        snap.append_event({"kind": "invalid_obs"}, tmp_path / "zero.jsonl")


def test_fsync_failure_is_typed_and_not_acknowledged(tmp_path, monkeypatch):
    monkeypatch.setattr(snap.os, "fsync", Mock(side_effect=OSError("sync failed")))
    with pytest.raises(getattr(snap, "JournalWriteError", OSError)):
        snap.append_event({"kind": "invalid_obs"}, tmp_path / "sync.jsonl")


def test_caller_cannot_rewind_journal_sequence(tmp_path):
    journal = tmp_path / "seq.jsonl"
    snap.append_event({"kind": "invalid_obs", "seq": -2}, journal)
    snap.append_event({"kind": "invalid_obs", "seq": -2}, journal)
    assert [e["seq"] for e in snap.load_events(journal)] == [1, 2]


def test_torn_tail_refuses_append_and_preserves_bytes(tmp_path):
    journal = tmp_path / "torn.jsonl"
    before = b'{"seq":1,"kind":"invalid_obs"}\n{"seq":2'
    journal.write_bytes(before)
    with pytest.raises(OSError):
        snap.append_event({"kind": "invalid_obs"}, journal)
    assert journal.read_bytes() == before


def test_batch_fsyncs_once_including_partial_final_batch(tmp_path, monkeypatch):
    journal = tmp_path / "batch.jsonl"
    real_fsync = snap.os.fsync
    calls = []
    def counted(fd):
        calls.append(fd)
        return real_fsync(fd)
    monkeypatch.setattr(snap.os, "fsync", counted)
    acknowledged = snap.append_events([{"kind": "invalid_obs"}] * 3, journal)
    assert len(calls) == 1
    assert [r["seq"] for r in acknowledged] == [1, 2, 3]
    assert snap.replay(journal)["invalid_observations"] == 3


def test_batch_serialization_failure_writes_nothing(tmp_path):
    journal = tmp_path / "invalid-batch.jsonl"
    with pytest.raises(TypeError):
        snap.append_events([{"kind": "invalid_obs"}, {"unserializable": object()}], journal)
    assert not journal.exists()


def test_oversized_batch_rejected_before_writes(tmp_path):
    journal = tmp_path / "oversized.jsonl"
    with pytest.raises(ValueError):
        snap.append_events([{"kind": "invalid_obs"}] * 101, journal)
    assert not journal.exists()


def test_no_direct_health_transition_outside_single_helper():
    tree = ast.parse((SOURCE / "app.py").read_text(encoding="utf-8"))
    writes = []
    for method in ast.walk(tree):
        if isinstance(method, (ast.FunctionDef, ast.AsyncFunctionDef)):
            for node in ast.walk(method):
                if isinstance(node, (ast.Assign, ast.AnnAssign, ast.AugAssign)):
                    targets = node.targets if isinstance(node, ast.Assign) else [node.target]
                    for target in targets:
                        if isinstance(target, ast.Subscript) and ast.unparse(target.value) == "self.health":
                            writes.append((method.name, node.lineno))
    assert len(writes) == 1 and writes[0][0] == "_set_health", writes


def test_durability_error_bypasses_tick_and_forever_catchall():
    tree = ast.parse((SOURCE / "app.py").read_text(encoding="utf-8"))
    for name in ("_tick_sensor", "run_forever"):
        method = next(n for n in ast.walk(tree) if isinstance(n, ast.AsyncFunctionDef) and n.name == name)
        handlers = [n for n in ast.walk(method) if isinstance(n, ast.ExceptHandler) and n.type is not None]
        typed = [h for h in handlers if ast.unparse(h.type) == "JournalWriteError"]
        assert typed and isinstance(typed[0].body[0], ast.Raise), name
