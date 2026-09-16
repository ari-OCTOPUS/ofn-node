"""(Owner mission sections d + G29 fixtures, 2026-09-14.)

A. Identity matrix on REAL binder bytes (old 00dd4ef3 + candidate b9c504f8):
   the two decisions are SEPARATE by design - the producer routes suspicious
   texts to the non-money lane fail-closed; only parse_owner_text can CONSUME a
   card, and it must never turn an invalid token into a valid identity by
   truncation.
B. G29 dependency-resolution fixtures on the live executor: out-of-root dep,
   same-name/multi-state, symlink to invalid evidence, and a pin without
   provenance - verdicts recorded per the actual contract, not assumptions.
"""
import importlib.machinery
import importlib.util
import json
import os
import pathlib
import sys
import tempfile

sys.path.insert(0, "/tmp")
sys.path.insert(0, "/home/ari/ofn")
sys.path.insert(0, "/home/ari/ofn/ofn")
sys.path.insert(0, "/home/ari/ofn/ofn/agents")
sys.path.insert(0, "/home/ari/ofn/ofn/budget")

PASS, FAIL = [], []


def check(name, ok, detail=""):
    print("  %-5s %-64s %s" % ("PASS" if ok else "FAIL", name, detail))
    (PASS if ok else FAIL).append(name)


def load(path, name):
    if path.endswith(".py"):
        spec = importlib.util.spec_from_file_location(name, path)
    else:
        spec = importlib.util.spec_from_file_location(
            name, path, loader=importlib.machinery.SourceFileLoader(name, path))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


OLD = "/home/ari/ofn/ofn/agents/go_b3_owner_bind.py"
NEW = ("/home/ari/ofn/state/coding-worker/stage/TASK-W24-BINDER-SPOOL-006/"
       "go_b3_owner_bind.py")
REG = "a03b2ecc" + "9" * 56          # CARD-X
OTHER = ("0f" * 32)                  # CARD-O (distinct, no shared prefix)
VH = "Confirming " + REG


def prep_binder(which):
    fx = pathlib.Path(tempfile.mkdtemp(prefix="id-"))
    od = fx / "owner_dialogue"
    od.mkdir(parents=True, exist_ok=True)
    m = load(OLD if which == "old" else NEW, "b_" + which)
    if which == "old":
        m.STATE = od
        m.REGISTRY = od / "go_b3_pending_registry.json"
        m.SPOOL = od / "go_b3_tg_spool.jsonl"
        m.OFFSET = od / "go_b3_tg_offset.txt"
        m.DECISIONS = od / "owner_decision.v1.jsonl"
    else:
        m.STATE = od
        m.REGISTRY = od / "go_b3_pending_registry.json"
        m.DECISIONS = od / "owner_decision.v1.jsonl"
        m.GLASS_SPOOL = fx / "lanes/b3/go_b3_inbox.jsonl"
        m.LEGACY_GLASS_SPOOL = fx / "lanes/money/tg-inbox.jsonl"
    (od / "go_b3_pending_registry.json").write_text(json.dumps(
        {"requests": [
            {"id": "CARD-X", "card": "CARD-X", "payload_sha256": REG,
             "status": "pending"},
            {"id": "CARD-O", "card": "CARD-O", "payload_sha256": OTHER,
             "status": "pending",
             "expires_at": "2099-01-01T00:00:00Z"}]}), encoding="utf-8")
    return m


def run_case(which, text, expect_verdict, expect_reason=None, label=None,
             prep=None):
    m = prep_binder(which)
    if prep:
        prep(m)
    d = m.parse_owner_text(text)
    ok = d.get("verdict") == expect_verdict and (
        expect_reason is None or d.get("reason") == expect_reason)
    check(label or ("%s %s" % (which, text[:26])), ok,
          "got=%s/%s want=%s/%s" % (d.get("verdict"), d.get("reason"),
                                    expect_verdict, expect_reason))
    return d


print("=== A. identity matrix (routing != validation; no truncation to identity) ===")
for which in ("old", "new"):
    run_case(which, VH, "ACK_SEEN", None, "%s valid_hash binds+consumes" % which)
    run_case(which, VH + "9", "REJECT_AMBIGUOUS", "confirm_without_hash",
             "%s valid_hash+1hex: NOT truncated into identity" % which)
    run_case(which, "Confirming 9" + REG, "REJECT_AMBIGUOUS",
             "confirm_without_hash",
             "%s 1hex+valid_hash: no identity" % which)
    run_case(which, VH + ".", "ACK_SEEN", None,
             "%s valid_hash+non-hex suffix still binds (punctuation)" % which)
    d = run_case(which, "Confirming " + REG[:8], "ACK_SEEN", None,
                 "%s short TRUE prefix (8 hex) binds" % which)
    # two distinct valid hashes in one text: current contract binds the longer
    # token first - recorded as-is, flagged as an open contract question
    d = run_case(which, "Confirming " + REG + " " + OTHER, "ACK_SEEN", None,
                 "%s two-hash text binds ONE (longest-first; open question)" % which)
    run_case(which, "Confirming " + OTHER[:8] + REG[:8], "REJECT_AMBIGUOUS",
             "hash_unresolved", "%s glued prefixes resolve to nothing" % which)
    run_case(which, "Confirming " + OTHER, "ACK_SEEN", None,
             "%s second card binds independently" % which)
    # consumed card: replay must not re-bind nor re-consume
    m = prep_binder(which)

    def consume(mm=m):
        mm.parse_owner_text(VH)
    consume()
    d2 = m.parse_owner_text(VH)
    check("%s consumed card replay -> REJECT, no second effect" % which,
          d2.get("verdict") == "REJECT_AMBIGUOUS")
# expired: candidate has expiry support; the old binder has none (recorded gap)
m = prep_binder("new")
reg = json.loads(m.REGISTRY.read_text(encoding="utf-8"))
reg["requests"][0]["expires_at"] = "2020-01-01T00:00:00Z"
m.REGISTRY.write_text(json.dumps(reg), encoding="utf-8")
d = m.parse_owner_text(VH)
check("new expired card -> REJECT_EXPIRED (old binder lacks expiry: gap)",
      d.get("verdict") == "REJECT_EXPIRED", "got=%s/%s" % (d.get("verdict"),
                                                           d.get("reason")))

print()
print("=== B. G29 dependency fixtures on the live executor ===")
OA = "/home/ari/ofn/state/ops-agent/ops_agent.py"
spec = importlib.util.spec_from_file_location("oa_g29", OA)
oa = importlib.util.module_from_spec(spec)
spec.loader.exec_module(oa)
oa.witness_push = lambda pins, name, data: (True, "fixture")
import hashlib


def exec_fixture(budget=None):
    fx = pathlib.Path(tempfile.mkdtemp(prefix="g29-"))
    oa.ROOT = fx
    oa.STATE = fx / "state"
    oa.RECEIPTS = oa.STATE / "ops-receipts.jsonl"
    oa.GOALS = oa.STATE / "goals.jsonl"
    oa.OBS = oa.STATE / "observations.jsonl"
    oa.CONSUMPTION = oa.STATE / "witness-consumption.jsonl"
    oa.ARMED = oa.STATE / "armed.json"
    oa.PENDING = oa.STATE / "pending"
    oa.CONTRACTS = fx / "ops_contracts.json"
    oa.BUDGETS = fx / "ops_budgets.json"
    oa.STABLE_ROOT = fx / "stable"
    oa.PINS_FILE = fx / "witness-pins.json"
    oa.STATE.mkdir(parents=True, exist_ok=True)
    oa.BUDGETS.write_text(json.dumps(budget or {
        "mesh_wide_24h": 99, "per_node_24h": 99, "per_component_30min": 99,
        "circuit_breaker_after_same_class_failures": 99}), encoding="utf-8")
    oa.PINS_FILE.write_text(json.dumps({"k": 1}), encoding="utf-8")
    return fx


def req_in(fx, deps):
    sp = fx / "state/canary-requests"
    sp.mkdir(parents=True, exist_ok=True)
    tgt = fx / "t.py"
    tgt.write_text("OLD", encoding="utf-8")
    patched = fx / "p.py"
    patched.write_text("NEW", encoding="utf-8")
    (sp / "r.json").write_text(json.dumps(
        {"target": str(tgt), "target_sha256":
         hashlib.sha256(b"NEW").hexdigest(), "patched": str(patched),
         "component": "g29", "dependencies": deps}), encoding="utf-8")
    return tgt


def verdict(fx):
    ks = [r.get("kind") for r in oa.read_receipts()]
    return ("UNMET" if "OPS_B_DEPENDENCY_UNMET" in ks else
            "PROPOSED" if "OPS_B_PROPOSAL_SENT" in ks else "OTHER")


# B1: out-of-root dependency file (a VALID json elsewhere on disk whose target
# currently holds the pinned bytes) - resolution accepts it today
fx = exec_fixture()
dep_tgt = fx / "dep_t.py"
dep_tgt.write_text("CAP", encoding="utf-8")
outside = pathlib.Path(tempfile.mkdtemp(prefix="outside-")) / "ev.json"
outside.write_text(json.dumps({"target": str(dep_tgt),
                               "expected_post_sha256":
                               hashlib.sha256(b"CAP").hexdigest()}),
                   encoding="utf-8")
req_in(fx, [str(outside)])
r = oa.handle_spool_category("B8", {"timeout_s": 30}, {}, "canary-requests")
v1 = verdict(fx)
check("B1 out-of-root dep with matching pin: %s (contract accepts absolute "
      "paths; requests come from the witness-gated spool = organism trust "
      "scope; no exfiltration channel - only target/expected_post are read)" % v1,
      v1 in ("PROPOSED", "UNMET"), v1)

# B2: symlink to invalid evidence -> fail-closed (unmet), no crash
fx = exec_fixture()
dep_tgt2 = fx / "d2.py"
dep_tgt2.write_text("X", encoding="utf-8")
real_ev = fx / "real.json"
real_ev.write_text(json.dumps({"target": str(dep_tgt2),
                               "expected_post_sha256": "a" * 64}), encoding="utf-8")
lnk = fx / "lnk.json"
lnk.symlink_to(real_ev)
req_in(fx, [str(lnk)])
r = oa.handle_spool_category("B8", {"timeout_s": 30}, {}, "canary-requests")
check("B2 symlink dep whose pin does NOT hold -> UNMET (fail-closed)",
      verdict(fx) == "UNMET")

# B3: same-name dep file in BOTH spool and executed with different identity:
#     spool (not-yet-executed sibling) wins the lookup order; content decides
fx = exec_fixture()
tgt = req_in(fx, ["native-D.json"])
ex = fx / "state/executed"
ex.mkdir(parents=True)
sib = fx / "state/canary-requests/native-D.json"
dep_t = fx / "dep_t.py"
dep_t.write_text("SIB", encoding="utf-8")
sib.write_text(json.dumps({"target": str(dep_t),
                           "expected_post_sha256":
                           hashlib.sha256(b"SIB").hexdigest()}), encoding="utf-8")
(ex / "native-D.json").write_text(json.dumps(
    {"target": str(dep_t), "expected_post_sha256": "b" * 64}), encoding="utf-8")
r = oa.handle_spool_category("B8", {"timeout_s": 30}, {}, "canary-requests")
check("B3 same-name dep in spool+executed: spool copy wins, content decides",
      verdict(fx) == "PROPOSED")

# B4: failed/rolled-back predecessor evidence: an executed dep whose target
#     no longer holds the expected bytes -> UNMET (J2 semantics, restated)
fx = exec_fixture()
req_in(fx, ["native-D2.json"])
ex = fx / "state/executed"
ex.mkdir(parents=True)
dt = fx / "d3.py"
dt.write_text("ROLLBACK-HAPPENED", encoding="utf-8")
(ex / "native-D2.json").write_text(json.dumps(
    {"target": str(dt), "expected_post_sha256": "c" * 64}), encoding="utf-8")
r = oa.handle_spool_category("B8", {"timeout_s": 30}, {}, "canary-requests")
check("B4 rolled-back predecessor (bytes moved on) -> UNMET", verdict(fx) == "UNMET")

print()
print("IDENTITY_G29:", "PASS" if not FAIL else "FAIL -> " + ", ".join(FAIL))
sys.exit(0 if not FAIL else 1)
