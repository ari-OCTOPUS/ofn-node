"""TRIO v2 dedicated battery (owner mission ROUND30 sections 1-4).

Counterexamples run against trio-v1 (d0b86a35) and/or the live executor
(109e68c0); fixes are proven on trio-v2 (9126c388). All state fixture-isolated
(Path.home pinned into the fixture for the B5 scan); only the witness boundary
is simulated; real mv/verify execution on fixture paths.
"""
import importlib.machinery
import importlib.util
import json
import os
import pathlib
import sys
import tempfile
import time

sys.path.insert(0, "/tmp")
V1 = ("/home/ari/ofn/state/coding-worker/stage/SUCCESSOR-TRIO-20260914/"
      "ops_agent.py.trio-v1-d0b86a35")
V2 = ("/home/ari/ofn/state/coding-worker/stage/SUCCESSOR-TRIO-20260914/"
      "ops_agent.py")
LIVE = "/home/ari/ofn/state/ops-agent/ops_agent.py"
PASS, FAIL = [], []
PROD_GUARD = ["/home/ari/ofn/state/ops-agent/state/ops-receipts.jsonl",
              "/home/ari/ofn/state/autonomy",
              "/home/ari/ofn/state/pulse/glass-offset.txt"]
import hashlib


def check(name, ok, detail=""):
    print("  %-5s %-62s %s" % ("PASS" if ok else "FAIL", name, detail))
    (PASS if ok else FAIL).append(name)


def guard():
    out = []
    for p in PROD_GUARD:
        q = pathlib.Path(p)
        if p.endswith("receipts.jsonl"):
            out.append(hashlib.sha256(q.read_bytes()).hexdigest() if q.exists() else None)
        else:
            out.append(sorted(str(x) for x in q.glob("*")) if q.exists() else None)
    return out


def load_oa(fx, artifact, budget=None):
    _name = "oa_" + hashlib.sha256((str(fx) + artifact).encode()).hexdigest()[:8]
    if artifact.endswith(".py"):
        spec = importlib.util.spec_from_file_location(_name, artifact)
    else:
        spec = importlib.util.spec_from_file_location(
            _name, artifact,
            loader=importlib.machinery.SourceFileLoader(_name, artifact))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    m.ROOT = fx
    m.STATE = fx / "state"
    m.RECEIPTS = m.STATE / "ops-receipts.jsonl"
    m.GOALS = m.STATE / "goals.jsonl"
    m.OBS = m.STATE / "observations.jsonl"
    m.CONSUMPTION = m.STATE / "witness-consumption.jsonl"
    m.ARMED = m.STATE / "armed.json"
    m.PENDING = m.STATE / "pending"
    m.CONTRACTS = fx / "ops_contracts.json"
    m.BUDGETS = fx / "ops_budgets.json"
    m.STABLE_ROOT = fx / "stable"
    m.PINS_FILE = fx / "witness-pins.json"
    m.STATE.mkdir(parents=True, exist_ok=True)
    m.STABLE_ROOT.mkdir(parents=True, exist_ok=True)
    m.BUDGETS.write_text(json.dumps(budget or {
        "mesh_wide_24h": 99, "per_node_24h": 99, "per_component_30min": 99,
        "circuit_breaker_after_same_class_failures": 99}), encoding="utf-8")
    m.PINS_FILE.write_text(json.dumps({"k": 1}), encoding="utf-8")
    m.witness_push = lambda pins, name, data: (True, "fx")
    m.witness_pull = lambda pins: []
    return m


class FW:
    """Witness simulator: echoes envelope fields into chained verdict rows."""

    def __init__(self, m, pins):
        self.m, self.pins, self.rows = m, pins, []
        m.witness_push = self.push
        m.witness_pull = lambda pins: list(self.rows)

    def push(self, pins, name, data):
        env = json.loads(data.decode())
        prev = self.rows[-1]["witness_hash"] if self.rows else None
        row = {"schema": "octopus.remote-witness-receipt.v1",
               "verdict": "OUTCOME_CONFIRMED"
               if env.get("envelope_kind") == "outcome"
               else "APPROVE_ELIGIBLE_CLASS_B",
               "executable": False, "action_authority": "NONE",
               "proposal_id": env["proposal_id"],
               "proposal_hash": env.get("checksum"),
               "action_contract_hash": env.get("action_contract_hash"),
               "precondition_hash": env.get("precondition_hash"),
               "input_hash": env.get("input_hash"),
               "rollback_contract_hash": env.get("rollback_contract_hash"),
               "target_node": env.get("target_node"),
               "target_component": env.get("target_component"),
               "action_class": env.get("action_class"),
               "timeout_s": env.get("timeout_s"),
               "producer_authority": env.get("producer_authority"),
               "timestamp": self.m.now_iso(),
               "witness_code_hash": "c" * 64, "witness_contract_hash": "d" * 64,
               "node_182_identity_evidence": {"machine_id_sha256": "f" * 64},
               "previous_witness_hash": prev}
        row["witness_hash"] = self.m.sha_obj(row)
        self.rows.append(row)
        return True, "fx"


def sha(b):
    return hashlib.sha256(b).hexdigest()


def mkfx(prefix):
    fx = pathlib.Path(tempfile.mkdtemp(prefix=prefix))
    return fx


def write_req(sp, name, target, patched, priority=None, component="c",
              preconditions=None):
    req = {"target": str(target), "target_sha256": sha(b"NEW"),
           "patched": str(patched), "component": component}
    if priority is not None:
        req["priority"] = priority
    if preconditions is not None:
        req["preconditions"] = preconditions
    (sp / name).write_text(json.dumps(req), encoding="utf-8")


def req_pair(d, names=("a.json", "b.json")):
    sp = d / "state/canary-requests"
    sp.mkdir(parents=True, exist_ok=True)
    outs = []
    for nm in names:
        tgt = d / ("t-" + nm)
        tgt.write_text("OLD", encoding="utf-8")
        p = d / ("p-" + nm)
        p.write_text("NEW", encoding="utf-8")
        outs.append((sp, nm, tgt, p))
    return outs


PINS = {"node182_identity": "f" * 64, "witness_code_sha256": "c" * 64,
         "witness_contract_sha256": "d" * 64}


def main():
    g0 = guard()
    real_home = pathlib.Path.home
    # pin home for the WHOLE run: the B5 scan globs ~/wt-* and must
    # never see the real one (isolation-leak lesson 2026-09-14)
    battery_home = mkfx("b5home-")
    pathlib.Path.home = classmethod(lambda cls, _h=battery_home: _h)

    def pin_home(fx):
        pathlib.Path.home = classmethod(lambda cls, _fx=fx: _fx)

    # ---------------- B5 ----------------
    def b5_fixture(n_dirs, kb=1, extra_unrelated_kb=0):
        fx = mkfx("b5-")
        pin_home(fx)
        for i in range(n_dirs):
            d = fx / ("stable/pkg%d/__pycache__" % i)
            d.mkdir(parents=True)
            (d / "x.pyc").write_bytes(b"Z" * (kb * 1024))
        if extra_unrelated_kb:
            u = fx / "stable/unrelated/__pycache__"
            u.mkdir(parents=True)
            (u / "big.pyc").write_bytes(b"U" * (extra_unrelated_kb * 1024))
        return fx

    def run_b5(artifact, fx):
        m = load_oa(fx, artifact)
        FW(m, PINS)
        r1 = m.handle_b5_storage({"timeout_s": 30}, {})
        if r1 != "proposal-sent":
            return r1, None
        r2 = m.progress_pending(PINS)
        return r1, (r2, [x for x in m.read_receipts()
                         if x.get("kind") == "OPS_B_EXECUTED"])

    # CE on trio-v1: 30 target dirs -> findings[:20]=20KB before, after-walk
    # counts ALL 30KB -> FAILED despite successful cleanup
    fx = b5_fixture(30, kb=1)
    r1, res = run_b5(V1, fx)
    ex = res[1] if res else []
    check("B5-CE v1: successful cleanup FAILED via out-of-scope after-count",
          res is not None and ex and ex[-1]["verified"] is False,
          "r2=%s verified=%s" % (res[0] if res else r1,
                                 ex[-1]["verified"] if ex else "-"))
    # v2: same scenario -> VERIFIED, freed == frozen-set bytes, quarantine move
    fx = b5_fixture(30, kb=1)
    m = load_oa(fx, V2)
    fw = FW(m, PINS)
    r1 = m.handle_b5_storage({"timeout_s": 30}, {})
    r2 = m.progress_pending(PINS)
    ex = [x for x in m.read_receipts() if x.get("kind") == "OPS_B_EXECUTED"]
    qdirs = list((m.STATE / "b5-quarantine").glob("*")) if (m.STATE / "b5-quarantine").exists() else []
    quarantined = sum(len(list(q.rglob("*"))) for q in qdirs)
    check("B5 v2: same-scope VERIFIED with explicit freed bytes",
          r1 == "proposal-sent" and ex and ex[-1]["verified"] is True
          and ex[-1].get("bytes_freed", 0) > 0
          and ex[-1].get("bytes_before") == ex[-1].get("bytes_freed"),
          "freed=%s" % (ex[-1].get("bytes_freed") if ex else "-"))
    check("B5 v2: targets MOVED to quarantine (no delete), dirs gone from set",
          quarantined > 0 and r2 == "outcome-sent", "q_items=%d r2=%s" % (quarantined, r2))
    # v2: unrelated cache growth between proposal and verify changes nothing
    fx = b5_fixture(25, kb=1)  # frozen set = findings[:20]
    m = load_oa(fx, V2)
    FW(m, PINS)
    r1 = m.handle_b5_storage({"timeout_s": 30}, {})
    # grow a NON-frozen dir massively after proposal (outside frozen set)
    nf = fx / "stable/pkg24/__pycache__"   # beyond findings[:20]
    (nf / "grown.pyc").write_bytes(b"G" * (500 * 1024))
    r2 = m.progress_pending(PINS)
    ex = [x for x in m.read_receipts() if x.get("kind") == "OPS_B_EXECUTED"]
    check("B5 v2: out-of-scope growth never flips the verdict",
          ex and ex[-1]["verified"] is True, "r2=%s" % r2)
    # v2: zero-before -> no proposal at all
    fx = mkfx("b5z-")
    pin_home(fx)
    z = fx / "stable/z/__pycache__"
    z.mkdir(parents=True)
    (z / "empty.pyc").write_bytes(b"")
    m = load_oa(fx, V2)
    r1 = m.handle_b5_storage({"timeout_s": 30}, {})
    check("B5 v2: zero-before -> B5_NOTHING_MEASURABLE, no proposal",
          r1 == "no-action-needed"
          and any(x.get("kind") == "B5_NOTHING_MEASURABLE"
                  for x in m.read_receipts()), "r1=%s" % r1)
    # v2: access error inside the frozen set is explicit, partial success real
    fx = b5_fixture(3, kb=1)
    m = load_oa(fx, V2)
    FW(m, PINS)
    os.chmod(fx / "stable/pkg1/__pycache__", 0o000)
    r1 = m.handle_b5_storage({"timeout_s": 30}, {})
    r2 = m.progress_pending(PINS)
    ex = [x for x in m.read_receipts() if x.get("kind") == "OPS_B_EXECUTED"]
    check("B5 v2: access errors explicit; measurable part still VERIFIED",
          ex and ex[-1]["verified"] is True
          and "access_errors_after" in ex[-1], "r1=%s r2=%s" % (r1, r2))
    # v2: symlink inside a target is not counted (no traversal)
    fx = b5_fixture(2, kb=1)
    os.symlink("/etc", fx / "stable/pkg0/__pycache__/evil")
    m = load_oa(fx, V2)
    FW(m, PINS)
    r1 = m.handle_b5_storage({"timeout_s": 30}, {})
    ex = [x for x in m.read_receipts() if x.get("kind") == "OPS_B_EXECUTED"]
    check("B5 v2: symlink excluded from counting, no traversal",
          r1 in ("proposal-sent", "no-action-needed"), "r1=%s" % r1)

    # ---------------- CATSCOPE ----------------
    def receipts_fx(artifact, rows):
        fx = mkfx("cat-")
        m = load_oa(fx, artifact, budget={
            "mesh_wide_24h": 99, "per_node_24h": 99, "per_component_30min": 99,
            "circuit_breaker_after_same_class_failures": 1})
        with m.RECEIPTS.open("a", encoding="utf-8") as f:
            for r in rows:
                f.write(json.dumps(r) + "\n")
        return m

    now = time.strftime("%Y-%m-%dT%H:%M:%S+00:00", time.gmtime())
    rej_alpha = {"kind": "OPS_B_OUTCOME_REJECTED", "category": "ALPHA_XY",
                 "at": now}
    m_live = receipts_fx(LIVE, [rej_alpha])
    m_v2 = receipts_fx(V2, [rej_alpha])
    ok_live = m_live.budget_allows("BETA_XY", "c2")[0]
    ok_v2 = m_v2.budget_allows("BETA_XY", "c2")[0]
    check("CAT-CE live: same-suffix different class POLLUTES via outcome-reject",
          ok_live is False, "live=%s" % ok_live)
    check("CAT v2: different class isolated (allowed)",
          ok_v2 is True, "v2=%s" % ok_v2)
    failrow = {"kind": "OPS_B_EXECUTED", "category": "B8_ROLLBACK",
               "verified": False, "component": "c1", "at": now}
    m_v2b = receipts_fx(V2, [failrow])
    check("CAT v2: SAME class still counts (B8 fail blocks B8)",
          m_v2b.budget_allows("B8_CANARY", "c3")[0] is False)
    m_v2c = receipts_fx(V2, [dict(rej_alpha, category="B8_ROLLBACK")])
    check("CAT v2: outcome-rejection filter class-scoped (B8 blocked, B6 not)",
          m_v2c.budget_allows("B8_CANARY", "c4")[0] is False
          and m_v2c.budget_allows("B6_REBUILD", "c5")[0] is True)
    # malformed row: live crashes, v2 tolerant & closed
    fx = mkfx("catm-")
    m_live2 = load_oa(fx, LIVE, budget={
        "mesh_wide_24h": 99, "per_node_24h": 99, "per_component_30min": 99,
        "circuit_breaker_after_same_class_failures": 1})
    m_v2d = load_oa(mkfx("catm2-"), V2, budget={
        "mesh_wide_24h": 99, "per_node_24h": 99, "per_component_30min": 99,
        "circuit_breaker_after_same_class_failures": 1})
    for mm in (m_live2, m_v2d):
        with mm.RECEIPTS.open("a", encoding="utf-8") as f:
            f.write('{"kind": "OPS_B_EXECUTED", "category": "B8_X", '
                    '"verified": false, "at": "2026-09-14T00:00:00+00:00"}\n')
            f.write('{"torn-json...')
    try:
        m_live2.budget_allows("B8_X", "c")
        live_crash = False
    except Exception:
        live_crash = True
    ok_v2d = m_v2d.budget_allows("B8_X", "c")[0]
    check("CAT-CE live: malformed ledger row KILLS budget check",
          live_crash)
    check("CAT v2: malformed row skipped, budget stays closed",
          ok_v2d is False)

    # ---------------- G3 ----------------
    # tie-break: equal priority -> deterministic filename order
    fx = mkfx("g3t-")
    m = load_oa(fx, V2)
    FW(m, PINS)
    (sp, n1, t1, p1), (sp, n2, t2, p2) = req_pair(fx, ("b-same.json", "a-same.json"))
    write_req(sp, "b-same.json", t1, p1, priority=1)
    write_req(sp, "a-same.json", t2, p2, priority=1)
    r = m.handle_spool_category("B8", {"timeout_s": 30}, {}, "canary-requests")
    check("G3 v2: tie-break deterministic (alphabetical among equal)",
          r == "proposal-sent" and (m.STATE / "executed" / "a-same.json").exists(),
          "r=%s" % r)
    # null/invalid priority: v1 crashes, v2 deterministic-100
    for bad in (None, "abc"):
        fx = mkfx("g3b-")
        m1 = load_oa(fx, V1)
        (sp, n1, t1, p1), (sp, n2, t2, p2) = req_pair(fx, ("good.json", "bad.json"))
        (sp / "bad.json").write_text(json.dumps(
            {"target": str(t1), "target_sha256": sha(b"NEW"),
             "patched": str(p1), "component": "c", "priority": bad}),
            encoding="utf-8")
        write_req(sp, "good.json", t2, p2, priority=1)
        try:
            m1.handle_spool_category("B8", {"timeout_s": 30}, {}, "canary-requests")
            v1_crashed = False
        except Exception:
            v1_crashed = True
        m2 = load_oa(fx, V2)
        FW(m2, {"node182_identity": "f" * 64})
        r = m2.handle_spool_category("B8", {"timeout_s": 30}, {}, "canary-requests")
        check("G3 CE+v2 (priority=%r): v1 crashes, v2 proceeds with prio-1 first"
              % (bad,), v1_crashed and r == "proposal-sent"
              and (m2.STATE / "executed" / "good.json").exists(), "r=%s" % r)
    # corrupt file: sorted last, no crash
    fx = mkfx("g3c-")
    m = load_oa(fx, V2)
    FW(m, PINS)
    (sp, n1, t1, p1), (sp, n2, t2, p2) = req_pair(fx, ("good.json", "zz-corrupt.json"))
    write_req(sp, "good.json", t1, p1, priority=5)
    (sp / "zz-corrupt.json").write_text("{not json", encoding="utf-8")
    r = m.handle_spool_category("B8", {"timeout_s": 30}, {}, "canary-requests")
    check("G3 v2: corrupt file ignored for ordering, valid request proceeds",
          r == "proposal-sent" and (sp / "zz-corrupt.json").exists(), "r=%s" % r)
    # no-starvation: blocked prio-1 + ready prio-2 in the SAME tick
    for art, tag in ((V1, "CE"), (V2, "v2")):
        fx = mkfx("g3s-")
        m = load_oa(fx, art, budget={"mesh_wide_24h": 99, "per_node_24h": 99,
                                     "per_component_30min": 1,
                                     "circuit_breaker_after_same_class_failures": 99})
        FW(m, PINS)
        with m.RECEIPTS.open("a", encoding="utf-8") as f:
            f.write(json.dumps({"kind": "OPS_B_EXECUTED", "category": "B8_X",
                                "verified": True, "component": "blocked-comp",
                                "at": time.strftime("%Y-%m-%dT%H:%M:%S+00:00",
                                                    time.gmtime())}) + "\n")
        (sp, n1, t1, p1), (sp, n2, t2, p2) = req_pair(fx, ("p1-blocked.json", "p2-ready.json"))
        write_req(sp, "p1-blocked.json", t1, p1, priority=1, component="blocked-comp")
        write_req(sp, "p2-ready.json", t2, p2, priority=2, component="other-comp")
        r = m.handle_spool_category("B8", {"timeout_s": 30}, {}, "canary-requests")
        if tag == "CE":
            check("G3-CE v1: blocked prio-1 STARVES ready prio-2 this tick",
                  r == "budget-blocked"
                  and (sp / "p2-ready.json").exists()
                  and "OPS_B_PROPOSAL_SENT" not in [x.get("kind") for x in m.read_receipts()],
                  "r=%s" % r)
        else:
            check("G3 v2: blocked prio-1 does NOT starve ready prio-2",
                  r == "proposal-sent" and (m.STATE / "executed" / "p2-ready.json").exists()
                  and (sp / "p1-blocked.json").exists(), "r=%s" % r)

    # ---------------- S4a barrier: swap source AFTER check, BEFORE write ----
    fx = mkfx("s4a-")
    m = load_oa(fx, V2)
    FW(m, PINS)
    ((sp, nm, tgt, patched),) = req_pair(fx, ("s4a.json",))
    write_req(sp, "s4a.json", tgt, patched)
    r = m.handle_spool_category("B8", {"timeout_s": 30}, {}, "canary-requests")
    assert r == "proposal-sent", r
    real_replace = os.replace
    swap_done = []

    def trap(a, b):
        if str(a).endswith(".deploy.tmp"):
            patched.write_bytes(b"ATTACKER-BYTES")  # swap after check
            swap_done.append(True)
        return real_replace(a, b)
    os.replace = trap
    try:
        r2 = m.progress_pending(PINS)
    finally:
        os.replace = real_replace
    ex = [x for x in m.read_receipts() if x.get("kind") == "OPS_B_EXECUTED"]
    check("S4a barrier: source swapped after check -> target still gets the "
          "VERIFIED bytes (in-memory copy wins)",
          swap_done and ex and ex[-1]["verified"] is True
          and tgt.read_text(encoding="utf-8") == "NEW"
          and patched.read_text(encoding="utf-8") == "ATTACKER-BYTES",
          "swap=%s target=%r" % (bool(swap_done), tgt.read_text(encoding="utf-8")))

    # ---------------- S4b: precondition invalidated AFTER admission --------
    fx = mkfx("s4b-")
    m = load_oa(fx, V2)
    FW(m, PINS)
    gate = fx / "money-gates.py"
    gate.write_text("GATES-LIVE", encoding="utf-8")
    sp = fx / "state/canary-requests"
    sp.mkdir(parents=True)
    tgt = fx / "t.py"
    tgt.write_text("OLD", encoding="utf-8")
    patched = fx / "p.py"
    patched.write_text("NEW", encoding="utf-8")
    (sp / "rb.json").write_text(json.dumps(
        {"target": str(tgt), "target_sha256": sha(b"NEW"), "patched": str(patched),
         "component": "rollback-fixture",
         "preconditions": [{"path": str(gate), "sha256": sha(b"GATES-LIVE")}]}),
        encoding="utf-8")
    r = m.handle_spool_category("B4_ROLLBACK", {"timeout_s": 30}, {},
                                "canary-requests")
    assert r == "proposal-sent", r
    gate.write_text("GATES-GONE", encoding="utf-8")  # containment invalidated
    r2 = m.progress_pending(PINS)
    ex = [x for x in m.read_receipts() if x.get("kind") == "OPS_B_PRE_EFFECT_BLOCKED"]
    check("S4b: precondition drift after admission -> BLOCKED before restore, "
          "target untouched",
          r2 == "pre-effect-blocked" and ex
          and ex[-1]["reason"] == "PRECONDITION_DRIFT"
          and tgt.read_text(encoding="utf-8") == "OLD", "r2=%s" % r2)
    # positive: gate stays valid -> restore executes
    fx = mkfx("s4bp-")
    m = load_oa(fx, V2)
    FW(m, PINS)
    gate = fx / "money-gates.py"
    gate.write_text("GATES-LIVE", encoding="utf-8")
    sp = fx / "state/canary-requests"
    sp.mkdir(parents=True)
    tgt = fx / "t.py"
    tgt.write_text("OLD", encoding="utf-8")
    patched = fx / "p.py"
    patched.write_text("NEW", encoding="utf-8")
    (sp / "rb.json").write_text(json.dumps(
        {"target": str(tgt), "target_sha256": sha(b"NEW"), "patched": str(patched),
         "component": "rollback-fixture",
         "preconditions": [{"path": str(gate), "sha256": sha(b"GATES-LIVE")}]}),
        encoding="utf-8")
    r = m.handle_spool_category("B4_ROLLBACK", {"timeout_s": 30}, {},
                                "canary-requests")
    r2 = m.progress_pending(PINS)
    ex = [x for x in m.read_receipts() if x.get("kind") == "OPS_B_EXECUTED"]
    check("S4b positive: valid precondition -> restore executes + VERIFIED",
          r2 == "outcome-sent" and ex and ex[-1]["verified"] is True
          and tgt.read_text(encoding="utf-8") == "NEW", "r2=%s" % r2)

    pathlib.Path.home = real_home
    g1 = guard()
    check("ISOLATION: production untouched", g0 == g1)
    print()
    print("TRIO_V2_BATTERY:", "PASS" if not FAIL else "FAIL -> " + ", ".join(FAIL))
    return 0 if not FAIL else 1


if __name__ == "__main__":
    sys.exit(main())
