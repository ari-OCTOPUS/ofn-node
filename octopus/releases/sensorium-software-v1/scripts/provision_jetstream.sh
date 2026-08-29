#!/usr/bin/env bash
# One-shot: enable provisioner, apply streams, disable provisioner. Not a daemon.
set -euo pipefail
VENV=/opt/octopus/venv
CA=/root/octopus-ca
LISTEN="${NATS_LISTEN:-192.168.0.182}"
INCLUDE_PROVISIONER=1 NATS_LISTEN="$LISTEN" /opt/octopus/venv/bin/python /opt/octopus/scripts/write_nats_config.py
systemctl restart nats-server
sleep 1
set -a
# shellcheck disable=SC1091
source "$CA/nats-provisioner.env"
set +a
PYTHONPATH=/opt/octopus/src "$VENV/bin/python" /opt/octopus/scripts/ensure_streams.py
INCLUDE_PROVISIONER=0 NATS_LISTEN="$LISTEN" "$VENV/bin/python" /opt/octopus/scripts/write_nats_config.py
systemctl restart nats-server
unset NATS_USER NATS_PASSWORD NATS_URL
echo "provisioner exited"
