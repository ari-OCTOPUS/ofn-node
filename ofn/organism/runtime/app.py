import argparse
import fcntl
import json
import os
import signal
import threading
import time
import urllib.parse
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from ofn.organism import ORGANISM_ID
from ofn.organism.cognition.backend import AskCascade, LocalCortex
from ofn.organism.cognition.learn import list_topics
from ofn.organism.cognition.teacher import teacher_status
from ofn.organism.contracts.events import make_event
from ofn.organism.event_kernel.kernel import EventKernel
from ofn.organism.growth.futures import seed_futures
from ofn.organism.growth.habits import heartbeat_interval_s, set_meta
from ofn.organism.growth.parent import seed_lessons, write_parent_decisions
from ofn.organism.homeostasis.core import measure, transition
from ofn.organism.identity.heartbeat import beat
from ofn.organism.identity.ledger import (
    IdentityChainError,
    append_identity_event,
    ensure_identity_genesis,
    verify_identity_chain,
)
from ofn.organism.memory.episodic import recall, remember
from ofn.organism.persistence.db import connect
from ofn.organism.runtime.life_cycle import (
    enrich_snapshot,
    latest_utterance,
    tick as life_tick,
)
from ofn.organism.school.eval import run_transformation_eval
from ofn.organism.runtime.lan_auth import (
    TOKEN_HEADER,
    failure_cooled,
    lan_token_required,
    load_lan_token,
    record_failure,
    record_success,
    tokens_match,
)
from ofn.organism.runtime.public_status import (
    PUBLIC_STATUS_PATH,
    first_stage_label,
    meta_value,
    write_public_status,
)
from ofn.organism.identity.attestation import read_attestation, write_attestation

BOOT_ID = uuid.uuid4().hex
STARTED_WALL = time.time()
STARTED_MONOTONIC = time.monotonic()
STATE = {
    "health_state": "BOOTSTRAP",
    "local_cortex": "STARTING",
    "last_event_sequence": 0,
    "ask_lan": False,
}
STATE_LOCK = threading.RLock()
MAX_REQUEST_BYTES = 16 * 1024
MAX_ASK_TEXT_CHARS = 4000
LAN_BIND_HOST = "192.168.0.180"
SALIENCE = {
    "heartbeat": 0.2,
    "ask": 0.55,
    "utterance": 0.85,
    "self_model": 0.7,
    "world": 0.7,
    "growth": 0.9,
    "attention": 0.8,
    "development": 0.75,
    "inner": 0.55,
    "school": 0.9,
}


def _remember_event(con, ev):
    payload = ev.get("payload")
    if not isinstance(payload, dict):
        payload = {"priority": ev.get("priority")}
    remember(
        con,
        ev["event_id"],
        ev["event_type"],
        payload,
        salience=SALIENCE.get(ev["event_type"], 0.4),
        outcome="handled",
    )


def maybe_stable(con, measured_health, alerts, *, count=False):
    if alerts or measured_health not in {"OBSERVING", "STABLE"}:
        if count:
            set_meta(con, "consecutive_stable_body", "0")
        return measured_health
    raw = meta_value(con, "consecutive_stable_body", "0") or "0"
    try:
        consecutive = int(raw)
    except ValueError:
        consecutive = 0
    if count:
        consecutive += 1
        set_meta(con, "consecutive_stable_body", str(consecutive))
    if consecutive >= 5:
        return "STABLE"
    return measured_health


def build(db_path):
    con = connect(Path(db_path))
    k = EventKernel(con)

    def on_any(ev):
        _remember_event(con, ev)

    k.register("*", on_any)
    return con, k


def identity_status(con):
    chain = verify_identity_chain(con)
    return {
        "identity_chain_valid": chain["valid"],
        "identity_chain_entries": chain["entries"],
        "identity_chain_first_hash": chain["first_hash"],
        "identity_chain_last_hash": chain["last_hash"],
        "identity_chain_error": chain["error"],
        "identity_chain_scope": "identity_ledger_v1_from_genesis_forward",
        "identity_chain_verification_scope": chain["verification_scope"],
        "identity_chain_external_anchor": chain["external_anchor"],
        "identity_chain_tail_truncation_detectable": chain[
            "tail_truncation_detectable"
        ],
        "legacy_heartbeats_in_chain": False,
    }


def effective_measurement(con):
    measured = measure()
    synthetic_state = meta_value(con, "lab_synthetic_health_state")
    synthetic_reason = meta_value(con, "lab_synthetic_health_reason")
    if synthetic_state in {"DEGRADED", "SAFE_HALT"}:
        measured = dict(measured)
        measured["health_state"] = synthetic_state
        measured["alerts"] = list(measured.get("alerts", [])) + [
            f"LAB_SYNTHETIC_{synthetic_state}:{synthetic_reason or 'UNSPECIFIED'}"
        ]
    return measured


def apply_health_state(con, measured_health, alerts, source):
    with STATE_LOCK:
        previous = STATE["health_state"]
        current = transition(previous, measured_health)
        STATE["health_state"] = current
        if current != previous:
            try:
                append_identity_event(
                    con,
                    BOOT_ID,
                    "health_transition",
                    {
                        "previous": previous,
                        "current": current,
                        "source": source,
                        "alerts": alerts,
                    },
                )
            except IdentityChainError as exc:
                alerts.append(f"IDENTITY_CHAIN_WRITE_ERROR:{exc}")
        return current


def get_pure_enabled() -> bool:
    return os.environ.get("OCTOPUS_GET_PURE", "0") == "1"


def organism_snapshot(
    con,
    kernel,
    public_status_path=PUBLIC_STATUS_PATH,
    persist: bool | None = None,
    mutate_runtime_state: bool | None = None,
):
    persist_writes = (not get_pure_enabled()) if persist is None else persist
    mutate_state = persist_writes if mutate_runtime_state is None else mutate_runtime_state
    measured = effective_measurement(con)
    cortex = LocalCortex()
    cortex_available = cortex.available()
    alerts = list(measured.get("alerts", []))
    measured_health = maybe_stable(con, measured["health_state"], alerts, count=False)
    if not cortex_available:
        alerts.append("CORTEX_DOWN")
        if measured_health != "SAFE_HALT":
            measured_health = "DEGRADED"
    if persist_writes:
        health_state = apply_health_state(
            con,
            measured_health,
            alerts,
            "organism_snapshot",
        )
    else:
        health_state = measured_health
    if mutate_state:
        with STATE_LOCK:
            STATE["local_cortex"] = (
                "AVAILABLE" if cortex_available else "DEGRADED"
            )
            state = dict(STATE)
    else:
        with STATE_LOCK:
            state = dict(STATE)
        state["local_cortex"] = (
            "AVAILABLE" if cortex_available else "DEGRADED"
        )
    body = {
        "organism_id": ORGANISM_ID,
        "boot_id": BOOT_ID,
        "age_seconds": int(time.monotonic() - STARTED_MONOTONIC),
        "health_state": health_state,
        "autonomy_state": "PROPOSE_ONLY",
        "last_event_sequence": kernel.metrics["last_seq"] if kernel else 0,
        "local_cortex": state["local_cortex"],
        "external_api": "DISABLED",
        "teacher": teacher_status(),
        "memory_status": "AVAILABLE",
        "unknowns": [
            item["name"]
            for item in measured["signals"]
            if item["state"] == "UNKNOWN"
        ],
        "current_experiment": "board-life-001",
        "model_failure_is_organism_failure": False,
        "first_stage_label": first_stage_label(con),
        "alerts": alerts,
    }
    body.update(identity_status(con))
    with STATE_LOCK:
        ask_lan = bool(STATE.get("ask_lan"))
    if persist_writes:
        body = enrich_snapshot(con, body, measured, ask_lan=ask_lan)
        utterance = latest_utterance(con)
        if utterance:
            body["last_utterance"] = utterance.get("text")
            body["last_utterance_kind"] = utterance.get("kind")
        write_public_status(con, body, path=public_status_path)
    return body


class Handler(BaseHTTPRequestHandler):
    con = None
    kernel = None
    asker = None
    public_status_path = PUBLIC_STATUS_PATH

    def log_message(self, *args):
        return

    def _send_json(self, status, body):
        raw = json.dumps(
            body,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(raw)

    def _loopback_listener(self) -> bool:
        host = self.server.server_address[0]
        return host in {"127.0.0.1", "::1"}

    def _public_cached(self) -> dict:
        path = Path(self.public_status_path)
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return {}
        return payload if isinstance(payload, dict) else {}

    def _get_view(self) -> dict:
        persist = not get_pure_enabled()
        snapshot = organism_snapshot(
            self.con,
            self.kernel,
            self.public_status_path,
            persist=persist,
            mutate_runtime_state=persist,
        )
        if persist:
            return snapshot
        public = self._public_cached()
        for key in (
            "world_hosts",
            "self_model",
            "growth",
            "season",
            "school",
            "development",
            "inner",
            "futures",
            "topics",
            "teacher",
            "place",
            "discovery",
            "last_utterance",
            "last_utterance_kind",
            "soak",
        ):
            if snapshot.get(key) in (None, {}, []) and key in public:
                snapshot[key] = public[key]
        if not snapshot.get("topics"):
            snapshot["topics"] = list_topics(self.con)
            snapshot["topics_count"] = len(snapshot["topics"] or [])
        return snapshot

    def _authorize(self, path: str) -> str:
        if not lan_token_required():
            return "ok"
        if path == "/health" and self._loopback_listener():
            return "ok"
        peer = self.client_address[0]
        try:
            expected = load_lan_token()
        except Exception:
            record_failure(peer)
            return "unauthorized"
        if not expected:
            record_failure(peer)
            return "unauthorized"
        offered = self.headers.get(TOKEN_HEADER) or ""
        if tokens_match(offered, expected):
            record_success(peer)
            return "ok"
        if failure_cooled(peer):
            return "cooldown"
        record_failure(peer)
        return "unauthorized"

    def _reject_auth(self, kind: str) -> None:
        if kind == "cooldown":
            self._send_json(429, {"error": "auth_cooldown"})
            return
        self._send_json(401, {"error": "unauthorized"})

    def _bounded_length(self, *, allow_empty: bool) -> int | None:
        raw = self.headers.get("Content-Length", "0")
        try:
            content_length = int(raw)
        except ValueError:
            self._send_json(400, {"error": "invalid_content_length"})
            return None
        if content_length < 0 or content_length > MAX_REQUEST_BYTES:
            self._send_json(413, {"error": "request_size_out_of_range"})
            return None
        if not allow_empty and content_length < 1:
            self._send_json(413, {"error": "request_size_out_of_range"})
            return None
        return content_length

    def do_GET(self):
        parsed = urllib.parse.urlsplit(self.path)
        if self._bounded_length(allow_empty=True) is None:
            return
        decision = self._authorize(parsed.path)
        if decision != "ok":
            self._reject_auth(decision)
            return
        persist = not get_pure_enabled()
        if parsed.path == "/health":
            with STATE_LOCK:
                health = STATE.get("health_state")
            self._send_json(
                200,
                {
                    "ok": True,
                    "health_state": health,
                    "loopback": self._loopback_listener(),
                },
            )
            return
        if parsed.path == "/api/v1/organism":
            self._send_json(200, self._get_view())
            return
        if parsed.path == "/api/v1/episodes":
            query = urllib.parse.parse_qs(parsed.query)
            try:
                limit = int(query.get("limit", ["20"])[0])
            except (TypeError, ValueError):
                self._send_json(400, {"error": "invalid_limit"})
                return
            if limit < 1 or limit > 100:
                self._send_json(400, {"error": "limit_must_be_between_1_and_100"})
                return
            episodes = recall(self.con, limit=limit)
            provenance_complete = all(
                bool(item.get("source_event_id"))
                and item.get("provenance_valid") is True
                for item in episodes
            )
            self._send_json(200, {
                "episodes": episodes,
                "count": len(episodes),
                "provenance_complete": provenance_complete,
            })
            return
        if parsed.path == "/api/v1/self":
            snapshot = self._get_view()
            self._send_json(200, snapshot.get("self_model") or snapshot)
            return
        if parsed.path == "/api/v1/world":
            snapshot = self._get_view()
            self._send_json(
                200,
                {
                    "hosts": snapshot.get("world_hosts") or [],
                    "limits": ["192.168.0.0/24"],
                },
            )
            return
        if parsed.path == "/api/v1/utterance":
            self._send_json(200, latest_utterance(self.con) or {"text": None})
            return
        if parsed.path == "/api/v1/growth":
            self._send_json(200, self._get_view().get("growth") or {})
            return
        if parsed.path == "/api/v1/place":
            self._send_json(200, self._get_view().get("place") or {})
            return
        if parsed.path == "/api/v1/tools":
            snapshot = self._get_view()
            self._send_json(
                200,
                {
                    "tools": ["place", "body", "neighbors", "senses"],
                    "discovery": snapshot.get("discovery") or {},
                },
            )
            return
        if parsed.path == "/api/v1/development":
            self._send_json(200, self._get_view().get("development") or {})
            return
        if parsed.path == "/api/v1/lessons":
            development = self._get_view().get("development") or {}
            self._send_json(
                200,
                {
                    "lessons": development.get("lessons") or [],
                    "count": development.get("lessons_taught") or 0,
                    "stage": development.get("stage"),
                },
            )
            return
        if parsed.path == "/api/v1/school":
            self._send_json(200, self._get_view().get("school") or {})
            return
        if parsed.path == "/api/v1/inner":
            self._send_json(200, self._get_view().get("inner") or {})
            return
        if parsed.path == "/api/v1/futures":
            self._send_json(
                200,
                {
                    "kind": "hypothesis",
                    "paths": self._get_view().get("futures") or [],
                    "executable": False,
                },
            )
            return
        if parsed.path == "/api/v1/season":
            self._send_json(200, self._get_view().get("season") or {})
            return
        if parsed.path == "/api/v1/eval":
            self._send_json(
                405,
                {
                    "error": "method_not_allowed",
                    "use": "POST /api/v1/eval",
                    "executable": False,
                },
            )
            return
        if parsed.path == "/api/v1/topics":
            snapshot = self._get_view()
            self._send_json(
                200,
                {
                    "topics": snapshot.get("topics") or list_topics(self.con),
                    "count": snapshot.get("topics_count") or 0,
                    "claim_level": "LEARNED_FROM_MODEL",
                    "teacher": snapshot.get("teacher") or teacher_status(),
                    "external_api": snapshot.get("external_api"),
                },
            )
            return
        if parsed.path == "/api/v1/teacher":
            snapshot = self._get_view()
            teacher = snapshot.get("teacher") or teacher_status()
            self._send_json(
                200,
                {
                    "deepseek": teacher.get("deepseek"),
                    "flash": teacher.get("flash"),
                    "ready": teacher.get("ready"),
                    "learn_env": teacher.get("learn_env"),
                    "host": teacher.get("host"),
                    "external_api": snapshot.get("external_api"),
                },
            )
            return
        if parsed.path == "/api/v1/attestation":
            if persist:
                snapshot = self._get_view()
                self._send_json(200, write_attestation(snapshot))
                return
            existing = read_attestation()
            self._send_json(200, existing or {"present": False})
            return
        self._send_json(404, {"error": "not_found"})

    def do_POST(self):
        parsed = urllib.parse.urlsplit(self.path)
        decision = self._authorize(parsed.path)
        if decision != "ok":
            self._reject_auth(decision)
            return
        if parsed.path == "/api/v1/eval":
            if self._bounded_length(allow_empty=True) is None:
                return
            snapshot = organism_snapshot(
                self.con,
                self.kernel,
                self.public_status_path,
            )
            report = run_transformation_eval(
                lambda text: self.asker.ask(text, snapshot).get("answer"),
                con=self.con,
            )
            report["executable"] = False
            report["wave0"] = True
            report["autonomy_state"] = "PROPOSE_ONLY"
            self._send_json(200, report)
            return
        if parsed.path != "/api/v1/ask":
            self._send_json(404, {"error": "not_found"})
            return
        content_length = self._bounded_length(allow_empty=False)
        if content_length is None:
            return
        try:
            request = json.loads(self.rfile.read(content_length))
        except (json.JSONDecodeError, UnicodeDecodeError):
            self._send_json(400, {"error": "invalid_json"})
            return
        text = request.get("text") if isinstance(request, dict) else None
        if not isinstance(text, str) or not text.strip():
            self._send_json(400, {"error": "text_must_be_nonempty_string"})
            return
        if len(text) > MAX_ASK_TEXT_CHARS:
            self._send_json(413, {"error": "text_too_long"})
            return

        status_snapshot = organism_snapshot(
            self.con,
            self.kernel,
            self.public_status_path,
        )
        result = self.asker.ask(text, status_snapshot)
        event = make_event(
            "ask",
            {
                "request_hash": result["request_hash"],
                "route": result["route"],
                "label": result["label"],
            },
            priority=40,
        )
        receipt = self.kernel.accept(event)
        if receipt["status"] == "committed":
            self.kernel.replay_pending(limit=20)
        result["source_event_id"] = event["event_id"]
        result["event_receipt"] = receipt
        result["executable"] = False
        self._send_json(200, result)


class OrganismHTTPServer(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = True


def create_server(
    con,
    kernel,
    host="127.0.0.1",
    port=8090,
    *,
    bind_and_activate=True,
    public_status_path=PUBLIC_STATUS_PATH,
):
    if host not in {"127.0.0.1", "::1", LAN_BIND_HOST}:
        raise ValueError("organism_server_must_bind_loopback_or_board_lan")
    Handler.con = con
    Handler.kernel = kernel
    Handler.asker = AskCascade(con)
    Handler.public_status_path = public_status_path
    return OrganismHTTPServer(
        (host, port),
        Handler,
        bind_and_activate=bind_and_activate,
    )


def start_server(httpd):
    t = threading.Thread(target=httpd.serve_forever, daemon=True)
    t.start()
    return t


def serve(
    con,
    kernel,
    host="127.0.0.1",
    port=8090,
    *,
    public_status_path=PUBLIC_STATUS_PATH,
):
    httpd = create_server(
        con,
        kernel,
        host,
        port,
        public_status_path=public_status_path,
    )
    start_server(httpd)
    return httpd


def heartbeat_loop(con, kernel, stop, interval=120):
    while not stop.is_set():
        m = effective_measurement(con)
        cortex_available = LocalCortex().available()
        alerts = list(m.get("alerts", []))
        measured_health = maybe_stable(con, m["health_state"], alerts, count=True)
        if not cortex_available:
            alerts.append("CORTEX_DOWN")
            if measured_health != "SAFE_HALT":
                measured_health = "DEGRADED"
        health_state = apply_health_state(
            con,
            measured_health,
            alerts,
            "heartbeat",
        )
        with STATE_LOCK:
            STATE["local_cortex"] = (
                "AVAILABLE" if cortex_available else "DEGRADED"
            )
            state = dict(STATE)
        body = beat(con, {
            "boot_id": BOOT_ID,
            "age_seconds": int(time.monotonic() - STARTED_MONOTONIC),
            "health_state": health_state,
            "last_event_sequence": kernel.metrics["last_seq"],
            "local_cortex": state["local_cortex"],
            "unknowns": [
                item["name"]
                for item in m["signals"]
                if item["state"] == "UNKNOWN"
            ],
        })
        body["first_stage_label"] = first_stage_label(con)
        body["alerts"] = alerts
        with STATE_LOCK:
            ask_lan = bool(STATE.get("ask_lan"))
        body = enrich_snapshot(con, body, m, ask_lan=ask_lan)
        life = life_tick(con, kernel, body, m, ask_lan=ask_lan)
        body = life["snapshot"]
        if life.get("utterance"):
            body["last_utterance"] = life["utterance"].get("text")
            body["last_utterance_kind"] = life["utterance"].get("kind")
        write_public_status(con, body)
        ev = make_event(
            "heartbeat",
            {"health": health_state, "alerts": alerts},
            priority=15,
        )
        kernel.accept(ev)
        kernel.replay_pending(limit=20)
        stop.wait(heartbeat_interval_s(con, interval))


def _write_pid_file(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(f"{os.getpid()}\n", encoding="utf-8")
    os.replace(temporary, path)


def _remove_own_pid_file(path: Path) -> None:
    try:
        recorded = int(path.read_text(encoding="utf-8").strip())
    except (OSError, ValueError):
        return
    if recorded == os.getpid():
        path.unlink(missing_ok=True)


def _acquire_runtime_lock(path: Path) -> int:
    inherited = os.environ.get("OCTOPUS_ORGANISM_LOCK_FD")
    if inherited is not None:
        fd = int(inherited)
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        return fd
    path.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(path, os.O_CREAT | os.O_RDWR, 0o600)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except Exception:
        os.close(fd)
        raise
    return fd


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--db",
        default="/opt/octopus/lab/lab-data/organism.db",
    )
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8090)
    parser.add_argument("--heartbeat-interval", type=float, default=120.0)
    parser.add_argument(
        "--pid-file",
        default="/opt/octopus/lab/receipts/organism.pid",
    )
    args = parser.parse_args()
    if args.host != "127.0.0.1" or args.port != 8090:
        parser.error("lab organism is fixed to 127.0.0.1:8090")

    runtime_lock_fd = _acquire_runtime_lock(
        Path("/opt/octopus/lab/receipts/organism.start.lock")
    )
    con, kernel = build(args.db)
    initial_chain = ensure_identity_genesis(con, BOOT_ID)
    if not initial_chain["valid"]:
        con.close()
        raise IdentityChainError(initial_chain["error"])
    seed_lessons(con)
    seed_futures(con)
    write_parent_decisions()
    kernel.replay_pending(limit=1000)

    try:
        httpd = create_server(
            con,
            kernel,
            args.host,
            args.port,
            bind_and_activate=False,
        )
        httpd.server_bind()
    except Exception:
        con.close()
        raise
    pid_file = Path(args.pid_file)
    try:
        append_identity_event(
            con,
            BOOT_ID,
            "process_started",
            {
                "pid": os.getpid(),
                "started_wall_ns": int(STARTED_WALL * 1_000_000_000),
                "db_path": str(Path(args.db).resolve()),
                "listen": "127.0.0.1:8090",
                "listen_state": "BOUND_NOT_ACCEPTING",
            },
        )
        httpd.server_activate()
        start_server(httpd)
    except Exception:
        httpd.server_close()
        con.close()
        raise
    lan_httpd = None
    try:
        lan_httpd = create_server(
            con,
            kernel,
            LAN_BIND_HOST,
            8090,
            public_status_path=PUBLIC_STATUS_PATH,
        )
        start_server(lan_httpd)
        with STATE_LOCK:
            STATE["ask_lan"] = True
        append_identity_event(
            con,
            BOOT_ID,
            "lan_listen_started",
            {"listen": f"{LAN_BIND_HOST}:8090"},
        )
    except Exception:
        lan_httpd = None
        with STATE_LOCK:
            STATE["ask_lan"] = False
    if meta_value(con, "heartbeat_interval_s") is None:
        set_meta(con, "heartbeat_interval_s", str(int(args.heartbeat_interval)))
    _write_pid_file(pid_file)

    stop = threading.Event()

    def request_stop(_signum, _frame):
        stop.set()

    signal.signal(signal.SIGTERM, request_stop)
    signal.signal(signal.SIGINT, request_stop)
    heartbeat = threading.Thread(
        target=heartbeat_loop,
        args=(con, kernel, stop, args.heartbeat_interval),
        daemon=True,
    )
    heartbeat.start()

    try:
        while not stop.wait(1.0):
            pass
    finally:
        try:
            append_identity_event(
                con,
                BOOT_ID,
                "process_stopping",
                {"pid": os.getpid(), "reason": "signal"},
            )
        except IdentityChainError:
            pass
        httpd.shutdown()
        httpd.server_close()
        if lan_httpd is not None:
            lan_httpd.shutdown()
            lan_httpd.server_close()
        heartbeat.join(timeout=5)
        _remove_own_pid_file(pid_file)
        con.close()
        os.close(runtime_lock_fd)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
