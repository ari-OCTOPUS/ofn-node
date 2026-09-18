"""Paired tests for the compute-worker `test_shard` profile (RUN-TO-COMPLETION item 5).

Source of truth: state/fleet-compute/compute_worker.py (deployed to
/usr/local/bin on every fleet node). These hold the profile contract: the
allowlist entry, param validation, disjoint-and-covering shard math, and a
real mini-suite execution slice. Runs on any host with pytest — including the
fleet workers themselves, where the suite shards across nodes.
"""
import importlib.util
import time
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
WORKER = REPO / "state" / "fleet-compute" / "compute_worker.py"


@pytest.fixture(scope="module")
def worker():
    spec = importlib.util.spec_from_file_location("compute_worker_under_test", WORKER)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _task(**over):
    task = {
        "schema": "compute_task.v1", "task_id": "t-testshard-1",
        "profile": "test_shard",
        "params": {"root": "/srv/octopus-compute/ofn-suite",
                   "shard_index": 0, "shard_count": 6},
        "input_digest": "x" * 64, "resource_class": "cpu_batch",
        "max_seconds": 100, "external_effects": 0, "customer_send": False,
    }
    task.update(over)
    return task


class TestRegistry:
    def test_profile_registered(self, worker):
        assert "test_shard" in worker.PROFILES

    def test_spec_gates(self, worker):
        spec = worker.PROFILES["test_shard"]
        assert spec["resource_class"] == "cpu_batch"
        assert spec["max_seconds"] >= 100
        assert set(spec["params"]) == {"root", "shard_index", "shard_count", "pylib"}


class TestValidation:
    def test_valid_envelope_accepted(self, worker):
        ok, err = worker.validate_task(_task())
        assert ok, err

    def test_unknown_param_refused(self, worker):
        task = _task()
        task["params"]["evil"] = "rm -rf"
        ok, err = worker.validate_task(task)
        assert not ok and err == "PARAM_NOT_ALLOWED"

    def test_index_out_of_range_refused(self, worker):
        task = _task(params={"root": "/srv/octopus-compute/ofn-suite",
                             "shard_index": 9, "shard_count": 6})
        ok, err = worker.validate_task(task)
        assert not ok and err == "SHARD_INDEX_GE_COUNT"

    def test_bool_index_refused(self, worker):
        task = _task(params={"root": "/srv/octopus-compute/ofn-suite",
                             "shard_index": True, "shard_count": 6})
        ok, err = worker.validate_task(task)
        assert not ok and err == "PARAM_TYPE"


class TestShardMath:
    IDS = [f"tests/test_x.py::t{i}" for i in range(10)]

    def test_shards_cover_and_are_disjoint(self, worker):
        picked = [worker._shard_ids(self.IDS, i, 3) for i in range(3)]
        flat = sorted(x for shard in picked for x in shard)
        assert flat == sorted(self.IDS)
        assert len(flat) == len(set(flat)) == len(self.IDS)

    @pytest.mark.parametrize("i,n", [(-1, 3), (3, 3), (5, 2)])
    def test_out_of_range_raises(self, worker, i, n):
        with pytest.raises(ValueError):
            worker._shard_ids(self.IDS, i, n)


def _make_mini_suite(tmp_path):
    suite = tmp_path / "mini"
    (suite / "tests").mkdir(parents=True)
    (suite / "pytest.ini").write_text("[pytest]\ntestpaths = tests\n", encoding="utf-8")
    (suite / "tests" / "test_a.py").write_text(
        "def test_a1():\n    assert 1\n\n\ndef test_a2():\n    assert 2\n\n\ndef test_a3():\n    assert 3\n",
        encoding="utf-8")
    (suite / "tests" / "test_b.py").write_text(
        "def test_b1():\n    assert 1\n\n\ndef test_b2():\n    assert 2\n",
        encoding="utf-8")
    return suite


class TestRealRun:
    def test_mini_suite_slice_executes(self, worker, tmp_path):
        suite = _make_mini_suite(tmp_path)
        ctx = {"allowed_roots": (str(tmp_path),), "profile": "test_shard",
               "max_seconds": 60, "deadline_mono": time.monotonic() + 60}
        res = worker._work_test_shard(
            {"root": str(suite), "shard_index": 0, "shard_count": 2}, ctx)
        # sorted collection: a1,a2,a3,b1,b2 -> [0::2] = a1,a3,b1
        assert res["collected"] == 5
        assert res["selected"] == 3
        assert res["pytest_rc"] == 0
        assert "3 passed" in res["summary"]

    def test_tolerates_wallclock_deadline_ctx(self, worker, tmp_path):
        # run_task builds ctx["deadline_mono"] from time.time() (wall clock,
        # despite the name). The workload must not feed that base into
        # subprocess timeouts — live failure 2026-09-18:
        # OverflowError("timeout is too large"), task-f09a28425d3e574c a2.
        suite = _make_mini_suite(tmp_path)
        ctx = {"allowed_roots": (str(tmp_path),), "profile": "test_shard",
               "max_seconds": 60, "deadline_mono": time.time() + 60}
        res = worker._work_test_shard(
            {"root": str(suite), "shard_index": 1, "shard_count": 2}, ctx)
        assert res["pytest_rc"] == 0
        assert "2 passed" in res["summary"]

    def test_root_outside_allowed_refused(self, worker, tmp_path):
        ctx = {"allowed_roots": (str(tmp_path),), "profile": "test_shard",
               "max_seconds": 5, "deadline_mono": time.monotonic() + 5}
        with pytest.raises(PermissionError):
            worker._work_test_shard(
                {"root": "/etc", "shard_index": 0, "shard_count": 2}, ctx)
