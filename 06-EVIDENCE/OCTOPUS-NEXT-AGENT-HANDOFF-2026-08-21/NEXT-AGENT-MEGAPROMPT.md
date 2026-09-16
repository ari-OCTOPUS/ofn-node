# NEXT AGENT MEGAPROMPT - SINGLE-WRITER CONTINUATION

Operate only in `F:/backup` under the active owner order. Read `README-FIRST.md`, `DO-NOT-TOUCH.md`, and `NEXT-AGENT-EXECUTION-ORDER.md` first. Verify the writer lock, branch, HEAD, preservation manifest, and source mtimes immediately before writing. Preserve all dirty work; never use reset, clean, or add-A.

Adopt and consolidate existing implementation instead of rebuilding the archived `d301339` plan. Start with the reproducibility blocker: review untracked `poll_lease.py` and `transport_subprocess.py`, their tracked callers, and isolated tests, with no token, network, or production state. Proceed in atomic waves A-I exactly as recorded.

Keep every Telegram output mutation blocked through fixtures, clean-checkout verification, controlled restart, and the 60-minute polling soak. Never call `getUpdates` manually. Never mutate webhook. Never inspect secrets. Never resend uncertain outcomes.

Builder terminal state may only be `IMPLEMENTATION_COMPLETE_VERIFICATION_PENDING`, `FAILED_SAFE`, or a documented blocker. Prepare SIG-IV but do not self-sign it. Stop before the live outbound n=1 canary and request exact owner authorization.
