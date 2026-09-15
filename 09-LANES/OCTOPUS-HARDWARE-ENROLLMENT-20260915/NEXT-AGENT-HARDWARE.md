# NEXT AGENT — Hardware Discovery & Enrollment Continuation

**Created:** 2026-09-15T01:30:00Z
**Priority:** Find SD cards on existing boards, prepare them for booting new OPi5 boards

## Current State (READ FIRST)

Three existing Orange Pi 5 Pro boards are running the OCTOPUS organism:
- **138** (192.168.0.138) — executor, SSH as `ari` (`ssh board138`), ✅ alive
- **180** (192.168.0.180) — llama model server, SSH as `root` (`ssh root@192.168.0.180`), ✅ alive
- **182** (192.168.0.182) — witness, SSH as `root` (`ssh root@192.168.0.182`), ⚠️ may be boot-looping

Five NEW Orange Pi 5 boards (4 Pro + 1 Plus) are purchased, powered, connected via LAN to the same router:
- Two are visible: .100 and .160 (SSH open, Debian 13, password unknown — all common passwords rejected)
- Three are invisible on the network (may have no OS on EMMC, or no LAN cable was connected)
- Owner says some boards may not have had LAN cables connected — verify each board has a LAN cable to the 16-port switch

Seven ESP32-S3 boards are powered (no data connection, no WiFi config):
- Two appear on WiFi: .113 (MAC be:85:3a:89:82:04) and .118 (MAC 8e:ed:f9:80:65:f0) — no open ports
- Five others are invisible

Router: Tenda at 192.168.0.1, WPS PIN = password: `19122960`
Browser access works (login via `http://192.168.0.1/login.html` with that password, then click "Online: N" to see device list)

## MISSION

### Phase 1: Find SD cards on existing boards

The owner says microSD cards are inside some of the three existing boards. Check ALL THREE:

```bash
# On 138:
ssh board138 'ls /dev/mmcblk1* 2>/dev/null; lsblk | grep -v mmcblk0 | grep -v loop; dmesg | grep -i mmcblk1'

# On 180:
ssh root@192.168.0.180 'ls /dev/mmcblk1* 2>/dev/null; lsblk | grep -v mmcblk0 | grep -v loop; dmesg | grep -i mmcblk1'

# On 182 (if reachable):
ssh root@192.168.0.182 'ls /dev/mmcblk1* 2>/dev/null; lsblk | grep -v mmcblk0 | grep -v loop; dmesg | grep -i mmcblk1'
```

If a board has SD detected at boot time (in `dmesg` from boot, NOT hot-plugged):
- Record: size, partition layout, filesystem type, mount status
- Mount it and check contents

### Phase 2: Prepare bootable SD card

**CRITICAL WARNING:** Hot-plugging SD card into a running OPi5 Pro causes a KERNEL PANAGCR (confirmed twice on 182). The ONLY safe approach:

**Option A: Boot-time script (recommended)**
1. Write a script on the target board that runs at boot and copies bootloader to SD if present
2. Power off the board
3. Insert SD card
4. Power on — board boots from EMMC, script runs, bootloader is copied to SD
5. Power off, remove SD, insert into new board

```bash
# On the board with SD slot (e.g., 180):
cat > /usr/local/bin/prepare_sd.sh << 'EOF'
#!/bin/bash
# Runs at boot; if SD card is present, copies bootloader from EMMC
if [ -b /dev/mmcblk1 ]; then
    echo "SD card detected — copying bootloader..."
    # Copy first 16MB (bootloader + boot sectors)
    dd if=/dev/mmcblk0 of=/dev/mmcblk1 bs=1M count=16 conv=notrunc status=progress
    # Copy boot partition if it exists (first 2GB for safety)
    dd if=/dev/mmcblk0 of=/dev/mmcblk1 bs=1M skip=16 seek=16 count=2000 conv=notrunc status=progress
    # Add SSH key
    mkdir -p /tmp/sdprep
    if mount /dev/mmcblk1p1 /tmp/sdprep 2>/dev/null; then
        mkdir -p /tmp/sdprep/root/.ssh
        echo "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIBhZWe7gxOT7SkB+YtRgp3WtAkhVSlGSUV2hgpNHeE1Q ari@DietPi" >> /tmp/sdprep/root/.ssh/authorized_keys
        chmod 600 /tmp/sdprep/root/.ssh/authorized_keys
        # Disable dietpi-kill_ssh
        rm -f /tmp/sdprep/etc/systemd/system/dietpi-kill_ssh.service
        ln -sf /dev/null /tmp/sdprep/etc/systemd/system/dietpi-kill_ssh.service
        umount /tmp/sdprep
    fi
    sync
    echo "SD card prepared — safe to power off and move to new board"
fi
EOF
chmod +x /usr/local/bin/prepare_sd.sh
# Create systemd service to run at boot
cat > /etc/systemd/system/prepare-sd.service << 'EOF'
[Unit]
Description=Prepare SD card for new board boot
After=multi-user.target
[Service]
Type=oneshot
ExecStart=/usr/local/bin/prepare_sd.sh
RemainAfterExit=no
[Install]
WantedBy=multi-user.target
EOF
systemctl daemon-reload
systemctl enable prepare-sd.service
```

Then:
1. `poweroff` the board
2. Owner inserts SD card
3. Owner powers on
4. Script runs automatically, prepares SD
5. Check with `systemctl status prepare-sd.service` for result
6. `poweroff`
7. Owner removes SD, puts in new board

**Option B: USB SD card reader on PC (if owner obtains one)**
- Download DietPi/Armbian image for OPi5
- Flash with `dd` or balenaEtcher
- Pre-configure SSH key in the image before writing

### Phase 3: Boot new board from SD

1. Insert prepared SD into a new OPi5 board (one that has NO OS on EMMC)
2. Connect LAN cable
3. Power on
4. Wait 60 seconds for boot + DHCP
5. Scan network from 138: `for i in $(seq 1 254); do ping -c1 -W1 192.168.0.$i & done; wait`
6. Look for NEW IP (not in the known list)
7. SSH: `ssh -i ~/.ssh/id_ed25519 root@<NEW_IP>`
8. If SSH works → enroll in mesh

### Phase 4: Enroll new board in OCTOPUS mesh

Once SSH access is established:
```bash
# Basic enrollment
hostnamectl set-hostname opi5-node-<N>
# Copy mesh SSH keys
# Install basic monitoring (heartbeat)
# Add to /etc/hosts on 138
# Configure as dedicated model server or compute node
```

## Known SSH Keys on 138
```
~/.ssh/id_ed25519 (main key — use this)
~/.ssh/octopus_mesh_ed25519
~/.ssh/inter_board_ed25519
~/.ssh/ofn_deploy
~/.ssh/octopus_138
```

## Tools Already Installed
- 138: `sshpass`, `rkdeveloptool`, `expect`
- 182: (unverified — may need reinstall after reboot)

## DNS/Network
- Router: Tenda at 192.168.0.1 (password: 191122960)
- Subnet: 192.168.0.0/24
- 16-port switch connects all boards
- Laptop (192.168.0.191) connects via WiFi to router

## Rules
- NEVER hot-plug SD card into a running OPi5 (causes crash — confirmed)
- NEVER power off 138 (it's the executor — organism dies)
- ALWAYS verify with `dmesg` that SD was detected at boot time
- The organism on 138 continues running regardless — these are additive operations
- customer_send=false, GO-B4=false, hold_external=true (unchanged)
- Do NOT re-ask owner decisions already recorded (two-hash=REJECT, W6=PREPARE, live-test=YES)

## Success Criteria
- At least 1 new board boots from prepared SD and is SSH-accessible
- Board is enrolled in the OCTOPUS mesh (hostname + monitoring)
- All 5 new boards identified and accounted for (even if 3 need OS installation)
- 182 witness board restored to normal operation
