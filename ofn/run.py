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
from .adapters.audience_store import AudienceStore
from .adapters.boot import BootSupervisor
from .kernel.callbudget import CallBudget
from .adapters.consent_store import ConsentStore
from .adapters.facts import FactStore
from .adapters.http_api import ApiApp, HostMap, serve
from .adapters.ledger import Ledger
from .adapters.media import MediaStore
from .adapters.outbox import Outbox
from .adapters.packloader import load_dir
from .adapters.products import ProductStore
from .adapters.studio_store import StudioStore
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

    # One store for every leg: the rows carry `tenant_id`, and the pack of
    # each leg supplies its own cost formula.
    ziman = packs["ziman"]
    products = ProductStore(cfg.products_path,
                            cost_fields=ziman.cost_fields,
                            labour_hours_field=ziman.labour_hours_field,
                            labour_rate_field=ziman.labour_rate_field)

    # The studio leg's three: what is being made, who agreed to be in it,
    # and where the bytes live. Opened here so their schemas exist from the
    # first boot rather than the first upload.
    studio = StudioStore(cfg.studio_path)
    audience = AudienceStore(cfg.audience_path)
    consent = ConsentStore(cfg.consent_path)
    media = MediaStore(cfg.photos_root)

    return Node(products=products, studio=studio, consent=consent, media=media,
                audience=audience,
                registry=registry, quota=quota, ledger=ledger, facts=facts,
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
    # Extra paths the same file answers on. Saba's mini app lives at
    # `app.<domain>/sabaapp`, so the studio port has to serve its shell there
    # as well as at the root — a Telegram Web App URL is fixed in the bot's
    # menu button and is not something a partner can be asked to change.
    aliases = {cfg.ports["studio"]: ("/sabaapp", "/sabaapp/")}

    out: dict[str, dict[str, bytes]] = {}
    for port, name in mapping.items():
        path = os.path.join(root, name)
        try:
            with open(path, "rb") as fh:
                data = fh.read()
            served = {"/index.html": data}
            for alias in aliases.get(port, ()):
                served[alias] = data
            out[port] = served
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
        partner_user_ids=cfg.partner_user_ids,
        now=config.epoch_seconds,
        questions_for=node.questions_for,
        submit_answer=node.submit_answer,
        status_for=node.status_for,
        products_for=node.products_for,
        create_product=node.create_product,
        update_product=node.update_product,
        attach_photo=node.attach_product_photo,
        studio_board=node.studio_board,
        create_draft=node.create_draft,
        attach_media=node.attach_media,
        publish_draft=node.publish_draft,
        record_felt=node.record_felt,
        brain_status=node.brain_status,
        brain_probe=node.run_brain_probe,
        owner_ask=node.ask_owner_question,
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
    # Say out loud who can get in. An empty allowlist is the correct default
    # and a locked door, but a door nobody knows is locked wastes an evening
    # on "the login is broken" when the login is working exactly as told.
    for leg, ids in sorted(cfg.partner_user_ids.items()):
        print(f"  allowlist {leg}: "
              + (f"{len(ids)} account(s)" if ids
                 else "EMPTY — nobody can enter this shell (set "
                      f"OFN_PARTNER_USER_IDS_{leg.upper()})"))

    worker = build_worker(cfg, node)
    # Phase A: the owner's panel can now reach the brain. The partner
    # surfaces cannot, and will not until the extraction layer exists.
    # Attached after `build_api`, and that is safe rather than lucky: the
    # API holds `node.brain_status` as a bound method, which reads
    # `self.worker` when it is called. Passing `node.worker` directly would
    # capture the None and look identical until the first request.
    node.worker = worker
    node.call_budget = CallBudget()
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
