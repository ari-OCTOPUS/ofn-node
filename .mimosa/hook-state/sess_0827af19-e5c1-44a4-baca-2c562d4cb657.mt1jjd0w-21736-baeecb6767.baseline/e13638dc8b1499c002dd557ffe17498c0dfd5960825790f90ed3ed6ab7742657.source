#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_talk_discovery.py — Phase C/D: journal + dark pulse + no auto-arm."""
from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path

_OPS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_OPS))
sys.path.insert(0, str(_OPS / "owner_console"))
sys.path.insert(0, str(_OPS / "tests"))

import harness  # noqa: E402


def t_journal_append_and_forbid_money_arm():
    from owner_console import capability_journal as cj
    with tempfile.TemporaryDirectory() as td:
        path = Path(td) / "j.jsonl"
        e = cj.append_entry(
            candidate="OCTOPUS_COLLAB_USE_MODEL",
            level="STRUCTURAL",
            evidence="adapter wired",
            path=path,
        )
        assert e["auto_arm"] is False
        assert e["schema"] == "CapabilityJournal.entry.v1"
        rows = cj.read_entries(path=path)
        assert len(rows) == 1
        try:
            cj.append_entry(
                candidate="OCTOPUS_LEAD_ASK_WHEN_UNSCOREABLE",
                level="ARMED",
                evidence="should fail",
                path=path,
            )
            raise AssertionError("expected ValueError for money/lead ARMED")
        except ValueError:
            pass


def t_dark_pulse_excludes_lead_and_never_arms():
    from owner_console import discovery_pulse as dp
    fake = {
        "n_dark": 3,
        "live_source": "absent",
        "dark": [
            {"flag": "OCTOPUS_COLLAB_USE_MODEL", "n_readers": 5},
            {"flag": "CORTEX_LOCAL_FIRST", "n_readers": 4},
            {"flag": "OCTOPUS_LEAD_ASK_WHEN_UNSCOREABLE", "n_readers": 9},
            {"flag": "OCTOPUS_WIRE_OUTBOUND_HTTPS", "n_readers": 9},
        ],
    }
    pulse = dp.build_dark_pulse(scan_result=fake)
    flags = [p["candidate"] for p in pulse["proposals"]]
    assert "OCTOPUS_COLLAB_USE_MODEL" in flags
    assert "CORTEX_LOCAL_FIRST" in flags
    assert "OCTOPUS_LEAD_ASK_WHEN_UNSCOREABLE" not in flags
    assert "OCTOPUS_WIRE_OUTBOUND_HTTPS" not in flags
    assert all(p.get("auto_arm") is False for p in pulse["proposals"])


def t_heldout_at_least_five():
    from owner_console import discovery_pulse as dp
    cands = dp.heldout_candidates()
    assert len(cands) >= 5


def t_seed_journal_idempotent():
    from owner_console import capability_journal as cj
    from owner_console import discovery_pulse as dp
    with tempfile.TemporaryDirectory() as td:
        jpath = Path(td) / "j.jsonl"
        mdpath = Path(td) / "j.md"
        os.environ["OCTOPUS_CAPABILITY_JOURNAL_JSONL"] = str(jpath)
        os.environ["OCTOPUS_CAPABILITY_JOURNAL_MD"] = str(mdpath)
        try:
            pulse = {
                "ts": "2026-08-11T00:00:00Z",
                "proposals": [{
                    "candidate": "CORTEX_SELF_MONITOR",
                    "level": "STRUCTURAL",
                    "evidence": "test",
                    "owner_vote": "pending",
                    "next_step": "propose-only",
                }],
            }
            w1 = dp.seed_journal_from_pulse(pulse=pulse, write_md=True)
            w2 = dp.seed_journal_from_pulse(pulse=pulse, write_md=True)
            assert len(w1) == 1 and len(w2) == 0
            assert mdpath.is_file()
            assert "CORTEX_SELF_MONITOR" in mdpath.read_text(encoding="utf-8")
        finally:
            os.environ.pop("OCTOPUS_CAPABILITY_JOURNAL_JSONL", None)
            os.environ.pop("OCTOPUS_CAPABILITY_JOURNAL_MD", None)


def t_living_card_mentions_no_auto_arm():
    from owner_console import discovery_pulse as dp
    text = dp.living_card(pulse={
        "n_ai_core_dark": 2,
        "n_dark_total": 10,
        "live_source": "absent",
        "proposals": [{"candidate": "CORTEX_LOCAL_FIRST", "level": "STRUCTURAL"}],
    }, digest={"status": "OK"})
    assert "بدون arm خودکار" in text
    assert "CORTEX_LOCAL_FIRST" in text


def t_discover_intent_uses_pulse_text():
    from owner_console import conversation as conv
    r = conv.handle("چه چیزی داری که من ندیدم؟")
    assert r["kind"] == "discover"
    assert "propose-only" in r["text"] or "بدون arm" in r["text"] or "کشف" in r["text"]


def t_capability_journal_md_exists():
    md = _OPS / "CAPABILITY-JOURNAL.md"
    assert md.is_file()
    body = md.read_text(encoding="utf-8")
    assert "No auto-arm" in body or "auto-arm" in body.lower()
    # Gate C: at least 5 candidates documented
    assert body.count("|") >= 20


def t_discovery_protocol_exists():
    p = _OPS / "DISCOVERY-PROTOCOL.md"
    assert p.is_file()
    body = p.read_text(encoding="utf-8")
    assert "OCTOPUS_COLLAB_USE_MODEL" in body
    assert "OCTOPUS_COLLAB_MODEL_DAILY_CAP" in body


def t_model_daily_cap_blocks():
    from owner_console import collab_model_adapter as ma
    with tempfile.TemporaryDirectory() as td:
        cpath = Path(td) / "c.json"
        os.environ["OCTOPUS_COLLAB_MODEL_COUNTER"] = str(cpath)
        os.environ["OCTOPUS_COLLAB_MODEL_DAILY_CAP"] = "1"
        called = []

        def _fake(task, prompt, system, max_tokens):
            called.append(1)
            return {"ok": True, "text": "من اختاپوس پاسخ آزمایشی.", "tier": "local",
                    "model": "m", "cost_usd": 0.0}

        ma.set_ask_impl(_fake)
        try:
            r1 = ma.complete("سلام معرفی کن", kind_hint="intro")
            r2 = ma.complete("سلام معرفی کن", kind_hint="intro")
        finally:
            ma.set_ask_impl(None)
            os.environ.pop("OCTOPUS_COLLAB_MODEL_COUNTER", None)
            os.environ.pop("OCTOPUS_COLLAB_MODEL_DAILY_CAP", None)
        assert r1.get("ok") is True
        assert r2.get("ok") is False and r2.get("reason") == "daily-cap"
        assert len(called) == 1


def t_living_callback():
    from owner_console import conversation as conv
    r = conv.callback("oc:living")
    assert r["kind"] == "living-card"
    assert "arm" in r["text"].lower() or "Living" in r["text"] or "مغز" in r["text"]


def t_discover_hidden_callback():
    from owner_console import conversation as conv
    r = conv.callback("oc:discover-hidden")
    assert r["kind"] == "discover"


def t_task_tiers_collab_chat_is_secondary_deepseek():
    """2026-08-12: collab talk uses DeepSeek (secondary), not local qwen."""
    ops = _OPS
    sys.path.insert(0, str(ops / "cortex"))
    sys.path.insert(0, str(ops))
    import importlib
    import model_router as mr  # noqa: WPS433 — flat module on cortex path
    importlib.reload(mr)
    assert mr.TASK_TIERS.get("collab_chat") == "secondary"


def t_interaction_contract_is_pointer_to_canonical():
    ptr = (_OPS / "INTERACTION-CONTRACT.md").read_text(encoding="utf-8")
    assert "OCTOPUS-COLLABORATOR-INTERACTION-CONTRACT" in ptr
    canon = (
        _OPS.parent / "06 - Architecture Maps" / "OCTOPUS-COLLABORATOR-INTERACTION-CONTRACT.md"
    )
    assert canon.is_file()
    body = canon.read_text(encoding="utf-8")
    assert "collab_chat" in body
    assert "canonical: true" in body.lower() or "Canonical" in body


def t_discover_stays_stub_even_with_model():
    """discover must keep journal/pulse text — not overwritten by LLM."""
    import collaborator as col
    called = []

    def _track(*a, **k):
        called.append(1)
        return {"ok": True, "text": "should-not-replace-discover", "tier": "local", "model": "x"}

    os.environ["OCTOPUS_WIRE_COLLAB"] = "1"
    os.environ["OCTOPUS_COLLAB_USE_MODEL"] = "1"
    col._model.set_ask_impl(_track)
    try:
        r = col.handle("چه چیزی پنهان داری؟")
    finally:
        col._model.set_ask_impl(None)
        os.environ.pop("OCTOPUS_WIRE_COLLAB", None)
        os.environ.pop("OCTOPUS_COLLAB_USE_MODEL", None)
    assert not called
    assert r["kind"] == "discover"
    assert "should-not-replace-discover" not in r["text"]


CHECKS = [
    ("journal-append-forbid-money-arm", t_journal_append_and_forbid_money_arm),
    ("dark-pulse-excludes-lead", t_dark_pulse_excludes_lead_and_never_arms),
    ("heldout-at-least-five", t_heldout_at_least_five),
    ("seed-journal-idempotent", t_seed_journal_idempotent),
    ("living-card-no-auto-arm", t_living_card_mentions_no_auto_arm),
    ("discover-intent-text", t_discover_intent_uses_pulse_text),
    ("capability-journal-md", t_capability_journal_md_exists),
    ("discovery-protocol-md", t_discovery_protocol_exists),
    ("model-daily-cap-blocks", t_model_daily_cap_blocks),
    ("living-callback", t_living_callback),
    ("discover-hidden-callback", t_discover_hidden_callback),
    ("task-tiers-collab-chat", t_task_tiers_collab_chat_is_secondary_deepseek),
    ("interaction-contract-canonical", t_interaction_contract_is_pointer_to_canonical),
    ("discover-stays-stub-with-model", t_discover_stays_stub_even_with_model),
]

failed = harness.run(CHECKS)
sys.exit(1 if failed else 0)
