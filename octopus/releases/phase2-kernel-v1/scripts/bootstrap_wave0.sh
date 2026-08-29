#!/usr/bin/env bash
# Wave 0 host bootstrap. Does not enable unknown sensors or attach legs.
set -euo pipefail
export DEBIAN_FRONTEND=noninteractive
umask 077

BOARD_ID="sensorium-opi5pro-68e44cdf"
NATS_LISTEN="${NATS_LISTEN:-192.168.0.182}"
NATS_DEB="${NATS_DEB:-/tmp/nats-server.deb}"
VENV=/opt/octopus/venv
CA=/root/octopus-ca
SECRETS=/etc/octopus/secrets

log() { printf '%s %s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$*" >&2; }

log "creating users and groups"
getent group nats >/dev/null || groupadd --system nats
getent passwd nats >/dev/null || useradd --system --home /var/lib/nats --shell /usr/sbin/nologin --gid nats nats
getent group i2c >/dev/null || groupadd --system i2c
getent group octopus >/dev/null || groupadd --system octopus
getent passwd octopus >/dev/null || useradd --system --home /var/lib/octopus --shell /usr/sbin/nologin --gid octopus octopus
usermod -aG i2c octopus
gpasswd -d octopus gpio 2>/dev/null || true

log "directories and ownership"
mkdir -p /var/lib/nats/jetstream /var/log/nats \
  /var/lib/octopus/state/snapshots /var/lib/octopus/audit /var/lib/octopus/cache \
  /var/log/octopus /etc/octopus/state/snapshots /etc/octopus/state/audit \
  /etc/octopus/trust /etc/octopus/config "$SECRETS" "$CA"
chown -R nats:nats /var/lib/nats /var/log/nats
chown -R octopus:octopus /var/lib/octopus /var/log/octopus /etc/octopus/state
chown -R root:root /etc/octopus/trust /etc/octopus/config /opt/octopus
chmod -R a+rX /opt/octopus
chmod 0755 /opt/octopus /opt/octopus/src /opt/octopus/venv
chmod 0755 /etc/octopus /etc/octopus/trust /etc/octopus/config
chmod 0750 /etc/octopus/secrets /etc/octopus/state /var/lib/octopus /var/log/octopus
chown root:octopus /etc/octopus/secrets
chown root:octopus /etc/octopus/secrets/nats-sensorium.env 2>/dev/null || true
chmod 0700 "$CA"

log "install nats-server 2.12.1"
if ! dpkg -s nats-server >/dev/null 2>&1; then
  dpkg -i "$NATS_DEB"
fi
# Prefer the sandboxed unit in /etc over the package unit.
systemctl disable --now nats-server 2>/dev/null || true

log "python venv"
if [[ ! -x $VENV/bin/python ]]; then
  python3 -m venv "$VENV"
fi
"$VENV/bin/pip" install --upgrade pip
"$VENV/bin/pip" install -e "/opt/octopus[test]"

log "trust root (operator key stays in $CA)"
if [[ ! -f $CA/root.ed25519 ]]; then
  "$VENV/bin/python" /opt/octopus/scripts/sign_config.py keygen
else
  # Re-export public key only.
  "$VENV/bin/python" - <<'PY'
from pathlib import Path
from nacl.signing import SigningKey
key = SigningKey(Path("/root/octopus-ca/root.ed25519").read_bytes())
Path("/etc/octopus/trust/root.pub").write_bytes(bytes(key.verify_key))
Path("/etc/octopus/trust/root.pub").chmod(0o444)
PY
fi
"$VENV/bin/python" /opt/octopus/scripts/sign_config.py sign /etc/octopus/config/board.yaml
"$VENV/bin/python" /opt/octopus/scripts/sign_config.py sign /etc/octopus/config/registry.yaml
chmod 0444 /etc/octopus/trust/root.pub /etc/octopus/trust/revoked.json
chmod 0444 /etc/octopus/config/board.yaml /etc/octopus/config/registry.yaml
chmod 0444 /etc/octopus/config/board.yaml.sig /etc/octopus/config/registry.yaml.sig
chown root:root /etc/octopus/trust/root.pub /etc/octopus/config/board.yaml /etc/octopus/config/registry.yaml
if command -v chattr >/dev/null; then
  chattr +i /etc/octopus/trust/root.pub 2>/dev/null || true
fi

log "NATS credentials and config (passwords not printed)"
NATS_LISTEN="$NATS_LISTEN" OCTOPUS_CA="$CA" OCTOPUS_SECRETS="$SECRETS" \
  "$VENV/bin/python" /opt/octopus/scripts/write_nats_config.py
chown root:octopus "$SECRETS/nats-sensorium.env" 2>/dev/null || chown root:root "$SECRETS/nats-sensorium.env"
chmod 0640 "$SECRETS/nats-sensorium.env"

log "clock: write system UTC into RTC"
timedatectl set-local-rtc 0 2>/dev/null || true
hwclock --systohc --utc || true
hwclock --verbose --show || true

log "udev + systemd"
udevadm control --reload-rules 2>/dev/null || true
udevadm trigger --subsystem-match=i2c-dev 2>/dev/null || true
systemctl daemon-reload
# Apply RuntimeWatchdogSec. This re-execs PID 1; it does not reboot.
systemctl daemon-reexec || true

log "start NATS"
systemctl enable nats-server
systemctl restart nats-server
sleep 1
systemctl --no-pager --full status nats-server | head -20
curl -fsS http://127.0.0.1:8222/varz >/dev/null
curl -fsS http://127.0.0.1:8222/jsz | head -c 200 || true
echo

log "JetStream streams via one-shot provisioner"
INCLUDE_PROVISIONER=1 NATS_LISTEN="$NATS_LISTEN" OCTOPUS_CA="$CA" OCTOPUS_SECRETS="$SECRETS" \
  "$VENV/bin/python" /opt/octopus/scripts/write_nats_config.py
systemctl restart nats-server
sleep 1
set -a
# shellcheck disable=SC1091
source "$CA/nats-provisioner.env"
set +a
PYTHONPATH=/opt/octopus/src "$VENV/bin/python" /opt/octopus/scripts/ensure_streams.py
# Drop provisioner from the live server so the agent cannot use JS admin APIs.
INCLUDE_PROVISIONER=0 NATS_LISTEN="$NATS_LISTEN" OCTOPUS_CA="$CA" OCTOPUS_SECRETS="$SECRETS" \
  "$VENV/bin/python" /opt/octopus/scripts/write_nats_config.py
systemctl reload nats-server 2>/dev/null || systemctl restart nats-server
unset NATS_USER NATS_PASSWORD NATS_URL

log "pytest isolation + identity"
cd /opt/octopus
PYTHONPATH=/opt/octopus/src "$VENV/bin/pytest" -q

log "enable sensorium agent"
systemctl enable octopus-sensorium
systemctl restart octopus-sensorium
sleep 2
systemctl --no-pager --full status octopus-sensorium | head -25

log "Wave 0 bootstrap complete"
