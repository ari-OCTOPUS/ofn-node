import os, sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from _common import read_input, emit, append_ledger

d = read_input()
lane = os.environ.get("OCTOPUS_LANE", "UNDECLARED")
append_ledger({"kind": "session_start", "session_id": d.get("session_id"),
               "lane": lane, "mode": d.get("composer_mode")})

ctx = (
    "OCTOPUS session context.\n"
    f"Declared lane: {lane}.\n"
    "Binding contract: AGENTS.md at repository root.\n"
    "Hard boundaries active this session: no outbound network, no flag enabling, "
    "no closed-gate opening, no recursive delete, no secret file reads, "
    "MCP servers deny-by-default.\n"
    "Every numeric claim needs a source path or the token unverified.\n"
    "Session cannot complete without 09-LANES/<LANE>/LANE-REPORT.md."
)
emit({"additional_context": ctx, "env": {"OCTOPUS_LANE": lane}})
