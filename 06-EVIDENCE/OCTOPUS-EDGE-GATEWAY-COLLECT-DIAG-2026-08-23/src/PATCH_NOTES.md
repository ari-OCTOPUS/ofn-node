# Edge Gateway Stage2D deploy notes

1. Install package files under `/opt/octopus/current/src/octopus_sensorium/edge_gateway/`
2. Add `COLLECT_DIAGNOSTICS` to ALLOWED_COMMANDS in command_gate.py
3. Replace `_on_command` defer-all with branch for DIAG_COMMANDS
4. Prove: `sudo -u octopus /opt/octopus/venv/bin/python -m octopus_sensorium.edge_gateway.collect_diagnostics --prove`
5. Restart `octopus-sensorium.service` only after prove PASS/DEGRADED
