"""Drop REAL-NOTIFY-SILENT-EXCEPT-003 with the corrected contract:
- pytest-only run_tests (validator only accepts pytest commands)
- summary field explicitly required
- valid Python test content (no sys.path.insert with literal '..')
- anchor context matches actual code (pass + env-fallback follow the except)
"""
import hashlib
import json
import pathlib

TASKS = pathlib.Path("/home/ari/ofn/state/coding-worker/state/tasks")
target = pathlib.Path("/home/ari/ofn/ofn/agents/owner_notify.py")
target_sha = hashlib.sha256(target.read_bytes()).hexdigest()

task = {
    "schema": "octopus.coding-task.v1",
    "task_id": "REAL-NOTIFY-SILENT-EXCEPT-003",
    "patch_mode": "free",
    "component": "coding-worker",
    "purpose": "add error receipt to silent except in owner_notify._secrets()",
    "context": {
        "target_file": "ofn/agents/owner_notify.py",
        "IMPORTANT": (
            "Patch ONLY ofn/agents/owner_notify.py. "
            "Do NOT patch ops_agent.py or any other file."
        ),
        "anchor": "except Exception:  # noqa: BLE001\n        pass",
        "anchor_location": "inside function _secrets(), around line 30",
        "code_after_anchor": (
            "After the 'pass' line, there is a comment about env fallback "
            "and then a for loop checking os.environ.get(k)."
        ),
        "expected_change": (
            "Replace 'except Exception:  # noqa: BLE001\\n        pass' with "
            "'except Exception as exc:  # noqa: BLE001\\n"
            "        try:\\n"
            "            opslib.append_jsonl(\\n"
            "                opslib.STATE_DIR / 'legs' / 'lead-inbox' / 'events.jsonl',\\n"
            "                {'event_type': 'owner_notify.secrets_read_error',\\n"
            "                 'occurred_at': opslib.now_iso(),\\n"
            "                 'payload': {'error': type(exc).__name__}})\\n"
            "        except Exception:\\n"
            "            pass"
        ),
        "test_hint": (
            "Write a pytest test that imports owner_notify and checks the "
            "source contains 'secrets_read_error'. Use pytest format only. "
            "Valid run_tests: ['python3 -m pytest -q test_notify_fix.py']"
        ),
    },
    "output_contract": (
        "Return ONE JSON object on ONE line with these REQUIRED keys: "
        "kind='octopus.patch.v1', summary (a short string), "
        "diff_scope=['ofn/agents/owner_notify.py'], "
        "files=[{path, op, anchor, replacement}], "
        "tests=[{path, content}], "
        "run_tests=['python3 -m pytest -q <test_file>'] "
        "run_tests MUST use pytest commands. "
        "summary is REQUIRED. "
        "test content must be valid Python (use import, not sys.path tricks)."
    ),
    "provenance": {
        "class": "REAL_CODE_DEFECT",
        "source": "bare except+pass in owner_notify.py:30 with no receipt "
                  "(GAPS-34 class); previous attempts 001/002 failed due to "
                  "contract issues (wrong test format, missing summary)",
        "source_ts": "2026-09-14T21:00:00Z",
        "source_hash": target_sha,
    },
    "diff_scope": ["ofn/agents/owner_notify.py"],
}
p = TASKS / "REAL-NOTIFY-SILENT-EXCEPT-003.json"
p.write_text(json.dumps(task, indent=1) + "\n", encoding="utf-8")
print("dropped:", p.name)
