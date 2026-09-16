# Integration Wave — Rollback

No destructive migration, flag activation, WORKLOCK edit, outbound effect, or state-authority expansion occurred.

## Reversible code patches

| Patch | Rollback |
|---|---|
| Telegram/LLM auditors ignore exact inert backup dirs | revert scoped edits in `tg_send_audit.py`, `test_tg_send_audit.py`, `test_llm_call_inventory.py`, `test_llm_fence_coverage.py` |
| Dashboard profile test isolated from live flag file | revert scoped `test_dashboard.py` test-only edit |
| Owner-language status/goal/pain intents | revert scoped `owner_console/conversation.py`, `status.py`, and conversation tests |
| Collaborator cap default 20 | revert `COLLAB_DAILY_CAP_DEFAULT` to prior 30 only if owner explicitly reverses cap policy; test file can be removed only under a separate deletion approval |

## Operational rollback

- No runtime flag rollback is necessary: APPLY remained 0; PROPOSAL remained 1.
- No state migration exists.
- If owner-console replies regress, restart center/gateway after reverting code; no organism data reset is required.
- Preserve all evidence reports even after code rollback; they are audit history.
