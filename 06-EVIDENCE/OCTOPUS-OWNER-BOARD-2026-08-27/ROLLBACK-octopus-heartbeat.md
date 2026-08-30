# Rollback octopus-heartbeat drop-in (Board2 192.168.0.138)

Removes only the StartLimitIntervalSec=0 drop-in. Does not touch the python script or ofn-heartbeat.

```bash
sudo rm -f /etc/systemd/system/octopus-heartbeat.service.d/start-limit.conf
sudo rmdir /etc/systemd/system/octopus-heartbeat.service.d 2>/dev/null || true
sudo systemctl daemon-reload
sudo systemctl reset-failed octopus-heartbeat.service
```

After rollback, StartLimitBurst=3 / 300s returns and the 60s timer can hit start-limit-hit again.
