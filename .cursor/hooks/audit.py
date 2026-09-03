import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from _common import read_input, append_ledger, emit

REDACT_KEYS = {"content", "output", "result_json", "tool_output", "prompt", "text", "edits"}

data = read_input()
slim = {}
for k, v in data.items():
    if k in REDACT_KEYS:
        slim[k + "_len"] = len(str(v))
    else:
        slim[k] = v
append_ledger({"kind": "hook_event", "event": data.get("hook_event_name"), "payload": slim})
emit({})
