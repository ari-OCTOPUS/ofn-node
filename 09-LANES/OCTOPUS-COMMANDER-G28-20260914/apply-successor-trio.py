"""SUCCESSOR-TRIO rebuild (owner mission هـ): B5 measured-recovery + CATSCOPE
budget scoping + G3 priority ordering, applied as one combined successor onto
the LIVE executor baseline 109e68c0 (all current protections preserved: B8
prefer-patched, base-verify, G22 evidence deps, G28 dedupe, TCB gate, G29
resolution, PRE-EFFECT integrity, enforced preconditions). Byte-exact anchors;
preimage kept; staged only (deploy behind quota, AFTER G8/W24/G30-wiring)."""
import ast
import hashlib
import pathlib
import shutil
import sys

P = pathlib.Path("/home/ari/ofn/state/ops-agent/ops_agent.py")
STAGE = pathlib.Path("/home/ari/ofn/state/coding-worker/stage/SUCCESSOR-TRIO-20260914")

EDITS = []

# --- CATSCOPE: budget category scoping by token, not suffix
EDITS.append((
    "def budget_allows(category: str, component: str, now: float | None = None) -> tuple:",
    "def _cat_key(category: str) -> str:\n"
    "    return category.split('_')[0]\n"
    "\n"
    "\n"
    "def budget_allows(category: str, component: str, now: float | None = None) -> tuple:"))
EDITS.append((
    "    fails = [r for r in ex if r.get(\"category\") == category and r.get(\"verified\") is False]",
    "    fails = [r for r in ex if _cat_key(r.get(\"category\", \"\")) == _cat_key(category)\n"
    "             and r.get(\"verified\") is False]"))
EDITS.append((
    "    orej = [r for r in rows if r.get(\"kind\") == \"OPS_B_OUTCOME_REJECTED\"\n"
    "            and category[-2:] in str(r.get(\"category\", \"\"))]",
    "    orej = [r for r in rows if r.get(\"kind\") == \"OPS_B_OUTCOME_REJECTED\"\n"
    "            and _cat_key(r.get(\"category\", \"\")) == _cat_key(category)]"))
EDITS.append((
    "        ok_b, why_b = budget_allows(category[-2:], component)",
    "        ok_b, why_b = budget_allows(_cat_key(category), component)"))

# --- G3: priority honored over filename (module-level helper + call site)
EDITS.append((
    "def handle_spool_category(category: str, cat: dict, pins: dict, subdir: str) -> str:",
    "def _spool_order(_spool):\n"
    "    def _key(_n):\n"
    "        try:\n"
    "            _row = load_json(_spool / _n) or {}\n"
    "        except OSError:\n"
    "            _row = {}\n"
    "        return (int(_row.get(\"priority\", 100)), _n)\n"
    "    return sorted(os.listdir(_spool), key=_key)\n"
    "\n"
    "\n"
    "def handle_spool_category(category: str, cat: dict, pins: dict, subdir: str) -> str:"))
EDITS.append((
    "    for name in sorted(os.listdir(spool)):",
    "    for name in _spool_order(spool):"))

# --- B5: measured byte recovery instead of unfalsifiable path absence
EDITS.append((
    """    action_spec = {"commands": [["rm", "-rf", str(f)] for f in findings[:20]],
                   "rollback": "caches regenerate (reproducible artifacts only)",
                   "timeout_s": cat["timeout_s"]}
    evidence = {"paths": [str(f) for f in findings[:20]],
                "note": "whitelist-matched reproducible caches only"}
    targets = findings[:20]
    return _witnessed_action("B5_SAFE_STORAGE_MAINTENANCE", "storage-cache",
                             action_spec, evidence, pins,
                             {"argv": [["rm", "-rf", str(f)] for f in targets],
                              "verify_kind": "paths-absent:" + "|".join(str(f) for f in targets),
                              "timeout_s": 30})""",
    """    action_spec = {"commands": [["rm", "-rf", str(f)] for f in findings[:20]],
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
                              "timeout_s": 30})"""))

# --- B5 verify branch in _execute_pending
EDITS.append((
    """        elif vk.startswith("sha256:"):
            _, target, want = vk.split(":", 2)
            verified = Path(target).exists() and hashlib.sha256(
                Path(target).read_bytes()).hexdigest() == want""",
    """        elif vk.startswith("cache-bytes-freed:"):
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
            verified = want > 0 and after < want
        elif vk.startswith("sha256:"):
            _, target, want = vk.split(":", 2)
            verified = Path(target).exists() and hashlib.sha256(
                Path(target).read_bytes()).hexdigest() == want"""))

raw = P.read_bytes()
old = raw.decode("utf-8")
if raw != old.encode("utf-8"):
    sys.exit("ABORT: round-trip mismatch")
base = hashlib.sha256(raw).hexdigest()
assert base.startswith("109e68c0"), base
for i, (a, _) in enumerate(EDITS):
    if old.count(a) != 1:
        sys.exit("ABORT: edit %d anchor count = %d" % (i, old.count(a)))
new = old
for a, b in EDITS:
    new = new.replace(a, b)
ast.parse(new)
STAGE.mkdir(parents=True, exist_ok=True)
shutil.copy2(P, STAGE / "ops_agent.py.baseline-109e68c0")
(STAGE / "ops_agent.py").write_bytes(new.encode("utf-8"))
print("baseline:", base[:16])
print("successor:", hashlib.sha256((STAGE / "ops_agent.py").read_bytes()).hexdigest()[:16])
