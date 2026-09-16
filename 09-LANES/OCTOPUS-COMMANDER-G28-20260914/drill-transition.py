"""Joint transition drill (owner mission section ب, 2026-09-14).

Real bytes of BOTH components against one shared, fcntl-locked stateful
server: new producer (8da9471c via g27runner), OLD live binder (00dd4ef3) and
the W24 candidate binder (b9c504f8) via g27binder. Invocations are sequential
subprocesses (deterministic barriers); the only deliberate overlap is S7,
controlled by a 5s in-process hold (parent proceeds at 1.5s).

Per scenario we record: receiver, requested offsets (tagged), server-confirmed
ids, durable rows per spool, decisions consumed, effect (ACK) count.
"""
import json
import pathlib
import subprocess
import sys
import tempfile
import time

sys.path.insert(0, "/tmp")
sys.path.insert(0, "/home/ari/ofn")
sys.path.insert(0, "/home/ari/ofn/ofn")
sys.path.insert(0, "/home/ari/ofn/ofn/agents")
sys.path.insert(0, "/home/ari/ofn/ofn/budget")
import g27server  # noqa: E402

GLASS_ART = ("/home/ari/ofn/state/coding-worker/stage/W24-G8G27-PRODUCER/"
             "glass_runner.py")
OWNER = 6150431610
REG_X = "a03b2ecc" + "9" * 56
REG_Y = "c" * 64
REG_Z = "d" * 64
PASS, FAIL = [], []


def check(name, ok, detail=""):
    print("  %-5s %-58s %s" % ("PASS" if ok else "FAIL", name, detail))
    (PASS if ok else FAIL).append(name)


def b3txt(h):
    return "Confirming " + h


def mkfx(cards):
    """cards: list of (name, payload) tuples."""
    fx = pathlib.Path(tempfile.mkdtemp(prefix="drill-"))
    for d in ("lanes/b3", "lanes/money", "pulse"):
        (fx / d).mkdir(parents=True, exist_ok=True)
    od = fx / "owner_dialogue"
    od.mkdir(parents=True, exist_ok=True)
    (od / "go_b3_pending_registry.json").write_text(json.dumps(
        {"requests": [{"id": n, "card": n, "payload_sha256": p, "status": "pending"}
                      for n, p in cards]}), encoding="utf-8")
    srv = str(fx / "server.json")
    g27server.new(srv)
    return fx, srv


def glass(fx, srv, mode="normal"):
    r = subprocess.run([sys.executable, "/tmp/g27runner.py", GLASS_ART,
                        str(fx), srv, mode], capture_output=True, text=True,
                       timeout=60)
    return r.returncode, _lastjson(r.stdout)


def binder(which, fx, srv, mode="poll"):
    r = subprocess.run([sys.executable, "/tmp/g27binder.py", which, str(fx),
                        srv, mode], capture_output=True, text=True, timeout=90)
    return r.returncode, _lastjson(r.stdout)


def _lastjson(s):
    out = {}
    for line in (s or "").splitlines():
        try:
            out = json.loads(line)
        except ValueError:
            pass
    return out


def rows(p):
    q = pathlib.Path(p)
    if not q.exists():
        return []
    return [json.loads(l) for l in q.read_text(encoding="utf-8").splitlines()
            if l.strip()]


def snap(fx, srv):
    od = fx / "owner_dialogue"
    dec = rows(od / "owner_decision.v1.jsonl")
    return {"inbox": [r.get("update_id") for r in rows(fx / "lanes/b3/go_b3_inbox.jsonl")],
            # the candidate binder also mirrors consumed rows into tg_spool
            # (update_id absent -> None); count only real old-binder receives
            "tg": [r.get("update_id") for r in rows(od / "go_b3_tg_spool.jsonl")
                   if r.get("update_id") is not None],
            "acks": [d for d in dec if str(d.get("verdict", "")).startswith("ACK")],
            "rejects": [d for d in dec if str(d.get("verdict", "")).startswith("REJECT")],
            "decisions": [(d.get("verdict"), d.get("reason", ""),
                           str(d.get("bound_request_payload_sha256"))[:8]) for d in dec],
            "server": g27server.state(srv),
            "consumed": [r["id"] for r in json.loads(
                (od / "go_b3_pending_registry.json").read_text(encoding="utf-8"))["requests"]
                if r.get("status") == "consumed"]}


def main():
    # S1: glass receives the new message FIRST (state B standby is live)
    fx, srv = mkfx([("CARD-X", REG_X)])
    g27server.enqueue(srv, 1001, OWNER, b3txt(REG_X))
    rc, out = glass(fx, srv)
    rc, out = glass(fx, srv)  # second poll confirms server-side
    rc, bout = binder("old", fx, srv)
    s = snap(fx, srv)
    check("S1 glass-first: durable in inbox, binder sees nothing after confirm",
          s["inbox"] == [1001] and s["tg"] == [] and s["acks"] == []
          and s["server"]["server_confirmed"] == [1001]
          and [t for _, t in s["server"]["getupdates_calls"]] ==
          ["glass", "glass", "binder-old"],
          "inbox=%s tg=%s confirmed=%s" % (s["inbox"], s["tg"],
                                           s["server"]["server_confirmed"]))

    # S2: OLD binder receives first (state A behavior preserved)
    fx, srv = mkfx([("CARD-X", REG_X)])
    g27server.enqueue(srv, 2001, OWNER, b3txt(REG_X))
    rc, bout = binder("old", fx, srv)
    rc, bout = binder("old", fx, srv)  # its next offset confirms
    rc, gout = glass(fx, srv)
    s = snap(fx, srv)
    check("S2 binder-first: binds once, glass gets nothing, no inbox row",
          len(s["acks"]) == 1 and s["inbox"] == [] and len(s["tg"]) == 1
          and s["server"]["server_confirmed"] == [2001]
          and s["acks"][0]["bound_request_payload_sha256"] == REG_X
          and s["consumed"] == ["CARD-X"],
          "acks=%d tg=%s consumed=%s" % (len(s["acks"]), s["tg"], s["consumed"]))

    # S3: BOTH receive the same update -> W24-era consumer must NOT double-bind
    fx, srv = mkfx([("CARD-X", REG_X)])
    g27server.enqueue(srv, 3001, OWNER, b3txt(REG_X))
    rc, out = glass(fx, srv)            # glass spools, does not confirm yet
    rc, bout = binder("old", fx, srv)   # binder receives the same update + binds
    rc, bout = binder("old", fx, srv)   # binder confirms server-side
    rc, nout = binder("new", fx, srv, "consume")  # W24 world consumes inbox row
    s = snap(fx, srv)
    check("S3 overlap: exactly ONE bind; W24 consumer never re-binds the replay",
          len(s["acks"]) == 1 and s["inbox"] == [3001] and s["tg"] == [3001]
          and (nout.get("skipped_replay") == 1 or len(s["rejects"]) >= 1),
          "acks=%d skip=%s rejects=%d" % (len(s["acks"]),
                                          nout.get("skipped_replay"),
                                          len(s["rejects"])))

    # S4: old binder dies AFTER receiving, BEFORE persistence
    fx, srv = mkfx([("CARD-X", REG_X)])
    g27server.enqueue(srv, 4001, OWNER, b3txt(REG_X))
    rc, bout = binder("old", fx, srv, "crash_before_spool")
    s = snap(fx, srv)
    check("S4 crash pre-persistence: no row, no bind, no confirm",
          rc == 9 and s["tg"] == [] and s["acks"] == []
          and s["server"]["server_confirmed"] == []
          and 4001 in [u["update_id"] for u in s["server"]["queue"]],
          "rc=%d tg=%s queue-has-4001=%s"
          % (rc, s["tg"], 4001 in [u["update_id"] for u in s["server"]["queue"]]))

    # S5: standby takes over in the gap (glass advances, then W24 binds once)
    rc, out = glass(fx, srv)
    rc, out = glass(fx, srv)  # confirms 4001
    rc, nout = binder("new", fx, srv, "consume")
    s = snap(fx, srv)
    check("S5 standby takeover: message durable via glass, bound exactly once",
          s["inbox"] == [4001] and 4001 in s["server"]["server_confirmed"]
          and len(s["acks"]) == 1 and s["acks"][0]["bound_request_payload_sha256"] == REG_X,
          "inbox=%s confirmed=%s acks=%d" % (s["inbox"],
                                             s["server"]["server_confirmed"],
                                             len(s["acks"])))

    # S6: long state B soak - alternating first-receivers, exactly-once each
    reg = json.loads((fx / "owner_dialogue/go_b3_pending_registry.json")
                     .read_text(encoding="utf-8"))
    reg["requests"].append({"id": "CARD-Y", "card": "CARD-Y",
                            "payload_sha256": REG_Y, "status": "pending"})
    reg["requests"].append({"id": "CARD-Z", "card": "CARD-Z",
                            "payload_sha256": REG_Z, "status": "pending"})
    (fx / "owner_dialogue/go_b3_pending_registry.json").write_text(
        json.dumps(reg), encoding="utf-8")
    g27server.enqueue(srv, 5001, OWNER, b3txt(REG_Y))
    rc, bout = binder("old", fx, srv)
    rc, bout = binder("old", fx, srv)
    g27server.enqueue(srv, 5002, OWNER, b3txt(REG_Z))
    rc, out = glass(fx, srv)
    rc, out = glass(fx, srv)
    rc, bout = binder("old", fx, srv)          # must see nothing new
    rc, nout = binder("new", fx, srv, "consume")  # binds 5002 from inbox
    s = snap(fx, srv)
    check("S6 soak: every message exactly-once durable + at most one bind",
          s["inbox"] == [4001, 5002] and 5001 in s["tg"]
          and len([a for a in s["acks"]]) == 3
          and s["server"]["server_confirmed"].count(5001) == 1
          and s["server"]["server_confirmed"].count(5002) == 1,
          "inbox=%s tg=%s acks=%d decisions=%s"
          % (s["inbox"], s["tg"], len(s["acks"]), s["decisions"]))

    # S7: old binder process still alive at cutover (5s hold, barrier at 1.5s)
    fx, srv = mkfx([("CARD-X", REG_X)])
    g27server.enqueue(srv, 7001, OWNER, b3txt(REG_X))
    p = subprocess.Popen([sys.executable, "/tmp/g27binder.py", "old", str(fx),
                          srv, "slow_poll"], stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE, text=True)
    time.sleep(1.5)  # old binder is provably inside its pre-write hold
    rc, out = glass(fx, srv)                       # glass also durably spools
    rc, nout = binder("new", fx, srv, "consume")   # post-deploy binder binds FIRST
    p.wait(timeout=60)                              # old binder wakes, writes, parses
    s = snap(fx, srv)
    check("S7 overlap at cutover: one bind total, laggard rejects, both durable",
          len(s["acks"]) == 1 and len(s["rejects"]) >= 1
          and s["inbox"] == [7001] and s["tg"] == [7001],
          "acks=%d inbox=%s tg=%s rejects=%d"
          % (len(s["acks"]), s["inbox"], s["tg"], len(s["rejects"])))

    # S8: restarts never resurrect the retired poller (candidate never polls)
    fx, srv = mkfx([("CARD-X", REG_X)])
    g27server.enqueue(srv, 8001, OWNER, b3txt(REG_X))
    for _ in range(3):
        rc, nout = binder("new", fx, srv, "consume")
    rc, out = glass(fx, srv)
    rc, out = glass(fx, srv)
    for _ in range(2):
        rc, nout = binder("new", fx, srv, "consume")
    s = snap(fx, srv)
    tags = [t for _, t in s["server"]["getupdates_calls"]]
    check("S8 post-cutover: only glass polls; candidate binder never getUpdates",
          set(tags) == {"glass"} and len(s["acks"]) == 1,
          "tags=%s acks=%d" % (sorted(set(tags)), len(s["acks"])))

    print()
    print("TRANSITION_DRILL:", "PASS" if not FAIL else "FAIL -> " + ", ".join(FAIL))
    return 0 if not FAIL else 1


if __name__ == "__main__":
    sys.exit(main())
