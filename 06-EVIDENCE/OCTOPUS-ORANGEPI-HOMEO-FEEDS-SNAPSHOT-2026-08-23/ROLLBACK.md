# ROLLBACK

1. `systemctl disable --now octopus-homeo-feeds-snapshot.timer`
2. `systemctl stop octopus-homeo-feeds-snapshot.service` (if running)
3. Remove `/etc/systemd/system/octopus-homeo-feeds-snapshot.service` and `.timer`
4. `systemctl daemon-reload`
5. Optional: keep snapshot JSON for audit
6. Confirm `octopus-external-feeds.timer` still active
