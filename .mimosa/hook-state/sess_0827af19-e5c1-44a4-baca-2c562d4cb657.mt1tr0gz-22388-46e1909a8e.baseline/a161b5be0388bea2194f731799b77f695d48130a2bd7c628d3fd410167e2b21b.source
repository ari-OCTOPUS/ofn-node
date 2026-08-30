#!/usr/bin/env python3
"""Arm the hosted brain, then replace every guess about it with a measurement.

Run this once on the board after `OFN_REMOTE_API_KEY` is filled in. It is the
only script in this repository that deliberately spends money, so it is
deliberately small, deliberately loud, and deliberately does one call.

What it proves, in order, and why each one is worth a real call:

  1. **The key works at all.** A key that is present but wrong fails exactly
     like a key that is absent, because `RemoteBrain` fails closed. Without a
     probe, the difference between "not armed yet" and "armed with a dead
     credential" is invisible until a partner is waiting on an answer.

  2. **Scrubbing happens before the wire, not after.** The prompt below
     contains a planted email address. If it appears in the outgoing text or
     anywhere in the ledger, the redaction layer is not where it claims to be.

  3. **How slow this rung actually is, from this board, on this link.** The
     shipped latency numbers are extrapolations. The board is in Sydney behind
     a home connection; the number that matters is the one measured here.

  4. **What one call actually costs.** Both what the provider admits to and
     what the quota layer bills after the invisible-spend multiplier.

  5. **That the interactive path still refuses this rung** even now that it is
     armed — the one regression that would be silent and would be felt by
     every partner at once.

Deliberately *not* done here:

  * It writes to a throwaway state directory, so no synthetic rows land in the
    business ledger. The spend is real; the audit trail of it is this
    script's output, which belongs in the phase report.
  * It never touches the deep rung unless `--deep` is passed, and says so.
    That rung costs roughly four times as much and takes minutes.
  * It never prints, logs, or length-checks the key.

Usage:
    python3 deploy/brain-probe.py            # fast rung only
    python3 deploy/brain-probe.py --deep     # also measures fugu-ultra
"""

from __future__ import annotations

import os
import sys
import tempfile
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ofn import config, run                                        # noqa: E402
from ofn.adapters.ledger import Ledger                             # noqa: E402
from ofn.adapters.packloader import load_dir                       # noqa: E402
from ofn.adapters.router import ModelRouter                        # noqa: E402
from ofn.kernel import routing                                     # noqa: E402
from ofn.kernel.quota import NodeQuota                             # noqa: E402
from ofn.kernel.routing import (RouteRequest, Rung,                # noqa: E402
                                fits_interactive, may_escalate)
from ofn.kernel.tenancy import TenantRegistry                      # noqa: E402
from ofn.worker import Job, WorkQueue, Worker                      # noqa: E402

# A planted identifier. If this string survives to the wire or to the ledger,
# the scrubber is not doing its job and the probe fails.
CANARY = "canary.probe@example.invalid"

PROMPT = (
    "In one short sentence: name the single most useful question to ask a "
    "customer who requested a quote and then went quiet. "
    f"(Reply to {CANARY} if you need anything.)"
)


def rule(title: str) -> None:
    print(f"\n\033[1m── {title} " + "─" * max(0, 58 - len(title)) + "\033[0m")


def main(argv: list[str]) -> int:
    deep = "--deep" in argv
    cfg = config.load()

    rule("0 · armed?")
    if not cfg.remote_api_key:
        print("  OFN_REMOTE_API_KEY is empty.")
        print("  Fill it in ~/.config/ofn/secrets.env (chmod 600) and re-run.")
        print("  Do not paste the value into a chat, a commit, or this terminal's")
        print("  history — type it into the file with an editor.")
        return 1
    print("  key present (value not read, not printed, not measured)")
    print(f"  endpoint: {cfg.remote_base_url}")

    packs = load_dir(cfg.packs_dir)
    if not packs:
        print(f"  no packs found in {cfg.packs_dir} — cannot pick a tenant")
        return 1
    tenant = "ziman" if "ziman" in packs else sorted(packs)[0]

    registry = TenantRegistry(packs)
    quota = NodeQuota(estimated_capacity_tokens=cfg.estimated_capacity_tokens,
                      utilisation=cfg.utilisation,
                      shares={n: p.quota_share for n, p in packs.items()})

    tmp = tempfile.TemporaryDirectory(prefix="ofn-probe-")
    ledger = Ledger(os.path.join(tmp.name, "probe.sqlite"))
    scope = registry.scope(tenant)

    brains = run.build_brains(cfg, announce=False)
    for rung in (Rung.REMOTE, Rung.REMOTE_DEEP):
        if rung not in brains:
            print(f"  {rung.value} did not get wired — check build_brains")
            return 1

    # Record what we are about to overwrite, so the report can show both.
    before = dict(routing.WORST_CASE_MS)

    def one_call(*, wired: dict, idem: str, max_rung: Rung,
                 deep_ok: bool = False):
        """Run exactly one job to completion and return its THINK_DONE payload.

        A fresh worker per call, sharing the quota and the ledger, so the two
        rungs are measured independently and the spend still accumulates in
        one place.
        """
        # By sequence number, not by slicing a list. `read()` returns newest
        # first, so slicing off a prior length hands back the *oldest* rows —
        # which is how an early version of this script reported the fast
        # rung's numbers twice and called the second one the deep rung.
        head = ledger.head(scope)
        since = head.seq if head else 0
        worker = Worker(WorkQueue(), ModelRouter(wired, quota), registry,
                        ledger, now_epoch_s=config.epoch_seconds,
                        now_iso=config.now_iso)
        started = time.monotonic()
        worker.submit(scope, Job(tenant=tenant, task="probe", prompt=PROMPT,
                                 idem_key=idem, max_rung=max_rung,
                                 owner_approved_deep=deep_ok,
                                 estimated_tokens=400))
        worker.step()
        fresh = [e for e in ledger.read(scope) if e.seq > since]
        done = [e for e in fresh if e.kind == "THINK_DONE"]
        return (done[0].payload if done else None), fresh, \
            time.monotonic() - started

    def show(payload, wall_s) -> None:
        print(f"  ok · rung={payload['rung']} · path={payload['path']}")
        print(f"  measured latency : {payload['elapsed_ms']:,} ms "
              f"(wall clock {wall_s:.1f} s)")
        print(f"  billed to quota  : {payload['billed_tokens']:,} tokens "
              f"(after the {quota._multiplier}x invisible-spend multiplier)")
        print(f"  redactions made  : {payload['scrubbed'] or 'none'}")

    def explain_failure(fresh) -> None:
        rule("RESULT · the call did not succeed")
        for e in fresh:
            print(f"  {e.kind}: {e.payload}")
        print("\n  The most common causes, in order: wrong key, no DNS on the")
        print("  board, clock skew breaking TLS (`timedatectl set-ntp true`),")
        print("  or the provider rejecting the model name.")

    rule("1 · one real call on the fast rung (fugu)")
    print(f"  tenant: {tenant}   ·   this will cost real tokens")
    payload, fresh, wall_s = one_call(
        wired={Rung.RULES: brains[Rung.RULES], Rung.REMOTE: brains[Rung.REMOTE]},
        idem="probe-fast", max_rung=Rung.REMOTE)
    if payload is None:
        explain_failure(fresh)
        ledger.close(); tmp.cleanup()
        return 1
    show(payload, wall_s)
    events = list(ledger.read(scope))

    rule("2 · did the canary leak?")
    leaked = [e.kind for e in events if CANARY in str(e.payload)]
    if leaked:
        print(f"  ✗ FAIL — the address survived into: {leaked}")
        print("  Stop here and report this. Nothing else in this phase matters")
        print("  until PII is being removed before the call, not after it.")
        ledger.close(); tmp.cleanup()
        return 1
    print("  ✓ the planted address appears nowhere in the ledger")
    if not payload["scrubbed"]:
        print("  ⚠ but nothing was recorded as redacted either — check scrub.py")

    rule("3 · is the interactive path still refused?")
    ok = True
    for rung in (Rung.REMOTE, Rung.REMOTE_DEEP):
        if fits_interactive(rung):
            print(f"  ✗ FAIL — {rung.value} is now considered fast enough for a "
                  f"partner to wait on")
            ok = False
    decision = may_escalate(Rung.LOCAL,
                            RouteRequest(task="probe", interactive=True,
                                         max_rung=Rung.REMOTE),
                            lower_reported_insufficient=True)
    if decision.allowed:
        print("  ✗ FAIL — an interactive request was allowed onto the hosted rung")
        ok = False
    else:
        print(f"  ✓ refused: {decision.rule}")
    if not ok:
        ledger.close(); tmp.cleanup()
        return 1

    if deep:
        rule("4 · one real call on the deep rung (fugu-ultra)")
        print("  this can take minutes and costs ~4x. Ctrl-C is safe.")
        # The fast rung is left out of this router's wiring on purpose. It is
        # not a way around the no-implicit-escalation rule — that rule is what
        # makes this necessary. A router holding both rungs would get a good
        # answer from `fugu` and correctly stop there, so the deep rung could
        # never be measured. Removing it makes the documented `remote:absent`
        # path run instead, which is the only honest way to reach the rung
        # below without faking an insufficiency that did not happen.
        deep_payload, deep_fresh, deep_wall = one_call(
            wired={Rung.RULES: brains[Rung.RULES],
                   Rung.REMOTE_DEEP: brains[Rung.REMOTE_DEEP]},
            idem="probe-deep", max_rung=Rung.REMOTE_DEEP, deep_ok=True)
        if deep_payload is None:
            print("  the deep rung did not answer:")
            for e in deep_fresh:
                print(f"    {e.kind}: {e.payload}")
        else:
            show(deep_payload, deep_wall)
    else:
        rule("4 · deep rung (fugu-ultra)")
        print("  skipped. Re-run with --deep when Ari asks for it.")

    rule("5 · calibration — guesses replaced by measurements")
    for rung in (Rung.REMOTE, Rung.REMOTE_DEEP):
        b, a = before[rung], routing.WORST_CASE_MS[rung]
        note = "unchanged (the measurement was faster; we never lower)" \
            if a == b else f"RAISED from {b:,}"
        print(f"  {rung.value:<12} {a:>10,} ms   {note}")

    print("\n  These live in memory only. If the measured number is "
          "consistently\n  higher than the shipped estimate, edit "
          "WORST_CASE_MS in\n  ofn/kernel/routing.py so a restart does not "
          "forget what we learned.")

    rule("6 · paste this into the phase report")
    print(f"""
    fugu measured latency  : {payload['elapsed_ms']:,} ms
    fugu billed tokens     : {payload['billed_tokens']:,} (one ~400-token call)
    weekly ceiling in use  : {quota.node_ceiling:,} tokens \
({int(cfg.utilisation * 100)}% of {cfg.estimated_capacity_tokens:,})
    capacity is an estimate: {quota.capacity_is_estimate}
    calls this probe made  : {2 if deep else 1}
    canary leaked          : no
    interactive still safe : yes
""")

    ledger.close()
    tmp.cleanup()
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
