#!/usr/bin/env python3
"""Run one weekly marketing cycle for the studio leg.

Called by the systemd timer (`ofn-marketing.timer`) every Monday after the
nightly backup, and callable by hand for a manual run. It does one thing:
builds the node exactly as `ofn.run` does, then calls `run_marketing_cycle`
for the current ISO week.

What this does NOT do, deliberately:

  * It does not read, print, or echo any secret. The env files are loaded
    by `config.load()` exactly as the running service loads them; this
    script never touches them directly.
  * It does not publish anything. A cycle produces proposals for the
    partner, never posts.
  * It does not run if the brain key is absent. With no key the cycle is a
    no-op that opens the week with the focus derived from gaps — useful,
    but not worth a scheduled wake. We log that and exit cleanly.

Usage:
    python3 -m ofn.marketing_run                # current week
    python3 -m ofn.marketing_run --week 2026-W33 # a specific week
    python3 -m ofn.marketing_run --style teaser  # force a style
"""
from __future__ import annotations

import argparse
import datetime as _dt
import sys

from . import config
from .run import arm_node_brain, build_node


def _iso_week(now: _dt.datetime) -> str:
    """The ISO 8601 week id, e.g. 2026-W32. Monday-anchored, no timezone
    surprises — the timer runs in local time and so does this."""
    iso = now.isocalendar()
    return f"{iso.year}-W{iso.week:02d}"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--week", help="ISO week id (default: current)")
    parser.add_argument("--style", default="educational",
                        help="marketing style id for this week")
    parser.add_argument("--terms", nargs="*", default=(),
                        help="trend terms to look for")
    args = parser.parse_args(argv)

    cfg = config.load()
    node = build_node(cfg)
    # Arm the brain the same way the running service does — without this,
    # the cycle's router is None and the model is never asked, even with a
    # key present. This was a real bug: the cycle silently reported "brain
    # not wired" because build_node does not arm the brain by itself.
    arm_node_brain(cfg, node, run_worker_loop=False)
    now = int(_dt.datetime.now().timestamp())
    week_id = args.week or _iso_week(_dt.datetime.now())

    # The studio leg is the only one with a marketing cycle today. Find it
    # through the registry rather than hard-coding the string 'studio' as a
    # key — iterate the tenant ids the node actually loaded.
    studio_tenant = next((t for t in node.registry
                          if t.value == "studio"), None)
    if studio_tenant is None:
        print("studio leg not found in registry; nothing to do",
              file=sys.stderr)
        return 0
    scope = node.registry.scope(studio_tenant)

    # The week starts Monday 00:00 local. Good enough for a focus anchor;
    # the exact second does not matter to the cycle.
    monday = _dt.datetime.now() - _dt.timedelta(
        days=_dt.datetime.now().weekday())
    starts_at = int(monday.replace(hour=0, minute=0, second=0,
                                   microsecond=0).timestamp())

    result = node.run_marketing_cycle(
        scope, week_id=week_id, starts_at=starts_at,
        style_id=args.style, terms=tuple(args.terms),
        now_epoch_s=now)

    # Print a one-line summary the timer's journal will keep. No secrets,
    # no PII — just counts and the focus.
    ok = result.get("ok")
    print(f"marketing cycle {week_id}: ok={ok} "
          f"fresh={result.get('fresh_candidates', 0)} "
          f"refused={result.get('refused_count', 0)} "
          f"obs={result.get('observations_kept', 0)} "
          f"brain={result.get('brain', '')}")
    if not ok:
        print(result.get("error", ""), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
