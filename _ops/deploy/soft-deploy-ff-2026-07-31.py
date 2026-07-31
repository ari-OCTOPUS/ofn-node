# -*- coding: utf-8 -*-
"""Soft-deploy: fast-forward the LIVE tree to master, preserving everything.

Rules honoured:
  * NOTHING deleted - every displaced file is copied/moved into
    _Archive/deploy-preserve-2026-07-31/ mirroring its path (constitution rule 1).
  * STOP files, flags, processes: untouched.
  * If any dirty-tracked file differs from the master blob (live evolved again),
    ABORT listing it - no silent clobber of an active parallel session.
"""
import shutil
import subprocess
import sys
import time
from pathlib import Path

LIVE = Path(r"F:\backup")
ARCH = LIVE / "_Archive" / "deploy-preserve-2026-07-31"


def git(*args, binary=False, ok=(0,)):
    r = subprocess.run(["git", "-C", str(LIVE), *args], capture_output=True)
    if r.returncode not in ok:
        print("GIT-FAIL:", args, r.stderr.decode("utf-8", "replace")[:400])
    return r.stdout if binary else r.stdout.decode("utf-8", "replace")


head = git("rev-parse", "HEAD").strip()
master = git("rev-parse", "master").strip()
print("live HEAD:", head[:9], "-> target:", master[:9])

changed = [ln for ln in git("diff", "--name-only", f"{head}..master").splitlines() if ln]
status = {}
for ln in git("status", "--porcelain", "--untracked-files=all").splitlines():
    if len(ln) > 3:
        status[ln[3:].strip('"')] = ln[:2]

E, R, U = [], [], []
for p in changed:
    st = status.get(p, "")
    if st == "??":
        U.append(p)
    elif st.strip():
        blob = git("show", f"master:{p}", binary=True)
        try:
            cur = (LIVE / p).read_bytes()
        except OSError:
            R.append(p)
            continue
        (E if cur == blob else R).append(p)

print(f"E={len(E)} U={len(U)} R={len(R)}")
if R:
    print("ABORT - live evolved again on:", *R, sep="\n  ")
    sys.exit(2)

ARCH.mkdir(parents=True, exist_ok=True)

# E: preserve copy, then reset to HEAD so the ff can write the (identical) target
for p in E:
    dst = ARCH / p
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(LIVE / p, dst)
ck = subprocess.run(["git", "-C", str(LIVE), "checkout", "HEAD", "--", *E],
                    capture_output=True)
if ck.returncode != 0:
    print("ABORT checkout:", ck.stderr.decode("utf-8", "replace")[:500])
    sys.exit(3)

# U: move aside (transfer, not delete) - the ff restores the same content from git
for p in U:
    dst = ARCH / p
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(LIVE / p), str(dst))

# ff (retry for AV locks)
for i in range(6):
    r = subprocess.run(["git", "-C", str(LIVE), "merge", "--ff-only", "master"],
                       capture_output=True)
    if r.returncode == 0:
        break
    print("ff attempt", i + 1, "failed:",
          r.stderr.decode("utf-8", "replace").splitlines()[:2])
    time.sleep(5 * (i + 1))
else:
    print("ABORT - ff kept failing; live untracked work preserved in", ARCH)
    sys.exit(4)

new_head = git("rev-parse", "HEAD").strip()
print("live HEAD now:", new_head[:9], "== master:", new_head == master)
print("STOP-ORGANISM exists:", (LIVE / "_ops" / "STOP-ORGANISM").exists())
n_dirty = len([ln for ln in git("status", "--porcelain").splitlines() if ln])
print("dirty entries after ff:", n_dirty)
print("preserved under:", ARCH)
