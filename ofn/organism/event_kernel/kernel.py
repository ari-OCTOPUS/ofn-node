
import json, queue, threading, time
from ofn.organism.contracts.events import validate_event, EVENT_QUEUE_MAXSIZE

class EventKernel:
    def __init__(self, con, maxsize=EVENT_QUEUE_MAXSIZE):
        self.con = con
        self.q = queue.PriorityQueue(maxsize=maxsize)
        self.maxsize = maxsize
        self.lock = threading.Lock()
        self.handlers = {}
        self.metrics = {
            "committed_event_loss": 0,
            "duplicate_external_effect": 0,
            "unknown_schema_silent_accept": 0,
            "rejected": 0,
            "saturated": 0,
            "last_seq": 0,
        }
        self._stop = False

    def register(self, event_type, fn):
        self.handlers[event_type] = fn

    def _next_seq(self):
        row = self.con.execute("SELECT COALESCE(MAX(node_seq),0) FROM events").fetchone()
        return int(row[0]) + 1

    def commit_event(self, ev: dict) -> dict:
        ev = validate_event(ev)
        with self.lock:
            existing = self.con.execute("SELECT event_id, hash FROM events WHERE event_id=? OR hash=?", (ev["event_id"], ev["hash"])).fetchone()
            if existing:
                if existing[1] == ev["hash"] and existing[0] == ev["event_id"]:
                    return {"status": "duplicate", "event_id": ev["event_id"], "hash": ev["hash"]}
                if existing[0] == ev["event_id"] and existing[1] != ev["hash"]:
                    raise ValueError("node_sequence_conflict")
                if existing[1] == ev["hash"] and existing[0] != ev["event_id"]:
                    return {"status": "duplicate_hash", "event_id": existing[0], "hash": ev["hash"]}
            seq = self._next_seq()
            self.con.execute("BEGIN IMMEDIATE")
            try:
                self.con.execute(
                    "INSERT INTO events(event_id,event_type,priority,payload_json,created_at,schema_version,hash,node_seq) VALUES (?,?,?,?,?,?,?,?)",
                    (ev["event_id"], ev["event_type"], ev["priority"], json.dumps(ev["payload"], sort_keys=True), ev["created_at"], ev["schema_version"], ev["hash"], seq),
                )
                self.con.execute(
                    "INSERT INTO outbox(event_id,hash,status,created_at) VALUES (?,?,?,?)",
                    (ev["event_id"], ev["hash"], "pending", time.time()),
                )
                self.con.execute("COMMIT")
            except Exception:
                self.con.execute("ROLLBACK")
                raise
            self.metrics["last_seq"] = seq
        try:
            self.q.put_nowait((ev["priority"], time.time(), ev["event_id"], ev["hash"]))
        except queue.Full:
            self.metrics["saturated"] += 1
            # committed already; dispatch recovers via replay_pending
        return {"status": "committed", "event_id": ev["event_id"], "hash": ev["hash"], "seq": seq}

    def accept(self, ev: dict) -> dict:
        try:
            return self.commit_event(ev)
        except ValueError as e:
            msg = str(e)
            self.metrics["rejected"] += 1
            if msg.startswith("unknown_schema"):
                pass
            return {"status": "rejected", "error": msg}

    def drain_outbox_once(self):
        row = self.con.execute("SELECT delivery_id, event_id, hash FROM outbox WHERE status='pending' ORDER BY delivery_id LIMIT 1").fetchone()
        if not row:
            return None
        delivery_id, event_id, h = row
        evrow = self.con.execute("SELECT event_type, payload_json, priority FROM events WHERE event_id=?", (event_id,)).fetchone()
        if not evrow:
            return {"status": "missing_event", "event_id": event_id}
        et, payload, pr = evrow
        handler = self.handlers.get(et) or self.handlers.get("*")
        if handler:
            handler({"event_id": event_id, "event_type": et, "payload": json.loads(payload), "priority": pr, "hash": h})
        self.con.execute("UPDATE outbox SET status='done', done_at=? WHERE delivery_id=?", (time.time(), delivery_id))
        return {"status": "done", "event_id": event_id}

    def replay_pending(self, limit=1000):
        n = 0
        for _ in range(limit):
            r = self.drain_outbox_once()
            if not r:
                break
            n += 1
        return n
