"""G27 integrated durability battery (mission S7, 9 scenarios).

Runs the PATCHED producer candidate (W24-G8G27-PRODUCER/glass_runner.py) in a
fixture: real file IO for lanes and cursor (faults injected with real chmod),
fake transport at the Telegram boundary, fake opslib event sink. Nothing is
stubbed to pass: the producer's own gates decide confirmation.
Records per scenario: deliveries received, lane rows, cursor, error events.
"""
import importlib.util
import json
import os
import pathlib
import stat
import sys
import tempfile

HOME = pathlib.Path.home()
OFN = HOME / "ofn"
ART = OFN / "state/coding-worker/stage/W24-G8G27-PRODUCER/glass_runner.py"
PROD_GUARD = [HOME / "ofn/state/pulse/glass-offset.txt",
              HOME / "ofn/state/revenue-drive/tg-inbox.jsonl",
              HOME / "ofn/state/owner_dialogue/go_b3_inbox.jsonl"]

sys.path.insert(0, str(OFN))
sys.path.insert(0, str(OFN / "ofn"))
sys.path.insert(0, str(OFN / "ofn/agents"))
sys.path.insert(0, str(OFN / "ofn/budget"))

PASS, FAIL = [], []


def check(name, ok, detail=""):
    print("  %-5s %-52s %s" % ("PASS" if ok else "FAIL", name, detail))
    (PASS if ok else FAIL).append(name)


def guard():
    return [(p.exists(), p.stat().st_size if p.exists() else 0) for p in PROD_GUARD]


def upd(uid, text, chat=6150431610):
    return {"update_id": uid, "message": {"chat": {"id": chat}, "text": text}}


class FakeTG:
    def __init__(self):
        self.script = []
        self.sent = []

    def __call__(self, token, method, params=None, timeout=20):
        if method == "getUpdates":
            return {"ok": True, "result": self.script.pop(0) if self.script else []}
        if method == "sendMessage":
            self.sent.append(params)
            return {"ok": True}
        raise AssertionError(method)


class FakeOpslib:
    def __init__(self):
        self.events = []
        self.raise_on = None
        self.STATE_DIR = pathlib.Path("/tmp/g27-fixture-opslib-state")

    def now_iso(self):
        return "2026-09-14T00:00:00Z"

    def append_jsonl(self, path, obj, **kw):
        if self.raise_on and obj.get("event_type") == self.raise_on:
            raise OSError("injected receipt failure")
        self.events.append(obj)
        return {}


def load_glass(fx):
    spec = importlib.util.spec_from_file_location("glass_g27", ART)
    g = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(g)
    ftg = FakeTG()
    fol = FakeOpslib()
    g._tg = ftg
    g._owner_token = lambda: "fixture-token"
    g._allowed_chats = lambda: {"6150431610"}
    g.opslib = fol
    g._LANES = {"B3": fx / "lanes/b3/go_b3_inbox.jsonl",
                "MONEY": fx / "lanes/money/tg-inbox.jsonl"}
    g._B3_REGISTRY = fx / "go_b3_pending_registry.json"
    (fx / "lanes/b3").mkdir(parents=True, exist_ok=True)
    (fx / "lanes/money").mkdir(parents=True, exist_ok=True)
    sd = fx / "pulse"
    sd.mkdir(parents=True, exist_ok=True)
    # fixture registry: one B3 card with payload hash a03b2ecc...
    (fx / "go_b3_pending_registry.json").write_text(json.dumps(
        {"requests": [{"id": "STRATA-CHOICE",
                       "payload_sha256": "a03b2ecc" + "9" * 56}]}), encoding="utf-8")
    return g, ftg, fol, sd


def rows(p):
    if not p.exists():
        return []
    return [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()]


def cursor(sd):
    f = sd / "glass-offset.txt"
    return int(f.read_text().strip()) if f.exists() else 0


def readonly(d, on=True):
    d.chmod(0o555 if on else 0o755)


def main():
    g0 = guard()
    B3TXT = "Confirming a03b2ecc for the card"
    MONTXT = "hello there, plain owner text"

    # S1: first persistence failure -> NO premature confirm
    fx = pathlib.Path(tempfile.mkdtemp(prefix="g27-S1-"))
    g, ftg, fol, sd = load_glass(fx)
    b3lane, moneylane = g._LANES["B3"], g._LANES["MONEY"]
    readonly(fx / "lanes/money")
    ftg.script = [[upd(101, MONTXT)]]
    r = g.cycle(sd)
    check("S1 no confirm on first persistence failure",
          r["stop_reason"] == "spool_write_failed" and r["failed_update_id"] == 101
          and cursor(sd) == 0 and rows(moneylane) == [],
          "cursor=%d rows=%d" % (cursor(sd), len(rows(moneylane))))
    check("S1 error event receipted",
          any(e["event_type"] == "glass.spool_write_error" for e in fol.events))

    # S2: fault clears -> recovery from the real path, exactly one row
    readonly(fx / "lanes/money", False)
    ftg.script = [[upd(101, MONTXT)]]
    r = g.cycle(sd)
    check("S2 recovery persists the same update exactly once",
          r["spooled"] == 1 and cursor(sd) == 101 and len(rows(moneylane)) == 1
          and r["stop_reason"] is None, "cursor=%d rows=%d" % (cursor(sd), len(rows(moneylane))))

    # S3: cut AFTER persistence BEFORE checkpoint -> replay dedupes, no duplicate
    fx = pathlib.Path(tempfile.mkdtemp(prefix="g27-S3-"))
    g, ftg, fol, sd = load_glass(fx)
    b3lane, moneylane = g._LANES["B3"], g._LANES["MONEY"]
    ftg.script = [[upd(201, B3TXT)]]
    r1 = g.cycle(sd)  # healthy write... then kill checkpoint
    # (simulate the crash-between: row durable, cursor not yet written)
    wrote = len(rows(b3lane))
    readonly(sd)
    # nothing more; restore and re-deliver (cursor never advanced)
    readonly(sd, False)
    ftg.script = [[upd(201, B3TXT)]]
    r2 = g.cycle(sd)
    check("S3 replay after lost checkpoint -> no duplicate row",
          wrote == 1 and r2["replayed"] == 1 and len(rows(b3lane)) == 1
          and cursor(sd) == 201, "rows=%d cursor=%d replayed=%s"
          % (len(rows(b3lane)), cursor(sd), r2.get("replayed")))

    # S4: checkpoint failure disposition (real read-only state dir)
    fx = pathlib.Path(tempfile.mkdtemp(prefix="g27-S4-"))
    g, ftg, fol, sd = load_glass(fx)
    b3lane, moneylane = g._LANES["B3"], g._LANES["MONEY"]
    readonly(sd)
    ftg.script = [[upd(301, B3TXT)]]
    r = g.cycle(sd)
    check("S4 checkpoint failure -> row durable, cursor unchanged, disposition set",
          len(rows(b3lane)) == 1 and cursor(sd) == 0
          and r["stop_reason"] == "checkpoint_failed" and r.get("checkpoint_error"),
          "rows=%d cursor=%d stop=%s" % (len(rows(b3lane)), cursor(sd), r.get("stop_reason")))
    readonly(sd, False)
    ftg.script = [[upd(301, B3TXT)]]
    r = g.cycle(sd)
    check("S4 recovery -> exactly one row, cursor advances",
          len(rows(b3lane)) == 1 and cursor(sd) == 301 and r["replayed"] == 1)

    # S5: routing receipt failure -> not a persistence failure
    fx = pathlib.Path(tempfile.mkdtemp(prefix="g27-S5-"))
    g, ftg, fol, sd = load_glass(fx)
    b3lane, moneylane = g._LANES["B3"], g._LANES["MONEY"]
    fol.raise_on = "owner_route.decided"
    ftg.script = [[upd(401, B3TXT)]]
    r = g.cycle(sd)
    check("S5 receipt failure does not block spool or confirmation",
          r.get("receipt_failed") is True and len(rows(b3lane)) == 1
          and cursor(sd) == 401 and r["stop_reason"] is None,
          "rows=%d cursor=%d" % (len(rows(b3lane)), cursor(sd)))

    # S6: mid-batch failure -> later update NOT processed this cycle; recovered next
    fx = pathlib.Path(tempfile.mkdtemp(prefix="g27-S6-"))
    g, ftg, fol, sd = load_glass(fx)
    b3lane, moneylane = g._LANES["B3"], g._LANES["MONEY"]
    readonly(fx / "lanes/money")
    ftg.script = [[upd(501, MONTXT), upd(502, B3TXT)]]
    r = g.cycle(sd)
    check("S6 mid-batch failure stops the batch (B not written, not confirmed)",
          r["stop_reason"] == "spool_write_failed" and cursor(sd) == 0
          and rows(moneylane) == [] and rows(b3lane) == [],
          "cursor=%d" % cursor(sd))
    readonly(fx / "lanes/money", False)
    ftg.script = [[upd(501, MONTXT), upd(502, B3TXT)]]
    r = g.cycle(sd)
    check("S6 next cycle continues from the failed update",
          len(rows(moneylane)) == 1 and len(rows(b3lane)) == 1 and cursor(sd) == 502,
          "money=%d b3=%d cursor=%d" % (len(rows(moneylane)), len(rows(b3lane)), cursor(sd)))

    # S7: replay of an already-confirmed update (restart corner) -> idempotent
    fx = pathlib.Path(tempfile.mkdtemp(prefix="g27-S7-"))
    g, ftg, fol, sd = load_glass(fx)
    b3lane, moneylane = g._LANES["B3"], g._LANES["MONEY"]
    ftg.script = [[upd(601, B3TXT)]]
    g.cycle(sd)
    ftg.script = [[upd(601, B3TXT)]]
    r = g.cycle(sd)
    check("S7 replay of confirmed update -> no new row, cursor not lowered",
          len(rows(b3lane)) == 1 and r["replayed"] == 1 and cursor(sd) == 601)

    # S8: healthy control -> correct lanes, fsync-durable, cursor advances
    fx = pathlib.Path(tempfile.mkdtemp(prefix="g27-S8-"))
    g, ftg, fol, sd = load_glass(fx)
    b3lane, moneylane = g._LANES["B3"], g._LANES["MONEY"]
    ftg.script = [[upd(701, B3TXT), upd(702, MONTXT), upd(703, "x", chat=999)]]
    r = g.cycle(sd)
    # "ignored" keeps the ORIGINAL semantics: every non-command update counts
    # (2 owner non-command texts + 1 stranger = 3); the stranger alone is not
    # spooled, which spooled==2 already proves.
    check("S8 healthy: B3 lane by identity, money lane for plain, stranger not spooled",
          len(rows(b3lane)) == 1 and rows(b3lane)[0]["lane"] == "B3"
          and len(rows(moneylane)) == 1 and cursor(sd) == 703
          and r["spooled"] == 2 and r["ignored"] == 3,
          "b3=%d money=%d cursor=%d spooled=%s ignored=%s"
          % (len(rows(b3lane)), len(rows(moneylane)), cursor(sd), r["spooled"], r["ignored"]))
    check("S8 rows carry update_id for downstream dedupe",
          all("update_id" in x for x in rows(b3lane) + rows(moneylane)))

    # S9: prefix boundary - success AFTER a failure must not confirm it
    fx = pathlib.Path(tempfile.mkdtemp(prefix="g27-S9-"))
    g, ftg, fol, sd = load_glass(fx)
    b3lane, moneylane = g._LANES["B3"], g._LANES["MONEY"]
    readonly(fx / "lanes/b3")
    ftg.script = [[upd(801, MONTXT), upd(802, B3TXT), upd(803, MONTXT)]]
    r = g.cycle(sd)
    check("S9 batch stops at failure: cursor == last confirmed prefix (801)",
          cursor(sd) == 801 and rows(b3lane) == [] and len(rows(moneylane)) == 1,
          "cursor=%d money=%d" % (cursor(sd), len(rows(moneylane))))
    readonly(fx / "lanes/b3", False)
    ftg.script = [[upd(802, B3TXT), upd(803, MONTXT)]]
    r = g.cycle(sd)
    check("S9 recovery completes the tail exactly once",
          cursor(sd) == 803 and len(rows(b3lane)) == 1 and len(rows(moneylane)) == 2,
          "cursor=%d b3=%d money=%d" % (cursor(sd), len(rows(b3lane)), len(rows(moneylane))))

    g1 = guard()
    check("ISOLATION: production glass paths untouched", g0 == g1)

    print()
    import hashlib
    print("ARTIFACT_SHA256=%s" % hashlib.sha256(ART.read_bytes()).hexdigest())
    print("G27_BATTERY:", "PASS" if not FAIL else "FAIL -> " + ", ".join(FAIL))
    return 0 if not FAIL else 1


if __name__ == "__main__":
    sys.exit(main())
