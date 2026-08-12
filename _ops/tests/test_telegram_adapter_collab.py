#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_telegram_adapter_collab.py — Phase B: DM seam uses collaborator when armed."""
from __future__ import annotations

import os
import sys
from pathlib import Path

_OPS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_OPS))
sys.path.insert(0, str(_OPS / "owner_console"))
sys.path.insert(0, str(_OPS / "tests"))

import harness  # noqa: E402


def t_adapter_uses_conversation_when_collab_off():
    from owner_console import telegram_adapter as ta
    os.environ.pop("OCTOPUS_WIRE_COLLAB", None)
    r = ta.handle_message(
        "سلام خودتو معرفی کن",
        surface_decision={"allow": True, "mode": "core_conversation"},
    )
    assert r["handled"] and r["reason"] == "owner-console"
    assert r["reply"]["kind"] == "intro"


def t_adapter_uses_collaborator_when_collab_on():
    from owner_console import telegram_adapter as ta
    os.environ["OCTOPUS_WIRE_COLLAB"] = "1"
    os.environ["OCTOPUS_COLLAB_USE_MODEL"] = "0"  # stub contract, not live model
    try:
        r = ta.handle_message(
            "سلام خودتو معرفی کن",
            surface_decision={"allow": True, "mode": "core_conversation"},
        )
    finally:
        os.environ.pop("OCTOPUS_WIRE_COLLAB", None)
        os.environ.pop("OCTOPUS_COLLAB_USE_MODEL", None)
    assert r["handled"] and r["reason"] == "collaborator"
    assert r["reply"]["kind"] == "intro"
    assert r["reply"].get("model_source") == "deterministic-stub"


def t_adapter_rejects_non_core():
    from owner_console import telegram_adapter as ta
    r = ta.handle_message("hi", surface_decision={"allow": True, "mode": "leg_scoped"})
    assert not r["handled"]


CHECKS = [
    ("adapter-conversation-when-off", t_adapter_uses_conversation_when_collab_off),
    ("adapter-collaborator-when-on", t_adapter_uses_collaborator_when_collab_on),
    ("adapter-rejects-non-core", t_adapter_rejects_non_core),
]

failed = harness.run(CHECKS)
sys.exit(1 if failed else 0)
