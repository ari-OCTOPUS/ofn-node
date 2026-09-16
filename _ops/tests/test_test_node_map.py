#!/usr/bin/env python3
"""The registered test suite must have a reproducible, collision-free node map."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import harness

ENV = harness.setup("test-node-map")
_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

import generate_test_node_map as generator  # noqa: E402


def t_a_registry_is_literal_unique_and_complete():
    result = generator.build()
    assert result["registered_files"] == result["unique_registered_files"]
    assert result["duplicate_registry_entries"] == []
    assert result["missing_registered_files"] == []
    assert result["parse_errors"] == []
    assert result["duplicate_node_ids"] == []


def t_b_wave_a_tests_are_registered_with_nodes():
    result = generator.build()
    rows = {row["path"]: row for row in result["files"]}
    expected = {
        "_ops/tests/test_poll_lease.py",
        "_ops/tests/test_transport_subprocess.py",
        "_ops/tests/test_launcher_state_dir_scrub.py",
        "_ops/tests/test_test_node_map.py",
    }
    assert expected <= set(rows)
    for path in expected:
        assert rows[path]["nodes"], path


def t_c_json_round_trip_preserves_node_count():
    result = generator.build()
    encoded = json.dumps(result, ensure_ascii=False, sort_keys=True)
    decoded = json.loads(encoded)
    assert decoded["discovered_nodes"] == result["discovered_nodes"]
    assert decoded["registered_files"] == result["registered_files"]


if __name__ == "__main__":
    checks = [(name, fn) for name, fn in sorted(globals().items()) if name.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'OK' if not failed else 'FAIL'} test_test_node_map: "
          f"{len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
