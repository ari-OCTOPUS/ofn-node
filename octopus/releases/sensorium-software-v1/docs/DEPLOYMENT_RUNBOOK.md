# DEPLOYMENT_RUNBOOK

1. Build a read-only release under /opt/octopus/releases/<id>
2. Run pytest inside that tree
3. Verifier to a temp file, not live boot_report
4. Atomic `ln -sfn` of /opt/octopus/current
5. Restart only octopus-sensorium
6. Promote boot_report only if gates_failed=[]
