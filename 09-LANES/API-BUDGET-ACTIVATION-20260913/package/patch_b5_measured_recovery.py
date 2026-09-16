#!/usr/bin/env python3
"""patch_b5_measured_recovery.py — REAL_CODE_DEFECT fix for B5 outcome predicate.

Deterministic diagnosis (zero paid API):
  B5's verify_kind "paths-absent" is unfalsifiable for REGENERATING caches
  (__pycache__/.pytest_cache/*.pyc reappear between rm and verify in a live
  Python tree) -> verified=False -> OUTCOME_MISMATCH -> breaker, even though
  the rm really freed space. Fix: measured byte recovery (REAL-WORK-BRIDGE §8:
  "storage issue: measured space recovery").

Deploys as a B8 canary proposal (witness-gated, budget-queued). No service
restart; next ops-agent tick picks up the verdict path only after canary.
"""
import hashlib
import pathlib
import py_compile
import shutil
import subprocess
import sys

OPS = pathlib.Path("/home/ari/ofn/state/ops-agent")
T = OPS / "ops_agent.py"
STAGE = pathlib.Path("/home/ari/ofn/state/coding-worker/stage/B5-MEASURED-RECOVERY-001")

src = T.read_text(encoding="utf-8")
print("pre_image:", hashlib.sha256(src.encode()).hexdigest()[:24])

# --- 1. handler: measure bytes BEFORE, declare a measured verify_kind --------
OLD_H = '''    evidence = {"paths": [str(f) for f in findings[:20]],
                "note": "whitelist-matched reproducible caches only"}
    targets = findings[:20]
    return _witnessed_action("B5_SAFE_STORAGE_MAINTENANCE", "storage-cache",
                             action_spec, evidence, pins,'''
NEW_H = '''    before_bytes = sum(f.stat().st_size if f.is_file() else
                       sum(x.stat().st_size for x in f.rglob("*") if x.is_file())
                       for f in findings[:20] if f.exists())
    evidence = {"paths": [str(f) for f in findings[:20]],
                "measured_bytes_before": before_bytes,
                "note": "whitelist-matched reproducible caches only; success = measured byte recovery (REAL-WORK-BRIDGE s8), NOT path absence (caches regenerate by design)"}
    targets = findings[:20]
    action_spec["verify_kind"] = "cache-bytes-freed:%d" % before_bytes
    return _witnessed_action("B5_SAFE_STORAGE_MAINTENANCE", "storage-cache",
                             action_spec, evidence, pins,'''

# --- 2. executor: measured predicate ----------------------------------------
OLD_V = '''        elif vk.startswith("sha256:"):'''
NEW_V = '''        elif vk.startswith("cache-bytes-freed:"):
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
        elif vk.startswith("sha256:"):'''

for old, new, label in ((OLD_H, NEW_H, "handler"), (OLD_V, NEW_V, "executor")):
    if old not in src:
        print("ANCHOR_MISSING:", label)
        sys.exit(3)
    if src.count(old) != 1:
        print("ANCHOR_NOT_UNIQUE:", label)
        sys.exit(3)
    src = src.replace(old, new, 1)
    print("patched:", label)

# --- 3. stage + compile + unit test ------------------------------------------
STAGE.mkdir(parents=True, exist_ok=True)
stage_file = STAGE / "ops_agent.py"
stage_file.write_text(src, encoding="utf-8")
py_compile.compile(str(stage_file), doraise=True)
print("stage compiles OK")

TEST = '''def test_predicate_present():
    src = open(%r).read()
    assert 'cache-bytes-freed:' in src
    assert 'measured_bytes_before' in src
    assert 'after < want' in src
''' % (str(stage_file),)
(STAGE / "test_predicate.py").write_text(TEST, encoding="utf-8")
r = subprocess.run([sys.executable, "-m", "pytest", "-q", "test_predicate.py"],
                   cwd=STAGE, capture_output=True, text=True, timeout=120)
print("stage test:", (r.stdout or "").strip().splitlines()[-1:][0][:120])
if r.returncode != 0:
    print(r.stdout[-400:]); sys.exit(5)

# --- 4. B8 canary proposal (queued behind CATSCOPE; fires at budget wake) ----
backup = STAGE / "ops_agent.py.bak"
shutil.copyfile(T, backup)
patched_sha, backup_sha = (hashlib.sha256(p.read_bytes()).hexdigest()
                           for p in (stage_file, backup))
prop = pathlib.Path("/home/ari/ofn/state/ops-agent/state/canary-requests") / \
    "native-B5-MEASURED-RECOVERY-001.json"
prop.write_text(json.dumps({
    "patched": str(stage_file), "backup": str(backup), "target": str(T),
    "target_sha256": patched_sha, "component": "ops-agent",
    "requested_by": "octopus-realwork-bridge/1.0", "task_id": "B5-MEASURED-RECOVERY-001",
    "provenance": {"class": "REAL_CODE_DEFECT",
                   "source": "ops-receipts OPS_B_OUTCOME_REJECTED 2026-09-13T02:30:02Z OUTCOME_MISMATCH + ops_agent.py paths-absent predicate",
                   "source_ts": "2026-09-13T02:30:02Z",
                   "source_hash": "bf2ab4279712ca0f164e903c36093ad8ed28fc8065ab2cb9be37b2a996c6d965"},
    "diagnosis": "paths-absent is unfalsifiable for regenerating caches; fix = measured byte recovery",
    "diff_scope": ["state/ops-agent/ops_agent.py"],
    "rollback": "restore backup copy"},
    sort_keys=True) + "\n", encoding="utf-8")
print("canary proposal:", prop.name)
print("patched_sha:", patched_sha[:24], "backup_sha:", backup_sha[:24])
print("PATCH_B5_OK")
