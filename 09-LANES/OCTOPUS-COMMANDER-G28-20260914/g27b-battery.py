"""G27b battery: stateful-transport durability drills T1-T10 on the v2 producer
artifact, plus the routing matrix on the FINAL bytes, plus the v1-vs-v2
fsync->dedupe counterexample comparison.

Boundaries named per mission:
  received -> durably persisted -> local checkpoint -> remote confirmation.
- "durably persisted" = row appended + flushed + fsynced (or re-fsynced on
  dedupe). Page-cache visibility alone is NOT durability.
- "local checkpoint" = cursor file written via temp+fsync+replace (+dir fsync
  best-effort, disposition recorded).
- "remote confirmation" = the server drops the id; happens only when a LATER
  getUpdates(offset) passes it. The server fake logs this; the tripwire fails
  the battery if any id is remotely confirmed without a durable row (or a
  deterministic stranger disposition).
"""
import hashlib
import importlib.util
import json
import pathlib
import subprocess
import sys
import tempfile

RUNNER = "/tmp/g27runner.py"
ART = "/home/ari/ofn/state/coding-worker/stage/W24-G8G27-PRODUCER/glass_runner.py"
PRE_V1 = "/home/ari/ofn/state/coding-worker/stage/W24-G8G27-PRODUCER/glass_runner.py.pre-g27v2"
PROD_GUARD = ["/home/ari/ofn/state/pulse/glass-offset.txt",
              "/home/ari/ofn/state/revenue-drive/tg-inbox.jsonl",
              "/home/ari/ofn/state/owner_dialogue/go_b3_inbox.jsonl"]
REG_HASH = "a03b2ecc" + "9" * 56
OWNER = 6150431610
B3TXT = "Confirming " + REG_HASH + " now"
MONTXT = "hello there, plain owner text"

sys.path.insert(0, "/tmp")
import g27server  # noqa: E402

PASS, FAIL = [], []


def check(name, ok, detail=""):
    print("  %-5s %-56s %s" % ("PASS" if ok else "FAIL", name, detail))
    (PASS if ok else FAIL).append(name)


def guard():
    out = []
    for p in PROD_GUARD:
        q = pathlib.Path(p)
        out.append(hashlib.sha256(q.read_bytes()).hexdigest() if q.exists() else None)
    return out


def mkfx():
    fx = pathlib.Path(tempfile.mkdtemp(prefix="g27b-"))
    for d in ("lanes/b3", "lanes/money", "pulse"):
        (fx / d).mkdir(parents=True, exist_ok=True)
    (fx / "registry.json").write_text(json.dumps(
        {"requests": [{"id": "CARD-X", "payload_sha256": REG_HASH}]}),
        encoding="utf-8")
    srv = str(fx / "server.json")
    g27server.new(srv)
    return fx, srv


def run(fx, srv, mode, artifact=ART, extra=None):
    r = subprocess.run([sys.executable, RUNNER, str(artifact if isinstance(
        artifact, str) else artifact), str(fx), srv, mode] + (extra or []),
        capture_output=True, text=True, timeout=60)
    out = {}
    for line in (r.stdout or "").splitlines():
        try:
            out = json.loads(line)
        except ValueError:
            pass
    return r.returncode, out, (r.stderr or "")


def rows(p):
    q = pathlib.Path(p)
    if not q.exists():
        return []
    out = []
    for line in q.read_text(encoding="utf-8").splitlines():
        if line.strip():
            try:
                out.append(json.loads(line))
            except ValueError:
                out.append({"__torn__": line})
    return out


def lane_ids(fx):
    ids = set()
    for lane in ("b3/go_b3_inbox.jsonl", "money/tg-inbox.jsonl"):
        for r in rows(fx / "lanes" / lane):
            if isinstance(r.get("update_id"), int):
                ids.add(r["update_id"])
    return ids


def cursor(fx):
    f = fx / "pulse" / "glass-offset.txt"
    return int(f.read_text().strip()) if f.exists() else 0


def events(fx, kind):
    f = fx / "opslib-events.jsonl"
    if not f.exists():
        return []
    return [json.loads(l) for l in f.read_text(encoding="utf-8").splitlines()
            if l.strip() and json.loads(l).get("event_type") == kind]


def tripwire(fx, srv, strangers=()):
    s = g27server._load(srv)
    have = lane_ids(fx)
    bad = [u for u in s["server_confirmed"] if u not in have and u not in strangers]
    return not bad, bad


def readonly(d, on=True):
    pathlib.Path(d).chmod(0o555 if on else 0o755)


def main():
    g0 = guard()
    print("artifact v2 sha256:", hashlib.sha256(
        pathlib.Path(ART).read_bytes()).hexdigest()[:16])

    # ---------------- T1: failure BEFORE the spool file is created
    fx, srv = mkfx()
    g27server.enqueue(srv, 101, OWNER, MONTXT)
    readonly(fx / "lanes/money")
    rc, out, _ = run(fx, srv, "normal")
    ok1 = (out.get("stop_reason") == "spool_write_failed"
           and cursor(fx) == 0 and rows(fx / "lanes/money/tg-inbox.jsonl") == []
           and g27server._load(srv)["server_confirmed"] == [])
    readonly(fx / "lanes/money", False)
    rc, out, _ = run(fx, srv, "normal")
    rc, out, _ = run(fx, srv, "normal")  # third poll confirms server-side
    s = g27server._load(srv)
    ok2 = (len(rows(fx / "lanes/money/tg-inbox.jsonl")) == 1
           and cursor(fx) == 101 and 101 in s["server_confirmed"]
           and s["requested_offsets"] == [1, 1, 102])
    tw, bad = tripwire(fx, srv)
    check("T1 pre-creation failure: no confirm, then exactly-once recovery",
          ok1 and ok2 and tw, "ok1=%s ok2=%s tripwire=%s" % (ok1, ok2, bad))

    # ---------------- T2: torn final line - repair, never blind-append
    fx, srv = mkfx()
    money = fx / "lanes/money/tg-inbox.jsonl"
    money.write_bytes(b'{"update_id":211,"chat":"6150431610","text":"a","lane":"MONEY"}\n'
                      b'{"update_id":212,"chat":"6150431610","te')
    g27server.enqueue(srv, 212, OWNER, MONTXT)
    rc, out, _ = run(fx, srv, "normal")
    rr = rows(money)
    ok = (len(rr) == 2 and all("__torn__" not in r for r in rr)
          and rr[-1].get("update_id") == 212 and rr[0].get("update_id") == 211
          and bool(events(fx, "glass.spool_torn_tail_repaired"))
          and cursor(fx) == 212)
    tw, bad = tripwire(fx, srv)
    check("T2 torn tail truncated+repaired, row written after newline", ok and tw,
          "rows=%d cursor=%d" % (len(rr), cursor(fx)))
    # T2b: file with ONLY a torn fragment
    fx, srv = mkfx()
    money = fx / "lanes/money/tg-inbox.jsonl"
    money.write_bytes(b'{"update_id":5,"chat":"6150431610","te')
    g27server.enqueue(srv, 5, OWNER, MONTXT)
    rc, out, _ = run(fx, srv, "normal")
    rr = rows(money)
    ok = (len(rr) == 1 and rr[0].get("update_id") == 5
          and "__torn__" not in rr[0] and cursor(fx) == 5)
    check("T2b torn-only file repaired from zero", ok,
          "rows=%d cursor=%d" % (len(rr), cursor(fx)))

    # ---------------- T3/T4: crash between write and fsync -> dedupe must
    # re-fsync before trusting the row (v1 counterexample, v2 fixed)
    verdicts = {}
    for tag, art in (("v1", PRE_V1), ("v2", ART)):
        fx, srv = mkfx()
        flog = fx / "fsync.log"
        g27server.enqueue(srv, 301, OWNER, B3TXT)
        rc, out, _ = run(fx, srv, "crash_after_write_before_fsync", artifact=art)
        crashed_ok = (rc == 9 and cursor(fx) == 0
                      and len(rows(fx / "lanes/b3/go_b3_inbox.jsonl")) == 1
                      and g27server._load(srv)["server_confirmed"] == [])
        rc, out, _ = run(fx, srv, "count_fsync", artifact=art, extra=[str(flog)])
        logged = flog.read_text().splitlines() if flog.exists() else []
        lane_refsync = any("/lanes/b3/" in p for p in logged)
        verdicts[tag] = (crashed_ok, lane_refsync,
                         len(rows(fx / "lanes/b3/go_b3_inbox.jsonl")) == 1,
                         out.get("replayed") == 1, cursor(fx) == 301)
    c1, l1 = verdicts["v1"][0], verdicts["v1"][1]
    c2, l2, r2, p2, cur2 = verdicts["v2"]
    check("T3 crash(write,no-fsync): row visible, cursor 0, no server confirm",
          c1 and c2, "v1=%s v2=%s" % (c1, c2))
    check("T4 COUNTEREXAMPLE v1: recovery trusts unproven-durable row (no re-fsync)",
          c1 and (not l1), "v1_lane_refsync=%s" % l1)
    check("T4 v2 FIX: recovery re-fsyncs the lane before dedupe-success",
          c2 and l2 and r2 and p2 and cur2,
          "lane_refsync=%s rows=1 replayed cursor=%d" % (l2, cur2))

    # ---------------- T5: REAL process cut after persistence, before checkpoint
    fx, srv = mkfx()
    g27server.enqueue(srv, 401, OWNER, B3TXT)
    rc, out, _ = run(fx, srv, "crash_before_checkpoint")
    ok = (rc == 9 and len(rows(fx / "lanes/b3/go_b3_inbox.jsonl")) == 1
          and cursor(fx) == 0 and g27server._load(srv)["server_confirmed"] == [])
    rc, out, _ = run(fx, srv, "normal")
    rc, out, _ = run(fx, srv, "normal")
    ok2 = (len(rows(fx / "lanes/b3/go_b3_inbox.jsonl")) == 1
           and cursor(fx) == 401 and out.get("replayed") in (0, 1)
           and 401 in g27server._load(srv)["server_confirmed"])
    tw, bad = tripwire(fx, srv)
    check("T5 real process cut -> restart replay exactly-once", ok and ok2 and tw,
          "cut=%s recover=%s" % (ok, ok2))

    # ---------------- T6: checkpoint failure + replay from stateful transport
    fx, srv = mkfx()
    g27server.enqueue(srv, 501, OWNER, MONTXT)
    readonly(fx / "pulse")
    rc, out, _ = run(fx, srv, "normal")
    ok = (out.get("stop_reason") == "checkpoint_failed"
          and len(rows(fx / "lanes/money/tg-inbox.jsonl")) == 1 and cursor(fx) == 0)
    readonly(fx / "pulse", False)
    rc, out, _ = run(fx, srv, "normal")
    rc, out, _ = run(fx, srv, "normal")
    ok2 = (len(rows(fx / "lanes/money/tg-inbox.jsonl")) == 1 and cursor(fx) == 501
           and 501 in g27server._load(srv)["server_confirmed"])
    tw, bad = tripwire(fx, srv)
    check("T6 checkpoint failure disposition + exactly-once replay", ok and ok2 and tw,
          "fail=%s recover=%s" % (ok, ok2))

    # ---------------- T7: msg1 ok, msg2 fails, msg3 exists -> prefix boundary
    fx, srv = mkfx()
    for uid, txt in ((601, MONTXT), (602, B3TXT), (603, "second plain text")):
        g27server.enqueue(srv, uid, OWNER, txt)
    readonly(fx / "lanes/b3")
    rc, out, _ = run(fx, srv, "normal")
    ok = (cursor(fx) == 601 and rows(fx / "lanes/b3/go_b3_inbox.jsonl") == []
          and len(rows(fx / "lanes/money/tg-inbox.jsonl")) == 1
          and out.get("stop_reason") == "spool_write_failed"
          and out.get("failed_update_id") == 602)
    s = g27server._load(srv)
    # after the failing run nothing is server-confirmed; the delivered-but-
    # unconfirmed 601 is still in the re-delivery queue (drop happens only on
    # the NEXT getUpdates past it)
    ok_srv = (s["server_confirmed"] == []
              and 601 in [u["update_id"] for u in s["queue"]])
    readonly(fx / "lanes/b3", False)
    rc, out, _ = run(fx, srv, "normal")
    rc, out, _ = run(fx, srv, "normal")
    ok2 = (cursor(fx) == 603 and len(rows(fx / "lanes/b3/go_b3_inbox.jsonl")) == 1
           and len(rows(fx / "lanes/money/tg-inbox.jsonl")) == 2
           and 603 in g27server._load(srv)["server_confirmed"])
    tw, bad = tripwire(fx, srv)
    check("T7 offset never passes the failure; tail recovered next cycle",
          ok and ok_srv and ok2 and tw,
          "cut=%s server=%s recover=%s" % (ok, ok_srv, ok2))

    # ---------------- T8: directory-fsync failure is a recorded disposition
    fx, srv = mkfx()
    g27server.enqueue(srv, 701, OWNER, B3TXT)
    rc, out, _ = run(fx, srv, "dirfsync_fail")
    ok = (out.get("cursor_dirfsync_failed") and cursor(fx) == 701
          and len(rows(fx / "lanes/b3/go_b3_inbox.jsonl")) == 1
          and out.get("stop_reason") is None)
    tw, bad = tripwire(fx, srv)
    check("T8 dir-fsync failure recorded; cursor+row still written", ok and tw,
          "dirfsync=%s cursor=%d" % (out.get("cursor_dirfsync_failed"), cursor(fx)))
    print("       [boundary] crash guarantee = file fsync (done) + rename; the"
          " dir fsync covers rename durability after POWER LOSS only - a lost"
          " rename replays and is absorbed by update_id dedupe")

    # ---------------- T9: replay after registry change - no re-lane, no dup
    fx, srv = mkfx()
    g27server.enqueue(srv, 801, OWNER, B3TXT)
    rc, out, _ = run(fx, srv, "normal")
    ok1 = (len(rows(fx / "lanes/b3/go_b3_inbox.jsonl")) == 1
           and rows(fx / "lanes/b3/go_b3_inbox.jsonl")[0]["route_reason"]
           == "resolves_to_registered_b3_card")
    (fx / "registry.json").write_text(json.dumps({"requests": []}), encoding="utf-8")
    (fx / "pulse/glass-offset.txt").write_text("800", encoding="utf-8")  # reverted ckpt
    # reset the server queue to hold exactly ONE re-delivery of 801 (Telegram
    # never returns the same still-queued id twice in one response)
    st = g27server._load(srv)
    st["queue"] = [u for u in st["queue"] if u["update_id"] == 801][:1]
    g27server._save(srv, st)
    rc, out, _ = run(fx, srv, "normal")
    rr = rows(fx / "lanes/b3/go_b3_inbox.jsonl")
    ok2 = (len(rr) == 1 and out.get("replayed") == 1
           and rows(fx / "lanes/money/tg-inbox.jsonl") == [] and cursor(fx) == 801)
    tw, bad = tripwire(fx, srv)
    check("T9 registry change + replay: same lane, no duplicate, no re-effect",
          ok1 and ok2 and tw, "routed=%s replay=%s" % (ok1, ok2))
    print("       [scope] routing rules cannot flip a hex-bearing text to MONEY;"
          " the cross-lane dedupe scan is defense-in-depth for future routing"
          " changes; the reachable invariant (no dup / no re-lane) is asserted")

    # ---------------- T10: transport error / malformed response
    oks = []
    for mode, why in (("transport_none", "transport_none"),
                      ("transport_not_ok", "transport_not_ok"),
                      ("transport_malformed", "transport_malformed:list")):
        fx, srv = mkfx()
        g27server.enqueue(srv, 901, OWNER, MONTXT)
        rc, out, _ = run(fx, srv, mode)
        s = g27server._load(srv)
        oks.append(rc == 0 and out.get("transport") == "error"
                   and out.get("reason") == why and out.get("offset") == 0
                   and s["server_confirmed"] == [] and s["queue"]
                   and lane_ids(fx) == set() and cursor(fx) == 0
                   and len(s["requested_offsets"]) == 0)  # transport died before the server saw a request
    check("T10 transport error/malformed: disposition, no fabricated success",
          all(oks), str(oks))

    # ---------------- routing matrix on FINAL bytes
    for p in ("/home/ari/ofn", "/home/ari/ofn/ofn", "/home/ari/ofn/ofn/agents",
              "/home/ari/ofn/ofn/budget"):
        sys.path.insert(0, p)
    spec = importlib.util.spec_from_file_location("glass_rm", ART)
    gm = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gm)
    fx, srv = mkfx()
    gm._B3_REGISTRY = fx / "registry.json"
    cases = [
        ("Confirming " + REG_HASH, "B3", "resolves_to_registered_b3_card"),
        ("بفرست " + REG_HASH, "B3", "resolves_to_registered_b3_card"),
        ("ارسال " + REG_HASH, "B3", "resolves_to_registered_b3_card"),
        ("Confirming " + "f" * 32, "B3", "carries_payload_length_hash"),
        ("Confirming " + "f" * 16, "B3", "card_confirm_language"),
        ("0" + REG_HASH, "B3", "carries_payload_length_hash"),
        ("x" + REG_HASH + "x", "MONEY", "not_b3_shaped"),
        ("بفرست", "MONEY", "not_b3_shaped"),
        ("بفرست MONEY-BATCH", "MONEY", "not_b3_shaped"),
        (REG_HASH + " و " + "b" * 64, "B3", "resolves_to_registered_b3_card"),
        ("", None, "empty"),
    ]
    rm_ok = True
    for text, want_lane, want_reason in cases:
        d = gm._route_owner_message(text)
        if d["route"] != want_lane or d["reason"] != want_reason:
            rm_ok = False
            print("       RM-MISMATCH: %r -> %s/%s (want %s/%s)"
                  % (text[:40], d["route"], d["reason"], want_lane, want_reason))
    hexf = gm._HEX_PAT.findall("xa03b2ecc" + "9" * 56 + "x")
    check("RM routing matrix on final bytes (9 cases incl بفرست/ارسال)", rm_ok
          and hexf == [], "hex-boundary=%s" % hexf)
    print("       [scope] bare «بفرست»/named-card MONEY rows are consumed by"
          " owner_reply gates (f8187600: no-identity=0 calls, ambiguity=0 calls,"
          " named card=1 call - prior regression, not re-run here)")

    g1 = guard()
    check("ISOLATION: production glass files byte-identical", g0 == g1)

    print()
    print("G27B_BATTERY:", "PASS" if not FAIL else "FAIL -> " + ", ".join(FAIL))
    return 0 if not FAIL else 1


if __name__ == "__main__":
    sys.exit(main())
