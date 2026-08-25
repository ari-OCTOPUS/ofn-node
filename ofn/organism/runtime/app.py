
import json, os, threading, time, uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from ofn.organism.persistence.db import connect
from ofn.organism.event_kernel.kernel import EventKernel
from ofn.organism.contracts.events import make_event
from ofn.organism.homeostasis.core import measure, transition
from ofn.organism.identity.heartbeat import beat
from ofn.organism.memory.episodic import remember
from ofn.organism.cognition.backend import PolicyGate, LocalCortex

BOOT_ID = uuid.uuid4().hex
STARTED = time.time()
STATE = {"health_state": "BOOTSTRAP", "local_cortex": "STARTING", "last_event_sequence": 0}

def build(db_path):
    con = connect(Path(db_path))
    k = EventKernel(con)
    def on_any(ev):
        remember(con, ev["event_id"], ev["event_type"], {"priority": ev["priority"]}, salience=0.4, outcome="handled")
    k.register("*", on_any)
    return con, k

class Handler(BaseHTTPRequestHandler):
    con = None
    kernel = None
    def log_message(self, *args):
        return
    def do_GET(self):
        if self.path != "/api/v1/organism":
            self.send_response(404); self.end_headers(); return
        m = measure()
        STATE["health_state"] = transition(STATE["health_state"], m["health_state"])
        cortex = LocalCortex()
        STATE["local_cortex"] = "AVAILABLE" if cortex.available() else "DEGRADED"
        body = {
            "organism_id": "board-life-001",
            "boot_id": BOOT_ID,
            "age_seconds": int(time.time() - STARTED),
            "health_state": STATE["health_state"],
            "autonomy_state": "PROPOSE_ONLY",
            "last_event_sequence": self.kernel.metrics["last_seq"] if self.kernel else 0,
            "identity_chain_valid": True,
            "local_cortex": STATE["local_cortex"],
            "external_api": "DISABLED",
            "memory_status": "AVAILABLE",
            "unknowns": [s["name"] for s in m["signals"] if s["state"]=="UNKNOWN"],
            "current_experiment": "board-life-001",
            "model_failure_is_organism_failure": False,
        }
        raw = json.dumps(body).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

def serve(con, kernel, host="127.0.0.1", port=8090):
    Handler.con = con; Handler.kernel = kernel
    httpd = ThreadingHTTPServer((host, port), Handler)
    t = threading.Thread(target=httpd.serve_forever, daemon=True)
    t.start()
    return httpd

def heartbeat_loop(con, kernel, stop, interval=120):
    while not stop.is_set():
        m = measure()
        STATE["health_state"] = transition(STATE["health_state"], m["health_state"])
        beat(con, {
            "boot_id": BOOT_ID,
            "age_seconds": int(time.time()-STARTED),
            "health_state": STATE["health_state"],
            "last_event_sequence": kernel.metrics["last_seq"],
            "local_cortex": STATE["local_cortex"],
            "unknowns": [s["name"] for s in m["signals"] if s["state"]=="UNKNOWN"],
        })
        ev = make_event("heartbeat", {"health": STATE["health_state"]}, priority=15)
        kernel.accept(ev)
        kernel.replay_pending(limit=20)
        stop.wait(interval)
