#!/usr/bin/env python3
"""fix_v14_testcwd.py — stage tests must run where the patched module lives."""
import hashlib
import pathlib
import py_compile
import shutil
import sys

T = pathlib.Path("/home/ari/ofn/state/coding-worker/coding_worker.py")
src = T.read_text(encoding="utf-8")
print("pre_image:", hashlib.sha256(src.encode()).hexdigest()[:24])

OLD_W = '''        for t in doc.get("tests") or []:
            (stage / t["path"]).write_text(str(t.get("content", "")), encoding="utf-8")'''
NEW_W = '''        _tdir = stage / Path(doc["files"][0]["path"]).parent
        _tdir.mkdir(parents=True, exist_ok=True)
        for t in doc.get("tests") or []:
            (_tdir / Path(t["path"]).name).write_text(
                str(t.get("content", "")), encoding="utf-8")'''

OLD_R = '''    ok_all = True
    for cmd in doc.get("run_tests") or []:
        p = subprocess.run(str(cmd).split(), cwd=stage, capture_output=True,
                           text=True, timeout=300)'''
NEW_R = '''    _dirs = sorted({str((stage / Path(f["path"])).parent) for f in doc["files"]})
    _tdir = stage / Path(doc["files"][0]["path"]).parent
    _env = {**os.environ, "PYTHONPATH": os.pathsep.join(_dirs)}
    ok_all = True
    for cmd in doc.get("run_tests") or []:
        p = subprocess.run(str(cmd).split(), cwd=_tdir, env=_env, capture_output=True,
                           text=True, timeout=300)'''

for old, new, label in ((OLD_W, NEW_W, "tests-write"), (OLD_R, NEW_R, "tests-run")):
    if old not in src:
        print("ANCHOR_MISSING:", label)
        sys.exit(3)
    src = src.replace(old, new, 1)
    print("patched:", label)

B = T.with_suffix(".py.pre-freedom-fix1-20260913")
if not B.exists():
    shutil.copy2(T, B)
T.write_text(src, encoding="utf-8")
try:
    py_compile.compile(str(T), doraise=True)
except py_compile.PyCompileError as exc:
    shutil.copy2(B, T)
    sys.exit(4)
print("post_image:", hashlib.sha256(T.read_bytes()).hexdigest()[:24])
print("FIX_OK")
