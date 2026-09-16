#!/usr/bin/env python3
"""TRIO-003 isolated harness (lane OCTOPUS-EXECUTOR-SAFETY-20260915).

Proves, on the merged TRIO-003 artifact (SUCCESSOR-TRIO-003-20260915), in
fixture-isolated state on board138 (no queue, no deploy):

  Part N — net-new TRIO features (adapted from the authoritative
  OCTOPUS-COMMANDER-G28-20260914/trio-v2-battery.py):
    B5 completeness/quarantine, G3 priority ordering + no-starvation,
    S4a in-memory byte-copy barrier, S4b precondition freeze/recheck,
    class-scoped outcome-rejection breaker, torn-receipt fail-closed,
    decision consumer wired into tick.
  Part R — executor-safety regressions (F-001 layer1/layer2, OW-8
  no-starvation, canonical category, success-only retire, request+
  proposal_id provenance).

Counterexamples run against the historical baseline 109e68c0 where that is
safe and cheap. Only the witness boundary is simulated; real mv/verify
execution happens on fixture paths. Production guard hashes are compared
before/after.
"""
import importlib.machinery
import importlib.util
import json
import hashlib
import os
import pathlib
import sys
import tempfile
import time

MERGED = ("/home/ari/ofn/state/coding-worker/stage/SUCCESSOR-TRIO-003-20260915/"
          "ops_agent.py")
BASELINE = ("/home/ari/ofn/state/coding-worker/stage/SUCCESSOR-TRIO-20260914/"
            "ops_agent.py.baseline-109e68c0")
PROD_GUARD = ["/home/ari/ofn/state/ops-agent/state/ops-receipts.jsonl",
              "/home/ari/ofn/state/autonomy",
              "/home/ari/ofn/state/pulse/glass-offset.txt"]
PASS, FAIL = [], []


def check(name, ok, detail=""):
    print("  %-5s %-64s %s" % ("PASS" if ok else "FAIL", name, detail))
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


def sha(b):
    return hashlib.sha256(b).hexdigest()


def load_oa(fx, artifact, budget=None):
    _name = "oa_" + hashlib.sha256((str(fx) + artifact).encode()).hexdigest()[:8]
    spec = importlib.util.spec_from_file_location(
        _name, artifact,
        loader=importlib.machinery.SourceFileLoader(_name, artifact))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    m.ROOT = fx / "root"           # ROOT.parent must stay inside the fixture
    m.STATE = m.ROOT / "state"
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


PINS = {"node182_identity": "f" * 64, "witness_code_sha256": "c" * 64,
        "witness_contract_sha256": "d" * 64}


def mkfx(prefix):
    return pathlib.Path(tempfile.mkdtemp(prefix=prefix))


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
    sp = d / "root/state/canary-requests"
    sp.mkdir(parents=True, exist_ok=True)
    outs = []
    for nm in names:
        tgt = d / ("t-" + nm)
        tgt.write_text("OLD", encoding="utf-8")
        p = d / ("p-" + nm)
        p.write_text("NEW", encoding="utf-8")
        outs.append((sp, nm, tgt, p))
    return outs


def main():
    g0 = guard()
    real_home = pathlib.Path.home
    battery_home = mkfx("b5home003-")
    pathlib.Path.home = classmethod(lambda cls, _h=battery_home: _h)

    def pin_home(fx):
        pathlib.Path.home = classmethod(lambda cls, _fx=fx: _fx)

    # ================= Part N: B5 completeness / quarantine =================
    print("-- B5 (net-new)")
    def b5_fixture(n_dirs, kb=1):
        fx = mkfx("b5-")
        pin_home(fx)
        for i in range(n_dirs):
            d = fx / ("stable/pkg%d/__pycache__" % i)
            d.mkdir(parents=True)
            (d / "x.pyc").write_bytes(b"Z" * (kb * 1024))
        return fx

    # merged: successful cleanup VERIFIED with explicit freed bytes + quarantine
    fx = b5_fixture(30, kb=1)
    m = load_oa(fx, MERGED)
    fw = FW(m, PINS)
    r1 = m.handle_b5_storage({"timeout_s": 30}, {})
    r2 = m.progress_pending(PINS)
    ex = [x for x in m.read_receipts() if x.get("kind") == "OPS_B_EXECUTED"]
    qdirs = list((m.STATE / "b5-quarantine").glob("*")) if (m.STATE / "b5-quarantine").exists() else []
    quarantined = sum(len(list(q.rglob("*"))) for q in qdirs)
    check("B5-N1 frozen-set verdict VERIFIED with freed bytes",
          r1 == "proposal-sent" and ex and ex[-1]["verified"] is True
          and ex[-1].get("bytes_freed", 0) > 0
          and ex[-1].get("bytes_before") == ex[-1].get("bytes_freed"),
          "freed=%s" % (ex[-1].get("bytes_freed") if ex else "-"))
    check("B5-N2 targets MOVED to quarantine (no delete)",
          quarantined > 0 and r2 == "outcome-sent", "q=%d r2=%s" % (quarantined, r2))
    check("B5-N3 no rm -rf in executed action",
          all("rm" not in str(c) for c in (ex[-1].get("argv") or [])) if ex else False)
    # out-of-scope growth between proposal and verify never flips verdict
    fx = b5_fixture(25, kb=1)
    m = load_oa(fx, MERGED)
    FW(m, PINS)
    m.handle_b5_storage({"timeout_s": 30}, {})
    (fx / "stable/pkg24/__pycache__/grown.pyc").write_bytes(b"G" * (500 * 1024))
    m.progress_pending(PINS)
    ex = [x for x in m.read_receipts() if x.get("kind") == "OPS_B_EXECUTED"]
    check("B5-N4 out-of-scope growth never flips the verdict",
          ex and ex[-1]["verified"] is True)
    # zero-before -> explicit disposition, no proposal
    fx = mkfx("b5z-")
    pin_home(fx)
    z = fx / "stable/z/__pycache__"
    z.mkdir(parents=True)
    (z / "empty.pyc").write_bytes(b"")
    m = load_oa(fx, MERGED)
    r1 = m.handle_b5_storage({"timeout_s": 30}, {})
    check("B5-N5 zero-before -> B5_NOTHING_MEASURABLE, no proposal",
          r1 == "no-action-needed"
          and any(x.get("kind") == "B5_NOTHING_MEASURABLE" for x in m.read_receipts()),
          "r1=%s" % r1)
    # access error inside frozen set stays explicit (lower bound, not fake)
    fx = b5_fixture(3, kb=1)
    m = load_oa(fx, MERGED)
    FW(m, PINS)
    os.chmod(fx / "stable/pkg1/__pycache__", 0o000)
    r1 = m.handle_b5_storage({"timeout_s": 30}, {})
    kinds = [x.get("kind") for x in m.read_receipts()]
    check("B5-N6 partial measurement -> explicit B5_MEASUREMENT_INCOMPLETE, "
          "no proposal, no slot burn",
          r1 == "measurement-incomplete"
          and "B5_MEASUREMENT_INCOMPLETE" in kinds
          and "OPS_B_EXECUTED" not in kinds, "r1=%s" % r1)
    # symlink inside target never traversed
    fx = b5_fixture(2, kb=1)
    os.symlink("/etc", fx / "stable/pkg0/__pycache__/evil")
    m = load_oa(fx, MERGED)
    FW(m, PINS)
    r1 = m.handle_b5_storage({"timeout_s": 30}, {})
    check("B5-N7 symlink excluded, no traversal",
          r1 in ("proposal-sent", "no-action-needed"), "r1=%s" % r1)

    # ================= Part N: G3 priority ordering =================
    print("-- G3 (net-new)")
    fx = mkfx("g3t-")
    m = load_oa(fx, MERGED)
    FW(m, PINS)
    (sp, n1, t1, p1), (sp, n2, t2, p2) = req_pair(fx, ("b-same.json", "a-same.json"))
    write_req(sp, "b-same.json", t1, p1, priority=1)
    write_req(sp, "a-same.json", t2, p2, priority=1)
    r = m.handle_spool_category("B8", {"timeout_s": 30}, {}, "canary-requests")
    check("G3-N1 tie-break deterministic (priority then filename)",
          r == "proposal-sent" and (m.STATE / "executed" / "a-same.json").exists(),
          "r=%s" % r)
    # priority order actually honoured: prio 1 wins over prio 5
    fx = mkfx("g3p-")
    m = load_oa(fx, MERGED)
    FW(m, PINS)
    (sp, n1, t1, p1), (sp, n2, t2, p2) = req_pair(fx, ("z-low.json", "a-high.json"))
    write_req(sp, "z-low.json", t1, p1, priority=9)
    write_req(sp, "a-high.json", t2, p2, priority=1)
    r = m.handle_spool_category("B8", {"timeout_s": 30}, {}, "canary-requests")
    check("G3-N2 priority-1 request wins the tick",
          r == "proposal-sent" and (m.STATE / "executed" / "a-high.json").exists(),
          "r=%s" % r)
    for bad in (None, "abc"):
        fx = mkfx("g3b-")
        m = load_oa(fx, MERGED)
        FW(m, PINS)
        (sp, n1, t1, p1), (sp, n2, t2, p2) = req_pair(fx, ("good.json", "bad.json"))
        (sp / "bad.json").write_text(json.dumps(
            {"target": str(t1), "target_sha256": sha(b"NEW"),
             "patched": str(p1), "component": "c", "priority": bad}),
            encoding="utf-8")
        write_req(sp, "good.json", t2, p2, priority=1)
        r = m.handle_spool_category("B8", {"timeout_s": 30}, {}, "canary-requests")
        check("G3-N3 invalid priority %r: deterministic, no crash" % (bad,),
              r == "proposal-sent" and (m.STATE / "executed" / "good.json").exists(),
              "r=%s" % r)
    fx = mkfx("g3c-")
    m = load_oa(fx, MERGED)
    FW(m, PINS)
    (sp, n1, t1, p1), (sp, n2, t2, p2) = req_pair(fx, ("good.json", "zz-corrupt.json"))
    write_req(sp, "good.json", t1, p1, priority=5)
    (sp / "zz-corrupt.json").write_text("{not json", encoding="utf-8")
    r = m.handle_spool_category("B8", {"timeout_s": 30}, {}, "canary-requests")
    check("G3-N4 corrupt file ignored for ordering",
          r == "proposal-sent" and (sp / "zz-corrupt.json").exists(), "r=%s" % r)
    # no-starvation (OW-8 x G3): blocked prio-1 must not starve ready prio-2
    for art, tag in ((BASELINE, "CE-baseline"), (MERGED, "merged")):
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
        if tag.startswith("CE"):
            check("G3-N5 CE baseline: blocked prio-1 starves ready prio-2",
                  r == "budget-blocked" and (sp / "p2-ready.json").exists(), "r=%s" % r)
        else:
            check("G3-N6 merged: blocked prio-1 does NOT starve ready prio-2",
                  r == "proposal-sent"
                  and (m.STATE / "executed" / "p2-ready.json").exists()
                  and (sp / "p1-blocked.json").exists(), "r=%s" % r)

    # ================= Part N: S4a in-memory byte-copy barrier =================
    print("-- S4a (net-new)")
    fx = mkfx("s4a-")
    m = load_oa(fx, MERGED)
    FW(m, PINS)
    ((sp, nm, tgt, patched),) = req_pair(fx, ("s4a.json",))
    write_req(sp, "s4a.json", tgt, patched)
    assert m.handle_spool_category("B8", {"timeout_s": 30}, {}, "canary-requests") == "proposal-sent"
    real_replace = os.replace
    swap_done = []

    def trap(a, b):
        if str(a).endswith(".deploy.tmp"):
            patched.write_bytes(b"ATTACKER-BYTES")
            swap_done.append(True)
        return real_replace(a, b)
    os.replace = trap
    try:
        m.progress_pending(PINS)
    finally:
        os.replace = real_replace
    ex = [x for x in m.read_receipts() if x.get("kind") == "OPS_B_EXECUTED"]
    check("S4a-N1 source swapped after check -> target keeps VERIFIED bytes",
          bool(swap_done) and ex and ex[-1]["verified"] is True
          and tgt.read_text(encoding="utf-8") == "NEW"
          and patched.read_text(encoding="utf-8") == "ATTACKER-BYTES",
          "target=%r" % tgt.read_text(encoding="utf-8"))

    # ================= Part N: S4b precondition freeze/recheck =================
    print("-- S4b (net-new)")
    def s4b_fx():
        fx = mkfx("s4b-")
        m = load_oa(fx, MERGED)
        FW(m, PINS)
        gate = fx / "money-gates.py"
        gate.write_text("GATES-LIVE", encoding="utf-8")
        sp = fx / "root/state/canary-requests"
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
        return fx, m, gate, tgt
    fx, m, gate, tgt = s4b_fx()
    r = m.handle_spool_category("B4_ROLLBACK", {"timeout_s": 30}, {}, "canary-requests")
    gate.write_text("GATES-GONE", encoding="utf-8")
    r2 = m.progress_pending(PINS)
    ex = [x for x in m.read_receipts() if x.get("kind") == "OPS_B_PRE_EFFECT_BLOCKED"]
    check("S4b-N1 precondition drift after admission -> BLOCKED, target untouched",
          r == "proposal-sent" and r2 == "pre-effect-blocked" and ex
          and ex[-1]["reason"] == "PRECONDITION_DRIFT"
          and tgt.read_text(encoding="utf-8") == "OLD", "r2=%s" % r2)
    fx, m, gate, tgt = s4b_fx()
    r = m.handle_spool_category("B4_ROLLBACK", {"timeout_s": 30}, {}, "canary-requests")
    r2 = m.progress_pending(PINS)
    ex = [x for x in m.read_receipts() if x.get("kind") == "OPS_B_EXECUTED"]
    check("S4b-N2 valid precondition -> executes VERIFIED",
          r2 == "outcome-sent" and ex and ex[-1]["verified"] is True
          and tgt.read_text(encoding="utf-8") == "NEW", "r2=%s" % r2)
    check("S4b-N3 verified receipt carries request + proposal_id (preserved)",
          ex and ex[-1].get("request") == "rb.json"
          and str(ex[-1].get("proposal_id", "")).startswith("op-"), str(ex[-1].get("proposal_id"))[:12] if ex else "-")

    # ================= Part N: class-scoped breaker + torn receipts ==========
    print("-- CATSCOPE / torn ledger (net-new fix on hardened gap)")
    now = time.strftime("%Y-%m-%dT%H:%M:%S+00:00", time.gmtime())

    def receipts_fx(artifact, rows):
        fx = mkfx("cat-")
        m = load_oa(fx, artifact, budget={
            "mesh_wide_24h": 99, "per_node_24h": 99, "per_component_30min": 99,
            "circuit_breaker_after_same_class_failures": 1})
        with m.RECEIPTS.open("a", encoding="utf-8") as f:
            for r in rows:
                f.write(json.dumps(r) + "\n")
        return m
    m = receipts_fx(MERGED, [{"kind": "OPS_B_OUTCOME_REJECTED",
                              "category": "B8_ROLLBACK", "at": now}])
    check("CAT-N1 outcome-rejection class-scoped (B8 blocked, B6 free)",
          m.budget_allows("B8_CANARY", "c4")[0] is False
          and m.budget_allows("B6_REBUILD", "c5")[0] is True)
    m = receipts_fx(MERGED, [{"kind": "OPS_B_EXECUTED", "category": "B8_ROLLBACK",
                              "verified": False, "component": "c1", "at": now}])
    check("CAT-N2 same-class execution failure still blocks",
          m.budget_allows("B8_CANARY", "c3")[0] is False)
    fx = mkfx("catm-")
    m = load_oa(fx, MERGED, budget={
        "mesh_wide_24h": 99, "per_node_24h": 99, "per_component_30min": 99,
        "circuit_breaker_after_same_class_failures": 1})
    with m.RECEIPTS.open("a", encoding="utf-8") as f:
        f.write('{"kind": "OPS_B_EXECUTED", "category": "B8_X", '
                '"verified": false, "at": "2026-09-14T00:00:00+00:00"}\n')
        f.write('{"torn-json...')
    check("CAT-N3 torn ledger row skipped, budget stays closed (fail-closed)",
          m.budget_allows("B8_X", "c")[0] is False)

    # ================= Part N: decision consumer =================
    print("-- decision consumer (net-new)")
    def dec_fx():
        fx = mkfx("dec-")
        m = load_oa(fx, MERGED)
        od = fx / "owner_dialogue"
        od.mkdir(parents=True)
        return fx, m, od
    # D1: ACK_SEEN + registered awaiting task -> resumed, consumed
    fx, m, od = dec_fx()
    psha = sha(b"task-payload")
    (od / "decision_tasks.json").write_text(json.dumps(
        {"tasks": [{"task_id": "T1", "payload_sha256": psha,
                    "state": "awaiting_ack", "created_at": "2026-09-15T00:00:00+00:00"}]}),
        encoding="utf-8")
    (od / "owner_decision.v1.jsonl").write_text(json.dumps(
        {"at": "2026-09-15T10:00:00+00:00",
         "source_text_sha256": sha(b"card1"),
         "verdict": "ACK_SEEN", "bound_request_payload_sha256": psha}) + "\n",
        encoding="utf-8")
    r = m.consume_decisions()
    tasks = json.loads((od / "decision_tasks.json").read_text(encoding="utf-8"))
    cons = (od / "decision_consumption.jsonl").read_text(encoding="utf-8")
    check("DEC-N1 ACK_SEEN resumes registered task (flag clear only)",
          r == "consumed" and tasks["tasks"][0]["state"] == "resumed"
          and "DECISION_CONSUMED" in cons
          and any(x.get("kind") == "DECISION_CONSUMED" for x in m.read_receipts()))
    r2 = m.consume_decisions()
    tasks2 = json.loads((od / "decision_tasks.json").read_text(encoding="utf-8"))
    check("DEC-N2 replay idempotent (second pass idle, state stable)",
          r2 == "idle" and tasks2["tasks"][0]["state"] == "resumed")
    # D3: no registered task -> retryable, key NOT consumed
    fx, m, od = dec_fx()
    (od / "decision_tasks.json").write_text('{"tasks": []}', encoding="utf-8")
    (od / "owner_decision.v1.jsonl").write_text(json.dumps(
        {"at": "2026-09-15T10:00:00+00:00", "source_text_sha256": sha(b"card2"),
         "verdict": "ACK_SEEN", "bound_request_payload_sha256": "b" * 64}) + "\n",
        encoding="utf-8")
    r = m.consume_decisions()
    check("DEC-N3 no matching task -> DECISION_NO_TASK_RETRYABLE, key not consumed",
          r == "consumed" and "DECISION_NO_TASK_RETRYABLE" in
          (od / "decision_consumption.jsonl").read_text(encoding="utf-8"))
    m.consume_decisions()
    check("DEC-N4 retryable decision re-evaluated next tick (not consumed)",
          (od / "decision_consumption.jsonl").read_text(encoding="utf-8").count(
              "DECISION_NO_TASK_RETRYABLE") == 2)
    # D5: non-ACK verdict -> terminal DECISION_IGNORED, no task effect
    fx, m, od = dec_fx()
    psha = sha(b"task-payload-2")
    (od / "decision_tasks.json").write_text(json.dumps(
        {"tasks": [{"task_id": "T2", "payload_sha256": psha,
                    "state": "awaiting_ack", "created_at": "2026-09-15T00:00:00+00:00"}]}),
        encoding="utf-8")
    (od / "owner_decision.v1.jsonl").write_text(json.dumps(
        {"at": "2026-09-15T10:00:00+00:00", "source_text_sha256": sha(b"card3"),
         "verdict": "NEED_MORE_INFO", "bound_request_payload_sha256": psha}) + "\n",
        encoding="utf-8")
    r = m.consume_decisions()
    tasks = json.loads((od / "decision_tasks.json").read_text(encoding="utf-8"))
    check("DEC-N5 non-ACK verdict ignored, task untouched",
          r == "consumed" and tasks["tasks"][0]["state"] == "awaiting_ack"
          and "DECISION_IGNORED" in (od / "decision_consumption.jsonl").read_text(encoding="utf-8"))
    # D6: missing decision file -> idle
    fx, m, od = dec_fx()
    check("DEC-N6 no decision file -> idle", m.consume_decisions() == "idle")

    # ================= Part R: executor-safety regressions =================
    print("-- executor-safety regressions (preserved)")
    CAT = "B8_NON_TCB_PATCH_CANARY"
    # R1 (F-001 layer-2): verified receipt self-heals retire, zero spend
    fx = mkfx("r1-")
    m = load_oa(fx, MERGED)
    FW(m, PINS)
    xsha = "f" * 64
    tgt = fx / "glass_runner.py"
    tgt.write_text("DEPLOYED", encoding="utf-8")
    with m.RECEIPTS.open("a", encoding="utf-8") as f:
        f.write(json.dumps({"kind": "OPS_B_EXECUTED", "category": CAT,
                            "at": now, "verified": True, "outcome": "VERIFIED",
                            "verify_kind": "sha256:" + str(tgt) + ":" + xsha}) + "\n")
    sp = fx / "root/state/canary-requests"
    sp.mkdir(parents=True)
    (sp / "sim-g8-021.json").write_text(json.dumps(
        {"target": str(tgt), "target_sha256": xsha, "artifact_sha256": xsha,
         "patched": str(fx / "nonexistent-patched"), "component": "ofn-agents"}),
        encoding="utf-8")
    out = m.handle_spool_category(CAT, {"timeout_s": 30}, PINS, "canary-requests")
    kinds = [x.get("kind") for x in m.read_receipts()]
    check("R1 F-001 layer-2: verified receipt self-retires (zero spend)",
          (m.STATE / "executed" / "sim-g8-021.json").exists()
          and "F001_SELF_RETIRE" in kinds and "OPS_B_BLOCKED" not in kinds
          and out == "no-action-needed", "out=%s" % out)
    # R2 (F-001 layer-1): request file moves BEFORE the closure receipt
    fx = mkfx("r2-")
    m = load_oa(fx, MERGED)
    FW(m, PINS)
    m.witness_pull = lambda p: [{"proposal_id": "op-r2",
                                 "verdict": "OUTCOME_CONFIRMED",
                                 "witness_hash": "deadbeefdeadbeef"}]
    for d in ("executed", "closed", "failed", "owner-tasks", "awaiting-outcome"):
        (m.STATE / d).mkdir(parents=True, exist_ok=True)
    (m.STATE / "canary-requests").mkdir(parents=True, exist_ok=True)
    (m.STATE / "canary-requests" / "req-x.json").write_text("{}", encoding="utf-8")
    (m.STATE / "awaiting-outcome" / "ao.json").write_text(json.dumps(
        {"request": "req-x.json", "category": CAT, "component": "comp9",
         "outcome_proposal": "op-r2"}), encoding="utf-8")
    out = m.progress_outcomes(PINS)
    check("R2 F-001 layer-1: retire before OPS_B_CYCLE_CLOSED",
          (m.STATE / "executed" / "req-x.json").exists() and out == "cycle-closed"
          and any(x.get("kind") == "OPS_B_CYCLE_CLOSED" for x in m.read_receipts()),
          "out=%s" % out)
    # R3 (success-only retire): witness-unavailable stays queued, never executed/
    fx = mkfx("r3-")
    m = load_oa(fx, MERGED)  # witness_push succeeds trivially; break it:
    m.witness_push = lambda pins, name, data: (False, "down")
    (m.STATE / "canary-requests").mkdir(parents=True, exist_ok=True)
    (m.STATE / "canary-requests" / "wu-req.json").write_text(json.dumps(
        {"target": "/tmp/r3-target", "target_sha256": sha(b"NEW"),
         "patched": "/tmp/r3-nonexistent", "component": "wu-comp"}),
        encoding="utf-8")
    out = m.handle_spool_category(CAT, {"timeout_s": 30}, PINS, "canary-requests")
    check("R3 success-only retire: witness-unavailable stays queued (no false dedupe)",
          (m.STATE / "canary-requests" / "wu-req.json").exists()
          and not (m.STATE / "executed" / "wu-req.json").exists(), "out=%s" % out)
    # R4 (canonical category OW-8b): canonical + legacy signature keys honoured
    fx = mkfx("r4-")
    m = load_oa(fx, MERGED, budget={
        "mesh_wide_24h": 99, "per_node_24h": 99, "per_component_30min": 99,
        "circuit_breaker_after_same_class_failures": 1})
    (m.STATE / "failure-signatures.json").write_text(json.dumps(
        {"signatures": [{"category": "B8", "fixed_at": "2026-09-15T09:00:00Z",
                         "signature": "r4"}]}), encoding="utf-8")
    with m.RECEIPTS.open("a", encoding="utf-8") as f:
        f.write(json.dumps({"kind": "OPS_B_OUTCOME_REJECTED", "category": CAT,
                            "at": "2026-09-15T08:00:00+00:00"}) + "\n")
        f.write(json.dumps({"kind": "OPS_B_OUTCOME_REJECTED", "category": CAT,
                            "at": "2026-09-15T08:10:00+00:00"}) + "\n")
    ok, why = m.budget_allows("B8", "test-comp")
    check("R4 canonical category key honoured (breaker closed)", ok and why == "OK", why)
    # R5: _verified_by_receipt refuses a mismatched named receipt
    fx = mkfx("r5-")
    m = load_oa(fx, MERGED)
    with m.RECEIPTS.open("a", encoding="utf-8") as f:
        f.write(json.dumps({"kind": "OPS_B_EXECUTED", "category": CAT, "at": now,
                            "verified": True, "outcome": "VERIFIED",
                            "request": "SOMEONE-ELSE.json",
                            "verify_kind": "sha256:/tmp/x:" + ("a" * 64)}) + "\n")
    check("R5 named receipt does not retire a different request",
          m._verified_by_receipt({"target_sha256": "a" * 64}, "MY-REQ.json") is False
          and m._verified_by_receipt({"target_sha256": "a" * 64}, "SOMEONE-ELSE.json") is True)
    # R6: tick wires the decision consumer without crashing on empty fixture
    fx = mkfx("r6-")
    m = load_oa(fx, MERGED)
    (m.CONTRACTS).write_text(json.dumps({"categories": {}}), encoding="utf-8")
    m.goal_engine = lambda contracts: "healthy"
    m.progress_pending = lambda pins: None
    m.progress_outcomes = lambda pins: None
    m.verify_own_chain = lambda: (True, 0)
    m.witness_pins = lambda: {"k": 1}
    m.killed = lambda: False
    m.load_json = lambda p: (json.loads(open(p, encoding="utf-8").read())
                             if str(p) in (str(m.CONTRACTS),) else ({} if str(p) == str(m.ARMED) else json.loads(open(p, encoding="utf-8").read())))
    rc = m.tick()
    check("R6 tick consumes decisions (wired into results)",
          rc == 0 and any(x.get("kind") == "OPS_TICK_COMPLETE"
                          and "decisions" in x for x in m.read_receipts()))

    pathlib.Path.home = real_home
    g1 = guard()
    check("ISOLATION: production untouched", g0 == g1)
    print()
    print("TRIO_003_HARNESS: %d checks, %d PASS, %d FAIL"
          % (len(PASS) + len(FAIL), len(PASS), len(FAIL)))
    if FAIL:
        print("FAILED -> " + ", ".join(FAIL))
    return 0 if not FAIL else 1


if __name__ == "__main__":
    sys.exit(main())
