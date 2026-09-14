#!/bin/bash
# ROUND31 section 1: kernel-level harness fence + negative probe + the
# same-basename mapping fixture. The fence: mutating harnesses run as
# 'nobody' with a world-writable scratch root - production (/home/ari/ofn)
# is NOT writable by that uid at the DAC level, so a wrong Path.home pin
# can no longer touch real files. monkeypatching stays a convenience layer.
set -u
SCRATCH=$(mktemp -d /tmp/fence-XXXX)
chmod 777 "$SCRATCH"
ART=/home/ari/ofn/state/ops-agent/ops_agent.py
cp "$ART" "$SCRATCH/ops_agent.py"
chmod a+r "$SCRATCH/ops_agent.py"
STAGE=/home/ari/ofn/state/coding-worker/stage/SUCCESSOR-TRIO-20260914/ops_agent.py
cp "$STAGE" "$SCRATCH/trio_ops_agent.py"
chmod a+r "$SCRATCH/trio_ops_agent.py"

echo "=== NEGATIVE PROBE: nobody must NOT write production ==="
if sudo -n setpriv --reuid=nobody --regid=nogroup --clear-groups \
    bash -c "echo x > /home/ari/ofn/state/ops-agent/state/zz-fence-probe" 2>/dev/null; then
  echo "FENCE FAIL: production write succeeded"
  rm -f /home/ari/ofn/state/ops-agent/state/zz-fence-probe
  exit 1
else
  echo "FENCE OK: production write rejected (kernel DAC)"
fi
echo "=== POSITIVE: scratch writable by nobody ==="
sudo -n setpriv --reuid=nobody --regid=nogroup --clear-groups \
    bash -c "echo ok > $SCRATCH/probe" && cat "$SCRATCH/probe"

echo "=== SAME-BASENAME MAPPING FIXTURE (as nobody, in scratch) ==="
sudo -n setpriv --reuid=nobody --regid=nogroup --clear-groups \
    env SCRATCH="$SCRATCH" python3 - <<'PYEOF'
import json, os, pathlib, shutil
fx = pathlib.Path(os.environ["SCRATCH"]) / "samename"
if fx.exists():
    shutil.rmtree(fx)
for tag, sub in (("A", "projA/pkg"), ("B", "projB/pkg")):
    d = fx / sub / "__pycache__"
    d.mkdir(parents=True)
    (d / "m.pyc").write_text("CONTENT-" + tag, encoding="utf-8")
q = fx / "qdir"
q.mkdir()
# the INCIDENT-era quarantine style: mv to the shared dir by basename
import subprocess
r1 = subprocess.run(["mv", str(fx / "projA/pkg/__pycache__"), str(q)])
r2 = subprocess.run(["mv", str(fx / "projB/pkg/__pycache__"), str(q)])
print("mv1 rc=%s mv2 rc=%s  (collision expected on the second)" %
      (r1.returncode, r2.returncode))
landed = q / "__pycache__"
print("landed content:", landed.joinpath("m.pyc").read_text())
print("projB still in place:", (fx / "projB/pkg/__pycache__").exists())
# basename-based recovery mapping is UNSOUND for the landed item: which of
# A/B is it? Prove the ambiguity:
cand = landed.joinpath("m.pyc").read_text()
print("basename-recovery would guess parent by basename -> identity:",
      cand, "- ambiguous between projA and projB unless content/argv known")
# the CORRECT mapping source: the recorded argv (src->dst pairs)
argv_pairs = [[str(fx / "projA/pkg/__pycache__"), str(q / "__pycache__")],
              [str(fx / "projB/pkg/__pycache__"), str(q / "__pycache__")]]
print("argv-recorded pairs resolve identity exactly: pair0 landed=%s"
      % (pathlib.Path(argv_pairs[0][1]).exists()))
PYEOF
echo "SCRATCH=$SCRATCH"
