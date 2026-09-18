#!/usr/bin/env python3
"""event_ledger_consumer.py — JetStream -> vault event ledger (EVENT-DRIVEN-OCTOPUS 2026-09-18).

Runs on the laptop (the NATS hub). Durable pull consumer on OCTOPUS_EVENTS filtered to
the event spine (`octopus.events.>`, `octopus.beat.>`), appending every message to a
daily JSONL in the vault. This is the cross-node proof that an event really landed on
JetStream (acceptance: chain traceable with shas) and the archive for the fleet.

  python event_ledger_consumer.py --once     # drain what is available, exit
  python event_ledger_consumer.py            # loop forever (durable: no gaps)

Auth: user hub_local; password read from the hub keys file (never printed).
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import time

import nats
from nats.js.api import ConsumerConfig

HUB = os.environ.get("OCTOPUS_HUB_ADDR", "nats://hub_local:%s@127.0.0.1:4222")
KEYS_FILE = r"F:\recon-clones-20260917\nats-hub\keys\HUB-LOCAL-PASSWORD.txt"
LEDGER_DIR = r"F:\backup\06-EVIDENCE\EVENT-DRIVEN-OCTOPUS-20260918\jetstream-ledger"
STREAM = "OCTOPUS_EVENTS"
DURABLE = "vault-event-ledger"
FILTERS = ["octopus.events.>", "octopus.beat.>"]


def hub_password() -> str:
    try:
        parts = open(KEYS_FILE, encoding="utf-8", errors="replace").read().split()
        return parts[1] if len(parts) > 1 else ""
    except OSError:
        return ""


async def run(once: bool) -> int:
    pw = hub_password()
    if not pw:
        print("no hub password found")
        return 2
    nc = await nats.connect(HUB % pw)
    js = nc.jetstream()
    cfg = ConsumerConfig(durable_name=DURABLE, filter_subjects=FILTERS, ack_policy="explicit")
    sub = await js.pull_subscribe("", durable=DURABLE, stream=STREAM, config=cfg)
    os.makedirs(LEDGER_DIR, exist_ok=True)
    archived = 0
    idle_rounds = 0
    while True:
        try:
            msgs = await sub.fetch(50, timeout=4)
            idle_rounds = 0
        except Exception:  # noqa: BLE001 — timeout = nothing new
            msgs = []
            idle_rounds += 1
        for m in msgs:
            try:
                data = m.data.decode("utf-8", "replace")
                day = time.strftime("%Y-%m-%d", time.gmtime())
                out = os.path.join(LEDGER_DIR, "events-%s.jsonl" % day)
                with open(out, "a", encoding="utf-8") as fh:
                    fh.write(json.dumps({
                        "subject": m.subject,
                        "seq": (m.reply or {}).get("stream") if isinstance(m.reply, dict) else None,
                        "at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                        "data": data}, ensure_ascii=False) + "\n")
                await m.ack()
                archived += 1
            except Exception as exc:  # noqa: BLE001
                print("msg error: %s: %s" % (type(exc).__name__, exc), flush=True)
        if archived and archived % 25 == 0:
            print("archived %d messages" % archived, flush=True)
        if once and idle_rounds >= 1:
            break
        if not msgs:
            await asyncio.sleep(1 if once else 5)
    await nc.close()
    print(json.dumps({"archived": archived}))
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--once", action="store_true")
    a = ap.parse_args()
    raise SystemExit(asyncio.run(run(a.once)))
