"""TRIO v3 (ROUND31 sections 3+4): B5 measurement COMPLETENESS + the DECISION
CONSUMER wired into the existing ops-agent tick. Staged only; live untouched."""
import ast
import hashlib
import pathlib
import shutil
import sys

P = pathlib.Path("/home/ari/ofn/state/coding-worker/stage/"
                 "SUCCESSOR-TRIO-20260914/ops_agent.py")
PRE = P.parent / "ops_agent.py.trio-v2d-a85db3b0"
E = []


def edit(a, b):
    E.append((a, b))


edit('''def _b5_measure(paths) -> tuple:
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
    return total, errs''',
     '''def _b5_measure(paths) -> tuple:
    """ONE counting rule for both sides of the B5 comparison: logical bytes of
    regular files under each FROZEN path. Symlinks excluded (no traversal);
    the SET itself is never re-enumerated. Returns (total, errs, per_path) -
    unreadable bytes are UNKNOWN, not zero."""
    total, errs = 0, 0
    per = {}
    for p in paths:
        n, ok = 0, True
        try:
            _p = Path(p)
            if _p.is_symlink():
                per[str(p)] = {"bytes": 0, "visible": True, "symlink": True}
                continue
            if _p.is_file():
                n = _p.stat().st_size
            elif _p.is_dir():
                for x in _p.rglob("*"):
                    if x.is_file() and not x.is_symlink():
                        n += x.stat().st_size
            per[str(p)] = {"bytes": n, "visible": True}
        except OSError:
            ok = False
            errs += 1
            per[str(p)] = {"bytes": None, "visible": False}
        total += n if ok else 0
    return total, errs, per''')

edit('''    targets = findings[:20]
    before_bytes, errs_before = _b5_measure(targets)
    if before_bytes <= 0:''',
     '''    targets = findings[:20]
    before_bytes, errs_before, per_before = _b5_measure(targets)
    if errs_before:
        # a partially-measurable set cannot be verified honestly - no
        # proposal, no slot burn, no fake verdict
        receipt("B5_MEASUREMENT_INCOMPLETE", component="storage-cache",
                paths=len(targets), access_errors=errs_before, stage="before")
        return "measurement-incomplete"
    if before_bytes <= 0:''')

edit('''                              "target_set": [str(f) for f in targets],
                              "access_errors_before": errs_before})''',
     '''                              "target_set": [str(f) for f in targets],
                              "access_errors_before": errs_before,
                              "per_target_before": per_before,
                              "quarantine_dir": str(_qdir)})''')

edit('''        want = int(vk.split(":", 1)[1] or 0)
        after, errs_after = _b5_measure(m.get("target_set") or [])
        _extra.update({"bytes_before": want, "bytes_after": after,
                       "bytes_freed": want - after,
                       "access_errors_after": errs_after})
        verified = want > 0 and (want - after) > 0''',
     '''        want = int(vk.split(":", 1)[1] or 0)
        after, errs_after, per_after = _b5_measure(m.get("target_set") or [])
        qdir = m.get("quarantine_dir")
        moved, move_failed, invisible = [], [], []
        for i, p in enumerate(m.get("target_set") or []):
            a = per_after.get(str(p), {})
            if not a.get("visible", False):
                invisible.append(str(p)[-60:])
                continue
            qitem = (list(Path(qdir).glob("%03d-*" % i))
                     if qdir and Path(qdir).exists() else [])
            if qitem or not Path(p).exists():
                moved.append(str(p)[-60:])
            else:
                move_failed.append(str(p)[-60:])
        _extra.update({"bytes_before": want, "bytes_after": after,
                       "bytes_freed": want - after,
                       "access_errors_after": errs_after,
                       "targets_moved": len(moved),
                       "targets_move_failed": len(move_failed),
                       "targets_unreadable_after": len(invisible),
                       "measurement_complete": errs_after == 0})
        if errs_after:
            # unreadable after-bytes are UNKNOWN, not zero - a read error can
            # never masquerade as freed bytes; freed stays a LOWER BOUND
            _extra["outcome_detail"] = ("MEASUREMENT_INCOMPLETE: freed %d "
                                        "is a LOWER BOUND only" % (want - after))
            verified = False
        else:
            verified = want > 0 and (want - after) > 0''')

CONSUMER = '''# ------------------------------------------------- decision consumer (Class A)
def _record_decision(cons_path, key, kind, **kw):
    row = {"schema": "octopus.decision-consumption.v1", "key": key,
           "kind": kind, "at": now_iso(), **kw}
    with cons_path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(row, sort_keys=True) + "\\n")


def consume_decisions() -> str:
    """The owner chain's FINAL edge: owner_decision.v1.jsonl -> task resume.
    Contract: ACK_SEEN means the owner SAW the card - it clears an
    awaiting-owner flag and NOTHING else (no approvals, no effects, no
    money). Tasks come ONLY from the trusted decision_tasks.json registry
    (never from message text); identity is an EXACT payload-hash match (no
    prefix truncation); replay/restart are idempotent via task state; the
    crash boundary is task-state-first, receipt-second."""
    od = ROOT.parent / "owner_dialogue"
    dec_path = od / "owner_decision.v1.jsonl"
    tasks_path = od / "decision_tasks.json"
    cons_path = od / "decision_consumption.jsonl"
    if not dec_path.exists():
        return "idle"
    consumed = set()
    if cons_path.exists():
        for l in cons_path.read_text(encoding="utf-8").splitlines():
            try:
                consumed.add(json.loads(l).get("key"))
            except ValueError:
                continue
    tasks = load_json(tasks_path) or {"tasks": []}
    n = 0
    for l in dec_path.read_text(encoding="utf-8").splitlines():
        if not l.strip():
            continue
        try:
            d = json.loads(l)
        except ValueError:
            receipt("DECISION_ROW_UNPARSEABLE", detail=l[:60])
            continue
        key = "%s|%s" % (d.get("at"), d.get("source_text_sha256"))
        if not d.get("source_text_sha256") or key in consumed:
            continue
        bound = d.get("bound_request_payload_sha256")
        verdict = str(d.get("verdict", ""))
        task = next((t for t in tasks["tasks"]
                     if t.get("payload_sha256") == bound), None)
        if verdict not in ("ACK_SEEN", "ACK_BATCH"):
            _record_decision(cons_path, key, "DECISION_IGNORED",
                             verdict=verdict[:24],
                             task=task and task.get("task_id"))
        elif task is None:
            # the CARD was already consumed by the binder; no registered task
            # means nothing to resume - cards are NEVER re-pended
            _record_decision(cons_path, key, "DECISION_NO_TASK",
                             bound=str(bound)[:16])
        elif task.get("state") != "awaiting_ack":
            _record_decision(cons_path, key, "DECISION_TASK_NOT_WAITING",
                             task=task.get("task_id"), state=task.get("state"))
        elif str(d.get("at", "")) < str(task.get("created_at", "")):
            _record_decision(cons_path, key, "DECISION_STALE",
                             task=task.get("task_id"),
                             decision_at=d.get("at"),
                             task_created=task.get("created_at"))
        else:
            # resume = the ONE allowed internal action: clear the awaiting
            # flag. Task-state write FIRST (crash boundary), receipt second;
            # replay after a crash lands in TASK_NOT_WAITING, idempotent.
            task["state"] = "resumed"
            task["resumed_at"] = now_iso()
            task["resumed_by_decision"] = key
            _tmp = tasks_path.with_suffix(".tmp")
            _tmp.write_text(json.dumps(tasks, indent=1, sort_keys=True) + "\\n",
                            encoding="utf-8")
            os.replace(_tmp, tasks_path)
            _record_decision(cons_path, key, "DECISION_CONSUMED",
                             task=task.get("task_id"), bound=str(bound)[:16])
            receipt("DECISION_CONSUMED", task=task.get("task_id"),
                    verdict=verdict, note="awaiting flag cleared only")
        n += 1
    return "consumed" if n else "idle"


# ---------------------------------------------------------------- goal engine (Class A)'''

edit("# ---------------------------------------------------------------- goal engine (Class A)",
     CONSUMER)

edit('''    # Class A goal engine every tick
    ge = goal_engine(contracts)''',
     '''    # Class A goal engine every tick
    ge = goal_engine(contracts)
    # owner chain final edge: decisions -> task resume (ACK clears a flag only)
    results = {"decisions": consume_decisions()}''')

raw = P.read_bytes()
old = raw.decode("utf-8")
if raw != old.encode("utf-8"):
    sys.exit("roundtrip")
if hashlib.sha256(raw).hexdigest()[:8] != "a85db3b0":
    sys.exit("not v2d")
for i, (a, _) in enumerate(E):
    if old.count(a) != 1:
        sys.exit("edit %d anchor=%d" % (i, old.count(a)))
new = old
for a, b in E:
    new = new.replace(a, b)
ast.parse(new)
shutil.copy2(P, PRE)
P.write_bytes(new.encode("utf-8"))
print("v2d preimage:", hashlib.sha256(PRE.read_bytes()).hexdigest()[:16])
print("v3          :", hashlib.sha256(P.read_bytes()).hexdigest()[:16])
