from __future__ import annotations

from pathlib import Path

import pytest


@pytest.fixture(autouse=True)
def _isolate_sequence_file(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "octopus_sensorium.kernel.sequences.DEFAULT_PATH",
        tmp_path / "sequences.json",
    )
