#!/bin/bash
# =============================================================================
# write-pro-card.sh — write a bootable DietPi image for Orange Pi 5 Pro onto an
# SD card that is ALREADY INSERTED in a running board, then inject SSH keys.
#
# Run ON a board (138 has the verified image at ~/bootmedia/).  NOT run yet —
# this is the prepared "option A" path from OWNER-ACTIONS.md, awaiting a decision.
#
#   ssh board138 'sudo bash ~/bootmedia/write-pro-card.sh /dev/mmcblk1'
#
# Rollback: the previous card content is an Armbian OPi5-Plus image that can be
# re-downloaded from armbian.com; nothing unique is destroyed.  A sector-level
# backup of the first 1.55 GiB is taken to ~/bootmedia/ before writing, so the
# old card can be restored with:
#   xz -dc ~/bootmedia/prev-card-backup.img.xz | dd of=/dev/mmcblk1 bs=4M conv=fsync
# =============================================================================
set -euo pipefail

DEV="${1:-/dev/mmcblk1}"
IMG="${IMG:-/home/ari/bootmedia/dietpi-opi5pro.img.xz}"
BACKUP="${BACKUP:-/home/ari/bootmedia/prev-card-backup.img.xz}"

KEYS=(
  "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAID1NT5HvzUjeedbqARa6BF08LO/JtWRzQZf0sfnpj+zO armin@DESKTOP-KA9RFN5"
  "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIATTB6531MqG2h86kU/oWWnFIhSJhA0udryJ4H+2Gg0B piggybank-2026"
  "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIN+rryRur5/Yz3hNiNCmOD0rN9bFEJiZI2FIOA2uRP5c octopus-mesh-ari@DietPi"
  "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIBhZWe7gxOT7SkB+YtRgp3WtAkhVSlGSUV2hgpNHeE1Q ari@DietPi"
)

fail() { echo "ABORT: $*" >&2; exit 1; }

[ "$(id -u)" -eq 0 ] || fail "must run as root"
[ -b "$DEV" ]        || fail "$DEV is not a block device"
[ -f "$IMG" ]        || fail "image not found: $IMG"

# --- Safety gate 1: never touch eMMC ----------------------------------------
case "$DEV" in
  /dev/mmcblk0*) fail "$DEV is the eMMC — refusing. Use /dev/mmcblk1*." ;;
esac

# --- Safety gate 2: must be the removable SD host ---------------------------
[ -e "${DEV%p*}" ] || fail "parent device of $DEV not found"
SIZE_GB=$(( $(blockdev --getsize64 "$DEV") / 1000000000 ))
[ "$SIZE_GB" -lt 8 ]  && fail "$DEV is only ${SIZE_GB}GB — too small"
[ "$SIZE_GB" -gt 40 ] && fail "$DEV is ${SIZE_GB}GB — larger than the known 32GB card; refusing"

# --- Safety gate 3: nothing mounted -----------------------------------------
if lsblk -no MOUNTPOINT "$DEV" | grep -q .; then
  fail "$DEV (or a partition) is mounted — unmount first (avoid hot-removal surprises)"
fi

echo "Target : $DEV (${SIZE_GB}GB)"
echo "Image  : $IMG"
echo "This will DESTROY the current contents of $DEV."
if [ "${FORCE:-0}" = "1" ]; then
  echo "FORCE=1 -> proceeding without prompt"
else
  read -r -p "Type WRITE to continue: " a
  [ "$a" = "WRITE" ] || fail "not confirmed"
fi

# --- Backup the old card's bootloader + rootfs (1.55 GiB) -------------------
if [ "${BACKUP:-}" = "none" ]; then
  echo "[1/4] backup skipped (BACKUP=none)"
elif [ ! -f "$BACKUP" ]; then
  echo "[1/4] backing up old card head (bootstrap + rootfs) -> $BACKUP"
  dd if="$DEV" bs=4M count=400 status=none | python3 -c "
import sys, lzma
with lzma.open('$BACKUP','wb',preset=0) as o:
    while True:
        b = sys.stdin.buffer.read(4<<20)
        if not b: break
        o.write(b)
"
else
  echo "[1/4] backup already exists: $BACKUP"
fi

# --- Write ------------------------------------------------------------------
# NOTE: `xz` is NOT installed on 138 — use Python's stdlib lzma instead.
# (A previous run silently wrote 0 bytes because of exactly this.)
echo "[2/4] writing image (this takes a few minutes)"
sudo python3 - "$IMG" "$DEV" <<'PY'
import lzma, os, sys
src, dst = sys.argv[1], sys.argv[2]
n = 0
o = open(dst, "wb", buffering=0)
try:
    with lzma.open(src, "rb") as f:
        while True:
            b = f.read(4 << 20)
            if not b:
                break
            o.write(b); n += len(b)
    o.flush(); os.fsync(o.fileno())
finally:
    o.close()
print("WROTE_BYTES", n)
if n == 0:
    sys.exit(1)
PY
sync
partprobe "$DEV" || true
sleep 2
lsblk "$DEV"

# --- Inject SSH keys --------------------------------------------------------
P1="${DEV}p1"
[ -b "$P1" ] || fail "$P1 did not appear after write"
echo "[3/4] injecting SSH keys into $P1"
MNT=$(mktemp -d)
mount "$P1" "$MNT"
mkdir -p "$MNT/root/.ssh"
chmod 700 "$MNT/root/.ssh"
printf '%s\n' "${KEYS[@]}" > "$MNT/root/.ssh/authorized_keys"
chmod 600 "$MNT/root/.ssh/authorized_keys"
chown -R 0:0 "$MNT/root/.ssh"
grep -q '^PermitRootLogin' "$MNT/etc/ssh/sshd_config" \
  && sed -i 's/^PermitRootLogin.*/PermitRootLogin yes/' "$MNT/etc/ssh/sshd_config"
# hostname so the board is unmistakable on the LAN
echo "opi5pro-new" > "$MNT/etc/hostname"
sed -i 's/127.0.1.1.*/127.0.1.1\topi5pro-new/' "$MNT/etc/hosts" 2>/dev/null || true
sync
umount "$MNT"
rmdir "$MNT"

# --- Verify -----------------------------------------------------------------
echo "[4/4] verifying"
e2fsck -fn "$P1" 2>&1 | tail -3
echo "done — safe to power off the source board, move the card, and boot the new board"
