"""PRE-EFFECT integrity patch (owner mission J4, 2026-09-14).

Freezes CONTENT identity at proposal time (source bytes, target bytes, the
verified dependency state) into the frozen action-map record, re-checks all
three BEFORE any invocation in _execute_pending, and blocks with
OPS_B_PRE_EFFECT_BLOCKED (target untouched, pending -> failed/) on drift.
Also adds an enforced `preconditions` request field (list of {path, sha256}
pins checked at admission - until now the rollback containment condition was
prose with no consumer). Five anchored byte-exact edits; preimage kept."""
import ast
import hashlib
import pathlib
import shutil
import sys

P = pathlib.Path("/home/ari/ofn/state/ops-agent/ops_agent.py")
PRE = P.parent / "ops_agent.py.pre-preeffect-20260914"

EDITS = []

# 1) collect verified dep state in the G22 loop
EDITS.append((
    """        _deps = req.get("dependencies") or []
        if _deps:
            _unmet = []""",
    """        _deps = req.get("dependencies") or []
        _deps_verified = []
        if _deps:
            _unmet = []"""))

EDITS.append((
    """                if not _ok_dep:
                    _unmet.append(str(_dep)[:40])""",
    """                if _ok_dep:
                    _deps_verified.append({"target": _dt, "sha256": _dw})
                else:
                    _unmet.append(str(_dep)[:40])"""))

# 2) enforced preconditions (admission) - was prose-only in the rollback field
EDITS.append((
    """        if not backup or not Path(backup).exists():
            continue""",
    """        # owner-mission (j): preconditions are ENFORCED here (and stay
        # fail-closed: the request waits in the queue, re-checked every tick)
        _preconds = req.get("preconditions") or []
        _unmet_pc = []
        for _pc in _preconds:
            _pp = Path(str(_pc.get("path", "")))
            _have_pc = (hashlib.sha256(_pp.read_bytes()).hexdigest()
                        if _pp.exists() else None)
            if _have_pc != _pc.get("sha256"):
                _unmet_pc.append({"path": str(_pp)[:60],
                                  "want": str(_pc.get("sha256"))[:16],
                                  "have": (_have_pc or "absent")[:16]})
        if _unmet_pc:
            receipt("OPS_B_PRECONDITION_UNMET", category=category, request=name,
                    unmet=_unmet_pc[:3])
            continue
        if not backup or not Path(backup).exists():
            continue"""))

# 3) freeze content identity into the B8 action record
EDITS.append((
    """        _out = _witnessed_action(category, component, action_spec, evidence, pins,
                                 {"argv": [["cp", str(Path(backup)), target]],
                                  "verify_kind": "sha256:" + target + ":" + want,
                                  "timeout_s": 30})""",
    """        _tgt_p = Path(target)
        _out = _witnessed_action(category, component, action_spec, evidence, pins,
                                 {"argv": [["cp", str(Path(backup)), target]],
                                  "verify_kind": "sha256:" + target + ":" + want,
                                  "timeout_s": 30,
                                  # PRE-EFFECT freeze: argv pins PATHS, these pin
                                  # the CONTENT that was reviewed and approved
                                  "source_path": str(Path(backup)),
                                  "source_sha256": evidence["deploy_sha256"],
                                  "target_path": target,
                                  "pre_target_sha256":
                                      (hashlib.sha256(_tgt_p.read_bytes()).hexdigest()
                                       if _tgt_p.exists() else None),
                                  "deps_verified": _deps_verified})"""))

# 4) pre-effect gate in _execute_pending (before ANY invocation)
EDITS.append((
    """    m = load_json(STATE / "proposals" / "action-map" / (exp["proposal_id"] + ".json"))
    if not m:
        return receipt("OPS_B_EXECUTED", category=category,
                       component=exp["target_component"], verified=False,
                       outcome="NO_ACTION_MAP", exit_codes=[])""",
    """    m = load_json(STATE / "proposals" / "action-map" / (exp["proposal_id"] + ".json"))
    if not m:
        return receipt("OPS_B_EXECUTED", category=category,
                       component=exp["target_component"], verified=False,
                       outcome="NO_ACTION_MAP", exit_codes=[])
    # PRE-EFFECT integrity (owner mission J4): connect the reviewed bytes to the
    # executed bytes. Drift between approval and execution blocks BEFORE any
    # invocation; the target is never written with unreviewed bytes.
    if m.get("source_sha256"):
        _sp = Path(str(m.get("source_path", "")))
        _have_src = (hashlib.sha256(_sp.read_bytes()).hexdigest()
                     if _sp.exists() else None)
        if _have_src != m["source_sha256"]:
            return receipt("OPS_B_PRE_EFFECT_BLOCKED", category=category,
                           component=m.get("component"), reason="SOURCE_DRIFT",
                           source=str(_sp)[:80], want=m["source_sha256"][:16],
                           have=(_have_src or "absent")[:16],
                           outcome="BLOCKED_NO_EFFECT", exit_codes=[])
    if m.get("pre_target_sha256") is not None or "pre_target_sha256" in m:
        _tp = Path(str(m.get("target_path", "")))
        _have_t = (hashlib.sha256(_tp.read_bytes()).hexdigest()
                   if _tp.exists() else None)
        if _have_t != m.get("pre_target_sha256"):
            return receipt("OPS_B_PRE_EFFECT_BLOCKED", category=category,
                           component=m.get("component"), reason="TARGET_DRIFT",
                           target=str(_tp)[:80],
                           outcome="BLOCKED_NO_EFFECT", exit_codes=[])
    for _dv in (m.get("deps_verified") or []):
        _dpt = Path(str(_dv.get("target", "")))
        _have_d = (hashlib.sha256(_dpt.read_bytes()).hexdigest()
                   if _dpt.exists() else None)
        if _have_d != _dv.get("sha256"):
            return receipt("OPS_B_PRE_EFFECT_BLOCKED", category=category,
                           component=m.get("component"), reason="DEPENDENCY_DRIFT",
                           dep=str(_dpt)[:80],
                           outcome="BLOCKED_NO_EFFECT", exit_codes=[])"""))

# 5) blocked cycles fail closed without consuming the verdict
EDITS.append((
    """        result = _execute_pending(category, exp)
        consume_verdict(row, exp["proposal_id"], result.get("ops_hash"))""",
    """        result = _execute_pending(category, exp)
        if result.get("outcome") == "BLOCKED_NO_EFFECT":
            receipt("OPS_B_PRE_EFFECT_CYCLE_FAILED", category=category,
                    reason=result.get("reason"))
            os.replace(PENDING / name, STATE / "failed" / name)
            return "pre-effect-blocked"
        consume_verdict(row, exp["proposal_id"], result.get("ops_hash"))"""))

raw = P.read_bytes()
old = raw.decode("utf-8")
if raw != old.encode("utf-8"):
    sys.exit("ABORT: round-trip mismatch")
if "PRE_EFFECT_BLOCKED" in old:
    sys.exit("ABORT: already applied")
for i, (a, b) in enumerate(EDITS):
    if old.count(a) != 1:
        sys.exit("ABORT: edit %d anchor count = %d" % (i, old.count(a)))
new = old
for a, b in EDITS:
    new = new.replace(a, b)
ast.parse(new)
shutil.copy2(P, PRE)
P.write_bytes(new.encode("utf-8"))
print("preimage:", hashlib.sha256(PRE.read_bytes()).hexdigest()[:16])
print("patched :", hashlib.sha256(P.read_bytes()).hexdigest()[:16])
