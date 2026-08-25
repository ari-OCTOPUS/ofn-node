from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from ofn.organism.contracts.events import make_event
from ofn.organism.event_kernel.kernel import EventKernel
from ofn.organism.growth.capabilities import (
    CapabilityRegistryError,
    INTERNAL_CAPABILITIES,
    load_registry,
    transition_capabilities,
    validate_registry,
)
from ofn.organism.growth.controlled import (
    ControlledGrowthError,
    engineering_delta_theta,
    run_controlled_growth,
)
from ofn.organism.identity.ledger import ensure_identity_genesis
from ofn.organism.persistence.db import connect
from ofn.organism.runtime.app import _remember_event


LIVE_REGISTRY_FIXTURE = Path(
    "/opt/octopus/lab/artifacts/capability-awakening/02_capability_registry.json"
)


def initial_registry_fixture():
    registry = json.loads(json.dumps(load_registry(LIVE_REGISTRY_FIXTURE)))
    for capability_id, entry in registry["capabilities"].items():
        entry["history"] = [entry["history"][0]]
        entry["state"] = (
            "SHADOW" if capability_id == "ACTIVE_INFERENCE_SHADOW" else "LOCKED"
        )
        entry.pop("quarantined", None)
        entry.pop("quarantine_reason", None)
    registry["phase"] = "LOCKED"
    registry.pop("quarantined", None)
    registry["approval"].update(
        {
            "execution_id": None,
            "used_once": False,
            "expired": False,
            "status": "PREPARED",
        }
    )
    return validate_registry(registry)


class FakeCortex:
    def __init__(self):
        self.calls = 0

    def complete(self, _prompt: str, max_tokens: int = 4):
        self.calls += 1
        return {
            "status": "LOW_CONFIDENCE",
            "http_status": 200,
            "latency_ms": self.calls * 10,
        }


class ControlledGrowthTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.con = connect(Path(self.temp.name) / "organism.db")
        self.addCleanup(self.con.close)
        self.con.execute(
            "INSERT INTO meta(k,v) VALUES('schema_migration_version','phase3-skin-1')"
        )
        ensure_identity_genesis(self.con, "test-boot")
        self.kernel = EventKernel(self.con)
        self.kernel.register("*", lambda event: _remember_event(self.con, event))
        self.env = patch.dict(
            os.environ,
            {
                "OCTOPUS_GET_PURE": "1",
                "OCTOPUS_REQUIRE_LAN_TOKEN": "1",
                "OCTOPUS_LEARN_EXTERNAL": "0",
            },
            clear=False,
        )
        self.env.start()
        self.addCleanup(self.env.stop)
        registry = initial_registry_fixture()
        for target in ("SHADOW", "TESTED", "CANARY"):
            registry = transition_capabilities(registry, target)
            registry["phase"] = target
        registry["approval"].update(
            {
                "execution_id": "test-execution",
                "used_once": True,
                "expired": False,
                "status": "RUNNING",
            }
        )
        self.registry = validate_registry(registry)

    def heartbeat(self, suffix: str) -> str:
        event = make_event(
            "heartbeat",
            {"health": "STABLE", "suffix": suffix},
            priority=15,
        )
        receipt = self.kernel.accept(event)
        self.assertEqual(receipt["status"], "committed")
        self.kernel.replay_pending(limit=20)
        return event["event_id"]

    def run_one(self, heartbeat_id: str, experiment: str, **kwargs):
        return run_controlled_growth(
            self.con,
            self.kernel,
            gate_id="GATE-CONTROLLED-CAPABILITY-AWAKENING-15MIN",
            execution_id="test-execution",
            heartbeat_event_id=heartbeat_id,
            experiment=experiment,
            registry=self.registry,
            watcher_probe=lambda: True,
            **kwargs,
        )

    def test_registry_requires_every_transition_and_keeps_active_inference_shadow(self):
        initial = initial_registry_fixture()
        with self.assertRaises(CapabilityRegistryError):
            transition_capabilities(initial, "TESTED")
        shadow = transition_capabilities(initial, "SHADOW")
        tested = transition_capabilities(shadow, "TESTED")
        canary = transition_capabilities(tested, "CANARY")
        active = transition_capabilities(canary, "ACTIVE_LOCAL")
        for capability_id in INTERNAL_CAPABILITIES:
            expected = (
                "SHADOW"
                if capability_id == "ACTIVE_INFERENCE_SHADOW"
                else "ACTIVE_LOCAL"
            )
            self.assertEqual(active["capabilities"][capability_id]["state"], expected)
        unsafe = json.loads(json.dumps(active))
        unsafe["forbidden"]["WAN_ACCESS"] = True
        with self.assertRaises(CapabilityRegistryError):
            validate_registry(unsafe)

    def test_self_model_gap_persists_non_executable_proposal_with_memory(self):
        receipt = self.run_one(self.heartbeat("gap"), "SELF_MODEL_GAP")
        self.assertTrue(receipt["persisted"])
        self.assertEqual(receipt["classification"], "SUPPORT")
        self.assertFalse(receipt["executable"])
        self.assertGreaterEqual(receipt["memory_reads_per_cycle"], 1)
        self.assertEqual(receipt["memory_future_use_total"], 0)
        proposal = self.con.execute(
            "SELECT payload_json FROM events WHERE event_type='capability_proposal'"
        ).fetchone()
        body = json.loads(proposal[0])
        self.assertEqual(body["proposal_type"], "CapabilityProposal")
        self.assertNotEqual(body["capability_id"], "ACTIVE_INFERENCE_SHADOW")
        self.assertTrue(body["evidence_ids"])
        self.assertFalse(body["executable"])
        self.assertEqual(
            self.con.execute(
                "SELECT COALESCE(SUM(executable),0) FROM decision_evidence"
            ).fetchone()[0],
            0,
        )

    def test_consolidation_preserves_raw_events_and_records_all_provenance(self):
        source_ids = [self.heartbeat(str(index)) for index in range(3)]
        before = dict(
            self.con.execute(
                f"SELECT event_id, hash FROM events WHERE event_id IN "
                f"({','.join('?' for _ in source_ids)})",
                source_ids,
            ).fetchall()
        )
        receipt = self.run_one(source_ids[-1], "EPISODIC_CONSOLIDATION")
        measurement = receipt["steps"]["9_measure_result"]
        self.assertTrue(measurement["raw_events_unchanged"])
        self.assertEqual(len(measurement["source_event_ids"]), 3)
        after = dict(
            self.con.execute(
                f"SELECT event_id, hash FROM events WHERE event_id IN "
                f"({','.join('?' for _ in source_ids)})",
                source_ids,
            ).fetchall()
        )
        self.assertEqual(before, after)
        consolidation = self.con.execute(
            "SELECT payload_json FROM events WHERE event_type='memory_consolidation'"
        ).fetchone()
        body = json.loads(consolidation[0])
        self.assertEqual(body["model_version"], "1")
        self.assertEqual(len(body["source_event_ids"]), 3)
        self.assertFalse(body["raw_events_overwritten"])

    def test_local_hypothesis_is_bounded_local_and_noncausal(self):
        values = iter(
            [
                {"MemTotal": 1000, "MemAvailable": 900},
                {"MemTotal": 1000, "MemAvailable": 800},
                {"MemTotal": 1000, "MemAvailable": 700},
                {"MemTotal": 1000, "MemAvailable": 600},
                {"MemTotal": 1000, "MemAvailable": 500},
            ]
        )
        fake = FakeCortex()
        receipt = self.run_one(
            self.heartbeat("hypothesis"),
            "LOCAL_HYPOTHESIS",
            cortex=fake,
            mem_probe=lambda: next(values),
        )
        self.assertEqual(fake.calls, 5)
        self.assertEqual(receipt["classification"], "SUPPORT")
        result = self.con.execute(
            "SELECT payload_json FROM events WHERE event_type='local_hypothesis'"
        ).fetchone()
        body = json.loads(result[0])
        self.assertFalse(body["causal_claim"])
        self.assertEqual(body["external_calls"], 0)
        self.assertEqual(body["wan_fetches"], 0)
        self.assertFalse(body["executable"])

    def test_one_experiment_per_heartbeat_and_three_total(self):
        first = self.heartbeat("first")
        self.run_one(first, "SELF_MODEL_GAP")
        with self.assertRaisesRegex(ControlledGrowthError, "heartbeat_already_used"):
            self.run_one(first, "EPISODIC_CONSOLIDATION")

        second = self.heartbeat("second")
        self.run_one(second, "EPISODIC_CONSOLIDATION")
        third = self.heartbeat("third")
        values = iter(
            [{"MemTotal": 1000, "MemAvailable": 900 - index * 100} for index in range(5)]
        )
        self.run_one(
            third,
            "LOCAL_HYPOTHESIS",
            cortex=FakeCortex(),
            mem_probe=lambda: next(values),
        )
        with self.assertRaisesRegex(ControlledGrowthError, "experiment_limit_reached"):
            self.run_one(self.heartbeat("fourth"), "SELF_MODEL_GAP")

    def test_engineering_theta_is_pure_non_executable_metric(self):
        result = engineering_delta_theta(
            belief_change=2,
            homeostatic_error=-1,
            action_relevance=0.5,
            memory_retention=1,
        )
        self.assertFalse(result["subjective_claim"])
        self.assertFalse(result["consciousness_claim"])
        self.assertFalse(result["executable"])
        self.assertLessEqual(result["delta_theta"], 1)


if __name__ == "__main__":
    unittest.main()
