#!/bin/sh
# fleet-inventory-v2.sh — T0 repaired collector (GOV-V8 L2)
set +e
COLLECT_UTC=$(date -u +%Y-%m-%dT%H:%M:%SZ 2>/dev/null || echo UNKNOWN)
BOOT_ID=$(cat /proc/sys/kernel/random/boot_id 2>/dev/null || echo UNKNOWN)
HOST=$(hostname 2>/dev/null); EXIT_HOST=$?
MODEL=$(tr -d '\0' < /proc/device-tree/model 2>/dev/null); EXIT_MODEL=$?
[ -z "$MODEL" ] && MODEL=UNKNOWN
CORES=$(nproc 2>/dev/null); EXIT_NPROC=$?
MEM_MB=$(awk '/MemTotal/{print int($2/1024)}' /proc/meminfo 2>/dev/null); EXIT_MEM=$?
DISK_TOTAL_GB=$(df -BG / 2>/dev/null | awk 'NR==2{gsub(/G/,"",$2); print $2}'); EXIT_DF=$?
DISK_FREE_GB=$(df -BG / 2>/dev/null | awk 'NR==2{gsub(/G/,"",$4); print $4}')
KERNEL=$(uname -r 2>/dev/null); EXIT_UNAME=$?
OS_CODENAME=UNKNOWN
EXIT_OSRELEASE=1
if [ -r /etc/os-release ]; then
  OS_CODENAME=$(. /etc/os-release; printf '%s' "$VERSION_CODENAME")
  EXIT_OSRELEASE=$?
  [ -z "$OS_CODENAME" ] && OS_CODENAME=UNKNOWN
fi
TEMP_C=$(awk '{printf "%.1f", $1/1000}' /sys/class/thermal/thermal_zone0/temp 2>/dev/null || echo UNKNOWN)
MAC=$(ip -o link show eth0 2>/dev/null | awk '{print $17}'); EXIT_MAC=$?
[ -z "$MAC" ] && MAC=UNKNOWN
SD_PRESENT=$(lsblk -no NAME 2>/dev/null | grep -c '^mmcblk1' || true)
UPTIME_S=$(cut -d. -f1 /proc/uptime 2>/dev/null || echo UNKNOWN)
SWAP_TOTAL_KB=$(awk '/SwapTotal/{print $2}' /proc/meminfo 2>/dev/null); [ -z "$SWAP_TOTAL_KB" ] && SWAP_TOTAL_KB=UNKNOWN
SWAP_FREE_KB=$(awk '/SwapFree/{print $2}' /proc/meminfo 2>/dev/null); [ -z "$SWAP_FREE_KB" ] && SWAP_FREE_KB=UNKNOWN

SVC_LIST=$(systemctl list-units --type=service --state=running --no-legend --no-pager 2>/dev/null)
SVC_EXIT=$?
RUNNING_SERVICES_COUNT=$(printf '%s\n' "$SVC_LIST" | awk 'NF{c++} END{print c+0}')
SVC_NAMES=$(printf '%s\n' "$SVC_LIST" | awk 'NF{print $1}' | head -n 80 | tr '\n' ',' | sed 's/,$//')
SVC_NAMES_TOTAL=$RUNNING_SERVICES_COUNT
if [ "$SVC_NAMES_TOTAL" -gt 80 ] 2>/dev/null; then SVC_NAMES_TRUNCATED=1; else SVC_NAMES_TRUNCATED=0; fi
[ -z "$SVC_NAMES" ] && [ "$SVC_EXIT" -ne 0 ] && SVC_NAMES=UNKNOWN
OCTOPUS_SVC_NAMES=$(printf '%s\n' "$SVC_LIST" | awk 'BEGIN{IGNORECASE=1} NF && $1 ~ /octopus|octomesh|sensorium|capability-school|llama|rknn|npu/ {print $1}' | tr '\n' ',' | sed 's/,$//')
[ -z "$OCTOPUS_SVC_NAMES" ] && OCTOPUS_SVC_NAMES=NONE

LIBRKKNRT_PATHS=$(find /usr /opt /lib /home -name 'librknnrt*' 2>/dev/null | head -n 20)
LIBRKKNRT_EXIT=$?
LIBRKKNRT_COUNT=$(printf '%s\n' "$LIBRKKNRT_PATHS" | awk 'NF{c++} END{print c+0}')
if [ "$LIBRKKNRT_COUNT" -eq 0 ]; then
  LIBRKKNRT_PATHS=NONE
else
  LIBRKKNRT_PATHS=$(printf '%s\n' "$LIBRKKNRT_PATHS" | tr '\n' '|' | sed 's/|$//')
fi

RKNPU_DRM=UNKNOWN
EXIT_RKNPU=1
for ue in /sys/class/drm/*/device/uevent; do
  [ -r "$ue" ] || continue
  if grep -q 'DRIVER=RKNPU' "$ue" 2>/dev/null; then
    RKNPU_DRM=$(tr '\n' ' ' < "$ue" | sed 's/ $//')
    EXIT_RKNPU=0
    break
  fi
done
NPU_COMPAT=$(tr '\0' ' ' < /proc/device-tree/npu@fdab0000/compatible 2>/dev/null | sed 's/ $//')
EXIT_NPU_COMPAT=$?
[ -z "$NPU_COMPAT" ] && NPU_COMPAT=UNKNOWN

printf 'COLLECT_UTC=%s\n' "$COLLECT_UTC"
printf 'BOOT_ID=%s\n' "$BOOT_ID"
printf 'HOST=%s\n' "$HOST"
printf 'MODEL=%s\n' "$MODEL"
printf 'CORES=%s\n' "$CORES"
printf 'MEM_MB=%s\n' "$MEM_MB"
printf 'DISK_TOTAL_GB=%s\n' "$DISK_TOTAL_GB"
printf 'DISK_FREE_GB=%s\n' "$DISK_FREE_GB"
printf 'KERNEL=%s\n' "$KERNEL"
printf 'OS_CODENAME=%s\n' "$OS_CODENAME"
printf 'TEMP_C=%s\n' "$TEMP_C"
printf 'MAC=%s\n' "$MAC"
printf 'SD_PRESENT=%s\n' "$SD_PRESENT"
printf 'UPTIME_S=%s\n' "$UPTIME_S"
printf 'SWAP_TOTAL_KB=%s\n' "$SWAP_TOTAL_KB"
printf 'SWAP_FREE_KB=%s\n' "$SWAP_FREE_KB"
printf 'RUNNING_SERVICES_COUNT=%s\n' "$RUNNING_SERVICES_COUNT"
printf 'SVC_EXIT=%s\n' "$SVC_EXIT"
printf 'SVC_NAMES=%s\n' "$SVC_NAMES"
printf 'SVC_NAMES_TRUNCATED=%s\n' "$SVC_NAMES_TRUNCATED"
printf 'OCTOPUS_SVC_NAMES=%s\n' "$OCTOPUS_SVC_NAMES"
printf 'LIBRKKNRT_COUNT=%s\n' "$LIBRKKNRT_COUNT"
printf 'LIBRKKNRT_PATHS=%s\n' "$LIBRKKNRT_PATHS"
printf 'LIBRKKNRT_EXIT=%s\n' "$LIBRKKNRT_EXIT"
printf 'RKNPU_DRM=%s\n' "$RKNPU_DRM"
printf 'NPU_COMPAT=%s\n' "$NPU_COMPAT"
printf 'EXIT_HOST=%s\n' "$EXIT_HOST"
printf 'EXIT_MODEL=%s\n' "$EXIT_MODEL"
printf 'EXIT_NPROC=%s\n' "$EXIT_NPROC"
printf 'EXIT_MEM=%s\n' "$EXIT_MEM"
printf 'EXIT_DF=%s\n' "$EXIT_DF"
printf 'EXIT_UNAME=%s\n' "$EXIT_UNAME"
printf 'EXIT_OSRELEASE=%s\n' "$EXIT_OSRELEASE"
printf 'EXIT_MAC=%s\n' "$EXIT_MAC"
printf 'EXIT_RKNPU=%s\n' "$EXIT_RKNPU"
printf 'EXIT_NPU_COMPAT=%s\n' "$EXIT_NPU_COMPAT"
