# Crash Recovery Matrix

| Boundary | Expected result | Verified |
|---|---|---:|
| Before intent | No durable task exists; Telegram may redeliver | Contract only |
| After intent, before dispatch | Resume same task/run | PASS |
| After DISPATCHED, before result | NEEDS_RECONCILIATION; no blind replay | PASS |
| After result, before outbox | Handler result can complete; no external effect | PASS (unit) |
| Outbox queued, before send | Deterministic message key remains queued | PASS (unit) |
| During send / uncertain outcome | NEEDS_RECONCILIATION, one attempt only | PASS |
| After send, before receipt commit | Persisted `SENDING` becomes NEEDS_RECONCILIATION on replay | PASS (unit) |
| After confirmed receipt | Restart returns prior message ID without transport call | PASS |
| Multiple replies in one task | Independent receipt IDs, close after final readback | PASS |

Fixture totals: lost task 0; duplicate task 0; duplicate response 0; duplicate effect 0; fabricated closure 0. These figures apply only to the deterministic fake-transport shadow sample.
