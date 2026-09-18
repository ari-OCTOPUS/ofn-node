import hashlib
import json
import pathlib

TASKS = pathlib.Path("/home/ari/ofn/state/coding-worker/tasks")
TASKS.mkdir(parents=True, exist_ok=True)

target = pathlib.Path("/home/ari/ofn/ofn/agents/owner_notify.py")
target_sha = hashlib.sha256(target.read_bytes()).hexdigest()

task = {
    "schema": "octopus.coding-task.v1",
    "task_id": "REAL-NOTIFY-SILENT-EXCEPT-001",
    "patch_mode": "free",
    "component": "coding-worker",
    "purpose": ("fix silent exception handling in owner_notify._secrets(): "
                "bare except Exception returns empty dict with no receipt, "
                "hiding secrets-file corruption (GAPS-34 class defect)"),
    "context": {
        "file": "ofn/agents/owner_notify.py",
        "defect": ("the _secrets() function has a bare except Exception that "
                   "silently returns an empty dict when the secrets file is "
                   "missing or corrupt. Per the GAPS-34 lesson in the file "
                   "docstring, this except should append a receipt."),
        "anchor_hint": "except Exception:  # noqa: BLE001",
        "expected_change": ("add opslib.append_jsonl receipt in the except "
                            "block, similar to the send() function error "
                            "handling already in this file"),
    },
    "provenance": {
        "class": "REAL_CODE_DEFECT",
        "source": ("intake-20260914 S5 + manual review: bare except in "
                   "owner_notify.py with no receipt"),
        "source_ts": "2026-09-14T12:15:00Z",
        "source_hash": target_sha,
    },
    "diff_scope": ["ofn/agents/owner_notify.py"],
}
p = TASKS / "REAL-NOTIFY-SILENT-EXCEPT-001.json"
p.write_text(json.dumps(task, indent=1) + "\n", encoding="utf-8")
print("dropped:", p)
