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
from ofn.organism.contracts.events import make_event
from ofn.organism.event_kernel.kernel import EventKernel
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

BOOT_ID = uuid.uuid4().hex
STARTED_WALL = time.time()
STARTED_MONOTONIC = time.monotonic()
STATE = {"health_state": "BOOTSTRAP", "local_cortex": "STARTING", "last_event_sequence": 0}
STATE_LOCK = threading.RLock()
MAX_REQUEST_BYTES = 16 * 1024
MAX_ASK_TEXT_CHARS = 4000


def build(db_path):
    con = connect(Path(db_path))
    k = EventKernel(con)

    def on_any(ev):
        remember(
            con,
            ev["event_id"],
            ev["event_type"],
            {"priority": ev["priority"]},
            salience=0.4,
            outcome="handled",
        )

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


def organism_snapshot(con, kernel):
    measured = measure()
    with STATE_LOCK:
        STATE["health_state"] = transition(
            STATE["health_state"],
            measured["health_state"],
        )
        cortex = LocalCortex()
        STATE["local_cortex"] = "AVAILABLE" if cortex.available() else "DEGRADED"
        state = dict(STATE)
    body = {
        "organism_id": ORGANISM_ID,
        "boot_id": BOOT_ID,
        "age_seconds": int(time.monotonic() - STARTED_MONOTONIC),
        "health_state": state["health_state"],
        "autonomy_state": "PROPOSE_ONLY",
        "last_event_sequence": kernel.metrics["last_seq"] if kernel else 0,
        "local_cortex": state["local_cortex"],
        "external_api": "DISABLED",
        "memory_status": "AVAILABLE",
        "unknowns": [
            item["name"]
            for item in measured["signals"]
            if item["state"] == "UNKNOWN"
        ],
        "current_experiment": "board-life-001",
        "model_failure_is_organism_failure": False,
    }
    body.update(identity_status(con))
    return body


class Handler(BaseHTTPRequestHandler):
    con = None
    kernel = None
    asker = None

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

    def do_GET(self):
        parsed = urllib.parse.urlsplit(self.path)
        if parsed.path == "/api/v1/organism":
            self._send_json(200, organism_snapshot(self.con, self.kernel))
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
        self._send_json(404, {"error": "not_found"})

    def do_POST(self):
        parsed = urllib.parse.urlsplit(self.path)
        if parsed.path != "/api/v1/ask":
            self._send_json(404, {"error": "not_found"})
            return
        try:
            content_length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            self._send_json(400, {"error": "invalid_content_length"})
            return
        if content_length < 1 or content_length > MAX_REQUEST_BYTES:
            self._send_json(413, {"error": "request_size_out_of_range"})
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

        status_snapshot = organism_snapshot(self.con, self.kernel)
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
):
    if host not in {"127.0.0.1", "::1"}:
        raise ValueError("organism_server_must_bind_loopback")
    Handler.con = con
    Handler.kernel = kernel
    Handler.asker = AskCascade(con)
    return OrganismHTTPServer(
        (host, port),
        Handler,
        bind_and_activate=bind_and_activate,
    )


def start_server(httpd):
    t = threading.Thread(target=httpd.serve_forever, daemon=True)
    t.start()
    return t


def serve(con, kernel, host="127.0.0.1", port=8090):
    httpd = create_server(con, kernel, host, port)
    start_server(httpd)
    return httpd


def heartbeat_loop(con, kernel, stop, interval=120):
    while not stop.is_set():
        m = measure()
        with STATE_LOCK:
            STATE["health_state"] = transition(
                STATE["health_state"],
                m["health_state"],
            )
            STATE["local_cortex"] = (
                "AVAILABLE" if LocalCortex().available() else "DEGRADED"
            )
            state = dict(STATE)
        beat(con, {
            "boot_id": BOOT_ID,
            "age_seconds": int(time.monotonic() - STARTED_MONOTONIC),
            "health_state": state["health_state"],
            "last_event_sequence": kernel.metrics["last_seq"],
            "local_cortex": state["local_cortex"],
            "unknowns": [
                item["name"]
                for item in m["signals"]
                if item["state"] == "UNKNOWN"
            ],
        })
        ev = make_event("heartbeat", {"health": state["health_state"]}, priority=15)
        kernel.accept(ev)
        kernel.replay_pending(limit=20)
        stop.wait(interval)


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
        heartbeat.join(timeout=5)
        _remove_own_pid_file(pid_file)
        con.close()
        os.close(runtime_lock_fd)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
