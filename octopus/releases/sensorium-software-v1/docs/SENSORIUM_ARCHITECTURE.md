# SENSORIUM_ARCHITECTURE

Board agent `agent://octopus/sensorium-board/main` on `sensorium-opi5pro-68e44cdf`.

Live code: `/opt/octopus/current` → release directory (atomic symlink).
Config: signed `/etc/octopus/config/{board,registry}.yaml` verified with root-v2.
State: `/var/lib/octopus/state` (snapshots, evidence, sequences).
Audit: `/var/lib/octopus/audit` append-only hash chain.
Bus: NATS Core + JetStream on 192.168.0.182:4222. Agent cannot create streams.

SOFTWARE_PLATFORM_COMPLETE ≠ ARMED ≠ HARDWARE_SAFE ≠ ALL_100_SENSORS_ACTIVE.
READY means WAVE0_OBSERVE_ONLY.
