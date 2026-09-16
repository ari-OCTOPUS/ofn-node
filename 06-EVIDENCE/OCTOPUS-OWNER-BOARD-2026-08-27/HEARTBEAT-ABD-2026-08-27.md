# HEARTBEAT-ABD 2026-08-27 ~10:58 AEST

GO: ari (owner: adapt boards)
Unit: octopus-heartbeat.service (timer every 60s)
Change: drop-in /etc/systemd/system/octopus-heartbeat.service.d/start-limit.conf
  [Unit]
  StartLimitIntervalSec=0
Script: UNCHANGED sha256 4f7baa2bb28b963396ae7e99bfdf07a31f9321192c9459d22537399429bc1eaf
ofn-heartbeat.service: left active (untouched)

Verify:
- StartLimitIntervalUSec=0
- 3x systemctl start -> Result=success ExecMainStatus=0 (no start-limit-hit)
- timer active; last trigger 10:57, next 10:58 AEST

Rollback: ROLLBACK-octopus-heartbeat.md in this folder
