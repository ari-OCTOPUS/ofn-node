"""Fix the REAL-NOTIFY task contract: prescriptive context + explicit
output_contract with correct target file, anchor, and test format.
Re-runs the SAME task without changing model or budget."""
import hashlib
import json
import pathlib

TASKS = pathlib.Path("/home/ari/ofn/state/coding-worker/state/tasks")

target = pathlib.Path("/home/ari/ofn/ofn/agents/owner_notify.py")
target_bytes = target.read_bytes()
target_sha = hashlib.sha256(target_bytes).hexdigest()

# Find the exact anchor (the bare except in _secrets)
anchor = "except Exception:  # noqa: BLE001"
assert target_bytes.decode("utf-8").count(anchor) >= 1, "anchor not found"

task = {
    "schema": "octopus.coding-task.v1",
    "task_id": "REAL-NOTIFY-SILENT-EXCEPT-002",
    "patch_mode": "free",
    "component": "coding-worker",
    "purpose": "add receipt to silent except in owner_notify._secrets()",
    "context": {
        "target_file": "ofn/agents/owner_notify.py",
        "target_file_absolute": str(target),
        "IMPORTANT": (
            "The file to patch is ofn/agents/owner_notify.py. "
            "Do NOT patch state/ops-agent/ops_agent.py. "
            "Do NOT patch any other file. "
            "Only ofn/agents/owner_notify.py needs a change."
        ),
        "anchor": anchor,
        "current_code_after_anchor": (
            "The line after the anchor currently reads:  return d  "
            "(or equivalent). The except block silently swallows errors."
        ),
        "expected_replacement": (
            "Inside the except block, BEFORE any return statement, add:\n"
            "  opslib.append_jsonl(opslib.STATE_DIR / 'legs' / 'lead-inbox' / "
            "'events.jsonl', {'event_type': 'owner_notify.secrets_read_error', "
            "'occurred_at': opslib.now_iso(), 'payload': {'error': "
            "type(exc).__name__}})  # noqa: S110 intentional silent-soft\n"
            "The except clause must capture the exception: "
            "'except Exception as exc:  # noqa: BLE001'"
        ),
        "test_hint": (
            "Tests should verify that owner_notify.py still imports correctly "
            "and that the new receipt call exists in the source. "
            "A valid test file path is ANY .py file inside the stage directory. "
            "A valid run_tests command is: python3 -c \"import ofn.agents.owner_notify\" "
            "or python3 test_notify_receipt.py"
        ),
    },
    "output_contract": (
        "Return exactly ONE JSON object on ONE line. "
        'kind must be "octopus.patch.v1". '
        'files[0].path must be "ofn/agents/owner_notify.py". '
        'files[0].op must be "replace_anchor". '
        'files[0].anchor must be the exact string: except Exception:  # noqa: BLE001 '
        "files[0].replacement must be the new code block as a string. "
        "tests is an array of objects like: "
        '{"path": "test_fix.py", "content": "import sys; sys.path.insert(0,..); '
        'import ofn.agents.owner_notify; print(\'ok\')"} '
        "run_tests is an array of strings like: "
        '["python3 test_fix.py"] '
        "diff_scope is: [\"ofn/agents/owner_notify.py\"]"
    ),
    "provenance": {
        "class": "REAL_CODE_DEFECT",
        "source": "12+ PATCH_REJECTED receipts 17:42-20:24Z show the model keeps "
                  "targeting the wrong file and using invalid test formats; "
                  "root cause: task context was too vague about target file "
                  "and test contract",
        "source_ts": "2026-09-14T20:30:00Z",
        "source_hash": target_sha,
    },
    "diff_scope": ["ofn/agents/owner_notify.py"],
}
p = TASKS / "REAL-NOTIFY-SILENT-EXCEPT-002.json"
p.write_text(json.dumps(task, indent=1) + "\n", encoding="utf-8")
print("dropped:", p.name)
print("target:", task["context"]["target_file"])
print("anchor:", anchor[:50])
