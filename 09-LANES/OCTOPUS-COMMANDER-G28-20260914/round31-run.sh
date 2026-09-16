#!/bin/bash
# ROUND31 battery under the kernel fence: scratch root world-writable, harness
# runs as uid nobody (production not writable by that uid - proven by the
# in-run negative probe). Artifacts + real queue requests are COPIES.
set -u
S=$(mktemp -d /tmp/r31-XXXX)
chmod 777 "$S"
cp /home/ari/ofn/state/coding-worker/stage/SUCCESSOR-TRIO-20260914/ops_agent.py "$S/trio_ops_agent.py"
cp /home/ari/ofn/state/coding-worker/stage/SUCCESSOR-TRIO-20260914/ops_agent.py.trio-v2d-a85db3b0 "$S/v2d_ops_agent"
cp /home/ari/ofn/state/ops-agent/ops_agent.py "$S/live_ops_agent.py"
mkdir "$S/requests"
cp /home/ari/ofn/state/ops-agent/state/canary-requests/*.json "$S/requests/"
cp /home/ari/ofn/state/coding-worker/stage/W24-G8G27-PRODUCER/glass_runner.py "$S/art_glass.py"
cp /home/ari/ofn/state/coding-worker/stage/TASK-W24-BINDER-SPOOL-006/go_b3_owner_bind.py "$S/art_binder.py"
cp /home/ari/ofn/state/coding-worker/stage/G30-STAGE-GUARD-WIRING-001/coding_worker.py "$S/art_worker.py"
cp "$S/trio_ops_agent.py" "$S/art_trio.py"
chmod -R a+rX "$S"

echo "=== in-fence negative probe (production write must fail) ==="
if sudo -n setpriv --reuid=nobody --regid=nogroup --clear-groups \
    bash -c "echo x > /home/ari/ofn/state/ops-agent/state/zz-r31-probe" 2>/dev/null; then
  echo "FENCE FAIL"; rm -f /home/ari/ofn/state/ops-agent/state/zz-r31-probe; exit 1
else
  echo "FENCE OK (production write rejected for uid nobody)"
fi

sudo -n setpriv --reuid=nobody --regid=nogroup --clear-groups \
    env FXROOT="$S" TMPDIR="$S" HOME="$S/home" \
    python3 /tmp/round31-battery.py
rc=$?
sudo -n rm -rf "$S"
echo "battery rc=$rc"
exit $rc
