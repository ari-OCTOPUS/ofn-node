"""TRIO v2 (owner mission ROUND30, 2026-09-14): all executor changes of this
round land on the STAGED successor so live bytes (109e68c0) and every existing
pin stay untouched.

Fixes:
 B5  same-scope measurement (frozen target set, ONE counting rule both sides,
     explicit freed/access-error numbers, zero-before = no proposal) +
     quarantine-mv instead of rm -rf (AGENTS.md-aligned: stale -> archive)
 G3  no-starvation (budget-block records + continues; first admissible wins
     the tick) + safe priority parse (missing/null/invalid -> deterministic 100)
 CAT malformed ledger row no longer kills the tick (read_receipts tolerant,
     fail-closed for budgets); class scoping already via _cat_key (v1)
 S4a checked-bytes == consumed-bytes: the executor performs the B8 copy itself
     from the bytes READ at check time (path swap after check cannot alter the
     target); frozen argv stays the recorded contract
 S4b preconditions frozen into the action record at admission and re-checked
     at pre-effect (PRECONDITION_DRIFT blocks before any restore)
"""
import ast
import hashlib
import pathlib
import shutil
import sys

P = pathlib.Path("/home/ari/ofn/state/coding-worker/stage/SUCCESSOR-TRIO-20260914/ops_agent.py")
PRE = P.parent / "ops_agent.py.trio-v1-d0b86a35"
E = []


def edit(a, b):
    E.append((a, b))


# 1) tolerant read_receipts
edit('''def read_receipts() -> list:
    if not RECEIPTS.exists():
        return []
    return [json.loads(l) for l in RECEIPTS.read_text(encoding="utf-8").splitlines() if l.strip()]''',
     '''def read_receipts() -> list:
    if not RECEIPTS.exists():
        return []
    out = []
    for l in RECEIPTS.read_text(encoding="utf-8").splitlines():
        if not l.strip():
            continue
        try:
            out.append(json.loads(l))
        except ValueError:
            # a torn/partial line must never kill the tick, and it can never
            # count as OPS_B_EXECUTED, so budgets stay closed (fail-closed).
            # Chain integrity stays strict in verify_own_chain().
            continue
    return out''')


# 2) B5 one-counting-rule helper before the handler
edit('def handle_b5_storage(cat: dict, pins: dict) -> str:',
     '''def _b5_measure(paths) -> tuple:
    """ONE counting rule for both sides of the B5 comparison: logical bytes of
    regular files under each FROZEN path. Symlinks excluded (no traversal);
    the SET itself is never re-enumerated from the filesystem."""
    total, errs = 0, 0
    for p in paths:
        try:
            _p = Path(p)
            if _p.is_symlink():
                continue
            if _p.is_file():
                total += _p.stat().st_size
            elif _p.is_dir():
                for x in _p.rglob("*"):
                    if x.is_file() and not x.is_symlink():
                        total += x.stat().st_size
        except OSError:
            errs += 1
    return total, errs


def handle_b5_storage(cat: dict, pins: dict) -> str:''')

# 3) B5 handler: frozen set + quarantine-mv + nothing-measurable skip
edit('''    action_spec = {"commands": [["rm", "-rf", str(f)] for f in findings[:20]],
                   "rollback": "caches regenerate (reproducible artifacts only)",
                   "timeout_s": cat["timeout_s"]}
    before_bytes = sum(f.stat().st_size if f.is_file() else
                       sum(x.stat().st_size for x in f.rglob("*") if x.is_file())
                       for f in findings[:20] if f.exists())
    evidence = {"paths": [str(f) for f in findings[:20]],
                "measured_bytes_before": before_bytes,
                "note": "whitelist-matched reproducible caches only; success = "
                        "measured byte recovery (REAL-WORK-BRIDGE s8), NOT path "
                        "absence (caches regenerate by design)"}
    targets = findings[:20]
    # NOTE (rebuild 2026-09-14): the historical delta set cache-bytes-freed only
    # on action_spec while the ACTION-RECORD still carried paths-absent, so the
    # executed verify never switched. Both are connected here.
    _vk = "cache-bytes-freed:%d" % before_bytes
    action_spec["verify_kind"] = _vk
    return _witnessed_action("B5_SAFE_STORAGE_MAINTENANCE", "storage-cache",
                             action_spec, evidence, pins,
                             {"argv": [["rm", "-rf", str(f)] for f in targets],
                              "verify_kind": _vk,
                              "timeout_s": 30})''',
     '''    targets = findings[:20]
    before_bytes, errs_before = _b5_measure(targets)
    if before_bytes <= 0:
        # explicit disposition: nothing measurable to free - proposing a
        # no-op action would only burn a class-B slot for a fake verdict
        receipt("B5_NOTHING_MEASURABLE", component="storage-cache",
                paths=len(targets), access_errors=errs_before)
        return "no-action-needed"
    # AGENTS.md alignment: no rm -rf. Stale material moves to a quarantine
    # (archive) dir; physical purge stays a separate owner-scoped decision.
    _qdir = STATE / "b5-quarantine" / now_iso().replace(":", "")
    action_spec = {"commands": [["mkdir", "-p", str(_qdir)]] +
                               [["mv", str(f), str(_qdir)] for f in targets],
                   "rollback": "mv back from the quarantine dir; caches are "
                               "reproducible artifacts only",
                   "timeout_s": cat["timeout_s"]}
    evidence = {"paths": [str(f) for f in targets],
                "measured_bytes_before": before_bytes,
                "access_errors_before": errs_before,
                "criterion": "logical byte reduction of the FROZEN target set, "
                             "one counting rule on both sides; quarantine frees "
                             "NO physical space (mv, not delete)"}
    _vk = "target-set-bytes:%d" % before_bytes
    action_spec["verify_kind"] = _vk
    return _witnessed_action("B5_SAFE_STORAGE_MAINTENANCE", "storage-cache",
                             action_spec, evidence, pins,
                             {"argv": action_spec["commands"],
                              "verify_kind": _vk,
                              "timeout_s": 30,
                              "target_set": [str(f) for f in targets],
                              "access_errors_before": errs_before})''')

# 4) B5 verify branch: same frozen set, same rule, explicit numbers
edit('''        elif vk.startswith("cache-bytes-freed:"):
            # REAL-WORK-BRIDGE s8: storage success = MEASURED recovery.
            # Path absence is unfalsifiable for regenerating caches.
            import fnmatch as _fm
            want = int(vk.split(":", 1)[1] or 0)
            after = 0
            for _root in [STABLE_ROOT] + list(Path.home().glob("wt-*")):
                if not _root.exists():
                    continue
                for _dp, _dns, _fns in os.walk(_root):
                    for _d in _dns:
                        if _d in ("__pycache__", ".pytest_cache"):
                            after += sum(x.stat().st_size for x in
                                         (Path(_dp) / _d).rglob("*") if x.is_file())
                    for _f in _fns:
                        if _fm.fnmatch(_f, "*.pyc"):
                            try:
                                after += (Path(_dp) / _f).stat().st_size
                            except OSError:
                                pass
            verified = want > 0 and after < want''',
     '''        elif vk.startswith("target-set-bytes:"):
            # B5 same-scope criterion: logical bytes of the FROZEN target set
            # (from the action record), the SAME counting rule on both sides.
            # Changes OUTSIDE the frozen set never affect the verdict; the set
            # is never re-enumerated. Explicit numbers land in the receipt.
            want = int(vk.split(":", 1)[1] or 0)
            after, errs_after = _b5_measure(m.get("target_set") or [])
            _extra.update({"bytes_before": want, "bytes_after": after,
                           "bytes_freed": want - after,
                           "access_errors_after": errs_after})
            verified = want > 0 and (want - after) > 0''')

# 5) _extra init + receipt threading
edit('''    vk = m.get("verify_kind", "")
    verified = False
    if rc == 0:''',
     '''    vk = m.get("verify_kind", "")
    verified = False
    _extra = {}
    if rc == 0:''')
edit('''    return receipt("OPS_B_EXECUTED", category=category, component=m["component"],
                   argv=argvs, exit_codes=codes, verified=verified, outcome=outcome,
                   verify_kind=vk)''',
     '''    return receipt("OPS_B_EXECUTED", category=category, component=m["component"],
                   argv=argvs, exit_codes=codes, verified=verified, outcome=outcome,
                   verify_kind=vk, **_extra)''')

# 6) G3 no-starvation + end-of-loop signal
edit('''    (STATE / "owner-tasks").mkdir(parents=True, exist_ok=True)
    for name in _spool_order(spool):''',
     '''    (STATE / "owner-tasks").mkdir(parents=True, exist_ok=True)
    _any_blocked = False
    for name in _spool_order(spool):''')
edit('''        if not ok_b:
            receipt("OPS_B_BLOCKED", category=category, component=component, reason=why_b)
            return "budget-blocked"''',
     '''        if not ok_b:
            # G3: a budget-blocked request must not STARVE independent ready
            # requests behind it; record, skip, continue - the first
            # admissible request still wins the tick (one action per tick).
            receipt("OPS_B_BLOCKED", category=category, component=component,
                    reason=why_b)
            _any_blocked = True
            continue''')
edit('''        return _out
    return "no-action-needed"''',
     '''        return _out
    return "budget-blocked" if _any_blocked else "no-action-needed"''')

# 7) G3 safe priority parse
edit('''    def _key(_n):
        try:
            _row = load_json(_spool / _n) or {}
        except OSError:
            _row = {}
        return (int(_row.get("priority", 100)), _n)''',
     '''    def _key(_n):
        try:
            _row = load_json(_spool / _n) or {}
        except OSError:
            _row = {}
        try:
            _prio = int(_row.get("priority", 100))
        except (TypeError, ValueError):
            _prio = 100  # missing/null/invalid: deterministic, never a crash
        return (_prio, _n)''')

# 8) S4b freeze satisfied preconditions at admission
edit('''        if _unmet_pc:
            receipt("OPS_B_PRECONDITION_UNMET", category=category, request=name,
                    unmet=_unmet_pc[:3])
            continue''',
     '''        if _unmet_pc:
            receipt("OPS_B_PRECONDITION_UNMET", category=category, request=name,
                    unmet=_unmet_pc[:3])
            continue
        _preconds_verified = [{"path": str(_pc.get("path", "")),
                               "sha256": _pc.get("sha256")}
                              for _pc in _preconds]''')
edit('''                                  "deps_verified": _deps_verified})''',
     '''                                  "deps_verified": _deps_verified,
                                  "preconditions_verified": _preconds_verified})''')

# 9) S4b pre-effect re-check + S4a internal byte-copy
edit('''    for _dv in (m.get("deps_verified") or []):
        _dpt = Path(str(_dv.get("target", "")))
        _have_d = (hashlib.sha256(_dpt.read_bytes()).hexdigest()
                   if _dpt.exists() else None)
        if _have_d != _dv.get("sha256"):
            return receipt("OPS_B_PRE_EFFECT_BLOCKED", category=category,
                           component=m.get("component"), reason="DEPENDENCY_DRIFT",
                           dep=str(_dpt)[:80],
                           outcome="BLOCKED_NO_EFFECT", exit_codes=[])''',
     '''    for _dv in (m.get("deps_verified") or []):
        _dpt = Path(str(_dv.get("target", "")))
        _have_d = (hashlib.sha256(_dpt.read_bytes()).hexdigest()
                   if _dpt.exists() else None)
        if _have_d != _dv.get("sha256"):
            return receipt("OPS_B_PRE_EFFECT_BLOCKED", category=category,
                           component=m.get("component"), reason="DEPENDENCY_DRIFT",
                           dep=str(_dpt)[:80],
                           outcome="BLOCKED_NO_EFFECT", exit_codes=[])
    for _pv in (m.get("preconditions_verified") or []):
        _ppt = Path(str(_pv.get("path", "")))
        _have_pc2 = (hashlib.sha256(_ppt.read_bytes()).hexdigest()
                     if _ppt.exists() else None)
        if _have_pc2 != _pv.get("sha256"):
            return receipt("OPS_B_PRE_EFFECT_BLOCKED", category=category,
                           component=m.get("component"), reason="PRECONDITION_DRIFT",
                           path=str(_ppt)[:80],
                           outcome="BLOCKED_NO_EFFECT", exit_codes=[])
    _internal_copy = None
    if m.get("source_sha256") and m.get("target_path"):
        _internal_copy = (Path(str(m.get("source_path", ""))),
                          Path(str(m.get("target_path", ""))),
                          m["source_sha256"])''')

edit('''    raw = m.get("argv", [])
    argvs = raw if (raw and isinstance(raw[0], list)) else ([raw] if raw else [])
    codes = []
    for a in argvs:
        rc, out = run_frozen_action(a, m.get("timeout_s", 60))
        codes.append(rc)
    rc = max(codes) if codes else 1''',
     '''    raw = m.get("argv", [])
    argvs = raw if (raw and isinstance(raw[0], list)) else ([raw] if raw else [])
    codes = []
    if _internal_copy is not None:
        # S4a GAP CLOSURE: the bytes READ at check time are the bytes WRITTEN.
        # The executor performs the copy itself from memory, so a source swap
        # after the check cannot alter what lands on the target; the frozen
        # argv remains the recorded action contract.
        _srcp, _tgtp, _sha = _internal_copy
        try:
            _data = _srcp.read_bytes()
        except OSError as _e:
            return receipt("OPS_B_PRE_EFFECT_BLOCKED", category=category,
                           component=m.get("component"),
                           reason="SOURCE_UNREADABLE", error=type(_e).__name__,
                           outcome="BLOCKED_NO_EFFECT", exit_codes=[])
        if hashlib.sha256(_data).hexdigest() != _sha:
            return receipt("OPS_B_PRE_EFFECT_BLOCKED", category=category,
                           component=m.get("component"), reason="SOURCE_DRIFT",
                           outcome="BLOCKED_NO_EFFECT", exit_codes=[])
        _tmpw = _tgtp.with_name(_tgtp.name + ".deploy.tmp")
        with _tmpw.open("wb") as _f:
            _f.write(_data)
            _f.flush()
            os.fsync(_f.fileno())
        os.replace(_tmpw, _tgtp)
        codes = [0]
    else:
        for a in argvs:
            rc, out = run_frozen_action(a, m.get("timeout_s", 60))
            codes.append(rc)
    rc = max(codes) if codes else 1''')

raw = P.read_bytes()
old = raw.decode("utf-8")
if raw != old.encode("utf-8"):
    sys.exit("ABORT: round-trip mismatch")
if hashlib.sha256(raw).hexdigest().startswith("d0b86a35") is False:
    sys.exit("ABORT: stage file is not trio-v1 d0b86a35")
for i, (a, _) in enumerate(E):
    if old.count(a) != 1:
        sys.exit("ABORT: edit %d anchor count = %d" % (i, old.count(a)))
new = old
for a, b in E:
    new = new.replace(a, b)
ast.parse(new)
shutil.copy2(P, PRE)
P.write_bytes(new.encode("utf-8"))
print("trio-v1:", hashlib.sha256(PRE.read_bytes()).hexdigest()[:16])
print("trio-v2:", hashlib.sha256(P.read_bytes()).hexdigest()[:16])
