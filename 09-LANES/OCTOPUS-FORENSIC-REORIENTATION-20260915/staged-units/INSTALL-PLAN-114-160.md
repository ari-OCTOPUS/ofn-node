# Install plan — persistence units for 114 (evaluator) and 160 (ingestion)

Status: **STAGED, NOT APPLIED** (per round acceptance: unit پیشنهادی staged نه applied).
Same pattern as the proven `octopus-t3-model.service` on 193.

## Precondition

The services currently run via `nohup` (reboot-orphaned). Installing the unit while
nohup still holds the port will double-bind or flap. Order matters.

## Exact install sequence (per node, from 138, mesh key)

```bash
# 114 — evaluator
ssh -i /home/ari/.ssh/octopus_mesh_ed25519 root@192.168.0.114 '
  pkill -f "python3 /opt/octopus-worker/evaluator.py" || true; sleep 2
  # copy staged unit from this lane to /etc/systemd/system/octopus-evaluator.service
  systemctl daemon-reload
  systemctl enable --now octopus-evaluator.service
  sleep 3; systemctl is-active octopus-evaluator.service
  curl -s -m 4 http://127.0.0.1:8114/health'
# 160 — ingestion (same shape, port 8160, ingestion.py)
```

## Acceptance

- `systemctl is-active` = active AND `/health` returns ok
- after a service restart: port answers again (survives restart)
- ps shows the process parented by systemd (not ppid=1 orphan from nohup)

## Rollback

```bash
systemctl disable --now octopus-evaluator.service
nohup python3 /opt/octopus-worker/evaluator.py >/dev/null 2>&1 &
```

(rollback returns to the current nohup state — port healthy, reboot-fragile as today)

## Authority note

Internal, reversible, non-TCB (Class A under GOV-FREEDOM-V2 / AUTONOMY-V3 GREEN).
Cross-node write is outside the 138 executor sandbox; executing the install is a
commander action, not an ops-agent canary. Recorded as OPEN-WORK OW-4.
