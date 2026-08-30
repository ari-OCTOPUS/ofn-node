#!/usr/bin/env bash
# install-docker.sh — Install Docker Engine + Compose plugin on Ubuntu 22.04/24.04
# Run as root (or with sudo): sudo bash install-docker.sh
set -euo pipefail

echo "[install-docker] Starting Docker installation on Ubuntu..."

# 1. Remove old/conflicting packages
for pkg in docker.io docker-doc docker-compose docker-compose-v2 podman-docker containerd runc; do
    apt-get remove -y "$pkg" 2>/dev/null || true
done

# 2. Install prerequisites
apt-get update
apt-get install -y ca-certificates curl gnupg lsb-release python3 python3-pip pyyaml

# 3. Add Docker's official GPG key
install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg \
    | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
chmod a+r /etc/apt/keyrings/docker.gpg

# 4. Add Docker repository
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
  https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" \
  | tee /etc/apt/sources.list.d/docker.list > /dev/null

# 5. Install Docker Engine + Compose plugin
apt-get update
apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# 6. Start and enable Docker
systemctl enable docker
systemctl start docker

# 7. Add deploy user to docker group (avoids sudo for docker commands)
DEPLOY_USER="${SUDO_USER:-deploy}"
if id "$DEPLOY_USER" &>/dev/null; then
    usermod -aG docker "$DEPLOY_USER"
    echo "[install-docker] Added $DEPLOY_USER to docker group."
else
    echo "[install-docker] WARN: user '$DEPLOY_USER' not found; add manually: usermod -aG docker <user>"
fi

# 8. Install pyyaml for stackctl
pip3 install pyyaml --break-system-packages 2>/dev/null || pip3 install pyyaml

# 9. Verify
docker --version
docker compose version

echo ""
echo "[install-docker] Done. Log out and back in for group membership to take effect."
echo "  Then run: docker run hello-world"
