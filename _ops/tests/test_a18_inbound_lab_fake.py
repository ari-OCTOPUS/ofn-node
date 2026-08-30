# -*- coding: utf-8 -*-
from __future__ import annotations
import json
import importlib.util
from pathlib import Path

SCRIPT = Path(r"F:/backup/06-EVIDENCE/OCTOPUS-ARCH-EVOLUTION-LOOP-2026-08-23/A18-INBOUND-LAB-FAKE/_run_lab_fake.py")
RESULT = SCRIPT.parent / "RESULT.json"


def test_a18_inbound_lab_fake_pass():
    spec = importlib.util.spec_from_file_location("a18_lab_fake", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(mod)
    assert mod.main() == 0
    d = json.loads(RESULT.read_text(encoding="utf-8"))
    assert d["status"] == "PASS"
    assert d["checks"]["remember_durable_CONFIRMED_CLOSED"] is True
    assert d["checks"]["correct_invalid_durable_CONFIRMED_CLOSED"] is True
    assert d["remaining_gap"]["id"] == "A18-LIVE-OWNER-INBOUND"
    assert d["constraints"]["no_live_sendMessage"] is True
