# DO NOT TOUCH - Owner Safety Boundary

- Never use `git reset --hard`, `git clean`, force push, or history rewriting.
- Never expose, copy, inspect, rotate, or commit secret/token values.
- Never issue manual `getUpdates`.
- Never send a live `sendMessage` under this order.
- During protected soak, block every Telegram mutation including `editMessageText`, callback answers, menus, topics, pin/delete and media.
- Never activate, delete, or migrate webhook.
- Never auto-resend `UNCERTAIN_SEND_OUTCOME`.
- Never mutate owner identity, signed owner orders, governance roots, or TCB gates.
- Never destructively migrate production memory.
- Never stage unrelated dirty state; never use `git add -A`.
- Never treat Obsidian prose, fixture evidence, LAB_PASS, or builder output as independent verification.
- Preserve `poll_lease.py` and `transport_subprocess.py` byte identity until their dedicated adoption review.
- Preserve historical uncertain rows and append-only evidence.
