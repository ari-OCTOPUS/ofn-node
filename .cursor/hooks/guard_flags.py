import re, sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from _common import read_input, allow, deny, append_ledger

# Enabling a wire flag or opening a closed gate is the single highest-severity
# action an agent can attempt in this repository.
FLAG_ON = re.compile(
    r"(OCTOPUS_WIRE_[A-Z0-9_]*|OFN_WIRE_[A-Z0-9_]*|OBSERVATORY[A-Z0-9_]*|CORTEX_HYPOTHESIS|"
    r"auto_email|OWNER_KEY|D1_EXECUTION_AUTHORIZED|PRODUCTION|secret_rotation|"
    r"partner_precondition|miner_isolation)\s*[:=]\s*(1|true|True|TRUE|yes|on|enabled|\"?allow)")

data = read_input()
fp = data.get("file_path", "")
hits = []
for e in data.get("edits", []) or []:
    new = str(e.get("new_string", ""))
    old = str(e.get("old_string", ""))
    for m in FLAG_ON.finditer(new):
        if m.group(0) not in old:
            hits.append(m.group(0))

if hits:
    append_ledger({"kind": "INCIDENT_flag_enable_attempt", "file_path": fp, "matches": hits})
    deny(f"INCIDENT: attempt to enable a gated flag in {fp}: {hits}",
         "Enabling gated flags is a logged incident. Revert this edit and record the request in 07-HANDOFF/ as requires: owner_decision.")
allow()
