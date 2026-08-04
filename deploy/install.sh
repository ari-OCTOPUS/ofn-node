#!/usr/bin/env bash
# OFN installer for the Orange Pi. Idempotent and non-destructive:
# it never enables an outbound flag and never writes a secret.
set -euo pipefail

USER_NAME="${SUDO_USER:-$USER}"
HOME_DIR="$(getent passwd "$USER_NAME" | cut -d: -f6)"
APP_DIR="$HOME_DIR/ofn"
STATE_DIR="$HOME_DIR/.local/share/ofn"
CONF_DIR="$HOME_DIR/.config/ofn"

say() { printf '\n\033[1;36m==> %s\033[0m\n' "$*"; }
warn() { printf '\033[1;33m !  %s\033[0m\n' "$*"; }

[[ $EUID -eq 0 ]] || { echo "run with sudo"; exit 1; }

say "Checking the environment before changing anything"
python3 --version
uname -m
free -h | head -2
df -h "$HOME_DIR" | tail -1

# A board with no RTC will read near-epoch until NTP lands. Installing is
# harmless, but the node would boot straight into SAFE MODE.
if [[ "$(date +%s)" -lt 1767225600 ]]; then
  warn "System clock looks unsynced. Run: timedatectl set-ntp true"
fi

if [[ ! -f "$APP_DIR/ofn/__init__.py" ]]; then
  echo "Expected the app at $APP_DIR — unzip it there first."; exit 1
fi

say "Creating directories"
install -d -o "$USER_NAME" -g "$USER_NAME" -m 0755 "$STATE_DIR"
install -d -o "$USER_NAME" -g "$USER_NAME" -m 0700 "$CONF_DIR"

if [[ ! -f "$CONF_DIR/node.env" ]]; then
  cat > "$CONF_DIR/node.env" <<'ENV'
# Non-secret node configuration.
OFN_STATE_DIR=%STATE%
OFN_PACKS_DIR=%APP%/packs
OFN_UTILISATION=0.40
OFN_ESTIMATED_CAPACITY_TOKENS=180000000

# Outbound stays off. Turning any of these on is an owner decision made in a
# session, not a default shipped by an installer.
OFN_WIRE_OUTBOUND=0
OFN_WIRE_EMAIL=0
OFN_WIRE_PUBLISH=0
ENV
  sed -i "s|%STATE%|$STATE_DIR|; s|%APP%|$APP_DIR|" "$CONF_DIR/node.env"
  chown "$USER_NAME:$USER_NAME" "$CONF_DIR/node.env"
  chmod 0600 "$CONF_DIR/node.env"
fi

if [[ ! -f "$CONF_DIR/secrets.env" ]]; then
  # Names only. Values are typed in on this machine, never shipped.
  cat > "$CONF_DIR/secrets.env" <<'ENV'
OFN_SESSION_SECRET=
OFN_BOT_TOKEN_ZIMAN=
OFN_BOT_TOKEN_LEAD=
OFN_BOT_TOKEN_STUDIO=
OFN_BOT_TOKEN_OWNER=
OFN_OWNER_USER_IDS=
OFN_REMOTE_API_KEY=
ENV
  chown "$USER_NAME:$USER_NAME" "$CONF_DIR/secrets.env"
  chmod 0600 "$CONF_DIR/secrets.env"
  warn "Fill $CONF_DIR/secrets.env by hand. Never paste those values into a chat."
fi

say "Running the test suite before installing any unit"
sudo -u "$USER_NAME" python3 -m pytest -q --rootdir "$APP_DIR" "$APP_DIR" \
  || { echo "Tests failed — refusing to install."; exit 1; }

say "Installing systemd units"
install -m 0644 systemd/ofn.service        /etc/systemd/system/
install -m 0644 systemd/ofn-boot.service   /etc/systemd/system/
install -m 0644 systemd/ofn-backup.service /etc/systemd/system/
install -m 0644 systemd/ofn-backup.timer   /etc/systemd/system/
# Named by ofn-backup.service's OnFailure=. Installing the two separately is
# how the alert went missing in the first place.
install -m 0644 systemd/ofn-backup-alert.service /etc/systemd/system/

if [[ -e /dev/watchdog ]]; then
  install -d -m 0755 /etc/systemd/system.conf.d
  install -m 0644 systemd/99-watchdog.conf /etc/systemd/system.conf.d/
  say "Hardware watchdog configured (timeout rounds up to 44s on this SoC)"
else
  warn "No /dev/watchdog — enable it in the device tree if you want one."
fi

systemctl daemon-reload
say "Units installed but NOT started."
cat <<'NEXT'

Deliberately not started. Before enabling:

  1. Fill  ~/.config/ofn/secrets.env
  2. Dry run:   python3 -m ofn.preflight
  3. Then:      sudo systemctl enable --now ofn-boot ofn ofn-backup.timer
  4. Watch:     journalctl -u ofn -f

Enabling a service that has never had a successful dry run is how a board
ends up in a restart loop at 2am.
NEXT
