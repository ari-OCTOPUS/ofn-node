"""Service entry point: boot, serve, beat.

Four listeners — one per shell — because the platform now restricts its
client APIs to the exact origin registered for each app. One process, four
sockets on loopback; the tunnel maps a hostname to each.

The watchdog loop lives on the main thread and the servers on daemon threads,
so a wedged HTTP handler cannot keep the process alive by holding the main
thread hostage. If the health probe stops passing, the ping stops, and the
supervisor does what supervisors are for.
"""

from __future__ import annotations

import os
import signal
import sys
import threading
import time

from . import config
from .adapters.boot import BootSupervisor
from .adapters.facts import FactStore
from .adapters.http_api import ApiApp, HostMap, serve
from .adapters.ledger import Ledger
from .adapters.outbox import Outbox
from .adapters.packloader import load_dir
from .adapters.watchdog import HealthGate, Notifier, beat, watchdog_interval_s
from .adapters.remote_brain import RemoteBrain
from .adapters.router import ModelRouter, RulesBrain
from .kernel.quota import NodeQuota
from .kernel.routing import Rung
from .kernel.tenancy import TenantRegistry
from .node import Node
from .worker import WorkQueue, Worker, loop as worker_loop

_stop = threading.Event()


def _shutdown(signum, frame):        # noqa: ARG001
    _stop.set()


def build_node(cfg: config.Config) -> Node:
    os.makedirs(cfg.state_dir, exist_ok=True)
    packs = load_dir(cfg.packs_dir)
    registry = TenantRegistry(packs)
    quota = NodeQuota(
        estimated_capacity_tokens=cfg.estimated_capacity_tokens,
        utilisation=cfg.utilisation,
        shares={name: p.quota_share for name, p in packs.items()})

    ledger = Ledger(cfg.ledger_path)
    facts = FactStore(cfg.facts_path)
    outbox = Outbox(cfg.outbox_path)

    report = BootSupervisor(
        db_paths=cfg.db_paths, tenants=list(registry),
        now_epoch_s=config.epoch_seconds, state_dir=cfg.state_dir,
    ).run(ledger=ledger, outbox=outbox, now_iso=config.now_iso())

    return Node(registry=registry, quota=quota, ledger=ledger, facts=facts,
                outbox=outbox, now_epoch_s=config.epoch_seconds,
                now_iso=config.now_iso,
                base_closed_gates=cfg.base_closed_gates, boot=report)


def load_web(cfg: config.Config) -> dict[str, dict[str, bytes]]:
    """Read each shell's HTML once at boot, keyed by the port that serves it.

    Read once rather than per-request because these files never change while
    the process runs, and a flash-backed board should not re-read the same
    120 KB on every screen open. If a file is missing the port still serves
    the API — a partner sees a blank page rather than a dead node, and the
    owner sees exactly which file is absent in the boot log.
    """
    root = os.path.join(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__))), "web")
    mapping = {cfg.ports["ziman"]: "ziman.html",
               cfg.ports["lead"]: "lead.html",
               cfg.ports["studio"]: "studio.html",
               cfg.ports["owner"]: "panel.html"}
    out: dict[str, dict[str, bytes]] = {}
    for port, name in mapping.items():
        path = os.path.join(root, name)
        try:
            with open(path, "rb") as fh:
                out[port] = {"/index.html": fh.read()}
        except OSError:
            print(f"  ⚠ {name} missing — port {port} serves API only")
            out[port] = {}
    return out


def build_api(cfg: config.Config, node: Node) -> ApiApp:
    return ApiApp(
        node.registry,
        HostMap(tenants=cfg.hosts, owner_host=cfg.owner_host),
        bot_tokens=cfg.bot_tokens,
        session_secret=cfg.session_secret,
        owner_user_ids=cfg.owner_user_ids,
        now=config.epoch_seconds,
        questions_for=node.questions_for,
        submit_answer=node.submit_answer,
        status_for=node.status_for,
        owner_queue=node.owner_queue,
        owner_decide=node.owner_decide,
        owner_status=node.owner_status,
        owner_events=node.recent_events,
    )


SYSTEM_PROMPT = ("You are assisting a small business operator. "
                 "Answer concisely. Never invent a number.")


def build_brains(cfg: config.Config, *, announce: bool = True) -> dict:
    """Wire one brain per rung.

    The rules rung is always present and always first — most of what this node
    does is a lookup, and routing a lookup through a hosted model would be
    slower, costlier, and less explainable than a dictionary.

    The hosted rungs are only wired if a key exists. With no key they are
    simply absent, and the router records `remote:absent` rather than
    inventing a path around them. That is the correct state until the secrets
    are rotated.

    The two hosted rungs share a key and share nothing else. `fugu` is the
    fast one and gets the standard timeout; `fugu-ultra` reasons for minutes
    and gets fifteen of them, because a timeout shorter than the model's
    normal working time converts correct behaviour into a failure rate.

    Kept separate from `build_worker` so the deployment probe can exercise
    exactly this wiring rather than a copy of it that might drift.
    """
    brains = {Rung.RULES: RulesBrain({})}
    if cfg.remote_api_key:
        brains[Rung.REMOTE] = RemoteBrain(
            api_key=cfg.remote_api_key, model="fugu",
            base_url=cfg.remote_base_url,
            system_prompt=SYSTEM_PROMPT)
        brains[Rung.REMOTE_DEEP] = RemoteBrain(
            api_key=cfg.remote_api_key, model="fugu-ultra",
            base_url=cfg.remote_base_url,
            reasoning_effort="high", timeout_s=900,
            system_prompt=SYSTEM_PROMPT)
    elif announce:
        print("  no remote key — hosted rungs are NOT ARMED (correct for now)")
    return brains


def build_worker(cfg: config.Config, node: Node) -> Worker:
    """Assemble the background thinker."""
    router = ModelRouter(build_brains(cfg), node.quota,
                         on_event=lambda kind, payload: None)
    return Worker(WorkQueue(), router, node.registry, node.ledger,
                  now_epoch_s=config.epoch_seconds, now_iso=config.now_iso)


def main() -> int:
    cfg = config.load()
    if not cfg.session_secret:
        print("OFN_SESSION_SECRET is not set — refusing to start. "
              "Sessions cannot be signed without it.", file=sys.stderr)
        return 1

    node = build_node(cfg)
    print(node.boot.summary() if node.boot else "boot: no report")

    api = build_api(cfg, node)
    web = load_web(cfg)
    servers = []
    for port in sorted(set(cfg.ports.values())):
        # One listener per shell. The messaging platform restricts its client
        # APIs to the exact origin registered for each app, so the shells
        # cannot share a port and be routed by path.
        srv = serve(api, port, static=web.get(port))
        threading.Thread(target=srv.serve_forever, daemon=True).start()
        servers.append(srv)
    print(f"listening on 127.0.0.1: {sorted(set(cfg.ports.values()))}")

    worker = build_worker(cfg, node)
    threading.Thread(target=worker_loop, args=(worker, _stop),
                     daemon=True).start()
    print(f"worker running — {worker.status()}")

    signal.signal(signal.SIGTERM, _shutdown)
    signal.signal(signal.SIGINT, _shutdown)

    notifier = Notifier()
    gate = HealthGate(node.healthy, tolerate_failures=2)
    notifier.ready()
    notifier.status(f"{len(node.registry)} legs · "
                    f"{'SAFE MODE' if 'safe_mode' in node.closed_gates else 'normal'}")

    interval = watchdog_interval_s(default=15.0)
    while not _stop.is_set():
        beat(notifier, gate)
        _stop.wait(interval)

    notifier.stopping()
    for srv in servers:
        srv.shutdown()
    node.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
