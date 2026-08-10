#!/usr/bin/env python3
"""O12 — daily pilot snapshot, one file per day.

Writes docs/operations/pilot-daily/YYYY-MM-DD.txt with the canonical
stores' numbers plus the live Telegram pilot status. Idempotent per day:
re-running overwrites the same day's file (a fix is a fix, not a dup).

Run: python3 tools/pilot_daily.py
"""

from __future__ import annotations

import datetime
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ofn import config  # noqa: E402


def main() -> int:
    out_dir = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "docs", "operations", "pilot-daily")
    os.makedirs(out_dir, exist_ok=True)
    day = datetime.date.today().isoformat()
    path = os.path.join(out_dir, f"{day}.txt")

    import subprocess
    report = subprocess.run(
        [sys.executable, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                      "pilot_report.py"), "--days", "1"],
        capture_output=True, text=True).stdout.strip()

    # Live pilot status (read-only, with the owner bot). Fail-soft: a
    # network hiccup must not kill the day's snapshot.
    pilot_line = "pilot: not checked"
    try:
        for f in ("/home/ari/.config/ofn/node.env",
                  "/home/ari/.config/ofn/secrets.env"):
            if os.path.exists(f):
                for line in open(f):
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        k, _, v = line.partition("=")
                        os.environ.setdefault(k.strip(), v.strip())
        from ofn.adapters.pilot import PilotState, ReadOnlyPilot
        from ofn.adapters.platforms.telegram_readonly import (
            TelegramReadOnlyAdapter,
        )
        cfg = config.load()
        adapter = TelegramReadOnlyAdapter(
            token=str(cfg.bot_tokens.get("__owner__") or ""),
            channel_id=cfg.telegram_channel_id or "")
        state = PilotState(connector_id="telegram", tenant="studio")
        out = ReadOnlyPilot(adapter, state, page_limit=20).run()
        if out.get("ok"):
            pilot_line = (f"pilot: ok — {out['read']} items read "
                          f"({', '.join(r['id'] for r in state.receipts)})")
        else:
            pilot_line = f"pilot: {out.get('rule', out.get('error', '?'))}"
    except Exception as exc:
        pilot_line = f"pilot: read failed ({exc})"

    text = (f"pilot daily — {day}\n"
            f"  {report.replace(chr(10), chr(10) + '  ')}\n"
            f"  {pilot_line}\n")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text)
    print(text.strip())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
