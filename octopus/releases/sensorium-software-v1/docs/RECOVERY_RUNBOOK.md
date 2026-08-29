# RECOVERY_RUNBOOK

Code rollback: `ln -sfn /opt/octopus/releases/phase2-kernel-v1 /opt/octopus/current && systemctl restart octopus-sensorium`

Do not restore root-v1. Do not rewrite audit or evidence.
Wave 0 freeze `sha256:046566dab34ca98f7f7c564cde9e8c92b471bae65f93bf7cf4f7d85b9a2fa3d4` must stay.
Registry v4 and v5 milestones stay.
If gates_failed is non-empty after restart, keep DEGRADED and do not claim READY.
