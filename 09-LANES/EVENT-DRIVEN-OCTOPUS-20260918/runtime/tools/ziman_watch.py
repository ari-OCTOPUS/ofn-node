#!/usr/bin/env python3
"""ziman_watch.py — beat-driven store sensor (EVENT-DRIVEN-OCTOPUS 2026-09-18, Phase 3).

Why a daemon and not a systemd timer: Shopify's Admin API has no push without a
public webhook endpoint + HMAC secret (neither exists on this fleet — see the
migration table). The sensor therefore has to look at the world. What changes is
WHO clocks it: the heartbeat (the fleet's system clock), not a private timer, and
the daemon is fail-closed on a stale beat.

  - orders_check() every ORDER_S (default 60s)  -> order_seen / payment_seen
  - stock_check()  every STOCK_S (default 300s) -> stock_changed
  - full store_watch.main() every FULL_S (default 600s) -> store-watch.json + receipt

Signals only; no business logic. stdlib only.
"""
from __future__ import annotations

import os
import sys
import time

sys.path.insert(0, "/home/ari/octopus-mesh/bin")
sys.path.insert(0, "/home/ari/ofn/tools")
import octopus_events as oe  # noqa: E402
import store_watch as sw  # noqa: E402

ORDER_S = float(os.environ.get("OCTOPUS_ORDER_POLL_S", "60"))
STOCK_S = float(os.environ.get("OCTOPUS_STOCK_POLL_S", "300"))
FULL_S = float(os.environ.get("OCTOPUS_STORE_FULL_S", "600"))
TICK = float(os.environ.get("OCTOPUS_ZIMAN_TICK_S", "15"))


def log(msg: str) -> None:
    print("%s %s" % (time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), msg), flush=True)


def main() -> int:
    last_order = last_stock = last_full = 0.0
    while True:
        try:
            now = time.time()
            if not oe.beat_fresh():
                log("beat stale — sensor idle (fail-closed)")
                time.sleep(TICK)
                continue
            if now - last_full >= FULL_S:
                sw.main()          # writes store-watch.json + receipts (incl. domain check)
                last_full = now
            elif now - last_order >= ORDER_S:
                r = sw.orders_check()
                if r.get("new_orders"):
                    log("orders: new=%s paid=%s" % (r.get("new_orders"), r.get("new_paid")))
                last_order = now
            if now - last_stock >= STOCK_S:
                s = sw.stock_check()
                if s.get("changed"):
                    log("stock changed: %s" % s.get("changed"))
                last_stock = now
        except Exception as exc:  # noqa: BLE001 — daemon must survive
            log("error: %s: %s" % (type(exc).__name__, exc))
        time.sleep(TICK)


if __name__ == "__main__":
    raise SystemExit(main())
