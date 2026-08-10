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
from .adapters.advisor import Advisor
from .adapters.audience_store import AudienceStore
from .adapters.boot import BootSupervisor
from .kernel.callbudget import CallBudget
from .adapters.consent_store import ConsentStore
from .adapters.facts import FactStore
from .adapters.http_api import ApiApp, HostMap, serve
from .adapters.ledger import Ledger
from .adapters.lead_store import LeadStore
from .adapters.marketing_inbox import MarketingInbox
from .adapters.marketing_store import MarketingStore
from .adapters.media import MediaStore
from .adapters.outbox import Outbox
from .adapters.packloader import load_dir
from .adapters.products import ProductStore
from .adapters.studio_store import StudioStore
from .adapters.studio_assistant import StudioAssistantStore
from .adapters.watchdog import HealthGate, Notifier, beat, watchdog_interval_s
from .adapters.remote_brain import RemoteBrain
from .adapters.router import ModelRouter, RulesBrain
from .kernel.quota import NodeQuota
from .kernel.routing import Rung
from .kernel.tenancy import TenantRegistry
from .node import Node
from .worker import WorkQueue, Worker, loop as worker_loop

_stop = threading.Event()


def _shared_memory(cfg):
    """Open the shared three-layer memory, or None if it is unavailable.

    fugu_core is an optional dependency: the node boots and runs fully without
    it, and every call site treats None as "no shared memory today". This way
    a missing or corrupt memory file never breaks the partner shells.
    """
    try:
        from fugu_core.memory import Memory
    except Exception:
        return None
    try:
        return Memory(cfg.memory_path)
    except Exception:
        return None


def _shutdown(signum, frame):        # noqa: ARG001
    _stop.set()


def build_node(cfg: config.Config) -> Node:
    # mode=0o700: the state directory holds SQLite databases with tenant
    # data. Only the owner should read or write it. When the directory is
    # created fresh, this mode is applied; when it already exists (e.g. from
    # an older installer that used 0755), the mode is left unchanged here —
    # correcting it is a deliberate operator action, not a side effect of boot.
    os.makedirs(cfg.state_dir, exist_ok=True, mode=0o700)
    packs = load_dir(cfg.packs_dir)
    registry = TenantRegistry(packs)
    quota = NodeQuota(
        estimated_capacity_tokens=cfg.estimated_capacity_tokens,
        utilisation=cfg.utilisation,
        shares={name: p.quota_share for name, p in packs.items()})

    ledger = Ledger(cfg.ledger_path)
    facts = FactStore(cfg.facts_path)
    outbox = Outbox(cfg.outbox_path)

    # The shared fugu_core memory is checked at boot like every other DB
    # (finding 23): it lives outside state_dir, so it is added explicitly.
    # "not yet created" is fine — fugu_core creates it lazily.
    db_paths = dict(cfg.db_paths)
    db_paths["memory"] = cfg.memory_path
    report = BootSupervisor(
        db_paths=db_paths, tenants=list(registry),
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
    marketing = MarketingStore(cfg.marketing_path)
    painting = LeadStore(cfg.painting_path)
    painting.ensure_seed_channels("lead", config.now_iso())
    assistant = StudioAssistantStore(cfg.assistant_path, shared_memory=_shared_memory(cfg))
    inbox = MarketingInbox(cfg.inbox_path)
    from .adapters.inbound_rate import InboundRateLimiter
    from .adapters.connector_metrics import ConnectorMetrics
    rate_limiter = InboundRateLimiter()
    connector_metrics = ConnectorMetrics()

    return Node(products=products, studio=studio, consent=consent, media=media,
                audience=audience, marketing=marketing, painting=painting, assistant=assistant, backup_root=cfg.backup_root,
                registry=registry, quota=quota, ledger=ledger, facts=facts,
                outbox=outbox, now_epoch_s=config.epoch_seconds,
                now_iso=config.now_iso, state_dir=cfg.state_dir,
                base_closed_gates=cfg.base_closed_gates, boot=report,
                inbox=inbox, rate_limiter=rate_limiter,
                connector_metrics=connector_metrics)


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

    # The font, served from this node rather than a CDN. Every shell gets it
    # on its own port: the platform ties each app to one origin, so a shared
    # font host would be a fourth origin and a fourth thing to be blocked.
    font_path = os.path.join(root, "font", "vazirmatn.woff2")
    try:
        with open(font_path, "rb") as fh:
            font = fh.read()
    except OSError:
        font = b""
        print("  ⚠ font missing — shells fall back to whatever the phone has")

    out: dict[str, dict[str, bytes]] = {}
    for port, name in mapping.items():
        path = os.path.join(root, name)
        try:
            with open(path, "rb") as fh:
                data = fh.read()
            served = {"/index.html": data}
            if font:
                served["/font/vazirmatn.woff2"] = font
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
        webhook_handler=node.handle_webhook,
        questions_for=node.questions_for,
        submit_answer=node.submit_answer,
        status_for=node.status_for,
        products_for=node.products_for,
        create_product=node.create_product,
        update_product=node.update_product,
        attach_photo=node.attach_product_photo,
        studio_board=node.studio_board,
        studio_marketing=node.studio_marketing,
        route_preview=node.route_preview,
        send_to_outbox=node.send_to_outbox,
        studio_reading=node.studio_reading,
        studio_media=node.studio_media,
        export_album=node.export_album,
        studio_gallery=node.studio_gallery,
        studio_overview=node.studio_overview,
        studio_guidance=node.studio_guidance,
        set_labels=node.set_draft_labels,
        set_media_labels=node.set_media_labels,
        describe_media=node.describe_media,
        add_media=node.add_to_library,
        create_album=node.create_album,
        file_media=node.file_media,
        delete_album=node.delete_album,
        delete_media=node.delete_media,
        assistant_chat=node.studio_assistant_chat,
        assistant_update=node.update_studio_assistant,
        assistant_history=node.studio_assistant_history,
        assistant_suggest=node.studio_assistant_suggest,
        request_reading=node.request_studio_reading,
        judge_reading=node.judge_studio_finding,
        create_draft=node.create_draft,
        attach_media=node.attach_media,
        publish_draft=node.publish_draft,
        record_felt=node.record_felt,
        brain_status=node.brain_status,
        brain_probe=node.run_brain_probe,
        run_marketing_cycle=node.run_marketing_cycle,
        owner_ask=node.ask_owner_question,
        owner_queue=node.owner_queue,
        owner_decide=node.owner_decide,
        owner_status=node.owner_status,
        owner_events=node.recent_events,
        owner_metrics=node.owner_metrics,
        owner_observability=node.owner_observability,
        engage_kill=node.engage_kill,
        release_kill=node.release_kill,
        owner_snapshot=node.owner_snapshot,
        owner_businesses=node.owner_businesses,
        owner_business_snapshot=node.owner_business_snapshot,
        owner_core_snapshot=node.owner_core_snapshot,
        owner_risks=node.owner_risks,
        owner_ledger_summary=node.owner_ledger_summary,
        painting_dashboard=node.painting_dashboard,
        hypno_edge_decision=node.hypno_edge_decision,
        hypno_edge_daily=node.hypno_edge_daily,
        hypno_edge_history=node.hypno_edge_history,
        painting_leads=node.painting_leads,
        create_painting_lead=node.create_painting_lead,
        update_painting_lead=node.update_painting_lead,
        upsert_painting_channel=node.upsert_painting_channel,
        upsert_painting_campaign=node.upsert_painting_campaign,
        upsert_painting_module=node.upsert_painting_module,
        create_painting_interaction=node.create_painting_interaction,
        update_painting_interaction=node.update_painting_interaction,
        create_painting_account=node.create_painting_account,
        create_painting_tender=node.create_painting_tender,
        create_painting_vendor_application=node.create_painting_vendor_application,
        send_lead_reply=node.send_lead_reply,
        send_lead_quote=node.send_lead_quote,
        owner_mini_webs_summary=node.owner_mini_webs_summary,
        owner_telegram_summary=node.owner_telegram_summary,
        mini_apps=tuple({
            "id": name,
            "business_id": None if name == "owner" else name,
            "role": "owner" if name == "owner" else "partner",
            "listen_port": cfg.ports[name],
            "paths": (("/", "/index.html", "/sabaapp", "/sabaapp/")
                      if name == "studio" else ("/", "/index.html")),
        } for name in ("lead", "studio", "ziman", "owner")),
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


def arm_node_brain(cfg: config.Config, node: Node, *,
                   run_worker_loop: bool = False) -> Worker | None:
    """Wire the hosted brain onto a node, without starting the HTTP servers.

    `main()` builds the node, arms the brain, then starts servers and the
    worker loop. A one-shot script like `marketing_run` needs the same
    armed node but not the loop: it calls the router directly. This function
    is the shared wiring so the two paths cannot drift — a brain that the
    script forgot to arm is exactly the bug this exists to prevent.

    Returns the Worker (so `main` can start its loop), or None when
    `run_worker_loop` is False (the script path, which does not loop).
    """
    worker = build_worker(cfg, node)
    node.worker = worker
    node.call_budget = CallBudget()
    # Same router the worker uses, so there is one place that spends and
    # one budget that counts — whether the call comes from the API, the
    # worker loop, or a one-shot cycle run.
    node.router = worker._router
    node.advisor = Advisor()
    if run_worker_loop:
        threading.Thread(target=worker_loop, args=(worker, _stop),
                         daemon=True).start()
        return worker
    return None


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

    worker = arm_node_brain(cfg, node, run_worker_loop=True)
    # Phase A: the owner's panel can now reach the brain. The partner
    # surfaces cannot, and will not until the extraction layer exists.
    # Attached after `build_api`, and that is safe rather than lucky: the
    # API holds `node.brain_status` as a bound method, which reads
    # `self.worker` when it is called. Passing `node.worker` directly would
    # capture the None and look identical until the first request.
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
