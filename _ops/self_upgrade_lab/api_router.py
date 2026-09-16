# -*- coding: utf-8 -*-
"""Discover local/free APIs. Never print secrets. Paid calls forbidden.
Outputs are untrusted proposals — they never patch production directly."""
from __future__ import annotations

import json
import os
import socket
from typing import Any

from .contracts import append_jsonl, utc_now
from . import STATE_DIR

_NAME_ONLY = (
    "DEEPSEEK_API_KEY", "OPENAI_API_KEY", "ANTHROPIC_API_KEY",
    "FUGU_API_KEY", "SAKANA_API_KEY", "TELEGRAM_BOT_TOKEN",
)


def _present(name: str) -> bool:
    v = os.environ.get(name, "")
    return bool(str(v).strip())


def _port_open(host: str, port: int, timeout: float = 0.4) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def inventory() -> dict[str, Any]:
    rec = {
        "schema": "api-inventory/1",
        "ts": utc_now(),
        "paid_calls": "FORBIDDEN",
        "env_present_names_only": [n for n in _NAME_ONLY if _present(n)],
        "local": {
            "ollama_11434": _port_open("127.0.0.1", 11434),
            "organism_8771": _port_open("127.0.0.1", 8771),
            "cortex_8772": _port_open("127.0.0.1", 8772),
            "miniapp_8774": _port_open("127.0.0.1", 8774),
            "center_8776": _port_open("127.0.0.1", 8776),
        },
        "policy": {
            "api_may_propose": True,
            "api_may_patch_production": False,
            "paid_calls": "FORBIDDEN_WITHOUT_BUDGET",
            "secret_echo": False,
        },
        "budget_proposal_to_owner": (
            "If DeepSeek/Fugu should enter the loop, set an explicit daily AUD cap. "
            "Until then the lab continues on local tests + verifier."
        ),
    }
    append_jsonl(STATE_DIR / "api-calls.jsonl", {
        "ts": rec["ts"], "kind": "inventory", "paid": False,
        "local_ollama": rec["local"]["ollama_11434"],
    })
    return rec


def propose_untrusted(prompt: str) -> dict[str, Any]:
    """Local-only stub. Does not call paid APIs. Returns a receipt, not a patch."""
    inv = inventory()
    return {
        "untrusted": True,
        "used": "none" if not inv["local"]["ollama_11434"] else "ollama-available-not-called",
        "paid": False,
        "prompt_sha16": __import__("hashlib").sha256(prompt.encode("utf-8")).hexdigest()[:16],
        "note": "API output would be an untrusted proposal; local tests+verifier remain mandatory.",
    }
