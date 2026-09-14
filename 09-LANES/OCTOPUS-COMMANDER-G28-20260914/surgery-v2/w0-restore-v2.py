#!/usr/bin/env python3
"""W0 isolation probe v2 — replaces the blind OSError→REJECTED bug.

Per R2 from the surgery review:
  1. verdict_isolation is SEPARATE from verdict_bytes (they can diverge)
  2. per-host protected path + policy determined from the host itself
  3. uid/gid/groups, resolved path, parent existence, errno all recorded
  4. ENOENT / ENOSPC / tool errors are NOT PermissionDenied
  5. EACCES/EPERM/EROFS only count with a positive control (scratch write works)
  6. archive member list checked for path traversal BEFORE extraction
  7. mode + executable bit checked alongside size/hash
"""
import errno
import hashlib
import json
import os
import pathlib
import pwd
import grp
import py_compile
import subprocess
import sys
import tarfile

BUNDLE = sys.argv[1]
MANIFEST = sys.argv[2]
SCRATCH = pathlib.Path(sys.argv[3])
EXPECT_HOST = sys.argv[4]
# per-host protected path + what we expect to be protecting it
PROTECTED = {
    "138": {"path": "/home/ari/ofn/state/ops-agent/state",
            "policy": "DAC: owned by uid ari, process runs as nobody"},
    "180": {"path": "/opt/octopus",
            "policy": "DAC: owned by root, process runs as nobody"},
}[EXPECT_HOST]

out = {"host": EXPECT_HOST, "observed_at_utc": subprocess.run(
    ["date", "-u", "+%Y-%m-%dT%H:%M:%SZ"], capture_output=True, text=True
).stdout.strip()}

# --- identity of this process
try:
    me = pwd.getpwuid(os.getuid())
    out["process_identity"] = {
        "uid": os.getuid(), "gid": os.getgid(),
        "username": me.pw_name,
        "groups": [grp.getgrgid(g).gr_name for g in os.getgroups()]}
except Exception as e:
    out["process_identity"] = {"error": str(e)[:60]}

# --- archive safety: check members BEFORE extraction
rst = SCRATCH / "restore"
rst.mkdir(parents=True, exist_ok=True)
with tarfile.open(BUNDLE, "r:gz") as tf:
    members = tf.getnames()
    dangerous = [m for m in members if ".." in m or m.startswith("/")]
    out["archive_members"] = len(members)
    out["archive_dangerous_paths"] = dangerous
    if dangerous:
        out["verdict_bytes"] = "FAIL"
        out["verdict_isolation"] = "NOT_RUN"
        print(json.dumps(out, indent=1))
        sys.exit(1)
    tf.extractall(str(rst))

# --- byte restore (hash + size + mode + exec-bit)
man = json.loads(pathlib.Path(MANIFEST).read_text(encoding="utf-8"))
byte_ok, byte_fail, meta_fail = 0, [], []
for f in man["files"]:
    p = rst / "root" / f["path"].lstrip("/")
    if not p.exists():
        if "RESTORE_DEPENDENCY" in f.get("note", ""):
            continue
        byte_fail.append({"path": f["path"][-50:], "err": "ABSENT"})
        continue
    h = hashlib.sha256(p.read_bytes()).hexdigest()
    if h != f["sha256"]:
        byte_fail.append({"path": f["path"][-50:], "err": "HASH"})
    elif p.stat().st_size != f["size"]:
        byte_fail.append({"path": f["path"][-50:], "err": "SIZE"})
    else:
        # mode: manifest mode is a string like "755" or "644"
        want_mode = int(f.get("mode", "644"), 8)
        have_mode = p.stat().st_mode & 0o777
        if want_mode != 0 and have_mode != want_mode:
            meta_fail.append({"path": f["path"][-50:],
                              "want_mode": oct(want_mode),
                              "have_mode": oct(have_mode)})
        else:
            byte_ok += 1
out["bytes_ok"] = byte_ok
out["bytes_fail"] = byte_fail
out["metadata_mode_mismatches"] = meta_fail
out["verdict_bytes"] = "PASS" if (not byte_fail and not meta_fail) else "FAIL"

# --- compile
compiled, cfail = 0, []
for py in (rst / "root").rglob("*.py"):
    try:
        py_compile.compile(str(py), cfile=str(SCRATCH / "c.pyc"), doraise=True)
        compiled += 1
    except Exception as e:
        cfail.append({"f": str(py)[-50:], "e": type(e).__name__})
out["py_compiled"] = compiled
out["py_compile_failures"] = cfail

# --- POSITIVE CONTROL: write to scratch MUST succeed
try:
    (SCRATCH / "positive-control").write_text("ok")
    out["positive_control_scratch_write"] = "OK"
except OSError as e:
    out["positive_control_scratch_write"] = "FAIL errno=%s" % e.errno

# --- NEGATIVE PROBE: attempt write to the protected path
#     record the actual errno, don't blindly call it REJECTED
pp = pathlib.Path(PROTECTED["path"])
probe_target = pp / "zz-w0-v2-probe"
out["negative_probe"] = {
    "target": str(probe_target),
    "parent_exists": pp.exists(),
    "parent_resolved": str(pp.resolve()) if pp.exists() else None,
    "parent_mode": oct(pp.stat().st_mode & 0o777) if pp.exists() else None,
    "parent_owner": pwd.getpwuid(pp.stat().st_uid).pw_name if pp.exists() else None,
}
try:
    probe_target.write_text("x")
    # if we get here the write SUCCEEDED — that's a fence failure
    out["negative_probe"]["errno"] = None
    out["negative_probe"]["result"] = "WRITTEN_FENCE_FAIL"
    probe_target.unlink()  # clean up
except OSError as e:
    out["negative_probe"]["errno"] = e.errno
    out["negative_probe"]["errno_name"] = errno.errorcode.get(e.errno, "?")
    if e.errno in (errno.EACCES, errno.EPERM, errno.EROFS):
        out["negative_probe"]["result"] = "REJECTED_BY_PERMISSION"
    elif e.errno == errno.ENOENT:
        out["negative_probe"]["result"] = "REJECTED_BY_ABSENCE_NOT_PERMISSION"
    elif e.errno == errno.ENOSPC:
        out["negative_probe"]["result"] = "REJECTED_BY_DISK_FULL_NOT_PERMISSION"
    else:
        out["negative_probe"]["result"] = "REJECTED_BY_ERRNO_%d" % e.errno

# --- verdict_isolation (separate from verdict_bytes)
ok_iso = (out["negative_probe"]["result"] == "REJECTED_BY_PERMISSION"
          and out["positive_control_scratch_write"] == "OK")
out["verdict_isolation"] = "PASS" if ok_iso else "FAIL"

pathlib.Path(SCRATCH / "restore-result-v2.json").write_text(
    json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
# summary line
print("bytes:%s isolation:%s probe_errno:%s positive:%s" % (
    out["verdict_bytes"], out["verdict_isolation"],
    out["negative_probe"].get("errno_name", "?"),
    out["positive_control_scratch_write"]))
sys.exit(0 if (out["verdict_bytes"] == "PASS"
              and out["verdict_isolation"] == "PASS"
              and not cfail) else 1)
