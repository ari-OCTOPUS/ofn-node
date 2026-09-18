#!/bin/bash
set -u
KEY="$HOME/.ssh/octopus_mesh_ed25519"
for ip in 138 180 182 100 160 193 114; do
  echo "==== NODE $ip ===="
  ssh -i "$KEY" -o BatchMode=yes -o ConnectTimeout=10 -o StrictHostKeyChecking=accept-new "root@192.168.0.$ip" 'date -u +%Y-%m-%dT%H:%M:%SZ; hostname; . /etc/os-release; echo PRETTY_NAME=$PRETTY_NAME; echo VERSION_CODENAME=$VERSION_CODENAME; echo BOOT_ID=$(cat /proc/sys/kernel/random/boot_id); echo -n SVC_FILTERED=; systemctl list-units --type=service --state=running --no-pager --no-legend 2>/dev/null | awk "{print \$1}" | grep -Ei "octo|ofn|mesh|llama|rknn|sensor|owner" | tr "\n" " "; echo; echo -n SVC_COUNT_RUNNING=; systemctl list-units --type=service --state=running --no-pager --no-legend 2>/dev/null | wc -l; ls /usr/lib/librknnrt.so* /usr/lib/aarch64-linux-gnu/librknnrt.so* 2>/dev/null || echo LIBRKKNRT_ABSENT; ls /dev/dri/renderD* 2>/dev/null | head -8; echo -n NPU_MODALIAS=; cat /sys/devices/platform/fdab0000.npu/modalias 2>/dev/null || echo NONE; command -v python3; python3 --version; command -v git; git --version'
  echo "ssh_exit=$?"
done