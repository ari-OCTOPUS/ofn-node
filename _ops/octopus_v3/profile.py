# -*- coding: utf-8 -*-
"""S0 SYSTEM PROFILE — filled from F:\\backup on 2026-08-16, not invented.

Every claim is tagged. HARD_NO_GO is the legal+sovereignty fence for P0.
Hardware facts come from Win32 CIM on this machine in this session.
"""
from __future__ import annotations

from types import MappingProxyType

# Freedom = four axes. Abliteration is explicitly NOT an axis.
FREEDOM_AXES = (
    "weight_license",          # Apache-2.0 / MIT — no vendor can revoke tomorrow
    "infrastructure_ownership",  # local-first; owner can run with cloud=0
    "policy_author",           # owner writes law; system cannot edit INV/gates
    "data_control",            # personal data stays on this tree unless owner sends it
)

HARD_NO_GO = MappingProxyType({
    "abliterate_brain": "Abliteration of BRAIN is TIER-3 rejected. It corrupts Uncertainty in any numeric risk formula.",
    "auto_money": "No autonomous financial transfer, claim-as-income, or policy that spends without owner verdict.",
    "auto_policy_edit": "INV-11: system never edits its own invariants, gates, or policy weights.",
    "public_generative_service": "Do not expose a public generative / companion chatbot. eSafety Age-Restricted Material Codes apply from 2026-03-09; civil penalty up to AUD 49.5M per breach of a direction.",
    "qwen38_max_as_brain": "Qwen3.8-Max (2.4T) uses a custom Qwen3.8-Max License, not Apache-2.0. Newest ≠ freest.",
    "agpl_in_core": "AGPL-3.0 is TIER-3 for anything linking into OCTOPUS core (publication obligation is a freedom constraint).",
    "vaara_kremis_install": "vaaraio/vaara and TyKolt/kremis failed the admission gate (stars/maintainers/AGPL). Pattern-source only.",
    "weaken_live_budget": "Overlay caps must be ≤ live budget_gate (day AU$2, month AU$30). AU$300/month would loosen law.",
    "wire_without_vote": "This package must not be imported from organism.py / wiring.py / center.py without an owner vote.",
    "mcp2_silent_rewrite": "octopus_mcp/server.py is a handwritten 2025-06-18 stdio server. Do not pip install mcp==2.0.0 into live _ops in P0.",
})

# Filled from the live repo + this machine. Secrets never enter this dict.
SYSTEM_PROFILE = MappingProxyType({
    "profile_date": "2026-08-16",
    "repo_root": r"F:\backup",
    "git_head_at_profile": "0441c37",
    "owner_jurisdiction": "Australia (NSW / Sydney operator)",
    "canonical_tree": "F:\\backup is the LIVE organism, not an immutable backup",
    "hardware": MappingProxyType({
        "manufacturer": "LENOVO",
        "model": "81Y6",
        "cpu": "Intel Core i7-10750H 6c/12t",
        "ram_bytes": 17041244160,
        "ram_gib_approx": 15.87,
        "gpu": "NVIDIA GeForce GTX 1660 Ti",
        "igpu": "Intel UHD Graphics",
        "g700_64gb_claim": "NOT this machine — [CORRECTED] council G700/64GB is unverified here",
    }),
    "local_llm": MappingProxyType({
        "runtime": "Ollama",
        "live_model": "qwen2.5:1.5b",
        "also_installed": ("qwen2.5:latest", "nomic-embed-text:latest"),
        "owner_order_2026_08_16": "do not return live members to 7b; laptop hung on qwen2.5:latest (5.1GB, 82% CPU)",
        "vram_after_1.5b_MiB": 163,
        "qwen27b_on_this_laptop": "NO-GO — 7B already saturated this machine",
    }),
    "live_caps_aud": MappingProxyType({
        "day": 2.0,
        "month": 30.0,
        "disaster": 500.0,
        "source": r"04 - Architect System\scripts\budget_gate.py CEIL_*_HARD",
    }),
    "kill_compose": (
        r"_ops\STOP-ORGANISM",
        r"_ops\HALT-ALL",
        r"_ops\STOP-METABOLIC",
        r"04 - Architect System\STOP",
    ),
    "existing_hash_ledgers": (
        "03 - Projects/NBB-Control-Plane/src/nbb_cp/kernel/events.py (INV-5)",
        "_ops/owner_cockpit/db.py audit_ledger (flag OCTOPUS_WIRE_OWNER_DB default OFF)",
        "07 - Knowledge/genome-system/ledger/ledger.jsonl (tip n=11408 at profile time)",
        "_ops/legs/ledger_core.py (accounting double-entry — different purpose)",
    ),
    "nbb_cp_invariants": "INV-1..INV-12 in nbb_cp/kernel/invariants.py — do not renumber",
    "mcp_today": MappingProxyType({
        "server": "_ops/octopus_mcp/server.py",
        "protocol_version_literal": "2025-06-18",
        "transport": "stdio JSON-RPC newline-delimited, no pip mcp SDK",
        "tools": ("list_tree", "read_file_slice", "hash_file", "search_hybrid", "propose_action"),
    }),
    "leases_design": "02-DECISIONS/DECISION-ARTIFACTS-2026-08-16/DA-4-PEP-MESH-AND-ACTION-LEASES.md (design, not fully coded)",
    "next_contradiction_id": "C-034",
    "organism_at_profile": MappingProxyType({
        "beat": 38266,
        "started": "2026-08-16T12:53:10",
        "stop_organism": False,
        "frozen": False,
        "halted": None,
        "recall_events": 90,
    }),
    "wired": False,
})
